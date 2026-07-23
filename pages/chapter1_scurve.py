"""
pages/chapter1_scurve.py — S-Curve & Zone Status dashboard.

Reads directly from the sheet's own percentage columns (PlanPct_%,
ActualPct_%, DevPct_%) — no in-app recalculation. Deviation is maintained
manually by the user in the sheet and simply displayed, combined into one
chart with the Plan/Actual lines (bars on a secondary axis).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

import config
from services import sheets
from services import zone_progress as zp
from services.charts import scurve_combined_chart
from utils import fmt_pct, fmt_signed, status_badge, kpi_card


def render() -> None:
    st.markdown("##### JK7 STRUCTURE WORKS")
    st.title("📊 S-Curve & Zone Status")

    try:
        df = sheets.load_scurve_main()
    except Exception as e:
        st.error(f"Could not load S-Curve data: {e}")
        return

    if df.empty:
        st.info("No S-Curve data available yet.")
        return

    # --- Filters -----------------------------------------------------------
    with st.expander("🔎 Filters", expanded=False):
        min_d, max_d = df["Date"].min().date(), df["Date"].max().date()
        date_range = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        search_term = st.text_input("Search remarks / milestone")

    filtered = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered["Date"].dt.date >= start) & (filtered["Date"].dt.date <= end)]
    if search_term:
        filtered = filtered[filtered["Remarks"].str.contains(search_term, case=False, na=False)]

    # --- Latest known values (last row with an Actual value) ---------------
    has_actual = df["ActualPct_%"].notna()
    last_idx = df[has_actual].index.max() if has_actual.any() else None
    last_row = df.loc[last_idx] if last_idx is not None else None

    plan_today = last_row["PlanPct_%"] if last_row is not None else 0
    actual_today = last_row["ActualPct_%"] if last_row is not None else 0
    deviation_today = last_row["DevPct_%"] if last_row is not None else 0

    if pd.notna(deviation_today) and deviation_today >= 0:
        status_label, status_color = "ON TRACK / AHEAD", config.THEME["green"]
    elif pd.notna(deviation_today) and deviation_today >= -10:
        status_label, status_color = "SLIGHTLY BEHIND", config.THEME["amber"]
    else:
        status_label, status_color = "BEHIND SCHEDULE", config.THEME["red"]

    next_date = (last_row["Date"] + timedelta(days=1)).date() if last_row is not None else df["Date"].min().date()

    if last_row is not None:
        st.caption(f"Last Update: {last_row['Date'].strftime('%d %B %Y')}")

    # --- KPI cards -----------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Overall Target", "100%", accent=config.THEME["blue"]), unsafe_allow_html=True)
    c2.markdown(kpi_card("Plan Progress", fmt_pct(plan_today), accent=config.THEME["purple"]), unsafe_allow_html=True)
    c3.markdown(kpi_card("Actual Progress", fmt_pct(actual_today), accent=config.THEME["pink"]), unsafe_allow_html=True)
    with c4:
        st.markdown(status_badge(status_label, status_color), unsafe_allow_html=True)

    st.divider()

    # --- Combined S-Curve + Deviation chart ---------------------------------
    st.subheader("📈 S-Curve — Plan vs Actual vs Deviation")
    st.plotly_chart(scurve_combined_chart(filtered if not filtered.empty else df), use_container_width=True)
    st.caption("Deviation bars (right axis) are read directly from the sheet's DevPct_% column — maintained manually.")

    st.divider()

    # --- Daily report input form + Milestone tracker ------------------------
    col_form, col_milestone = st.columns([1.1, 1])
    with col_form:
        st.subheader("Daily Report")
        with st.form("update_form", clear_on_submit=True):
            date_input = st.date_input("Date", value=next_date)
            qty_input = st.number_input("Actual Zoning", min_value=0.0, step=1.0)
            remarks_input = st.text_input("Remarks / Milestone (optional)")
            submitted = st.form_submit_button("Update Data", type="primary")
            if submitted:
                ok, msg = sheets.update_scurve_actual(date_input.strftime("%Y-%m-%d"), qty_input, remarks_input)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    with col_milestone:
        milestones = df[df["Remarks"] != ""]
        st.subheader(f"Milestone Tracker ({len(milestones)})")
        st.dataframe(
            milestones[["Date", "Remarks"]].rename(columns={"Date": "Date"}),
            hide_index=True, use_container_width=True, height=280,
        )

    st.divider()

    # --- Progress table ------------------------------------------------------
    st.subheader("Progress Table")
    table_df = filtered[["Date", "PlanZoning", "PlanPct_%", "ActualZoning", "ActualPct_%", "DevPct_%", "Remarks"]].copy()
    table_df.columns = ["Date", "Plan/day", "Plan Cum %", "Actual/day", "Actual Cum %", "Deviation %", "Remarks"]
    for col in ["Plan Cum %", "Actual Cum %", "Deviation %"]:
        table_df[col] = table_df[col].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    st.dataframe(table_df, hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️ Download CSV", data=table_df.to_csv(index=False).encode("utf-8"),
        file_name="scurve_progress.csv", mime="text/csv",
    )

    # --- Zone / Kolom progress -------------------------------------------------
    st.divider()
    st.header("🏗️ Zone / Kolom Progress")
    st.caption("Sourced from the columns beside 'Remarks' in the same scurve-jk7 tab.")

    try:
        zone_df_raw = sheets.load_scurve_zone()
        zone_df = zp.prepare_zone_df(zone_df_raw)
    except ValueError as e:
        st.error(str(e))
        st.info(
            "Check the zone/kolom columns in the scurve-jk7 tab (right after 'Remarks'). "
            "Expected headers: 'Date', 'Level', 'Metric', 'Done', 'Target'."
        )
        zone_df = pd.DataFrame(columns=["Date", "Level", "Metric", "Done", "Target"])

    levels_present = sorted(zone_df["Level"].unique().tolist()) if not zone_df.empty else ["GF", "L1", "L2"]
    tabs = st.tabs(levels_present)
    for tab, level in zip(tabs, levels_present):
        with tab:
            image_map = {
                ("GF", "Zone"): config.ASSETS_DIR / "denah_gf.jpeg",
                ("GF", "Kolom"): config.ASSETS_DIR / "denah_kolom_gf.jpg",
                ("L1", "Zone"): config.ASSETS_DIR / "denah_L1.jpeg",
                ("L1", "Kolom"): config.ASSETS_DIR / "denah_kolom_L1.jpg",
            }
            zp.render_progress_summary(
                zone_df, level, "Zone", f"JK7 STRUCTURE — Zone {level}",
                image_path=image_map.get((level, "Zone")),
            )
            st.divider()
            zp.render_progress_summary(
                zone_df, level, "Kolom", f"JK7 STRUCTURE — Kolom {level}",
                image_path=image_map.get((level, "Kolom")),
            )

    st.divider()
    with st.expander("✏️ Update Daily Progress (Zone/Kolom)"):
        with st.form("update_zone_progress_form", clear_on_submit=True):
            level_input = st.selectbox("Level", levels_present or ["GF", "L1", "L2"])
            metric_input = st.selectbox("Metric", ["Zone", "Kolom"])
            done_input = st.number_input("Total Done (cumulative)", min_value=0, step=1)
            target_input = st.number_input("Total Target", min_value=1, step=1, value=522)
            date_zone_input = st.date_input("Update Date", value=datetime.now().date())
            submitted_zone = st.form_submit_button("Save Progress", type="primary")
            if submitted_zone:
                ok, msg = sheets.append_zone_progress(
                    date_zone_input.strftime("%Y-%m-%d"), level_input, metric_input,
                    done_input, target_input,
                )
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
