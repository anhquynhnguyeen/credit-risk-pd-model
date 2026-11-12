# Bài II – Mô hình dự báo khách hàng good / bad

## 1. Cấu trúc thư mục

```
credit-risk-pd-model/
├── data.csv                 # dữ liệu đề bài (41.022 hồ sơ)
└── bai2/
    ├── README.md            # file này
    ├── bai2_notebook.ipynb  # NỘP BÀI: toàn bộ code + giải thích, đọc từ trên xuống, đã chạy sẵn kết quả
    ├── bai2_notebook_day_du.ipynb  # bản đầy đủ: thêm KS, Hosmer-Lemeshow chi tiết, PSI
    ├── requirements.txt
    ├── run.py               # chạy toàn bộ dạng script (tạo slide, biểu đồ, file kết quả)
    ├── features.py          # bước 1-2: đọc dữ liệu, làm sạch, tạo biến
    ├── woe.py               # chia nhóm biến, tính WOE / IV
    ├── model.py             # bước 3-6: chia dữ liệu, chọn biến, 2 mô hình, đánh giá
    ├── charts.py            # bước 7: biểu đồ
    ├── slides.py            # bước 8: slide thuyết trình
    └── output/
        ├── Bai2_Model_slides.html     # nộp bài: slide
        ├── performance.csv            # AUC / Gini / KS của 2 mô hình trên 3 tập
        ├── iv_feature_selection.csv   # IV và lý do giữ / loại từng biến
        ├── scorecard.csv              # bảng điểm của mô hình logistic
        ├── summary.json
        └── figures/                   # biểu đồ PNG
```

## 2. Cách chạy

```bash
cd credit-risk-pd-model/bai2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py          # khoảng 1 phút
open output/Bai2_Model_slides.html
```

## 3. Kết quả chính

| | Logistic (scorecard) | Gradient Boosting |
|---|---|---|
| AUC trên tập test (tháng 6–7) | 0,729 | **0,773** |
| AR (Accuracy Ratio) trên tập test | 0,458 | **0,547** |
| Chênh lệch train → test | rất nhỏ | có, nhưng vẫn tốt hơn |
| PD dự báo khớp thực tế (Hosmer-Lemeshow, ngưỡng 18,3) | 10,7 (đạt) | 11,5 (đạt) |

Đề xuất: **Gradient Boosting làm mô hình chính**, Logistic scorecard làm mô hình đối chứng (dùng khi cần giải thích từng điểm số).

Biến mạnh nhất là **số app vay trong máy**: không có app vay thì tỷ lệ bad khoảng 9%, có từ 3 app trở lên thì khoảng 29%.

---

## 4. Giải thích nguyên lý (dễ hiểu)

### 4.1. Bài toán là gì?
Có 41.022 người đã vay tiền. Ta biết ai trả được (good) và ai không trả (bad, khoảng 13%). Ta muốn dạy máy tính nhìn thông tin lúc nộp đơn (tuổi, công việc, điện thoại, Facebook...) để **đoán trước** người mới nộp đơn có khả năng thành bad hay không.

Kết quả của mô hình là một **xác suất (PD)**, ví dụ "người này có 25% khả năng không trả nợ". Đây chính là loại mô hình mà Bài I kiểm định.

### 4.2. Tạo biến: biến dữ liệu thô thành tín hiệu
Máy tính không hiểu được một danh sách 40 tên app. Ta phải tóm tắt nó thành con số có ý nghĩa, ví dụ "có bao nhiêu app vay tiền". Cách nghĩ:
- **Hỏi như người thẩm định:** "Nếu tự xét hồ sơ, mình sẽ để ý điều gì?" Người đang cài nhiều app vay thì có thể đang vay nhiều nơi. Tuổi trên Facebook khác tuổi khai báo thì có thể khai gian.
- **Không dùng thông tin "tương lai":** chỉ dùng những gì biết được tại lúc nộp đơn.

### 4.3. Chia dữ liệu: training, validation và test set

| Tập | Dữ liệu | Dùng để |
|---|---|---|
| **Training set** | 75% hồ sơ tháng 1–5 | Huấn luyện mô hình |
| **Validation set** | 25% hồ sơ tháng 1–5 | So sánh, phát hiện overfitting trong lúc xây mô hình |
| **Test set (out-of-time)** | Toàn bộ hồ sơ tháng 6–7 | Đánh giá cuối cùng trên dữ liệu mô hình chưa từng thấy |

Vì sao test set là 2 tháng cuối thay vì chia ngẫu nhiên? Khi đem dùng thật, mô hình luôn chấm cho khách hàng *trong tương lai*. Test trên các tháng sau mô phỏng đúng tình huống đó, và phát hiện được nếu hành vi khách hàng thay đổi theo thời gian.

### 4.4. WOE và IV: biến nào có ích?
Với mỗi biến, ta chia khách thành vài nhóm rồi xem **tỷ lệ bad của từng nhóm**:

| Số app vay | 0 | 1 | 2 | 3+ |
|---|---|---|---|---|
| Tỷ lệ bad | 8,6% | 10,9% | 14,1% | 28,9% |

Các nhóm càng khác nhau thì biến càng có ích.
- **WOE** là "điểm rủi ro" của mỗi nhóm so với trung bình: dương là an toàn hơn, âm là rủi ro hơn.
- **IV** cộng tất cả các khác biệt đó thành một con số cho cả biến: dưới 0,02 thì vô dụng, 0,02–0,1 yếu, 0,1–0,3 trung bình.

Ta giữ biến có IV ≥ 0,02. Ta cũng bỏ biến trùng thông tin với biến khác (tương quan cao), và biến cho kết quả ngược với logic (ví dụ mô hình nói "gọi điện nhiều thì rủi ro hơn", trong khi dữ liệu từng nhóm nói ngược lại).

### 4.5. Hai mô hình
- **Logistic regression (scorecard)** giống một **bảng cộng điểm**. Mỗi đặc điểm cho một số điểm, ví dụ "0 app vay: +95 điểm", "3 app vay trở lên: −44 điểm". Cộng lại được tổng điểm, điểm càng cao càng an toàn. Ngân hàng rất thích vì giải thích được rõ ràng tại sao khách bị từ chối. Đây cũng chính là kiểu điểm số trong Bài I.
- **Gradient Boosting** giống **một hội đồng gồm hàng trăm người chấm nhỏ**. Mỗi người chấm là một cây hỏi vài câu kiểu "có hơn 2 app vay không? thâm niên dưới 1 năm không?". Người chấm sau tập trung sửa các ca mà người trước đoán sai. Cách này mạnh hơn vì bắt được các kết hợp (ví dụ nhiều app vay *và* ít cuộc gọi) nhưng khó giải thích hơn. Nó cũng dễ **học thuộc** dữ liệu, nên ta giới hạn cây nhỏ, mỗi nhánh tối thiểu 500 hồ sơ, và dừng sớm khi điểm validation không tăng nữa.

### 4.6. Đánh giá: dùng lại kiến thức Bài I
- **AUC / AR:** mô hình xếp good và bad đúng thứ tự tới đâu (xem Bài I).
- **KS:** khoảng cách lớn nhất giữa "% bad đã bắt" và "% good bị từ chối nhầm" khi trượt ngưỡng. Càng lớn càng tốt; 0,3–0,4 là khá với mô hình tín dụng.
- **Học thuộc (overfitting):** so điểm trên train với test. Chênh nhiều nghĩa là mô hình "học vẹt".
- **PSI:** phân phối điểm có bị dịch chuyển giữa lúc xây và lúc dùng không. Dưới 0,1 là ổn định.
- **Hosmer-Lemeshow:** PD dự báo có khớp tỷ lệ bad thực tế không (Bài I). Ở bài này cả hai mô hình đều đạt, khác với mô hình trong Bài I.

### 4.7. Chọn mô hình
Boosting tốt hơn khoảng 0,09 AR trên dữ liệu tương lai, vẫn ổn định và hiệu chuẩn tốt, và dựa vào cùng các biến với logistic. Vì vậy ta chọn Boosting. Logistic được giữ làm đối chứng và là phương án thay thế khi cần giải thích từng điểm.

---

## 5. Các điểm ra quyết định (đề yêu cầu nêu đầy đủ)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | Bỏ `de_accomodation_type`, `ph_country_code` | Gần như chỉ có một giá trị |
| 2 | Bỏ app Kredivo khi đếm app vay | Có trên 98% máy, nhiều khả năng là chính app cho vay |
| 3 | Test theo thời gian (tháng 6–7) | Mô phỏng việc dùng mô hình cho khách hàng tương lai |
| 4 | Chia biến số thành tối đa 6 nhóm, mỗi nhóm ≥ 5% hồ sơ | WOE ổn định, không quá chi tiết |
| 5 | Ngưỡng IV 0,02; tương quan 0,6 | Ngưỡng phổ biến trong sách scorecard |
| 6 | Loại biến có hệ số ngược dấu | Mô hình phải hợp lý về nghiệp vụ |
| 7 | Boosting: 7 lá, ≥ 500 hồ sơ/lá, dừng sớm | Hạn chế học thuộc |
| 8 | Chọn Boosting làm mô hình chính | AR test cao hơn 0,09, ổn định, hiệu chuẩn tốt |
| 9 | Thang điểm 600 ↔ PD ≈ 9%, +50 điểm thì rủi ro giảm một nửa | Cách quy đổi điểm thông dụng, gần với thang điểm Bài I |

## 6. Hạn chế (nên nói thẳng khi phỏng vấn)
- Biến từ danh sách app còn đơn giản (dựa trên từ khóa).
- Chưa dò tham số có hệ thống cho Boosting.
- Chưa có giải thích cho từng khách hàng (SHAP).
- Không biết "bad" được định nghĩa thế nào (bao nhiêu ngày quá hạn).
- Dữ liệu chỉ gồm người đã được duyệt vay (reject inference).
- Chưa kiểm tra tính công bằng giữa các nhóm.

## 7. Câu hỏi phỏng vấn có thể gặp
- Vì sao chia theo thời gian mà không chia ngẫu nhiên?
- WOE và IV là gì? Vì sao chọn ngưỡng 0,02?
- Vì sao loại biến có hệ số ngược dấu?
- Boosting học thuộc tới mức nào? Làm sao biết vẫn dùng được?
- Nếu ngân hàng yêu cầu giải thích lý do từ chối thì chọn mô hình nào?
- Bạn sẽ chọn ngưỡng duyệt như thế nào?
