"""Bước 8: slide thuyết trình Bài II (một file .html, ảnh nhúng sẵn, không cần internet).

Mở bằng trình duyệt; bấm F để trình chiếu, ← → để chuyển slide; Cmd/Ctrl+P để lưu PDF.
"""
from __future__ import annotations

import base64
from pathlib import Path

from charts import label


def vn(x: float, d: int = 2) -> str:
    return f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x: float, d: int = 1) -> str:
    return vn(100 * x, d) + "%"


def img(path: Path, alt: str) -> str:
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f'<img src="data:image/png;base64,{data}" alt="{alt}">'


def _perf_table(r: dict) -> str:
    rows = "".join(
        f"<tr><td>{x['Mô hình']}</td><td>{x['Tập']}</td><td>{vn(x['AUC'], 3)}</td>"
        f"<td>{vn(x['Gini'], 3)}</td></tr>"
        for _, x in r["perf"].iterrows())
    return ("<table><thead><tr><th>Mô hình</th><th>Tập</th><th>AUC</th><th>AR</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>")


def _scorecard_sample(r: dict, var: str) -> str:
    t = r["scorecard"].query("`Biến` == @var")
    rows = "".join(f"<tr><td>{x['Nhóm']}</td><td>{x['Số hồ sơ']:,}</td><td>{pct(x['Tỷ lệ bad'])}</td>"
                   f"<td>{vn(x['WOE'], 2)}</td><td><b>{x['Điểm']}</b></td></tr>" for _, x in t.iterrows())
    return ("<table class='compact'><thead><tr><th>Nhóm</th><th>Số hồ sơ</th><th>Tỷ lệ bad</th><th>WOE</th>"
            f"<th>Điểm</th></tr></thead><tbody>{rows}</tbody></table>")


def _split_table(r: dict) -> str:
    sc = r["split_check"]
    rows = "".join(
        f"<tr><td>{m}</td><td><b>{vn(sc['time'][m], 3)}</b></td>"
        f"<td>{vn(sc['random'][m].mean(), 3)}</td><td>{vn(sc['random'][m].min(), 3)} – {vn(sc['random'][m].max(), 3)}</td></tr>"
        for m in sc["time"])
    return ("<table class='compact'><thead><tr><th>AUC trên test set</th><th>Theo thời gian</th>"
            "<th>Ngẫu nhiên (TB 5 lần)</th><th>Ngẫu nhiên (thấp – cao)</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>")


def _no_fb_table(r: dict) -> str:
    s = r["split_check"]["no_fb_by_month"]
    head = "".join(f"<th>T{int(m[-2:])}</th>" for m in s.index)
    cells = "".join(f"<td>{pct(v, 0)}</td>" for v in s)
    return f"<table class='compact'><thead><tr>{head}</tr></thead><tbody><tr>{cells}</tr></tbody></table>"


def slides(r: dict, figs: dict) -> list[tuple[str, str]]:
    sets = r["sets"]
    n_all = sum(len(v) for v in sets.values())
    bad_all = sum(v["flag_bad"].sum() for v in sets.values())
    perf = r["perf"].set_index(["Mô hình", "Tập"])
    lr_t, gb_t = perf.loc[("Logistic (scorecard)", "Test OOT")], perf.loc[("Gradient Boosting", "Test OOT")]
    gb_tr = perf.loc[("Gradient Boosting", "Train")]
    lr_tr = perf.loc[("Logistic (scorecard)", "Train")]
    sel = ", ".join(label(c) for c in r["selected"])
    hl_lr, hl_gb = r["hl"]["Logistic (scorecard)"], r["hl"]["Gradient Boosting"]
    loan = r["binners"]["n_loan_apps"].table

    return [
        ("", f"""
<div class="cover">
  <p class="kicker">Bài test ứng viên · Bài II</p>
  <h1>Mô hình dự báo khách hàng good / bad</h1>
  <p class="lead">Từ dữ liệu nhân khẩu học, điện thoại và Facebook đến một mô hình có thể dùng để chấm điểm</p>
  <p class="muted">{vn(n_all, 0)} hồ sơ vay · 01/2018 – 07/2018 · Python (pandas, scikit-learn)</p>
</div>"""),

        ("Bài toán và dữ liệu", f"""
<div class="two">
  <div>
    <div class="tiles">
      <div class="tile"><b>{vn(n_all, 0)}</b><span>hồ sơ vay</span></div>
      <div class="tile warn"><b>{pct(bad_all / n_all)}</b><span>tỷ lệ bad</span></div>
    </div>
    <p><b>Mục tiêu:</b> dự báo xác suất một người nộp đơn trở thành khách hàng bad (<code>flag_bad = 1</code>).</p>
    <p><b>3 nguồn dữ liệu (20 cột):</b></p>
    <ul><li><b>de_</b>: tuổi, giới tính, lương, công việc, học vấn, hôn nhân...</li>
    <li><b>ph_</b>: danh bạ, thiết bị, thống kê cuộc gọi (JSON), danh sách app</li>
    <li><b>fb_</b>: giới tính, ngày sinh, ngày cập nhật, tình trạng quan hệ</li></ul>
    <p class="note">Mã vùng điện thoại 99,9% là "id", nên dữ liệu nhiều khả năng đến từ một công ty cho vay qua app ở Indonesia.</p>
  </div>
  <div>{img(figs['monthly'], 'Số hồ sơ và tỷ lệ bad theo tháng')}
  <p class="note">Tỷ lệ bad dao động 11–15% theo tháng. Dữ liệu có thứ tự thời gian, nên cần kiểm tra mô hình trên các tháng sau.</p></div>
</div>"""),

        ("Luồng xử lý", """
<ol class="flow">
  <li><b>Khám phá dữ liệu</b><span>Thiếu dữ liệu, phân phối, tỷ lệ bad theo tháng và theo nhóm</span></li>
  <li><b>Làm sạch + tạo biến</b><span>Tách JSON, đếm app, kiểm tra độ nhất quán FB với thông tin khai báo</span></li>
  <li><b>Chia dữ liệu theo thời gian</b><span>Tháng 1–5 để xây mô hình, tháng 6–7 để kiểm tra</span></li>
  <li><b>Chọn biến bằng IV</b><span>Loại biến yếu, trùng lặp, ngược dấu</span></li>
  <li><b>Hai mô hình</b><span>Logistic scorecard (dễ giải thích) và Gradient Boosting (mạnh hơn)</span></li>
  <li><b>Đánh giá + chọn</b><span>AUC, PD dự báo có khớp thực tế không, mô hình dựa vào biến nào</span></li>
</ol>
<p class="note">Mỗi bước có một điểm ra quyết định, được trình bày ở các slide sau.</p>"""),

        ("Làm sạch dữ liệu và tạo biến", """
<table class="compact"><thead><tr><th>Dữ liệu gốc</th><th>Xử lý / biến mới</th><th>Lý do</th></tr></thead><tbody>
<tr><td>de_accomodation_type, ph_country_code</td><td>Bỏ</td><td>Gần như chỉ một giá trị, không có thông tin</td></tr>
<tr><td>de_num_friends = −1, lương = 0</td><td>Coi là thiếu dữ liệu</td><td>Giá trị không hợp lý</td></tr>
<tr><td>de_monthly_salary</td><td>log(lương)</td><td>Phân phối lệch phải mạnh</td></tr>
<tr><td>Hôn nhân 3–4, công việc 4</td><td>Gộp nhóm</td><td>Nhóm quá ít hồ sơ, tỷ lệ bad không ổn định</td></tr>
<tr><td>de_date_joined</td><td>Tháng (để chia tập), giờ, ngày trong tuần</td><td>Hành vi nộp đơn</td></tr>
<tr><td>ph_app_list</td><td>Tổng số app, số app vay, số app ngân hàng, số app game</td><td>Nhu cầu vay nhiều nơi là dấu hiệu rủi ro; bỏ app Kredivo (có trên 98% máy)</td></tr>
<tr><td>ph_call_log_stats (JSON)</td><td>Tổng cuộc gọi, % gọi đến/đi ngày/đêm, tổng thời lượng</td><td>Mức độ hoạt động xã hội</td></tr>
<tr><td>ph_other_device_info</td><td>Hãng điện thoại (8 hãng phổ biến + khác)</td><td>Đại diện thu nhập</td></tr>
<tr><td>fb_dob, fb_gender</td><td>Lệch tuổi FB với tuổi khai báo; giới tính FB có khớp không</td><td>Dấu hiệu khai báo sai</td></tr>
<tr><td>fb_last_updated_date</td><td>Số ngày từ lần cập nhật FB đến lúc nộp đơn</td><td>0,2% cập nhật sau ngày nộp đơn → đặt về 0 để tránh dùng thông tin "tương lai"</td></tr>
</tbody></table>"""),

        ("Chia dữ liệu: vì sao theo thời gian?", f"""
<div class="two">
  <div>
    <table class="compact"><thead><tr><th>Tập</th><th>Thời gian</th><th>Số hồ sơ</th><th>Tỷ lệ bad</th><th>Dùng để</th></tr></thead><tbody>
    <tr><td>Train</td><td>T1–T5 (75%)</td><td>{vn(len(sets['Train']), 0)}</td><td>{pct(sets['Train']['flag_bad'].mean())}</td><td>Học mô hình</td></tr>
    <tr><td>Validation</td><td>T1–T5 (25%)</td><td>{vn(len(sets['Validation']), 0)}</td><td>{pct(sets['Validation']['flag_bad'].mean())}</td><td>So sánh, kiểm tra học thuộc</td></tr>
    <tr><td>Test OOT</td><td>T6–T7</td><td>{vn(len(sets['Test OOT']), 0)}</td><td>{pct(sets['Test OOT']['flag_bad'].mean())}</td><td>Đánh giá cuối cùng</td></tr>
    </tbody></table>
  </div>
  <div>
    <p><b>Quyết định:</b> giữ riêng 2 tháng cuối làm tập test (out-of-time), thay vì chia ngẫu nhiên.</p>
    <p>Khi đưa vào dùng thật, mô hình luôn chấm cho khách hàng <i>trong tương lai</i>. Test trên các tháng mà mô hình chưa thấy mô phỏng đúng tình huống đó và phát hiện được nếu hành vi khách hàng thay đổi theo thời gian.</p>
    <p class="note">Tập test chỉ dùng một lần ở cuối, không dùng để chọn biến hay chỉnh tham số. So sánh với cách chia ngẫu nhiên ở slide "Kiểm tra thêm".</p>
  </div>
</div>"""),

        ("Chọn biến bằng Information Value (IV)", f"""
<div class="two narrow-left">
  <div>
    <p><b>IV</b> đo một biến tách good và bad tốt đến đâu: &lt; 0,02 không có ích, 0,02–0,1 yếu, 0,1–0,3 trung bình, 0,3–0,5 mạnh, &gt; 0,5 <b>đáng ngờ</b> (kiểm tra rò rỉ dữ liệu hoặc nhóm quá nhỏ).</p>
    <p><b>3 quy tắc loại biến:</b></p>
    <ol><li>IV &lt; 0,02</li>
    <li>Tương quan &gt; 0,6 với một biến đã chọn có IV cao hơn</li>
    <li>Hệ số logistic ngược dấu (vô lý về nghiệp vụ): {', '.join(label(c) for c in r['sign_dropped'])}</li></ol>
    <p><b>Còn lại {len(r['selected'])} biến.</b></p>
    <p class="note">Biến nhân khẩu học như tuổi, lương, giới tính gần như không có sức dự báo trong dữ liệu này.</p>
  </div>
  <div>{img(figs['iv'], 'Information Value của từng biến').replace('<img ', '<img class="tall" ')}</div>
</div>"""),

        ("Biến mạnh nhất nói gì?", f"""
{img(figs['woe'], 'Tỷ lệ bad theo nhóm của 3 biến')}
<div class="two">
  <p><b>Số app vay trong máy</b> là tín hiệu mạnh nhất (IV {vn(r['binners']['n_loan_apps'].iv, 2)}). Người không có app vay nào có tỷ lệ bad
  {pct(loan['bad_rate'].iloc[0])}, người có từ 3 app trở lên là {pct(loan['bad_rate'].iloc[-1])}. Cách hiểu hợp lý: người đang vay nhiều nơi cùng lúc thì dễ mất khả năng trả nợ.</p>
  <p><b>Tổng số app</b> càng ít thì càng rủi ro (có thể là máy mới, cài vội để vay, hoặc ít hoạt động số).
  <b>Học vấn</b> cao thì tỷ lệ bad thấp hơn. Cả ba quan hệ đều đi một chiều và có ý nghĩa nghiệp vụ.</p>
</div>"""),

        ("Chọn thuật toán", """
<table class="compact"><thead><tr><th></th><th>Logistic Regression trên WOE (scorecard)</th><th>Gradient Boosting (HistGradientBoosting)</th></tr></thead><tbody>
<tr><td><b>Cách hoạt động</b></td><td>Mỗi biến được chia nhóm, mỗi nhóm cộng/trừ một số điểm, tổng điểm → PD</td><td>Hàng trăm cây quyết định nhỏ, cây sau sửa lỗi của cây trước</td></tr>
<tr><td><b>Ưu điểm</b></td><td>Dễ giải thích từng điểm số; chuẩn ngành ngân hàng; ổn định</td><td>Bắt được quan hệ phi tuyến và tương tác giữa các biến; xử lý sẵn dữ liệu thiếu</td></tr>
<tr><td><b>Nhược điểm</b></td><td>Bỏ lỡ tương tác giữa các biến</td><td>Khó giải thích hơn; dễ học thuộc nếu không kiểm soát</td></tr>
<tr><td><b>Kiểm soát học thuộc</b></td><td>Ít biến, WOE gộp nhóm</td><td>Cây nhỏ (7 lá), mỗi lá ≥ 500 hồ sơ, dừng sớm theo validation</td></tr>
</tbody></table>
<p class="note">Quyết định: xây cả hai. Logistic là mô hình nền dễ giải thích, Boosting là mô hình thách thức, để xem độ phức tạp thêm vào có đáng không.</p>"""),

        ("Kết quả", f"""
<div class="two">
  <div>{_perf_table(r)}
  <p class="note"><b>AUC</b> = xác suất một khách bad bị chấm rủi ro hơn một khách good (0,5 = đoán bừa, 1 = hoàn hảo). <b>AR</b> (Accuracy Ratio) = 2×AUC − 1, như ở Bài I.</p>
  <p>Trên tập test OOT, Boosting cao hơn Logistic <b>{vn(gb_t['AUC'] - lr_t['AUC'], 3)} AUC</b> (AR {vn(gb_t['Gini'], 2)} so với {vn(lr_t['Gini'], 2)}).</p>
  <p>Logistic gần như không chênh giữa train và test ({vn(lr_tr['AUC'], 3)} → {vn(lr_t['AUC'], 3)}). Boosting chênh nhiều hơn ({vn(gb_tr['AUC'], 3)} → {vn(gb_t['AUC'], 3)}): có học thuộc một phần nhưng vẫn tốt hơn trên dữ liệu mới.</p></div>
  <div>{img(figs['roc'], 'Đường ROC trên tập test')}</div>
</div>"""),

        ("Con số PD dự báo có khớp thực tế không?", f"""
{img(figs['deciles'], 'Tỷ lệ bad theo nhóm 10% trên tập test')}
<div class="two">
  <p><b>Vì sao cần kiểm tra:</b> mô hình đưa ra con số PD (ví dụ 9%) để định giá khoản vay và trích lập dự phòng. Chia khách trong test set thành 10 nhóm theo PD dự báo, rồi so <b>PD dự báo</b> (cam) với <b>tỷ lệ bad thực tế</b> (xanh).</p>
  <p><b>Kết quả:</b> hai thứ gần nhau ở mọi nhóm, và thứ tự đúng: nhóm 10% rủi ro nhất có tỷ lệ bad khoảng {pct(r['deciles']['Gradient Boosting']['bad_rate'].iloc[0], 0)}, gấp hơn 3 lần trung bình. Hosmer-Lemeshow (Bài I): {vn(hl_lr['HL'], 1)} và {vn(hl_gb['HL'], 1)}, đều dưới ngưỡng 18,3.</p>
</div>"""),

        ("Kiểm tra thêm: chia theo thời gian hay chia ngẫu nhiên?", f"""
<div class="two">
  <div>
    <p>Chạy lại <b>toàn bộ quy trình</b> với cách chia thứ hai: test set lấy <b>ngẫu nhiên đều cả 7 tháng</b> (cùng số hồ sơ, giữ tỷ lệ từng tháng và tỷ lệ bad), lặp 5 lần.</p>
    {_split_table(r)}
    <p>AUC của cách chia theo thời gian <b>nằm trong khoảng dao động</b> của 5 lần chia ngẫu nhiên. Hai cách cho kết quả tương đương: chia theo thời gian không làm kết quả đẹp lên hay xấu đi một cách giả tạo.</p>
    <p class="note">Lặp 5 lần vì một lần chia ngẫu nhiên có thể cao hơn hoặc thấp hơn một chút do may rủi.</p>
  </div>
  <div>
    <p><b>Vậy vì sao vẫn chọn chia theo thời gian?</b> Vì nó phát hiện được khách tương lai khác khách cũ. Ví dụ, tỷ lệ hồ sơ <b>không có dữ liệu Facebook</b>:</p>
    {_no_fb_table(r)}
    <p>Nếu chia ngẫu nhiên, các hồ sơ này bị trộn vào cả training lẫn test, nên không thấy được thay đổi. Chia theo thời gian cho thấy mô hình <b>vẫn giữ được AUC</b> dù dữ liệu Facebook đã đổi.</p>
  </div>
</div>"""),

        ("Mô hình dựa vào đâu để quyết định?", f"""
{img(figs['importance'], 'Mức độ quan trọng của biến')}
<div class="two">
  <p class="note"><b>Trái, Logistic:</b> độ lớn hệ số |β|. Mọi biến đều đã đổi sang WOE (cùng thang), nên |β| càng lớn thì biến thay đổi PD càng mạnh.<br>
  <b>Phải, Boosting:</b> xáo trộn ngẫu nhiên một biến giữa các khách để nó mất thông tin, rồi đo AUC giảm bao nhiêu. Giảm càng nhiều, mô hình càng dựa vào biến đó.</p>
  <p>Hai mô hình đồng ý về các biến quan trọng nhất: <b>số app vay, tổng số app, hoạt động gọi điện, thâm niên làm việc</b>. Boosting không dựa vào biến lạ mà khai thác cùng các tín hiệu, chỉ chi tiết hơn.</p>
</div>"""),

        ("Quyết định chọn mô hình", f"""
<div class="two">
  <div class="card accent">
    <p><b>Đề xuất: Gradient Boosting làm mô hình chính</b>, Logistic scorecard làm mô hình đối chứng.</p>
    <ul><li>Tốt hơn rõ rệt trên dữ liệu tương lai: AR {vn(gb_t['Gini'], 2)} so với {vn(lr_t['Gini'], 2)}</li>
    <li>Giữ được AUC trên tháng 6–7, và PD dự báo khớp thực tế</li>
    <li>Biến quan trọng giống Logistic, có ý nghĩa nghiệp vụ</li></ul>
    <p class="note">Nếu đơn vị yêu cầu mô hình phải giải thích được từng điểm (ví dụ theo quy định nội bộ), Logistic scorecard là phương án thay thế, chấp nhận giảm khoảng {vn(gb_t['Gini'] - lr_t['Gini'], 2)} AR.</p>
  </div>
  <div><p><b>Ví dụ scorecard:</b> điểm cho biến "số app vay" (600 điểm ≈ PD 9%, cứ thêm 50 điểm thì rủi ro giảm một nửa):</p>
  {_scorecard_sample(r, 'n_loan_apps')}
  <p class="note">Bảng điểm đầy đủ: output/scorecard.csv</p></div>
</div>"""),

        ("Nếu mô hình dự báo kém trên khách mới?", f"""
<div class="two">
  <div>
    <p>Phát hiện điều này <b>trước khi dùng thật</b> chính là mục đích của test set theo thời gian.</p>
    <p><b>Bước 1: kém ở mặt nào?</b></p>
    <table class="compact"><thead><tr><th>Kiểu kém</th><th>Dấu hiệu</th><th>Cách xử lý</th></tr></thead><tbody>
    <tr><td>Xếp hạng kém</td><td>AUC / AR giảm mạnh</td><td>Bỏ biến không ổn định hoặc huấn luyện lại</td></tr>
    <tr><td>Mức PD lệch</td><td>AUC ổn nhưng Hosmer-Lemeshow không đạt</td><td>Hiệu chỉnh lại mức PD (recalibrate), không cần xây lại</td></tr>
    </tbody></table>
    <p><b>Bước 2: tìm nguyên nhân</b> bằng cách so phân phối từng biến giữa lúc xây và lúc dùng (ví dụ chỉ số PSI): cách thu thập dữ liệu, tệp khách, chính sách duyệt hay kinh tế thay đổi? Hay dữ liệu mới chưa đủ thời gian để lộ ra bad?</p>
    <p><b>Bước 3: trong lúc chờ sửa</b>, dùng ngưỡng duyệt chặt hơn, chạy song song mô hình cũ và mới (champion–challenger), theo dõi AUC và tỷ lệ thiếu dữ liệu hằng tháng.</p>
  </div>
  <div class="card accent">
    <p><b>Áp dụng cho bài này</b></p>
    <ul><li><b>Facebook:</b> tháng 7 có {pct(r['split_check']['no_fb_by_month'].get('2018-07', 0), 0)} hồ sơ không có dữ liệu Facebook. Scorecard dùng 2 biến Facebook, nên cần theo dõi tỷ lệ này.</li>
    <li><b>Tháng 7 mới nhất</b> nên có thể chưa đủ thời gian để lộ ra bad. Tỷ lệ bad tháng 7 ({pct(r['monthly'].loc['2018-07', 'bad_rate'])}) thấp hơn tháng 6 ({pct(r['monthly'].loc['2018-06', 'bad_rate'])}) có thể một phần vì lý do này.</li>
    <li><b>Trước khi dùng thật:</b> huấn luyện lại trên cả 7 tháng để mô hình học được thay đổi gần nhất.</li></ul>
  </div>
</div>"""),

        ("Hạn chế và bước tiếp theo", f"""
<ul class="bullets">
  <li><b>Đã tìm ra, chưa sửa:</b> scorecard chấm PD cho khách không có Facebook cao hơn thực tế (13,5% so với 10,0%), vì nhóm "Missing" của <code>fb_days_since_update</code> chỉ có 2 hồ sơ lúc học. Cách sửa: gán WOE = 0 cho nhóm quá nhỏ, hoặc hiệu chỉnh lại PD. Boosting không bị lỗi này.</li>
  <li><b>Biến tổng hợp từ danh sách app còn thô:</b> chỉ dựa vào từ khóa. Có thể phân loại app chuẩn hơn hoặc dùng các app phổ biến làm biến riêng.</li>
  <li><b>Chưa tối ưu tham số có hệ thống:</b> Boosting mới thử vài cấu hình bằng tay. Bước tiếp theo là cross-validation theo thời gian.</li>
  <li><b>Giải thích từng khách hàng:</b> cần SHAP để cho biết vì sao một hồ sơ bị chấm rủi ro (lý do từ chối).</li>
  <li><b>Định nghĩa "bad" và chính sách duyệt:</b> chưa biết bad được định nghĩa theo số ngày quá hạn nào. Ngưỡng duyệt cần chọn cùng nghiệp vụ dựa trên lợi nhuận và tỷ lệ duyệt.</li>
  <li><b>Sai lệch do chỉ có khách đã được duyệt</b> (reject inference): dữ liệu chỉ có người đã được cho vay, nên mô hình chưa thấy người bị từ chối.</li>
  <li><b>Công bằng:</b> cần kiểm tra mô hình không phân biệt theo giới tính hoặc các nhóm nhạy cảm.</li>
</ul>
<p class="note">Biến trong scorecard: {sel}.</p>"""),

        ("Tài liệu tham khảo", """
<div class="two refs">
  <div>
    <p><b>Credit scoring: WOE, IV, scorecard, PSI</b></p>
    <ol>
      <li>Siddiqi, N. (2017). <i>Intelligent Credit Scoring</i> (2nd ed.). Wiley.</li>
      <li>Thomas, L. C., Crook, J. N., &amp; Edelman, D. B. (2017). <i>Credit Scoring and Its Applications</i> (2nd ed.). SIAM.</li>
      <li>Anderson, R. (2007). <i>The Credit Scoring Toolkit</i>. Oxford University Press.</li>
    </ol>
    <p><b>Kiểm định mô hình PD</b></p>
    <ol start="4">
      <li>Sobehart, J., Keenan, S., &amp; Stein, R. (2000). <i>Benchmarking quantitative default risk models: A validation methodology</i>. Moody's.</li>
      <li>Basel Committee on Banking Supervision (2005). <i>Studies on the validation of internal rating systems</i> (WP 14). BIS.</li>
      <li>Hosmer, D. W., Lemeshow, S., &amp; Sturdivant, R. X. (2013). <i>Applied Logistic Regression</i> (3rd ed.). Wiley.</li>
      <li>Hanley, J. A., &amp; McNeil, B. J. (1982). The meaning and use of the area under a ROC curve. <i>Radiology, 143</i>(1).</li>
    </ol>
  </div>
  <div>
    <p><b>Thuật toán</b></p>
    <ol start="8">
      <li>James, G., Witten, D., Hastie, T., &amp; Tibshirani, R. (2021). <i>An Introduction to Statistical Learning</i> (2nd ed.). Springer.</li>
      <li>Hastie, T., Tibshirani, R., &amp; Friedman, J. (2009). <i>The Elements of Statistical Learning</i> (2nd ed.). Springer.</li>
      <li>Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. <i>Annals of Statistics, 29</i>(5).</li>
      <li>Ke, G. et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. <i>NeurIPS</i>.</li>
      <li>Lessmann, S., Baesens, B., Seow, H.-V., &amp; Thomas, L. C. (2015). Benchmarking classification algorithms for credit scoring. <i>EJOR, 247</i>(1).</li>
    </ol>
    <p><b>Rủi ro khi xây và dùng mô hình</b></p>
    <ol start="13">
      <li>Kaufman, S. et al. (2012). Leakage in data mining. <i>ACM TKDD, 6</i>(4).</li>
      <li>Lundberg, S. M., &amp; Lee, S.-I. (2017). A unified approach to interpreting model predictions (SHAP). <i>NeurIPS</i>.</li>
      <li>Yurdakul, B., &amp; Naranjo, J. D. (2020). Statistical properties of the population stability index. <i>Journal of Risk Model Validation</i>.</li>
    </ol>
  </div>
</div>"""),
    ]


CSS = """
:root{--ink:#1d2433;--muted:#5b6475;--line:#e3e7ee;--bg:#eef1f6;--card:#f6f8fb;--blue:#1F4E79;--orange:#E07B00}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
.deck{display:flex;flex-direction:column;align-items:center;gap:24px;padding:24px 16px}
.slide{background:#fff;width:min(1100px,100%);aspect-ratio:16/9;padding:36px 48px;border-radius:10px;
  box-shadow:0 4px 20px rgba(20,30,60,.08);display:flex;flex-direction:column;overflow:hidden;position:relative}
.slide h2{margin:0 0 16px;color:var(--blue);font-size:26px;border-bottom:3px solid var(--orange);padding-bottom:8px;align-self:flex-start}
.slide .num{position:absolute;right:24px;bottom:12px;color:var(--muted);font-size:13px}
.slide img.tall{max-height:440px}
.slide img{max-width:100%;max-height:330px;object-fit:contain;display:block;margin:0 auto}
.cover{margin:auto 0}.cover h1{font-size:42px;color:var(--blue);margin:8px 0 12px;line-height:1.15}
.kicker{color:var(--orange);font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin:0}
.lead{font-size:20px;margin:0 0 24px}.muted{color:var(--muted)}
.tiles{display:flex;gap:14px;margin-bottom:14px}
.tile{flex:1;background:var(--card);border-left:4px solid var(--blue);padding:10px 14px;border-radius:6px}
.tile b{display:block;font-size:26px;color:var(--blue)}.tile span{color:var(--muted);font-size:14px}
.tile.warn{border-color:var(--orange)}.tile.warn b{color:var(--orange)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start;min-height:0}
.two.narrow-left{grid-template-columns:.85fr 1.15fr}
.two>*{min-width:0}
.card{background:var(--card);border-radius:8px;padding:12px 18px}.card.accent{border-left:4px solid var(--orange)}
.note{color:var(--muted);font-size:14px}
p{margin:0 0 10px}ul,ol{margin:0 0 10px;padding-left:20px}li{margin-bottom:4px}
.flow{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;counter-reset:s}
.flow li{background:var(--card);border-radius:8px;padding:14px 16px;counter-increment:s;position:relative;margin:0}
.flow li::before{content:counter(s);position:absolute;top:10px;right:14px;font-size:30px;font-weight:700;color:#d5dbe5}
.flow b{display:block;color:var(--blue);font-size:17px}.flow span{font-size:14.5px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--blue);color:#fff;font-weight:600;padding:6px 8px;text-align:left}
td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
table.compact{font-size:13px}table.compact td,table.compact th{padding:4px 7px}
code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:.92em}
.bullets li{margin-bottom:6px}
.refs{font-size:12.5px;line-height:1.35}.refs ol{padding-left:22px;margin-bottom:8px}.refs li{margin-bottom:3px}.refs p{margin-bottom:4px}
.nav{position:fixed;bottom:16px;right:16px;display:flex;gap:8px}
.nav button{border:0;background:var(--blue);color:#fff;border-radius:6px;padding:8px 14px;font-size:15px;cursor:pointer}
body.present .deck{height:100vh;justify-content:center;padding:0}
body.present .slide{display:none;width:min(100vw,177.7vh);box-shadow:none;border-radius:0}
body.present .slide.on{display:flex}
@media (max-width:760px){.slide{aspect-ratio:auto;padding:22px 16px}.two,.two.narrow-left,.flow{grid-template-columns:1fr}}
@media print{body{background:#fff}.nav{display:none}.deck{padding:0;gap:0}
  .slide{box-shadow:none;border-radius:0;page-break-after:always;width:100%;display:flex!important}}
@page{size:landscape;margin:0}
"""

JS = """
const S=[...document.querySelectorAll('.slide')];let i=0;
function show(k){i=Math.max(0,Math.min(S.length-1,k));S.forEach((s,j)=>s.classList.toggle('on',j===i));}
function toggle(){document.body.classList.toggle('present');show(i);}
document.addEventListener('keydown',e=>{
  if(e.key==='f'||e.key==='F')toggle();
  if(!document.body.classList.contains('present'))return;
  if(['ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();show(i+1);}
  if(['ArrowLeft','PageUp'].includes(e.key))show(i-1);
  if(e.key==='Escape')toggle();});
show(0);
"""


def build(r: dict, figs: dict, out: Path) -> Path:
    items = slides(r, figs)
    body = "".join(
        f'<section class="slide">{f"<h2>{t}</h2>" if t else ""}{c}'
        f'<span class="num">{k + 1} / {len(items)}</span></section>'
        for k, (t, c) in enumerate(items))
    page = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mô hình good/bad</title><style>{CSS}</style></head>
<body><main class="deck">{body}</main>
<div class="nav"><button onclick="toggle()" title="Phím F">Trình chiếu</button>
<button onclick="show(i-1)">←</button><button onclick="show(i+1)">→</button></div>
<script>{JS}</script></body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out
