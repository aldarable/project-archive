"""
services/gsheet_client.py — Google Sheets read/write access.

The dashboard's data source is a single Google Sheet (exported from
Project-Archive-3.xlsx), one worksheet tab per project per chapter
(see config.gsheet_tab). Reads are cached for CACHE_TTL_SECONDS; writes
go straight through and then clear the relevant cache so the next read
picks up the change immediately.

COPY THIS SECRET AND FILL THE CREDENTIALS into .streamlit/secrets.toml:

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

# Read+write scope — the app can now edit the sheet (Daily Report / Zone-Kolom
# update forms), so this is no longer read-only.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GSheetError(RuntimeError):
    """Raised whenever the Google Sheet can't be reached, is misconfigured,
    or a requested tab/row can't be found."""


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


def _get_worksheet(tab_name: str):
    try:
        client = _get_client()
        sheet_id = st.secrets["sheet_id"]
        sh = client.open_by_key(sheet_id)
        return sh.worksheet(tab_name)
    except GSheetError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise GSheetError(f"Couldn't open tab '{tab_name}': {exc}") from exc


def _dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for i, h in enumerate(headers):
        h = (h or "").strip() or f"col_{i}"
        if h in seen:
            seen[h] += 1
            h = f"{h}_{seen[h]}"
        else:
            seen[h] = 0
        out.append(h)
    return out


@st.cache_data(ttl=config.CACHE_TTL_SECONDS, show_spinner=False)
def read_tab(tab_name: str) -> pd.DataFrame:
    """Read a whole worksheet tab as a DataFrame, raw values (no formatting),
    tolerant of blank/duplicate header cells (the source workbook has a
    spacer column between the daily S-Curve block and the Zone/Kolom log)."""
    try:
        ws = _get_worksheet(tab_name)
        values = ws.get_all_values(value_render_option="UNFORMATTED_VALUE")
    except GSheetError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise GSheetError(f"Couldn't read tab '{tab_name}': {exc}") from exc

    if not values:
        return pd.DataFrame()

    headers = _dedupe_headers(values[0])
    rows = values[1:]
    # Pad/truncate every row to the header width so DataFrame() doesn't choke
    # on ragged rows (common when only part of the sheet is filled in).
    fixed_rows = [r + [""] * (len(headers) - len(r)) if len(r) < len(headers) else r[: len(headers)] for r in rows]
    return pd.DataFrame(fixed_rows, columns=headers)


def _col_letter(n: int) -> str:
    """1-indexed column number -> spreadsheet column letter."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def find_next_empty_row(tab_name: str, col_index: int, header_row: int = 1) -> int:
    """Return the 1-indexed row number of the first empty cell in the given
    column, scanning below header_row. col_index is 1-indexed."""
    ws = _get_worksheet(tab_name)
    values = ws.col_values(col_index, value_render_option="UNFORMATTED_VALUE")
    return max(len(values), header_row) + 1


def find_row_by_column_value(tab_name: str, col_index: int, value: str, header_row: int = 1) -> int | None:
    """Return the 1-indexed row number where the given column matches value
    (string-compared), or None if not found."""
    ws = _get_worksheet(tab_name)
    values = ws.col_values(col_index, value_render_option="UNFORMATTED_VALUE")
    for i, v in enumerate(values):
        if i < header_row:
            continue
        if str(v).strip() == str(value).strip():
            return i + 1
    return None


def write_row_range(tab_name: str, row: int, start_col: int, values: list) -> None:
    """Write a list of values into a single row, starting at start_col
    (1-indexed), then clear the read cache for this tab."""
    try:
        ws = _get_worksheet(tab_name)
        start = _col_letter(start_col)
        end = _col_letter(start_col + len(values) - 1)
        ws.update(f"{start}{row}:{end}{row}", [values])
    except GSheetError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise GSheetError(f"Couldn't write to tab '{tab_name}': {exc}") from exc
    finally:
        read_tab.clear()
