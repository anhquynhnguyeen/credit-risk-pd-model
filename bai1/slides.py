"""Xuất slide thuyết trình dạng một file .html (không cần internet, biểu đồ vẽ bằng SVG).

Mở bằng trình duyệt; dùng phím ← → để chuyển slide; Ctrl/Cmd+P để in ra PDF.
"""
from __future__ import annotations

import html
from pathlib import Path

from validation import Results

BLUE, ORANGE, GREY, GREEN, RED, AMBER = "#1F4E79", "#E07B00", "#8A94A6", "#2E7D32", "#C62828", "#B7791F"


def vn(x: float, digits: int = 2) -> str:
    """Định dạng số kiểu Việt Nam: 1.234,56"""
    s = f"{x:,.{digits}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x: float, digits: int = 1) -> str:
    return vn(100 * x, digits) + "%"


def pval(p: float) -> str:
    if p < 0.001:
        mantissa, exp = f"{p:.1e}".split("e")
        return f"{mantissa.replace('.', ',')}×10<sup>{int(exp)}</sup>"
    return vn(p, 3)


# ---------- biểu đồ SVG ----------

def bar_line_svg(r: Results) -> str:
    g = r.grades
    w, h, left, bottom, top, right = 640, 320, 52, 40, 20, 16
    pw, ph = w - left - right, h - top - bottom
    ymax = 0.30
    step = pw / len(g)

    def y(v):
        return top + ph * (1 - v / ymax)

    parts = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" '
             f'aria-label="ODR thực tế so với PD dự báo theo hạng">']
    for t in (0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30):
        parts.append(f'<line x1="{left}" x2="{w - right}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="grid"/>'
                     f'<text x="{left - 8}" y="{y(t) + 4:.1f}" class="tick" text-anchor="end">{int(t * 100)}%</text>')
    pts = []
    for i, row in g.iterrows():
        cx = left + step * (i + 0.5)
        bw = step * 0.55
        parts.append(f'<rect x="{cx - bw / 2:.1f}" y="{y(row.odr):.1f}" width="{bw:.1f}" '
                     f'height="{y(0) - y(row.odr):.1f}" fill="{BLUE}" rx="2"><title>Hạng {row.grade}: '
                     f'ODR {pct(row.odr)}</title></rect>')
        parts.append(f'<text x="{cx:.1f}" y="{h - bottom + 18}" class="tick" text-anchor="middle">{row.grade}</text>')
        pts.append((cx, y(row.pd)))
    parts.append('<polyline fill="none" stroke="{}" stroke-width="2.5" points="{}"/>'.format(
        ORANGE, " ".join(f"{x:.1f},{yy:.1f}" for x, yy in pts)))
    for x, yy in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="4" fill="{ORANGE}"/>')
    parts.append(f'<text x="{left + pw / 2}" y="{h - 4}" class="axis" text-anchor="middle">Hạng (1 = rủi ro nhất)</text>')
    parts.append('</svg>')
    legend = (f'<div class="legend"><span><i style="background:{BLUE}"></i>ODR thực tế</span>'
              f'<span><i style="background:{ORANGE}"></i>PD dự báo</span></div>')
    return "".join(parts) + legend


def curve_svg(r: Results, kind: str) -> str:
    c = r.curve
    size, pad = 260, 36
    p = size - 2 * pad
    xcol = "cum_good" if kind == "ROC" else "cum_all"
    xlab = "FPR: % good bị từ chối nhầm" if kind == "ROC" else "% khách bị từ chối (rủi ro nhất trước)"

    def xy(x, y):
        return pad + p * x, pad + p * (1 - y)

    out = [f'<svg viewBox="0 0 {size} {size + 10}" class="chart sq" role="img" aria-label="Đường {kind}">',
           f'<rect x="{pad}" y="{pad}" width="{p}" height="{p}" class="frame"/>']
    for t in (0, 0.5, 1):
        x0, y0 = xy(t, 0)
        _, yt = xy(0, t)
        out.append(f'<text x="{x0:.1f}" y="{y0 + 16:.1f}" class="tick" text-anchor="middle">{int(t * 100)}%</text>'
                   f'<text x="{pad - 6}" y="{yt + 4:.1f}" class="tick" text-anchor="end">{int(t * 100)}%</text>')
    a, b = xy(0, 0), xy(1, 1)
    out.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{GREY}" stroke-dasharray="4 4"/>')
    if kind == "CAP":
        dr = r.data["bad"].mean()
        pts = [xy(0, 0), xy(dr, 1), xy(1, 1)]
        out.append('<polyline fill="none" stroke="{}" stroke-width="1.5" points="{}"/>'.format(
            GREEN, " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)))
    pts = [xy(x, y) for x, y in zip(c[xcol], c["cum_bad"])]
    out.append('<polyline fill="none" stroke="{}" stroke-width="2.5" points="{}"/>'.format(
        BLUE, " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)))
    for x, y in pts:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{BLUE}"/>')
    out.append(f'<text x="{size / 2}" y="{size + 6}" class="axis" text-anchor="middle">{xlab}</text>'
               f'<text x="{pad}" y="{pad - 10}" class="axis">Đường {kind} · y = TPR: % bad bị bắt</text></svg>')
    return "".join(out)


# ---------- nội dung slide ----------

def _binomial_rows(r: Results) -> str:
    colors = {"Xanh": GREEN, "Vàng": AMBER, "Đỏ": RED}
    rows = []
    for _, g in r.grades.iterrows():
        two = "Bác bỏ" if g.p_two < 0.05 else "Không bác bỏ"
        if g.p_two < 0.05:
            two += " (PD thấp)" if g.d > g.expected else " (PD cao)"
        rows.append(
            f"<tr><td>{g.grade}</td><td>{g.n}</td><td>{g.d}</td><td>{pct(g.pd)}</td>"
            f"<td>{pct(g.odr)}</td><td>{g.k_crit_95}</td><td>{pval(g.p_upper)}</td>"
            f"<td>{pval(g.p_two)}</td><td>{two}</td>"
            f'<td><span class="dot" style="background:{colors[g.light]}"></span>{g.light}</td></tr>')
    return "".join(rows)


def _grade_rows(r: Results) -> str:
    g = r.grades
    rows = "".join(
        f"<tr><td>{x.grade}</td><td>{html.escape(x.band)}</td><td>{x.n}</td><td>{x.d}</td>"
        f"<td>{pct(x.odr)}</td><td>{pct(x.pd)}</td><td>{vn(x.expected, 1)}</td></tr>"
        for _, x in g.iterrows())
    n, d, e = g.n.sum(), g.d.sum(), g.expected.sum()
    return rows + (f'<tr class="total"><td colspan="2">Tổng</td><td>{n}</td><td>{d}</td>'
                   f"<td>{pct(d / n)}</td><td>{pct(e / n)}</td><td>{vn(e, 1)}</td></tr>")


def slides(r: Results) -> list[tuple[str, str]]:
    g, d = r.grades, r.data
    odr, avg_pd = d["bad"].mean(), d["pd"].mean()
    lo, hi = r.auc_ci
    n_rej1 = int((g.p_upper < 0.05).sum())
    n_rej2 = int((g.p_two < 0.05).sum())
    top_hl = g.sort_values("hl", ascending=False).head(3)
    top_hl_txt = ", ".join(f"hạng {x.grade} ({vn(x.hl, 1)})" for _, x in top_hl.iterrows())
    under = 1 - avg_pd / odr
    c = r.curve.set_index("grade")   # điểm ROC/CAP theo hạng (lũy kế)

    return [
        ("", f"""
<div class="cover">
  <p class="kicker">Bài test ứng viên · Bài I</p>
  <h1>Kiểm định mô hình xác suất vỡ nợ (PD)</h1>
  <p class="lead">Accuracy Ratio / AUROC · Binomial test (1 phía, 2 phía) · Hosmer-Lemeshow test</p>
  <p class="muted">Dữ liệu: {vn(len(d), 0)} khách hàng có điểm tín dụng và nhãn good/bad thực tế</p>
</div>"""),

        ("Dữ liệu và câu hỏi kiểm định", f"""
<div class="tiles">
  <div class="tile"><b>{vn(len(d), 0)}</b><span>khách hàng</span></div>
  <div class="tile"><b>{d['bad'].sum()}</b><span>khách bad</span></div>
  <div class="tile"><b>{pct(odr, 2)}</b><span>tỷ lệ vỡ nợ thực tế (ODR)</span></div>
  <div class="tile warn"><b>{pct(avg_pd, 2)}</b><span>PD dự báo bình quân</span></div>
</div>
<div class="two">
  <div class="card"><h3>1 · Khả năng phân biệt <em>(discrimination)</em></h3>
    <p>Mô hình có xếp khách bad vào nhóm rủi ro cao hơn khách good không?</p>
    <p class="tag">→ Accuracy Ratio / AUROC</p></div>
  <div class="card"><h3>2 · Hiệu chuẩn <em>(calibration)</em></h3>
    <p>Mức PD dự báo có khớp với tỷ lệ vỡ nợ thực tế không?</p>
    <p class="tag">→ Binomial test (từng hạng), Hosmer-Lemeshow (toàn danh mục)</p></div>
</div>
<p class="note">Một mô hình có thể xếp hạng tốt mà PD vẫn sai, nên cần cả hai nhóm kiểm định.</p>"""),

        ("Quy trình xử lý", """
<ol class="flow">
  <li><b>Gán hạng</b><span>Điểm → hạng theo Master Scale (10 hạng, điểm càng cao càng an toàn)</span></li>
  <li><b>Gán PD</b><span>Mỗi hạng có một PD dự báo, từ 27,5% (hạng 1) đến 0,1% (hạng 10)</span></li>
  <li><b>Tổng hợp theo hạng</b><span>n, số bad d, ODR = d/n, số bad kỳ vọng E = n × PD</span></li>
  <li><b>AUC / AR</b><span>Đường ROC và CAP từ phân phối lũy kế bad / good</span></li>
  <li><b>Binomial</b><span>So sánh d với phân phối Binomial(n, PD) ở từng hạng</span></li>
  <li><b>Hosmer-Lemeshow</b><span>Gộp sai lệch của 10 hạng thành một thống kê χ²</span></li>
</ol>
<p class="note">Mọi bước được làm lại bằng công thức trong file Excel đính kèm và đối chiếu với code Python.</p>"""),

        ("Bảng tổng hợp theo hạng", f"""
<div class="two wide-left">
  <table><thead><tr><th>Hạng</th><th>Điểm</th><th>n</th><th>Bad</th><th>ODR</th><th>PD</th><th>Kỳ vọng</th></tr></thead>
  <tbody>{_grade_rows(r)}</tbody></table>
  <div>{bar_line_svg(r)}
    <p class="note">ODR giảm đều từ hạng 1 đến 10, nên thứ tự xếp hạng đúng. Nhưng ODR nằm trên PD ở 9/10 hạng,
    nghĩa là PD bị ước tính thấp.</p></div>
</div>"""),

        ("Accuracy Ratio / AUROC", f"""
<div class="two">
  <div>
    <p><b>AUC</b> = xác suất một khách bad ngẫu nhiên bị chấm rủi ro hơn một khách good ngẫu nhiên.
    0,5 = đoán bừa, 1 = hoàn hảo.</p>
    <p><b>AR (Gini)</b> = diện tích giữa CAP mô hình và đường ngẫu nhiên, chia cho diện tích tương ứng
    của mô hình hoàn hảo. Quan hệ: <code>AR = 2 × AUC − 1</code>.</p>
    <p><b>Cách tính:</b> xếp hạng từ rủi ro nhất → an toàn nhất, lũy kế % bad (TPR), % good (FPR), % khách,
    diện tích bằng quy tắc hình thang <code>Σ Δx·(yᵢ + yᵢ₋₁)/2</code>.</p>
    <div class="tiles small">
      <div class="tile"><b>{vn(r.auc_score, 3)}</b><span>AUC<br>CI 95%: {vn(lo, 3)}–{vn(hi, 3)}</span></div>
      <div class="tile"><b>{vn(r.ar_score, 3)}</b><span>Accuracy Ratio</span></div>
    </div>
    <p class="note">Theo 10 hạng: AUC = {vn(r.auc_grade, 3)}, AR từ CAP = {vn(r.ar_cap, 3)}, khớp với 2·AUC − 1.
    <b>Đánh giá:</b> khả năng phân biệt trung bình, sát ngưỡng 0,7 thường dùng cho mô hình bán lẻ.</p>
  </div>
  <div class="charts">{curve_svg(r, "ROC")}{curve_svg(r, "CAP")}</div>
</div>"""),

        ("Vì sao dùng AUC / ROC?", f"""
<div class="two">
  <div>
    <p><b>Đọc đường ROC:</b> lần lượt đặt ngưỡng "từ chối hạng 1 → k". Số người bị từ chối luôn là phần <b>cộng dồn</b> từ hạng 1:</p>
    <table class="compact"><thead><tr><th>Ngưỡng</th><th>Từ chối nhầm good<br>(FPR = % good lũy kế)</th><th>Bắt được bad<br>(TPR = % bad lũy kế)</th></tr></thead><tbody>
    <tr><td>đến hạng 1</td><td>{pct(c.cum_good[1])}</td><td>{pct(c.cum_bad[1])}</td></tr>
    <tr><td>đến hạng 2</td><td>{pct(c.cum_good[2])}</td><td>{pct(c.cum_bad[2])}</td></tr>
    <tr><td>đến hạng 4</td><td>{pct(c.cum_good[4])}</td><td>{pct(c.cum_bad[4])}</td></tr>
    </tbody></table>
    <p class="note">Mỗi ngưỡng là một điểm (FPR, TPR); nối 10 điểm thành đường ROC. AUC = diện tích dưới đường
    = xác suất một khách bad bị chấm rủi ro hơn một khách good ({pct(r.auc_score, 0)} số cặp được xếp đúng).</p>
  </div>
  <div>
    <p><b>Điểm lợi:</b></p>
    <ul class="bullets">
      <li><b>Đo đúng thứ ngân hàng dùng:</b> điểm số dùng để xếp hạng rồi duyệt / từ chối / định giá, nên thứ tự là điều quan trọng nhất.</li>
      <li><b>Không phụ thuộc ngưỡng cắt:</b> tính trên mọi ngưỡng, trong khi ngưỡng là quyết định kinh doanh có thể thay đổi.</li>
      <li><b>Không bị đánh lừa khi bad hiếm:</b> "mô hình" đoán ai cũng good đúng {pct(1 - odr, 0)} nhưng AUC chỉ 0,5.</li>
      <li><b>Dễ diễn giải:</b> AUC 0,69 = 69% số cặp (bad, good) được xếp đúng thứ tự.</li>
    </ul>
    <p class="note"><b>Giới hạn:</b> AUC chỉ đo thứ tự, không cho biết con số PD đúng hay sai, nên cần thêm Binomial và Hosmer-Lemeshow.</p>
  </div>
</div>"""),

        ("Binomial test theo từng hạng", f"""
<div class="two narrow-left">
  <div>
    <p><b>1 phía:</b> H₀: PD thật ≤ PD dự báo. H₁: mô hình đánh giá <b>thấp</b> rủi ro (hướng thận trọng).</p>
    <p><b>2 phía:</b> H₀: PD thật = PD dự báo. Bắt cả trường hợp quá cao lẫn quá thấp.</p>
    <p><code>p = P(X ≥ d), X ~ Bin(n, PD)</code><br>
    Excel: <code>1 − BINOM.DIST(d−1, n, PD, TRUE)</code><br>
    Ngưỡng 95%: <code>BINOM.INV(n, PD, 0,95)</code></p>
    <p class="note"><b>Kết quả (α = 5%):</b> 1 phía bác bỏ {n_rej1}/10 hạng, 2 phía bác bỏ {n_rej2}/10 hạng.
    Hạng 1 là trường hợp ngược lại: PD hơi cao hơn thực tế (thận trọng).</p>
  </div>
  <table class="compact"><thead><tr><th>Hạng</th><th>n</th><th>d</th><th>PD</th><th>ODR</th><th>Ngưỡng d</th>
  <th>p 1 phía</th><th>p 2 phía</th><th>Kết luận 2 phía</th><th>Đèn</th></tr></thead>
  <tbody>{_binomial_rows(r)}</tbody></table>
</div>"""),

        ("Hosmer-Lemeshow test", f"""
<div class="two">
  <div>
    <p class="formula">HL = Σ<sub>i</sub> (d<sub>i</sub> − n<sub>i</sub>·PD<sub>i</sub>)² / (n<sub>i</sub>·PD<sub>i</sub>·(1 − PD<sub>i</sub>)) ~ χ²(df)</p>
    <p>H₀: PD dự báo khớp với thực tế ở <b>tất cả</b> các hạng.
    PD được cố định từ trước (kiểm định ngoài mẫu) nên <b>df = số hạng = 10</b>
    (df = k − 2 chỉ dùng khi kiểm định trên mẫu phát triển).</p>
    <p>Excel: <code>CHISQ.DIST.RT(HL, 10)</code></p>
    <p>Đóng góp lớn nhất: {top_hl_txt}.</p>
  </div>
  <div>
    <div class="tiles small">
      <div class="tile bad"><b>{vn(r.hl['stat'], 1)}</b><span>HL (10 hạng)<br>ngưỡng χ² 95% = {vn(r.hl['crit_95'], 1)}</span></div>
      <div class="tile bad"><b>{pval(r.hl['p'])}</b><span>p-value</span></div>
    </div>
    <div class="card"><h3>Cách đọc</h3>
    <p>Nếu PD dự báo đúng, HL thường dao động quanh 10 (bằng số hạng) và chỉ vượt
    {vn(r.hl['crit_95'], 1)} trong 5% trường hợp.</p>
    <p class="tag">→ HL = {vn(r.hl['stat'], 1)}, vượt xa ngưỡng: bác bỏ H₀, PD chưa được hiệu chuẩn tốt.</p></div>
  </div>
</div>"""),

        ("Giả định và hạn chế", """
<ul class="bullets">
  <li><b>Vỡ nợ độc lập:</b> Binomial và HL giả định các khách hàng vỡ nợ độc lập. Thực tế có tương quan
  (cùng chịu chu kỳ kinh tế), làm phương sai số vỡ nợ lớn hơn, nên test dễ bác bỏ hơn mức cần.
  Có thể điều chỉnh bằng mô hình một nhân tố Vasicek (hệ số tương quan ρ).</li>
  <li><b>Một kỳ dữ liệu:</b> chưa biết dữ liệu thuộc giai đoạn nào của chu kỳ kinh tế (PIT hay TTC); cần
  kiểm định thêm theo thời gian (out-of-time) và độ ổn định quần thể (PSI).</li>
  <li><b>AUC theo hạng và theo điểm</b> chênh nhau rất ít, nên việc chia 10 hạng không làm mất thông tin xếp hạng.</li>
</ul>"""),

        ("Kết luận và khuyến nghị", f"""
<table class="verdict"><thead><tr><th>Tiêu chí</th><th>Kết quả</th><th>Đánh giá</th></tr></thead><tbody>
<tr><td>Khả năng phân biệt</td><td>AUC {vn(r.auc_score, 3)} · AR {vn(r.ar_score, 3)}</td><td class="mid">Trung bình, chấp nhận được</td></tr>
<tr><td>Thứ tự xếp hạng</td><td>ODR giảm đều qua 10 hạng</td><td class="ok">Đạt</td></tr>
<tr><td>Hiệu chuẩn từng hạng</td><td>Binomial 1 phía bác bỏ {n_rej1}/10 hạng</td><td class="ko">Không đạt</td></tr>
<tr><td>Hiệu chuẩn toàn danh mục</td><td>HL {vn(r.hl['stat'], 1)}, p ≈ 0</td><td class="ko">Không đạt</td></tr>
<tr><td>Mức PD trung bình</td><td>PD {pct(avg_pd, 2)} so với ODR {pct(odr, 2)}</td><td class="ko">Thấp hơn ~{pct(under, 0)}</td></tr>
</tbody></table>
<div class="card accent">
<p><b>Mô hình xếp hạng đúng nhưng PD bị đánh giá thấp có hệ thống.</b></p>
<p>Khuyến nghị: <b>hiệu chuẩn lại</b> (recalibration) thay vì xây lại mô hình. Ví dụ: ước lượng lại quan hệ
logit(PD) theo điểm hoặc dịch chuyển PD về xu hướng trung tâm mới, sau đó kiểm định lại out-of-time.
Song song, xem xét bổ sung biến để cải thiện AUC.</p></div>"""),

        ("Phụ lục: công thức Excel", """
<table class="compact"><thead><tr><th>Bước</th><th>Công thức</th></tr></thead><tbody>
<tr><td>Gán hạng</td><td><code>=MATCH(Điểm, CậnDưới, 1)</code></td></tr>
<tr><td>Gán PD</td><td><code>=INDEX(PD, Hạng)</code></td></tr>
<tr><td>n, d theo hạng</td><td><code>=COUNTIF(Hạng, h)</code> · <code>=COUNTIFS(Hạng, h, Bad, 1)</code></td></tr>
<tr><td>Diện tích ROC/CAP</td><td><code>=(x − x₋₁)·(y + y₋₁)/2</code>, AUC = tổng</td></tr>
<tr><td>AR từ CAP</td><td><code>=(DiệnTíchCAP − 0,5)/(0,5 − DR/2)</code></td></tr>
<tr><td>Binomial 1 phía</td><td><code>=1 − BINOM.DIST(d − 1, n, PD, TRUE)</code></td></tr>
<tr><td>Ngưỡng 95%</td><td><code>=BINOM.INV(n, PD, 0,95)</code></td></tr>
<tr><td>Binomial 2 phía</td><td><code>=MIN(1, 2·MIN(P(X≤d), P(X≥d)))</code></td></tr>
<tr><td>Thành phần HL</td><td><code>=(d − n·PD)^2/(n·PD·(1 − PD))</code></td></tr>
<tr><td>p-value HL</td><td><code>=CHISQ.DIST.RT(HL, 10)</code></td></tr>
</tbody></table>
<p class="note">Chi tiết trong file Bai1_PD_Validation.xlsx: mỗi sheet có cột "Python" màu xám để đối chiếu.</p>"""),
    ]


CSS = """
:root{--ink:#1d2433;--muted:#5b6475;--line:#e3e7ee;--bg:#eef1f6;--card:#f6f8fb;--blue:#1F4E79;--orange:#E07B00}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
.deck{display:flex;flex-direction:column;align-items:center;gap:24px;padding:24px 16px}
.slide{background:#fff;width:min(1100px,100%);aspect-ratio:16/9;padding:40px 52px;border-radius:10px;
  box-shadow:0 4px 20px rgba(20,30,60,.08);display:flex;flex-direction:column;overflow:hidden;position:relative}
.slide h2{margin:0 0 18px;color:var(--blue);font-size:28px;border-bottom:3px solid var(--orange);padding-bottom:8px;align-self:flex-start}
.slide .num{position:absolute;right:24px;bottom:14px;color:var(--muted);font-size:13px}
.cover{margin:auto 0}.cover h1{font-size:44px;color:var(--blue);margin:8px 0 12px;line-height:1.15}
.kicker{color:var(--orange);font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin:0}
.lead{font-size:20px;margin:0 0 24px}.muted{color:var(--muted)}
.tiles{display:flex;gap:14px;margin-bottom:18px;flex-wrap:wrap}
.tile{flex:1;min-width:130px;background:var(--card);border-left:4px solid var(--blue);padding:12px 16px;border-radius:6px}
.tile b{display:block;font-size:28px;color:var(--blue)}.tile span{color:var(--muted);font-size:14px}
.tile.warn{border-color:var(--orange)}.tile.warn b{color:var(--orange)}
.tile.bad{border-color:#C62828}.tile.bad b{color:#C62828}
.tiles.small .tile b{font-size:24px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:start;min-height:0}
.two.wide-left{grid-template-columns:1fr 1.15fr}.two.narrow-left{grid-template-columns:.8fr 1.4fr}
.card{background:var(--card);border-radius:8px;padding:14px 18px}.card h3{margin:0 0 6px;color:var(--blue);font-size:18px}
.card.accent{border-left:4px solid var(--orange);margin-top:16px}
.card p{margin:6px 0}.tag{color:var(--orange);font-weight:600}
.note{color:var(--muted);font-size:14.5px}
.flow{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;counter-reset:s}
.flow li{background:var(--card);border-radius:8px;padding:14px 16px;counter-increment:s;position:relative}
.flow li::before{content:counter(s);position:absolute;top:10px;right:14px;font-size:30px;font-weight:700;color:#d5dbe5}
.flow b{display:block;color:var(--blue);font-size:17px}.flow span{font-size:14.5px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}
th{background:var(--blue);color:#fff;font-weight:600;padding:6px 8px;text-align:left}
td{padding:5px 8px;border-bottom:1px solid var(--line)}tr.total td{font-weight:700;border-top:2px solid var(--blue)}
table.compact{font-size:13px}table.compact td,table.compact th{padding:4px 7px}
.verdict td.ok{color:#2E7D32;font-weight:600}.verdict td.ko{color:#C62828;font-weight:600}.verdict td.mid{color:#B7791F;font-weight:600}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:.92em}
.formula{font-size:18px;background:var(--card);padding:10px 14px;border-radius:6px}
.bullets{margin:0;padding-left:20px}.bullets li{margin-bottom:12px}
.chart{width:100%;height:auto}.chart .grid{stroke:#e8ecf2}.chart .tick{font-size:12px;fill:#5b6475}
.chart .axis{font-size:12.5px;fill:#3a4252}.chart .frame{fill:none;stroke:#cfd6e0}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.legend{display:flex;gap:18px;font-size:13px;color:var(--muted);margin-top:4px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.nav{position:fixed;bottom:16px;right:16px;display:flex;gap:8px}
.nav button{border:0;background:var(--blue);color:#fff;border-radius:6px;padding:8px 14px;font-size:15px;cursor:pointer}
body.present .deck{height:100vh;justify-content:center;padding:0}
body.present .slide{display:none;width:min(100vw,177.7vh);box-shadow:none;border-radius:0}
body.present .slide.on{display:flex}
@media (max-width:760px){.slide{aspect-ratio:auto;padding:24px 18px}.two,.two.wide-left,.two.narrow-left,.flow,.charts{grid-template-columns:1fr}}
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


def build(r: Results, out: Path) -> Path:
    items = slides(r)
    body = "".join(
        f'<section class="slide">{f"<h2>{t}</h2>" if t else ""}{c}'
        f'<span class="num">{k + 1} / {len(items)}</span></section>'
        for k, (t, c) in enumerate(items))
    page = f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kiểm định mô hình PD</title><style>{CSS}</style></head>
<body><main class="deck">{body}</main>
<div class="nav"><button onclick="toggle()" title="Phím F">Trình chiếu</button>
<button onclick="show(i-1)">←</button><button onclick="show(i+1)">→</button></div>
<script>{JS}</script></body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out
