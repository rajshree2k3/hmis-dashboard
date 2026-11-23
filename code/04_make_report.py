"""
04_make_report.py - builds report/CEGIS_Trichy_Assignment_Report.docx from the processed tables.
Key numbers are pulled from the CSVs so the text stays in sync with the analysis.
"""
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
FIG = ROOT / "report" / "figures"
OUT = ROOT / "report" / "CEGIS_Trichy_Assignment_Report.docx"

summ = pd.read_csv(P / "triangulation_summary.csv").set_index("indicator")
tri = pd.read_csv(P / "triangulation_district.csv")
sens = pd.read_csv(P / "fic_denominator_sensitivity.csv")
drv = pd.read_csv(P / "drivers_correlations.csv")
hm = pd.read_csv(P / "hmis_indicators_fy.csv")
nf = pd.read_csv(P / "nfhs5_tn.csv").pivot(index="district_nfhs32", columns="indicator", values="value")
f = lambda x, d=0: f"{x:.{d}f}"

S = lambda i, c: summ.loc[i, c]
trichy = tri[tri.district == "Tiruchirappalli"].set_index("indicator")
sd_occ = sens[(sens.frame_district != "Tamil Nadu (state)") & (sens.fy == "2019-20")]["full_imm_occurrence"].std()
sd_res = sens[(sens.frame_district != "Tamil Nadu (state)") & (sens.fy == "2019-20")]["full_imm_residence"].std()
h38 = hm[(hm.frame == 38) & (hm.frame_district != "Tamil Nadu (state)")]
anc_by_fy = h38.groupby("fy")["anc4"].median()
tr_h = hm[(hm.frame == 38) & (hm.frame_district == "Tiruchirappalli")].set_index("fy")
ins = drv[(drv.outcome == "anc4") & (drv.covariate == "health_insurance")].iloc[0]
n_tri_pos = int((tri[tri.indicator == "anc_1st_trimester"].gap > 0).sum())
sch = drv[(drv.outcome == "full_imm") & (drv.covariate == "fem_school10")].iloc[0]

doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(1.9)
sec.top_margin = sec.bottom_margin = Cm(1.6)
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10)
st.paragraph_format.space_after = Pt(4)
for lvl, size in [(1, 13), (2, 11)]:
    hs = doc.styles[f"Heading {lvl}"]
    hs.font.size = Pt(size)
    hs.font.color.rgb = RGBColor(0x1C, 0x5C, 0xAB)
    hs.paragraph_format.space_before = Pt(8)
    hs.paragraph_format.space_after = Pt(3)


def para(text, bold_lead=None, size=None, italic=False, style=None):
    p = doc.add_paragraph(style=style)
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
    r = p.add_run(text)
    r.italic = italic
    if size:
        for r in p.runs:
            r.font.size = Pt(size)
    return p


def bullet(text, bold_lead=None):
    if bold_lead and not bold_lead.rstrip().endswith((".", ":")):
        bold_lead = bold_lead + ":"
    return para(text, bold_lead, style="List Bullet")


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear")
    s.set(qn("w:fill"), hex_)
    tcPr.append(s)


def table(rows, widths, header=True, size=8.5):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Cm(widths[j])
            c.text = ""
            r = c.paragraphs[0].add_run(str(val))
            r.font.size = Pt(size)
            if header and i == 0:
                r.bold = True
                shade(c, "DCE8F7")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(path, width_cm, caption):
    doc.add_picture(str(path), width=Cm(width_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(caption, size=8, italic=True)


# ---------------------------------------------------------------- title
t = doc.add_paragraph()
r = t.add_run("Maternal & child health in Tamil Nadu: can we trust the HMIS numbers?")
r.bold, r.font.size = True, Pt(16)
para("CEGIS analytical assignment · District Data Analyst, Tiruchirappalli · Rajshree · November 2026",
     size=9, italic=True)

# ---------------------------------------------------------------- bottom line
doc.add_heading("Bottom line", 1)
bullet(f" HMIS gives believable state averages for deliveries, C-sections and 4+ ANC (HMIS {f(S('anc4','hmis_state'))}% vs "
       f"NFHS-5 ≈{f(S('anc4','nfhs_births_weighted'))}% for 4+ ANC; {f(S('csection','hmis_state'))}% vs "
       f"{f(S('csection','nfhs_births_weighted'))}% for C-sections).", "State level is fine.")
bullet(f" For 4+ ANC and full immunisation, HMIS and NFHS-5 district rankings are unrelated (Spearman ρ = "
       f"{f(S('anc4','spearman_rho'),2)} and {f(S('full_imm','spearman_rho'),2)}). C-sections are the exception "
       f"(ρ = {f(S('csection','spearman_rho'),2)}). HMIS should not be used on its own to name 'lagging' districts on ANC or immunisation.",
       "District rankings are not.")
bullet(f" Full immunisation exceeds 100% in {int(S('full_imm','hmis_over_100'))} of 31 comparable districts because births "
       "are counted where they happen and children are vaccinated where they live. Replacing the denominator with a "
       f"resident-birth proxy shrinks the spread across districts from SD {f(sd_occ)} to SD {f(sd_res)} points. "
       f"For Trichy, a referral hub, it moves HMIS from {f(trichy.loc['full_imm','hmis'])}% to "
       f"{f(trichy.loc['full_imm_residence','hmis'])}%, against NFHS-5's {f(trichy.loc['full_imm','nfhs'])}%.",
       "Biggest single problem: the denominator.")
bullet(f" HMIS reports {f(S('anc_1st_trimester','hmis_state'))}% of pregnancies registered in the first trimester; "
       f"NFHS-5 finds ≈{f(S('anc_1st_trimester','nfhs_births_weighted'))}% had a first-trimester check-up. HMIS is higher in {n_tri_pos} of 32 districts. "
       "I would not use this HMIS indicator for targets until the recording practice is verified.",
       "One indicator looks systematically inflated.")
bullet(" ANC registrations fell in Jul–Nov 2020 and deliveries fell ~9 months later. The data is consistent with fewer "
       f"conceptions during lockdown. The apparent 2020-21 rise in 4+ ANC (district median {f(anc_by_fy['2019-20'])}% → "
       f"{f(anc_by_fy['2020-21'])}%) is most likely a smaller denominator, not better care.", "COVID-19 is visible in the data.")
bullet(" Track 4+ ANC and immunisation on resident-based denominators, using RCH/PICME registrations by block. "
       "Use NFHS-5 for district ranking and HMIS for month-to-month monitoring. Ask why Trichy's 4+ ANC has slipped three years running "
       f"({f(tr_h.loc['2018-19','anc4'])}% → {f(tr_h.loc['2020-21','anc4'])}%).", "For the Collector's team:")

# ---------------------------------------------------------------- data & approach
doc.add_heading("1. Data and approach", 1)
para("HMIS: 'Data Itemwise Monthly – All States Across Districts' standard reports for Tamil Nadu, FY 2018-19, 2019-20 and "
     "2020-21 (the last marked provisional), monthly and annual, by total/public/private/urban/rural. The portal offers "
     "later years only to logged-in users, so 2020-21 is the latest year publicly downloadable; the pipeline accepts newer "
     "files unchanged. NFHS-5: the 707-district factsheet file (TN fieldwork early 2020). In that file, figures shown in "
     "brackets in the factsheets (25–49 unweighted cases) are stored as negative numbers. I verified this against the Phase-1 "
     "file, which carries an explicit note column, and flagged them; one value (Tiruppur, full immunisation) is suppressed.", "Sources. ")
para("Six districts were carved out in 2019-20 (Chengalpattu, Kallakurichi, Ranipet, Tirupathur, Tenkasi; "
     "Mayiladuthurai in Dec 2020). NFHS-5 reports on the old 32. HMIS events are counts, so I added each new "
     "district back to its parent. That is exact for counts, whereas splitting survey percentages would need invented "
     "weights. Spelling variants (e.g. Toothukudi/Tuticorin/Thoothukkudi) are mapped in a documented crosswalk. "
     "All comparisons with NFHS-5 use the 32-district frame. The dashboard can show either frame.", "Reconciling the district frames. ")
para("4+ ANC, first-trimester registration, institutional births, C-section rate, private share of deliveries, and full "
     "immunisation. These are defined as close to the NFHS-5 definitions as HMIS allows (definitions in the dashboard's 'About' tab).",
     "Indicators (in both sources). ")

# ---------------------------------------------------------------- DQ
doc.add_heading("2. Data quality of HMIS", 1)
table([
    ["Check (how detected)", "Finding", "What I did"],
    ["Monthly files vs annual file (re-summed 12 months)", "0 mismatches in 4,900 district × item × sector rows", "Internally consistent; used annual files"],
    ["Public+private = total; urban+rural = total", "No mismatches", "–"],
    ["Missing/zero months per district × item", "No gaps for key items. Mayiladuthurai reports all zeros in 2020-21; its data sits under Nagapattinam. Zero home deliveries are genuine in TN.", "Merged into parent; documented"],
    ["Private-sector columns", "ANC items have no private entries at all. Private full-immunisation entries disappear in most districts from 2019-20 (3% → 81% of districts blank).", "ANC treated as public-system registrations; immunisation trend read with care"],
    ["Ratios > 100% (bounds check)", f"Full immunisation >100% in 18–20 districts each year (max 157%, Thiruvallur). 4+ ANC up to 110% (Karur, 2020-21).", "Diagnosed as denominator mismatch; built a resident-birth denominator"],
    ["Births vs deliveries", "Live births ÷ reported deliveries = 0.99–1.01 everywhere", "Births are a sound count, but of where births occur"],
    ["Monthly outliers (robust z > 3.5 within district-year)", "418 district-months, mostly immunisation-session counts. Trichy: ANC registrations spike in Dec 2019 (4,548 vs ~3,200 normal), probably back-entry.", "Kept; flagged in dashboard; read trends, not single months"],
    ["Definitions across years", "Minor wording changes (TT→Td, MR→MR/MCV, 'midwife' added to SBA)", "Treated as continuous"],
], [5.0, 7.6, 5.0])
para("Total counts of deliveries, births, C-sections and ANC registrations at district and state level. "
     "State-level coverage ratios. Month-to-month and seasonal patterns.", "Would rely on: ")
para("Any HMIS coverage ratio used to rank districts (4+ ANC, full immunisation). First-trimester registration. "
     "Private-sector splits for ANC and immunisation. 2020-21 ratios without noting the COVID denominator effect. "
     "Mayiladuthurai/Nagapattinam separately.", "Would not rely on: ")

# ---------------------------------------------------------------- triangulation
doc.add_heading("3. Triangulation: HMIS vs NFHS-5", 1)
para("HMIS Apr 2018–Mar 2020 is pooled; NFHS-5 refers to births in the five years before early-2020 fieldwork, so this "
     "is the closest overlap available. The NFHS-5 state figure is approximated as a births-weighted average of districts. "
     "NFHS-5 95% intervals are indicative: n is estimated as 25% of interviewed women (25–49 where bracketed), with design effect 1.5.", italic=True, size=8.5)
names = {"inst_births": "Institutional births", "csection": "C-section", "anc4": "4+ ANC",
         "inst_births_private": "Private share of births", "anc_1st_trimester": "1st-trimester ANC",
         "full_imm": "Full immunisation", "full_imm_residence": "Full imm. (resident denominator)"}
rows = [["Indicator", "HMIS state", "NFHS-5 ≈state", "Mean |gap| (pts)", "Rank agreement ρ", "Districts outside NFHS CI"]]
for i in names:
    rows.append([names[i], f(S(i, "hmis_state")), f(S(i, "nfhs_births_weighted")), f(S(i, "mean_abs_gap"), 1),
                 f(S(i, "spearman_rho"), 2), f"{100 * S(i, 'share_outside_ci'):.0f}%"])
table(rows, [4.6, 2.0, 2.3, 2.6, 2.6, 3.4])
para("", "Characterising the gaps and plausible explanations:")
bullet(" (full immunisation, private share). HMIS records the facility's district, the survey the mother's. Trichy, "
       "Chennai, Vellore and Coimbatore attract deliveries; Thiruvallur has 42,500 ANC registrations but only 21,500 births "
       "(mothers deliver in Chennai), so its 'full immunisation' is 157%.", "Place of event vs place of residence")
bullet(" HMIS divides by events it sees in the same year, not by the population. When registrations drop (2020), "
       "ratios rise mechanically.", "Denominators")
bullet(" The ~16-point excess is uniform across districts, which points to a recording convention rather than random error. "
       "It may come from how the 12-week cut-off is applied at registration, versus a check-up in NFHS. This needs field verification.",
       "Definitions/recording (1st trimester)")
bullet(" Many NFHS-5 immunisation estimates rest on 25–49 children (±12 pts). Gaps of under ~10 points at district level are "
       "within noise. NFHS-5 also covers 2015–2020 births, while HMIS covers 2018–20.", "Survey sampling and reference period")
doc.add_picture(str(FIG / "fig3a_fic_occurrence.png"), width=Cm(8.4))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
figure(FIG / "fig3b_fic_residence.png", 8.4,
       "Figure 1. Full immunisation by district. Top: HMIS ÷ births recorded in the district. Bottom: HMIS ÷ resident-birth proxy "
       "(previous year's ANC registrations × state births-per-registration). Hollow circles = NFHS-5 based on 25–49 children.")
para("The comparison can show where HMIS is systematically biased and which indicators can be trusted for ranking. "
     "It cannot establish which source is 'true' for one district: survey noise is as large as most gaps. "
     "Agreement at state level also does not validate district numbers. Even the resident-denominator version stays "
     f"~{f(S('full_imm_residence','mean_gap'))} points above NFHS-5 on average and does not recover the ranking "
     f"(ρ = {f(S('full_imm_residence','spearman_rho'),2)}).", "What it can and cannot establish. ")

# ---------------------------------------------------------------- outcomes & drivers
doc.add_heading("4. Outcomes and their correlates", 1)
para(f"Across the 32 districts, NFHS-5 4+ ANC averages {f(nf['anc4'].mean(),1)}% "
     f"(SD {f(nf['anc4'].std(),1)}; range {f(nf['anc4'].min())}% Kancheepuram to {f(nf['anc4'].max())}% Theni). "
     f"Full immunisation averages {f(nf['full_imm'].mean(),1)}% (SD {f(nf['full_imm'].std(),1)}; "
     f"{f(nf['full_imm'].min())}% Kancheepuram to {f(nf['full_imm'].max())}% Thoothukkudi). In HMIS, the district median for 4+ ANC moved "
     f"{f(anc_by_fy['2018-19'])}% → {f(anc_by_fy['2019-20'])}% → {f(anc_by_fy['2020-21'])}%. "
     f"Trichy is mid-table on NFHS-5 4+ ANC ({f(trichy.loc['anc4','nfhs'])}%), but its HMIS rate has declined each year "
     f"({f(tr_h.loc['2018-19','anc4'])} → {f(tr_h.loc['2019-20','anc4'])} → {f(tr_h.loc['2020-21','anc4'])}%) "
     "while the district median recovered to {:.0f}% in 2020-21. That is worth a block-level look.".format(anc_by_fy["2020-21"]), "Descriptive picture. ")
figure(FIG / "fig1_state_monthly.png", 16, "Figure 2. Tamil Nadu monthly HMIS counts, three financial years. "
       "Registrations dipped after the 2020 lockdown; deliveries fell ~9 months later. February is low every year.")
para(f"Spearman correlations against seven NFHS-5 district covariates (wealth is not in the district factsheets, so clean "
     f"fuel, insurance and sanitation stand in for it), with bootstrap CIs. 4+ ANC is associated with household health-insurance coverage "
     f"(ρ = {f(ins.spearman_rho,2)}, 95% CI {f(ins.ci_low,2)}–{f(ins.ci_high,2)}). This is the only association that survives a "
     f"Bonferroni correction for 7 tests. Full immunisation is weakly associated with women's 10+ years of schooling "
     f"(ρ = {f(sch.spearman_rho,2)}, CI {f(sch.ci_low,2)}–{f(sch.ci_high,2)}), which does not survive correction. "
     "Schooling and clean fuel are, if anything, negatively related to 4+ ANC: the more urban districts (Chennai, "
     "Kanniyakumari, Thoothukkudi) are not the best performers.", "Exploratory correlates. ")
figure(FIG / "fig4_drivers.png", 15.5, "Figure 3. Strongest bivariate associations, NFHS-5 district level (n = 32/31).")
para("With 31–32 districts, a correlation needs |ρ| > 0.35 just to reach p < 0.05, and the CIs above span ~0.5. "
     "These are ecological associations: insurance coverage (largely the state CM scheme) probably proxies for reach of "
     "the public system and VHN outreach, not a causal lever. The outcome itself is measured with ±5–12 point error. Nothing here "
     "supports causal claims; it suggests where to look, e.g. whether low-insurance blocks are also low-outreach blocks.",
     "Limits of inference. ")

# ---------------------------------------------------------------- next steps
doc.add_heading("5. Dashboard and next steps", 1)
para("https://hmis-dashboard-23pwg7jrxhautuh6wbjhba.streamlit.app/. Filters by district (default Trichy), indicator, year and district frame. Tabs: at-a-glance "
     "takeaways with a 'trust level' per indicator; district ranking; monthly trends; HMIS vs NFHS-5 with uncertainty; data-quality checks.",
     "Live dashboard: ")
para("(1) Obtain 2021-22 onward HMIS (NDAP/portal login) and RCH/PICME registrations to build resident denominators at block level. "
     "(2) Field-check first-trimester recording with 2–3 PHCs. (3) Re-triangulate against NFHS-6 when district data is released.",
     "If I had more time / access: ")

doc.save(OUT)
print("saved", OUT)
