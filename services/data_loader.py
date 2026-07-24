"""
services/data_loader.py — Read-only data access layer.
"""

from __future__ import annotations
import json
import pandas as pd
import streamlit as st
import config
from services.gsheet_client import read_tab


def _read_csv(project: str, filename: str) -> pd.DataFrame:
    path = config.project_dir(project) / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_scurve_main(project: str) -> pd.DataFrame:
    df = _read_csv(project, config.CSV_SCURVE_MAIN)
    if df.empty:
        return df
    df.columns = [str(c).strip() for c in df.columns]
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["PlanWeekly_%", "PlanCumPct_%", "ActualWeekly_%", "ActualCumPct_%", "DeviationPct"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Remarks"] = df.get("Remarks", "").fillna("").astype(str)
    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    df["DeviationPct"] = df["ActualCumPct_%"] - df["PlanCumPct_%"]
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_scurve_workbreakdown(project: str) -> pd.DataFrame:
    df = _read_csv(project, config.CSV_SCURVE_WORKBREAKDOWN)
    if df.empty:
        return df
    df.columns = [str(c).strip() for c in df.columns]
    df["LoadPct"] = pd.to_numeric(df["LoadPct"], errors="coerce").fillna(0)
    df["ActualPct"] = pd.to_numeric(df["ActualPct"], errors="coerce").fillna(0).clip(0, 100)
    return df


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def load_scurve_meta(project: str) -> dict:
    path = config.project_dir(project) / config.JSON_SCURVE_META
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def load_manpower(project: str) -> pd.DataFrame:
    df = read_tab(config.GSHEET_TABS["2"])
    if df.empty:
        return df
    df.columns = [str(c).strip() for c in df.columns]
    if "Project" in df.columns:
        df = df[df["Project"].astype(str).str.upper() == project.upper()]
    if "Date" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in [*config.MANPOWER_CATEGORIES, "Total", "Manhours"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset="date", keep="last").reset_index(drop=True)
    return df


def load_docon(project: str) -> pd.DataFrame:
    df = read_tab(config.GSHEET_TABS["3"])
    if df.empty:
        return df
    df.columns = [str(c).strip() for c in df.columns]
    if "Project" in df.columns:
        df = df[df["Project"].astype(str).str.upper() == project.upper()]
    if "VENDOR" not in df.columns:
        return pd.DataFrame()
    numeric_cols = [c for c in df.columns if c not in ("VENDOR", "Project")]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    # Drop the sheet's own pre-computed TOTAL row — the app recomputes totals
    # itself so they stay correct even as vendors are added or removed.
    df = df[df["VENDOR"].astype(str).str.upper() != config.DOCON_TOTAL_ROW_LABEL].reset_index(drop=True)
    return df
