"""
auth.py — Isolated Google Sheets authentication.

Only this module knows about service-account credentials. Every other module
gets a ready-to-use gspread client via get_gspread_client(), so swapping auth
strategy later (e.g. OAuth user login) only touches this file.
"""

from __future__ import annotations

import logging

import streamlit as st

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_gspread_client():
    """Return a cached, authorized gspread client using the service-account
    secret configured in `st.secrets["gcp_service_account"]`.

    Returns None if no credentials are configured (development/CSV mode),
    so callers should check config.DATA_MODE before calling this.
    """
    import gspread
    from google.oauth2.service_account import Credentials

    if "gcp_service_account" not in st.secrets:
        logger.warning("No gcp_service_account secret found; Google Sheets auth unavailable.")
        return None

    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        logger.exception("Failed to authorize Google Sheets client.")
        raise
