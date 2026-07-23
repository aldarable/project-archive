"""
services/sheets.py — Data access layer.

Design goal (per project requirement): Google Sheets is the single source of
truth in production. Both the dashboard and direct edits in Google Sheets
write to / are read from the exact same spreadsheet, so either path updates
what everyone sees.

- Development mode (config.DATA_MODE == "csv"): reads/writes bundled CSV
  files under data/. Used ONLY for local testing without live credentials.
- Production mode (config.DATA_MODE == "gsheets"): every read hits the sheet
  through a short-TTL cache (so direct edits in Google Sheets show up within
  CACHE_TTL_SECONDS without a code change), and every write goes straight to
  the sheet followed by an explicit cache clear (so dashboard edits are
  visible immediately, not just after the TTL expires).

The scurve-jk7 tab is a special case: it holds TWO independent tables
side-by-side (main S-curve in columns A:J, zone/kolom progress in columns
K:O). We read it with raw values and split by column range rather than
gspread's get_all_records(), which assumes one table per sheet.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import streamlit as st

import config
from auth import get_gspread_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level worksheet access (gsheets mode)
# ---------------------------------------------------------------------------

def _get_worksheet(tab_name: str):
    client = get_gspread_client()
    if client is None:
        raise RuntimeError("Google Sheets client is not configured (missing service account secret).")
    spreadsheet = client.open_by_key(config.SHEET_ID)
    return spreadsheet.worksheet(tab_name)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def _read_raw_values(tab_name: str) -> list[list[Any]]:
    """Read all raw cell values from a worksheet tab. Cached with a short TTL
    so direct edits made in Google Sheets are picked up automatically."""
    ws = _get_worksheet(tab_name)
    return ws.get_all_values()


def _rows_to_dataframe(rows: list[list[Any]], col_start: int = 0, col_end: int | None = None) -> pd.DataFrame:
    """Build a DataFrame from raw sheet rows, restricted to a column slice.
    First row of the slice is treated as the header."""
    if not rows:
        return pd.DataFrame()
    sliced = [row[col_start:col_end] for row in rows]
    header = [str(h).strip() for h in sliced[0]]
    data_rows = sliced[1:]
    # Pad/truncate each row to header length (sheets often return ragged rows)
    fixed_rows = []
    for r in data_rows:
        r = list(r) + [""] * (len(header) - len(r)) if len(r) < len(header) else r[: len(header)]
        fixed_rows.append(r)
    df = pd.DataFrame(fixed_rows, columns=header)
    # Drop fully-empty rows (common at the tail of a sheet range)
    df = df[~(df.apply(lambda row: all(str(v).strip() == "" for v in row), axis=1))]
    return df.reset_index(drop=True)


def clear_cache() -> None:
    """Clear all cached reads. Call after any write so the dashboard reflects
    the change immediately, without waiting for the TTL to expire."""
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Chapter 1 — S-Curve (main table + zone/kolom table share one tab)
# ---------------------------------------------------------------------------

def load_scurve_main() -> pd.DataFrame:
    if config.DATA_MODE == "gsheets":
        rows = _read_raw_values(config.TAB_SCURVE)
        df = _rows_to_dataframe(rows, *config.SCURVE_MAIN_COLS)
    else:
        df = pd.read_csv(config.CSV_SCURVE_MAIN)
    return _clean_scurve_main(df)


def _clean_scurve_main(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    required = ["Date", "PlanPct_%", "ActualPct_%", "DevPct_%", "Remarks"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required columns missing from the S-Curve data: {missing}. "
            f"Columns found: {list(df.columns)}"
        )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["PlanZoning", "PlanCum", "PlanPct_%", "ActualZoning", "ActualCum", "ActualPct_%", "DevAbs_unit", "DevPct_%"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].replace("", pd.NA), errors="coerce")
    df["Remarks"] = df["Remarks"].fillna("").astype(str)
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    return df


def load_scurve_zone() -> pd.DataFrame:
    if config.DATA_MODE == "gsheets":
        rows = _read_raw_values(config.TAB_SCURVE)
        df = _rows_to_dataframe(rows, *config.SCURVE_ZONE_COLS)
    else:
        df = pd.read_csv(config.CSV_SCURVE_ZONE)
    return _clean_scurve_zone(df)


def _clean_scurve_zone(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]  # handles the "Date " trailing-space header
    required = ["Date", "Level", "Metric", "Done", "Target"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required columns missing from the zone/kolom data: {missing}. "
            f"Columns found: {list(df.columns)}"
        )
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Done"] = pd.to_numeric(df["Done"], errors="coerce").fillna(0)
    df["Target"] = pd.to_numeric(df["Target"], errors="coerce").fillna(0)
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    return df


def update_scurve_actual(target_date: str, qty: float, remarks: str) -> tuple[bool, str]:
    """Update ActualZoning & Remarks for a given date in the main S-curve table
    (columns A:J of the scurve-jk7 tab). Plan/Deviation columns are left
    untouched — Deviation is maintained manually by the user in the sheet."""
    if config.DATA_MODE != "gsheets":
        return False, "Writing is only available in production (Google Sheets) mode."
    try:
        ws = _get_worksheet(config.TAB_SCURVE)
        col_start, col_end = config.SCURVE_MAIN_COLS
        header = ws.row_values(1)[col_start:col_end]
        dates = ws.col_values(col_start + 1)  # column A of the main table (1-indexed)
        try:
            row_idx = dates.index(target_date) + 1
        except ValueError:
            return False, "The specified date was not found in the sheet. Use YYYY-MM-DD format."
        col_actual = col_start + header.index("ActualZoning") + 1
        col_remarks = col_start + header.index("Remarks") + 1
        ws.update_cell(row_idx, col_actual, qty)
        if remarks:
            ws.update_cell(row_idx, col_remarks, remarks)
        clear_cache()
        return True, "Successfully updated in Google Sheets."
    except Exception as e:
        logger.exception("Failed to update S-curve actual value.")
        return False, f"Update failed: {e}"


def append_zone_progress(date_str: str, level: str, metric: str, done: int, target: int) -> tuple[bool, str]:
    """Append a new snapshot row into the zone/kolom table (columns K:O of the
    scurve-jk7 tab) without disturbing the main S-curve table in columns A:J."""
    if config.DATA_MODE != "gsheets":
        return False, "Writing is only available in production (Google Sheets) mode."
    try:
        ws = _get_worksheet(config.TAB_SCURVE)
        col_start, col_end = config.SCURVE_ZONE_COLS
        all_values = ws.get_all_values()
        # Find first fully-empty row within the zone column range to write into
        next_row = None
        for i, row in enumerate(all_values[1:], start=2):
            zone_slice = row[col_start:col_end] if len(row) > col_start else []
            if not any(str(v).strip() for v in zone_slice):
                next_row = i
                break
        if next_row is None:
            next_row = len(all_values) + 1

        from gspread.utils import rowcol_to_a1
        start_cell = rowcol_to_a1(next_row, col_start + 1)
        end_cell = rowcol_to_a1(next_row, col_start + 5)
        ws.update(f"{start_cell}:{end_cell}", [[date_str, level, metric, done, target]])
        clear_cache()
        return True, "Progress saved to Google Sheets."
    except Exception as e:
        logger.exception("Failed to append zone progress.")
        return False, f"Save failed: {e}"


# ---------------------------------------------------------------------------
# Chapter 2 — HSE Manpower
# ---------------------------------------------------------------------------

def load_manpower() -> pd.DataFrame:
    if config.DATA_MODE == "gsheets":
        rows = _read_raw_values(config.TAB_MANPOWER)
        df = _rows_to_dataframe(rows)
    else:
        df = pd.read_csv(config.CSV_MANPOWER)
    return _clean_manpower(df)


def _clean_manpower(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if "Date" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"Date": "date"})
    required = ["date", "Total", "Manhours", *config.MANPOWER_CATEGORIES]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"Required columns missing from HSE Manpower data: {missing}. "
            f"Columns found: {list(df.columns)}"
        )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in [*config.MANPOWER_CATEGORIES, "Total", "Manhours"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset="date", keep="last").reset_index(drop=True)
    return df


def upsert_manpower_row(df: pd.DataFrame, row_date, values: dict) -> pd.DataFrame:
    """Insert or update one day's manpower figures in-memory. Caller is
    responsible for persisting via save_manpower()."""
    row_date = pd.Timestamp(row_date)
    df = df.copy()
    mask = df["date"] == row_date
    if mask.any():
        for k, v in values.items():
            df.loc[mask, k] = v
    else:
        new_row = {"date": row_date, **values}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df["Total"] = df[config.MANPOWER_CATEGORIES].sum(axis=1)
    if "Manhours" not in values:
        # Preserve existing manhours if untouched; else default to Total x 16
        # ONLY as a last-resort fallback for brand-new rows (production sheets
        # should already carry their own Manhours value).
        df["Manhours"] = df["Manhours"].where(df["Manhours"] > 0, df["Total"] * 16)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def save_manpower(df: pd.DataFrame) -> tuple[bool, str]:
    try:
        out = df[["date", *config.MANPOWER_CATEGORIES, "Total", "Manhours"]].copy()
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        if config.DATA_MODE == "gsheets":
            from gspread_dataframe import set_with_dataframe
            ws = _get_worksheet(config.TAB_MANPOWER)
            ws.clear()
            out.insert(0, "No", range(1, len(out) + 1))
            set_with_dataframe(ws, out)
        else:
            out.to_csv(config.CSV_MANPOWER, index=False)
        clear_cache()
        return True, "Manpower data saved."
    except Exception as e:
        logger.exception("Failed to save manpower data.")
        return False, f"Save failed: {e}"


# ---------------------------------------------------------------------------
# Chapter 3 — Document Control
# ---------------------------------------------------------------------------

def load_docon() -> pd.DataFrame:
    if config.DATA_MODE == "gsheets":
        rows = _read_raw_values(config.TAB_DOCON)
        df = _rows_to_dataframe(rows)
    else:
        df = pd.read_csv(config.CSV_DOCON)
    return _clean_docon(df)


def _clean_docon(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if "VENDOR" not in df.columns:
        raise ValueError(f"'VENDOR' column missing from Document Control data. Columns found: {list(df.columns)}")
    numeric_cols = [c for c in df.columns if c != "VENDOR"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # Drop the sheet's own pre-computed TOTAL row; the app recomputes totals
    # itself so they stay correct even if vendors are added/removed.
    df = df[df["VENDOR"].str.upper() != config.DOCON_TOTAL_ROW_LABEL].reset_index(drop=True)
    return df
