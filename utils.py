"""
utils.py — Small, dependency-free helpers shared across chapters.
"""

from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert a hex color (#RRGGBB) to a valid rgba(...) string for Plotly."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def fmt_pct(value: float | None, decimals: int = 1) -> str:
    """Format a number as a percentage string, or '-' if missing."""
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}%"


def fmt_signed(value: float | None, decimals: int = 1, suffix: str = "%") -> str:
    """Format a number with an explicit +/- sign, or '-' if missing."""
    if value is None or pd.isna(value):
        return "-"
    return f"{value:+.{decimals}f}{suffix}"


def fmt_int(value: float | None) -> str:
    """Format a number as a thousands-separated integer, or '-' if missing."""
    if value is None or pd.isna(value):
        return "-"
    return f"{int(value):,}".replace(",", ".")


def load_css(css_path: Path) -> None:
    """Inject the shared stylesheet into the current Streamlit page."""
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str | None = None, accent: str = "#8FB8E8") -> str:
    """Return HTML for one soft, rounded KPI card (used via st.markdown)."""
    delta_html = f'<div class="kpi-delta">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card" style="--accent:{accent};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def status_badge(label: str, color: str) -> str:
    """Return HTML for a soft status pill badge."""
    return f"""
    <div class="status-badge" style="--badge-color:{color};">
        <div class="status-badge-label">STATUS</div>
        <div class="status-badge-value">{label}</div>
    </div>
    """


def image_to_base64(image_path: Path) -> str | None:
    """Read an image file and return a base64 data URI, or None if missing/unreadable."""
    if not image_path.exists():
        return None
    try:
        data = image_path.read_bytes()
        ext = image_path.suffix.lstrip(".").lower()
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None
