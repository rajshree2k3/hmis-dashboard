"""
01_ingest_hmis.py
Parse the HMIS "Data Itemwise Monthly - All States Across Districts" reports for Tamil Nadu
into a single tidy (long) table.

Inputs  (data/raw/hmis/):
  TN_2018-19_monthly_<Month>.xls, TN_2019-20_monthly_<Month>.xls   (SAS HTML disguised as .xls)
  TN_2018-19_cumulative_March.xls, TN_2019-20_cumulative_March.xls (FY totals)
  TN_2020-21_cumupto_<Mon>.xlsx  (cumulative Apr..Mon; monthly values derived by differencing)
Output  (data/processed/):
  hmis_long.csv  columns: fy, period, month_start, district_raw, item_code, item_name, sector, value
     period = 'FY' for full-year cumulative, otherwise 3-letter month
"""
import re
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "hmis"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
SECTOR_MAP = {"Total": "total", "Public": "public", "Private": "private", "Urban": "urban", "Rural": "rural"}


def _sector(label: str) -> str:
    for k, v in SECTOR_MAP.items():
        if str(label).startswith(k):
            return v
    raise ValueError(label)


def _clean_code(c) -> str:
    return str(c).strip().strip("'").strip()


def parse_html_xls(path: Path) -> pd.DataFrame:
    """SAS HTML export (2018-19, 2019-20). 3-row column header: 'District' / district / sector."""
    t = pd.read_html(path, encoding="windows-1252")[0]
    meta = t.iloc[:, :4].copy()
    meta.columns = ["section", "item_code", "item_name", "item_type"]
    recs = []
    for col in t.columns[4:]:
        district, sector = col[1], _sector(col[2])
        s = pd.to_numeric(t[col], errors="coerce")
        recs.append(meta.assign(district_raw=district, sector=sector, value=s.values))
    df = pd.concat(recs, ignore_index=True)
    return df


def parse_xlsx(path: Path) -> pd.DataFrame:
    """Excel export (2020-21). Row 6 = district names (every 5 cols), row 7 = sector, data from row 8."""
    x = pd.read_excel(path, header=None)
    hdr_row = None
    for i in range(15):
        if str(x.iloc[i, 4]).startswith("Total"):
            hdr_row = i
            break
    dist_row = hdr_row - 1
    data = x.iloc[hdr_row + 1:].reset_index(drop=True)
    meta = data.iloc[:, :4].copy()
    meta.columns = ["section", "item_code", "item_name", "item_type"]
    recs = []
    district = None
    for j in range(4, x.shape[1]):
        d = x.iloc[dist_row, j]
        if pd.notna(d):
            district = str(d)
        sector = _sector(x.iloc[hdr_row, j])
        s = pd.to_numeric(data.iloc[:, j], errors="coerce")
        recs.append(meta.assign(district_raw=district, sector=sector, value=s.values))
    return pd.concat(recs, ignore_index=True)


def tidy(df: pd.DataFrame, fy: str, period: str) -> pd.DataFrame:
    df = df.copy()
    df["item_code"] = df["item_code"].map(_clean_code)
    df["district_raw"] = df["district_raw"].astype(str).str.strip().str.lstrip("_")
    df = df[df["item_code"].str.match(r"^\d")]          # drop blank / footer rows
    df.insert(0, "fy", fy)
    df.insert(1, "period", period)
    return df[["fy", "period", "district_raw", "section", "item_code", "item_name", "item_type", "sector", "value"]]


def month_start(fy: str, period: str):
    if period == "FY":
        return pd.NaT
    y0 = int(fy[:4])
    m = MONTHS.index(period)
    year = y0 if m < 9 else y0 + 1
    return pd.Timestamp(year=year, month=(m + 3) % 12 + 1, day=1)


frames = []
# --- 2018-19 and 2019-20: native monthly + FY cumulative ---------------------------------
full_names = {"April": "Apr", "May": "May", "June": "Jun", "July": "Jul", "August": "Aug", "September": "Sep",
              "October": "Oct", "November": "Nov", "December": "Dec", "January": "Jan", "February": "Feb", "March": "Mar"}
for fy in ["2018-19", "2019-20"]:
    for f in sorted(RAW.glob(f"TN_{fy}_monthly_*.xls")):
        mon = full_names[f.stem.split("_")[-1]]
        frames.append(tidy(parse_html_xls(f), fy, mon))
        print("parsed", f.name)
    frames.append(tidy(parse_html_xls(RAW / f"TN_{fy}_cumulative_March.xls"), fy, "FY"))

# --- 2020-21: cumulative-to-month files -> monthly by differencing ----------------------
cum = {}
for mon in MONTHS:
    f = RAW / f"TN_2020-21_cumupto_{mon}.xlsx"
    cum[mon] = tidy(parse_xlsx(f), "2020-21", mon)
    print("parsed", f.name)
key = ["district_raw", "section", "item_code", "item_name", "item_type", "sector"]
prev = None
for mon in MONTHS:
    cur = cum[mon].set_index(key)["value"]
    cur = cur[~cur.index.duplicated()]
    if prev is None:
        monthly = cur
    else:
        # missing in an earlier cumulative = 0 so far; in the HMIS export blank means "no report"
        monthly = cur.sub(prev.reindex(cur.index).fillna(0), fill_value=0)
        monthly[cur.isna()] = pd.NA
    prev = cur
    m = monthly.rename("value").reset_index()
    m.insert(0, "fy", "2020-21")
    m.insert(1, "period", mon)
    frames.append(m[cum[mon].columns])
fy2021 = cum["Mar"].copy()
fy2021["period"] = "FY"
frames.append(fy2021)

hmis = pd.concat(frames, ignore_index=True)
hmis["month_start"] = [month_start(a, b) for a, b in zip(hmis["fy"], hmis["period"])]
hmis.to_csv(OUT / "hmis_long.csv", index=False)
print(hmis.shape)
print(hmis.groupby("fy")["district_raw"].nunique())
