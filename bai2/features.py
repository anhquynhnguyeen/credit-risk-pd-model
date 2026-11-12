"""Feature engineering"""
from __future__ import annotations

import ast
import json

import numpy as np
import pandas as pd

# Từ khóa nhận diện app vay / tín dụng (tiếng Anh + tiếng Indonesia).
# Bỏ qua com.finaccel.android (Kredivo) vì có trên ~98% máy, nhiều khả năng là chính app cho vay.
LOAN_KEYWORDS = ("pinjam", "kredit", "loan", "cash", "dana", "uang", "rupiah", "credit",
                 "akulaku", "silvrr", "tunaiku", "modal", "kta", "paylater")
BANK_KEYWORDS = ("bca", "bni", "mandiri", "bri", "cimb", "danamon", "permata", "btn", "jenius")
GAME_KEYWORDS = ("game", "legends", "pubg", "freefire", "dts.freefire", "clash")
IGNORE_APPS = {"com.finaccel.android"}

CALL_KEYS = ["total_calls", "percent_incoming_daytime", "percent_incoming_nighttime",
             "percent_outgoing_daytime", "percent_outgoing_nighttime", "percent_other_calls",
             "duration_incoming_daytime", "duration_incoming_nighttime",
             "duration_outgoing_daytime", "duration_outgoing_nighttime"]

# Các biến đưa vào mô hình, chia theo loại để xử lý cho đúng
NUMERIC = [
    "age", "num_friends", "log_salary", "employment_duration", "children", "education",
    "apply_hour", "total_contacts", "n_apps", "n_loan_apps", "n_bank_apps", "n_game_apps",
    "call_total", "call_pct_in_day", "call_pct_in_night", "call_pct_out_day", "call_pct_out_night",
    "call_pct_other", "call_dur_total_log", "fb_age_gap", "fb_days_since_update",
]
CATEGORICAL = [
    "gender", "employment_type", "marital_status", "apply_weekday", "device_brand",
    "fb_relation_group", "fb_gender_mismatch", "has_fb", "contacts_zero",
]


def _count_keywords(apps: list[str], keywords: tuple[str, ...]) -> int:
    return sum(1 for a in apps if a not in IGNORE_APPS and any(k in a.lower() for k in keywords))


def _relation_group(x) -> str:
    if pd.isna(x):
        return "Not declared"
    x = str(x)
    if x.startswith("Married"):
        return "Married"
    if x.startswith("Single"):
        return "Single"
    if x.startswith("In a relationship") or x.startswith("Engaged"):
        return "In a relationship / engaged"
    return "Khác (ly hôn, phức tạp...)"


def load_raw(path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw
    out = pd.DataFrame({"index": d["index"], "flag_bad": d["flag_bad"]})

    # --- thời điểm nộp đơn: dùng để chia tập theo thời gian, và giờ/thứ nộp đơn làm biến
    joined = pd.to_datetime(d["de_date_joined"], format="%d/%m/%Y %H:%M")
    out["date_joined"] = joined
    out["month"] = joined.dt.to_period("M").astype(str)
    out["apply_hour"] = joined.dt.hour
    out["apply_weekday"] = joined.dt.dayofweek.map(lambda x: "Weekend" if x >= 5 else "Weekday")

    # --- demographic (de_)
    out["age"] = d["de_age"]
    out["gender"] = d["de_gender"].map({1: "Male", 2: "Female"})
    out["num_friends"] = d["de_num_friends"].replace(-1, np.nan)           # -1 = không có dữ liệu
    out["log_salary"] = np.log1p(d["de_monthly_salary"].replace(0, np.nan))  # lương lệch phải → lấy log
    out["employment_type"] = d["de_employment_type"].map(
        {1: "Full-time", 2: "Part-time", 3: "Business owner", 4: "Full-time"})  # 4: không có trong mô tả đề, chỉ 2 hồ sơ → gộp vào nhóm đông nhất
    out["employment_duration"] = d["de_employment_duration"]
    out["education"] = d["de_education"]                                    # thứ bậc 1-5, giữ dạng số
    out["marital_status"] = d["de_marital_status"].map(
        {1: "Single", 2: "Married", 3: "Divorced / widowed", 4: "Divorced / widowed"})  # 3 và 4 ít hồ sơ → gộp
    out["children"] = d["de_children"]
    # de_accomodation_type: chỉ có một giá trị (4) → không mang thông tin, bỏ

    # --- phone (ph_)
    out["total_contacts"] = d["ph_total_contacts"]
    out["contacts_zero"] = np.where(d["ph_total_contacts"] == 0, "Yes", "No")  # 66% = 0, có thể do không cấp quyền
    brand = d["ph_other_device_info"].apply(lambda s: json.loads(s).get("brand", "unknown")).str.lower()
    top = brand.value_counts().index[:8]
    out["device_brand"] = brand.where(brand.isin(top), "other")

    calls = d["ph_call_log_stats"].apply(lambda s: json.loads(s) if isinstance(s, str) else {})
    calls = pd.DataFrame(calls.tolist(), index=d.index).reindex(columns=CALL_KEYS)
    out["call_total"] = calls["total_calls"]
    out["call_pct_in_day"] = calls["percent_incoming_daytime"]
    out["call_pct_in_night"] = calls["percent_incoming_nighttime"]
    out["call_pct_out_day"] = calls["percent_outgoing_daytime"]
    out["call_pct_out_night"] = calls["percent_outgoing_nighttime"]
    out["call_pct_other"] = calls["percent_other_calls"]
    out["call_dur_total_log"] = np.log1p(calls[[c for c in CALL_KEYS if c.startswith("duration")]].sum(axis=1, min_count=1))
    # ph_country_code: 99,9% là "id" → bỏ

    apps = d["ph_app_list"].apply(ast.literal_eval)
    out["n_apps"] = apps.str.len()
    out["n_loan_apps"] = apps.apply(lambda a: _count_keywords(a, LOAN_KEYWORDS))
    out["n_bank_apps"] = apps.apply(lambda a: _count_keywords(a, BANK_KEYWORDS))
    out["n_game_apps"] = apps.apply(lambda a: _count_keywords(a, GAME_KEYWORDS))

    # --- facebook (fb_): chủ yếu là các phép kiểm tra tính nhất quán với thông tin khai báo
    out["has_fb"] = np.where(d["fb_gender"].notna() | d["fb_last_updated_date"].notna(), "Yes", "No")
    fb_gender = d["fb_gender"].map({"male": 1, "female": 2})
    out["fb_gender_mismatch"] = np.select(
        [fb_gender.isna(), fb_gender != d["de_gender"]], ["No FB", "Mismatch"], "Match")
    fb_dob = pd.to_datetime(d["fb_dob"], format="%m/%d/%Y", errors="coerce")
    fb_age = (joined - fb_dob).dt.days / 365.25
    out["fb_age_gap"] = (fb_age - d["de_age"]).abs()                        # tuổi FB lệch tuổi khai báo
    fb_upd = pd.to_datetime(d["fb_last_updated_date"], utc=True, errors="coerce").dt.tz_localize(None)
    # 0,2% hồ sơ cập nhật FB sau ngày nộp đơn → đặt về 0 để tránh dùng thông tin "tương lai"
    out["fb_days_since_update"] = (joined - fb_upd).dt.days.clip(lower=0)
    out["fb_relation_group"] = d["fb_relation"].apply(_relation_group)
    return out
