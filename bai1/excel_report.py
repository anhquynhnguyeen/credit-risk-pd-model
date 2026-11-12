"""Xuất file Excel có CÔNG THỨC THẬT, để người chấm thấy từng bước xử lý.

Builds an Excel workbook where every number is a live formula; Python values sit
next to them in grey "Python check" columns so the two can be compared.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference, ScatterChart, Series
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from validation import Results

HEAD_FILL = PatternFill("solid", fgColor="1F4E79")
HEAD_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14, color="1F4E79")
NOTE_FONT = Font(italic=True, color="595959")
CHECK_FONT = Font(color="808080", italic=True)
KEY_FILL = PatternFill("solid", fgColor="FFF2CC")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
PCT = "0.00%"
P_FMT = "0.0000"
SCI = "0.00E+00"

# Tên sheet
MS, DATA, GT, AUC, BIN, HL, SUM = ("MasterScale", "Data", "1_Bang_theo_hang", "2_AUC_AR",
                                   "3_Binomial", "4_Hosmer_Lemeshow", "0_Tom_tat")
FIRST, LAST = 4, 13          # dòng hạng 1..10 trong các sheet tính toán
TOTAL = 14                    # dòng tổng


def _title(ws, title: str, note: str) -> None:
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = note
    ws["A2"].font = NOTE_FONT


def _header(ws, row: int, labels: list[str], check_from: int | None = None) -> None:
    for i, label in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=label)
        c.font, c.fill, c.border = HEAD_FONT, HEAD_FILL, BOX
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        if check_from and i >= check_from:
            c.fill = PatternFill("solid", fgColor="7F7F7F")
    ws.row_dimensions[row].height = 45


def _widths(ws, widths: list[int]) -> None:
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _fmt(ws, cols: str, fmt: str, rows=range(FIRST, TOTAL + 1)) -> None:
    for col in cols:
        for r in rows:
            ws[f"{col}{r}"].number_format = fmt


def _box(ws, rows, ncols: int) -> None:
    for r in rows:
        for c in range(1, ncols + 1):
            ws.cell(row=r, column=c).border = BOX


def _axes_visible(chart) -> None:
    # openpyxl >= 3.1 ẩn trục mặc định
    chart.x_axis.delete = False
    chart.y_axis.delete = False
    # Tiêu đề ở trên, chú thích ở dưới, KHÔNG chồng lên vùng vẽ; chừa chỗ cho chúng
    if chart.title is not None:
        chart.title.overlay = False
    if chart.legend is not None:
        chart.legend.overlay = False
    chart.layout = Layout(manualLayout=ManualLayout(   # openpyxl ghi chart.layout vào vùng vẽ
        layoutTarget="inner", xMode="edge", yMode="edge", x=0.1, y=0.2, w=0.85, h=0.58))
    # đường nối thẳng giữa các điểm, không làm cong
    for s in chart.series:
        s.smooth = False


def _master_scale(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(MS)
    _header(ws, 1, ["Hạng", "Khoảng điểm", "Cận dưới", "Cận trên", "PD dự báo"])
    for i, m in r.master.iterrows():
        row = i + 2
        ws.cell(row=row, column=1, value=int(m["grade"]))
        ws.cell(row=row, column=2, value=m["band"])
        ws.cell(row=row, column=3, value=int(m["lower"]))
        ws.cell(row=row, column=4, value=None if m["upper"] == float("inf") else int(m["upper"]))
        ws.cell(row=row, column=5, value=float(m["pd"])).number_format = "0.0%"
    ws["G1"] = "Cận dưới = cận trên của hạng trước + 1 (điểm là số nguyên). Dùng cho hàm MATCH."
    ws["G1"].font = NOTE_FONT
    _widths(ws, [8, 13, 11, 11, 11])


def _data(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(DATA)
    _header(ws, 1, ["Điểm", "Good=0/Bad=1", "Hạng", "PD dự báo"])
    for i, (score, bad) in enumerate(zip(r.data["score"], r.data["bad"]), start=2):
        ws.cell(row=i, column=1, value=int(score))
        ws.cell(row=i, column=2, value=int(bad))
        ws.cell(row=i, column=3, value=f"=MATCH(A{i},{MS}!$C$2:$C$11,1)")
        ws.cell(row=i, column=4, value=f"=INDEX({MS}!$E$2:$E$11,C{i})").number_format = "0.0%"
    ws["F1"] = "Bước 1: Hạng = MATCH(điểm, cận dưới, 1); PD = INDEX(PD, hạng)."
    ws["F1"].font = NOTE_FONT
    ws.freeze_panes = "A2"
    _widths(ws, [9, 14, 8, 11])


def _grade_table(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(GT)
    _title(ws, "Bước 2: Bảng tổng hợp theo hạng",
           "ODR = tỷ lệ vỡ nợ thực tế; Kỳ vọng = n × PD (số bad mô hình dự báo).")
    _header(ws, 3, ["Hạng", "Khoảng điểm", "Số khách (n)", "Số bad (d)", "Số good",
                    "ODR = d/n", "PD dự báo", "Bad kỳ vọng = n×PD", "",
                    "Python: n", "Python: d"], check_from=10)
    for k in range(10):
        row = FIRST + k
        ws[f"A{row}"] = f"={MS}!A{k + 2}"
        ws[f"B{row}"] = f"={MS}!B{k + 2}"
        ws[f"C{row}"] = f"=COUNTIF({DATA}!$C:$C,A{row})"
        ws[f"D{row}"] = f"=COUNTIFS({DATA}!$C:$C,A{row},{DATA}!$B:$B,1)"
        ws[f"E{row}"] = f"=C{row}-D{row}"
        ws[f"F{row}"] = f"=D{row}/C{row}"
        ws[f"G{row}"] = f"={MS}!E{k + 2}"
        ws[f"H{row}"] = f"=C{row}*G{row}"
        ws[f"J{row}"] = int(r.grades["n"][k])
        ws[f"K{row}"] = int(r.grades["d"][k])
        ws[f"J{row}"].font = ws[f"K{row}"].font = CHECK_FONT
    ws[f"A{TOTAL}"] = "Tổng"
    for col in "CDEH":
        ws[f"{col}{TOTAL}"] = f"=SUM({col}{FIRST}:{col}{LAST})"
    ws[f"F{TOTAL}"] = f"=D{TOTAL}/C{TOTAL}"
    ws[f"G{TOTAL}"] = f"=H{TOTAL}/C{TOTAL}"
    for c in "ABCDEFGH":
        ws[f"{c}{TOTAL}"].font = Font(bold=True)
    ws[f"B{TOTAL + 1}"] = "PD tổng = PD bình quân gia quyền theo số khách"
    ws[f"B{TOTAL + 1}"].font = NOTE_FONT
    _fmt(ws, "FG", PCT)
    _fmt(ws, "H", "0.0")
    _box(ws, range(FIRST, TOTAL + 1), 8)
    _widths(ws, [8, 12, 12, 11, 10, 11, 11, 13, 3, 11, 11])

    chart = BarChart()
    # Không dùng tiêu đề trục (Excel hay đặt chúng đè lên số); mô tả trục nằm trong tiêu đề biểu đồ
    chart.title = "ODR thực tế so với PD dự báo\nNgang: hạng (1 = rủi ro nhất) · Dọc: tỷ lệ vỡ nợ"
    chart.legend.position = "b"
    chart.add_data(Reference(ws, min_col=6, min_row=3, max_row=LAST), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=FIRST, max_row=LAST))
    line = LineChart()
    line.add_data(Reference(ws, min_col=7, min_row=3, max_row=LAST), titles_from_data=True)
    line.series[0].marker.symbol = "circle"
    chart.y_axis.number_format = "0%"
    _axes_visible(chart)
    chart += line
    chart.height, chart.width = 9, 17
    ws.add_chart(chart, "M3")


def _auc(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(AUC)
    _title(ws, "Bước 3: Accuracy Ratio / AUROC - khả năng phân biệt",
           "Mỗi dòng = một ngưỡng 'từ chối hạng 1 đến hạng này'. Số người bị từ chối luôn là phần cộng dồn (lũy kế) từ hạng 1; diện tích tính bằng quy tắc hình thang.")
    _header(ws, 3, ["Từ chối từ hạng 1 đến", "n", "d (bad)", "good",
                    "% khách bị từ chối (trục x của CAP) = % khách lũy kế",
                    "TPR: % bad bị bắt (trục y) = % bad lũy kế",
                    "FPR: % good bị từ chối nhầm (trục x của ROC) = % good lũy kế",
                    "Diện tích ROC = ΔFPR·(TPR+TPR₋₁)/2", "Diện tích CAP = Δ%khách·(TPR+TPR₋₁)/2"])
    ws.row_dimensions[3].height = 75
    start = FIRST
    ws[f"A{start}"] = "Gốc"
    for col in "EFG":
        ws[f"{col}{start}"] = 0
    for k in range(10):
        row = start + 1 + k
        src = FIRST + k
        ws[f"A{row}"] = f"='{GT}'!A{src}"
        ws[f"B{row}"] = f"='{GT}'!C{src}"
        ws[f"C{row}"] = f"='{GT}'!D{src}"
        ws[f"D{row}"] = f"='{GT}'!E{src}"
        ws[f"E{row}"] = f"=E{row - 1}+B{row}/'{GT}'!$C${TOTAL}"
        ws[f"F{row}"] = f"=F{row - 1}+C{row}/'{GT}'!$D${TOTAL}"
        ws[f"G{row}"] = f"=G{row - 1}+D{row}/'{GT}'!$E${TOTAL}"
        ws[f"H{row}"] = f"=(G{row}-G{row - 1})*(F{row}+F{row - 1})/2"
        ws[f"I{row}"] = f"=(E{row}-E{row - 1})*(F{row}+F{row - 1})/2"
    end = start + 10
    _fmt(ws, "EFG", PCT, range(start, end + 1))
    _fmt(ws, "HI", P_FMT, range(start, end + 1))
    _box(ws, range(start, end + 1), 9)

    res = end + 2
    rows = [
        ("AUC (theo hạng) = tổng diện tích ROC", f"=SUM(H{start + 1}:H{end})", P_FMT),
        ("AR (Gini) = 2×AUC − 1", f"=2*B{res}-1", P_FMT),
        ("Diện tích dưới CAP của mô hình", f"=SUM(I{start + 1}:I{end})", P_FMT),
        ("Tỷ lệ bad toàn danh mục (DR)", f"='{GT}'!F{TOTAL}", PCT),
        ("AR từ CAP = (diện tích CAP − 0,5) / (0,5 − DR/2)", f"=(B{res + 2}-0.5)/(0.5-B{res + 3}/2)", P_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(rows):
        ws[f"A{res + i}"] = label
        ws[f"B{res + i}"] = formula
        ws[f"B{res + i}"].number_format = fmt
        ws[f"B{res + i}"].fill = KEY_FILL
    ws[f"A{res + 6}"] = "→ AR tính từ CAP phải bằng 2×AUC − 1 (hai cách đo cùng một thứ)."
    ws[f"A{res + 6}"].font = NOTE_FONT

    chk = res + 8
    lo, hi = r.auc_ci
    checks = [
        ("Python: AUC theo hạng", r.auc_grade),
        ("Python: AUC theo điểm gốc (chi tiết hơn)", r.auc_score),
        ("Python: AR theo điểm gốc", r.ar_score),
        ("Python: sai số chuẩn AUC (Hanley-McNeil)", r.auc_se),
        ("Python: AUC 95% CI - cận dưới", lo),
        ("Python: AUC 95% CI - cận trên", hi),
    ]
    for i, (label, val) in enumerate(checks):
        ws[f"A{chk + i}"] = label
        ws[f"B{chk + i}"] = round(float(val), 6)
        ws[f"A{chk + i}"].font = ws[f"B{chk + i}"].font = CHECK_FONT

    # Điểm phụ để vẽ đường ngẫu nhiên và mô hình hoàn hảo
    ws["K3"], ws["L3"], ws["M3"] = "Đường tham chiếu x", "Ngẫu nhiên", "CAP hoàn hảo"
    for c in "KLM":
        ws[f"{c}3"].font = NOTE_FONT
    ws["K4"], ws["L4"], ws["M4"] = 0, 0, 0
    ws["K5"], ws["L5"], ws["M5"] = f"=B{res + 3}", f"=B{res + 3}", 1
    ws["K6"], ws["L6"], ws["M6"] = 1, 1, 1
    _widths(ws, [44, 12, 9, 9, 18, 18, 20, 18, 18, 3, 12, 11, 12])

    def scatter(title, xcol, xlabel):
        ch = ScatterChart()
        # mô tả trục nằm trong tiêu đề biểu đồ thay vì tiêu đề trục (tránh chữ đè lên số)
        ch.title, ch.style = f"{title}\nNgang: {xlabel} · Dọc: TPR (% bad bị bắt)", 13
        ch.legend.position = "b"
        ch.x_axis.scaling.min = ch.y_axis.scaling.min = 0
        ch.x_axis.scaling.max = ch.y_axis.scaling.max = 1
        ch.x_axis.majorUnit = ch.y_axis.majorUnit = 0.2
        ch.x_axis.number_format = ch.y_axis.number_format = "0%"
        s = Series(Reference(ws, min_col=6, min_row=start, max_row=end),
                   Reference(ws, min_col=xcol, min_row=start, max_row=end), title="Mô hình")
        s.marker.symbol = "circle"
        ch.series.append(s)
        diag = Series(Reference(ws, min_col=11, min_row=4, max_row=6),
                      Reference(ws, min_col=11, min_row=4, max_row=6), title="Ngẫu nhiên")
        ch.series.append(diag)
        _axes_visible(ch)
        ch.height, ch.width = 10, 14
        return ch

    roc = scatter("Đường ROC", 7, "FPR (% good bị từ chối nhầm)")
    cap = scatter("Đường CAP", 5, "% khách bị từ chối")
    perfect = Series(Reference(ws, min_col=13, min_row=4, max_row=6),
                     Reference(ws, min_col=11, min_row=4, max_row=6), title="Hoàn hảo")
    perfect.smooth = False
    cap.series.append(perfect)
    ws.add_chart(roc, "K9")
    ws.add_chart(cap, "K31")


def _binomial(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(BIN)
    _title(ws, "Bước 4: Binomial test theo từng hạng (α = 5%)",
           "1 phía: H0 PD thật ≤ PD dự báo (lo ngại đánh giá thấp rủi ro). "
           "2 phía: H0 PD thật = PD dự báo. Giả định các khách hàng vỡ nợ độc lập.")
    _header(ws, 3, ["Hạng", "n", "d", "PD dự báo", "Kỳ vọng n×PD",
                    "Ngưỡng d tối đa (95%)", "Ngưỡng d tối đa (99%)",
                    "p 1 phía = P(X≥d)", "P(X≤d)", "p 2 phía = 2·min", "z (xấp xỉ chuẩn)",
                    "Kết luận 1 phía", "Kết luận 2 phía", "Đèn", "",
                    "Python: p 1 phía", "Python: p 2 phía (exact)"], check_from=16)
    for k in range(10):
        row, src = FIRST + k, FIRST + k
        ws[f"A{row}"] = f"='{GT}'!A{src}"
        ws[f"B{row}"] = f"='{GT}'!C{src}"
        ws[f"C{row}"] = f"='{GT}'!D{src}"
        ws[f"D{row}"] = f"='{GT}'!G{src}"
        ws[f"E{row}"] = f"=B{row}*D{row}"
        ws[f"F{row}"] = f"=_xlfn.BINOM.INV(B{row},D{row},0.95)"
        ws[f"G{row}"] = f"=_xlfn.BINOM.INV(B{row},D{row},0.99)"
        ws[f"H{row}"] = f"=IF(C{row}=0,1,1-_xlfn.BINOM.DIST(C{row}-1,B{row},D{row},TRUE))"
        ws[f"I{row}"] = f"=_xlfn.BINOM.DIST(C{row},B{row},D{row},TRUE)"
        ws[f"J{row}"] = f"=MIN(1,2*MIN(H{row},I{row}))"
        ws[f"K{row}"] = f"=(C{row}-E{row})/SQRT(B{row}*D{row}*(1-D{row}))"
        ws[f"L{row}"] = f'=IF(H{row}<0.05,"Bác bỏ: PD bị đánh giá thấp","Không bác bỏ")'
        ws[f"M{row}"] = (f'=IF(J{row}<0.05,IF(C{row}>E{row},"Bác bỏ: PD thấp hơn thực tế",'
                         f'"Bác bỏ: PD cao hơn thực tế"),"Không bác bỏ")')
        ws[f"N{row}"] = f'=IF(H{row}<0.01,"Đỏ",IF(H{row}<0.05,"Vàng","Xanh"))'
        ws[f"P{row}"] = float(r.grades["p_upper"][k])
        ws[f"Q{row}"] = float(r.grades["p_two_exact"][k])
        ws[f"P{row}"].font = ws[f"Q{row}"].font = CHECK_FONT
    _fmt(ws, "D", "0.0%", range(FIRST, LAST + 1))
    _fmt(ws, "E", "0.0", range(FIRST, LAST + 1))
    _fmt(ws, "HIJPQ", P_FMT, range(FIRST, LAST + 1))
    _fmt(ws, "K", "0.00", range(FIRST, LAST + 1))
    _box(ws, range(FIRST, LAST + 1), 14)
    rng = f"N{FIRST}:N{LAST}"
    for text, color in (("Đỏ", "F8CBAD"), ("Vàng", "FFE699"), ("Xanh", "C6EFCE")):
        ws.conditional_formatting.add(
            rng, CellIsRule(operator="equal", formula=[f'"{text}"'],
                            fill=PatternFill("solid", fgColor=color)))

    s = LAST + 2
    ws[f"A{s}"] = "Số hạng bị bác bỏ (1 phía, 5%)"
    ws[f"E{s}"] = f'=COUNTIF(L{FIRST}:L{LAST},"Bác bỏ*")'
    ws[f"A{s + 1}"] = "Số hạng bị bác bỏ (2 phía, 5%)"
    ws[f"E{s + 1}"] = f'=COUNTIF(M{FIRST}:M{LAST},"Bác bỏ*")'
    ws[f"E{s}"].fill = ws[f"E{s + 1}"].fill = KEY_FILL
    notes = [
        "Cách đọc: nếu d > 'Ngưỡng d tối đa (95%)' thì bác bỏ H0 ở mức 5% (tương đương p 1 phía < 5%).",
        "Đèn: Xanh p ≥ 5%; Vàng 1% ≤ p < 5%; Đỏ p < 1% (cách trình bày kiểu traffic light).",
        "p 2 phía = 2·min(P(X≤d), P(X≥d)); Python dùng cách exact của scipy nên có thể lệch nhẹ.",
        "Giới hạn: test giả định vỡ nợ độc lập; tương quan vỡ nợ thực tế làm test khắt khe hơn mức cần.",
    ]
    for i, n in enumerate(notes):
        ws[f"A{s + 3 + i}"] = n
        ws[f"A{s + 3 + i}"].font = NOTE_FONT
    _widths(ws, [8, 7, 6, 10, 10, 11, 11, 12, 10, 12, 10, 27, 27, 7, 3, 11, 12])


def _hl(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(HL)
    _title(ws, "Bước 5: Hosmer-Lemeshow test - hiệu chuẩn toàn danh mục",
           "HL = Σ (d − n·PD)² / (n·PD·(1−PD)) ~ χ²(df). Kiểm định ngoài mẫu (PD cố định) nên df = số hạng.")
    _header(ws, 3, ["Hạng", "n", "d", "PD", "Kỳ vọng E = n×PD", "Thành phần HL", "",
                    "Python: thành phần"], check_from=8)
    for k in range(10):
        row = FIRST + k
        ws[f"A{row}"] = f"='{GT}'!A{row}"
        ws[f"B{row}"] = f"='{GT}'!C{row}"
        ws[f"C{row}"] = f"='{GT}'!D{row}"
        ws[f"D{row}"] = f"='{GT}'!G{row}"
        ws[f"E{row}"] = f"=B{row}*D{row}"
        ws[f"F{row}"] = f"=(C{row}-E{row})^2/(B{row}*D{row}*(1-D{row}))"
        ws[f"H{row}"] = round(float(r.grades["hl"][k]), 4)
        ws[f"H{row}"].font = CHECK_FONT
    _fmt(ws, "D", "0.0%", range(FIRST, LAST + 1))
    _fmt(ws, "EF", "0.00", range(FIRST, LAST + 1))
    _box(ws, range(FIRST, LAST + 1), 6)

    def result_block(top, sum_rng, df_formula, check):
        items = [
            ("Thống kê HL", f"=SUM({sum_rng})", "0.00"),
            ("Bậc tự do (df)", df_formula, "0"),
            ("Giá trị tới hạn χ² (95%)", f"=_xlfn.CHISQ.INV.RT(0.05,B{top + 1})", "0.00"),
            ("p-value", f"=_xlfn.CHISQ.DIST.RT(B{top},B{top + 1})", SCI),
            ("Kết luận", f'=IF(B{top + 3}<0.05,"Bác bỏ H0: PD chưa được hiệu chuẩn tốt","Không bác bỏ H0")', None),
        ]
        for i, (label, formula, fmt) in enumerate(items):
            ws[f"A{top + i}"] = label
            ws[f"B{top + i}"] = formula
            ws[f"B{top + i}"].fill = KEY_FILL
            if fmt:
                ws[f"B{top + i}"].number_format = fmt
        ws[f"D{top}"] = f"Python: HL = {check['stat']:.2f}, p = {check['p']:.2e}"
        ws[f"D{top}"].font = CHECK_FONT

    result_block(TOTAL + 1, f"F{FIRST}:F{LAST}", f"=COUNT(A{FIRST}:A{LAST})", r.hl)

    # Kiểm tra độ nhạy: gộp hạng 9-10 vì số bad kỳ vọng < 5
    t = TOTAL + 8
    ws[f"A{t}"] = "Kiểm tra độ nhạy: gộp hạng 9-10 (số bad kỳ vọng < 5 làm xấp xỉ χ² kém tin cậy)"
    ws[f"A{t}"].font = Font(bold=True, color="1F4E79")
    _header(ws, t + 1, ["Nhóm", "n", "d", "PD gộp = E/n", "Kỳ vọng E", "Thành phần HL"])
    for k in range(9):
        row = t + 2 + k
        if k < 8:
            src = FIRST + k
            ws[f"A{row}"] = f"=A{src}"
            ws[f"B{row}"], ws[f"C{row}"], ws[f"E{row}"] = f"=B{src}", f"=C{src}", f"=E{src}"
        else:
            ws[f"A{row}"] = "9-10"
            ws[f"B{row}"] = f"=B{LAST - 1}+B{LAST}"
            ws[f"C{row}"] = f"=C{LAST - 1}+C{LAST}"
            ws[f"E{row}"] = f"=E{LAST - 1}+E{LAST}"
        ws[f"D{row}"] = f"=E{row}/B{row}"
        ws[f"F{row}"] = f"=(C{row}-E{row})^2/(B{row}*D{row}*(1-D{row}))"
        ws[f"D{row}"].number_format = "0.0%"
        ws[f"E{row}"].number_format = ws[f"F{row}"].number_format = "0.00"
    m_end = t + 10
    _box(ws, range(t + 2, m_end + 1), 6)
    result_block(m_end + 2, f"F{t + 2}:F{m_end}", f"=COUNT(B{t + 2}:B{m_end})", r.hl_merged)
    _widths(ws, [40, 10, 8, 12, 14, 14, 3, 14])


def _summary(wb: Workbook, r: Results) -> None:
    ws = wb.create_sheet(SUM, 0)
    _title(ws, "Bài I - Kiểm định mô hình PD: Tóm tắt kết quả",
           "Mọi số trong file là công thức; cột xám 'Python' để đối chiếu với code.")
    _header(ws, 4, ["Tiêu chí", "Kết quả", "Ngưỡng / cách đọc", "Đánh giá"])
    g = r.grades
    n_rej = int((g["p_upper"] < 0.05).sum())
    rows = [
        ("Số khách / số bad", f"='{GT}'!C{TOTAL}&\" / \"&'{GT}'!D{TOTAL}", "", ""),
        ("Tỷ lệ vỡ nợ thực tế (ODR)", f"='{GT}'!F{TOTAL}", "", ""),
        ("PD dự báo bình quân", f"='{GT}'!G{TOTAL}", "So với ODR",
         f"PD thấp hơn thực tế ~{1 - r.data['pd'].mean() / r.data['bad'].mean():.0%}"),
        ("AUC (theo hạng)", f"='{AUC}'!B16", "0,5 ngẫu nhiên; 0,7-0,8 tốt",
         "Trung bình, sát ngưỡng 0,7"),
        ("Accuracy Ratio (Gini)", f"='{AUC}'!B17", "AR = 2·AUC − 1", "Chấp nhận được"),
        ("Thứ tự ODR theo hạng", "Giảm đều 1 → 10", "Cần đơn điệu", "Tốt"),
        ("Binomial 1 phía: số hạng bác bỏ", f"='{BIN}'!E15", "trên 10 hạng, α = 5%",
         f"Không đạt ({n_rej}/10 hạng PD quá thấp)"),
        ("Binomial 2 phía: số hạng bác bỏ", f"='{BIN}'!E16", "trên 10 hạng, α = 5%", "Không đạt"),
        ("Hosmer-Lemeshow", f"='{HL}'!B15", f"χ² tới hạn (df=10) ≈ {r.hl['crit_95']:.1f}",
         "Không đạt (p ≈ 0)"),
        ("Hosmer-Lemeshow p-value", f"='{HL}'!B18", "< 0,05 thì bác bỏ", ""),
    ]
    fmts = [None, PCT, PCT, P_FMT, P_FMT, None, "0", "0", "0.00", SCI]
    for i, (row, fmt) in enumerate(zip(rows, fmts)):
        rr = 5 + i
        for j, v in enumerate(row, start=1):
            ws.cell(row=rr, column=j, value=v).border = BOX
        if fmt:
            ws.cell(row=rr, column=2).number_format = fmt
        ws.cell(row=rr, column=2).fill = KEY_FILL
    c = 5 + len(rows) + 1
    conclusion = [
        "KẾT LUẬN",
        "• Mô hình XẾP HẠNG đúng: ODR giảm đều qua 10 hạng, AUC ≈ 0,69 (khả năng phân biệt trung bình).",
        "• Mô hình HIỆU CHUẨN chưa tốt: PD dự báo thấp hơn thực tế có hệ thống ở hạng 3-10; HL bác bỏ mạnh.",
        "• Khuyến nghị: hiệu chuẩn lại PD (recalibration) thay vì xây lại mô hình; kiểm định lại out-of-time.",
        "",
        "CÁCH ĐỌC FILE: MasterScale → Data (gán hạng, PD) → 1_Bang_theo_hang → 2_AUC_AR → 3_Binomial → 4_Hosmer_Lemeshow",
    ]
    for i, line in enumerate(conclusion):
        ws[f"A{c + i}"] = line
        ws[f"A{c + i}"].font = Font(bold=(i == 0), color="1F4E79" if i == 0 else "000000")
    _widths(ws, [34, 16, 28, 36])


def build(r: Results, out: Path) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    _master_scale(wb, r)
    _data(wb, r)
    _grade_table(wb, r)
    _auc(wb, r)
    _binomial(wb, r)
    _hl(wb, r)
    _summary(wb, r)
    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out
