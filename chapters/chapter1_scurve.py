"""
chapters/chapter1_scurve.py — S-Curve & Zone Status.
"""

from __future__ import annotations
from datetime import date
import streamlit as st
import config
from services import data_loader as dl
from services.charts import scurve_combined_chart, sumaraja_scurve_chart
from services.gsheet_client import GSheetError
from utils import fmt_pct, fmt_signed, fmt_int, metric


def _status_label(deviation: float) -> str:
    if deviation >= 0:
        return "On Track / Ahead"
    if deviation >= -10:
        return "Slightly Behind"
    return "Behind Schedule"


def render(project: str) -> None:
    st.subheader(f"{project} STRUCTURE WORKS")
    st.title("📊 S-Curve & Zone Status")

    try:
        df = dl.load_scurve_main(project)
    except GSheetError as exc:
        st.error(f"Couldn't load S-Curve data from Google Sheets: {exc}")
        return

    if df.empty:
        st.info("No S-Curve data available yet for this project.")
        return

    has_actual = df["ActualPct_%"].notna()
    last_row = df[has_actual].iloc[-1] if has_actual.any() else df.iloc[-1]

    plan_today = last_row["PlanPct_%"]
    actual_today = last_row["ActualPct_%"] if has_actual.any() else 0
    deviation_today = last_row["DeviationPct"] if has_actual.any() else 0

    st.caption(f"Last update: {last_row['Date'].strftime('%d %b %Y')}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric("Overall Target", "100%", config.COLORS["plan"])
    with c2:
        metric("Plan Progress", fmt_pct(plan_today), config.COLORS["plan"])
    with c3:
        metric("Actual Progress", fmt_pct(actual_today), config.COLORS["actual"])
    with c4:
        metric("Status", _status_label(deviation_today), config.COLORS["deviation"],
               delta=f"{fmt_signed(deviation_today)} vs plan")

    st.divider()

    # --- Combined S-Curve: Plan vs Actual vs Deviation ---------------------
    st.markdown("##### 📈 S-Curve — Plan vs Actual vs Deviation")
    st.plotly_chart(scurve_combined_chart(df), width="stretch", config={"displayModeBar": False})
    st.caption("Deviation is plotted as an absolute value (|Actual − Plan|) on the same axis as Plan/Actual — recomputed in-app, not read from the sheet's DevPct_% column.")

    # --- Sumaraja (vendor) weekly S-Curve ----------------------------------
    st.markdown("##### 📈 S-Curve — Sumaraja (Vendor Weekly Report)")
    try:
        sri_df = dl.load_sumaraja_scurve(project)
    except GSheetError as exc:
        st.warning(f"Couldn't load the Sumaraja S-Curve: {exc}")
        sri_df = None
    except Exception as exc:  # noqa: BLE001 — never let one section crash the page
        st.warning(f"Couldn't parse the Sumaraja S-Curve sheet: {exc}")
        sri_df = None

    if sri_df is not None and not sri_df.empty:
        st.plotly_chart(sumaraja_scurve_chart(sri_df), width="stretch", config={"displayModeBar": False})
        st.caption("Weighted by each work item's % Load, summed weekly from the vendor's own (Sumaraja) schedule.")
    else:
        st.info("No Sumaraja S-Curve data available yet.")

    st.divider()

    # --- Daily Report + Milestone Tracker -----------------------------------
    col_report, col_milestone = st.columns(2)

    with col_report:
        st.markdown("##### 📝 Daily Report")
        with st.form("daily_report_form"):
            report_date = st.date_input("Date", value=date.today())
            actual_zoning = st.number_input("Actual Zoning", min_value=0.0, step=1.0)
            remarks = st.text_input("Remarks / Milestone (optional)")
            submitted = st.form_submit_button("Update Data", type="primary")
        if submitted:
            try:
                dl.update_scurve_daily_actual(project, report_date, actual_zoning, remarks)
                st.success(f"Saved actual zoning for {report_date.strftime('%d %b %Y')}.")
                st.rerun()
            except GSheetError as exc:
                st.error(str(exc))

    with col_milestone:
        st.markdown("##### 🏁 Milestone Tracker")
        milestones = df[df["Remarks"] != ""][["Date", "Remarks"]].sort_values("Date")
        if milestones.empty:
            st.info("No milestones recorded yet.")
        else:
            st.dataframe(
                milestones.rename(columns={"Date": "Date", "Remarks": "Remarks"})
                          .assign(Date=lambda d: d["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")),
                width="stretch", hide_index=True, height=320,
            )

    st.divider()

    # --- Progress Table ------------------------------------------------------
    st.markdown("##### 📋 Progress Table")
    table = df[["Date", "PlanZoning", "PlanPct_%", "ActualZoning", "ActualPct_%", "DeviationPct", "Remarks"]].copy()
    table.columns = ["Date", "Plan.day", "Plan Cum %", "Actual.day", "Actual Cum %", "Deviation %", "Remarks"]
    table["Date"] = table["Date"].dt.strftime("%Y-%m-%d 00:00:00")
    st.dataframe(table.tail(10), width="stretch", hide_index=True)
    st.download_button(
        "⬇️ Download CSV", data=table.to_csv(index=False).encode("utf-8"),
        file_name=f"{project.lower()}_scurve_progress.csv", mime="text/csv",
    )

    st.divider()

    # --- Zone / Kolom Progress -------------------------------------------------
    st.markdown("##### 🏗️ Zone / Kolom Progress")
    st.caption("Sourced from the columns beside 'Remarks' in the same source S-Curve tab.")

    try:
        zk_df = dl.load_zone_kolom(project)
    except GSheetError as exc:
        st.error(f"Couldn't load Zone/Kolom data: {exc}")
        zk_df = None

    level_tabs = st.tabs(config.ZONE_LEVELS)
    for level, tab in zip(config.ZONE_LEVELS, level_tabs):
        with tab:
            for metric_name in config.ZONE_METRICS:
                st.markdown(f"**{project} STRUCTURE — {metric_name} {level}**")
                img_path = config.DENAH_ASSETS.get(level, {}).get(metric_name)
                summary = dl.zone_kolom_summary(zk_df, level, metric_name) if zk_df is not None and not zk_df.empty else {}

                img_col, stat_col = st.columns([1, 1.2])
                with img_col:
                    if img_path and (config.BASE_DIR / img_path).exists():
                        st.image(str(config.BASE_DIR / img_path), width="stretch")
                    else:
                        st.info("Denah not available yet.")

                with stat_col:
                    if not summary:
                        st.info(f"No data yet for {level} - {metric_name}. Add it via the update form below.")
                    else:
                        st.caption(f"Cut off as of {summary['date'].strftime('%d %b %Y')}")
                        st.markdown(f"**TOTAL: {fmt_int(summary['done'])}/{fmt_int(summary['target'])} {metric_name.lower()} ({summary['pct']:.2f}%)**")
                        dcol, acol = st.columns(2)
                        with dcol:
                            st.markdown("**DAILY PROGRESS**")
                            st.caption(f"Previous: {fmt_int(summary['previous'])} {metric_name.lower()}")
                            st.caption(f"Current: {fmt_signed(summary['current_delta'], decimals=0, suffix='')} {metric_name.lower()}")
                            st.caption(f"Weekly (7 days): {fmt_signed(summary['weekly_delta'], decimals=0, suffix='')} {metric_name.lower()}")
                        with acol:
                            st.markdown("**ACCUMULATIVE PROGRESS**")
                            st.caption(f"Total: {fmt_int(summary['done'])}/{fmt_int(summary['target'])} {metric_name.lower()}")
                            st.caption(f"Remaining: {fmt_int(summary['remaining'])} {metric_name.lower()}")
                            st.caption(f"Percentage: {summary['pct']:.2f}%")
                st.markdown("")

    st.divider()

    # --- Update Daily Progress (Zone/Kolom) form -----------------------------
    with st.expander("✏️ Update Daily Progress (Zone/Kolom)"):
        with st.form("zone_kolom_form"):
            zc1, zc2 = st.columns(2)
            with zc1:
                level = st.selectbox("Level", config.ZONE_LEVELS)
            with zc2:
                metric_name = st.selectbox("Metric", config.ZONE_METRICS)
            done = st.number_input("Total Done (cumulative)", min_value=0.0, step=1.0)
            target = st.number_input("Total Target", min_value=0.0, step=1.0)
            update_date = st.date_input("Update Date", value=date.today(), key="zk_update_date")
            zk_submitted = st.form_submit_button("Save Progress", type="primary")
        if zk_submitted:
            try:
                dl.append_zone_kolom_update(project, level, metric_name, done, target, update_date)
                st.success(f"Saved {level} - {metric_name} progress for {update_date.strftime('%d %b %Y')}.")
                st.rerun()
            except GSheetError as exc:
                st.error(str(exc))
