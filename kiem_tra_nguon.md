# Kiểm tra nguồn tài liệu tham khảo (Bài II) — không nộp

Số [1]–[11] theo danh sách "Tài liệu tham khảo" ở cuối notebook `bai2_notebook.ipynb` (cập nhật 23/10/2026).

## Tóm tắt

- Notebook **chỉ giữ 11 nguồn đã kiểm chứng được nội dung**:
    - **Đọc toàn văn:** [2] Delamaire, [3] Basel WP14, [4] ISLR, [5] ESL, [7] LightGBM, [10] Lessmann, [11] SHAP
    - **Đọc abstract:** [6] Friedman, [8] Hanley & McNeil, [9] Kaufman
    - **Qua nguồn thứ cấp:** [1] Siddiqi (qua [2] Delamaire)
- **Đã bỏ 4 nguồn** vì không kiểm chứng được nội dung, hoặc ý của chúng đã có nguồn khác xác nhận: Thomas, Anderson, Sobehart, Hosmer.
- Cả 11 nguồn đều đã được kiểm tra **có thật** qua Crossref / OpenAlex / bis.org.

## Cách tự kiểm tra một nguồn

1. **Mở nguồn** bằng link bên dưới. Nguồn ghi "miễn phí" mở được toàn văn.
2. **Ctrl+F các từ khóa tiếng Anh** ghi ở mỗi nguồn.
3. **Đọc đoạn chứa từ khóa:** có nói đúng ý "Dẫn cho ý" không?
4. Nếu thấy chỗ nào không khớp, gửi Claude ảnh chụp đoạn đó để sửa.

## Từng nguồn

### [1] Siddiqi (2006), *Credit Risk Scorecards* — ⚠️ qua nguồn thứ cấp

- **Dẫn cho ý:** WOE/IV là công cụ xây scorecard (mục 4); ngưỡng IV (4.3 Quy tắc 1); dấu của biến phải đúng logic (4.3 Quy tắc 3); có thể đổi logistic thành scorecard (mục 5)
- **Kiểm chứng:** không truy cập được sách (trả phí). Các ý trên được xác nhận qua [2] Delamaire (2012, tr. 152), có ghi "(Siddiqi, 2006)".
- **Lưu ý:** cách đổi điểm PDO (600 điểm, thêm 50 điểm thì odds gấp đôi) **không** gắn nguồn, vì không tìm được nguồn xác nhận. Ngưỡng 0,5 ghi là "quy ước kinh nghiệm".

### [2] Delamaire (2012), luận án tiến sĩ, University of Birmingham — ✅ toàn văn (miễn phí)

- **Mở ở đâu:** http://etheses.bham.ac.uk/3344/
- **Dẫn cho ý:** ngưỡng IV và dấu của biến (cùng [1]); reject inference (Hạn chế)
- **Từ khóa:** `Siddiqi, 2006`, `unpredictive`, `logical sign`, `Reject inference`
- **Kết quả:**
    - Tr. 152: "Results (Siddiqi, 2006): less than 0,02: unpredictive; 0,02 to 0,1: weak; 0,1 to 0,3: medium; 0,3+: strong" (bản PDF in lỗi "0,002" ở dòng đầu).
    - Tr. 152: "[WOE] should follow a logical order and the associated sign should correspond to the logical sign (Siddiqi, 2006)".
    - Tr. 187, mục 4.2.7 "Reject inference": hệ thống chỉ xây trên khách đã được duyệt thì bị lệch.

### [3] Basel Committee WP 14 (2005) — ✅ toàn văn (miễn phí)

- **Mở ở đâu:** https://www.bis.org/publ/bcbs_wp14.htm
- **Dẫn cho ý:** kiểm tra trên dữ liệu độc lập (mục 3); AR và ROC đo khả năng phân biệt (6.1); Hosmer-Lemeshow (6.2)
- **Từ khóa:** `out-of-sample`, `Accuracy Ratio`, `Receiver Operating Characteristic`, `Hosmer`
- **Kết quả:**
    - Tr. 36: "the discriminatory power should be tested not only in the development dataset but also in an independent dataset (out-of-sample validation)".
    - Có mục về Accuracy Ratio, ROC, Binomial test, Hosmer-Lemeshow test (mục lục, từ tr. 36).
    - Không có "out-of-time" cho mô hình PD (chỉ có ở tr. 79, cho mô hình LGD), nên notebook không dẫn [3] cho ý "chia theo thời gian".

### [4] James và cộng sự (2021), *An Introduction to Statistical Learning*, 2nd ed. — ✅ toàn văn (miễn phí)

- **Mở ở đâu:** https://www.statlearning.com
- **Dẫn cho ý:** đa cộng tuyến (4.3 Quy tắc 2); logistic regression ước lượng bằng maximum likelihood (mục 5); boosting học từ từ (mục 5)
- **Từ khóa:** `collinearity`, `maximum likelihood`, `boosting`
- **Kết quả:** mục 3.3.3 "Potential Problems" có ý "6. Collinearity" (tr. 93); mục 4.3 logistic regression, "maximum likelihood" (tr. 135); mục 8.2.3 "Boosting" (tr. 345).

### [5] Hastie, Tibshirani & Friedman (2009), *The Elements of Statistical Learning*, 2nd ed. — ✅ toàn văn (miễn phí)

- **Mở ở đâu:** tìm "Elements of Statistical Learning pdf" (trang của Hastie)
- **Dẫn cho ý:** "gradient" = hướng giảm sai số nhanh nhất (mục 5); early stopping (5.2)
- **Từ khóa:** `steepest descent`, `validation sample`, `early stopping`
- **Kết quả:** mục 10.10.1 "Steepest Descent" (gradient boosting); chọn số cây M trên validation sample, "analogous to the early stopping strategy".

### [6] Friedman (2001), *Annals of Statistics* 29(5) — ✅ abstract

- **Mở ở đâu:** https://doi.org/10.1214/aos/1013203451
- **Dẫn cho ý:** "gradient" = hướng giảm sai số nhanh nhất (mục 5)
- **Kết quả (abstract):** "A connection is made between stagewise additive expansions and steepest-descent minimization. A general gradient descent 'boosting' paradigm is developed".

### [7] Ke và cộng sự (2017), LightGBM, NeurIPS — ✅ toàn văn (miễn phí)

- **Mở ở đâu:** tìm tên bài trên papers.nips.cc
- **Dẫn cho ý:** chia giá trị thành histogram để chạy nhanh (mục 5)
- **Từ khóa:** `histogram`
- **Kết quả:** bài mô tả thuật toán histogram-based (tr. 2).

### [8] Hanley & McNeil (1982), *Radiology* 143(1) — ✅ abstract

- **Mở ở đâu:** https://doi.org/10.1148/radiology.143.1.7063747
- **Dẫn cho ý:** AUC = xác suất một khách bad bị chấm rủi ro hơn một khách good (6.1)
- **Kết quả (abstract):** "the area represents the probability that a randomly chosen diseased subject is (correctly) rated or ranked with greater suspicion than a randomly chosen non-diseased subject".

### [9] Kaufman và cộng sự (2012), *ACM TKDD* 6(4) — ✅ abstract

- **Mở ở đâu:** https://doi.org/10.1145/2382577.2382579
- **Dẫn cho ý:** rò rỉ dữ liệu (4.3, ý IV > 0,5)
- **Kết quả (abstract):** "leakage is the introduction of information about the data mining target that should not be legitimately available to mine from". Ví dụ "số ngày quá hạn" là của bài làm, không phải của bài báo.

### [10] Lessmann và cộng sự (2015), *EJOR* 247(1) — ✅ toàn văn (preprint miễn phí)

- **Mở ở đâu:** https://doi.org/10.1016/j.ejor.2015.05.030 (preprint trên lirias.kuleuven.be)
- **Dẫn cho ý:** nhiều thuật toán, nhất là ensemble, chính xác hơn logistic regression, vốn là chuẩn của ngành (mục 5)
- **Từ khóa:** `industry standard`, `heterogeneous ensembles`
- **Kết quả:** "several classifiers predict credit risk significantly more accurately than the industry standard LR. Especially heterogeneous ensembles classifiers perform well". Bài **không** nói logistic phổ biến vì dễ giải thích, nên ý đó trong notebook không gắn nguồn.

### [11] Lundberg & Lee (2017), SHAP, NeurIPS — ✅ toàn văn (miễn phí)

- **Mở ở đâu:** https://arxiv.org/abs/1705.07874
- **Dẫn cho ý:** SHAP giải thích dự báo của từng khách (Hạn chế)
- **Từ khóa:** `SHAP`

## Các nguồn đã bỏ

- **Thomas, Crook & Edelman (2017):** không đọc được. Ý "reject inference" chuyển sang [2] Delamaire (tr. 187).
- **Anderson (2007):** abstract chỉ nói chung về xây scorecard, không nhắc WOE/IV. Ý "WOE/IV là công cụ chuẩn" đã có [1][2].
- **Sobehart, Keenan & Stein (2000):** không đọc được, và chưa tìm được nguồn thứ cấp cho ý "walk-forward". Câu ở mục 3 giờ chỉ dẫn [3] cho ý "kiểm tra trên dữ liệu độc lập".
- **Hosmer, Lemeshow & Sturdivant (2013):** không đọc được. Ý "maximum likelihood" đã có [4]; ý Hosmer-Lemeshow test đã có [3].
- Trước đó đã bỏ Yurdakul & Naranjo, Frisch & Waugh, Lovell vì notebook chính không còn dẫn. Ba nguồn này vẫn còn trong bản đầy đủ `bai2_notebook_day_du.ipynb` (đã kiểm chứng qua abstract).

## Ghi chú

- Slide "Tài liệu tham khảo" cũng còn 11 nguồn, nhưng xếp theo nhóm nên số thứ tự khác notebook.
