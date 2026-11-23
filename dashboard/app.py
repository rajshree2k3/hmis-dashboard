"""
Tamil Nadu Maternal & Child Health - HMIS vs NFHS-5 dashboard
Audience: District Collector's team, Tiruchirappalli.
Run locally:  streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data" / "processed"
HMIS_C, NFHS_C, HL_C, BASE_C, MUTED = "#2a78d6", "#eb6834", "#eb6834", "#9ec5f4", "#52514e"

st.set_page_config(page_title="TN MCH Data Check", page_icon="🩺", layout="wide")

IND = {
    "anc4": "4+ antenatal check-ups",
    "anc_1st_trimester": "ANC registered in 1st trimester",
    "full_imm": "Full immunisation (9-11 months)",
    "csection": "C-section deliveries",
    "inst_births": "Institutional deliveries",
    "inst_births_private": "Deliveries in private facilities",
}
# How far to trust each HMIS indicator - from the data-quality and triangulation work.
TRUST = {
    "anc4": ("⚠️ Use with caution", "State average matches NFHS-5 (89% vs 90%), but district rankings do not "
             "(rank correlation ≈ 0). Do not use HMIS alone to rank districts."),
    "anc_1st_trimester": ("⛔ Do not rely on", "HMIS is ~16 points higher than NFHS-5 in almost every district. "
                          "Likely recording practice (registration date vs first check-up)."),
    "full_imm": ("⛔ Not for ranking", "18 of 31 comparable districts exceed 100% (2018-20): births are counted where they happen, children "
                 "are immunised where they live. Use the 'resident-birth' version (Admin vs Survey tab) for comparisons."),
    "csection": ("✅ Reasonably reliable", "State level matches NFHS-5 (45% vs 46%) and district rankings agree (ρ = 0.68)."),
    "inst_births": ("✅ Reliable, but saturated", "~100% in both sources - no longer useful for telling districts apart."),
    "inst_births_private": ("⚠️ Use with caution", "Counts where delivery happens: hub districts (Chennai, Coimbatore, "
                            "Trichy) attract births from neighbours. Higher than NFHS-5 by ~10 points on average."),
}
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]


@st.cache_data
def load():
    d = pd.read_csv(DATA / "dashboard_long.csv", parse_dates=["month_start"])
    d["frame"] = d["frame"].astype("Int64").astype(str)
    tri = pd.read_csv(DATA / "triangulation_district.csv")
    summ = pd.read_csv(DATA / "triangulation_summary.csv")
    comp = pd.read_csv(DATA / "dq_completeness.csv")
    flags = pd.read_csv(DATA / "dq_logic_flags.csv")
    drv = pd.read_csv(DATA / "drivers_correlations.csv")
    return d, tri, summ, comp, flags, drv


d, tri, summ, comp, flags, drv = load()

# ---------------------------------------------------------------- sidebar filters
st.sidebar.title("Filters")
frame = st.sidebar.radio("District boundaries", ["38 (current districts)", "32 (NFHS-5 boundaries)"],
                         help="NFHS-5 reports on the 32 pre-2019 districts. To compare with it, new districts are "
                              "added back to their parent district (e.g. Tenkasi → Tirunelveli).")
fr = frame.split()[0]
fy_all = d[(d.source == "HMIS") & (d.period == "FY") & (d.frame == fr)]
districts = sorted([x for x in fy_all.district.unique() if x != "Tamil Nadu (state)"])
district = st.sidebar.selectbox("District", districts, index=districts.index("Tiruchirappalli"))
indicator = st.sidebar.selectbox("Indicator", list(IND), format_func=IND.get)
fy = st.sidebar.selectbox("Financial year (HMIS)", ["2020-21", "2019-20", "2018-19"])
st.sidebar.caption("HMIS: Ministry of Health HMIS portal, standard reports (district-wise). Public downloads cover up to "
                   "2020-21. NFHS-5 (2019-21), Tamil Nadu fieldwork early 2020.")

st.title("Tamil Nadu maternal & child health: what the data says, and how far to trust it")
st.caption("Government records (HMIS) checked against the national household survey (NFHS-5).")

tabs = st.tabs(["At a glance", "Compare districts", "Trends", "Admin vs survey", "Data quality", "About the data"])

# ---------------------------------------------------------------- 1. at a glance
with tabs[0]:
    st.subheader("Key takeaways")
    st.markdown(
        """
1. **Deliveries in hospitals are ~100% everywhere**, in both records and the survey. That target is met; it can no longer tell districts apart.
2. **Do not rank districts on HMIS 4+ ANC or full immunisation alone.** The state averages are believable, but district rankings do not match the survey.
3. **Full immunisation above 100% is a counting artefact, not over-performance.** Births are counted where they happen and children are vaccinated where they live. Hub districts like **Trichy**, Chennai and Vellore look low; their neighbours look high.
4. **'1st-trimester registration' in HMIS (~93%) is far above the survey (~78%).** Verify how VHNs record the registration date before using this for targets.
5. **COVID-19:** new pregnancy registrations fell in Jul–Nov 2020 and deliveries fell ~9 months later (Jan–Mar 2021). This matches fewer conceptions during the lockdown, not a reporting failure.
        """)
    st.divider()
    st.subheader(f"{district}: {fy}")
    cols = st.columns(3)
    for i, ind in enumerate(IND):
        h = fy_all[(fy_all.indicator == ind) & (fy_all.fy == fy)]
        v = h.loc[h.district == district, "value"]
        s = h.loc[h.district == "Tamil Nadu (state)", "value"]
        n = d[(d.source == "NFHS-5") & (d.indicator == ind)]
        nfhs_parent = tri.set_index("district")  # 32-frame names
        with cols[i % 3]:
            with st.container(border=True):
                val = f"{v.iloc[0]:.0f}%" if len(v) and pd.notna(v.iloc[0]) else "–"
                delta = (f"{v.iloc[0] - s.iloc[0]:+.0f} pts vs state" if len(v) and len(s) and pd.notna(v.iloc[0])
                         else None)
                st.metric(IND[ind] + " (HMIS)", val, delta, delta_color="off")
                st.caption(f"**{TRUST[ind][0]}**: {TRUST[ind][1]}")

# ---------------------------------------------------------------- 2. compare districts
with tabs[1]:
    st.subheader(f"{IND[indicator]}: all districts, HMIS {fy}")
    st.caption(f"Trust level: **{TRUST[indicator][0]}**. {TRUST[indicator][1]}")
    g = fy_all[(fy_all.indicator == indicator) & (fy_all.fy == fy)].dropna(subset=["value"])
    state_v = g.loc[g.district == "Tamil Nadu (state)", "value"]
    g = g[g.district != "Tamil Nadu (state)"].sort_values("value")
    colors = [HL_C if x == district else BASE_C for x in g.district]
    fig = go.Figure(go.Bar(x=g.value, y=g.district, orientation="h", marker_color=colors,
                           hovertemplate="%{y}: %{x:.1f}%<extra></extra>"))
    if len(state_v):
        fig.add_vline(x=state_v.iloc[0], line_dash="dot", line_color=MUTED,
                      annotation_text=f"State {state_v.iloc[0]:.0f}%", annotation_position="top")
    if indicator in ("full_imm", "anc4"):
        fig.add_vline(x=100, line_color="#e34948", line_width=1,
                      annotation_text="100% (values above are impossible)", annotation_position="bottom right")
    fig.update_layout(height=max(450, 22 * len(g)), margin=dict(l=10, r=10, t=30, b=10),
                      xaxis_title="%", plot_bgcolor="white", bargap=0.25)
    st.plotly_chart(fig, width="stretch")
    st.caption("Orange = selected district. Dotted line = state value.")

# ---------------------------------------------------------------- 3. trends
with tabs[2]:
    st.subheader(f"{IND[indicator]}: monthly, {district} vs state (HMIS, current districts)")
    m = d[(d.source == "HMIS") & (d.period.isin(MONTHS)) & (d.indicator == indicator)]
    dist38 = district if district in m.district.unique() else None
    if dist38 is None:
        st.info("Monthly trends are shown on current (38) district boundaries. Pick the district in 38-district mode.")
    fig = go.Figure()
    for name, col, w in [("Tamil Nadu (state)", MUTED, 1.5), (dist38, HMIS_C, 2.5)]:
        if name is None:
            continue
        s = m[m.district == name].sort_values("month_start")
        fig.add_trace(go.Scatter(x=s.month_start, y=s.value, name=name, mode="lines+markers",
                                 line=dict(color=col, width=w), marker=dict(size=5),
                                 hovertemplate="%{x|%b %Y}: %{y:.1f}%<extra>" + name + "</extra>"))
    fig.add_vrect(x0="2020-03-25", x1="2020-06-30", fillcolor="#e4e3df", opacity=0.5, line_width=0,
                  annotation_text="COVID lockdown", annotation_position="top left")
    fig.update_layout(height=420, hovermode="x unified", plot_bgcolor="white", yaxis_title="%",
                      margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width="stretch")
    st.caption("Monthly ratios jump around because numerator and denominator are not the same women/children "
               "(e.g. 4+ ANC visits this month vs registrations this month). Read the trend, not single months.")
    a = d[(d.source == "HMIS") & (d.period == "FY") & (d.indicator == indicator) & (d.frame == fr)]
    p = a.pivot_table(index="district", columns="fy", values="value").round(1)
    st.markdown("**Year-on-year, all districts**")
    st.dataframe(p.style.format("{:.1f}").highlight_between(left=100.0001, right=1e9, color="#fde2e1"),
                 width="stretch", height=300)

# ---------------------------------------------------------------- 4. admin vs survey
with tabs[3]:
    st.subheader("Government records (HMIS) vs household survey (NFHS-5), 32 NFHS districts")
    opts = {**{k: IND[k] for k in IND}, "full_imm_residence": "Full immunisation, resident-birth denominator"}
    ind2 = st.selectbox("Indicator to compare", list(opts), format_func=opts.get,
                        index=list(opts).index(indicator))
    t = tri[tri.indicator == ind2].sort_values("nfhs")
    s = summ.set_index("indicator").loc[ind2]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("HMIS, state (2018-20)", f"{s.hmis_state:.0f}%")
    c2.metric("NFHS-5, state (approx.)", f"{s.nfhs_births_weighted:.0f}%")
    c3.metric("Average gap by district", f"{s.mean_abs_gap:.0f} pts")
    c4.metric("Do rankings agree?", f"ρ = {s.spearman_rho:.2f}",
              "Yes" if s.spearman_rho > 0.5 else "No", delta_color="normal" if s.spearman_rho > 0.5 else "inverse")
    fig = go.Figure()
    for _, r in t.iterrows():
        fig.add_trace(go.Scatter(x=[r.hmis, r.nfhs], y=[r.district] * 2, mode="lines",
                                 line=dict(color="#e4e3df", width=3), showlegend=False, hoverinfo="skip"))
    small = t.nfhs_flag.fillna("").str.contains("small")
    fig.add_trace(go.Scatter(x=t.nfhs, y=t.district, mode="markers", name="NFHS-5 survey",
                             error_x=dict(type="data", array=t.nfhs_ci_halfwidth, color="rgba(235,104,52,.35)"),
                             marker=dict(size=10, color=[("white" if x else NFHS_C) for x in small],
                                         line=dict(color=NFHS_C, width=2)),
                             customdata=t.nfhs_flag.fillna(""),
                             hovertemplate="%{y}<br>NFHS-5: %{x:.1f}% %{customdata}<extra></extra>"))
    fig.add_trace(go.Scatter(x=t.hmis, y=t.district, mode="markers", name="HMIS 2018-20",
                             marker=dict(size=10, color=HMIS_C, line=dict(color="white", width=1)),
                             hovertemplate="%{y}<br>HMIS: %{x:.1f}%<extra></extra>"))
    fig.update_layout(height=820, plot_bgcolor="white", xaxis_title="%", margin=dict(l=10, r=10, t=20, b=10),
                      legend=dict(orientation="h", y=1.03))
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        """
**How to read this.** Hollow orange circles mean NFHS-5 is based on only 25–49 children/women in that district, so it carries a large margin of error (shown by the faint bar, indicative only).
Gaps arise from: (1) **place of event vs residence**: HMIS counts where the service happened, the survey asks where the mother lives;
(2) **denominators**: HMIS divides by reported events, not by all pregnancies/births in the population;
(3) **reference period**: NFHS-5 covers births in the 5 years before early 2020; HMIS here is Apr 2018–Mar 2020;
(4) **survey sampling error** at district level.
The comparison **can** show where HMIS is systematically off; it **cannot** say which source is "true" for a single district.
        """)

# ---------------------------------------------------------------- 5. data quality
with tabs[4]:
    st.subheader("Data-quality checks on HMIS")
    st.markdown(
        """
| Check | Result | What we did |
|---|---|---|
| Monthly files add up to the annual file | ✅ 0 mismatches in 4,900 district-item-sector rows (2018-20) | Used annual files for annual numbers |
| Public + private = total; urban + rural = total | ✅ No mismatches | – |
| Missing months | ✅ No blank months for key items, except **Mayiladuthurai** (new district, Dec 2020: all zeros) | Added it to Nagapattinam (its parent) |
| Private-sector reporting | ⚠️ ANC items have **no private entries at all**; private full-immunisation entries vanish in most districts from 2019-20 | Treat ANC as public-system registrations; flag immunisation |
| Values above 100% | ⛔ Full immunisation >100% in 18 of 31 comparable districts (2018-20 pooled); 4+ ANC up to 110% in 2020-21 | Built a resident-birth denominator; do not rank on raw HMIS |
| Births vs deliveries | ✅ Live births ÷ deliveries = 0.99–1.01 in all districts | Births are a sound denominator *for where births occur* |
| Unusual months (robust z > 3.5) | ⚠️ 418 district-months, mostly immunisation-session counts and Feb/Oct | Kept; read trends, not single months |
| Definitions changed | ℹ️ MR → MR/MCV (2020-21), "TT" → "Td"; minor | Treated as continuous |
        """)
    st.markdown("**Months with zero reported for the selected district** (Total column; zero home deliveries is normal in TN)")
    c = comp[(comp.district_38 == district)].pivot_table(index="item", columns="fy", values="months_zero")
    if len(c):
        st.dataframe(c, width="stretch")
    else:
        st.info("Switch to 38-district mode to see this for the current district.")
    st.markdown("**Indicator values above 100% (impossible) by FY**")
    f = flags[flags.frame.astype(str) == fr].groupby("fy")[["flag_anc4_gt_reg", "flag_fic_gt_lb"]].sum()
    f.columns = ["4+ ANC > 100%", "Full immunisation > 100%"]
    st.dataframe(f, width="stretch")

# ---------------------------------------------------------------- 6. about
with tabs[5]:
    st.markdown(
        """
**Sources**
- HMIS: hmis.mohfw.gov.in → Standard Reports → *C2. Data Itemwise Monthly → All States Across Districts* (Tamil Nadu), FY 2018-19, 2019-20, 2020-21 (2020-21 marked provisional). Later years are not offered for public download on the portal.
- NFHS-5 district factsheets (2019-21), all-India district file (707 districts, same layout as data.gov.in). Values in brackets in the factsheet (25–49 cases) are flagged; Tiruppur's full-immunisation value is suppressed (<25 cases).

**Indicator definitions (HMIS)**
- 4+ ANC = women receiving 4+ check-ups ÷ women registered for ANC (same year)
- 1st-trimester registration = registered within 12 weeks ÷ registered
- Institutional deliveries = institutional ÷ (institutional + home)
- Full immunisation = children 9–11 months fully immunised ÷ live births (same year). *Resident-birth version*: ÷ (previous year's ANC registrations × state births-per-registration ratio)
- C-section = C-sections ÷ institutional deliveries
- Private share = deliveries in private facilities ÷ all institutional deliveries

**District boundaries.** Six districts were created in 2019-20 (Chengalpattu, Kallakurichi, Ranipet, Tirupathur, Tenkasi, Mayiladuthurai). For comparison with NFHS-5 their counts are added back to the parent district. Adding counts is exact; splitting survey estimates would not be.

Code, notes and full methods: see the project README.
        """)
