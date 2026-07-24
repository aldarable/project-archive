"""
chapters/chapter2_manpower.py for HSE Manpower Monitoring.

"""

from __future__ import annotations
from datetime import date
import streamlit as st
import config
from services import data_loader as dl
from services.charts import category_trend_chart, single_line_chart
from services.gsheet_client import GSheetError
from utils import fmt_int, metric


def render(project: str) -> None:
    st.subheader(f"{project} STRUCTURE WORKS")
    st.title("👷 HSE Manpower Monitoring")

    try:
        df = dl.load_manpower(project)
    except GSheetError as exc:
        st.error(f"Couldn't load HSE Manpower from Google Sheets: {exc}")
        return

    if df.empty:
        st.info("No manpower data available yet for this project.")
        return

    last_row = df.iloc[-1]
    st.caption(f"Last update — {last_row['date'].strftime('%d %B %Y')} · {len(df)} days recorded")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric("Total Manpower (Today)", fmt_int(last_row["Total"]), config.COLORS["plan"])
    with c2:
        metric("30-Day Average", fmt_int(df["Total"].tail(30).mean()), config.COLORS["purple"])
    with c3:
        metric("Manhours (Today)", fmt_int(last_row["Manhours"]), config.COLORS["actual"])
    with c4:
        metric("Total Manhours (Period)", fmt_int(df["Manhours"].sum()), config.COLORS["pink"])

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Small Teams — HSE, K2, Tim Baja, Tim Bobok, Tim Cor")
        st.plotly_chart(
            category_trend_chart(df, config.MANPOWER_SMALL, config.MANPOWER_COLORS),
            width="stretch", config={"displayModeBar": False},
        )
    with col_b:
        st.markdown("##### Large Teams — Tim Besi, Tim Begisting")
        st.plotly_chart(
            category_trend_chart(df, config.MANPOWER_LARGE, config.MANPOWER_COLORS),
            width="stretch", config={"displayModeBar": False},
        )

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("##### Total Manpower")
        st.plotly_chart(
            single_line_chart(df, "Total", config.MANPOWER_COLORS["Total"]),
            width="stretch", config={"displayModeBar": False},
        )
    with col_d:
        st.markdown("##### Manhours")
        st.plotly_chart(
            single_line_chart(df, "Manhours", config.MANPOWER_COLORS["Manhours"]),
            width="stretch", config={"displayModeBar": False},
        )

    st.divider()

    with st.expander("✏️ Input / Update Daily Data"):
        with st.form("manpower_form"):
            row_date = st.date_input("Date", value=date.today())
            cols = st.columns(3)
            values = {}
            for i, cat in enumerate(config.MANPOWER_CATEGORIES):
                with cols[i % 3]:
                    values[cat] = st.number_input(cat, min_value=0.0, step=1.0)
            manhours = st.number_input("Manhours (optional — auto-estimated if left at 0)", min_value=0.0, step=1.0)
            if manhours:
                values["Manhours"] = manhours
            submitted = st.form_submit_button("Update Data", type="primary")
        if submitted:
            try:
                dl.append_manpower_row(project, row_date, values)
                st.success(f"Saved manpower data for {row_date.strftime('%d %b %Y')}.")
                st.rerun()
            except GSheetError as exc:
                st.error(str(exc))

    with st.expander("📄 View / Download Full Data"):
        st.dataframe(df, width="stretch", hide_index=True)
        st.download_button(
            "⬇️ Download CSV", data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{project.lower()}_manpower.csv", mime="text/csv",
        )
