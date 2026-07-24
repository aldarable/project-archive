"""
config.py for Central configuration for the Project Monitoring Dashboard.

"""

from __future__ import annotations
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


# Top bar for projects & chapters (per project scope)
PROJECTS: list[str] = ["JK5DH3", "JK6DH3", "JK7", "JK8", "H301", "H302", "GIS"]
ACTIVE_PROJECTS: set[str] = {"JK7"}  

CHAPTERS: dict[str, str] = {
    "1": "S-Curve",
    "2": "HSE Manpower",
    "3": "Document Control",
    "4": "HSE Safety",
    "5": "Equipment",
}
ACTIVE_CHAPTERS: set[str] = {"1", "2", "3"}  


# Local data paths (per project). Only JK7 is populated for now.
def project_dir(project: str) -> Path:
    return DATA_DIR / project.lower()


# Chapter 1 — S-Curve 
CSV_SCURVE_MAIN = "scurve_main.csv"
CSV_SCURVE_WORKBREAKDOWN = "scurve_workbreakdown.csv"
JSON_SCURVE_META = "scurve_meta.json"


# Google Sheets
GSHEET_TABS: dict[str, str] = {
    "2": "HSE_Manpower",
    "3": "Document_Control",
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
