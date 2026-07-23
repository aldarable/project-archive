import streamlit as st
from config import *
from components.navbar import navbar

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

with open("assets/style.css") as css:
    st.markdown(
        f"<style>{css.read()}</style>",
        unsafe_allow_html=True
    )

project, chapter = navbar()

if chapter == "S-Curve":
    from pages.chapter1_scurve import render
    render(project)
elif chapter == "Manpower":
    from pages.chapter2_manpower import render
    render(project)
elif chapter == "Document":
    from pages.chapter3_document import render
    render(project)
elif chapter == "Safety":
    from pages.chapter4_safety import render
    render(project)
else:
    from pages.chapter5_equipment import render
    render(project)
