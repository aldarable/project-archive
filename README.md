# DCI Project Monitoring System

A Streamlit dashboard for site progress (S-Curve), HSE manpower, document
control, HSE safety, and equipment monitoring — one project + chapter picker
at the top, editable data underneath.

## What was fixed

The app was crashing with an `IndentationError` because
`services/gsheet_client.py` had an empty `class GSheetError(RuntimeError):`
with no body. That's fixed, and the whole data layer has been rebuilt.

## What changed

- **Single data source.** Everything (S-Curve, Sumaraja vendor S-Curve, Zone/
  Kolom log, Manpower, Document Control) now reads from **one Google Sheet**
  mirroring `Project-Archive-3.xlsx`, via the `gcp_service_account` + `sheet_id`
  secrets you already configured on Streamlit Cloud. No more local CSVs.
- **Editable.** The Daily Report form, the Zone/Kolom "Update Daily Progress"
  form, and the Manpower "Input / Update Daily Data" form all write straight
  back to the Sheet (previously the app was view-only).
- **Sidebar** simplified to: About Dashboard, Version, Last Updated, PDF
  Report (a download button — drop your exported report at
  `assets/report.pdf` to enable it).
- **Top bar**: logo + "DCI PROJECT MONITORING SYSTEM" title, Project pills
  (JK5, JK6, JK7, JK8, H301, H302, GIS), Chapter pills (S-Curve, Manpower,
  Document, Safety, Equipment). Drop your DCI Indonesia logo at
  `assets/logo_dci.png` to replace the placeholder icon.
- **Chapter 1 (S-Curve)** now includes everything from your reference PDF:
  - KPI cards (Overall Target / Plan / Actual / Status)
  - one combined **Plan vs Actual vs Deviation** chart
  - a second **Sumaraja (vendor) weekly S-Curve** chart, parsed from the
    `-sri-scurve` tab
  - **Daily Report** form + **Milestone Tracker** table (from the `Remarks`
    column)
  - **Progress Table** with CSV download
  - **Zone / Kolom Progress** per level (GF / L1 / L2) with denah images,
    daily/weekly/accumulative stats
  - **Update Daily Progress** form for the Zone/Kolom log
- A parsing error in any one section (e.g. a malformed Sumaraja sheet) is now
  caught locally and shown as a warning — it no longer takes down the whole
  page like the old bug did.

## Google Sheet tab naming

One spreadsheet, one tab per project per chapter, named
`<project>-<chapter>` (lowercase project code), matching the source workbook:

```
jk7-scurve        Chapter 1 — daily zoning S-Curve (cols A:J) + Zone/Kolom log (cols L:P)
jk7-sri-scurve     Chapter 1 — Sumaraja vendor weekly work-item S-Curve
jk7-manpower       Chapter 2 — HSE Manpower
jk7-docon          Chapter 3 — Document Control
jk7-hse-safety     Chapter 4 — placeholder, not wired up yet
jk7-equipment      Chapter 5 — placeholder, not wired up yet
```

`jk7-scurve` columns, exactly as in the source file:

| A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Date | PlanZoning | PlanCum | PlanPct_% | ActualZoning | ActualCum | ActualPct_% | DevAbs_unit | DevPct_% | Remarks | *(spacer)* | Date Structure | Level | Metric | Done | Target |

To add a new project, add its 6 tabs (same layout) and add the project code
to `config.ACTIVE_PROJECTS`.

## Google Sheets access (already configured per your message)

Your service account needs **edit** access now (not just Viewer), since the
Daily Report / Update Progress forms write back to the sheet. Share the
Sheet with the service account's `client_email` as **Editor**. Secrets format
is unchanged — see `.streamlit/secret.toml.example`.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes / assumptions to double-check

- **Daily Report** updates the existing scheduled row for that date (it
  doesn't append a new one) — the sheet is pre-populated with future dates
  that already carry a Plan value and a blank Actual. If the date you pick
  isn't already a row, you'll get a clear error instead of a silent write to
  the wrong place.
- **Total zoning target** (used to turn cumulative Actual into a %) is
  derived from the sheet itself (`PlanCum ÷ PlanPct_%`), not hardcoded —
  double check the S-Curve chart matches your expectations after your first
  live update.
- **Sumaraja S-Curve** parser locates the row containing `W#1` and assumes a
  `Plan` row immediately followed by an `Actual` row for each work item, with
  weekly weighted values from column I onward. If Sumaraja's sheet layout
  changes, this section will show a warning instead of crashing — re-check
  `services/data_loader.py::load_sumaraja_scurve`.
