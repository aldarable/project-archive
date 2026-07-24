"""
services/gsheet_client.py for Google Sheets read-only access.

COPY THIS SECRET AND FILL THE CREDENTIALS.

    sheet_id = "..."

    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = \"\"\"-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----\"\"\"
    client_email = "...@....iam.gserviceaccount.com"
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "..."
    universe_domain = "googleapis.com"
    
"""

from __future__ import annotations
import pandas as pd
import streamlit as st
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GSheetError(RuntimeError):


@st.cache_resource(show_spinner=False)
def _get_client():
    import gspread
    from google.oauth2.service_account import Credentials

    if "gcp_service_account" not in st.secrets or "sheet_id" not in st.secrets:
        raise GSheetError(
            "Google Sheets is not configured — add `sheet_id` and "
            "`[gcp_service_account]` to your Streamlit secrets."
        )
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    return gspread.authorize(creds)


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def read_tab(tab_name: str) -> pd.DataFrame:
    try:
        client = _get_client()
        sheet_id = st.secrets["sheet_id"]
        sh = client.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        records = ws.get_all_records()
        return pd.DataFrame(records)
    except GSheetError:
        raise
    except Exception as exc:  # noqa: BLE001 — surface as a single friendly type
        raise GSheetError(f"Couldn't read tab '{tab_name}': {exc}") from exc
