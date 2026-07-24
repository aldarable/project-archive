"""chapters/_placeholder.py — Shared 'coming soon' block for unbuilt chapters."""

from __future__ import annotations
import streamlit as st

def coming_soon(title: str, emoji: str = "🕓") -> None:
    st.markdown(
        f"""
        <div style="text-align:center; padding:3.5rem 1rem; border:1px dashed rgba(128,128,128,0.35); border-radius:16px;">
            <div style="font-size:2.6rem;">{emoji}</div>
            <h3 style="margin:0.5rem 0 0.2rem 0;">Coming Soon</h3>
            <p style="opacity:0.65; margin:0;">{title}</p>
            <p style="opacity:0.5; font-size:0.85rem; margin-top:0.4rem;">Data source to be added.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
