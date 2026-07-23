"""pages/chapter5_equipment.py — Placeholder page (no data yet)."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.markdown(
        """
        <div class="coming-soon">
            <div class="emoji">🚜</div>
            <h2>Coming Soon</h2>
            <p>Equipment Monitoring Dashboard</p>
            <p style="font-size:0.85rem;">Data source will be added later.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
