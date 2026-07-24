"""
chapters/chapter2_manpower.py for HSE Manpower Monitoring.

"""

from __future__ import annotations
import streamlit as st
import config
from services import data_loader as dl
from services.charts import category_trend_chart, single_line_chart
from services.gsheet_client import GSheetError
from utils import fmt_int, metric


def render(project: str) -> None:
    st.subheader("Structure Works")
    st.title("HSE Manpower")

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
