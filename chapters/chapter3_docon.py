"""
chapters/chapter3_docon.py for Document Control.

"""

from __future__ import annotations
import streamlit as st
import config
from services import data_loader as dl
from services.charts import docon_grouped_bar
from services.gsheet_client import GSheetError
from utils import fmt_int, metric


def _totals(df, fields: list[str]) -> dict[str, int]:
    return {config.DOCON_FIELD_MAP[f]: int(df[f].sum()) for f in fields if f in df.columns}


def render(project: str) -> None:
    st.subheader(f"{project} STRUCTURE WORKS")
    st.title(f"📄 Document Control {project}")

    try:
        df = dl.load_docon(project)
    except GSheetError as exc:
        st.error(f"Couldn't load Document Control from Google Sheets: {exc}")
        return

    if df.empty:
        st.info("No document control data available yet for this project.")
        return

    vendors = df["VENDOR"].tolist()


    # Overall Status
    st.markdown("### Overall Status")

    overall = _totals(df, config.DOCON_OVERALL_FIELDS)
    top_labels = ["Total Deliverables", "Submitted by Vendor", "Pending (Not Yet Review)", "Overdue"]
    accents = [config.COLORS["plan"], config.COLORS["actual"], config.COLORS["purple"], config.COLORS["deviation"]]
    cols = st.columns(4)
    for col, label, accent in zip(cols, top_labels, accents):
        with col:
            metric(label, fmt_int(overall.get(label, 0)), accent)

    review_labels = ["Approved", "Approved w/ Note", "Rejected", "For Information Only", "In Review"]
    rcols = st.columns(5)
    for col, label in zip(rcols, review_labels):
        with col:
            metric(label, fmt_int(overall.get(label, 0)), config.COLORS["teal"])

    series = {config.DOCON_FIELD_MAP[f]: df[f].tolist() for f in config.DOCON_OVERALL_FIELDS if f in df.columns}
    st.plotly_chart(
        docon_grouped_bar(vendors, series, config.CATEGORICAL_PALETTE, height=440),
        width="stretch", config={"displayModeBar": False},
    )

    st.divider()



    # Vendor Submission Status
    st.markdown("### Vendor Submission Status")

    vs = _totals(df, config.DOCON_VENDOR_FIELDS)
    submitted_pct = (vs.get("Submitted by Vendor", 0) / vs.get("Total Deliverables", 1) * 100) if vs.get("Total Deliverables") else 0
    cols2 = st.columns(4)
    for col, label, accent in zip(cols2, top_labels, accents):
        with col:
            metric(label, fmt_int(vs.get(label, 0)), accent)
    st.caption(f"Vendor submission completion: **{submitted_pct:.1f}%** of total deliverables")

    series_vs = {config.DOCON_FIELD_MAP[f]: df[f].tolist() for f in config.DOCON_VENDOR_FIELDS if f in df.columns}
    st.plotly_chart(
        docon_grouped_bar(vendors, series_vs, config.CATEGORICAL_PALETTE, height=380),
        width="stretch", config={"displayModeBar": False},
    )

    st.divider()



    # PMO Review Status
    st.markdown("### PMO Review Status")

    pmo = _totals(df, config.DOCON_PMO_FIELDS)
    pmo_labels = ["Submitted by Vendor", "Completed (PMO Review)", "In Progress (PMO Review)", "Overdue (PMO Review)"]
    pmo_accents = [config.COLORS["actual"], config.COLORS["on_track"], config.COLORS["purple"], config.COLORS["deviation"]]
    cols3 = st.columns(4)
    for col, label, accent in zip(cols3, pmo_labels, pmo_accents):
        with col:
            metric(label, fmt_int(pmo.get(label, 0)), accent)

    series_pmo = {config.DOCON_FIELD_MAP[f]: df[f].tolist() for f in config.DOCON_PMO_FIELDS if f in df.columns}
    st.plotly_chart(
        docon_grouped_bar(vendors, series_pmo, config.CATEGORICAL_PALETTE, height=380),
        width="stretch", config={"displayModeBar": False},
    )

    st.divider()
    st.download_button(
        "⬇️ Download Full Data (CSV)", data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{project.lower()}_document_control.csv", mime="text/csv",
    )
