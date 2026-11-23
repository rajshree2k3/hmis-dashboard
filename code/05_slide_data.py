"""05_slide_data.py - export the numbers the slide deck needs to report/slide_data.json"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
summ = pd.read_csv(P / "triangulation_summary.csv").set_index("indicator")
tri = pd.read_csv(P / "triangulation_district.csv")
sens = pd.read_csv(P / "fic_denominator_sensitivity.csv")
drv = pd.read_csv(P / "drivers_correlations.csv")
hm = pd.read_csv(P / "hmis_indicators_fy.csv")
mi = pd.read_csv(P / "hmis_indicators_monthly.csv")
nf = pd.read_csv(P / "nfhs5_tn.csv").pivot(index="district_nfhs32", columns="indicator", values="value")

r = lambda x, d=1: None if pd.isna(x) else round(float(x), d)
order = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
st = mi[mi.frame_district == "Tamil Nadu (state)"]
monthly = {}
for var in ["n_anc_registered", "n_inst_deliveries"]:
    monthly[var] = {fy: [r(v / 1000) for v in g.set_index("period").loc[order, var]] for fy, g in st.groupby("fy")}

trichy = tri[tri.district == "Tiruchirappalli"].set_index("indicator")
h38 = hm[(hm.frame == 38)]
tr = h38[h38.frame_district == "Tiruchirappalli"].set_index("fy")
med = h38[h38.frame_district != "Tamil Nadu (state)"].groupby("fy")["anc4"].median()
s19 = sens[(sens.fy == "2019-20") & (sens.frame_district != "Tamil Nadu (state)")]

data = {
    "summary": {i: {k: r(summ.loc[i, k], 2) for k in ["hmis_state", "nfhs_births_weighted", "mean_abs_gap",
                                                      "mean_gap", "spearman_rho", "share_outside_ci", "hmis_over_100"]}
                for i in summ.index},
    "monthly": monthly, "months": order,
    "trichy": {i: {"hmis": r(trichy.loc[i, "hmis"], 3), "nfhs": r(trichy.loc[i, "nfhs"], 3)} for i in trichy.index},
    "trichy_anc4_by_fy": {fy: r(tr.loc[fy, "anc4"]) for fy in tr.index},
    "median_anc4_by_fy": {fy: r(v) for fy, v in med.items()},
    "fic_sd": {"occurrence": r(s19.full_imm_occurrence.std()), "residence": r(s19.full_imm_residence.std())},
    "first_tri_hmis_higher": int((tri[tri.indicator == "anc_1st_trimester"].gap > 0).sum()),
    "drivers": drv[["outcome", "covariate_label", "spearman_rho", "ci_low", "ci_high", "bonferroni_sig"]]
               .round(2).to_dict(orient="records"),
    "nfhs_anc4": {"mean": r(nf.anc4.mean()), "min": r(nf.anc4.min(), 0), "max": r(nf.anc4.max(), 0)},
    "nfhs_fic": {"mean": r(nf.full_imm.mean()), "min": r(nf.full_imm.min(), 0), "max": r(nf.full_imm.max(), 0)},
}
(ROOT / "report" / "slide_data.json").write_text(json.dumps(data, indent=1))
print(json.dumps({k: data[k] for k in ["trichy_anc4_by_fy", "median_anc4_by_fy", "fic_sd", "first_tri_hmis_higher"]}))
