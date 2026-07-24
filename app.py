"""
app.py for Project Monitoring Dashboard entry point.

"""

from __future__ import annotations
import streamlit as st
import config
from chapters._placeholder import coming_soon

st.set_page_config(
    page_title="Project Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Sidebar
with st.sidebar:
    st.markdown("## 📊 Monitoring Dashboard")
    st.caption("Site progress, manpower, document control, HSE Safety, and Equipment at a glance.")
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
    st.caption("Data source: CSV files maintained by the project team.")
    st.caption("This app is view-only — edit the source files to update figures.")


# Top bar — Project + Chapter selection
st.markdown(
    "<div style='font-size:0.78rem; opacity:0.55; text-transform:uppercase; letter-spacing:0.06em;'>Project</div>",
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
chapter_labels = [f"{k} · {v}" for k, v in config.CHAPTERS.items()]
chapter_choice = st.pills(
    "Chapter", chapter_labels, default=chapter_labels[0],
    label_visibility="collapsed", key="chapter_pill",
)
chapter = (chapter_choice or chapter_labels[0]).split(" · ")[0]

st.divider()


# Routing
if project not in config.ACTIVE_PROJECTS:
    st.subheader("Structure Works")
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
