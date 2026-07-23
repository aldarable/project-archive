"""
services/zone_progress.py — Zone/Kolom progress summary logic for Chapter 1.

Ported from the original zone_map.py, with the data-access parts removed
(now handled centrally by services/sheets.py) and the rest kept intact.
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

import config
from utils import image_to_base64


def normalize_level(raw: str) -> str:
    """Turn any Level text ('Kolom Level 1', 'Lt 1', 'Ground Floor', ...)
    into one of 'GF', 'L1', 'L2', etc. Unrecognized text is returned as-is."""
    if raw is None:
        return ""
    text = str(raw).strip().lower()
    text = "".join(ch for ch in text if ch.isalnum() or ch.isspace())

    if "gf" in text or "ground" in text:
        return "GF"

    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        return f"L{digits}"

    return str(raw).strip()


def normalize_metric(raw: str) -> str:
    """Turn any Metric text into 'Zone' or 'Kolom'. Defaults to 'Zone'."""
    if raw is None:
        return "Zone"
    text = str(raw).strip().lower()
    if "kolom" in text or "column" in text:
        return "Kolom"
    if "zone" in text:
        return "Zone"
    return str(raw).strip() or "Zone"


def prepare_zone_df(zone_df: pd.DataFrame) -> pd.DataFrame:
    df = zone_df.copy()
    df["Level"] = df["Level"].apply(normalize_level)
    df["Metric"] = df["Metric"].apply(normalize_metric)
    return df


def compute_progress_summary(zone_df: pd.DataFrame, level: str, metric: str) -> dict | None:
    """Compute Daily Progress (previous/current/weekly) and Accumulative
    Progress (total/remaining/percentage) for one Level+Metric combination."""
    df = zone_df[(zone_df["Level"] == level) & (zone_df["Metric"] == metric)]
    df = df.sort_values("Date").reset_index(drop=True)
    if df.empty:
        return None

    last = df.iloc[-1]
    total = int(last["Done"])
    target = int(last["Target"])
    remaining = target - total
    pct = (total / target * 100) if target else 0.0

    current_new = 0
    previous_new = 0
    if len(df) >= 2:
        current_new = int(df.iloc[-1]["Done"] - df.iloc[-2]["Done"])
    if len(df) >= 3:
        previous_new = int(df.iloc[-2]["Done"] - df.iloc[-3]["Done"])

    week_ago = last["Date"] - timedelta(days=7)
    older = df[df["Date"] <= week_ago]
    if not older.empty:
        weekly_new = int(last["Done"] - older.iloc[-1]["Done"])
    else:
        weekly_new = int(last["Done"] - df.iloc[0]["Done"])

    return {
        "last_date": last["Date"], "total": total, "target": target,
        "remaining": remaining, "pct": pct,
        "current_new": current_new, "previous_new": previous_new, "weekly_new": weekly_new,
    }


def render_progress_summary(zone_df: pd.DataFrame, level: str, metric: str,
                             title: str, unit_label: str | None = None,
                             image_path=None) -> None:
    """Render one summary panel: Daily Progress & Accumulative Progress for a
    single Level+Metric combination, with an optional site-plan image."""
    s = compute_progress_summary(zone_df, level, metric)
    unit_label = unit_label or metric.lower()
    st.markdown(f"##### {title}")

    if s is None:
        st.info(f"No data yet for {level} - {metric}. Add it via the update form below.")
        return

    img_col, info_col = (st.columns([1, 1.4]) if image_path else (None, st.container()))

    if image_path and img_col is not None:
        with img_col:
            data_uri = image_to_base64(image_path)
            if data_uri:
                st.image(data_uri, use_container_width=True)
            else:
                st.caption(f"(site plan image '{image_path.name}' not available)")

    with info_col:
        st.caption(f"CUT OFF {s['last_date'].strftime('%d %B %Y').upper()}")
        trend_icon = "✅" if s["remaining"] <= 0 else "📈"
        st.markdown(
            f"**TOTAL: {s['total']}/{s['target']} {unit_label} "
            f"({s['pct']:.2f}%) {s['current_new']:+d} {trend_icon}**"
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**DAILY PROGRESS**")
            st.write(f"PREVIOUS: {s['previous_new']:+d} {unit_label}")
            st.write(f"CURRENT: {s['current_new']:+d} {unit_label}")
            st.write(f"WEEKLY (7 days): {s['weekly_new']:+d} {unit_label}")
        with c2:
            st.markdown("**ACCUMULATIVE PROGRESS**")
            st.write(f"TOTAL: {s['total']}/{s['target']} {unit_label}")
            st.write(f"REMAINING: {s['remaining']} {unit_label}")
            st.write(f"PERCENTAGE: {s['pct']:.2f}%")
