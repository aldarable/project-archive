"""
pages/chapter3_docon.py — Document Control JK7 dashboard.

Three sections: Overall Status, Vendor Submission, PMO Review.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from services import sheets
from services.charts import docon_summary_bar_chart, bar_by_category_chart
from utils import kpi_card, fmt_int


def render() -> None:
    st.title("📄 Document Control JK7")

    try:
        df = sheets.load_docon()
    except Exception as e:
        st.error(f"Could not load Document Control data: {e}")
        return

    if df.empty:
        st.info("No document control data available yet.")
        return

    with st.expander("🔎 Filters", expanded=False):
        vendor_filter = st.multiselect("Vendor", df["VENDOR"].tolist(), default=df["VENDOR"].tolist())

    filtered = df[df["VENDOR"].isin(vendor_filter)] if vendor_filter else df

    # =========================================================================
    # SECTION 1 — Overall Status
    # =========================================================================
    st.header("1️⃣ Overall Status")

    summary = {
        config.DOCON_FIELD_MAP[col]: int(filtered[col].sum())
        for col in config.DOCON_FIELD_MAP if col in filtered.columns
    }

    cols = st.columns(4)
    accents = [config.THEME["blue"], config.THEME["purple"], config.THEME["pink"], config.THEME["amber"]]
    key_metrics = ["Total Deliverables", "Submitted by Vendor", "Not Yet Review", "Vendor Overdue"]
    for i, label in enumerate(key_metrics):
        with cols[i % 4]:
            st.markdown(kpi_card(label, fmt_int(summary.get(label, 0)), accent=accents[i % 4]), unsafe_allow_html=True)

    st.markdown("###### Review Status Breakdown")
    review_cols = st.columns(5)
    review_labels = ["A - Approved", "B - Approved w/ Note", "C - Rejected", "D - Information Only", "In Review"]
    for i, label in enumerate(review_labels):
        with review_cols[i]:
            st.markdown(kpi_card(label, fmt_int(summary.get(label, 0)), accent=accents[i % 4]), unsafe_allow_html=True)

    st.markdown("###### Summary Table")
    summary_table = pd.DataFrame([summary])
    st.dataframe(summary_table, hide_index=True, use_container_width=True)

    st.plotly_chart(docon_summary_bar_chart(summary), use_container_width=True)

    st.divider()

    # =========================================================================
    # SECTION 2 — Vendor Submission
    # =========================================================================
    st.header("2️⃣ Vendor Submission")

    vs_cols = ["Total Deliverable", "Submitted [Vendor]", "Not Yet Review", "Overdue [Vendor Submit]"]
    vs_totals = {config.DOCON_FIELD_MAP[c]: int(filtered[c].sum()) for c in vs_cols if c in filtered.columns}

    kcols = st.columns(4)
    for i, (label, value) in enumerate(vs_totals.items()):
        with kcols[i]:
            st.markdown(kpi_card(label, fmt_int(value), accent=accents[i % 4]), unsafe_allow_html=True)

    submitted_pct = (vs_totals.get("Submitted by Vendor", 0) / vs_totals.get("Total Deliverables", 1) * 100) if vs_totals.get("Total Deliverables") else 0
    st.caption(f"Vendor submission completion: **{submitted_pct:.1f}%** of total deliverables")

    vendor_vs_df = filtered[["VENDOR"] + vs_cols].rename(columns=config.DOCON_FIELD_MAP)
    st.plotly_chart(
        bar_by_category_chart(vendor_vs_df["VENDOR"].tolist(), vendor_vs_df["Submitted by Vendor"].tolist(), config.THEME["blue"], title_y="Submitted by Vendor"),
        use_container_width=True,
    )
    st.markdown("###### Summary Table")
    st.dataframe(vendor_vs_df, hide_index=True, use_container_width=True)

    st.divider()

    # =========================================================================
    # SECTION 3 — PMO Review
    # =========================================================================
    st.header("3️⃣ PMO Review")

    pmo_cols = ["Submitted [Vendor]", "Completed [PMO Review]", "In Progress [PMO Review]", "Overdue [PMO Review]"]
    pmo_totals = {config.DOCON_FIELD_MAP[c]: int(filtered[c].sum()) for c in pmo_cols if c in filtered.columns}

    kcols2 = st.columns(4)
    for i, (label, value) in enumerate(pmo_totals.items()):
        with kcols2[i]:
            st.markdown(kpi_card(label, fmt_int(value), accent=accents[i % 4]), unsafe_allow_html=True)

    vendor_pmo_df = filtered[["VENDOR"] + pmo_cols].rename(columns=config.DOCON_FIELD_MAP)
    st.plotly_chart(
        bar_by_category_chart(
            vendor_pmo_df["VENDOR"].tolist(), vendor_pmo_df["Completed PMO Review"].tolist(),
            config.THEME["green"], horizontal=True, title_y="Completed PMO Review",
        ),
        use_container_width=True,
    )
    st.markdown("###### Summary Table")
    st.dataframe(vendor_pmo_df, hide_index=True, use_container_width=True)

    st.divider()
    st.download_button(
        "⬇️ Download Full Data (CSV)", data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="docon_jk7.csv", mime="text/csv",
    )
