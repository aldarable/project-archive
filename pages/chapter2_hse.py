"""
pages/chapter2_hse.py — HSE Manpower dashboard.

Manhours is read directly from the sheet's own 'Manhours' column — never
recomputed by the app (source of truth lives in Google Sheets).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import config
from services import sheets
from services.charts import manpower_category_trend_chart, single_line_trend_chart, bar_by_category_chart
from utils import kpi_card, fmt_int


def render() -> None:
    st.title("👷 HSE Manpower Monitoring")

    try:
        df = sheets.load_manpower()
    except Exception as e:
        st.error(f"Could not load HSE Manpower data: {e}")
        return

    if df.empty:
        st.info("No manpower data available yet.")
        return

    st.caption(f"Latest data: **{df['date'].iloc[-1].strftime('%d %b %Y')}** • {len(df)} days recorded")

    # --- Filters -------------------------------------------------------------
    with st.expander("🔎 Filters", expanded=False):
        min_d, max_d = df["date"].min().date(), df["date"].max().date()
        date_range = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        contractor_filter = st.multiselect("Contractor / Team", config.MANPOWER_CATEGORIES, default=config.MANPOWER_CATEGORIES)

    filtered = df.copy()
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered["date"].dt.date >= start) & (filtered["date"].dt.date <= end)]
    active_categories = contractor_filter or config.MANPOWER_CATEGORIES

    # --- KPI cards -------------------------------------------------------------
    last_row = filtered.iloc[-1] if not filtered.empty else df.iloc[-1]
    total_manpower = int(last_row["Total"])
    monthly_avg = filtered["Total"].tail(30).mean() if not filtered.empty else df["Total"].mean()
    total_manhours = int(filtered["Manhours"].sum()) if not filtered.empty else int(df["Manhours"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Total Manpower (Today)", fmt_int(total_manpower), accent=config.THEME["blue"]), unsafe_allow_html=True)
    c2.markdown(kpi_card("Today's Date", last_row["date"].strftime("%d %b %Y"), accent=config.THEME["purple"]), unsafe_allow_html=True)
    c3.markdown(kpi_card("Monthly Average", fmt_int(monthly_avg), accent=config.THEME["pink"]), unsafe_allow_html=True)
    c4.markdown(kpi_card("Total Manhours", fmt_int(total_manhours), accent=config.THEME["green"]), unsafe_allow_html=True)

    st.divider()

    # --- Daily / Weekly / Monthly trend tabs -----------------------------------
    st.subheader("Manpower Trend by Contractor")
    tab_daily, tab_weekly, tab_monthly = st.tabs(["Daily", "Weekly", "Monthly"])

    with tab_daily:
        st.plotly_chart(
            manpower_category_trend_chart(filtered, active_categories, config.MANPOWER_COLORS),
            use_container_width=True,
        )

    with tab_weekly:
        weekly = filtered.set_index("date")[active_categories].resample("W").mean().reset_index()
        st.plotly_chart(
            manpower_category_trend_chart(weekly, active_categories, config.MANPOWER_COLORS),
            use_container_width=True,
        )

    with tab_monthly:
        monthly = filtered.set_index("date")[active_categories].resample("ME").mean().reset_index()
        st.plotly_chart(
            manpower_category_trend_chart(monthly, active_categories, config.MANPOWER_COLORS),
            use_container_width=True,
        )

    st.divider()

    # --- Manhours charts --------------------------------------------------------
    st.subheader("Manhours")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Accumulated Manhours**")
        cum_df = filtered[["date"]].copy()
        cum_df["Cumulative Manhours"] = filtered["Manhours"].cumsum()
        st.plotly_chart(
            single_line_trend_chart(cum_df, "Cumulative Manhours", "Manhours", config.MANPOWER_COLORS["Manhours"]),
            use_container_width=True,
        )
    with col_b:
        st.markdown("**Manhours by Contractor (share of headcount)**")
        latest = filtered.iloc[-1] if not filtered.empty else df.iloc[-1]
        headcount_share = {c: latest[c] for c in active_categories}
        total_hc = sum(headcount_share.values()) or 1
        manhours_by_contractor = {c: (v / total_hc) * latest["Manhours"] for c, v in headcount_share.items()}
        st.plotly_chart(
            bar_by_category_chart(
                list(manhours_by_contractor.keys()), list(manhours_by_contractor.values()),
                config.THEME["purple"], title_y="Estimated Manhours",
            ),
            use_container_width=True,
        )
        st.caption("Estimated proportionally from each contractor's share of today's headcount, since Manhours is tracked as one daily total.")

    st.divider()

    # --- Total manpower trend -------------------------------------------------
    st.subheader("Total Manpower Trend")
    st.plotly_chart(
        single_line_trend_chart(filtered, "Total", "Total Manpower", config.THEME["blue"]),
        use_container_width=True,
    )

    st.divider()

    # --- Input form ------------------------------------------------------------
    with st.expander("📝 Input / Update Daily Data"):
        input_date = st.date_input("Date", value=date.today(), key="mp_date")
        existing = df[df["date"] == pd.Timestamp(input_date)]
        prefill = existing.iloc[0].to_dict() if not existing.empty else {c: 0 for c in config.MANPOWER_CATEGORIES}
        with st.form("manpower_input_form"):
            vals = {c: st.number_input(c, min_value=0, step=1, value=int(prefill.get(c, 0) or 0)) for c in config.MANPOWER_CATEGORIES}
            submitted = st.form_submit_button("💾 Save Today's Data", type="primary")
            if submitted:
                updated = sheets.upsert_manpower_row(df, input_date, vals)
                ok, msg = sheets.save_manpower(updated)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()

    # --- Data table + export -----------------------------------------------------
    with st.expander("📋 View / Download Full Data"):
        display_df = filtered.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download CSV", data=display_df.to_csv(index=False).encode("utf-8"),
            file_name="hse_manpower.csv", mime="text/csv",
        )
