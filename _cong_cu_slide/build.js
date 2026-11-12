// Gộp slide Bài I + Bài II thành một file .pptx chỉnh sửa được (PowerPoint / Google Slides).
// node build.js <bai1.json> <bai2.json> <out.pptx> <skillDir>
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const [B1F, B2F, OUT, SKILL] = process.argv.slice(2);
const { applyTheme } = require(SKILL + "/scripts/apply_theme.js");
const b1 = JSON.parse(fs.readFileSync(B1F, "utf8"));
const b2 = JSON.parse(fs.readFileSync(B2F, "utf8"));

// ---------- theme ----------
// Bảng màu: xanh lá #3C8A48, cam #D89636
const NAVY = "3C8A48", ORANGE = "D89636", DARK = "1F5C30", INK = "1D2433", MUTED = "5B6475", TINT = "EDF5EE",
  CARD = "F4F7F4", LINE = "DCE5DD", GREEN = "2E7D32", RED = "C62828", AMBER = "B7791F", SKY = "A9CBB0";
const THEME = {
  name: "Green Orange", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: INK, lt1: "FFFFFF", dk2: DARK, lt2: TINT, accent1: NAVY, accent2: ORANGE, accent3: SKY,
    accent4: GREEN, accent5: RED, accent6: AMBER, hlink: NAVY, folHlink: "6B4E9B" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Bài test ứng viên – Bài I và Bài II";
const W = 13.333, M = 0.6, CW = W - 2 * M;

// ---------- number format (kiểu Việt Nam) ----------
const vn = (x, d = 2) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d })
  .replace(/,/g, "_").replace(/\./g, ",").replace(/_/g, ".");
const pct = (x, d = 1) => vn(100 * x, d) + "%";
const pval = (p) => (p < 0.001 ? "< 0,001" : vn(p, 3));

// ---------- layouts ----------
const footerOpts = (text) => [
  { text: { text, options: { x: M, y: 7.05, w: 8, h: 0.3, fontSize: 10, color: MUTED, fontFace: "Calibri" } } },
];
pres.defineSlideMaster({
  title: "COVER", background: { color: DARK },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: M, y: 1.7, w: CW, h: 0.5, fontSize: 16, bold: true, color: "F2C27A", fontFace: "Calibri" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.25, w: CW, h: 1.9, fontSize: 40, bold: true, color: "FFFFFF", fontFace: "Cambria", valign: "top" }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: M, y: 4.3, w: CW, h: 1.6, fontSize: 18, color: "E3F0E5", fontFace: "Calibri", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: DARK },
  objects: [
    { placeholder: { options: { name: "kicker", type: "body", x: M, y: 2.3, w: CW, h: 0.5, fontSize: 16, bold: true, color: "F2C27A", fontFace: "Calibri" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.85, w: CW, h: 1.2, fontSize: 36, bold: true, color: "FFFFFF", fontFace: "Cambria", valign: "top" }, text: "" } },
    { placeholder: { options: { name: "sub", type: "body", x: M, y: 4.1, w: CW, h: 1.2, fontSize: 16, color: "E3F0E5", fontFace: "Calibri", valign: "top" }, text: "" } },
  ],
});
for (const [name, foot] of [["CONTENT_B1", "Bài I · Kiểm định mô hình PD"], ["CONTENT_B2", "Bài II · Mô hình dự báo good / bad"], ["CONTENT", "Bài test ứng viên"]]) {
  pres.defineSlideMaster({
    title: name, background: { color: "FFFFFF" },
    objects: [
      ...footerOpts(foot),
      { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: CW, h: 0.8, fontSize: 28, bold: true, color: NAVY, fontFace: "Cambria", valign: "middle" }, text: "" } },
    ],
    slideNumber: { x: W - M - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: MUTED, align: "right" },
  });
}

// ---------- helpers ----------
let SECTION = null;
const slide = (master) => pres.addSlide({ masterName: master, sectionTitle: SECTION });
const content = (title, part) => { const s = slide(part); s.addText(title, { placeholder: "title" }); return s; };
const T = (s, text, o) => s.addText(text, { isTextBox: true, fontFace: "Calibri", fontSize: 14, color: INK, valign: "top", margin: 0, paraSpaceAfter: 6, ...o });
const R = (text, o = {}) => ({ text, options: o }); // run
const B = (text) => R(text, { bold: true });
const bullets = (items) => items.map((it, i) => {
  const runs = Array.isArray(it) ? it : [R(it)];
  return runs.map((r, j) => ({ text: r.text, options: { ...r.options, ...(j === 0 ? { bullet: { indent: 16 } } : {}), ...(j === runs.length - 1 && i < items.length - 1 ? { breakLine: true } : {}) } }));
}).flat();
const para = (items) => items.map((runs, i) => (Array.isArray(runs) ? runs : [R(runs)]).map((r, j, a) =>
  ({ text: r.text, options: { ...r.options, ...(j === a.length - 1 && i < items.length - 1 ? { breakLine: true } : {}) } }))).flat();
const box = (s, x, y, w, h, fill = CARD, name = "card") =>
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08, objectName: name });
const tile = (s, x, y, w, h, big, label, color = NAVY) => {
  box(s, x, y, w, h, TINT, "stat");
  T(s, big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: 0.65, fontSize: 30, bold: true, color, fontFace: "Cambria" });
  T(s, label, { x: x + 0.2, y: y + 0.85, w: w - 0.4, h: h - 0.95, fontSize: 12, color: MUTED });
};
const card = (s, x, y, w, h, head, body, o = {}) => {
  box(s, x, y, w, h, o.fill || CARD);
  T(s, head, { x: x + 0.25, y: y + 0.18, w: w - 0.5, h: 0.4, fontSize: 16, bold: true, color: o.headColor || NAVY });
  T(s, body, { x: x + 0.25, y: y + 0.65, w: w - 0.5, h: h - 0.8, fontSize: o.fontSize || 14 });
};
const numDot = (s, x, y, n, color = ORANGE) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color }, line: { color }, objectName: "step" });
  T(s, String(n), { x, y, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle", paraSpaceAfter: 0 });
};
const flow = (s, steps, y0 = 1.5) => { // 3 x 2 grid of numbered steps
  const cw = (CW - 0.6) / 3, ch = 2.35;
  steps.forEach(([h, d], i) => {
    const x = M + (i % 3) * (cw + 0.3), y = y0 + Math.floor(i / 3) * (ch + 0.3);
    box(s, x, y, cw, ch, CARD);
    numDot(s, x + 0.25, y + 0.25, i + 1);
    T(s, h, { x: x + 0.9, y: y + 0.27, w: cw - 1.1, h: 0.5, fontSize: 17, bold: true, color: NAVY, valign: "middle" });
    T(s, d, { x: x + 0.25, y: y + 0.95, w: cw - 0.5, h: ch - 1.1, fontSize: 14, color: INK });
  });
};
const table = (s, header, rows, o) => {
  const hdr = header.map((h) => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: NAVY } } }));
  const body = rows.map((r, i) => r.map((c) => (typeof c === "object" && c !== null && c.text !== undefined ? c :
    { text: String(c), options: { fill: { color: i % 2 ? "FFFFFF" : "F7F9FB" } } })));
  s.addTable([hdr, ...body], { fontFace: "Calibri", fontSize: 12, color: INK, border: { type: "solid", pt: 0.5, color: LINE },
    margin: [0.04, 0.08, 0.04, 0.08], valign: "middle", ...o });
};
const cell = (text, o = {}) => ({ text: String(text), options: o });
const axis = { catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: "E6EAF0", size: 0.75 },
  catGridLine: { style: "none" }, legendFontFace: "+mn-lt", legendFontSize: 11, legendColor: MUTED,
  titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: INK, valAxisTitleFontFace: "+mn-lt", catAxisTitleFontFace: "+mn-lt",
  valAxisTitleFontSize: 11, catAxisTitleFontSize: 11, valAxisTitleColor: MUTED, catAxisTitleColor: MUTED,
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: INK };
const interp = (pts, x) => { // linear interpolation on sorted [[x,y]]
  for (let i = 1; i < pts.length; i++) if (x <= pts[i][0]) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i]; return x1 === x0 ? y1 : y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }
  return pts[pts.length - 1][1];
};
const scatterLines = (s, xs, series, o) => {
  s.addChart(pres.charts.SCATTER, [{ name: "X", values: xs }, ...series.map((sr) => ({ name: sr.name, values: sr.values }))], {
    ...axis, lineSize: 2, lineDataSymbol: "none", chartColors: series.map((sr) => sr.color),
    valAxisMinVal: 0, valAxisMaxVal: 1, catAxisMinVal: 0, catAxisMaxVal: 1, valAxisLabelFormatCode: "0%", catAxisLabelFormatCode: "0%",
    valAxisMajorUnit: 0.25, catAxisMajorUnit: 0.25, showLegend: true, legendPos: "b", showTitle: !!o.title, ...o,
  });
};
const binLabel = (b, kind) => {
  if (b === "Missing") return "Thiếu dữ liệu";
  const m = b.match(/\((.+), (.+)\]/); if (!m) return b;
  const lo = m[1] === "-inf" ? null : Math.round(+m[1]), hi = m[2] === "inf" ? null : Math.round(+m[2]);
  if (kind === "edu") return { 2: "≤ THPT", 3: "Diploma", null: "Đại học+" }[hi];
  if (lo === null) return hi === 0 ? "0" : `≤ ${hi}`;
  if (hi === null) return `≥ ${lo + 1}`;
  return hi - lo === 1 ? `${hi}` : `${lo + 1}–${hi}`;
};

// =====================================================================
// COVER + OVERVIEW
// =====================================================================
SECTION = "Mở đầu";
pres.addSection({ title: SECTION });
{
  const s = slide("COVER");
  s.addText("BÀI TEST ỨNG VIÊN", { placeholder: "kicker" });
  s.addText("Kiểm định và xây dựng mô hình xác suất vỡ nợ (PD)", { placeholder: "title" });
  s.addText(para(["Bài I: Kiểm định mô hình PD (AUROC, Binomial test, Hosmer-Lemeshow)",
    "Bài II: Mô hình dự báo khách hàng good / bad (Logistic scorecard, Gradient Boosting)"]), { placeholder: "sub" });
}
{
  const s = content("Tóm tắt hai bài", "CONTENT");
  const cw = (CW - 0.4) / 2;
  [[M, "Bài I · Kiểm định mô hình PD", `${vn(b1.n, 0)} khách hàng có điểm và nhãn good/bad`,
    [[vn(b1.auc, 3), "AUC: phân biệt trung bình"], [vn(b1.hl.stat, 0), "Hosmer-Lemeshow (ngưỡng 18,3)"]],
    "Mô hình xếp hạng đúng, nhưng PD bị đánh giá thấp có hệ thống. Khuyến nghị hiệu chuẩn lại, không cần xây lại."],
   [M + cw + 0.4, "Bài II · Mô hình good / bad", `${vn(b2.n, 0)} hồ sơ vay, tháng 1–7/2018`,
    [[vn(b2.split.time["Gradient Boosting"], 3), "AUC Gradient Boosting (tháng 6–7)"], [vn(b2.split.time["Logistic (scorecard)"], 3), "AUC Logistic scorecard"]],
    "Đề xuất Gradient Boosting làm mô hình chính, Logistic scorecard làm mô hình đối chứng. Tín hiệu mạnh nhất: số app vay trong máy."]]
    .forEach(([x, head, sub, stats, msg]) => {
      box(s, x, 1.45, cw, 5.35, CARD);
      T(s, head, { x: x + 0.3, y: 1.65, w: cw - 0.6, h: 0.45, fontSize: 20, bold: true, color: NAVY, fontFace: "Cambria" });
      T(s, sub, { x: x + 0.3, y: 2.15, w: cw - 0.6, h: 0.35, fontSize: 13, color: MUTED });
      stats.forEach(([big, lab], j) => {
        const tx = x + 0.3 + j * ((cw - 0.8) / 2 + 0.2), tw = (cw - 0.8) / 2;
        s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: tx, y: 2.7, w: tw, h: 1.5, fill: { color: "FFFFFF" }, line: { color: "FFFFFF" }, rectRadius: 0.08, objectName: "stat" });
        T(s, big, { x: tx + 0.2, y: 2.85, w: tw - 0.4, h: 0.65, fontSize: 30, bold: true, color: j === 0 ? NAVY : ORANGE, fontFace: "Cambria" });
        T(s, lab, { x: tx + 0.2, y: 3.5, w: tw - 0.4, h: 0.6, fontSize: 12, color: MUTED });
      });
      T(s, msg, { x: x + 0.3, y: 4.5, w: cw - 0.6, h: 2.1, fontSize: 15 });
    });
}

// =====================================================================
// BÀI I
// =====================================================================
SECTION = "Bài I · Kiểm định mô hình PD";
pres.addSection({ title: SECTION });
const G = b1.grades;
const nRej1 = G.filter((g) => g.p_upper < 0.05).length, nRej2 = G.filter((g) => g.p_two < 0.05).length;
const under = 1 - b1.avg_pd / b1.odr;
{
  const s = slide("SECTION");
  s.addText("PHẦN I", { placeholder: "kicker" });
  s.addText("Kiểm định mô hình xác suất vỡ nợ (PD)", { placeholder: "title" });
  s.addText("Accuracy Ratio / AUROC · Binomial test (1 phía, 2 phía) · Hosmer-Lemeshow test", { placeholder: "sub" });
}
{
  const s = content("Dữ liệu và câu hỏi kiểm định", "CONTENT_B1");
  const tw = (CW - 0.9) / 4;
  [[vn(b1.n, 0), "khách hàng"], [String(b1.n_bad), "khách bad"], [pct(b1.odr, 2), "tỷ lệ vỡ nợ thực tế (ODR)"], [pct(b1.avg_pd, 2), "PD dự báo bình quân"]]
    .forEach(([b, l], i) => tile(s, M + i * (tw + 0.3), 1.45, tw, 1.45, b, l, i === 3 ? ORANGE : NAVY));
  const cw = (CW - 0.4) / 2;
  card(s, M, 3.2, cw, 2.6, "1 · Khả năng phân biệt (discrimination)",
    para(["Mô hình có xếp khách bad vào nhóm rủi ro cao hơn khách good không?", [R("→ Accuracy Ratio / AUROC", { bold: true, color: ORANGE })]]));
  card(s, M + cw + 0.4, 3.2, cw, 2.6, "2 · Hiệu chuẩn (calibration)",
    para(["Mức PD dự báo có khớp với tỷ lệ vỡ nợ thực tế không?", [R("→ Binomial test (từng hạng), Hosmer-Lemeshow (toàn danh mục)", { bold: true, color: ORANGE })]]));
  T(s, "Một mô hình có thể xếp hạng tốt mà PD vẫn sai, nên cần cả hai nhóm kiểm định.", { x: M, y: 6.1, w: CW, h: 0.5, fontSize: 13, color: MUTED });
}
{
  const s = content("Quy trình xử lý", "CONTENT_B1");
  flow(s, [["Gán hạng", "Điểm → hạng theo Master Scale (10 hạng, điểm càng cao càng an toàn)"],
    ["Gán PD", "Mỗi hạng có một PD dự báo, từ 27,5% (hạng 1) đến 0,1% (hạng 10)"],
    ["Tổng hợp theo hạng", "n, số bad d, ODR = d / n, số bad kỳ vọng E = n × PD"],
    ["AUC / AR", "Đường ROC và CAP từ phân phối lũy kế bad / good"],
    ["Binomial test", "So sánh d với phân phối Binomial(n, PD) ở từng hạng"],
    ["Hosmer-Lemeshow", "Gộp sai lệch của 10 hạng thành một thống kê χ²"]]);
  T(s, "Mọi bước được làm lại bằng công thức trong file Excel đính kèm và đối chiếu với code Python.", { x: M, y: 6.6, w: CW, h: 0.35, fontSize: 12, color: MUTED });
}
{
  const s = content("Bảng tổng hợp theo hạng", "CONTENT_B1");
  const n = G.reduce((a, g) => a + g.n, 0), d = G.reduce((a, g) => a + g.d, 0), e = G.reduce((a, g) => a + g.expected, 0);
  const rows = G.map((g) => [g.grade, g.band, g.n, g.d, pct(g.odr), pct(g.pd), vn(g.expected, 1)]);
  rows.push(["Tổng", "", n, d, pct(d / n), pct(e / n), vn(e, 1)].map((c) => cell(c, { bold: true, fill: { color: TINT } })));
  table(s, ["Hạng", "Điểm", "n", "Bad", "ODR", "PD", "Kỳ vọng"], rows, { x: M, y: 1.45, w: 5.6, colW: [0.6, 1.1, 0.7, 0.6, 0.85, 0.85, 0.9], fontSize: 12, rowH: 0.36 });
  s.addChart([{ type: pres.charts.BAR, data: [{ name: "ODR thực tế", labels: G.map((g) => String(g.grade)), values: G.map((g) => g.odr) }], options: { chartColors: [NAVY], barGapWidthPct: 60 } },
    { type: pres.charts.LINE, data: [{ name: "PD dự báo", labels: G.map((g) => String(g.grade)), values: G.map((g) => g.pd) }], options: { chartColors: [ORANGE], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7 } }],
    { ...axis, x: 6.6, y: 1.4, w: 6.1, h: 4.1, valAxisLabelFormatCode: "0%", valAxisMaxVal: 0.3, showLegend: true, legendPos: "b",
      showCatAxisTitle: true, catAxisTitle: "Hạng (1 = rủi ro nhất)", showTitle: true, title: "ODR thực tế so với PD dự báo" });
  T(s, [B("ODR giảm đều từ hạng 1 đến 10"), R(", nên thứ tự xếp hạng đúng. Nhưng ODR nằm trên PD ở 9/10 hạng, nghĩa là "), B("PD bị ước tính thấp"), R(".")],
    { x: 6.7, y: 5.7, w: 5.9, h: 1.0, fontSize: 14 });
}
{
  const s = content("Accuracy Ratio / AUROC", "CONTENT_B1");
  T(s, para([[B("AUC"), R(" = xác suất một khách bad ngẫu nhiên bị chấm rủi ro hơn một khách good ngẫu nhiên. 0,5 = đoán bừa, 1 = hoàn hảo.")],
    [B("AR (Accuracy Ratio)"), R(" = diện tích giữa CAP mô hình và đường ngẫu nhiên, chia cho diện tích tương ứng của mô hình hoàn hảo. AR = 2 × AUC − 1.")],
    [B("Cách tính:"), R(" xếp hạng từ rủi ro nhất đến an toàn nhất, lũy kế % bad (TPR), % good (FPR), % khách; diện tích theo quy tắc hình thang Σ Δx·(yᵢ + yᵢ₋₁)/2.")]]),
  { x: M, y: 1.45, w: 5.3, h: 2.9, fontSize: 14, paraSpaceAfter: 8 });
  tile(s, M, 4.45, 2.5, 1.4, vn(b1.auc, 3), `AUC · CI 95%: ${vn(b1.auc_ci[0], 3)}–${vn(b1.auc_ci[1], 3)}`);
  tile(s, M + 2.8, 4.45, 2.5, 1.4, vn(b1.ar, 3), "Accuracy Ratio");
  T(s, `Theo 10 hạng: AUC = ${vn(b1.auc_grade, 3)}, AR từ CAP = ${vn(b1.ar_cap, 3)}. Đánh giá: phân biệt trung bình, sát ngưỡng 0,7 thường dùng cho mô hình bán lẻ.`,
    { x: M, y: 6.0, w: 5.3, h: 0.8, fontSize: 12, color: MUTED });
  const C = b1.curve, dr = b1.odr;
  const roc = C.map((c) => [c.cum_good, c.cum_bad]), cap = C.map((c) => [c.cum_all, c.cum_bad]);
  scatterLines(s, roc.map((p) => p[0]), [{ name: "Mô hình", values: roc.map((p) => p[1]), color: NAVY }, { name: "Đoán bừa", values: roc.map((p) => p[0]), color: "9AA3B2" }],
    { x: 6.2, y: 1.4, w: 3.3, h: 4.4, title: "Đường ROC", showCatAxisTitle: true, catAxisTitle: "% good bị từ chối nhầm", showValAxisTitle: true, valAxisTitle: "% bad bị bắt" });
  const xs = [...new Set([...cap.map((p) => p[0]), dr])].sort((a, b) => a - b);
  scatterLines(s, xs, [{ name: "Mô hình", values: xs.map((x) => interp(cap, x)), color: NAVY }, { name: "Hoàn hảo", values: xs.map((x) => Math.min(x / dr, 1)), color: ORANGE },
    { name: "Ngẫu nhiên", values: xs, color: "9AA3B2" }],
    { x: 9.5, y: 1.4, w: 3.3, h: 4.4, title: "Đường CAP", showCatAxisTitle: true, catAxisTitle: "% khách bị từ chối", showValAxisTitle: false });
}
{
  const s = content("Vì sao dùng AUC / ROC?", "CONTENT_B1");
  const c = Object.fromEntries(b1.curve.map((x) => [x.grade, x]));
  T(s, [B("Đọc đường ROC: "), R("lần lượt đặt ngưỡng \"từ chối hạng 1 → k\". Số người bị từ chối luôn là phần cộng dồn từ hạng 1.")], { x: M, y: 1.45, w: 5.8, h: 0.8 });
  table(s, ["Ngưỡng", "Từ chối nhầm good (FPR)", "Bắt được bad (TPR)"],
    [1, 2, 4].map((k) => [`đến hạng ${k}`, pct(c[k].cum_good), pct(c[k].cum_bad)]), { x: M, y: 2.35, w: 5.8, colW: [1.6, 2.1, 2.1], fontSize: 13 });
  T(s, `Mỗi ngưỡng là một điểm (FPR, TPR); nối 10 điểm thành đường ROC. AUC = diện tích dưới đường = xác suất một khách bad bị chấm rủi ro hơn một khách good (${pct(b1.auc, 0)} số cặp được xếp đúng).`,
    { x: M, y: 4.0, w: 5.8, h: 1.4, fontSize: 13, color: MUTED });
  card(s, 6.8, 1.45, 5.9, 5.3, "Điểm lợi", bullets([
    [B("Đo đúng thứ ngân hàng dùng: "), R("điểm số dùng để xếp hạng rồi duyệt / từ chối / định giá.")],
    [B("Không phụ thuộc ngưỡng cắt: "), R("tính trên mọi ngưỡng, còn ngưỡng là quyết định kinh doanh.")],
    [B("Không bị đánh lừa khi bad hiếm: "), R(`đoán ai cũng good đúng ${pct(1 - b1.odr, 0)} nhưng AUC chỉ 0,5.`)],
    [B("Dễ diễn giải: "), R(`AUC ${vn(b1.auc, 2)} = ${pct(b1.auc, 0)} số cặp (bad, good) được xếp đúng thứ tự.`)],
    [B("Giới hạn: "), R("AUC chỉ đo thứ tự, không cho biết con số PD đúng hay sai, nên cần thêm Binomial và Hosmer-Lemeshow.", { color: MUTED })]]),
  { fontSize: 14 });
}
{
  const s = content("Binomial test theo từng hạng", "CONTENT_B1");
  T(s, para([[B("1 phía: "), R("H₀: PD thật ≤ PD dự báo. H₁: mô hình đánh giá thấp rủi ro (hướng thận trọng).")],
    [B("2 phía: "), R("H₀: PD thật = PD dự báo. Bắt cả trường hợp quá cao lẫn quá thấp.")],
    [R("p = P(X ≥ d), X ~ Bin(n, PD) · Excel: 1 − BINOM.DIST(d−1, n, PD, TRUE) · Ngưỡng 95%: BINOM.INV(n, PD, 0,95)", { color: MUTED, fontSize: 12 })]]),
  { x: M, y: 1.4, w: CW, h: 1.3, fontSize: 14, paraSpaceAfter: 4 });
  const lc = { "Xanh": GREEN, "Vàng": AMBER, "Đỏ": RED };
  table(s, ["Hạng", "n", "d", "PD", "ODR", "Ngưỡng d (95%)", "p 1 phía", "p 2 phía", "Kết luận 2 phía", "Đèn"],
    G.map((g) => {
      let two = g.p_two < 0.05 ? "Bác bỏ" + (g.d > g.expected ? " (PD thấp)" : " (PD cao)") : "Không bác bỏ";
      return [g.grade, g.n, g.d, pct(g.pd), pct(g.odr), g.k_crit_95, pval(g.p_upper), pval(g.p_two), two,
        cell("● " + g.light, { color: lc[g.light], bold: true })];
    }), { x: M, y: 2.75, w: CW, colW: [0.7, 0.8, 0.7, 0.95, 0.95, 1.5, 1.2, 1.2, 2.6, 1.53], fontSize: 12, rowH: 0.33 });
  T(s, [B(`Kết quả (α = 5%): `), R(`1 phía bác bỏ ${nRej1}/10 hạng, 2 phía bác bỏ ${nRej2}/10 hạng. Hạng 1 là trường hợp ngược lại: PD hơi cao hơn thực tế (thận trọng).`)],
    { x: M, y: 6.5, w: CW, h: 0.45, fontSize: 13 });
}
{
  const s = content("Hosmer-Lemeshow test", "CONTENT_B1");
  box(s, M, 1.45, 6.0, 0.8, TINT, "formula");
  T(s, "HL = Σᵢ (dᵢ − nᵢ·PDᵢ)² / (nᵢ·PDᵢ·(1 − PDᵢ))  ~  χ²(df)", { x: M + 0.25, y: 1.45, w: 5.6, h: 0.8, fontSize: 17, valign: "middle", fontFace: "Cambria", paraSpaceAfter: 0 });
  const top = [...G].sort((a, b) => b.hl - a.hl).slice(0, 3).map((g) => `hạng ${g.grade} (${vn(g.hl, 1)})`).join(", ");
  T(s, para([[R("H₀: PD dự báo khớp với thực tế ở "), B("tất cả"), R(" các hạng.")],
    [R("PD được cố định từ trước (kiểm định ngoài mẫu) nên "), B("df = số hạng = 10"), R(" (df = k − 2 chỉ dùng khi kiểm định trên mẫu phát triển).")],
    "Excel: CHISQ.DIST.RT(HL, 10)", `Đóng góp lớn nhất: ${top}.`]), { x: M, y: 2.5, w: 6.0, h: 3.5, fontSize: 14, paraSpaceAfter: 8 });
  tile(s, 7.1, 1.45, 2.7, 1.5, vn(b1.hl.stat, 1), `HL (10 hạng) · ngưỡng χ² 95% = ${vn(b1.hl.crit_95, 1)}`, RED);
  tile(s, 10.0, 1.45, 2.7, 1.5, "≈ 0", "p-value", RED);
  card(s, 7.1, 3.25, 5.6, 2.9, "Cách đọc", para([`Nếu PD dự báo đúng, HL thường dao động quanh 10 (bằng số hạng) và chỉ vượt ${vn(b1.hl.crit_95, 1)} trong 5% trường hợp.`,
    [R(`→ HL = ${vn(b1.hl.stat, 1)}, vượt xa ngưỡng: bác bỏ H₀, PD chưa được hiệu chuẩn tốt.`, { bold: true, color: ORANGE })]]));
}
{
  const s = content("Giả định và hạn chế", "CONTENT_B1");
  [["Vỡ nợ độc lập", "Binomial và HL giả định các khách hàng vỡ nợ độc lập. Thực tế có tương quan (cùng chịu chu kỳ kinh tế), làm phương sai số vỡ nợ lớn hơn, nên test dễ bác bỏ hơn mức cần. Có thể điều chỉnh bằng mô hình một nhân tố Vasicek (hệ số tương quan ρ)."],
   ["Một kỳ dữ liệu", "Chưa biết dữ liệu thuộc giai đoạn nào của chu kỳ kinh tế (PIT hay TTC); cần kiểm định thêm theo thời gian (out-of-time) và độ ổn định quần thể."],
   ["AUC theo hạng và theo điểm", "Chênh nhau rất ít, nên việc chia 10 hạng không làm mất thông tin xếp hạng."]]
    .forEach(([h, d], i) => {
      const y = 1.5 + i * 1.75;
      numDot(s, M, y + 0.05, i + 1, NAVY);
      T(s, h, { x: M + 0.75, y, w: CW - 0.75, h: 0.45, fontSize: 17, bold: true, color: NAVY });
      T(s, d, { x: M + 0.75, y: y + 0.5, w: CW - 0.75, h: 1.1, fontSize: 14 });
    });
}
{
  const s = content("Kết luận và khuyến nghị", "CONTENT_B1");
  const v = (t, c) => cell(t, { bold: true, color: c });
  table(s, ["Tiêu chí", "Kết quả", "Đánh giá"], [
    ["Khả năng phân biệt", `AUC ${vn(b1.auc, 3)} · AR ${vn(b1.ar, 3)}`, v("Trung bình, chấp nhận được", AMBER)],
    ["Thứ tự xếp hạng", "ODR giảm đều qua 10 hạng", v("Đạt", GREEN)],
    ["Hiệu chuẩn từng hạng", `Binomial 1 phía bác bỏ ${nRej1}/10 hạng`, v("Không đạt", RED)],
    ["Hiệu chuẩn toàn danh mục", `HL ${vn(b1.hl.stat, 1)}, p ≈ 0`, v("Không đạt", RED)],
    ["Mức PD trung bình", `PD ${pct(b1.avg_pd, 2)} so với ODR ${pct(b1.odr, 2)}`, v(`Thấp hơn khoảng ${pct(under, 0)}`, RED)]],
  { x: M, y: 1.45, w: CW, colW: [3.2, 5.2, 3.73], fontSize: 14, rowH: 0.42 });
  box(s, M, 4.3, CW, 2.45, "FBF0DF");
  T(s, para([[B("Mô hình xếp hạng đúng nhưng PD bị đánh giá thấp có hệ thống.")],
    [R("Khuyến nghị: "), B("hiệu chuẩn lại"), R(" (recalibration) thay vì xây lại mô hình. Ví dụ: ước lượng lại quan hệ logit(PD) theo điểm, hoặc dịch chuyển PD về xu hướng trung tâm mới, sau đó kiểm định lại out-of-time. Song song, xem xét bổ sung biến để cải thiện AUC.")]]),
  { x: M + 0.3, y: 4.5, w: CW - 0.6, h: 2.1, fontSize: 15, paraSpaceAfter: 8 });
}
{
  const s = content("Phụ lục: công thức Excel", "CONTENT_B1");
  table(s, ["Bước", "Công thức"], [["Gán hạng", "=MATCH(Điểm, CậnDưới, 1)"], ["Gán PD", "=INDEX(PD, Hạng)"],
    ["n, d theo hạng", "=COUNTIF(Hạng, h) · =COUNTIFS(Hạng, h, Bad, 1)"], ["Diện tích ROC / CAP", "=(x − x₋₁)·(y + y₋₁)/2, AUC = tổng"],
    ["AR từ CAP", "=(DiệnTíchCAP − 0,5)/(0,5 − DR/2)"], ["Binomial 1 phía", "=1 − BINOM.DIST(d − 1, n, PD, TRUE)"], ["Ngưỡng 95%", "=BINOM.INV(n, PD, 0,95)"],
    ["Binomial 2 phía", "=MIN(1, 2·MIN(P(X≤d), P(X≥d)))"], ["Thành phần HL", "=(d − n·PD)^2/(n·PD·(1 − PD))"], ["p-value HL", "=CHISQ.DIST.RT(HL, 10)"]]
    .map(([a, b]) => [a, cell(b, { fontFace: "Courier New", fontSize: 12 })]), { x: M, y: 1.45, w: CW, colW: [3.2, 8.93], fontSize: 13, rowH: 0.42 });
  T(s, "Chi tiết trong file Bai1_PD_Validation.xlsx: mỗi sheet có cột \"Python\" màu xám để đối chiếu.", { x: M, y: 6.4, w: CW, h: 0.4, fontSize: 12, color: MUTED });
}

// =====================================================================
// BÀI II
// =====================================================================
SECTION = "Bài II · Mô hình good / bad";
pres.addSection({ title: SECTION });
const P = Object.fromEntries(b2.perf.map((x) => [x.model + "|" + x.set, x]));
const LR = "Logistic (scorecard)", GB = "Gradient Boosting";
const lrT = P[LR + "|Test OOT"], gbT = P[GB + "|Test OOT"], lrTr = P[LR + "|Train"], gbTr = P[GB + "|Train"];
const loan = b2.woe.n_loan_apps.bins;
{
  const s = slide("SECTION");
  s.addText("PHẦN II", { placeholder: "kicker" });
  s.addText("Mô hình dự báo khách hàng good / bad", { placeholder: "title" });
  s.addText(`${vn(b2.n, 0)} hồ sơ vay · 01/2018 – 07/2018 · Python (pandas, scikit-learn)`, { placeholder: "sub" });
}
{
  const s = content("Bài toán và dữ liệu", "CONTENT_B2");
  tile(s, M, 1.45, 2.6, 1.4, vn(b2.n, 0), "hồ sơ vay");
  tile(s, M + 2.9, 1.45, 2.6, 1.4, pct(b2.bad_rate), "tỷ lệ bad", ORANGE);
  T(s, para([[B("Mục tiêu: "), R("dự báo xác suất một người nộp đơn trở thành khách hàng bad (flag_bad = 1).")], [B("3 nguồn dữ liệu (20 cột):")]]),
    { x: M, y: 3.1, w: 5.5, h: 1.0, fontSize: 14 });
  T(s, bullets([[B("de_ "), R("tuổi, giới tính, lương, công việc, học vấn, hôn nhân…")], [B("ph_ "), R("danh bạ, thiết bị, thống kê cuộc gọi (JSON), danh sách app")],
    [B("fb_ "), R("giới tính, ngày sinh, ngày cập nhật, tình trạng quan hệ")]]), { x: M, y: 4.05, w: 5.5, h: 1.6, fontSize: 14 });
  T(s, "Mã vùng điện thoại 99,9% là \"id\", nên dữ liệu nhiều khả năng đến từ một công ty cho vay qua app ở Indonesia.", { x: M, y: 5.8, w: 5.5, h: 0.8, fontSize: 12, color: MUTED });
  const mo = b2.monthly, lab = mo.map((m) => "T" + +m.month.slice(-2));
  s.addChart([{ type: pres.charts.BAR, data: [{ name: "Số hồ sơ", labels: lab, values: mo.map((m) => m.n) }], options: { chartColors: [NAVY], barGapWidthPct: 50 } },
    { type: pres.charts.LINE, data: [{ name: "Tỷ lệ bad", labels: lab, values: mo.map((m) => m.bad_rate) }], options: { chartColors: [ORANGE], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7, secondaryValAxis: true, secondaryCatAxis: true } }],
    { ...axis, x: 6.5, y: 1.4, w: 6.2, h: 4.4, showLegend: true, legendPos: "b", showTitle: true, title: "Số hồ sơ và tỷ lệ bad theo tháng",
      valAxes: [{ showValAxisTitle: true, valAxisTitle: "Số hồ sơ", valAxisLabelFormatCode: "#,##0" }, { showValAxisTitle: true, valAxisTitle: "Tỷ lệ bad", valAxisMinVal: 0, valAxisMaxVal: 0.2, valAxisLabelFormatCode: "0%", valGridLine: { style: "none" } }],
      catAxes: [{ catAxisTitle: "Tháng" }, { catAxisHidden: true }] });
  T(s, "Tỷ lệ bad dao động 11–15% theo tháng. Dữ liệu có thứ tự thời gian, nên cần kiểm tra mô hình trên các tháng sau.", { x: 6.6, y: 5.95, w: 6.0, h: 0.8, fontSize: 13, color: MUTED });
}
{
  const s = content("Luồng xử lý", "CONTENT_B2");
  flow(s, [["Khám phá dữ liệu", "Thiếu dữ liệu, phân phối, tỷ lệ bad theo tháng và theo nhóm"], ["Làm sạch + tạo biến", "Tách JSON, đếm app, kiểm tra độ nhất quán FB với thông tin khai báo"],
    ["Chia theo thời gian", "Tháng 1–5 để xây mô hình, tháng 6–7 để kiểm tra"], ["Chọn biến bằng IV", "Loại biến yếu, trùng lặp, ngược dấu"],
    ["Hai mô hình", "Logistic scorecard (dễ giải thích) và Gradient Boosting (mạnh hơn)"], ["Đánh giá + chọn", "AUC, PD dự báo có khớp thực tế không, mô hình dựa vào biến nào"]]);
}
{
  const s = content("Làm sạch dữ liệu và tạo biến", "CONTENT_B2");
  table(s, ["Dữ liệu gốc", "Xử lý / biến mới", "Lý do"], [
    ["de_accomodation_type, ph_country_code", "Bỏ", "Gần như chỉ một giá trị, không có thông tin"],
    ["de_num_friends = −1, lương = 0", "Coi là thiếu dữ liệu", "Giá trị không hợp lý"],
    ["de_monthly_salary", "log(lương)", "Phân phối lệch phải mạnh"],
    ["Hôn nhân 3–4, công việc mã 4", "Gộp nhóm", "Nhóm quá ít hồ sơ; mã 4 không có trong đề (2 hồ sơ) → gộp vào Full-time"],
    ["de_date_joined", "Tháng (để chia tập), giờ, ngày trong tuần", "Hành vi nộp đơn"],
    ["ph_app_list", "Tổng số app, số app vay, ngân hàng, game", "Vay nhiều nơi là dấu hiệu rủi ro; bỏ app Kredivo (trên 98% máy)"],
    ["ph_call_log_stats (JSON)", "Tổng cuộc gọi, % gọi đến/đi ngày/đêm, thời lượng", "Mức độ hoạt động xã hội"],
    ["ph_other_device_info", "Hãng điện thoại (8 hãng phổ biến + other)", "Đại diện thu nhập"],
    ["fb_dob, fb_gender", "Lệch tuổi FB với tuổi khai báo; giới tính FB có khớp không", "Dấu hiệu khai báo sai"],
    ["fb_last_updated_date", "Số ngày từ lần cập nhật FB đến lúc nộp đơn", "0,2% cập nhật sau ngày nộp đơn → đặt về 0, tránh dùng thông tin \"tương lai\""]],
  { x: M, y: 1.4, w: CW, colW: [3.4, 4.1, 4.63], fontSize: 12, rowH: 0.47 });
}
{
  const s = content("Chia dữ liệu: vì sao theo thời gian?", "CONTENT_B2");
  const st = b2.sets;
  table(s, ["Tập", "Thời gian", "Số hồ sơ", "Tỷ lệ bad", "Dùng để"], [
    ["Training", "T1–T5 (75%)", vn(st.Train.n, 0), pct(st.Train.bad_rate), "Học mô hình"],
    ["Validation", "T1–T5 (25%)", vn(st.Validation.n, 0), pct(st.Validation.bad_rate), "So sánh, kiểm tra học thuộc"],
    ["Test (out-of-time)", "T6–T7", vn(st["Test OOT"].n, 0), pct(st["Test OOT"].bad_rate), "Đánh giá cuối cùng"]],
  { x: M, y: 1.45, w: 6.6, colW: [1.6, 1.3, 1.1, 1.0, 1.6], fontSize: 13, rowH: 0.45 });
  card(s, 7.5, 1.45, 5.2, 4.2, "Quyết định", para(["Giữ riêng 2 tháng cuối làm test set (out-of-time), thay vì chia ngẫu nhiên.",
    [R("Khi dùng thật, mô hình luôn chấm cho khách hàng "), R("trong tương lai", { italic: true }), R(". Test trên các tháng mô hình chưa thấy mô phỏng đúng tình huống đó, và phát hiện được nếu khách hàng thay đổi theo thời gian.")]]));
  T(s, "Test set chỉ dùng một lần ở cuối, không dùng để chọn biến hay chỉnh tham số. So sánh với cách chia ngẫu nhiên ở slide \"Kiểm tra thêm\".",
    { x: M, y: 3.6, w: 6.6, h: 1.0, fontSize: 13, color: MUTED });
}
{
  const s = content("Chọn biến bằng Information Value (IV)", "CONTENT_B2");
  T(s, para([[B("IV"), R(" đo một biến tách good và bad tốt đến đâu: < 0,02 không có ích, 0,02–0,1 yếu, 0,1–0,3 trung bình, 0,3–0,5 mạnh, > 0,5 "), B("đáng ngờ"), R(" (kiểm tra rò rỉ dữ liệu hoặc nhóm quá nhỏ).")],
    [B("3 quy tắc loại biến:")]]), { x: M, y: 1.45, w: 5.0, h: 1.9, fontSize: 14 });
  T(s, [R("IV < 0,02", { bullet: { type: "number" }, breakLine: true }), R("Tương quan > 0,6 với một biến đã chọn có IV cao hơn", { bullet: { type: "number" }, breakLine: true }),
    R(`Hệ số logistic ngược dấu (vô lý về nghiệp vụ): ${b2.sign_dropped.join(", ")}`, { bullet: { type: "number" } })], { x: M, y: 3.35, w: 5.0, h: 2.0, fontSize: 14 });
  T(s, [B(`Còn lại ${b2.n_selected} biến. `), R("Biến nhân khẩu học như tuổi, lương, giới tính gần như không có sức dự báo trong dữ liệu này.", { color: MUTED })],
    { x: M, y: 5.55, w: 5.0, h: 1.1, fontSize: 13 });
  const iv = [...b2.iv].reverse(), labs = iv.map((v) => v.var);
  const ser = (name, k) => ({ name, labels: labs, values: iv.map((v) => (v.cat === k ? v.iv : 0)) });
  s.addChart(pres.charts.BAR, [ser("Giữ", "keep"), ser("Loại: ngược dấu", "sign"), ser("Loại: IV < 0,02", "low")], {
    ...axis, x: 5.9, y: 1.35, w: 6.8, h: 5.5, barDir: "bar", barGrouping: "stacked", chartColors: [NAVY, ORANGE, "B4BCC8"], barGapWidthPct: 35,
    catAxisLabelFontSize: 10, valAxisLabelFormatCode: "0.00", showLegend: true, legendPos: "b", showTitle: true, title: "IV của 20 biến mạnh nhất",
  });
}
{
  const s = content("Biến mạnh nhất nói gì?", "CONTENT_B2");
  const specs = [["n_loan_apps", "Số app vay trong máy", null], ["n_apps", "Tổng số app", null], ["education", "Học vấn", "edu"]];
  const cw = (CW - 0.6) / 3;
  specs.forEach(([k, title, kind], i) => {
    const bins = b2.woe[k].bins.filter((b) => b.bin !== "Missing");
    s.addChart(pres.charts.BAR, [{ name: "Tỷ lệ bad", labels: bins.map((b) => binLabel(b.bin, kind)), values: bins.map((b) => b.bad_rate) }], {
      ...axis, x: M + i * (cw + 0.3), y: 1.35, w: cw, h: 3.3, chartColors: [i === 0 ? ORANGE : NAVY], barGapWidthPct: 45, showLegend: false,
      valAxisLabelFormatCode: "0%", valAxisMinVal: 0, valAxisMaxVal: i === 0 ? 0.32 : 0.2, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%",
      showTitle: true, title: `${title} (IV ${vn(b2.woe[k].iv, 2)})`, catAxisLabelFontSize: 10,
    });
  });
  const cw2 = (CW - 0.4) / 2;
  T(s, [B("Số app vay trong máy"), R(` là tín hiệu mạnh nhất. Người không có app vay có tỷ lệ bad ${pct(loan[0].bad_rate)}, người có từ 3 app trở lên là ${pct(loan[loan.length - 1].bad_rate)}. Người đang vay nhiều nơi cùng lúc thì dễ mất khả năng trả nợ.`)],
    { x: M, y: 4.9, w: cw2, h: 1.8, fontSize: 14 });
  T(s, [B("Tổng số app"), R(" càng ít càng rủi ro (có thể là máy mới, cài vội để vay). "), B("Học vấn"), R(" cao thì tỷ lệ bad thấp hơn. Cả ba quan hệ đều đi một chiều và có ý nghĩa nghiệp vụ.")],
    { x: M + cw2 + 0.4, y: 4.9, w: cw2, h: 1.8, fontSize: 14 });
}
{
  const s = content("Chọn thuật toán", "CONTENT_B2");
  const h = (t) => cell(t, { bold: true, color: NAVY, fill: { color: TINT } });
  table(s, ["", "Logistic Regression trên WOE (scorecard)", "Gradient Boosting (HistGradientBoosting)"], [
    [h("Cách hoạt động"), "Mỗi biến được chia nhóm, mỗi nhóm cộng/trừ một số điểm, tổng điểm → PD", "Hàng trăm cây quyết định nhỏ, cây sau sửa lỗi của cây trước"],
    [h("Ưu điểm"), "Dễ giải thích từng điểm số; chuẩn ngành ngân hàng; ổn định", "Bắt được quan hệ phi tuyến và tương tác giữa các biến; tự xử lý dữ liệu thiếu"],
    [h("Nhược điểm"), "Bỏ lỡ tương tác giữa các biến", "Khó giải thích hơn; dễ học thuộc nếu không kiểm soát"],
    [h("Kiểm soát học thuộc"), "Ít biến, WOE gộp nhóm", "Cây nhỏ (7 lá), mỗi lá ≥ 500 hồ sơ, dừng sớm theo validation"]],
  { x: M, y: 1.45, w: CW, colW: [2.4, 4.86, 4.87], fontSize: 14, rowH: 0.85 });
  box(s, M, 5.55, CW, 1.15, "FBF0DF");
  T(s, [B("Quyết định: "), R("xây cả hai. Logistic là mô hình nền dễ giải thích, Boosting là mô hình thách thức, để xem độ phức tạp thêm vào có đáng không.")],
    { x: M + 0.3, y: 5.7, w: CW - 0.6, h: 0.9, fontSize: 15 });
}
{
  const s = content("Kết quả", "CONTENT_B2");
  table(s, ["Mô hình", "Tập", "AUC", "AR"], b2.perf.map((x) => [x.model, x.set === "Test OOT" ? "Test (T6–T7)" : x.set,
    x.set === "Test OOT" ? cell(vn(x.auc, 3), { bold: true }) : vn(x.auc, 3), vn(x.gini, 3)]), { x: M, y: 1.45, w: 6.0, colW: [2.4, 1.5, 1.05, 1.05], fontSize: 13, rowH: 0.4 });
  T(s, para([[B("AUC"), R(" = xác suất một khách bad bị chấm rủi ro hơn một khách good. "), B("AR"), R(" = 2 × AUC − 1, như ở Bài I.")],
    [R("Trên test set, Boosting cao hơn Logistic "), B(`${vn(gbT.auc - lrT.auc, 3)} AUC`), R(` (AR ${vn(gbT.gini, 2)} so với ${vn(lrT.gini, 2)}).`)],
    [R(`Logistic gần như không chênh giữa train và test (${vn(lrTr.auc, 3)} → ${vn(lrT.auc, 3)}). Boosting chênh nhiều hơn (${vn(gbTr.auc, 3)} → ${vn(gbT.auc, 3)}): có học thuộc một phần nhưng vẫn tốt hơn trên dữ liệu mới.`)]]),
  { x: M, y: 4.15, w: 6.0, h: 2.7, fontSize: 13, paraSpaceAfter: 8 });
  const xs = Array.from({ length: 51 }, (_, i) => i / 50);
  scatterLines(s, xs, [{ name: `Logistic: AUC ${vn(lrT.auc, 3)}`, values: xs.map((x) => interp(b2.roc[LR], x)), color: NAVY },
    { name: `Boosting: AUC ${vn(gbT.auc, 3)}`, values: xs.map((x) => interp(b2.roc[GB], x)), color: ORANGE }, { name: "Đoán bừa", values: xs, color: "9AA3B2" }],
  { x: 7.0, y: 1.35, w: 5.7, h: 5.4, title: "Đường ROC trên test set (tháng 6–7)", showCatAxisTitle: true, catAxisTitle: "% good bị từ chối nhầm", showValAxisTitle: true, valAxisTitle: "% bad bị bắt" });
}
{
  const s = content("Con số PD dự báo có khớp thực tế không?", "CONTENT_B2");
  const cw = (CW - 0.4) / 2;
  [[LR, M], [GB, M + cw + 0.4]].forEach(([m, x]) => {
    const d = b2.deciles[m], lab = d.map((r) => String(r.g));
    s.addChart([{ type: pres.charts.BAR, data: [{ name: "Tỷ lệ bad thực tế", labels: lab, values: d.map((r) => r.bad_rate) }], options: { chartColors: [NAVY], barGapWidthPct: 40 } },
      { type: pres.charts.LINE, data: [{ name: "PD dự báo", labels: lab, values: d.map((r) => r.pd) }], options: { chartColors: [ORANGE], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7 } }],
    { ...axis, x, y: 1.35, w: cw, h: 3.6, valAxisLabelFormatCode: "0%", valAxisMaxVal: 0.45, showLegend: true, legendPos: "b", showTitle: true,
      title: `${m} · Hosmer-Lemeshow ${vn(b2.hl[m], 1)} (dưới 18,3 → đạt)`, showCatAxisTitle: true, catAxisTitle: "Nhóm 10% (1 = rủi ro nhất)" });
  });
  T(s, [B("Vì sao cần kiểm tra: "), R("mô hình đưa ra con số PD (ví dụ 9%) để định giá khoản vay và trích lập dự phòng. Chia khách trong test set thành 10 nhóm theo PD dự báo, rồi so PD dự báo (cam) với tỷ lệ bad thực tế (xanh).")],
    { x: M, y: 5.2, w: cw, h: 1.6, fontSize: 14 });
  T(s, [B("Kết quả: "), R(`hai thứ gần nhau ở mọi nhóm, và thứ tự đúng: nhóm 10% rủi ro nhất có tỷ lệ bad khoảng ${pct(b2.deciles[GB][0].bad_rate, 0)}, gấp hơn 3 lần trung bình. Đây là Hosmer-Lemeshow của Bài I áp dụng cho mô hình mới.`)],
    { x: M + cw + 0.4, y: 5.2, w: cw, h: 1.6, fontSize: 14 });
}
{
  const s = content("Kiểm tra thêm: chia theo thời gian hay chia ngẫu nhiên?", "CONTENT_B2");
  const sp = b2.split;
  T(s, [R("Chạy lại "), B("toàn bộ quy trình"), R(" với cách chia thứ hai: test set lấy "), B("ngẫu nhiên đều cả 7 tháng"), R(" (cùng số hồ sơ, giữ tỷ lệ từng tháng và tỷ lệ bad), lặp 5 lần.")],
    { x: M, y: 1.45, w: 6.1, h: 1.0, fontSize: 14 });
  table(s, ["AUC trên test set", "Theo thời gian", "Ngẫu nhiên (TB 5 lần)", "Ngẫu nhiên (thấp – cao)"], [LR, GB].map((m) =>
    [m, cell(vn(sp.time[m], 3), { bold: true }), vn(sp.mean[m], 3), `${vn(sp.min[m], 3)} – ${vn(sp.max[m], 3)}`]), { x: M, y: 2.55, w: 6.1, colW: [1.9, 1.2, 1.4, 1.6], fontSize: 13, rowH: 0.45 });
  T(s, para([[R("AUC của cách chia theo thời gian "), B("nằm trong khoảng dao động"), R(" của 5 lần chia ngẫu nhiên: hai cách cho kết quả tương đương.")],
    [R("Lặp 5 lần vì một lần chia ngẫu nhiên có thể cao hoặc thấp hơn một chút do may rủi.", { color: MUTED, fontSize: 12 })]]), { x: M, y: 4.15, w: 6.1, h: 1.6, fontSize: 14 });
  const months = Object.keys(b2.no_fb);
  s.addChart(pres.charts.BAR, [{ name: "Không có dữ liệu Facebook", labels: months.map((m) => "T" + +m.slice(-2)), values: months.map((m) => b2.no_fb[m]) }], {
    ...axis, x: 7.0, y: 1.35, w: 5.7, h: 3.3, chartColors: [ORANGE], barGapWidthPct: 50, showLegend: false, valAxisLabelFormatCode: "0%", valAxisMaxVal: 0.5,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0%", showTitle: true, title: "Tỷ lệ hồ sơ không có dữ liệu Facebook",
  });
  T(s, [B("Vậy vì sao vẫn chọn chia theo thời gian? "), R("Vì nó phát hiện được khách tương lai khác khách cũ. Nếu chia ngẫu nhiên, các hồ sơ không có Facebook bị trộn vào cả training lẫn test, nên không thấy được thay đổi. Chia theo thời gian cho thấy mô hình "), B("vẫn giữ được AUC"), R(" dù dữ liệu Facebook đã đổi.")],
    { x: 7.1, y: 4.8, w: 5.6, h: 2.0, fontSize: 13 });
}
{
  const s = content("Mô hình dựa vào đâu để quyết định?", "CONTENT_B2");
  const cw = (CW - 0.4) / 2;
  const hb = (data, x, color, title, fmt) => {
    const d = [...data].reverse();
    s.addChart(pres.charts.BAR, [{ name: title, labels: d.map((v) => v.var), values: d.map((v) => v.v) }], {
      ...axis, x, y: 1.35, w: cw, h: 3.9, barDir: "bar", chartColors: [color], barGapWidthPct: 35, showLegend: false, catAxisLabelFontSize: 10,
      valAxisLabelFormatCode: fmt, showTitle: true, title,
    });
  };
  hb(b2.lr_coef, M, NAVY, "Logistic: độ lớn hệ số |β|", "0.0");
  hb(b2.gb_imp, M + cw + 0.4, ORANGE, "Gradient Boosting: AUC giảm khi xáo trộn biến", "0.00");
  T(s, [B("Trái: "), R("mọi biến đều đã đổi sang WOE (cùng thang), nên |β| càng lớn thì biến thay đổi PD càng mạnh. "),
    B("Phải: "), R("xáo trộn ngẫu nhiên một biến giữa các khách để nó mất thông tin, rồi đo AUC giảm bao nhiêu.")],
  { x: M, y: 5.45, w: cw, h: 1.4, fontSize: 13, color: MUTED });
  T(s, [R("Hai mô hình đồng ý về các biến quan trọng nhất: "), B("số app vay, tổng số app, hoạt động gọi điện, thâm niên làm việc"), R(". Boosting không dựa vào biến lạ mà khai thác cùng các tín hiệu, chỉ chi tiết hơn.")],
    { x: M + cw + 0.4, y: 5.45, w: cw, h: 1.4, fontSize: 14 });
}
{
  const s = content("Quyết định chọn mô hình", "CONTENT_B2");
  box(s, M, 1.45, 5.9, 5.3, "FBF0DF");
  T(s, [B("Đề xuất: Gradient Boosting làm mô hình chính"), R(", Logistic scorecard làm mô hình đối chứng.")], { x: M + 0.3, y: 1.65, w: 5.3, h: 0.9, fontSize: 16 });
  T(s, bullets([`Tốt hơn rõ rệt trên dữ liệu tương lai: AR ${vn(gbT.gini, 2)} so với ${vn(lrT.gini, 2)}`, "Giữ được AUC trên tháng 6–7, và PD dự báo khớp thực tế",
    "Biến quan trọng giống Logistic, có ý nghĩa nghiệp vụ"]), { x: M + 0.3, y: 2.65, w: 5.3, h: 2.0, fontSize: 15 });
  T(s, `Nếu cần giải thích được từng điểm số (ví dụ theo quy định nội bộ), Logistic scorecard là phương án thay thế, chấp nhận giảm khoảng ${vn(gbT.gini - lrT.gini, 2)} AR.`,
    { x: M + 0.3, y: 4.9, w: 5.3, h: 1.6, fontSize: 13, color: MUTED });
  T(s, "Ví dụ scorecard: điểm cho biến \"số app vay\" (600 điểm ≈ PD 9%, cứ thêm 50 điểm thì rủi ro giảm một nửa)", { x: 6.9, y: 1.45, w: 5.8, h: 0.8, fontSize: 14, bold: true, color: NAVY });
  table(s, ["Số app vay", "Số hồ sơ", "Tỷ lệ bad", "WOE", "Điểm"], b2.scorecard.map((x) => [binLabel(x.bin), vn(x.n, 0), pct(x.bad_rate), vn(x.woe, 2), cell(x.pts, { bold: true })]),
    { x: 6.9, y: 2.4, w: 5.8, colW: [1.4, 1.1, 1.1, 1.0, 1.2], fontSize: 14, rowH: 0.48 });
  T(s, "Bảng điểm đầy đủ: output/scorecard.csv", { x: 6.9, y: 5.0, w: 5.8, h: 0.4, fontSize: 12, color: MUTED });
}
{
  const s = content("Nếu mô hình dự báo kém trên khách mới?", "CONTENT_B2");
  T(s, [R("Phát hiện điều này "), B("trước khi dùng thật"), R(" chính là mục đích của test set theo thời gian.")], { x: M, y: 1.4, w: 6.6, h: 0.5, fontSize: 14 });
  T(s, "Bước 1: kém ở mặt nào?", { x: M, y: 1.95, w: 6.6, h: 0.4, fontSize: 15, bold: true, color: NAVY });
  table(s, ["Kiểu kém", "Dấu hiệu", "Cách xử lý"], [["Xếp hạng kém", "AUC / AR giảm mạnh", "Bỏ biến không ổn định hoặc huấn luyện lại"],
    ["Mức PD lệch", "AUC ổn nhưng Hosmer-Lemeshow không đạt", "Hiệu chỉnh lại mức PD (recalibrate), không cần xây lại"]], { x: M, y: 2.4, w: 6.6, colW: [1.5, 2.4, 2.7], fontSize: 12, rowH: 0.5 });
  T(s, para([[B("Bước 2: tìm nguyên nhân"), R(" bằng cách so phân phối từng biến giữa lúc xây và lúc dùng (ví dụ chỉ số PSI): dữ liệu, tệp khách, chính sách duyệt hay kinh tế thay đổi? Hay dữ liệu mới chưa đủ thời gian để lộ ra bad?")],
    [B("Bước 3: trong lúc chờ sửa"), R(", dùng ngưỡng duyệt chặt hơn, chạy song song mô hình cũ và mới (champion–challenger), theo dõi AUC và tỷ lệ thiếu dữ liệu hằng tháng.")]]),
  { x: M, y: 4.0, w: 6.6, h: 2.8, fontSize: 13, paraSpaceAfter: 8 });
  card(s, 7.6, 1.45, 5.1, 5.3, "Áp dụng cho bài này", bullets([
    [B("Facebook: "), R(`tháng 7 có ${pct(b2.no_fb["2018-07"], 0)} hồ sơ không có dữ liệu Facebook; scorecard dùng 2 biến Facebook, nên cần theo dõi tỷ lệ này.`)],
    [B("Tháng 7 mới nhất "), R(`nên có thể chưa đủ thời gian để lộ ra bad: tỷ lệ bad T7 (${pct(b2.monthly[6].bad_rate)}) thấp hơn T6 (${pct(b2.monthly[5].bad_rate)}).`)],
    [B("Trước khi dùng thật: "), R("huấn luyện lại trên cả 7 tháng để học được thay đổi gần nhất.")]]), { fontSize: 14 });
}
{
  const s = content("Hạn chế và bước tiếp theo", "CONTENT_B2");
  const items = [
    ["Đã tìm ra, chưa sửa", "scorecard chấm PD cho khách không có Facebook cao hơn thực tế (13,5% so với 10,0%), vì nhóm \"Missing\" của fb_days_since_update chỉ có 2 hồ sơ lúc học. Cách sửa: gán WOE = 0 cho nhóm quá nhỏ, hoặc hiệu chỉnh lại PD. Boosting không bị lỗi này."],
    ["Biến từ danh sách app còn thô", "chỉ dựa vào từ khóa; có thể phân loại app chuẩn hơn."],
    ["Chưa tối ưu tham số có hệ thống", "bước tiếp theo là cross-validation theo thời gian."],
    ["Giải thích từng khách hàng", "cần SHAP để cho biết vì sao một hồ sơ bị chấm rủi ro (lý do từ chối)."],
    ["Định nghĩa \"bad\" và ngưỡng duyệt", "chưa biết bad là quá hạn bao nhiêu ngày; ngưỡng duyệt cần chọn cùng nghiệp vụ."],
    ["Chỉ có khách đã được duyệt", "mô hình chưa thấy người bị từ chối (reject inference)."],
    ["Công bằng", "cần kiểm tra mô hình không phân biệt theo giới tính hoặc nhóm nhạy cảm."]];
  box(s, M, 1.4, CW, 1.25, "FBF0DF");
  T(s, [B(items[0][0] + ": "), R(items[0][1])], { x: M + 0.3, y: 1.52, w: CW - 0.6, h: 1.05, fontSize: 14 });
  const cw = (CW - 0.4) / 2;
  items.slice(1).forEach(([h, d], i) => {
    const x = M + (i % 2) * (cw + 0.4), y = 2.95 + Math.floor(i / 2) * 1.3;
    box(s, x, y, cw, 1.1, CARD);
    T(s, [B(h + ": "), R(d)], { x: x + 0.25, y: y + 0.12, w: cw - 0.5, h: 0.9, fontSize: 14 });
  });
}

// =====================================================================
// REFERENCES
// =====================================================================
SECTION = "Tài liệu tham khảo";
pres.addSection({ title: SECTION });
{
  const s = content("Tài liệu tham khảo", "CONTENT");
  const refs = [
    ["Credit scoring: WOE, IV, scorecard", [
      "Siddiqi, N. (2017). Intelligent Credit Scoring (2nd ed.). Wiley.",
      "Thomas, L. C., Crook, J. N., & Edelman, D. B. (2017). Credit Scoring and Its Applications (2nd ed.). SIAM.",
      "Anderson, R. (2007). The Credit Scoring Toolkit. Oxford University Press."]],
    ["Kiểm định mô hình PD", [
      "Sobehart, J., Keenan, S., & Stein, R. (2000). Benchmarking quantitative default risk models: A validation methodology. Moody's.",
      "Basel Committee on Banking Supervision (2005). Studies on the validation of internal rating systems (WP 14). BIS.",
      "Hosmer, D. W., Lemeshow, S., & Sturdivant, R. X. (2013). Applied Logistic Regression (3rd ed.). Wiley.",
      "Hanley, J. A., & McNeil, B. J. (1982). The meaning and use of the area under a ROC curve. Radiology, 143(1)."]],
    ["Thuật toán", [
      "James, G., Witten, D., Hastie, T., & Tibshirani, R. (2021). An Introduction to Statistical Learning (2nd ed.). Springer.",
      "Hastie, T., Tibshirani, R., & Friedman, J. (2009). The Elements of Statistical Learning (2nd ed.). Springer.",
      "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. Annals of Statistics, 29(5).",
      "Ke, G. et al. (2017). LightGBM: A highly efficient gradient boosting decision tree. NeurIPS.",
      "Lessmann, S., Baesens, B., Seow, H.-V., & Thomas, L. C. (2015). Benchmarking classification algorithms for credit scoring. EJOR, 247(1)."]],
    ["Rủi ro khi xây và dùng mô hình", [
      "Kaufman, S. et al. (2012). Leakage in data mining. ACM TKDD, 6(4).",
      "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions (SHAP). NeurIPS.",
      "Frisch, R., & Waugh, F. V. (1933). Partial time regressions as compared with individual trends. Econometrica, 1(4).",
      "Lovell, M. C. (1963). Seasonal adjustment of economic time series and multiple regression analysis. JASA, 58(304)."]]];
  const cw = (CW - 0.4) / 2; let n = 1;
  [[refs[0], refs[1]], [refs[2], refs[3]]].forEach((col, ci) => {
    const runs = [];
    col.forEach(([head, list], gi) => {
      runs.push(R(head, { bold: true, color: NAVY, fontSize: 13, breakLine: true, paraSpaceBefore: gi ? 8 : 0 }));
      list.forEach((t, li) => runs.push(R(`${n++}. ${t}`, { fontSize: 11, breakLine: !(gi === col.length - 1 && li === list.length - 1) })));
    });
    T(s, runs, { x: M + ci * (cw + 0.4), y: 1.4, w: cw, h: 5.4, paraSpaceAfter: 4 });
  });
}

pres.writeFile({ fileName: OUT }).then(async () => { await applyTheme(OUT, THEME); console.log("written", OUT); });
