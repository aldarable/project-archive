from streamlit_navigation_bar import st_navbar
from config import PROJECTS, CHAPTERS


def navbar():
    st_navbar(
        [],
        styles={
            "nav":{
                "background-color":"transparent",
                "justify-content":"center",
                "padding":"0rem"
            }
        }
    )
  
    import streamlit as st

    left,right = st.columns([7,1])

    with left:

        st.markdown("""
        <h1 style="margin-bottom:-5px;">
        📊 DCI Project Monitoring System
        </h1>

        <p style="
        color:gray;
        margin-top:0;
        ">
        Project Progress Monitoring Dashboard
        </p>
        """,unsafe_allow_html=True)
          
    with right:
        st.caption("Version")
        st.write("v2.0")
    project = st.segmented_control(
        "Project",
        PROJECTS,
        default="JK7"
    )
    chapter = st.segmented_control(
        "Chapter",
        CHAPTERS,
        default="S-Curve"
    )
    st.divider()
    return project,chapter
