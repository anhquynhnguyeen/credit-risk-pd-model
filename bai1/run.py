"""Chạy toàn bộ Bài I: tính toán, in kết quả, xuất Excel và slide HTML.

    python run.py                       # dùng file dữ liệu mặc định ở thư mục cha
    python run.py --data duong/dan.xlsx
"""
import argparse
from pathlib import Path

import excel_report
import slides
from validation import print_summary, run

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser(description="Kiểm định mô hình PD (Bài I)")
    ap.add_argument("--data", type=Path, default=HERE.parent / "Sample data for validation.xlsx")
    ap.add_argument("--out", type=Path, default=HERE / "output")
    args = ap.parse_args()

    r = run(args.data)
    print_summary(r)
    xlsx = excel_report.build(r, args.out / "Bai1_PD_Validation.xlsx")
    html = slides.build(r, args.out / "Bai1_PD_Validation_slides.html")
    print(f"\nĐã tạo:\n  {xlsx}\n  {html}")


if __name__ == "__main__":
    main()
