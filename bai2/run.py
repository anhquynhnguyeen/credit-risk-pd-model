"""Chạy toàn bộ Bài II: tạo biến → huấn luyện → đánh giá → biểu đồ → slide.

    python run.py
"""
from gettext import install
import json
from pathlib import Path
import charts
import features as F
import model
import slides
import matplotlib

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"


def main() -> None:
    print("1. Đọc dữ liệu và tạo biến...")
    df = F.build_features(F.load_raw(HERE.parent / "data.csv"))

    print("2. Huấn luyện và đánh giá 2 mô hình...")
    r = model.run(df)

    print("\nHiệu quả (AUC / Gini / KS):")
    print(r["perf"].round(3).to_string(index=False))
    print("\nBiến trong scorecard:", r["selected"])
    print("Loại vì hệ số ngược dấu:", r["sign_dropped"])
    print("PSI train → test:", {k: round(v, 4) for k, v in r["psi"].items()})
    print("Hosmer-Lemeshow trên test:", {k: round(v["HL"], 1) for k, v in r["hl"].items()})

    print("2b. So sánh chia theo thời gian với chia ngẫu nhiên (khoảng 1 phút)...")
    r["split_check"] = model.compare_splits(df)
    print(r["split_check"]["random"].round(3).describe().loc[["mean", "min", "max"]].to_string())

    print("\n3. Vẽ biểu đồ và lưu kết quả...")
    OUT.mkdir(exist_ok=True)
    figs = charts.all_charts(r, OUT / "figures")
    r["perf"].to_csv(OUT / "performance.csv", index=False)
    r["iv_log"].to_csv(OUT / "iv_feature_selection.csv")
    r["scorecard"].to_csv(OUT / "scorecard.csv", index=False)
    summary = {
        "performance": r["perf"].to_dict(orient="records"), "selected": r["selected"],
        "psi": r["psi"], "hosmer_lemeshow": r["hl"],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    deck = slides.build(r, figs, OUT / "Bai2_Model_slides.html")
    print(f"\nĐã tạo:\n  {deck}\n  {OUT / 'scorecard.csv'}\n  {OUT / 'figures'}")


if __name__ == "__main__":
    main()
