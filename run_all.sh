#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python code/00_download_data.py
python code/01_ingest_hmis.py
python code/02_build_indicators.py
python code/03_analysis.py
python code/04_make_report.py
python code/05_slide_data.py && node code/05_make_slides.js
