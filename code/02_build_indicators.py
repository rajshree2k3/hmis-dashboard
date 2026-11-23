"""
02_build_indicators.py
Cleans NFHS-5, harmonises district frames, builds HMIS indicators and runs data-quality checks.

Outputs (data/processed/):
  nfhs5_tn.csv              tidy NFHS-5 TN district indicators (+ small-sample flags)
  hmis_items_monthly.csv    selected HMIS items, district x month (38-district frame, as reported)
  hmis_indicators_fy.csv    HMIS indicators by district x FY, on BOTH frames (frame = '38' or '32')
  hmis_indicators_monthly.csv
  dq_*.csv                  data-quality check tables
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
XW = pd.read_csv(ROOT / "data" / "district_crosswalk.csv")

# ----------------------------------------------------------------------------------------
# 1. NFHS-5 (Tamil Nadu)
# ----------------------------------------------------------------------------------------
raw = pd.read_csv(ROOT / "data" / "raw" / "nfhs5_districts_707.csv")
raw = raw[raw["State/UT"].str.contains("Tamil")].copy()
raw["district"] = raw["District Names"].str.strip()

NFHS_COLS = {  # short name -> column index in the 707-district file
    "n_households": 2, "n_women": 3,
    "fem_literate": 18, "fem_school10": 19, "clean_fuel": 14, "health_insurance": 16,
    "electricity": 11, "improved_sanitation": 13, "child_marriage": 20, "births_3plus": 21,
    "anc_1st_trimester": 36, "anc4": 37, "ifa_180": 40, "mcp_card": 41,
    "inst_births": 46, "inst_births_public": 47, "skilled_birth": 49, "csection": 50,
    "csection_private": 51, "csection_public": 52,
    "full_imm": 53, "full_imm_card": 54, "bcg": 55, "penta3": 57, "mcv1": 58,
    "stunted": 77, "underweight": 80,
}
rows = []
for short, idx in NFHS_COLS.items():
    col = raw.columns[idx]
    for d, v in zip(raw["district"], raw[col]):
        s = str(v).strip()
        if s == "*":
            val, flag = np.nan, "suppressed (<25 cases)"
        else:
            f = float(s)
            # In this file, values shown in brackets in the official factsheet - i.e. based on
            # 25-49 unweighted cases - are stored as NEGATIVE numbers (verified against the
            # Phase-1 file, which carries an explicit note column).
            val, flag = abs(f), ("small sample (25-49 cases)" if f < 0 else "")
        rows.append({"district_nfhs32": d, "indicator": short, "label": col, "value": val, "flag": flag})
nfhs = pd.DataFrame(rows)
nfhs.to_csv(PROC / "nfhs5_tn.csv", index=False)
nfhs_w = nfhs.pivot(index="district_nfhs32", columns="indicator", values="value")
nfhs_flag = nfhs.pivot(index="district_nfhs32", columns="indicator", values="flag")
assert set(nfhs_w.index) == set(XW["district_nfhs32"]) - {"STATE"}, "NFHS / crosswalk names differ"

# ----------------------------------------------------------------------------------------
# 2. HMIS: keep the items we need
# ----------------------------------------------------------------------------------------
ITEMS = {
    "1.1": "anc_registered", "1.1.1": "anc_reg_1st_tri", "1.2.7": "anc4_received",
    "2.1.1.a": "home_del_sba", "2.1.1.b": "home_del_nonsba", "2.2": "inst_deliveries",
    "3.1": "csections", "4.1.1.a": "live_birth_m", "4.1.1.b": "live_birth_f", "4.1.3": "still_birth",
    "9.1.2": "bcg", "9.1.8": "penta3", "9.2.1": "mcv1", "9.2.4.a": "fic_m", "9.2.4.b": "fic_f",
    "9.7.1": "imm_sessions_planned", "9.7.2": "imm_sessions_held",
}
h = pd.read_csv(PROC / "hmis_long.csv", dtype={"item_code": str}, parse_dates=["month_start"])
# item-name consistency across years (definitional changes, e.g. TT -> Td)
names = h[h.item_code.isin(ITEMS)].groupby(["item_code", "fy"])["item_name"].first().unstack()
names.to_csv(PROC / "dq_item_names_by_year.csv")
h = h[h.item_code.isin(ITEMS)].copy()
h["item"] = h["item_code"].map(ITEMS)
h = h.merge(XW[["district_raw", "district_38", "district_nfhs32"]], on="district_raw", how="left")
assert h["district_38"].notna().all(), "unmapped district names"

# ----------------------------------------------------------------------------------------
# 3. Data-quality checks
# ----------------------------------------------------------------------------------------
dist = h[h.district_38 != "STATE"]
mon = dist[dist.period != "FY"]

# 3a. Completeness: blank vs zero, district x month, total column
tot = mon[mon.sector == "total"]
comp = tot.groupby(["fy", "district_38", "item"])["value"].agg(
    months_reported=lambda s: s.notna().sum(), months_zero=lambda s: (s == 0).sum()).reset_index()
comp.to_csv(PROC / "dq_completeness.csv", index=False)

# 3b. Private-sector reporting: share of FY total that comes from private facilities
fy = dist[dist.period == "FY"]
pp = fy.pivot_table(index=["fy", "district_38", "item"], columns="sector", values="value", aggfunc="sum")
pp["private_share"] = pp["private"] / pp["total"]
pp["pub_priv_gap"] = pp["total"] - (pp["public"].fillna(0) + pp["private"].fillna(0))
pp["urb_rur_gap"] = pp["total"] - (pp["urban"].fillna(0) + pp["rural"].fillna(0))
pp.reset_index().to_csv(PROC / "dq_sector_breakdown.csv", index=False)

# 3c. Sum of monthly files vs FY cumulative file (only for native monthly years)
sm = (mon[mon.fy.isin(["2018-19", "2019-20"])]
      .groupby(["fy", "district_38", "item", "sector"])["value"].sum(min_count=1))
fyv = fy.groupby(["fy", "district_38", "item", "sector"])["value"].sum(min_count=1)
mvf = pd.concat([sm.rename("sum_months"), fyv.rename("fy_file")], axis=1).dropna(how="all").reset_index()
mvf = mvf[mvf.fy.isin(["2018-19", "2019-20"])]
mvf["diff"] = mvf["fy_file"] - mvf["sum_months"]
mvf["pct_diff"] = 100 * mvf["diff"] / mvf["fy_file"]
mvf.to_csv(PROC / "dq_months_vs_fy.csv", index=False)

# 3d. Monthly outliers: robust z-score within district x item x FY (total column)
def robust_z(s):
    med = s.median()
    mad = (s - med).abs().median() * 1.4826
    return (s - med) / mad if mad and mad > 0 else s * 0
tot = tot.copy()
tot["rz"] = tot.groupby(["fy", "district_38", "item"])["value"].transform(robust_z)
out = tot[(tot.rz.abs() > 3.5) & tot.value.notna()]
out[["fy", "period", "district_38", "item", "value", "rz"]].sort_values("rz").to_csv(
    PROC / "dq_monthly_outliers.csv", index=False)

# ----------------------------------------------------------------------------------------
# 4. Indicators
# ----------------------------------------------------------------------------------------
def build(df):
    w = df.pivot_table(index=df.index.names if df.index.nlevels > 1 else None, columns="item",
                       values="value", aggfunc="sum")
    return w

def indicators(w: pd.DataFrame) -> pd.DataFrame:
    w = w.copy()
    w["deliveries_reported"] = w["inst_deliveries"] + w["home_del_sba"] + w["home_del_nonsba"]
    w["live_births"] = w["live_birth_m"] + w["live_birth_f"]
    w["fic"] = w["fic_m"] + w["fic_f"]
    o = pd.DataFrame(index=w.index)
    o["inst_births"] = 100 * w["inst_deliveries"] / w["deliveries_reported"]
    o["anc4"] = 100 * w["anc4_received"] / w["anc_registered"]
    o["anc_1st_trimester"] = 100 * w["anc_reg_1st_tri"] / w["anc_registered"]
    o["full_imm"] = 100 * w["fic"] / w["live_births"]
    o["csection"] = 100 * w["csections"] / w["inst_deliveries"]
    o["penta3"] = 100 * w["penta3"] / w["live_births"]
    o["mcv1"] = 100 * w["mcv1"] / w["live_births"]
    o["imm_session_held"] = 100 * w["imm_sessions_held"] / w["imm_sessions_planned"]
    o["lb_per_delivery"] = w["live_births"] / w["deliveries_reported"]
    for c in ["anc_registered", "inst_deliveries", "deliveries_reported", "live_births", "fic", "csections"]:
        o["n_" + c] = w[c]
    return o

def private_share(df):
    p = df[df.item == "inst_deliveries"].pivot_table(index=[c for c in df.columns if c in ("fy", "frame_district")],
                                                     columns="sector", values="value", aggfunc="sum")
    return 100 * p["private"].fillna(0) / p["total"]

frames = []
for frame, col in [("38", "district_38"), ("32", "district_nfhs32")]:
    d = h[(h.period == "FY")].rename(columns={col: "frame_district"})
    d = d[(d.frame_district != "STATE") | (d.district_raw == "Tamil Nadu")]
    t = d[d.sector == "total"]
    w = t.pivot_table(index=["fy", "frame_district"], columns="item", values="value", aggfunc="sum")
    ind = indicators(w)
    ind["inst_births_private"] = private_share(d)
    ind = ind.reset_index()
    ind.insert(0, "frame", frame)
    frames.append(ind)
ind_fy = pd.concat(frames, ignore_index=True)
ind_fy.loc[ind_fy.frame_district == "STATE", "frame_district"] = "Tamil Nadu (state)"
ind_fy.to_csv(PROC / "hmis_indicators_fy.csv", index=False)

# monthly indicators, 38-district frame as reported (+ state)
m = h[(h.period != "FY") & (h.sector == "total")].copy()
m["frame_district"] = np.where(m.district_raw == "Tamil Nadu", "Tamil Nadu (state)", m.district_38)
m = m[~((m.district_38 == "STATE") & (m.district_raw != "Tamil Nadu"))]
wm = m.pivot_table(index=["fy", "period", "month_start", "frame_district"], columns="item", values="value", aggfunc="sum")
ind_m = indicators(wm).reset_index()
ind_m.to_csv(PROC / "hmis_indicators_monthly.csv", index=False)

# logical-consistency flags at FY level (38 frame + 32 frame)
chk = ind_fy.copy()
chk["flag_anc4_gt_reg"] = chk["anc4"] > 100
chk["flag_fic_gt_lb"] = chk["full_imm"] > 100
chk["flag_lb_vs_deliv"] = (chk["lb_per_delivery"] < 0.95) | (chk["lb_per_delivery"] > 1.05)
chk.to_csv(PROC / "dq_logic_flags.csv", index=False)

print("NFHS", nfhs_w.shape, "| HMIS FY indicators", ind_fy.shape, "| monthly", ind_m.shape)
print(ind_fy[ind_fy.frame == "32"].groupby("fy")[["inst_births", "anc4", "anc_1st_trimester", "full_imm", "csection",
                                                   "inst_births_private"]].describe().T.round(1).to_string())
