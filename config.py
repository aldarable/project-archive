"""
config.py — Central configuration for the JK7 Monitoring Dashboard.

Single place to control:
- Data source mode (csv vs gsheets)
- The one Google Spreadsheet ID and its worksheet/tab names
- Shared constants (categories, colors, file paths)

Switching from CSV (development) to Google Sheets (production) requires no
code changes elsewhere in the app — only `st.secrets` needs to be populated
(see auth.py / services/sheets.py for how the switch is detected).
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def _has_secret(key: str) -> bool:
    """Safely check for a secret's presence. st.secrets raises
    StreamlitSecretNotFoundError (not just an empty mapping) when no
    secrets.toml exists at all, so a plain `in` check isn't safe on fresh
    development installs -- this guards against that."""
    try:
        return key in st.secrets
    except Exception:
        return False


def _get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Data source mode
# ---------------------------------------------------------------------------
# "gsheets" is used automatically whenever a valid service-account secret is
# present (production). Otherwise the app falls back to bundled CSV files
# under DATA_DIR (development / local testing only, per project requirements).
DATA_MODE: str = "gsheets" if _has_secret("gcp_service_account") else "csv"

# ---------------------------------------------------------------------------
# Google Sheets -- ONE spreadsheet, multiple tabs (one per chapter)
# ---------------------------------------------------------------------------
SHEET_ID: str = _get_secret("sheet_id", "")

TAB_SCURVE = "scurve-jk7"          # Chapter 1 — contains BOTH the daily S-curve
                                     # table (cols A-J) and the zone/kolom progress
                                     # table (cols K-O) side by side in one tab.
TAB_MANPOWER = "hse-manpower"       # Chapter 2
TAB_DOCON = "docon-jk7"             # Chapter 3
TAB_HSE_SAFETY = "hse-safety"       # Chapter 4 (placeholder, no data yet)
TAB_EQUIPMENT = "equipment-jk7"     # Chapter 5 (placeholder, no data yet)

# Column ranges within the scurve-jk7 tab (0-indexed, half-open) used to split
# the two side-by-side tables when reading raw sheet values.
SCURVE_MAIN_COLS = (0, 10)   # A:J -> Date..Remarks
SCURVE_ZONE_COLS = (10, 15)  # K:O -> "Date " (note trailing space), Level, Metric, Done, Target

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CSS_PATH = BASE_DIR / "css" / "style.css"

CSV_SCURVE_MAIN = DATA_DIR / "scurve_main.csv"
CSV_SCURVE_ZONE = DATA_DIR / "scurve_zone_status.csv"
CSV_MANPOWER = DATA_DIR / "hse_manpower.csv"
CSV_DOCON = DATA_DIR / "docon_jk7.csv"

# ---------------------------------------------------------------------------
# Chapter 2 — HSE Manpower categories & chart colors (soft palette)
# ---------------------------------------------------------------------------
MANPOWER_CATEGORIES = ["HSE", "K2", "Tim Besi", "Tim Baja", "Tim Begisting", "Tim Bobok", "Tim Cor"]

MANPOWER_COLORS = {
    "HSE": "#7EA6E0",
    "K2": "#8FD3C7",
    "Tim Besi": "#F09AC1",
    "Tim Baja": "#F6B26B",
    "Tim Begisting": "#B39DDB",
    "Tim Bobok": "#F2836B",
    "Tim Cor": "#6FCF97",
    "Total": "#7C6FE0",
    "Manhours": "#B693D6",
}

# Manhours are a stored, manually-maintained column in the sheet
# (historically Manhours = Total x 16), never recomputed by the app.
MANHOURS_MULTIPLIER_NOTE = "Manhours is read directly from the sheet's own 'Manhours' column."

# ---------------------------------------------------------------------------
# Chapter 3 — Document Control field mapping (sheet column -> display label)
# ---------------------------------------------------------------------------
DOCON_FIELD_MAP = {
    "Total Deliverable": "Total Deliverables",
    "Submitted [Vendor]": "Submitted by Vendor",
    "Not Yet Review": "Not Yet Review",
    "Overdue [Vendor Submit]": "Vendor Overdue",
    "Completed [PMO Review]": "Completed PMO Review",
    "In Progress [PMO Review]": "In Progress PMO Review",
    "Overdue [PMO Review]": "Overdue PMO Review",
    "(A)\nAPPROVED": "A - Approved",
    "(B) APPROVED\nW/ COMMENT": "B - Approved w/ Note",
    "(C)\nREJECTED": "C - Rejected",
    "(D) FOR INFO\nONLY": "D - Information Only",
    "PENDING\nREVIEW": "In Review",
}
DOCON_TOTAL_ROW_LABEL = "TOTAL"

# ---------------------------------------------------------------------------
# Theme tokens (kept here so services/charts.py can share the same palette)
# ---------------------------------------------------------------------------
THEME = {
    "bg": "#F9F8FC",
    "card_bg": "#FFFFFF",
    "ink": "#2C2A3A",
    "muted": "#8A8798",
    "pink": "#F0A6C6",
    "purple": "#B39DDB",
    "blue": "#8FB8E8",
    "green": "#7FD6A0",
    "amber": "#F2C26B",
    "red": "#F2836B",
}

CACHE_TTL_SECONDS = 30
