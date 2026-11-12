"""WOE (Weight of Evidence) và IV (Information Value): công cụ chuẩn khi làm scorecard tín dụng.

Ý tưởng: chia mỗi biến thành vài nhóm (bin), rồi thay giá trị gốc bằng "mức rủi ro" của nhóm:
    WOE = ln( %good trong nhóm / %bad trong nhóm )
    WOE > 0: nhóm an toàn hơn trung bình; WOE < 0: nhóm rủi ro hơn trung bình.
    IV  = Σ (%good − %bad) × WOE  → đo sức dự báo của cả biến.

Chỉ "học" các nhóm và WOE trên tập train, sau đó áp nguyên cho valid / test.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MISSING = "Missing"


@dataclass
class Binner:
    name: str
    kind: str                       # "numeric" hoặc "categorical"
    edges: list = field(default_factory=list)       # cận cho biến số
    mapping: dict = field(default_factory=dict)     # nhóm -> WOE
    table: pd.DataFrame | None = None
    iv: float = 0.0

    def labels(self, x: pd.Series) -> pd.Series:
        if self.kind == "numeric":
            lab = pd.cut(x, self.edges, include_lowest=True).astype(str)
            return lab.where(x.notna(), MISSING)
        lab = x.astype(object).where(x.notna(), MISSING).astype(str)
        known = set(self.mapping)
        return lab.where(lab.isin(known), "Other")

    def transform(self, x: pd.Series) -> pd.Series:
        return self.labels(x).map(self.mapping).fillna(0.0).astype(float)


def _woe_table(lab: pd.Series, y: pd.Series) -> pd.DataFrame:
    t = pd.DataFrame({"bin": lab, "y": y}).groupby("bin", sort=False)["y"].agg(n="size", bad="sum")
    t["good"] = t["n"] - t["bad"]
    # +0,5 để tránh chia cho 0 ở nhóm không có bad hoặc không có good
    t["pct_good"] = (t["good"] + 0.5) / (t["good"].sum() + 0.5)
    t["pct_bad"] = (t["bad"] + 0.5) / (t["bad"].sum() + 0.5)
    t["bad_rate"] = t["bad"] / t["n"]
    t["woe"] = np.log(t["pct_good"] / t["pct_bad"])
    t["iv_part"] = (t["pct_good"] - t["pct_bad"]) * t["woe"]
    return t


def fit_binner(x: pd.Series, y: pd.Series, name: str, kind: str,
               max_bins: int = 6, min_share: float = 0.05) -> Binner:
    b = Binner(name=name, kind=kind)
    if kind == "numeric":
        # chia theo phân vị (mỗi nhóm có số hồ sơ gần bằng nhau), tối đa max_bins nhóm
        qs = np.unique(np.nanquantile(x, np.linspace(0, 1, max_bins + 1)))
        edges = [-np.inf] + list(qs[:-1]) + [np.inf]
        # gộp nhóm quá nhỏ (< min_share hồ sơ) vào nhóm bên cạnh để WOE ổn định
        while len(edges) > 3:
            counts = pd.cut(x, edges, include_lowest=True).value_counts(sort=False, normalize=True).to_numpy()
            i = int(np.argmin(counts))
            if counts[i] >= min_share:
                break
            del edges[i if i > 0 else 1]
        b.edges = edges
    else:
        # nhóm quá nhỏ (< min_share) gộp thành "Other" để WOE ổn định
        share = x.astype(object).where(x.notna(), MISSING).value_counts(normalize=True)
        keep = set(share[share >= min_share].index.astype(str))
        b.mapping = {k: 0.0 for k in keep}
    lab = b.labels(x)
    if kind == "categorical":
        lab = lab.where(lab.isin(b.mapping), "Other")
    t = _woe_table(lab, y)
    if kind == "numeric":   # sắp các nhóm theo thứ tự giá trị, "Thiếu dữ liệu" để cuối
        order = [str(iv) for iv in pd.IntervalIndex.from_breaks(b.edges, closed="right")]
        t = t.reindex([o for o in order if o in t.index] + [i for i in t.index if i not in order])
    b.mapping = t["woe"].to_dict()
    b.table = t
    b.iv = float(t["iv_part"].sum())
    return b


def fit_all(df: pd.DataFrame, y: pd.Series, numeric: list[str], categorical: list[str]) -> dict[str, Binner]:
    out = {c: fit_binner(df[c], y, c, "numeric") for c in numeric}
    out.update({c: fit_binner(df[c], y, c, "categorical") for c in categorical})
    return out


def transform_all(df: pd.DataFrame, binners: dict[str, Binner], cols: list[str]) -> pd.DataFrame:
    return pd.DataFrame({c: binners[c].transform(df[c]) for c in cols}, index=df.index)


def iv_label(iv: float) -> str:
    """Thang đọc IV thường dùng trong sách scorecard (Siddiqi)."""
    if iv < 0.02:
        return "Không có ích"
    if iv < 0.1:
        return "Yếu"
    if iv < 0.3:
        return "Trung bình"
    return "Mạnh (kiểm tra rò rỉ dữ liệu)"
