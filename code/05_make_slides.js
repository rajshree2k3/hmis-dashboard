// 05_make_slides.js - builds report/CEGIS_Trichy_Assignment_Slides.pptx
// Usage: python code/05_slide_data.py && node code/05_make_slides.js   (needs: npm install pptxgenjs jszip)
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const D = JSON.parse(fs.readFileSync(path.join(ROOT, "report", "slide_data.json"), "utf8"));
const FIG = path.join(ROOT, "report", "figures");
const OUT = path.join(ROOT, "report", "CEGIS_Trichy_Assignment_Slides.pptx");
const APPLY_THEME = process.env.APPLY_THEME_JS; // optional: path to pptx skill's apply_theme.js

const THEME = {
  name: "CEGIS MCH",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F24", lt1: "FFFFFF", dk2: "14213D", lt2: "EEF2F6",
    accent1: "2A78D6", // HMIS (admin) blue
    accent2: "EB6834", // NFHS (survey) orange
    accent3: "1A8F5A", // reliable
    accent4: "D64545", // do not rely
    accent5: "C98500", // caution
    accent6: "6B7785", // muted
    hlink: "2A78D6", folHlink: "6250D6",
  },
};
const HEX = THEME.colors;
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Maternal & child health in Tamil Nadu: can we trust HMIS?";
pres.author = "[Candidate name]";
const C = pres.SchemeColor;
const W = 13.333;
const M = 0.6; // side margin
const f = (x, d = 0) => (x === null || x === undefined ? "–" : Number(x).toFixed(d));
const S = D.summary;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "DARK",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 2.2, w: W - 2 * M, h: 1.8, fontSize: 40, bold: true,
        color: C.background1, valign: "bottom", align: "left", fontFace: THEME.headFontFace }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 4.2, w: W - 2 * M, h: 1.4, fontSize: 18,
        color: "CADCFC", valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "DARK_LIST",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.6, w: W - 2 * M, h: 1.0, fontSize: 36, bold: true,
        color: C.background1, valign: "middle", align: "left", fontFace: THEME.headFontFace }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: W - 2 * M, h: 0.95, fontSize: 28, bold: true,
        color: C.text2, valign: "middle", fontFace: THEME.headFontFace }, text: "" } },
    { text: { text: "Sources: HMIS standard reports, MoHFW (FY 2018-19 to 2020-21); NFHS-5 district factsheets (2019-21)",
        options: { x: M, y: 7.05, w: 9, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.05, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

// ------------------------------------------------------------------ helpers
function txt(slide, text, opts) {
  slide.addText(text, { isTextBox: true, fontSize: 14, color: C.text1, valign: "top", margin: 0, ...opts });
}
function card(slide, x, y, w, h, fill, name) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill || C.background2 },
    line: { color: fill || C.background2, width: 0 }, objectName: name });
}
function dot(slide, x, y, color, label, name) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color }, line: { color, width: 0 }, objectName: name });
  slide.addText(label, { isTextBox: true, x, y, w: 0.42, h: 0.42, fontSize: 14, bold: true, color: C.background1,
    align: "center", valign: "middle", margin: 0 });
}
const axisFont = () => ({
  catAxisLabelColor: HEX.accent6, valAxisLabelColor: HEX.accent6, catAxisLabelFontFace: "+mn-lt",
  valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 12, dataLabelColor: HEX.dk1,
  legendFontFace: "+mn-lt", legendFontSize: 12, legendColor: HEX.dk1,
  titleFontFace: "+mn-lt", titleFontSize: 14, titleColor: HEX.dk2,
  valGridLine: { color: "E4E3DF", size: 0.75 }, catGridLine: { style: "none" },
});

// ================================================================== 1. title
pres.addSection({ title: "Opening" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
s.addText("Maternal & child health in Tamil Nadu: can we trust the HMIS numbers?", { placeholder: "title" });
s.addText([
  { text: "Data quality, triangulation with NFHS-5, and what it means for Tiruchirappalli", options: { breakLine: true } },
  { text: "CEGIS analytical assignment · District Data Analyst · [Candidate name] · November 2026", options: { fontSize: 14, color: "9FB3C8" } },
], { placeholder: "body" });
s.addNotes("Purpose: judge how far HMIS can be trusted for district decisions, check it against NFHS-5, and show what that means for Trichy.");

// ================================================================== 2. bottom line
pres.addSection({ title: "Bottom line" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Bottom line" });
s.addText("Bottom line: trust HMIS for state totals, not for ranking districts", { placeholder: "title" });
const cards = [
  [`${f(S.anc4.hmis_state)} vs ${f(S.anc4.nfhs_births_weighted)}%`, "State averages agree",
    `4+ ANC, HMIS vs NFHS-5. C-sections: ${f(S.csection.hmis_state)}% vs ${f(S.csection.nfhs_births_weighted)}%.`, C.accent3],
  [`ρ ≈ ${f(S.anc4.spearman_rho, 2)}`, "District rankings don't",
    "HMIS and NFHS-5 rank districts differently on 4+ ANC and full immunisation. C-sections are the exception.", C.accent4],
  [`${f(S.full_imm.hmis_over_100)} of 31`, "Districts above 100%",
    "Full immunisation: births are counted where they happen, children vaccinated where they live.", C.accent4],
  [`${f(S.anc_1st_trimester.hmis_state)} vs ${f(S.anc_1st_trimester.nfhs_births_weighted)}%`, "1st-trimester ANC",
    `HMIS higher in ${D.first_tri_hmis_higher} of 32 districts. Verify recording before using it for targets.`, C.accent5],
];
const cw = (W - 2 * M - 3 * 0.3) / 4;
cards.forEach(([big, head, body, col], i) => {
  const x = M + i * (cw + 0.3);
  card(s, x, 1.55, cw, 3.65, C.background2, `card-${i + 1}`);
  s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 1.8, w: 0.3, h: 0.3, fill: { color: col }, line: { color: col, width: 0 }, objectName: `card-${i + 1}-status` });
  txt(s, big, { x: x + 0.3, y: 2.25, w: cw - 0.6, h: 0.8, fontSize: 28, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  txt(s, head, { x: x + 0.3, y: 3.2, w: cw - 0.6, h: 0.45, fontSize: 16, bold: true });
  txt(s, body, { x: x + 0.3, y: 3.7, w: cw - 0.6, h: 1.4, fontSize: 14, color: C.accent6 });
});
card(s, M, 5.45, W - 2 * M, 1.35, "E3EEFB", "action-box");
txt(s, [
  { text: "For the Collector's team: ", options: { bold: true, color: C.text2 } },
  { text: "use NFHS-5 to rank districts and HMIS for month-to-month monitoring. Move 4+ ANC and immunisation to resident-based denominators (RCH/PICME registrations by block). " +
      `Ask why Trichy's 4+ ANC slipped three years running (${f(D.trichy_anc4_by_fy["2018-19"])}% → ${f(D.trichy_anc4_by_fy["2020-21"])}%).` },
], { x: M + 0.3, y: 5.6, w: W - 2 * M - 0.6, h: 1.1, fontSize: 15, valign: "middle" });
s.addNotes("Four headline messages. Green = reliable, red = do not rely, amber = verify first.");

// ================================================================== 3. data & approach
pres.addSection({ title: "Data and quality" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data and quality" });
s.addText("Two sources, two district maps: reconciled by adding counts back to the parent district", { placeholder: "title" });
const srcW = 5.6;
[[1.5, "HMIS: government records", C.accent1,
  "Monthly facility reports, district-wise, FY 2018-19 to 2020-21 (2020-21 provisional). Later years need a portal login, so 2020-21 is the latest public year."],
 [3.75, "NFHS-5: household survey", C.accent2,
  "District estimates, TN fieldwork early 2020, covering births in the previous 5 years. Small samples are flagged: 25–49 cases (bracketed) or suppressed (<25)."],
].forEach(([y, head, col, body], i) => {
  card(s, M, y, srcW, 2.0, C.background2, `source-${i + 1}`);
  s.addShape(pres.shapes.OVAL, { x: M + 0.3, y: y + 0.3, w: 0.3, h: 0.3, fill: { color: col }, line: { color: col, width: 0 }, objectName: `source-${i + 1}-key` });
  txt(s, head, { x: M + 0.75, y: y + 0.25, w: srcW - 1, h: 0.4, fontSize: 17, bold: true });
  txt(s, body, { x: M + 0.3, y: y + 0.8, w: srcW - 0.6, h: 1.1, fontSize: 14, color: C.accent6 });
});
txt(s, "6 new districts → added back to their 2019 parent", { x: 6.8, y: 1.5, w: 6, h: 0.4, fontSize: 17, bold: true });
const splits = [["Chengalpattu", "Kancheepuram"], ["Kallakurichi", "Viluppuram"], ["Ranipet", "Vellore"],
  ["Tirupathur", "Vellore"], ["Tenkasi", "Tirunelveli"], ["Mayiladuthurai*", "Nagapattinam"]];
splits.forEach(([a, b], i) => {
  const y = 2.05 + i * 0.5;
  card(s, 6.8, y, 2.5, 0.4, "E3EEFB", `new-${i + 1}`);
  txt(s, a, { x: 6.9, y, w: 2.3, h: 0.4, fontSize: 14, valign: "middle" });
  s.addShape(pres.shapes.RIGHT_ARROW, { x: 9.45, y: y + 0.1, w: 0.55, h: 0.2, fill: { color: C.accent6 }, line: { color: C.accent6, width: 0 }, objectName: `arrow-${i + 1}` });
  card(s, 10.15, y, 2.55, 0.4, "FDE9E0", `parent-${i + 1}`);
  txt(s, b, { x: 10.25, y, w: 2.35, h: 0.4, fontSize: 14, valign: "middle" });
});
txt(s, [
  { text: "Why this way: ", options: { bold: true } },
  { text: "HMIS events are counts, so adding them is exact. Splitting a survey percentage would need invented weights. Spelling variants (Tuticorin / Toothukudi / Thoothukkudi) are mapped in a crosswalk file." },
], { x: 6.8, y: 5.15, w: 5.9, h: 1.2, fontSize: 14 });
txt(s, "* Mayiladuthurai reports zeros all year in 2020-21; its activity is still booked under Nagapattinam.",
  { x: 6.8, y: 6.4, w: 5.9, h: 0.45, fontSize: 11, color: C.accent6, italic: true });

// ================================================================== 4. data quality
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Data and quality" });
s.addText("HMIS is internally consistent, but its ratios break where denominators don't match", { placeholder: "title" });
const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.dk2, fill: { color: HEX.lt2 } } });
const rows = [
  [hdr(""), hdr("Check"), hdr("What I found"), hdr("What I did")],
  ["OK", "Monthly files vs annual file", "0 mismatches in 4,900 district × item rows; public + private = total", "Used annual files"],
  ["OK", "Births vs deliveries", "Live births ÷ deliveries = 0.99–1.01 in every district", "Births are a sound count (of where births occur)"],
  ["!", "Private-sector columns", "ANC: no private entries at all. Private immunisation entries vanish in most districts from 2019-20", "Read ANC as public-system data"],
  ["!", "Unusual months (robust z > 3.5)", "418 district-months; Trichy ANC registrations spike in Dec 2019 (4,548 vs ~3,200)", "Kept and flagged; read trends, not single months"],
  ["X", "Values above 100%", `Full immunisation >100% in 18–20 districts a year (max 157%); 4+ ANC up to 110%`, "Built a resident-birth denominator"],
  ["X", "1st-trimester registration", `Above NFHS-5 in ${D.first_tri_hmis_higher} of 32 districts, by ~16 points`, "Not used; flagged for field check"],
];
const statusCol = { OK: HEX.accent3, "!": HEX.accent5, X: HEX.accent4 };
const tRows = rows.map((r, i) => i === 0 ? r : r.map((c, j) => j === 0
  ? { text: c === "X" ? "✕" : c === "!" ? "!" : "✓", options: { bold: true, color: "FFFFFF", fill: { color: statusCol[c] }, align: "center" } }
  : { text: c }));
s.addTable(tRows, { x: M, y: 1.5, w: W - 2 * M, colW: [0.5, 2.9, 5.0, 3.73], fontSize: 13, fontFace: THEME.bodyFontFace,
  color: HEX.dk1, valign: "middle", border: { type: "solid", pt: 0.75, color: "D5DCE4" }, rowH: 0.62, margin: 0.08 });
txt(s, [{ text: "Would rely on: ", options: { bold: true, color: C.accent3 } },
  { text: "counts at district and state level, state-level ratios, seasonal and monthly patterns." }],
  { x: M, y: 6.1, w: 6.0, h: 0.8, fontSize: 14 });
txt(s, [{ text: "Would not rely on: ", options: { bold: true, color: C.accent4 } },
  { text: "district rankings on 4+ ANC or immunisation, 1st-trimester registration, 2020-21 ratios without the COVID caveat." }],
  { x: 6.85, y: 6.1, w: 5.9, h: 0.8, fontSize: 14 });

// ================================================================== 5. triangulation
pres.addSection({ title: "Triangulation" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Triangulation" });
s.addText("State averages agree with the survey; district rankings mostly don't", { placeholder: "title" });
const inds = [["inst_births", "Institutional births"], ["csection", "C-section"], ["anc4", "4+ ANC"],
  ["inst_births_private", "Private share"], ["anc_1st_trimester", "1st-trimester ANC"], ["full_imm", "Full immunisation"]];
s.addChart(pres.charts.BAR, [
  { name: "HMIS 2018-20", labels: inds.map((x) => x[1]), values: inds.map((x) => S[x[0]].hmis_state) },
  { name: "NFHS-5", labels: inds.map((x) => x[1]), values: inds.map((x) => S[x[0]].nfhs_births_weighted) },
], { x: M, y: 1.45, w: 6.3, h: 5.3, barDir: "bar", barGrouping: "clustered", chartColors: [HEX.accent1, HEX.accent2],
  showTitle: true, title: "State level (%)", showLegend: true, legendPos: "b", showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "0", valAxisMinVal: 0, valAxisMaxVal: 115, valAxisHidden: true, catAxisOrientation: "maxMin",
  barGapWidthPct: 60, ...axisFont() });
const rhoInd = [...inds.map((x) => x), ["full_imm_residence", "Full imm. (resident denom.)"]];
s.addChart(pres.charts.BAR, [
  { name: "Rank agreement", labels: rhoInd.map((x) => x[1]), values: rhoInd.map((x) => S[x[0]].spearman_rho) },
], { x: 7.1, y: 1.45, w: 5.6, h: 4.3, barDir: "bar", chartColors: [HEX.dk2], showTitle: true,
  title: "District rank agreement (Spearman ρ, 32 districts)", showLegend: false, showValue: true, dataLabelFormatCode: "0.00",
  dataLabelPosition: "outEnd", valAxisMinVal: -0.4, valAxisMaxVal: 1, valAxisHidden: true, catAxisOrientation: "maxMin", catAxisLabelPos: "low",
  barGapWidthPct: 50, ...axisFont() });
txt(s, "Only C-sections and private share rank districts alike (ρ > 0.6). For 4+ ANC and immunisation, knowing a district's HMIS rank tells you nothing about its survey rank.",
  { x: 7.1, y: 5.85, w: 5.6, h: 0.95, fontSize: 14, color: C.accent6 });

// ================================================================== 6. denominator problem
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Triangulation" });
s.addText("Fix the denominator and full immunisation lines up with the survey", { placeholder: "title" });
const imgH = 4.75, imgW = imgH * (6.6 / 6.2);
s.addImage({ path: path.join(FIG, "fig3a_fic_occurrence.png"), x: M - 0.1, y: 1.4, w: imgW, h: imgH, altText: "Dot plot: HMIS full immunisation divided by births in district vs NFHS-5; many districts above 100%", objectName: "fig-occurrence" });
s.addImage({ path: path.join(FIG, "fig3b_fic_residence.png"), x: M - 0.1 + imgW + 0.15, y: 1.4, w: imgW, h: imgH, altText: "Dot plot: HMIS full immunisation with resident-birth denominator vs NFHS-5; values cluster near 90-105%", objectName: "fig-residence" });
const cx = M + 2 * imgW + 0.15, cW = W - M - cx;
card(s, cx, 1.45, cW, 4.95, C.background2, "trichy-callout");
txt(s, "Trichy, a referral hub", { x: cx + 0.2, y: 1.6, w: cW - 0.4, h: 0.4, fontSize: 15, bold: true });
[[f(D.trichy.full_imm.hmis) + "%", "HMIS ÷ births in Trichy", C.accent1],
 [f(D.trichy.full_imm_residence.hmis) + "%", "HMIS ÷ resident births", C.accent1],
 [f(D.trichy.full_imm.nfhs) + "%", "NFHS-5 survey", C.accent2]].forEach(([v, l, col], i) => {
  txt(s, v, { x: cx + 0.2, y: 2.1 + i * 1.05, w: cW - 0.4, h: 0.6, fontSize: 26, bold: true, color: col, fontFace: THEME.headFontFace });
  txt(s, l, { x: cx + 0.2, y: 2.68 + i * 1.05, w: cW - 0.4, h: 0.35, fontSize: 12, color: C.accent6 });
});
txt(s, `Spread across districts: SD ${f(D.fic_sd.occurrence)} → ${f(D.fic_sd.residence)} points.`, { x: cx + 0.2, y: 5.3, w: cW - 0.4, h: 0.9, fontSize: 13, bold: true });
txt(s, "Left: as HMIS reports it. Right: ÷ previous year's ANC registrations × state births-per-registration. Hollow circles = NFHS-5 based on only 25–49 children.",
  { x: M, y: 6.3, w: W - 2 * M, h: 0.5, fontSize: 11, color: C.accent6, italic: true });

// ================================================================== 7. why they disagree
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Triangulation" });
s.addText("Four reasons the sources disagree, and what the comparison can't tell us", { placeholder: "title" });
const reasons = [
  ["1", "Where vs who", "HMIS counts the facility's district; the survey asks the mother's. Thiruvallur: 42,500 ANC registrations, 21,500 births, so immunisation shows 157%."],
  ["2", "Denominators", "HMIS divides by events it sees that year, not the population. When registrations fall (2020), ratios rise mechanically."],
  ["3", "Recording practice", "First-trimester registration is ~16 points higher almost everywhere. A uniform gap points to a recording convention, not random error."],
  ["4", "Survey noise & timing", "Many district immunisation estimates rest on 25–49 children (±12 points). NFHS-5 covers 2015–20 births, HMIS 2018–20."],
];
const rw = (W - 2 * M - 0.3) / 2;
reasons.forEach(([n, head, body], i) => {
  const x = M + (i % 2) * (rw + 0.3), y = 1.5 + Math.floor(i / 2) * 1.85;
  card(s, x, y, rw, 1.65, C.background2, `reason-${n}`);
  dot(s, x + 0.25, y + 0.25, C.text2, n, `reason-${n}-num`);
  txt(s, head, { x: x + 0.85, y: y + 0.25, w: rw - 1.1, h: 0.42, fontSize: 16, bold: true, valign: "middle" });
  txt(s, body, { x: x + 0.85, y: y + 0.72, w: rw - 1.1, h: 0.9, fontSize: 13, color: C.accent6 });
});
card(s, M, 5.35, rw, 1.45, "E2F3EA", "can-box");
txt(s, [{ text: "Can establish", options: { bold: true, color: C.accent3, breakLine: true } },
  { text: "Where HMIS is biased in a consistent direction, and which indicators are safe for ranking." }],
  { x: M + 0.25, y: 5.5, w: rw - 0.5, h: 1.2, fontSize: 14 });
card(s, M + rw + 0.3, 5.35, rw, 1.45, "FBE5E5", "cannot-box");
txt(s, [{ text: "Cannot establish", options: { bold: true, color: C.accent4, breakLine: true } },
  { text: "Which source is 'true' for any one district: survey error is as large as most gaps." }],
  { x: M + rw + 0.55, y: 5.5, w: rw - 0.5, h: 1.2, fontSize: 14 });

// ================================================================== 8. COVID / time
pres.addSection({ title: "Outcomes" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Outcomes" });
s.addText("COVID-19 shows up as fewer pregnancies, then fewer births nine months later", { placeholder: "title" });
const fyCols = { "2018-19": "9EC5F4", "2019-20": "3987E5", "2020-21": "0D366B" };
[["n_anc_registered", "New ANC registrations, Tamil Nadu (thousands)", M, 70],
 ["n_inst_deliveries", "Institutional deliveries, Tamil Nadu (thousands)", 6.85, 45]].forEach(([v, ttl, x, vmin]) => {
  const fys = Object.keys(D.monthly[v]);
  s.addChart(pres.charts.LINE, fys.map((fy) => ({ name: fy, labels: D.months, values: D.monthly[v][fy] })), {
    x, y: 1.45, w: 5.9, h: 4.3, chartColors: fys.map((fy) => fyCols[fy]), lineSize: 2.5, lineDataSymbol: "circle",
    lineDataSymbolSize: 5, showTitle: true, title: ttl, showLegend: true, legendPos: "b", valAxisMinVal: vmin,
    ...axisFont() });
});
txt(s, [
  { text: "Registrations fell Jul–Nov 2020 ", options: { bold: true } },
  { text: "(75–81k a month vs 81–90k a year earlier); " },
  { text: "deliveries fell Jan–Mar 2021. ", options: { bold: true } },
  { text: `That fits fewer conceptions during lockdown, not a reporting breakdown. Side effect: 4+ ANC "improved" in 2020-21 (district median ${f(D.median_anc4_by_fy["2019-20"])}% → ${f(D.median_anc4_by_fy["2020-21"])}%) because its denominator shrank.` },
], { x: M, y: 5.95, w: W - 2 * M, h: 0.95, fontSize: 14 });

// ================================================================== 9. correlates
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Outcomes" });
s.addText("What goes with better coverage? One robust signal, and a lot of noise", { placeholder: "title" });
const anc = D.drivers.filter((d) => d.outcome === "anc4"), fic = D.drivers.filter((d) => d.outcome === "full_imm");
s.addChart(pres.charts.BAR, [
  { name: "4+ ANC", labels: anc.map((d) => d.covariate_label), values: anc.map((d) => d.spearman_rho) },
  { name: "Full immunisation", labels: fic.map((d) => d.covariate_label), values: fic.map((d) => d.spearman_rho) },
], { x: M, y: 1.45, w: 7.4, h: 5.35, barDir: "bar", barGrouping: "clustered", chartColors: [HEX.dk2, HEX.accent6],
  showTitle: true, title: "Spearman ρ with NFHS-5 district covariates (n = 32)", showLegend: true, legendPos: "b",
  showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "outEnd", valAxisMinVal: -0.5, valAxisMaxVal: 0.8,
  valAxisHidden: true, catAxisOrientation: "maxMin", catAxisLabelPos: "low", barGapWidthPct: 40, ...axisFont() });
const ins = anc.find((d) => d.covariate_label.includes("insurance"));
const sch = fic.find((d) => d.covariate_label.includes("schooling"));
const rx = 8.3, rW = W - M - rx;
card(s, rx, 1.45, rW, 1.6, C.background2, "finding-insurance");
txt(s, [{ text: `ρ = ${f(ins.spearman_rho, 2)}`, options: { bold: true, fontSize: 26, color: C.text2, breakLine: true, fontFace: THEME.headFontFace } },
  { text: `4+ ANC vs health-insurance coverage (CI ${f(ins.ci_low, 2)}–${f(ins.ci_high, 2)}). The only result that survives correction for 7 tests.` }],
  { x: rx + 0.25, y: 1.6, w: rW - 0.5, h: 1.4, fontSize: 13 });
card(s, rx, 3.25, rW, 1.0, C.background2, "finding-schooling");
txt(s, `Full immunisation vs women's schooling: ρ = ${f(sch.spearman_rho, 2)} (CI ${f(sch.ci_low, 2)}–${f(sch.ci_high, 2)}); does not survive correction.`,
  { x: rx + 0.25, y: 3.4, w: rW - 0.5, h: 0.8, fontSize: 13 });
txt(s, [{ text: "Limits: ", options: { bold: true, color: C.accent4 } },
  { text: "32 districts, ecological data, outcomes measured with ±5–12 point error. Insurance most likely proxies the public system's reach, not a lever to pull. These results suggest where to look, not what causes coverage." }],
  { x: rx, y: 4.5, w: rW, h: 1.8, fontSize: 13 });

// ================================================================== 10. Trichy
pres.addSection({ title: "Trichy and next steps" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Trichy and next steps" });
s.addText("Tiruchirappalli: a referral hub whose 4+ ANC is quietly slipping", { placeholder: "title" });
const fys = ["2018-19", "2019-20", "2020-21"];
s.addChart(pres.charts.LINE, [
  { name: "Trichy", labels: fys, values: fys.map((y) => D.trichy_anc4_by_fy[y]) },
  { name: "District median", labels: fys, values: fys.map((y) => D.median_anc4_by_fy[y]) },
], { x: M, y: 1.45, w: 5.8, h: 4.25, chartColors: [HEX.accent2, HEX.accent6], lineSize: 3, lineDataSymbol: "circle",
  lineDataSymbolSize: 8, showTitle: true, title: "4+ ANC, HMIS (%)", showLegend: true, legendPos: "b",
  valAxisMinVal: 80, valAxisMaxVal: 95, ...axisFont() });
txt(s, `Trichy ${fys.map((y) => f(D.trichy_anc4_by_fy[y], 1)).join(" → ")}  ·  district median ${fys.map((y) => f(D.median_anc4_by_fy[y], 1)).join(" → ")}`,
  { x: M, y: 5.75, w: 5.8, h: 0.35, fontSize: 12, color: C.accent6, align: "center" });
const tiles = [
  [`${f(D.trichy.inst_births_private.hmis)}% vs ${f(D.trichy.inst_births_private.nfhs)}%`, "Private share of deliveries, HMIS vs NFHS-5: births flow in from neighbouring districts"],
  [`${f(D.trichy.full_imm.hmis)}% → ${f(D.trichy.full_imm_residence.hmis)}%`, `Full immunisation once the denominator counts resident births (NFHS-5: ${f(D.trichy.full_imm.nfhs)}%)`],
  ["Dec 2019", "ANC registrations spike to 4,548 (normal ~3,200), so 4+ ANC dips to 64% that month. Probably a back-entry; check with the RCH team"],
];
tiles.forEach(([big, body], i) => {
  const y = 1.45 + i * 1.6;
  card(s, 6.85, y, W - M - 6.85, 1.45, C.background2, `trichy-tile-${i + 1}`);
  txt(s, big, { x: 7.1, y: y + 0.15, w: 5.4, h: 0.55, fontSize: 24, bold: true, color: C.text2, fontFace: THEME.headFontFace });
  txt(s, body, { x: 7.1, y: y + 0.72, w: 5.4, h: 0.68, fontSize: 13, color: C.accent6 });
});
txt(s, "Trichy's HMIS figures look low partly because it serves its neighbours. The 4+ ANC decline is within Trichy's own registrations, so it is worth a block-level look.",
  { x: M, y: 6.2, w: W - 2 * M, h: 0.7, fontSize: 14 });

// ================================================================== 11. next steps (dark)
s = pres.addSlide({ masterName: "DARK_LIST", sectionTitle: "Trichy and next steps" });
s.addText("What I would do next", { placeholder: "title" });
const steps = [
  ["1", "Resident denominators", "Rebuild 4+ ANC and immunisation from RCH/PICME registrations, by block."],
  ["2", "Field-check one indicator", "Verify how first-trimester registration is recorded at 2–3 PHCs."],
  ["3", "Use each source for its job", "NFHS-5 to rank districts; HMIS for monthly monitoring with the trust labels in the dashboard."],
  ["4", "Refresh", "Add HMIS 2021-22 onward (login access) and NFHS-6 when released; the pipeline takes new files unchanged."],
];
steps.forEach(([n, head, body], i) => {
  const y = 1.9 + i * 1.05;
  s.addShape(pres.shapes.OVAL, { x: M, y, w: 0.55, h: 0.55, fill: { color: C.accent2 }, line: { color: C.accent2, width: 0 }, objectName: `step-${n}` });
  txt(s, n, { x: M, y, w: 0.55, h: 0.55, fontSize: 18, bold: true, color: C.background1, align: "center", valign: "middle" });
  txt(s, [{ text: head + "  ", options: { bold: true, color: C.background1 } }, { text: body, options: { color: "CADCFC" } }],
    { x: M + 0.8, y, w: W - 2 * M - 0.8, h: 0.55, fontSize: 16, valign: "middle" });
});
txt(s, "Live dashboard: [DASHBOARD LINK]   ·   Full report, code & README in the submission folder",
  { x: M, y: 6.4, w: W - 2 * M, h: 0.5, fontSize: 14, color: "9FB3C8" });

// ------------------------------------------------------------------ write
(async () => {
  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("saved", OUT);
})();
