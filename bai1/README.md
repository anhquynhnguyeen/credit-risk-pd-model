# Bài I – Kiểm định mô hình PD

Kiểm định kết quả một mô hình phân loại rủi ro (3.698 khách hàng, điểm tín dụng + nhãn good/bad) theo 3 phương pháp:
- Accuracy Ratio / AUROC
- Binomial test (1 phía và 2 phía)
- Hosmer–Lemeshow test

## 1. Cấu trúc thư mục

```
credit-risk-pd-model/
├── Sample data for validation.xlsx    # dữ liệu đề bài (giữ nguyên)
└── bai1/
    ├── README.md                      # file này
    ├── requirements.txt               # thư viện cần cài
    ├── run.py                         # chạy toàn bộ: tính toán + xuất Excel + xuất slide
    ├── validation.py                  # các phép tính kiểm định (Python làm chuẩn)
    ├── excel_report.py                # tạo file Excel có công thức thật
    ├── slides.py                      # tạo slide thuyết trình .html
    └── output/
        ├── Bai1_PD_Validation.xlsx         # nộp bài: Excel trình bày từng bước
        └── Bai1_PD_Validation_slides.html  # nộp bài: slide tóm tắt
```

## 2. Cách chạy

```bash
cd credit-risk-pd-model/bai1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Kết quả được in ra màn hình, đồng thời hai file trong `output/` được tạo lại.

- **Excel:** mở bằng Microsoft Excel. File chỉ chứa công thức, Excel sẽ tự tính khi mở. Nếu Excel hỏi có lưu thay đổi không thì chọn Lưu.
- **Slide:** mở file `.html` bằng Chrome/Safari.
  - Bấm **F** (hoặc nút "Trình chiếu") để chiếu từng slide, dùng phím ← → để chuyển.
  - Bấm Cmd+P và chọn "Lưu dưới dạng PDF" (khổ ngang) nếu muốn nộp bản PDF.

## 3. Dữ liệu và cách hiểu đề

Sheet dữ liệu có 2 phần:

| Cột | Nội dung |
|---|---|
| A `Điểm` | Điểm tín dụng (431–917). **Điểm cao = rủi ro thấp.** |
| B `Good=0/Bad=1` | Nhãn thực tế (439 bad, tỷ lệ 11,87%) |
| C–E Master Scale | 10 hạng: khoảng điểm và PD dự báo của mỗi hạng (27,5% ở hạng 1 → 0,1% ở hạng 10) |

Đề nói "xác suất vỡ nợ đã được quy đổi điểm", nên **bước đầu tiên là đổi điểm ngược lại thành hạng và PD** theo Master Scale.

Ba phương pháp trả lời hai câu hỏi khác nhau:

| Câu hỏi | Phương pháp |
|---|---|
| **Phân biệt (discrimination):** mô hình có xếp khách bad vào nhóm rủi ro cao hơn khách good không? | AUC / AR |
| **Hiệu chuẩn (calibration):** con số PD có khớp với tỷ lệ vỡ nợ thực tế không? | Binomial (từng hạng), Hosmer–Lemeshow (toàn danh mục) |

Một mô hình có thể xếp hạng tốt nhưng PD vẫn sai. Bài này là đúng trường hợp đó.

## 4. Các bước tính và ý nghĩa

### Bước 1 – Gán hạng và PD (sheet `Data`)
- Hạng = `MATCH(điểm, cận dưới của các hạng, 1)`
- PD = `INDEX(PD, hạng)`
- Cận dưới của mỗi hạng = cận trên của hạng trước + 1, vì điểm là số nguyên.

### Bước 2 – Bảng tổng hợp theo hạng (sheet `1_Bang_theo_hang`)
Với mỗi hạng tính:
- n = số khách
- d = số bad
- ODR = d/n
- E = n × PD (số bad mà mô hình kỳ vọng)

Nhận xét:
- ODR giảm đều từ hạng 1 đến 10, tức thứ tự xếp hạng đúng.
- ODR cao hơn PD ở 9/10 hạng.
- PD bình quân là 8,22%, trong khi ODR là 11,87%.

### Bước 3 – AUC / Accuracy Ratio (sheet `2_AUC_AR`)
- **AUC** = xác suất một khách bad ngẫu nhiên bị chấm rủi ro hơn một khách good ngẫu nhiên.
- **AR (Gini)** = 2 × AUC − 1. AR cũng tính được trực tiếp từ đường CAP: AR = (diện tích CAP − 0,5) / (0,5 − DR/2).
- Cách tính: xếp hạng từ rủi ro nhất đến an toàn nhất, lũy kế %bad, %good, %khách, rồi tính diện tích bằng quy tắc hình thang.
- Kết quả:
  - Theo điểm gốc: **AUC = 0,692** (khoảng tin cậy 95%: 0,664–0,721), **AR = 0,385**.
  - Theo 10 hạng: AUC = 0,695.
- Đánh giá: khả năng phân biệt trung bình, sát ngưỡng 0,7.

### Bước 4 – Binomial test (sheet `3_Binomial`)
- **1 phía:** H₀: PD thật ≤ PD dự báo. p = P(X ≥ d) với X ~ Bin(n, PD).
  - Đây là hướng ngân hàng quan tâm nhất: mô hình có đánh giá thấp rủi ro không.
- **2 phía:** H₀: PD thật = PD dự báo. p = 2 × min(P(X ≤ d), P(X ≥ d)).
- Cột "Ngưỡng d tối đa (95%)" = `BINOM.INV(n, PD, 0,95)`. Nếu d vượt ngưỡng này thì bác bỏ.
- Có thêm cột đèn: Xanh / Vàng / Đỏ ứng với p ≥ 5% / 1–5% / < 1%.
- Kết quả: **8/10 hạng (hạng 3–10) bị bác bỏ**, PD thấp hơn thực tế. Hạng 1 ngược lại: PD hơi cao hơn thực tế.

### Bước 5 – Hosmer–Lemeshow (sheet `4_Hosmer_Lemeshow`)
- HL = Σ (d − n·PD)² / (n·PD·(1 − PD)), so với phân phối χ².
- df = 10, vì PD đã cố định từ trước (kiểm định ngoài mẫu). df = k − 2 chỉ dùng khi kiểm định trên chính mẫu phát triển mô hình.
- Kết quả: **HL = 195,4; p ≈ 1,5×10⁻³⁶**, nên bác bỏ mạnh giả thuyết PD khớp thực tế.

## 5. Kết luận

| Tiêu chí | Kết quả | Đánh giá |
|---|---|---|
| Phân biệt | AUC 0,692 · AR 0,385 | Trung bình, chấp nhận được |
| Thứ tự xếp hạng | ODR giảm đều | Đạt |
| Hiệu chuẩn từng hạng | Bác bỏ 8/10 hạng | Không đạt |
| Hiệu chuẩn toàn danh mục | HL 195,4 | Không đạt |

**Mô hình xếp hạng đúng nhưng PD bị đánh giá thấp có hệ thống (khoảng 31%).**

Khuyến nghị:
- **Hiệu chuẩn lại** (recalibration) thay vì xây lại mô hình.
- Kiểm định lại out-of-time.
- Xem xét bổ sung biến để cải thiện AUC.

## 6. Giả định và hạn chế (đề cho phép nêu ngắn gọn)
- Binomial và HL giả định các khách hàng **vỡ nợ độc lập**. Thực tế có tương quan vỡ nợ, nên các test này khắt khe hơn mức cần. Có thể điều chỉnh bằng mô hình một nhân tố Vasicek.
- Chỉ có một kỳ dữ liệu. Cần thêm kiểm định theo thời gian và độ ổn định quần thể (PSI).

## 7. Gợi ý cách trình bày khi nộp bài

Đề cho phép slide hoặc Excel. Gợi ý nộp **cả hai**:
1. **Excel (`Bai1_PD_Validation.xlsx`)** là bằng chứng "các bước xử lý tường minh".
   - Mọi số liệu đều là công thức, người chấm bấm vào ô là thấy cách tính.
   - Cột màu xám "Python" dùng để đối chiếu.
   - Sheet `0_Tom_tat` là trang đầu tiên.
2. **Slide (`..._slides.html`, hoặc in ra PDF)** dùng để thuyết trình, gồm 11 slide:
   - Đề bài → quy trình → bảng theo hạng → AUC → vì sao dùng AUC/ROC → Binomial → HL → hạn chế → kết luận → phụ lục công thức.
3. Khi thuyết trình, mỗi phương pháp nên nói theo 3 ý: **đo cái gì → kết quả → ý nghĩa nghiệp vụ**. Đề nhấn mạnh phần giải thích ý nghĩa.

Câu hỏi người phỏng vấn có thể hỏi:
- Vì sao df của HL là 10 mà không phải 8?
- Tại sao dùng kiểm định 1 phía?
- Tương quan vỡ nợ ảnh hưởng thế nào đến kết quả?
- Nên hiệu chuẩn lại mô hình bằng cách nào?
- AUC và AR khác nhau ra sao?
