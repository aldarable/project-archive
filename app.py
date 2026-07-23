import streamlit as st

from config import *

from components.navbar import render_navbar

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

with open("assets/style.css") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

project, chapter = render_navbar()

st.session_state.project = project
st.session_state.chapter = chapter

if chapter == "S-Curve":
    from pages.chapter1_scurve import show
    show(project)

elif chapter == "Manpower":
    from pages.chapter2_manpower import show
    show(project)

elif chapter == "Document":
    from pages.chapter3_document import show
    show(project)

elif chapter == "Safety":
    from pages.chapter4_safety import show
    show(project)

else:
    from pages.chapter5_equipment import show
    show(project)
