import streamlit as st


def kpi(title,value,delta=None):
    html=f"""

<div class="card">
<div class="title">
{title}
</div>
<div class="value">
{value}
</div>

"""
    if delta is not None:
        color="#22C55E"
        if "-" in str(delta):
            color="#EF4444"
        html+=f"""

<div style="color:{color};">
{delta}
</div>
"""

    html+="</div>"
    st.markdown(html,unsafe_allow_html=True)
