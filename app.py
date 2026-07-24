"""
config.py — Central configuration for the DCI Project Monitoring System.
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import subprocess

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

APP_TITLE = "DCI PROJECT MONITORING SYSTEM"
APP_VERSION = "v2.0.0"

LOGO_PATH = ASSETS_DIR / "logo_dci.png"     # DCI logo
REPORT_FILENAME = "DCI_Project_Report.pdf"  # Download filename


def get_last_code_update() -> str:
    """Latest Git commit date."""
    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=format:%d %b %Y"],
            text=True,
        ).strip()
    except Exception:
        return datetime.now().strftime("%d %b %Y")


LAST_CODE_UPDATE = get_last_code_update()
LAST_DATA_UPDATE = "-"  # Filled from Google Sheets
