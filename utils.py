"""
utils.py for helpers shared across chapters.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st


def fmt_pct(value: float | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "–"
    return f"{value:.{decimals}f}%"


def fmt_signed(value: float | None, decimals: int = 1, suffix: str = "%") -> str:
    if value is None or pd.isna(value):
        return "–"
    return f"{value:+.{decimals}f}{suffix}"


def fmt_int(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "–"
    return f"{int(round(value)):,}"


def load_css(css_path) -> None:
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def metric(label: str, value: str, accent: str, delta: str | None = None) -> None:
    delta_html = f'<div style="font-size:0.78rem;opacity:0.65;margin-top:2px;">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div style="border-left:3px solid {accent}; padding:2px 0 2px 12px; margin-bottom:4px;">
            <div style="font-size:0.74rem; opacity:0.6; text-transform:uppercase; letter-spacing:0.04em;">{label}</div>
            <div style="font-size:1.5rem; font-weight:700; line-height:1.25;">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
