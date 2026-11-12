"""Bước 3-6: chia dữ liệu, chọn biến, huấn luyện 2 mô hình, đánh giá.

Mô hình 1 - Logistic Regression trên WOE (scorecard): chuẩn ngành tín dụng, dễ giải thích.
Mô hình 2 - Gradient Boosting (HistGradientBoosting của scikit-learn): bắt được quan hệ phi tuyến.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

import features as F
import woe as W

OOT_MONTHS = ["2018-06", "2018-07"]     # 2 tháng cuối để kiểm tra theo thời gian
IV_MIN = 0.02                           # biến có IV < 0,02 coi như không có ích
CORR_MAX = 0.6                          # hai biến WOE tương quan > 0,6 → giữ biến có IV cao hơn
SEED = 42

# Thang điểm: 600 điểm ↔ tỷ lệ good:bad = 10:1 (PD ≈ 9%); cứ thêm 50 điểm thì tỷ lệ đó gấp đôi
BASE_SCORE, BASE_ODDS, PDO = 600, 10, 50


# ---------- chia dữ liệu ----------

def split(df: pd.DataFrame):
    oot = df["month"].isin(OOT_MONTHS)
    dev, test = df[~oot], df[oot]
    train, valid = train_test_split(dev, test_size=0.25, stratify=dev["flag_bad"], random_state=SEED)
    return train, valid, test


# ---------- chỉ số đánh giá ----------

def ks(y, p) -> float:
    """KS = khoảng cách lớn nhất giữa phân phối lũy kế của bad và good."""
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))


def metrics(y, p) -> dict:
    auc = roc_auc_score(y, p)
    return {"AUC": auc, "Gini": 2 * auc - 1, "KS": ks(y, p)}


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """PSI: phân phối điểm có dịch chuyển giữa lúc xây và lúc dùng không. < 0,1 ổn định."""
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.histogram(expected, edges)[0] / len(expected) + 1e-6
    a = np.histogram(actual, edges)[0] / len(actual) + 1e-6
    return float(np.sum((a - e) * np.log(a / e)))


def decile_table(y, p, n: int = 10) -> pd.DataFrame:
    """Chia khách thành 10 nhóm theo PD dự báo (nhóm 1 = rủi ro nhất)."""
    t = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    t["decile"] = pd.qcut(t["p"].rank(method="first", ascending=False), n, labels=range(1, n + 1))
    g = t.groupby("decile", observed=True).agg(n=("y", "size"), bad=("y", "sum"), pd_mean=("p", "mean"))
    g["bad_rate"] = g["bad"] / g["n"]
    g["cum_bad_share"] = g["bad"].cumsum() / g["bad"].sum()
    return g


def hosmer_lemeshow(tbl: pd.DataFrame) -> dict:
    e = tbl["n"] * tbl["pd_mean"]
    hl = float(((tbl["bad"] - e) ** 2 / (e * (1 - tbl["pd_mean"]))).sum())
    df = len(tbl)        # kiểm định trên dữ liệu ngoài mẫu (OOT) nên df = số nhóm
    return {"HL": hl, "df": df, "p": float(stats.chi2.sf(hl, df))}


# ---------- mô hình 1: scorecard ----------

def select_features(binners: dict, x_woe: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
    iv = pd.Series({k: b.iv for k, b in binners.items()}).sort_values(ascending=False)
    log = pd.DataFrame({"IV": iv, "Đánh giá": iv.map(W.iv_label), "Quyết định": ""})
    keep = []
    corr = x_woe.corr().abs()
    for c in iv.index:
        if iv[c] < IV_MIN:
            log.loc[c, "Quyết định"] = "Loại: IV < 0,02"
            continue
        clash = [k for k in keep if corr.loc[c, k] > CORR_MAX]
        if clash:
            log.loc[c, "Quyết định"] = f"Loại: tương quan cao với {clash[0]}"
            continue
        keep.append(c)
        log.loc[c, "Quyết định"] = "Giữ"
    return keep, log


def fit_scorecard(x: pd.DataFrame, y: pd.Series, cols: list[str]):
    """Logistic regression trên WOE. Với WOE = ln(%good/%bad), hệ số hợp lý phải ÂM.
    Biến nào ra hệ số dương (ngược chiều do tương quan với biến khác) thì loại rồi chạy lại."""
    cols = list(cols)
    dropped = []
    while True:
        lr = LogisticRegression(C=1.0, max_iter=2000).fit(x[cols], y)
        coef = pd.Series(lr.coef_[0], index=cols)
        wrong = coef[coef > 0]
        if wrong.empty:
            return lr, cols, dropped
        worst = wrong.idxmax()
        dropped.append(worst)
        cols.remove(worst)


def scorecard_points(lr, cols: list[str], binners: dict) -> pd.DataFrame:
    """Đổi mô hình thành bảng điểm: mỗi nhóm của mỗi biến được bao nhiêu điểm."""
    factor = PDO / np.log(2)
    offset = BASE_SCORE - factor * np.log(BASE_ODDS)
    k = len(cols)
    rows = []
    for c, beta in zip(cols, lr.coef_[0]):
        t = binners[c].table
        for b, woe_val in t["woe"].items():
            # ln(odds good) = −(β0 + Σ βi·WOEi)  → chia đều hằng số cho các biến
            pts = offset / k - factor * (beta * woe_val + lr.intercept_[0] / k)
            rows.append({"Biến": c, "Nhóm": b, "Số hồ sơ": int(t.loc[b, "n"]),
                         "Tỷ lệ bad": t.loc[b, "bad_rate"], "WOE": woe_val, "Điểm": round(pts)})
    return pd.DataFrame(rows)


def to_score(p_bad: np.ndarray) -> np.ndarray:
    factor = PDO / np.log(2)
    offset = BASE_SCORE - factor * np.log(BASE_ODDS)
    p = np.clip(p_bad, 1e-6, 1 - 1e-6)
    return offset + factor * np.log((1 - p) / p)


# ---------- mô hình 2: gradient boosting ----------

def _encode(x: pd.DataFrame, categories: dict) -> pd.DataFrame:
    out = x[F.NUMERIC + F.CATEGORICAL].copy()
    for c in F.CATEGORICAL:
        out[c] = pd.Categorical(out[c].astype(str), categories=categories[c]).codes
    return out


def fit_boosting(train: pd.DataFrame):
    categories = {c: sorted(train[c].astype(str).unique()) for c in F.CATEGORICAL}
    cols = F.NUMERIC + F.CATEGORICAL
    gb = HistGradientBoostingClassifier(
        learning_rate=0.05, max_iter=1000,
        max_leaf_nodes=7,            # cây nhỏ + mỗi lá ≥ 500 hồ sơ → hạn chế học thuộc
        min_samples_leaf=500, l2_regularization=1.0,
        categorical_features=[cols.index(c) for c in F.CATEGORICAL],
        early_stopping=True, validation_fraction=0.15, n_iter_no_change=30, random_state=SEED)
    gb.fit(_encode(train, categories), train["flag_bad"])
    return gb, categories


# ---------- chạy toàn bộ ----------

def run(df: pd.DataFrame) -> dict:
    train, valid, test = split(df)
    sets = {"Train": train, "Validation": valid, "Test OOT": test}

    binners = W.fit_all(train, train["flag_bad"], F.NUMERIC, F.CATEGORICAL)
    all_cols = list(binners)
    x = {k: W.transform_all(v, binners, all_cols) for k, v in sets.items()}
    selected, iv_log = select_features(binners, x["Train"])
    lr, final_cols, sign_dropped = fit_scorecard(x["Train"], train["flag_bad"], selected)
    for c in sign_dropped:
        iv_log.loc[c, "Quyết định"] = "Loại: hệ số ngược dấu"

    gb, cats = fit_boosting(train)

    preds = {"Logistic (scorecard)": {}, "Gradient Boosting": {}}
    for k, v in sets.items():
        preds["Logistic (scorecard)"][k] = lr.predict_proba(x[k][final_cols])[:, 1]
        preds["Gradient Boosting"][k] = gb.predict_proba(_encode(v, cats))[:, 1]

    perf = []
    for m, by_set in preds.items():
        for k, p in by_set.items():
            perf.append({"Mô hình": m, "Tập": k, **metrics(sets[k]["flag_bad"], p)})
    perf = pd.DataFrame(perf)

    stability, deciles, hl = {}, {}, {}
    for m, by_set in preds.items():
        stability[m] = psi(to_score(by_set["Train"]), to_score(by_set["Test OOT"]))
        deciles[m] = decile_table(test["flag_bad"], by_set["Test OOT"])
        hl[m] = hosmer_lemeshow(deciles[m])

    imp = permutation_importance(gb, _encode(valid, cats), valid["flag_bad"], scoring="roc_auc",
                                 n_repeats=5, random_state=SEED)
    gb_importance = pd.Series(imp.importances_mean, index=F.NUMERIC + F.CATEGORICAL).sort_values(ascending=False)

    monthly = df.groupby("month")["flag_bad"].agg(n="size", bad_rate="mean")
    monthly["Tập"] = np.where(monthly.index.isin(OOT_MONTHS), "Test OOT", "Train + Validation")

    return {
        "sets": sets, "binners": binners, "iv_log": iv_log, "selected": final_cols,
        "sign_dropped": sign_dropped, "lr": lr, "gb": gb, "preds": preds, "perf": perf,
        "psi": stability, "deciles": deciles, "hl": hl, "gb_importance": gb_importance,
        "scorecard": scorecard_points(lr, final_cols, binners), "monthly": monthly,
        "lr_coef": pd.Series(lr.coef_[0], index=final_cols),
    }


# ---------- kiểm tra thêm: chia theo thời gian hay chia ngẫu nhiên? ----------

def test_auc(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    """Chạy lại toàn bộ quy trình (WOE, chọn biến, 2 mô hình) trên một cách chia, trả về AUC trên test."""
    binners = W.fit_all(train, train["flag_bad"], F.NUMERIC, F.CATEGORICAL)
    cols = list(binners)
    x_train, x_test = W.transform_all(train, binners, cols), W.transform_all(test, binners, cols)
    selected, _ = select_features(binners, x_train)
    lr, final_cols, _ = fit_scorecard(x_train, train["flag_bad"], selected)
    gb, cats = fit_boosting(train)
    return {"Logistic (scorecard)": roc_auc_score(test["flag_bad"], lr.predict_proba(x_test[final_cols])[:, 1]),
            "Gradient Boosting": roc_auc_score(test["flag_bad"], gb.predict_proba(_encode(test, cats))[:, 1])}


def compare_splits(df: pd.DataFrame, n_random: int = 5) -> dict:
    """Cách A: test = tháng 6-7. Cách B: test lấy ngẫu nhiên đều 7 tháng (cùng kích thước), lặp n_random lần."""
    train, _, test = split(df)
    by_time = test_auc(train, test)
    strata = df["month"] + "_" + df["flag_bad"].astype(str)     # giữ tỷ lệ từng tháng và tỷ lệ bad
    runs = []
    for seed in range(n_random):
        dev, test_r = train_test_split(df, test_size=len(test), stratify=strata, random_state=seed)
        train_r, _ = train_test_split(dev, test_size=0.25, stratify=dev["flag_bad"], random_state=seed)
        runs.append(test_auc(train_r, test_r))
    no_fb = pd.crosstab(df["month"], df["has_fb"], normalize="index").get("No", 0.0)
    return {"time": by_time, "random": pd.DataFrame(runs), "no_fb_by_month": no_fb}
