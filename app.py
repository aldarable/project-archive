"""
app.py — JK7 Monitoring Dashboard entry point.

Responsible ONLY for page config, theme injection, and sidebar navigation /
routing. All chapter logic lives in pages/*.py, all data access in
services/sheets.py, keeping this file thin per the project's modularity goal.
"""

from __future__ import annotations

import streamlit as st

import config
from utils import load_css

st.set_page_config(
    page_title="Dashboard Monitoring JK7",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css(config.CSS_PATH)

CHAPTERS = {
    "Chapter 1 — S-Curve & Zone Status": "chapter1_scurve",
    "Chapter 2 — HSE Manpower": "chapter2_hse",
    "Chapter 3 — Document Control": "chapter3_docon",
    "Chapter 4 — HSE Safety (Coming Soon)": "chapter4_hse_safety",
    "Chapter 5 — Equipment Monitoring (Coming Soon)": "chapter5_equipment",
}

with st.sidebar:
    st.markdown("## 📊 Dashboard Monitoring JK7")
    st.caption(f"Data source: {'Google Sheets (production)' if config.DATA_MODE == 'gsheets' else 'CSV (development/testing)'}")
    st.divider()
    selection = st.radio("Navigate", list(CHAPTERS.keys()), label_visibility="collapsed")

module_name = CHAPTERS[selection]

if module_name == "chapter1_scurve":
    from pages.chapter1_scurve import render
elif module_name == "chapter2_hse":
    from pages.chapter2_hse import render
elif module_name == "chapter3_docon":
    from pages.chapter3_docon import render
elif module_name == "chapter4_hse_safety":
    from pages.chapter4_hse_safety import render
else:
    from pages.chapter5_equipment import render

render()
