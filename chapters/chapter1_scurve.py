"""
chapters/chapter1_scurve.py for S-Curve & Work Breakdown.
"""

from __future__ import annotations
import streamlit as st
import config
from services import data_loader as dl
from services.charts import scurve_plan_actual_chart, scurve_deviation_chart, workbreakdown_bar
from utils import fmt_pct, fmt_signed, metric


def render(project: str) -> None:
    st.subheader("Structure Works")
    st.title("S-Curve Progress")

    df = dl.load_scurve_main(project)
    if df.empty:
        st.info("No S-Curve data available yet for this project.")
        return

    meta = dl.load_scurve_meta(project)

    has_actual = df["ActualCumPct_%"].notna()
    last_row = df[has_actual].iloc[-1] if has_actual.any() else None

    plan_today = last_row["PlanCumPct_%"] if last_row is not None else 0
    actual_today = last_row["ActualCumPct_%"] if last_row is not None else 0
    deviation_today = last_row["DeviationPct"] if last_row is not None else 0

    if meta:
        st.caption(
            f"{meta.get('contractor', '')} · {meta.get('service', '')} scope · "
            f"{meta.get('week_label', '')} · report last updated {meta.get('last_updated', '')}"
        )
    elif last_row is not None:
        st.caption(f"Last reported — {last_row['Date'].strftime('%d %B %Y')} ({last_row['Week']})")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric("Overall Target", "100%", config.COLORS["plan"])
    with c2:
        metric("Plan Progress", fmt_pct(plan_today), config.COLORS["plan"])
    with c3:
        metric("Actual Progress", fmt_pct(actual_today), config.COLORS["actual"])
    with c4:
        if deviation_today >= 0:
            status_label = "On Track / Ahead"
        elif deviation_today >= -10:
            status_label = "Slightly Behind"
        else:
            status_label = "Behind Schedule"
        metric("Status", status_label, config.COLORS["deviation"], delta=f"{fmt_signed(deviation_today)} vs plan")

    st.divider()

    st.markdown("##### S-Curve — Plan vs Actual")
    st.plotly_chart(scurve_plan_actual_chart(df), width="stretch", config={"displayModeBar": False})
    st.caption("Plan continues week by week as scheduled; Actual stops at the latest reported week.")

    st.markdown("##### Deviation")
    st.plotly_chart(scurve_deviation_chart(df), width="stretch", config={"displayModeBar": False})
    st.caption("Deviation = Actual − Plan (cumulative). Negative means behind schedule.")

    st.divider()

    # Work Breakdown
    st.markdown("### Work Breakdown by Package")
    wb_df = dl.load_scurve_workbreakdown(project)

    if wb_df.empty:
        st.info("No work-package data available yet for this project.")
        return

    st.caption("Each bar is % of that package's own scope completed. Package weight = its share of total project scope.")
    st.plotly_chart(workbreakdown_bar(wb_df), width="stretch", config={"displayModeBar": False})
