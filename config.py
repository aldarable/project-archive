"""
config.py — Central configuration for the DCI Project Monitoring System.
"""

from __future__ import annotations
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

APP_TITLE = "DCI PROJECT MONITORING SYSTEM"
APP_VERSION = "v2.0.0"
LAST_UPDATED = "24 July 2026"
LOGO_PATH = ASSETS_DIR / "logo_dci.png"          # drop your DCI Indonesia logo here
PDF_REPORT_PATH = ASSETS_DIR / "report.pdf"       # drop the exported PDF report here


# Top bar — Project + Chapter
PROJECTS: list[str] = ["JK5", "JK6", "JK7", "JK8", "H301", "H302", "GIS"]
ACTIVE_PROJECTS: set[str] = {"JK7"}

CHAPTERS: dict[str, str] = {
    "1": "S-Curve",
    "2": "Manpower",
    "3": "Document",
    "4": "Safety",
    "5": "Equipment",
}
ACTIVE_CHAPTERS: set[str] = {"1", "2", "3", "4"}


def project_dir(project: str) -> Path:
    return DATA_DIR / project.lower()


# Google Sheet — single spreadsheet, one tab per project per chapter.
# Tab naming convention (matches the source workbook Project-Archive-3.xlsx):
#   <project>-scurve        Chapter 1 — daily zoning S-Curve (+ Zone/Kolom log)
#   <project>-sri-scurve    Chapter 1 — vendor (Sumaraja) weekly work-item S-Curve
#   <project>-manpower      Chapter 2 — HSE Manpower
#   <project>-docon         Chapter 3 — Document Control
#   <project>-hse-safety    Chapter 4 — HSE Safety
#   <project>-equipment     Chapter 5 — Equipment
def gsheet_tab(project: str, key: str) -> str:
    return f"{project.lower()}-{key}"


# Chapter 1 — S-Curve
SCURVE_MAIN_COLS = [
    "Date", "PlanZoning", "PlanCum", "PlanPct_%", "ActualZoning",
    "ActualCum", "ActualPct_%", "DevAbs_unit", "DevPct_%", "Remarks",
]
ZONE_KOLOM_COLS = ["Date Structure", "Level", "Metric", "Done", "Target"]
ZONE_LEVELS: list[str] = ["GF", "L1", "L2"]
ZONE_METRICS: list[str] = ["Zone", "Kolom"]

# Denah (floor plan) images per level/metric — set to None where not available yet.
DENAH_ASSETS: dict[str, dict[str, str | None]] = {
    "GF": {"Zone": "assets/denah_gf.jpeg", "Kolom": "assets/denah_kolom_gf.jpg"},
    "L1": {"Zone": "assets/denah_L1.jpg", "Kolom": "assets/denah_kolom_L1.jpg"},
    "L2": {"Zone": "assets/denah_L2.jpg", "Kolom": None},
}


# Chapter 2 — HSE Manpower
MANPOWER_SMALL = ["HSE", "K2", "Tim Baja", "Tim Bobok", "Tim Cor"]
MANPOWER_LARGE = ["Tim Besi", "Tim Begisting"]
MANPOWER_CATEGORIES = MANPOWER_SMALL + MANPOWER_LARGE

MANPOWER_COLORS = {
    "HSE": "#3B82F6",
    "K2": "#8B5CF6",
    "Tim Baja": "#EC4899",
    "Tim Bobok": "#F59E0B",
    "Tim Cor": "#10B981",
    "Tim Besi": "#0EA5E9",
    "Tim Begisting": "#F97316",
    "Total": "#6366F1",
    "Manhours": "#A855F7",
}


# Chapter 4 — HSE Safety
HSE_SAFETY_COLS = [
    "No", "Date", "Observation", "Assessment", "Risks", "Photos",
    "Rectification Evidence (Site Photos)", "Remarks", "Scope / Not Scope {DCI)", "Status",
]
HSE_STATUS_COLORS = {"Open": "#EF4444", "Close": "#10B981"}
HSE_ASSESSMENT_COLORS = {"Unacceptable": "#EF4444", "Need Improvements": "#F59E0B"}
HSE_RISK_COLORS = {"P0 - Significant Risks": "#EF4444", "P1 - Managable Risks": "#F59E0B"}


# Chapter 3 — Document Control
DOCON_FIELD_MAP = {
    "Total Deliverable": "Total Deliverables",
    "Submitted [Vendor]": "Submitted by Vendor",
    "Not Yet Review": "Pending (Not Yet Review)",
    "Overdue [Vendor Submit]": "Overdue",
    "Completed [PMO Review]": "Completed (PMO Review)",
    "In Progress [PMO Review]": "In Progress (PMO Review)",
    "Overdue [PMO Review]": "Overdue (PMO Review)",
    "(A)\nAPPROVED": "Approved",
    "(B) APPROVED\nW/ COMMENT": "Approved w/ Note",
    "(C)\nREJECTED": "Rejected",
    "(D) FOR INFO\nONLY": "For Information Only",
    "PENDING\nREVIEW": "In Review",
}
DOCON_TOTAL_ROW_LABEL = "TOTAL"

DOCON_OVERALL_FIELDS = [
    "Total Deliverable", "Submitted [Vendor]", "Not Yet Review", "Overdue [Vendor Submit]",
    "(A)\nAPPROVED", "(B) APPROVED\nW/ COMMENT", "(C)\nREJECTED",
    "(D) FOR INFO\nONLY", "PENDING\nREVIEW",
]
DOCON_VENDOR_FIELDS = ["Total Deliverable", "Submitted [Vendor]", "Not Yet Review", "Overdue [Vendor Submit]"]
DOCON_PMO_FIELDS = ["Submitted [Vendor]", "Completed [PMO Review]", "In Progress [PMO Review]", "Overdue [PMO Review]"]

COLORS = {
    "plan": "#3B82F6",
    "actual": "#F5B942",
    "deviation": "#EF4444",
    "on_track": "#10B981",
    "purple": "#8B5CF6",
    "pink": "#EC4899",
    "teal": "#14B8A6",
    "grid": "rgba(128,128,128,0.18)",
    "text": "#8A8A9A",
}

CATEGORICAL_PALETTE = [
    "#3B82F6", "#8B5CF6", "#EC4899", "#F59E0B",
    "#10B981", "#14B8A6", "#EF4444", "#6366F1", "#F97316",
]

CACHE_TTL_SECONDS = 60
