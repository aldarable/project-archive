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


# ---------------------------------------------------------------------------
# Chapter 1 — daily zoning S-Curve + Zone/Kolom log (tab: <project>-scurve)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_scurve_main(project: str) -> pd.DataFrame:
    tab = config.gsheet_tab(project, "scurve")
    raw = gs.read_tab(tab)
    if raw.empty or "Date" not in raw.columns:
        return pd.DataFrame()

    df = raw[config.SCURVE_MAIN_COLS].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["PlanZoning", "PlanCum", "PlanPct_%", "ActualZoning", "ActualCum", "ActualPct_%"]:
        df[c] = _to_num(df[c])
    df["Remarks"] = df["Remarks"].fillna("").astype(str)
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    # Deviation is always recomputed in-app, never trusted blindly from the sheet.
    df["DeviationPct"] = df["ActualPct_%"] - df["PlanPct_%"]
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_zone_kolom(project: str) -> pd.DataFrame:
    tab = config.gsheet_tab(project, "scurve")
    raw = gs.read_tab(tab)
    needed = config.ZONE_KOLOM_COLS
    if raw.empty or not all(c in raw.columns for c in needed):
        return pd.DataFrame()

    df = raw[needed].copy()
    df["Date Structure"] = pd.to_datetime(df["Date Structure"], errors="coerce")
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


# ---------------------------------------------------------------------------
# Chapter 1 (secondary) — Sumaraja vendor weekly S-Curve (tab: <project>-sri-scurve)
# ---------------------------------------------------------------------------
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

    out_dates = []
    for j in week_cols:
        d = week_dates[j] if j < len(week_dates) else None
        if isinstance(d, str):
            d = pd.to_datetime(d, errors="coerce")
        out_dates.append(d)

    df = pd.DataFrame({
        "Week": [str(week_labels[j]).strip() for j in week_cols],
        "WeekStart": out_dates,
        "PlanWeekly": plan_totals,
        "ActualWeekly": actual_totals,
        "HasActual": [c > 0 for c in actual_counts],
    })
    df["WeekStart"] = pd.to_datetime(df["WeekStart"], errors="coerce")
    df = df.dropna(subset=["WeekStart"]).reset_index(drop=True)
    df["PlanCumPct"] = df["PlanWeekly"].cumsum() * 100
    df["ActualCumPct"] = df["ActualWeekly"].cumsum() * 100
    df.loc[~df["HasActual"], "ActualCumPct"] = np.nan
    return df


# ---------------------------------------------------------------------------
# Chapter 2 — HSE Manpower (tab: <project>-manpower)
# ---------------------------------------------------------------------------
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
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
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


# ---------------------------------------------------------------------------
# Chapter 3 — Document Control (tab: <project>-docon)
# ---------------------------------------------------------------------------
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
