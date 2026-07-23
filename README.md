# Dashboard Monitoring JK7

One integrated Streamlit application replacing the two previous standalone
dashboards (S-Curve, HSE Manpower) plus a new Document Control chapter, with
Chapter 4 (HSE Safety) and Chapter 5 (Equipment Monitoring) as placeholders
for future data.

## Project structure

```
project/
├── app.py                 # sidebar navigation + page router only
├── config.py               # data mode switch, sheet/tab names, theme tokens
├── auth.py                  # isolated Google auth (single cached client)
├── utils.py                  # shared formatting + KPI card helpers
├── requirements.txt
├── pages/
│   ├── chapter1_scurve.py
│   ├── chapter2_hse.py
│   ├── chapter3_docon.py
│   ├── chapter4_hse_safety.py   (placeholder)
│   └── chapter5_equipment.py     (placeholder)
├── services/
│   ├── sheets.py           # data access layer (CSV dev / Google Sheets prod)
│   ├── zone_progress.py     # zone/kolom progress computation
│   └── charts.py             # reusable Plotly figure builders
├── css/style.css
├── data/                      # dev-mode CSVs only (see below)
└── assets/                    # site-plan images for the zone/kolom panels
```

## Data source: one Google Spreadsheet, five tabs

| Tab name | Chapter |
|---|---|
| `scurve-jk7` | 1 — contains **two tables side-by-side**: columns A:J = daily S-curve, columns K:O = zone/kolom progress |
| `hse-manpower` | 2 |
| `docon-jk7` | 3 |
| `hse-safety` | 4 (empty placeholder) |
| `equipment-jk7` | 5 (empty placeholder) |

## Running locally (development mode — CSV files)

```bash
pip install -r requirements.txt
streamlit run app.py
```

With no `secrets.toml` present, the app automatically uses the bundled CSVs
in `data/` — **for local testing only**, per project requirements. All
production reads/writes go to Google Sheets.

## Running in production (Google Sheets — single source of truth)

Create `.streamlit/secrets.toml`:

```toml
sheet_id = "YOUR_GOOGLE_SHEET_ID"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

Share the spreadsheet with the service account's `client_email` as **Editor**.

Once `sheet_id` and `gcp_service_account` are present, `config.DATA_MODE`
automatically switches to `"gsheets"` — no other code changes needed.

**Two-way sync:** reads are cached for 30 seconds, so edits made directly in
Google Sheets appear in the dashboard within that window (or immediately on
manual refresh). Writes made from the dashboard hit Google Sheets immediately
and clear the cache, so they appear right away for every viewer.

## Security note

⚠️ Never commit `.streamlit/secrets.toml` or any service-account JSON key to
version control — `.gitignore` already excludes it. If a key is ever
accidentally shared or exposed, rotate it immediately in Google Cloud
Console (IAM & Admin → Service Accounts → Keys).

## Still to build (next iteration)

- Export buttons: PDF (`services/export_pdf.py`), Excel, CSV (CSV already
  implemented per-chapter)
- Automated email report (`services/email_report.py`) via Gmail SMTP
- Chapter 4 (HSE Safety) and Chapter 5 (Equipment Monitoring) once their
  data sources are defined
