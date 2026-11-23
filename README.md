# Tamil Nadu MCH: HMIS data quality & triangulation with NFHS-5

CEGIS analytical assignment, District Data Analyst (Tiruchirappalli).

| Deliverable | Where |
|---|---|
| Report (4 pages) | `report/CEGIS_Trichy_Assignment_Report.pdf` (editable: `.docx`) |
| Slides (11) | `report/CEGIS_Trichy_Assignment_Slides.pptx` (+ `.pdf`) |
| Live dashboard | **https://hmis-dashboard-23pwg7jrxhautuh6wbjhba.streamlit.app/** (source: `dashboard/app.py`) |
| Code | `code/00`–`05` (run in order) |
| AI-use note | `AI_use_note.md` |

## Data sources
- **HMIS** (MoHFW), hmis.mohfw.gov.in → Standard Reports → *C2. Data Itemwise Monthly (up to sub district) → 2. All States Across Districts* → Tamil Nadu. FY 2018-19 and 2019-20 (monthly + annual) and FY 2020-21 (cumulative-to-month files, marked provisional). The portal lists later years only to logged-in users, so 2020-21 is the latest public year. The pipeline accepts newer files in the same format.
- **NFHS-5** district factsheets (2019-21), 707-district table (same layout as data.gov.in resource *India Districts Factsheets - NFHS-5*). TN has 32 districts. In this file, bracketed factsheet values (25–49 unweighted cases) are stored as **negative numbers**; `*` = suppressed (<25 cases). The code flags both.

## Reproduce
```bash
pip install -r requirements.txt
python code/00_download_data.py      # ~260 MB download; keeps only Tamil Nadu files
python code/01_ingest_hmis.py        # SAS-HTML .xls and .xlsx -> data/processed/hmis_long.csv
python code/02_build_indicators.py   # NFHS cleaning, district crosswalk, HMIS indicators, data-quality tables
python code/03_analysis.py           # triangulation, drivers, figures, dashboard data
python code/04_make_report.py        # report/CEGIS_Trichy_Assignment_Report.docx
python code/05_slide_data.py && node code/05_make_slides.js   # slide deck (needs: npm install pptxgenjs)
streamlit run dashboard/app.py       # dashboard locally
```
Or `bash run_all.sh`. Python 3.10+.

## Key method choices
- **District frames.** `data/district_crosswalk.csv` maps every HMIS spelling to (a) the current 38 districts and (b) the 32 NFHS-5 districts. New districts (Chengalpattu, Kallakurichi, Ranipet, Tirupathur, Tenkasi, Mayiladuthurai) are **added back to their parent** for NFHS comparison. Counts aggregate exactly; survey percentages cannot be split.
- **2020-21 monthly values** = difference of consecutive cumulative files (the portal's month-wise 2020-21 files returned server errors).
- **Triangulation period.** HMIS Apr 2018–Mar 2020 pooled vs NFHS-5 (births in the 5 years before early-2020 fieldwork).
- **Full immunisation, resident denominator** (sensitivity). Fully-immunised children ÷ (previous FY's ANC registrations × state live-births-per-registration). Corrects for births being counted in the district where they occur.
- **NFHS-5 confidence intervals** are indicative only (n ≈ 25% of women interviewed for birth indicators; 37 for bracketed immunisation values, 65 otherwise; design effect 1.5).

## Deploy the dashboard (Streamlit Community Cloud, free)
1. Push this folder to a **public GitHub repo**. `.gitignore` excludes the raw data and the 470 MB `hmis_long.csv`; the dashboard only needs the small CSVs in `data/processed/`.
2. Go to share.streamlit.io → *New app* → pick the repo → main file `dashboard/app.py` → Deploy.
3. Paste the app URL into the report (section 5) and this README.

## Folder layout
```
code/            00-04 pipeline scripts
dashboard/app.py Streamlit app
data/raw/        downloaded files (not committed)
data/processed/  analysis tables (dashboard reads these)
data/district_crosswalk.csv
report/          report + figures
```
