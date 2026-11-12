"""Bài I - Các phép tính kiểm định mô hình PD (Python làm chuẩn để đối chiếu với Excel).

Part I - PD model validation calculations (Python reference values, used to cross-check Excel).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SCORE_COL = "Điểm"
LABEL_COL = "Good=0/Bad=1"


@dataclass
class Results:
    data: pd.DataFrame            # từng khách hàng: score, bad, grade, pd
    master: pd.DataFrame          # master scale: grade, band, lower, upper, pd
    grades: pd.DataFrame          # bảng tổng hợp theo hạng
    auc_score: float              # AUC tính trên điểm gốc
    auc_se: float
    auc_grade: float              # AUC tính trên 10 hạng (bằng giá trị Excel)
    ar_cap: float                 # AR tính từ diện tích đường CAP (theo hạng)
    curve: pd.DataFrame           # điểm vẽ ROC / CAP
    hl: dict                      # Hosmer-Lemeshow: 10 hạng
    hl_merged: dict               # Hosmer-Lemeshow: gộp hạng 9-10 (kiểm tra độ nhạy)

    @property
    def ar_score(self) -> float:
        return 2 * self.auc_score - 1

    @property
    def auc_ci(self) -> tuple[float, float]:
        return self.auc_score - 1.96 * self.auc_se, self.auc_score + 1.96 * self.auc_se


def load(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Đọc sheet dữ liệu: cột A-B là khách hàng, cột C-E là master scale."""
    raw = pd.read_excel(path, sheet_name=0)
    data = pd.DataFrame({"score": raw[SCORE_COL].astype(int), "bad": raw[LABEL_COL].astype(int)})

    ms = raw.iloc[:, 2:5].dropna()
    ms.columns = ["grade", "band", "pd"]
    ms["grade"] = ms["grade"].astype(int)
    # "≤ 450" -> cận trên 450; "> 850" -> không có cận trên
    ms["upper"] = [float(re.findall(r"\d+", b)[0]) if "≤" in b else np.inf for b in ms["band"]]
    ms["lower"] = [0.0] + [u + 1 for u in ms["upper"][:-1]]   # điểm là số nguyên
    ms["band"] = ms["band"].str.replace(" ", "")
    return data, ms.reset_index(drop=True)[["grade", "band", "lower", "upper", "pd"]]


def assign_grade(data: pd.DataFrame, ms: pd.DataFrame) -> pd.DataFrame:
    """Điểm -> hạng (hạng đầu tiên có cận trên >= điểm) -> PD dự báo."""
    out = data.copy()
    idx = np.searchsorted(ms["upper"].to_numpy(), out["score"].to_numpy(), side="left")
    out["grade"] = ms["grade"].to_numpy()[idx]
    out["pd"] = ms["pd"].to_numpy()[idx]
    return out


def auc(score_risky: np.ndarray, bad: np.ndarray) -> float:
    """AUC = P(khách bad bị chấm rủi ro hơn khách good), hòa tính 0.5 (Mann-Whitney U)."""
    u = stats.mannwhitneyu(score_risky[bad == 1], score_risky[bad == 0]).statistic
    return u / ((bad == 1).sum() * (bad == 0).sum())


def hanley_mcneil_se(a: float, n_bad: int, n_good: int) -> float:
    q1, q2 = a / (2 - a), 2 * a**2 / (1 + a)
    return float(np.sqrt((a * (1 - a) + (n_bad - 1) * (q1 - a**2) + (n_good - 1) * (q2 - a**2))
                         / (n_bad * n_good)))


def grade_table(data: pd.DataFrame, ms: pd.DataFrame) -> pd.DataFrame:
    g = (data.groupby("grade").agg(n=("bad", "size"), d=("bad", "sum"))
         .reindex(ms["grade"], fill_value=0).reset_index())
    g["pd"] = ms["pd"].to_numpy()
    g["band"] = ms["band"].to_numpy()
    g["odr"] = g["d"] / g["n"]
    g["expected"] = g["n"] * g["pd"]

    # Binomial test từng hạng
    g["k_crit_95"] = stats.binom.ppf(0.95, g["n"], g["pd"]).astype(int)
    g["k_crit_99"] = stats.binom.ppf(0.99, g["n"], g["pd"]).astype(int)
    g["p_upper"] = stats.binom.sf(g["d"] - 1, g["n"], g["pd"])        # P(X >= d)
    g["p_lower"] = stats.binom.cdf(g["d"], g["n"], g["pd"])           # P(X <= d)
    g["p_two"] = np.minimum(1, 2 * np.minimum(g["p_upper"], g["p_lower"]))
    g["p_two_exact"] = [stats.binomtest(int(d), int(n), p).pvalue
                        for d, n, p in zip(g["d"], g["n"], g["pd"])]
    g["z"] = (g["d"] - g["expected"]) / np.sqrt(g["n"] * g["pd"] * (1 - g["pd"]))
    g["light"] = np.select([g["p_upper"] < 0.01, g["p_upper"] < 0.05], ["Đỏ", "Vàng"], "Xanh")

    # Thành phần Hosmer-Lemeshow
    g["hl"] = (g["d"] - g["expected"]) ** 2 / (g["n"] * g["pd"] * (1 - g["pd"]))
    return g


def roc_cap_curve(g: pd.DataFrame) -> pd.DataFrame:
    """Đường ROC và CAP theo hạng, đi từ hạng rủi ro nhất (1) đến an toàn nhất (10)."""
    good = g["n"] - g["d"]
    c = pd.DataFrame({
        "grade": g["grade"],
        "cum_all": g["n"].cumsum() / g["n"].sum(),
        "cum_bad": g["d"].cumsum() / g["d"].sum(),
        "cum_good": good.cumsum() / good.sum(),
    })
    zero = pd.DataFrame({"grade": [0], "cum_all": [0.0], "cum_bad": [0.0], "cum_good": [0.0]})
    return pd.concat([zero, c], ignore_index=True)


def trapezoid(x: pd.Series, y: pd.Series) -> float:
    return float(((x.diff()) * (y + y.shift()) / 2).sum())


def hosmer_lemeshow(n, d, pd_) -> dict:
    n, d, pd_ = map(np.asarray, (n, d, pd_))
    stat = float(((d - n * pd_) ** 2 / (n * pd_ * (1 - pd_))).sum())
    df = len(n)  # kiểm định ngoài mẫu: PD cố định từ trước nên df = số nhóm
    return {"stat": stat, "df": df, "p": float(stats.chi2.sf(stat, df)),
            "crit_95": float(stats.chi2.ppf(0.95, df))}


def run(path: Path) -> Results:
    raw, ms = load(path)
    data = assign_grade(raw, ms)
    g = grade_table(data, ms)

    bad = data["bad"].to_numpy()
    a_score = auc(-data["score"].to_numpy(), bad)          # điểm thấp = rủi ro cao
    a_grade = auc(-data["grade"].to_numpy(), bad)
    curve = roc_cap_curve(g)
    dr = bad.mean()
    cap_area = trapezoid(curve["cum_all"], curve["cum_bad"])
    ar_cap = (cap_area - 0.5) / (0.5 - dr / 2)              # CAP hoàn hảo có diện tích 1 - DR/2

    merged = g.copy()
    merged.loc[merged["grade"] >= 9, "grade"] = 9
    m = merged.groupby("grade").agg(n=("n", "sum"), d=("d", "sum"), e=("expected", "sum"))
    hl_m = hosmer_lemeshow(m["n"], m["d"], m["e"] / m["n"])
    hl_m["note"] = "Gộp hạng 9-10 (PD gộp = tổng kỳ vọng / tổng số khách)"

    return Results(
        data=data, master=ms, grades=g,
        auc_score=a_score, auc_se=hanley_mcneil_se(a_score, int(bad.sum()), int((1 - bad).sum())),
        auc_grade=a_grade, ar_cap=ar_cap, curve=curve,
        hl=hosmer_lemeshow(g["n"], g["d"], g["pd"]), hl_merged=hl_m,
    )


def print_summary(r: Results) -> None:
    d = r.data
    print(f"Số khách: {len(d)}, bad: {d['bad'].sum()}, ODR: {d['bad'].mean():.2%}, "
          f"PD bình quân: {d['pd'].mean():.2%}")
    lo, hi = r.auc_ci
    print(f"AUC (điểm) = {r.auc_score:.4f}  [95% CI {lo:.4f}-{hi:.4f}],  AR = {r.ar_score:.4f}")
    print(f"AUC (hạng) = {r.auc_grade:.4f},  AR từ CAP (hạng) = {r.ar_cap:.4f}")
    cols = ["grade", "n", "d", "odr", "pd", "expected", "k_crit_95", "p_upper", "p_two", "light", "hl"]
    print(r.grades[cols].round(4).to_string(index=False))
    print(f"HL (10 hạng) = {r.hl['stat']:.2f}, df = {r.hl['df']}, p = {r.hl['p']:.2e}")
    print(f"HL (gộp 9-10) = {r.hl_merged['stat']:.2f}, df = {r.hl_merged['df']}, "
          f"p = {r.hl_merged['p']:.2e}")
