"""Bước 7: vẽ biểu đồ (lưu PNG trong output/figures)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import roc_curve  # noqa: E402

BLUE, ORANGE, GREY, RED, TEAL = "#1F4E79", "#E07B00", "#8A94A6", "#C62828", "#23808E"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 13, "figure.dpi": 130})

LABELS = {
    "n_loan_apps": "Số app vay trong máy", "n_apps": "Tổng số app", "education": "Học vấn",
    "call_pct_in_day": "% cuộc gọi đến ban ngày", "n_bank_apps": "Số app ngân hàng",
    "call_total": "Tổng số cuộc gọi", "fb_age_gap": "Lệch tuổi FB và khai báo",
    "call_pct_other": "% cuộc gọi khác", "employment_duration": "Thâm niên làm việc",
    "employment_type": "Loại hình công việc", "call_dur_total_log": "Tổng thời lượng gọi (log)",
    "fb_days_since_update": "Số ngày từ lần cập nhật FB", "call_pct_out_night": "% gọi đi ban đêm",
    "num_friends": "Số bạn bè", "gender": "Giới tính", "call_pct_in_night": "% cuộc gọi đến ban đêm",
    "call_pct_out_day": "% gọi đi ban ngày", "n_game_apps": "Số app game",
    "fb_gender_mismatch": "Giới tính FB lệch khai báo", "apply_hour": "Giờ nộp đơn",
    "marital_status": "Tình trạng hôn nhân", "contacts_zero": "Danh bạ = 0", "age": "Tuổi",
    "device_brand": "Hãng điện thoại", "total_contacts": "Số danh bạ",
    "fb_relation_group": "Tình trạng quan hệ FB", "children": "Số con", "log_salary": "Lương (log)",
    "apply_weekday": "Ngày nộp đơn", "has_fb": "Có Facebook",
}


def label(c: str) -> str:
    return LABELS.get(c, c)


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / f"{name}.png"
    fig.tight_layout()
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


def monthly(r: dict, out: Path) -> Path:
    m = r["monthly"]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    colors = [GREY if s == "Test OOT" else BLUE for s in m["Tập"]]
    ax.bar(m.index, m["n"], color=colors)
    ax.set_ylabel("Số hồ sơ")
    ax2 = ax.twinx()
    ax2.plot(m.index, m["bad_rate"] * 100, color=ORANGE, marker="o", lw=2)
    ax2.set_ylabel("Tỷ lệ bad (%)", color=ORANGE)
    ax2.set_ylim(0, 20)
    ax2.spines["top"].set_visible(False)
    ax.set_title("Số hồ sơ và tỷ lệ bad theo tháng (xanh: xây mô hình, xám: test OOT)")
    return _save(fig, out, "01_monthly")


def iv_bar(r: dict, out: Path) -> Path:
    log = r["iv_log"].sort_values("IV").tail(20)   # 20 biến có IV cao nhất cho dễ đọc
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = [BLUE if d == "Giữ" else (ORANGE if "ngược" in d or "tương quan" in d else GREY)
              for d in log["Quyết định"]]
    ax.barh([label(c) for c in log.index], log["IV"], color=colors)
    ax.axvline(0.02, color=RED, ls="--", lw=1)
    ax.text(0.022, 0.3, "ngưỡng 0,02", color=RED, fontsize=9)
    ax.set_xlabel("Information Value (IV)")
    ax.set_title("IV của 20 biến mạnh nhất\nxanh: giữ · cam: loại vì ngược dấu · xám: IV < 0,02")
    return _save(fig, out, "02_iv")


def woe_profile(r: dict, out: Path, cols: list[str]) -> Path:
    fig, axes = plt.subplots(1, len(cols), figsize=(4.2 * len(cols), 3.6))
    for ax, c in zip(np.atleast_1d(axes), cols):
        t = r["binners"][c].table
        ax.bar(range(len(t)), t["bad_rate"] * 100, color=BLUE)
        ax.set_xticks(range(len(t)))
        ax.set_xticklabels([s.replace("-inf", "−∞").replace("inf", "∞") for s in t.index], rotation=35, ha="right", fontsize=8)
        ax.set_title(label(c), fontsize=12)
        ax.set_ylabel("Tỷ lệ bad (%)")
    return _save(fig, out, "03_woe_profiles")


def roc(r: dict, out: Path) -> Path:
    y = r["sets"]["Test OOT"]["flag_bad"]
    fig, ax = plt.subplots(figsize=(5.2, 5))
    for (m, by_set), col in zip(r["preds"].items(), [BLUE, ORANGE]):
        fpr, tpr, _ = roc_curve(y, by_set["Test OOT"])
        auc = r["perf"].query("`Mô hình` == @m and `Tập` == 'Test OOT'")["AUC"].iloc[0]
        ax.plot(fpr, tpr, color=col, lw=2, label=f"{m}: AUC {auc:.3f}")
    ax.plot([0, 1], [0, 1], color=GREY, ls="--", lw=1, label="Đoán bừa: AUC 0,5")
    ax.set_xlabel("% good bị từ chối nhầm")
    ax.set_ylabel("% bad bị bắt")
    ax.set_title("Đường ROC trên tập test OOT (tháng 6-7)")
    ax.legend(loc="lower right", fontsize=9)
    return _save(fig, out, "04_roc")


def deciles(r: dict, out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for ax, (m, t) in zip(axes, r["deciles"].items()):
        x = np.arange(1, len(t) + 1)
        ax.bar(x, t["bad_rate"] * 100, color=BLUE, label="Tỷ lệ bad thực tế")
        ax.plot(x, t["pd_mean"] * 100, color=ORANGE, marker="o", lw=2, label="PD dự báo trung bình")
        ax.set_xticks(x)
        ax.set_xlabel("Nhóm 10% (1 = rủi ro nhất)")
        ax.set_title(m, fontsize=12)
    axes[0].set_ylabel("%")
    axes[0].legend(fontsize=9)
    fig.suptitle("PD dự báo (cam) so với tỷ lệ bad thực tế (xanh) trên test set", fontweight="bold")
    return _save(fig, out, "05_deciles")


def importance(r: dict, out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    lr = r["lr_coef"].abs().sort_values()
    axes[0].barh([label(c) for c in lr.index], lr, color=BLUE)
    axes[0].set_title("Logistic: độ lớn hệ số |β|")
    gb = r["gb_importance"].head(12).sort_values()
    axes[1].barh([label(c) for c in gb.index], gb, color=ORANGE)
    axes[1].set_title("Gradient Boosting: mức giảm AUC khi xáo trộn biến")
    return _save(fig, out, "06_importance")


def all_charts(r: dict, out: Path) -> dict[str, Path]:
    return {
        "monthly": monthly(r, out), "iv": iv_bar(r, out),
        "woe": woe_profile(r, out, ["n_loan_apps", "n_apps", "education"]),
        "roc": roc(r, out), "deciles": deciles(r, out), "importance": importance(r, out),
    }
