"""
app.py — DCI Project Monitoring System, entry point.
"""

from __future__ import annotations
import streamlit as st
import config
from chapters._placeholder import coming_soon
from utils import load_css

st.set_page_config(
    page_title="DCI Project Monitoring System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css(config.BASE_DIR / "css" / "style.css")



# Sidebar
with st.sidebar:
    st.markdown("### ℹ️ About Dashboard")
    st.caption(
        "Site progress, manpower, document control, HSE Safety, and Equipment "
        "monitoring for DCI Indonesia project sites."
    )
    st.markdown(f"**Version**  \n{config.APP_VERSION}")
    st.markdown(f"**Last Updated**  \n{config.LAST_UPDATED}")

    if config.PDF_REPORT_PATH.exists():
        with open(config.PDF_REPORT_PATH, "rb") as f:
            st.download_button(
                "📄 PDF Report", data=f.read(),
                file_name=config.PDF_REPORT_PATH.name, mime="application/pdf",
                width="stretch",
            )
    else:
        st.button("📄 PDF Report", disabled=True, width="stretch",
                   help="Drop the report file at assets/report.pdf to enable this.")

    st.divider()
    st.markdown("**Legend**")
    st.markdown(
        f"""
        <div style="font-size:0.85rem; line-height:2;">
        <span style="color:{config.COLORS['plan']};">●</span> Plan &nbsp;
        <span style="color:{config.COLORS['actual']};">●</span> Actual &nbsp;
        <span style="color:{config.COLORS['deviation']};">●</span> Deviation
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("Data source: Google Sheet (Project-Archive), editable directly from this app.")

    st.caption(f"Version : {APP_VERSION}")
    st.caption(f"Last Data Update : {last_data_update}")   # dari Google Sheets
    st.caption(f"Last Code Update : {LAST_CODE_UPDATE}")   # dari GitHub



# Top bar
logo_col, title_col = st.columns([1, 9])
with logo_col:
    if config.LOGO_PATH.exists():
        st.image(str(config.LOGO_PATH), width=64)
    else:
        st.markdown("<div style='font-size:2.2rem;'>🏢</div>", unsafe_allow_html=True)
with title_col:
    st.markdown(
        f"<div style='font-size:1.4rem; font-weight:800; letter-spacing:0.02em; padding-top:0.3rem;'>{config.APP_TITLE}</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    "<div style='font-size:0.78rem; opacity:0.55; text-transform:uppercase; letter-spacing:0.06em; margin-top:0.6rem;'>Project</div>",
    unsafe_allow_html=True,
)
project = st.pills(
    "Project", config.PROJECTS, default="JK7",
    label_visibility="collapsed", key="project_pill",
)
project = project or "JK7"

st.markdown(
    "<div style='font-size:0.78rem; opacity:0.55; text-transform:uppercase; letter-spacing:0.06em; margin-top:0.4rem;'>Chapter</div>",
    unsafe_allow_html=True,
)
chapter_labels = list(config.CHAPTERS.values())
chapter_choice = st.pills(
    "Chapter", chapter_labels, default=chapter_labels[0],
    label_visibility="collapsed", key="chapter_pill",
)
chapter_choice = chapter_choice or chapter_labels[0]
chapter = next(k for k, v in config.CHAPTERS.items() if v == chapter_choice)

st.divider()


# Routing
if project not in config.ACTIVE_PROJECTS:
    st.subheader(f"{project} STRUCTURE WORKS")
    st.title(config.CHAPTERS.get(chapter, ""))
    coming_soon(f"{project} Dashboard", "🏗️")
else:
    if chapter == "1":
        from chapters.chapter1_scurve import render
    elif chapter == "2":
        from chapters.chapter2_manpower import render
    elif chapter == "3":
        from chapters.chapter3_docon import render
    elif chapter == "4":
        from chapters.chapter4_safety import render
    else:
        from chapters.chapter5_equipment import render

    render(project)
