"""
chapters/chapter4_safety.py for HSE Safety.
"""

from __future__ import annotations
from datetime import date, timedelta
import pandas as pd
import streamlit as st
import config
from services import data_loader as dl
from services.charts import hse_status_donut, hse_category_bar, hse_trend_chart
from services.gsheet_client import GSheetError
from utils import fmt_int, fmt_pct, metric


def _badge(label: str, color: str) -> str:
    if not label:
        return ""
    return (
        f'<span style="background:{color}22; color:{color}; border:1px solid {color}55; '
        f'padding:2px 10px; border-radius:999px; font-size:0.78rem; font-weight:600;">{label}</span>'
    )


def render(project: str) -> None:
    st.subheader(f"{project} STRUCTURE WORKS")
    st.title("🦺 HSE Safety")

    try:
        df = dl.load_hse_safety(project)
    except GSheetError as exc:
        st.error(f"Couldn't load HSE Safety from Google Sheets: {exc}")
        return

    if df.empty:
        st.info("No HSE Safety data available yet for this project.")
        return

    min_date, max_date = df["Date"].min().date(), df["Date"].max().date()

    
    # Filters — quick date presets (+ custom range) and Status
    st.markdown("##### Filter")
    f1, f2 = st.columns([2, 1])
    with f1:
        preset = st.pills(
            "Period", ["All Dates", "Last 7 Days", "Last 30 Days", "Custom Range"],
            default="All Dates", label_visibility="collapsed", key="hse_period_pill",
        )
    preset = preset or "All Dates"

    if preset == "Custom Range":
        start_date, end_date = st.date_input(
            "Custom range", value=(min_date, max_date),
            min_value=min_date, max_value=max_date,
            label_visibility="collapsed", key="hse_custom_range",
        )
    elif preset == "Last 7 Days":
        start_date, end_date = max(min_date, max_date - timedelta(days=6)), max_date
    elif preset == "Last 30 Days":
        start_date, end_date = max(min_date, max_date - timedelta(days=29)), max_date
    else:
        start_date, end_date = min_date, max_date

    with f2:
        status_options = sorted(df["Status"].unique().tolist())
        status_filter = st.multiselect(
            "Status", status_options, default=status_options,
            label_visibility="collapsed", placeholder="Filter Status",
            key="hse_status_filter",
        )
    status_filter = status_filter or status_options

    mask = (
        (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
        & (df["Status"].isin(status_filter))
    )
    fdf = df[mask].reset_index(drop=True)

    st.caption(
        f"Showing **{len(fdf)}** findings · {start_date.strftime('%d %b %Y')} → "
        f"{end_date.strftime('%d %b %Y')} · {len(df)} total recorded"
    )
    st.divider()

    if fdf.empty:
        st.info("No findings match the selected filters.")
        return

    # KPI summary
    total = len(fdf)
    open_count = int((fdf["Status"] == "Open").sum())
    close_count = int((fdf["Status"] == "Close").sum())
    p0_count = int(fdf["Risks"].str.contains("P0", na=False).sum())
    closure_rate = (close_count / total * 100) if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric("Total Findings", fmt_int(total), config.COLORS["plan"])
    with c2:
        metric("Open", fmt_int(open_count), config.HSE_STATUS_COLORS["Open"])
    with c3:
        metric("Closed", fmt_int(close_count), config.HSE_STATUS_COLORS["Close"])
    with c4:
        metric("Closure Rate", fmt_pct(closure_rate), config.COLORS["on_track"])
    with c5:
        metric("P0 — Significant Risks", fmt_int(p0_count), config.HSE_RISK_COLORS["P0 - Significant Risks"])

    st.divider()

    
    # Breakdown charts
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_a:
        st.markdown("##### Status")
        st.plotly_chart(
            hse_status_donut(fdf, "Status", config.HSE_STATUS_COLORS),
            width="stretch", config={"displayModeBar": False},
        )
    with col_b:
        st.markdown("##### Assessment")
        st.plotly_chart(
            hse_category_bar(fdf, "Assessment", config.HSE_ASSESSMENT_COLORS),
            width="stretch", config={"displayModeBar": False},
        )
    with col_c:
        st.markdown("##### Risk Level")
        st.plotly_chart(
            hse_category_bar(fdf, "Risks", config.HSE_RISK_COLORS),
            width="stretch", config={"displayModeBar": False},
        )

    st.markdown("##### Findings Over Time")
    st.plotly_chart(
        hse_trend_chart(fdf, "Date", "Status", config.HSE_STATUS_COLORS),
        width="stretch", config={"displayModeBar": False},
    )

    st.divider()

    # Browse a specific inspection date — full finding detail
    st.markdown("##### 🗂️ Browse by Date")
    available_dates = sorted(fdf["Date"].dt.date.unique(), reverse=True)
    picked_date = st.selectbox(
        "Inspection date", available_dates,
        format_func=lambda d: d.strftime("%d %B %Y"), key="hse_browse_date",
    )
    day_df = fdf[fdf["Date"].dt.date == picked_date]
    st.caption(f"{len(day_df)} finding(s) recorded on {picked_date.strftime('%d %B %Y')}")

    for _, row in day_df.iterrows():
        with st.container(border=True):
            badges = " ".join([
                _badge(row["Status"], config.HSE_STATUS_COLORS.get(row["Status"], "#8B5CF6")),
                _badge(row["Assessment"], config.HSE_ASSESSMENT_COLORS.get(row["Assessment"], "#8B5CF6")),
                _badge(row["Risks"], config.HSE_RISK_COLORS.get(row["Risks"], "#8B5CF6")),
            ])
            st.markdown(badges, unsafe_allow_html=True)
            st.markdown(f"**{row['Observation']}**")
            if row.get("Remarks"):
                st.caption(f"↳ {row['Remarks']}")
            link_cols = st.columns(2)
            with link_cols[0]:
                if row.get("Photos"):
                    st.link_button("📷 Site Photo", row["Photos"], width="stretch")
            with link_cols[1]:
                if row.get("Rectification Evidence (Site Photos)"):
                    st.link_button("✅ Rectification Evidence", row["Rectification Evidence (Site Photos)"], width="stretch")

    st.divider()

   
    # Full data table + download
    with st.expander("📄 View / Download Full Data"):
        st.dataframe(
            fdf.drop(columns=["Scope / Not Scope {DCI)"], errors="ignore"),
            width="stretch", hide_index=True,
            column_config={
                "Photos": st.column_config.LinkColumn("Photos", display_text="Open"),
                "Rectification Evidence (Site Photos)": st.column_config.LinkColumn(
                    "Rectification Evidence", display_text="Open"
                ),
            },
        )
        st.download_button(
            "⬇️ Download CSV", data=fdf.to_csv(index=False).encode("utf-8"),
            file_name=f"{project.lower()}_hse_safety.csv", mime="text/csv",
        )
