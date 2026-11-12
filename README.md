# Credit Risk: Kiểm định & Xây dựng mô hình PD

Case study về rủi ro tín dụng, gồm hai phần bổ trợ nhau:

- **Bài I – Kiểm định (validation)** một mô hình xác suất vỡ nợ (PD) có sẵn.
- **Bài II – Phát triển (development)** một mô hình phân loại khách hàng vay good / bad từ dữ liệu thô.

Bài I trả lời câu hỏi *"một mô hình PD tốt là thế nào và đo bằng gì?"*. Bài II tự xây một mô hình rồi đánh giá nó bằng chính các thước đo đó.

| | Bài I – Kiểm định | Bài II – Phát triển |
|---|---|---|
| Dữ liệu | 3.698 khách hàng: điểm + nhãn | 41.022 hồ sơ vay, ~13% bad |
| Kết quả chính | AUC 0,692 · AR 0,385. **Xếp hạng đúng nhưng PD bị đánh giá thấp ~31%** | Gradient Boosting: **AUC 0,773 · AR 0,547** trên tập test out-of-time, hiệu chuẩn đạt |
| Trình bày | Excel (mọi ô là công thức) + slide | Notebook + code Python + slide |

---

## 1. Tóm tắt đề bài

> Đề gốc không kèm trong repo. Phần dưới đây được diễn đạt lại.

### Bài I – Kiểm định mô hình PD
- **Dữ liệu** (`Sample data for validation.xlsx`): đầu ra của một mô hình phân loại rủi ro, 3.698 bản ghi, gồm 2 cột:
  - Xác suất vỡ nợ, đã được quy đổi sang điểm
  - Nhãn thực tế (good = 0, bad = 1)
- **Yêu cầu:** kiểm định và trình bày kết quả theo 3 phương pháp đánh giá mô hình PD:
  1. Accuracy Ratio / AUROC
  2. Binomial test (1 phía và 2 phía)
  3. Hosmer–Lemeshow test
- **Trọng tâm:** giải thích *ý nghĩa* và *cách đo lường* của từng tiêu chí. Tương quan vỡ nợ giữa các khách hàng có thể bỏ qua hoặc chỉ nêu ngắn gọn.
- **Hình thức:** slide hoặc Excel, các bước xử lý phải đầy đủ và tường minh.

### Bài II – Mô hình dự báo good / bad
- **Dữ liệu** (`data.csv`): bảng phẳng tổng hợp từ 3 nguồn:
  - Nhân khẩu học, tiền tố `de_`: tuổi, giới tính, học vấn, loại hình và thâm niên công việc, thu nhập, tình trạng hôn nhân…
  - Facebook, tiền tố `fb_`: ngày sinh, giới tính, ngày cập nhật, số bạn bè…
  - Điện thoại, tiền tố `ph_`: thông tin thiết bị, thống kê cuộc gọi, số danh bạ, danh sách app đã cài
  - Nhãn `flag_bad` (1 = bad, 0 = good) và thời điểm nộp đơn.
- **Yêu cầu:** phát triển mô hình phân loại, trình bày bằng code và slide. Nội dung cần có:
  - Cách tiếp cận
  - Cách lựa chọn thuật toán
  - Luồng xử lý, từ phát triển đến đánh giá mô hình
  - **Nêu đầy đủ các điểm ra quyết định**

---

## 2. Bài I – Kiểm định mô hình PD

Chi tiết từng bước và công thức: [bai1/README.md](bai1/README.md).

### Cách tiếp cận
1. **Đổi điểm ngược lại thành PD.** Đề nói PD "đã được quy đổi điểm", nên mỗi điểm được gán vào 1 trong 10 hạng của Master Scale. Mỗi hạng có một PD dự báo, từ 27,5% ở hạng 1 xuống 0,1% ở hạng 10.
2. **Tách hai câu hỏi khác nhau.** Ba phương pháp của đề đo hai thứ khác nhau:
   - **Phân biệt (discrimination):** mô hình có xếp khách bad vào nhóm rủi ro cao hơn khách good không? Đo bằng **AUC / AR**.
   - **Hiệu chuẩn (calibration):** con số PD có khớp tỷ lệ vỡ nợ thực tế không? Đo bằng **Binomial** (từng hạng) và **Hosmer–Lemeshow** (toàn danh mục).
3. **Tính hai lần:** một lần bằng công thức Excel để người đọc bấm vào ô là thấy cách tính, một lần bằng Python để đối chiếu.

### Kết quả

| Tiêu chí | Kết quả | Đánh giá |
|---|---|---|
| Phân biệt | AUC 0,692 (KTC 95%: 0,664–0,721) · AR 0,385 | Trung bình, sát ngưỡng 0,7 |
| Thứ tự xếp hạng | Tỷ lệ vỡ nợ thực tế (ODR) giảm đều từ hạng 1 đến 10 | Đạt |
| Hiệu chuẩn từng hạng (Binomial 1 phía) | Bác bỏ ở **8/10 hạng** (hạng 3–10) | Không đạt |
| Hiệu chuẩn toàn danh mục (HL) | HL = 195,4; p ≈ 1,5×10⁻³⁶ | Không đạt |

**Kết luận:** mô hình **xếp hạng đúng thứ tự nhưng đánh giá thấp rủi ro một cách có hệ thống**. PD bình quân là 8,22%, trong khi tỷ lệ vỡ nợ thực tế là 11,87%, tức thấp hơn khoảng 31%. ODR cao hơn PD ở 9/10 hạng.

### Lập luận chính
- **Nên hiệu chuẩn lại, không cần xây lại.** Thứ tự xếp hạng vẫn đúng, chỉ có mức PD bị lệch. Chỉ cần dịch chuyển hoặc co giãn lại PD (recalibration), phần xếp hạng giữ nguyên.
- **Ưu tiên Binomial 1 phía.** Với ngân hàng, rủi ro nằm ở việc mô hình *đánh giá thấp* PD, vì khi đó vốn và dự phòng bị trích thiếu. Kiểm định 2 phía được trình bày kèm để đầy đủ.
- **Hosmer–Lemeshow dùng df = 10, không phải 8.** PD được cố định từ trước, nên đây là kiểm định ngoài mẫu. Bậc tự do k − 2 chỉ áp dụng khi kiểm định trên chính mẫu đã dùng để ước lượng mô hình.
- **AUC và AR là cùng một thông tin**, vì AR = 2·AUC − 1. AR được tính thêm trực tiếp từ đường CAP để kiểm chứng chéo.

### Hạn chế
- Binomial và HL giả định các khách hàng **vỡ nợ độc lập**. Thực tế có tương quan vỡ nợ, nên hai test này khắt khe hơn mức cần. Có thể điều chỉnh bằng mô hình một nhân tố Vasicek. Tuy vậy, với HL ≈ 195, kết luận "không đạt" khó có khả năng thay đổi.
- Chỉ có **một kỳ dữ liệu**, nên chưa kiểm định được độ ổn định theo thời gian và độ ổn định quần thể (PSI).
- Không có thông tin về định nghĩa vỡ nợ, kỳ quan sát hay quần thể phát triển mô hình. Vì vậy chưa xác định được *nguyên nhân* PD bị lệch: do môi trường thay đổi, do quần thể thay đổi, hay do mô hình bị hiệu chuẩn sai từ đầu.

---

## 3. Bài II – Mô hình good / bad

Giải thích nguyên lý và từng bước: [bai2/README.md](bai2/README.md). Notebook chính: [bai2/bai2_notebook.ipynb](bai2/bai2_notebook.ipynb).

### Luồng xử lý
```
Dữ liệu thô ─► Làm sạch ─► Tạo biến ─► Chia train / validation / test (theo thời gian)
           ─► WOE / IV ─► Chọn biến ─► Logistic scorecard  +  Gradient Boosting
           ─► Đánh giá (AUC/AR, KS, PSI, Hosmer–Lemeshow) ─► Chọn mô hình
```

### Các điểm ra quyết định chính
| Quyết định | Lý do |
|---|---|
| **Tạo biến theo góc nhìn người thẩm định.** Ví dụ: đếm số app vay, số app ngân hàng; độ lệch giữa tuổi trên Facebook và tuổi khai báo; tỷ lệ cuộc gọi ngày/đêm | Mô hình không đọc được danh sách 40 tên app. Phải tóm tắt thành tín hiệu có ý nghĩa rủi ro, và chỉ dùng thông tin có tại thời điểm nộp đơn |
| Không đếm app Kredivo khi đếm app vay | App này có trên 98% máy, nhiều khả năng là chính app cho vay, nên không mang thông tin phân biệt |
| **Test out-of-time:** train/validation dùng tháng 1–5 (chia 75/25), test dùng tháng 6–7 | Mô phỏng đúng cách mô hình được dùng thật: chấm điểm cho khách hàng *tương lai* |
| Chia nhóm biến số (≤ 6 nhóm, mỗi nhóm ≥ 5% hồ sơ), giữ biến có IV ≥ 0,02, loại biến có tương quan > 0,6 | Giữ WOE ổn định và bỏ biến trùng thông tin. Các ngưỡng này phổ biến trong thực hành scorecard |
| Loại biến có hệ số **ngược dấu** so với xu hướng WOE | Mô hình phải hợp lý về nghiệp vụ, giải thích được với người dùng và cơ quan quản lý |
| Gradient Boosting: cây 7 lá, ≥ 500 hồ sơ mỗi lá, dừng sớm theo validation | Hạn chế học thuộc dữ liệu |
| Thang điểm: 600 điểm ↔ PD ≈ 9%; cứ +50 điểm thì odds rủi ro giảm một nửa | Cách quy đổi thông dụng, cùng kiểu thang điểm với Bài I |

11 biến được giữ lại. Mạnh nhất là **số app vay trong máy** (IV 0,28): không có app vay thì tỷ lệ bad khoảng 8,6%, có từ 3 app vay trở lên thì khoảng 28,9%.

### Kết quả

| | Logistic (scorecard) | Gradient Boosting |
|---|---|---|
| AUC – train / validation / **test OOT** | 0,734 / 0,743 / **0,729** | 0,826 / 0,784 / **0,773** |
| AR (Gini) trên test OOT | 0,458 | **0,547** |
| KS trên test OOT | 0,347 | **0,406** |
| PSI (train → test) | 0,005 | 0,003 |
| Hosmer–Lemeshow trên test (df = 10, ngưỡng 18,3) | 10,7 · p = 0,38 ✅ | 11,5 · p = 0,32 ✅ |

### Lựa chọn và lập luận
- **Chọn Gradient Boosting làm mô hình chính.** Trên dữ liệu tương lai, AR của nó cao hơn khoảng 0,09. Điểm số ổn định (PSI rất thấp) và PD khớp thực tế (HL đạt). Mô hình này cũng dựa vào cùng nhóm biến với logistic, nên không học các tín hiệu khó giải thích.
- **Giữ Logistic scorecard làm mô hình đối chứng.** Nó minh bạch, giải thích được từng điểm cộng/trừ, và gần như không bị học thuộc (train ≈ test). Đây là phương án thay thế khi cần nêu lý do từ chối cho từng khách hàng.
- **Liên hệ với Bài I:** cả hai mô hình đều đạt Hosmer–Lemeshow, tức PD khớp thực tế. Đây chính là điểm mô hình trong Bài I không đạt.

### Hạn chế
- **Học thuộc vẫn còn:** AUC của Boosting giảm từ 0,826 (train) xuống 0,773 (test). Mức này chấp nhận được vì vẫn tốt hơn logistic, nhưng cần theo dõi.
- **Chưa dò tham số có hệ thống** cho Boosting (grid/Bayesian search) và **chưa có giải thích cho từng khách hàng** (SHAP).
- **Biến từ danh sách app còn đơn giản**, chỉ dựa trên từ khóa. Phân loại app tốt hơn có thể tăng thêm sức phân biệt.
- **Không biết định nghĩa "bad"** (bao nhiêu ngày quá hạn, trong bao lâu), nên không kiểm tra được tính nhất quán của nhãn.
- **Reject inference:** dữ liệu chỉ gồm người đã được duyệt vay, nên mô hình có thể bị lệch khi chấm cho toàn bộ người nộp đơn.
- **Chưa đánh giá tính công bằng** giữa các nhóm khách hàng. Cũng chưa xem xét vấn đề quyền riêng tư khi dùng dữ liệu mạng xã hội và điện thoại.
- **Test chỉ dài 2 tháng.** Cần theo dõi thêm độ ổn định khi có dữ liệu mới.

---

## 4. Cấu trúc repo

```
credit-risk-pd-model/
├── README.md                         # file này
├── Sample data for validation.xlsx   # dữ liệu Bài I
├── data.csv                          # dữ liệu Bài II (~63 MB)
├── Bai1_Bai2_slides.pptx             # slide tổng hợp cả hai bài
├── kiem_tra_nguon.md / .pdf          # kiểm chứng các tài liệu tham khảo của Bài II
├── bai1/                             # Kiểm định PD
│   ├── validation.py                 #   các phép tính kiểm định
│   ├── excel_report.py               #   xuất Excel với công thức thật
│   ├── run.py                        #   chạy toàn bộ
│   ├── bai1_pd_validation.html       #   báo cáo dạng web
│   └── output/                       #   Excel + slide HTML
├── bai2/                             # Phát triển mô hình
│   ├── bai2_notebook.ipynb           #   notebook chính, đã chạy sẵn kết quả
│   ├── bai2_notebook_day_du.ipynb    #   bản mở rộng: KS, HL chi tiết, PSI
│   ├── features.py / woe.py / model.py / charts.py
│   ├── run.py                        #   chạy toàn bộ dạng script
│   └── output/                       #   kết quả, bảng điểm, biểu đồ, slide HTML
└── _cong_cu_slide/                   # script dựng file PowerPoint
```

## 5. Cách chạy

Yêu cầu Python 3.9+. Mỗi bài có môi trường riêng:

```bash
# Bài I
cd bai1 && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python run.py

# Bài II (khoảng 1 phút)
cd bai2 && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python run.py
```

Các file `.html` mở trực tiếp bằng trình duyệt. Bấm **F** để trình chiếu.

## 6. Ghi chú

Dữ liệu đi kèm repo là dữ liệu mẫu của case study, chỉ dùng cho mục đích học tập và minh họa.
