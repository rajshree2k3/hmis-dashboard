"""
00_download_data.py - fetch the raw public data used in this project.

HMIS (hmis.mohfw.gov.in -> Standard Reports -> C2. Data Itemwise Monthly (up to sub district)
      -> 2. All States Across Districts). Only folders the portal lists publicly (no login) are used:
      FY 2018-19 and 2019-20 as all-India zips (Tamil Nadu files extracted, zips deleted),
      FY 2020-21 as Tamil Nadu cumulative 'UpTo_<month>' files.
NFHS-5 district factsheet table (707 districts; same layout as the data.gov.in resource
      'India Districts Factsheets - NFHS-5 2019-2021'), via a public GitHub mirror.
"""
import io
import urllib.parse
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
HM = RAW / "hmis"
HM.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research download)"}
BASE = "Standard Reports/5~C2. Data Itemwise Monthly (up to sub district)/2. All States Across Districts"


def hmis_get(path: str) -> bytes:
    # The portal expects the path URI-encoded like JavaScript encodeURI, without a leading slash
    q = urllib.parse.quote(path, safe="-_.!~*'();/?:@=+$,#")
    r = requests.get(f"https://hmis.mohfw.gov.in/downloadfiles?filepath={q}", headers=UA, timeout=900)
    r.raise_for_status()
    return r.content


# NFHS-5
nfhs = RAW / "nfhs5_districts_707.csv"
if not nfhs.exists():
    url = ("https://raw.githubusercontent.com/manya2731/nfhs5-institutional-delivery-prediction/"
           "HEAD/nfhs5_district_factsheet_raw.csv")
    nfhs.write_bytes(requests.get(url, timeout=120).content)
    print("NFHS-5 saved")

# HMIS 2018-19, 2019-20 (all-India zip -> keep Tamil Nadu monthly files + March cumulative)
for fy, folder in [("2018-19", "2018-2019"), ("2019-20", "2019-2020")]:
    if list(HM.glob(f"TN_{fy}_monthly_*.xls")):
        continue
    z = zipfile.ZipFile(io.BytesIO(hmis_get(f"{BASE}/{folder}.zip")))
    for n in z.namelist():
        if "/Tamil Nadu/" in n and not n.endswith("/"):
            kind = "monthly" if "Monthwise" in n else "cumulative"
            if kind == "cumulative" and "March" not in n:
                continue
            (HM / f"TN_{fy}_{kind}_{n.split('/')[-1].split('_')[-1]}").write_bytes(z.read(n))
    print("HMIS", fy, "saved")

# HMIS 2020-21 cumulative-to-month files (monthly values are derived by differencing in 01_ingest)
letters = "ABCDEFGHIJKL"
months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
for L, m in zip(letters, months):
    out = HM / f"TN_2020-21_cumupto_{m}.xlsx"
    if not out.exists():
        out.write_bytes(hmis_get(f"{BASE}/2020-2021(Data is Provisional)/B.Cummulative/Tamil Nadu/{L}-Tamil Nadu_UpTo_{m}.xlsx"))
        print("HMIS 2020-21 up to", m, "saved")
print("done")
