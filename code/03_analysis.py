"""
03_analysis.py
Task 2 (triangulation) and Task 3 (outcomes & drivers); writes tables + report figures.

Outputs:
  data/processed/triangulation_district.csv, triangulation_summary.csv
  data/processed/fic_denominator_sensitivity.csv
  data/processed/drivers_correlations.csv
  data/processed/dashboard_long.csv   (single tidy file the dashboard reads)
  report/figures/*.png
"""
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "report" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)

HMIS_C, NFHS_C, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "figure.dpi": 150})

LABELS = {"anc4": "4+ ANC visits (%)", "anc_1st_trimester": "ANC registered in 1st trimester (%)",
          "inst_births": "Institutional births (%)", "full_imm": "Full immunisation (%)",
          "csection": "C-section births (%)", "inst_births_private": "Births in private facilities (%)"}

hm = pd.read_csv(PROC / "hmis_indicators_fy.csv")
nf_long = pd.read_csv(PROC / "nfhs5_tn.csv")
nf = nf_long.pivot(index="district_nfhs32", columns="indicator", values="value")
nf_flag = nf_long.pivot(index="district_nfhs32", columns="indicator", values="flag")
nf["inst_births_private"] = nf["inst_births"] - nf["inst_births_public"]

# ----------------------------------------------------------------------------------------
# Residence-based denominator for full immunisation (sensitivity)
# HMIS counts births where they OCCUR. Children are immunised where they LIVE. Districts with
# referral hospitals (Chennai, Vellore, Trichy, Madurai) therefore look "under-immunised" and
# their catchment districts look >100%. Proxy for resident birth cohort: last year's ANC
# registrations (done near home) x state ratio of live births to ANC registrations.
# ----------------------------------------------------------------------------------------
h32 = hm[hm.frame == 32].set_index(["fy", "frame_district"])
state_ratio = (h32.xs("Tamil Nadu (state)", level=1)["n_live_births"] /
               h32.xs("Tamil Nadu (state)", level=1)["n_anc_registered"])
sens = []
for fy, prev in [("2019-20", "2018-19"), ("2020-21", "2019-20")]:
    cur, pr = h32.xs(fy, level=0), h32.xs(prev, level=0)
    exp_births = pr["n_anc_registered"] * state_ratio[prev]
    sens.append(pd.DataFrame({"fy": fy, "full_imm_occurrence": cur["full_imm"],
                              "full_imm_residence": 100 * cur["n_fic"] / exp_births,
                              "births_per_anc": cur["n_live_births"] / cur["n_anc_registered"]}))
sens = pd.concat(sens).reset_index()
sens.to_csv(PROC / "fic_denominator_sensitivity.csv", index=False)

# ----------------------------------------------------------------------------------------
# Task 2: triangulation (32-district frame; HMIS 2018-19 + 2019-20 pooled = closest public
# overlap with NFHS-5 reference period, i.e. births in the 5 years before early-2020 fieldwork)
# ----------------------------------------------------------------------------------------
pool = (hm[(hm.frame == 32) & hm.fy.isin(["2018-19", "2019-20"])]
        .groupby("frame_district")[[c for c in hm.columns if c.startswith("n_")]].sum())
raw = pd.read_csv(PROC / "hmis_long.csv", usecols=["fy", "period", "district_raw", "item_code", "sector", "value"],
                  dtype={"item_code": str})
raw = raw[(raw.period == "FY") & raw.fy.isin(["2018-19", "2019-20"])]
xw = pd.read_csv(ROOT / "data" / "district_crosswalk.csv")
raw = raw.merge(xw[["district_raw", "district_nfhs32"]], on="district_raw")
raw.loc[raw.district_raw == "Tamil Nadu", "district_nfhs32"] = "Tamil Nadu (state)"
raw = raw[raw.district_nfhs32 != "STATE"]
def s(code, sector="total"):
    return raw[(raw.item_code == code) & (raw.sector == sector)].groupby("district_nfhs32")["value"].sum()
H = pd.DataFrame({
    "anc4": 100 * s("1.2.7") / s("1.1"),
    "anc_1st_trimester": 100 * s("1.1.1") / s("1.1"),
    "inst_births": 100 * s("2.2") / (s("2.2") + s("2.1.1.a") + s("2.1.1.b")),
    "csection": 100 * s("3.1") / s("2.2"),
    "inst_births_private": 100 * s("2.2", "private") / s("2.2"),
    "full_imm": 100 * (s("9.2.4.a") + s("9.2.4.b")) / (s("4.1.1.a") + s("4.1.1.b")),
})
H["full_imm_residence"] = sens[sens.fy == "2019-20"].set_index("frame_district")["full_imm_residence"]
births_w = s("4.1.1.a") + s("4.1.1.b")

def approx_ci(p, n, deff=1.5):
    """Indicative 95% CI half-width (pp) for a survey proportion."""
    p = np.clip(p / 100, 0.01, 0.99)
    return 196 * np.sqrt(deff * p * (1 - p) / n)

rows, summ = [], []
for ind in ["anc4", "anc_1st_trimester", "inst_births", "csection", "inst_births_private", "full_imm"]:
    for d in nf.index:
        hv = H.loc[d, ind]
        nv = nf.loc[d, ind]
        flag = nf_flag.loc[d, ind] if ind in nf_flag.columns else ""
        # rough n: full immunisation -> 25-49 if flagged, else assume 50-80; birth indicators ~25% of women
        if ind == "full_imm":
            n = 37 if "small" in str(flag) else 65
        else:
            n = 0.25 * nf.loc[d, "n_women"]
        ci = approx_ci(nv, n) if pd.notna(nv) else np.nan
        rows.append({"district": d, "indicator": ind, "hmis": hv, "nfhs": nv, "gap": hv - nv,
                     "nfhs_ci_halfwidth": ci, "outside_ci": abs(hv - nv) > ci if pd.notna(nv) else np.nan,
                     "nfhs_flag": flag if isinstance(flag, str) else ""})
tri = pd.DataFrame(rows)
# residence-based full immunisation as an extra row-set
fr = tri[tri.indicator == "full_imm"].copy()
fr["indicator"] = "full_imm_residence"
fr["hmis"] = fr["district"].map(H["full_imm_residence"])
fr["gap"] = fr["hmis"] - fr["nfhs"]
fr["outside_ci"] = fr["gap"].abs() > fr["nfhs_ci_halfwidth"]
tri = pd.concat([tri, fr], ignore_index=True)
tri.to_csv(PROC / "triangulation_district.csv", index=False)

for ind, g in tri.groupby("indicator"):
    g = g.dropna(subset=["hmis", "nfhs"])
    w = g["district"].map(births_w)
    rho, p = stats.spearmanr(g.hmis, g.nfhs)
    summ.append({"indicator": ind, "n_districts": len(g),
                 "hmis_state": H.loc["Tamil Nadu (state)", ind] if ind in H.columns else np.nan,
                 "nfhs_births_weighted": np.average(g.nfhs, weights=w),
                 "mean_gap": g.gap.mean(), "mean_abs_gap": g.gap.abs().mean(),
                 "max_gap": g.gap.max(), "min_gap": g.gap.min(),
                 "hmis_sd": g.hmis.std(), "nfhs_sd": g.nfhs.std(),
                 "spearman_rho": rho, "spearman_p": p,
                 "share_outside_ci": g.outside_ci.mean(),
                 "hmis_over_100": (g.hmis > 100).sum()})
summ = pd.DataFrame(summ)
summ.to_csv(PROC / "triangulation_summary.csv", index=False)
print(summ.round(2).to_string())

# ----------------------------------------------------------------------------------------
# Task 3: outcomes & drivers (NFHS-5, n = 32 districts; exploratory)
# ----------------------------------------------------------------------------------------
COVS = {"fem_school10": "Women with 10+ yrs schooling", "clean_fuel": "Households using clean cooking fuel",
        "health_insurance": "Households with health insurance", "child_marriage": "Women 20-24 married before 18",
        "births_3plus": "Births of order 3+", "improved_sanitation": "Improved sanitation",
        "mcp_card": "Pregnancies with MCP card"}
OUTS = {"anc4": "4+ ANC visits", "full_imm": "Full immunisation"}
drv = []
for o in OUTS:
    for c in COVS:
        d = nf[[o, c]].dropna()
        rho, p = stats.spearmanr(d[o], d[c])
        boots = []
        for _ in range(2000):
            i = rng.integers(0, len(d), len(d))
            boots.append(stats.spearmanr(d[o].values[i], d[c].values[i])[0])
        lo, hi = np.nanpercentile(boots, [2.5, 97.5])
        drv.append({"outcome": o, "covariate": c, "covariate_label": COVS[c], "n": len(d),
                    "spearman_rho": rho, "p_value": p, "ci_low": lo, "ci_high": hi,
                    "bonferroni_sig": p < 0.05 / len(COVS)})
drv = pd.DataFrame(drv)
drv.to_csv(PROC / "drivers_correlations.csv", index=False)
print(drv.round(3).to_string())

# ----------------------------------------------------------------------------------------
# Dashboard data (one tidy table)
# ----------------------------------------------------------------------------------------
mi = pd.read_csv(PROC / "hmis_indicators_monthly.csv")
dash = []
for ind in ["anc4", "anc_1st_trimester", "inst_births", "full_imm", "csection"]:
    t = hm[[c for c in ["frame", "fy", "frame_district", ind] if c in hm.columns]].rename(
        columns={ind: "value", "frame_district": "district"})
    t["indicator"], t["source"], t["period"] = ind, "HMIS", "FY"
    dash.append(t)
    m = mi[["fy", "period", "month_start", "frame_district", ind]].rename(
        columns={ind: "value", "frame_district": "district"})
    m["indicator"], m["source"], m["frame"] = ind, "HMIS", 38
    dash.append(m)
t = hm[["frame", "fy", "frame_district", "inst_births_private"]].rename(
    columns={"inst_births_private": "value", "frame_district": "district"})
t["indicator"], t["source"], t["period"] = "inst_births_private", "HMIS", "FY"
dash.append(t)
for ind in ["anc4", "anc_1st_trimester", "inst_births", "full_imm", "csection", "inst_births_private"]:
    n = nf[[ind]].reset_index().rename(columns={"district_nfhs32": "district", ind: "value"})
    n["indicator"], n["source"], n["fy"], n["period"], n["frame"] = ind, "NFHS-5", "2019-21", "survey", 32
    n["flag"] = n["district"].map(nf_flag[ind]) if ind in nf_flag.columns else ""
    dash.append(n)
pd.concat(dash, ignore_index=True).to_csv(PROC / "dashboard_long.csv", index=False)

# ----------------------------------------------------------------------------------------
# Figures for the report
# ----------------------------------------------------------------------------------------
def dumbbell(ind, fname, title, xlim=None):
    g = tri[tri.indicator == ind].dropna(subset=["hmis"]).sort_values("nfhs", na_position="first")
    fig, ax = plt.subplots(figsize=(6.6, 6.2))
    y = np.arange(len(g))
    ax.hlines(y, g[["hmis", "nfhs"]].min(axis=1), g[["hmis", "nfhs"]].max(axis=1), color=GRID, lw=2, zorder=1)
    ax.errorbar(g.nfhs, y, xerr=g.nfhs_ci_halfwidth, fmt="none", ecolor=NFHS_C, alpha=.35, lw=1, zorder=2)
    small = g.nfhs_flag.str.contains("small", na=False)
    ax.scatter(g.nfhs[~small], y[~small], s=34, color=NFHS_C, label="NFHS-5 (survey)", zorder=3, edgecolor="white", lw=1)
    ax.scatter(g.nfhs[small], y[small], s=34, facecolor="white", edgecolor=NFHS_C, lw=1.5,
               label="NFHS-5, 25-49 cases only", zorder=3)
    ax.scatter(g.hmis, y, s=34, color=HMIS_C, label="HMIS 2018-20 (admin)", zorder=4, edgecolor="white", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([("▶ " + d) if d == "Tiruchirappalli" else d for d in g.district], fontsize=7.5)
    for lab in ax.get_yticklabels():
        if "Tiruchirappalli" in lab.get_text():
            lab.set_fontweight("bold")
    ax.axvline(100, color=MUTED, lw=.8, ls=":")
    if xlim:
        ax.set_xlim(*xlim)
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    ax.legend(loc="lower right", fontsize=7, frameon=False)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(FIG / fname)
    plt.close(fig)

dumbbell("anc4", "fig2_anc4_dumbbell.png", "4+ ANC visits: HMIS vs NFHS-5, by district (%)", (55, 105))
dumbbell("full_imm", "fig3a_fic_occurrence.png", "Full immunisation: HMIS (÷ births recorded in district) vs NFHS-5", (55, 165))
dumbbell("full_imm_residence", "fig3b_fic_residence.png", "Full immunisation: HMIS (÷ resident-birth proxy) vs NFHS-5", (55, 165))

# Fig 1: state monthly time series (counts), 3 FYs overlaid
st = mi[mi.frame_district == "Tamil Nadu (state)"].copy()
order = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), sharex=True)
cols = {"2018-19": "#9ec5f4", "2019-20": "#3987e5", "2020-21": "#0d366b"}
for ax, var, ttl in [(axes[0], "n_anc_registered", "New ANC registrations (thousands)"),
                     (axes[1], "n_inst_deliveries", "Institutional deliveries (thousands)")]:
    for fy, g in st.groupby("fy"):
        g = g.set_index("period").loc[order]
        ax.plot(range(12), g[var] / 1000, color=cols[fy], lw=2, label=fy)
    ax.set_xticks(range(12))
    ax.set_xticklabels(order, fontsize=7)
    ax.set_title(ttl, loc="left", fontsize=9.5)
axes[0].axvspan(3, 7, color=GRID, alpha=.6, lw=0)
axes[0].text(5, axes[0].get_ylim()[1] - 0.5, "2020 dip (Jul-Nov)", ha="center", va="top", fontsize=7, color=MUTED)
axes[1].axvspan(9, 11, color=GRID, alpha=.6, lw=0)
axes[1].text(10, axes[1].get_ylim()[1] - 0.5, "~9 months later", ha="center", va="top", fontsize=7, color=MUTED)
axes[1].legend(fontsize=7, frameon=False, loc="lower left")
fig.tight_layout()
fig.savefig(FIG / "fig1_state_monthly.png")
plt.close(fig)

# Fig 4: drivers - scatter of ANC4 vs 10+ yrs schooling and full_imm vs schooling
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
for ax, o in zip(axes, ["anc4", "full_imm"]):
    best = drv[drv.outcome == o].iloc[drv[drv.outcome == o].spearman_rho.abs().argmax()]
    c = best.covariate
    d = nf[[o, c]].dropna()
    ax.scatter(d[c], d[o], s=30, color=HMIS_C, edgecolor="white", lw=1)
    if "Tiruchirappalli" in d.index:
        ax.scatter(d.loc["Tiruchirappalli", c], d.loc["Tiruchirappalli", o], s=60, color=NFHS_C, edgecolor="white", zorder=5)
        ax.annotate("Trichy", (d.loc["Tiruchirappalli", c], d.loc["Tiruchirappalli", o]), xytext=(5, -10),
                    textcoords="offset points", fontsize=7.5)
    ax.set_xlabel(COVS[c] + " (%)")
    ax.set_ylabel(OUTS[o] + " (%), NFHS-5")
    ax.set_title(f"{OUTS[o]}: strongest bivariate association\nSpearman ρ = {best.spearman_rho:.2f} "
                 f"(95% CI {best.ci_low:.2f} to {best.ci_high:.2f}), n = {int(best.n)}", loc="left", fontsize=8.5)
fig.tight_layout()
fig.savefig(FIG / "fig4_drivers.png")
plt.close(fig)

# Fig 5: ANC4 by district over time (HMIS, 38 frame) - small slope chart of 2018-19 -> 2020-21 (32 frame)
p = hm[hm.frame == 32].pivot(index="frame_district", columns="fy", values="anc4").drop("Tamil Nadu (state)")
fig, ax = plt.subplots(figsize=(4.4, 4.6))
for d, r in p.iterrows():
    hl = d == "Tiruchirappalli"
    ax.plot([0, 1, 2], r.values, color=NFHS_C if hl else "#b7d3f6", lw=2.2 if hl else 1, zorder=3 if hl else 1)
ax.plot([0, 1, 2], p.median().values, color=HMIS_C, lw=2.5, label="District median")
ax.annotate("Trichy", (2, p.loc["Tiruchirappalli"].values[-1]), xytext=(4, 0), textcoords="offset points", fontsize=7.5)
ax.set_xticks([0, 1, 2])
ax.set_xticklabels(p.columns)
ax.set_title("HMIS 4+ ANC (%) by district, 3 years", loc="left", fontsize=9.5)
ax.legend(frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig(FIG / "fig5_anc4_trend.png")
plt.close(fig)
print("figures written to", FIG)
