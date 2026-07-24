"""
services/data_loader.py — Data access layer. Everything now lives in one
Google Sheet (mirrors Project-Archive-3.xlsx), read/written through
services.gsheet_client.
"""

from __future__ import annotations
from datetime import date, datetime
import numpy as np
import pandas as pd
import streamlit as st
import config
from services import gsheet_client as gs


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("", np.nan), errors="coerce")


def _fix_pct_scale_glitches(series: pd.Series) -> pd.Series:
    """Fix cumulative %-complete values that land ~100x too small.

    `PlanPct_%` / `ActualPct_%` are read with `UNFORMATTED_VALUE`, which
    returns a cell's *underlying* stored number, not what's displayed. Most
    rows are plain Number cells (e.g. 41.04 stored as 41.04), but if a cell
    (or a run of cells) has Percent number-format applied instead, Sheets
    stores it as a fraction (0.4104) even though it still *displays* as
    "41.04%" — so the app reads 0.41 instead of 41.04. This one format
    mismatch on a handful of rows in the sheet is the actual cause of
    "Actual" reading e.g. 0.42% when the real cumulative value is 41.04%.

    Since these columns are running cumulative totals, they should trend
    upward and stay on a 0-100 scale. A run of values that suddenly drops
    to ~1/100th of the running high-water mark - and would land back above
    it once scaled by 100 - is that formatting glitch, not real data. Fix
    those in place; genuinely small values early in the series (before any
    high-water mark is established) are left untouched.
    """
    arr = series.to_numpy(dtype=float)
    out = arr.copy()
    running_max = 0.0
    for i, v in enumerate(arr):
        if np.isnan(v):
            continue
        if running_max > 1 and 0 < v < (running_max / 10):
            scaled = v * 100
            out[i] = scaled
            running_max = max(running_max, scaled)
        else:
            running_max = max(running_max, v)
    return pd.Series(out, index=series.index)


def _parse_sheet_date(series: pd.Series) -> pd.Series:
    """Parse a raw date column coming from Google Sheets.

    `gsheet_client.read_tab` reads cells with `UNFORMATTED_VALUE`, so any
    date-formatted cell arrives as a bare number - the spreadsheet "serial"
    day count since 1899-12-30 - not a date string. Feeding that straight
    into `pd.to_datetime()` makes pandas treat it as a nanosecond offset
    from 1970-01-01, which collapses every date onto ~Jan 1, 1970 (the root
    cause of the "cut off as of 1970" bug and the collapsed, single-point
    S-Curve/Manpower charts).

    This converts numeric serials using the correct spreadsheet epoch and
    still falls back to normal string parsing for any cell typed in as text
    (e.g. "2026-07-20"), so both sources of data keep working.
    """
    s = series.copy()
    numeric = pd.to_numeric(s, errors="coerce")
    is_serial = numeric.notna()

    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if is_serial.any():
        out.loc[is_serial] = pd.to_datetime(numeric[is_serial], unit="D", origin="1899-12-30")
    if (~is_serial).any():
        out.loc[~is_serial] = pd.to_datetime(s[~is_serial], errors="coerce")
    return out


# Chapter 1 — daily zoning S-Curve + Zone/Kolom log
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_scurve_main(project: str) -> pd.DataFrame:
    tab = config.gsheet_tab(project, "scurve")
    raw = gs.read_tab(tab)
    if raw.empty or "Date" not in raw.columns:
        return pd.DataFrame()

    df = raw[config.SCURVE_MAIN_COLS].copy()
    df["Date"] = _parse_sheet_date(df["Date"])
    for c in ["PlanZoning", "PlanCum", "PlanPct_%", "ActualZoning", "ActualCum", "ActualPct_%"]:
        df[c] = _to_num(df[c])
    for c in ["PlanPct_%", "ActualPct_%"]:
        df[c] = _fix_pct_scale_glitches(df[c])
    df["Remarks"] = df["Remarks"].fillna("").astype(str)
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    # Signed deviation (Actual - Plan) is always recomputed in-app, never
    # trusted blindly from the sheet — used for the on-track/behind status
    # label and the "vs plan" delta. The dashboard's S-Curve chart plots the
    # absolute value instead (deviation magnitude only, always >= 0), which
    # is the intended display convention for that chart.
    df["DeviationPct"] = df["ActualPct_%"] - df["PlanPct_%"]
    df["DeviationPctAbs"] = df["DeviationPct"].abs()
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_zone_kolom(project: str) -> pd.DataFrame:
    tab = config.gsheet_tab(project, "scurve")
    raw = gs.read_tab(tab)
    needed = config.ZONE_KOLOM_COLS
    if raw.empty or not all(c in raw.columns for c in needed):
        return pd.DataFrame()

    df = raw[needed].copy()
    df["Date Structure"] = _parse_sheet_date(df["Date Structure"])
    df["Done"] = _to_num(df["Done"])
    df["Target"] = _to_num(df["Target"])
    df["Level"] = df["Level"].astype(str).str.strip()
    df["Metric"] = df["Metric"].astype(str).str.strip()
    df = df.dropna(subset=["Date Structure", "Level", "Metric"])
    df = df[(df["Level"] != "") & (df["Metric"] != "")]
    df = df.sort_values("Date Structure").reset_index(drop=True)
    return df


def zone_kolom_summary(zk_df: pd.DataFrame, level: str, metric: str) -> dict:
    """Latest cumulative + daily/weekly deltas for one Level/Metric pair."""
    sub = zk_df[(zk_df["Level"] == level) & (zk_df["Metric"] == metric)].sort_values("Date Structure")
    if sub.empty:
        return {}
    last = sub.iloc[-1]
    prev = sub.iloc[-2] if len(sub) > 1 else None
    week_ago_cutoff = last["Date Structure"] - pd.Timedelta(days=7)
    week_rows = sub[sub["Date Structure"] > week_ago_cutoff]
    week_start_done = week_rows.iloc[0]["Done"] if not week_rows.empty else last["Done"]

    return {
        "date": last["Date Structure"],
        "done": last["Done"],
        "target": last["Target"],
        "pct": (last["Done"] / last["Target"] * 100) if last["Target"] else 0,
        "previous": prev["Done"] if prev is not None else last["Done"],
        "current_delta": last["Done"] - (prev["Done"] if prev is not None else 0),
        "weekly_delta": last["Done"] - week_start_done,
        "remaining": max(last["Target"] - last["Done"], 0),
    }


def update_scurve_daily_actual(project: str, report_date: date, actual_zoning: float, remarks: str) -> None:
    """Daily Report form — updates (or appends) the row for report_date in the
    main S-Curve block (columns A:J) with the day's Actual Zoning + remarks."""
    tab = config.gsheet_tab(project, "scurve")
    date_str = report_date.strftime("%Y-%m-%d")

    df = load_scurve_main(project)
    row_num = gs.find_row_by_column_value(tab, 1, date_str)
    if row_num is None:
        # Also try matching however the sheet actually stores dates.
        row_num = gs.find_row_by_column_value(tab, 1, report_date.strftime("%d/%m/%Y"))
    if row_num is None:
        raise gs.GSheetError(
            f"No scheduled row found for {date_str} in '{tab}'. "
            "Add the date to the sheet's schedule first, or pick an existing date."
        )

    prior = df[df["Date"] < pd.Timestamp(report_date)]
    prev_actual_cum = prior["ActualCum"].dropna().iloc[-1] if not prior["ActualCum"].dropna().empty else 0
    this_row = df[df["Date"] == pd.Timestamp(report_date)]
    plan_cum = this_row["PlanCum"].iloc[0] if not this_row.empty else np.nan
    plan_pct = this_row["PlanPct_%"].iloc[0] if not this_row.empty else np.nan

    # Derive the project's total zoning target from rows where PlanPct_% is known.
    valid = df[(df["PlanPct_%"] > 0) & df["PlanCum"].notna()]
    target = float((valid["PlanCum"] / (valid["PlanPct_%"] / 100)).median()) if not valid.empty else np.nan

    actual_cum = prev_actual_cum + actual_zoning
    actual_pct = (actual_cum / target * 100) if target else np.nan
    dev_abs = actual_cum - plan_cum if pd.notna(plan_cum) else np.nan
    dev_pct = actual_pct - plan_pct if pd.notna(plan_pct) and pd.notna(actual_pct) else np.nan

    gs.write_row_range(tab, row_num, start_col=5, values=[
        actual_zoning, actual_cum,
        round(actual_pct, 4) if pd.notna(actual_pct) else "",
        round(dev_abs, 4) if pd.notna(dev_abs) else "",
        round(dev_pct, 4) if pd.notna(dev_pct) else "",
        remarks or "",
    ])
    load_scurve_main.clear()
    load_zone_kolom.clear()


def append_zone_kolom_update(project: str, level: str, metric: str, done: float, target: float, update_date: date) -> None:
    """Update Daily Progress form — appends a new cumulative reading to the
    Zone/Kolom log block (columns L:P)."""
    tab = config.gsheet_tab(project, "scurve")
    next_row = gs.find_next_empty_row(tab, col_index=12)  # column L
    gs.write_row_range(tab, next_row, start_col=12, values=[
        update_date.strftime("%Y-%m-%d"), level, metric, done, target,
    ])
    load_scurve_main.clear()
    load_zone_kolom.clear()


# Chapter 1 (secondary) — Sumaraja vendor weekly S-Curve 
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_sumaraja_scurve(project: str) -> pd.DataFrame:
    """Parses the vendor's weekly work-item S-Curve sheet into a tidy
    Week / WeekStart / PlanCumPct / ActualCumPct table.

    Layout: row containing 'W#1' marks the week-label row; the row directly
    above it holds each week's start date. From there, each work item spans
    two rows — one tagged 'Plan', the next 'Actual' — with per-week weighted
    contribution values from column I (index 8) onward. Summed vertically and
    cumulated horizontally, these reconstruct the overall project S-Curve.
    """
    tab = config.gsheet_tab(project, "sri-scurve")
    raw = gs.read_tab(tab)
    if raw.empty:
        return pd.DataFrame()

    values = raw.values.tolist()

    week_label_row = None
    for i, row in enumerate(values):
        if any(str(v).strip().upper().startswith("W#1") for v in row):
            week_label_row = i
            break
    if week_label_row is None or week_label_row == 0:
        return pd.DataFrame()

    week_labels = values[week_label_row]
    week_dates = values[week_label_row - 1]

    week_cols = [j for j, v in enumerate(week_labels) if str(v).strip().upper().startswith("W#")]
    if not week_cols:
        return pd.DataFrame()

    plan_totals = [0.0] * len(week_cols)
    actual_totals = [0.0] * len(week_cols)
    actual_counts = [0] * len(week_cols)

    tag_col = 5  # column F — 'Plan' / 'Actual' tag, based on the source layout
    for i in range(week_label_row + 1, len(values)):
        row = values[i]
        if len(row) <= tag_col:
            continue
        tag = str(row[tag_col]).strip().lower()
        if tag not in ("plan", "actual"):
            continue
        for k, j in enumerate(week_cols):
            if j >= len(row):
                continue
            v = row[j]
            if v == "" or v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if tag == "plan":
                plan_totals[k] += v
            else:
                actual_totals[k] += v
                actual_counts[k] += 1

    out_dates = [week_dates[j] if j < len(week_dates) else None for j in week_cols]

    df = pd.DataFrame({
        "Week": [str(week_labels[j]).strip() for j in week_cols],
        "WeekStart": out_dates,
        "PlanWeekly": plan_totals,
        "ActualWeekly": actual_totals,
        "HasActual": [c > 0 for c in actual_counts],
    })
    # Dates from Google Sheets (UNFORMATTED_VALUE) arrive as spreadsheet
    # serial numbers, not strings — see _parse_sheet_date for why this must
    # not go through a plain pd.to_datetime() call.
    df["WeekStart"] = _parse_sheet_date(df["WeekStart"])
    df = df.dropna(subset=["WeekStart"]).reset_index(drop=True)
    df["PlanWeeklyPct"] = df["PlanWeekly"] * 100
    df["ActualWeeklyPct"] = df["ActualWeekly"] * 100
    df["PlanCumPct"] = df["PlanWeekly"].cumsum() * 100
    df["ActualCumPct"] = df["ActualWeekly"].cumsum() * 100
    df.loc[~df["HasActual"], "ActualCumPct"] = np.nan
    df.loc[~df["HasActual"], "ActualWeeklyPct"] = np.nan
    return df


# Chapter 2 — HSE Manpower
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_manpower(project: str) -> pd.DataFrame:
    tab = config.gsheet_tab(project, "manpower")
    df = gs.read_tab(tab)
    if df.empty:
        return df
    df.columns = [str(c).strip() for c in df.columns]
    if "Date" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"Date": "date"})
    if "date" not in df.columns:
        return pd.DataFrame()
    df["date"] = _parse_sheet_date(df["date"])
    for c in [*config.MANPOWER_CATEGORIES, "Total", "Manhours"]:
        if c in df.columns:
            df[c] = _to_num(df[c]).fillna(0)
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset="date", keep="last").reset_index(drop=True)
    return df


def append_manpower_row(project: str, row_date: date, values_by_category: dict) -> None:
    tab = config.gsheet_tab(project, "manpower")
    raw = gs.read_tab(tab)
    headers = list(raw.columns) if not raw.empty else ["No", "Date", *config.MANPOWER_CATEGORIES, "Total", "Manhours"]
    date_col_idx = headers.index("Date") + 1 if "Date" in headers else 2

    date_str = row_date.strftime("%Y-%m-%d")
    row_num = gs.find_row_by_column_value(tab, date_col_idx, date_str)
    total = sum(values_by_category.get(c, 0) for c in config.MANPOWER_CATEGORIES)
    manhours = values_by_category.get("Manhours", total * 8)

    row_values = []
    for h in headers:
        if h == "Date":
            row_values.append(date_str)
        elif h == "No":
            row_values.append("")
        elif h == "Total":
            row_values.append(total)
        elif h == "Manhours":
            row_values.append(manhours)
        else:
            row_values.append(values_by_category.get(h, 0))

    if row_num is None:
        row_num = gs.find_next_empty_row(tab, col_index=date_col_idx)
    gs.write_row_range(tab, row_num, start_col=1, values=row_values)
    load_manpower.clear()


# Chapter 4 — HSE Safety
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_hse_safety(project: str) -> pd.DataFrame:
    """Findings log: one row per observation (not one row per day), so
    several rows can share the same Date and dates aren't necessarily
    consecutive — filtering/aggregation must group by Date rather than
    assume a fixed daily cadence."""
    tab = config.gsheet_tab(project, "hse-safety")
    raw = gs.read_tab(tab)
    if raw.empty or "Date" not in raw.columns:
        return pd.DataFrame()

    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df["Date"] = _parse_sheet_date(df["Date"])
    df = df.dropna(subset=["Date"])

    text_cols = [
        "Observation", "Assessment", "Risks", "Photos",
        "Rectification Evidence (Site Photos)", "Remarks",
        "Scope / Not Scope {DCI)", "Status",
    ]
    for c in text_cols:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()
    if "Status" in df.columns:
        df["Status"] = df["Status"].replace("", "Open")
    if "No" in df.columns:
        df["No"] = _to_num(df["No"])

    df = df.sort_values("Date").reset_index(drop=True)
    return df



# Chapter 3 — Document Control

@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_docon(project: str) -> pd.DataFrame:
    tab = config.gsheet_tab(project, "docon")
    df = gs.read_tab(tab)
    if df.empty or "VENDOR" not in df.columns:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    numeric_cols = [c for c in df.columns if c != "VENDOR"]
    for c in numeric_cols:
        df[c] = _to_num(df[c]).fillna(0)
    df = df[df["VENDOR"].astype(str).str.upper() != config.DOCON_TOTAL_ROW_LABEL].reset_index(drop=True)
    return df
