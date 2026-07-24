# Project Monitoring Dashboard

A clean, minimalist Streamlit dashboard for site progress, HSE manpower, and
document control monitoring. **View-only** app — there is no data-entry UI.
Two different data sources, by design:

- **Chapter 1 (S-Curve)** — static local files under `data/<project>/`,
  generated once from the vendor's own weekly S-Curve Excel report. Update
  by re-generating these files when a new report comes in.
- **Chapters 2-3 (HSE Manpower, Document Control)** — live from a **Google
  Sheet**, one worksheet tab per chapter. Edit the Sheet and the dashboard
  reflects it on next load (cache TTL: 60s). No local files, no GitHub
  commits needed for these two.

## Structure

```
app.py                        # top bar (Project + Chapter) + routing only
config.py                     # projects, chapters, colors, field mappings, gsheet tab names
utils.py                      # formatting + minimal metric-card helper
services/
  data_loader.py              # data access (cached) — CSV for Ch.1, Sheets for Ch.2-3
  gsheet_client.py            # gspread auth + cached tab reader (creds via st.secrets)
  charts.py                   # Plotly figure builders (theme-adaptive)
chapters/
  chapter1_scurve.py          # S-Curve (Plan/Actual/Deviation) + Work Breakdown
  chapter2_manpower.py        # HSE Manpower (4 focused charts)
  chapter3_docon.py           # Document Control (Overall / Vendor / PMO)
  chapter4_safety.py          # placeholder — coming soon
  chapter5_equipment.py       # placeholder — coming soon
  _placeholder.py             # shared "coming soon" block
data/
  jk7/
    scurve_main.csv           # weekly Plan vs Actual cumulative % (S-Curve report)
    scurve_workbreakdown.csv  # per work-package: weight + % of own scope done
    scurve_meta.json          # report header (contractor, week, last updated)
.streamlit/
  secrets.toml.example        # template — copy to secrets.toml and fill in your own creds
requirements.txt
```

## Top bar

- **Project**: JK5DH3, JK6DH3, JK7, JK8, H301, H302, GIS — only **JK7** has
  live data today; the rest show a "Coming Soon" placeholder. Add a project by
  adding local S-Curve files (Chapter 1) and adding the project name to
  `config.ACTIVE_PROJECTS`.
- **Chapter**: 1 S-Curve, 2 HSE Manpower, 3 Document Control (all live),
  4 HSE Safety, 5 Equipment (both placeholders for now).

## Theme

No custom theme is injected — Streamlit's native light/dark toggle (⋮ menu,
top right) controls the whole app. Only chart colors are fixed, since they
need to stay meaningful regardless of theme:

- **Plan** → blue
- **Actual** → amber
- **Deviation** → red (always — a deviation chart is a warning signal)
- Small purple / pink / teal accents used for secondary KPIs and categories.

## Setting up Google Sheets (Chapters 2 & 3)

1. **Rotate any credentials that have ever been pasted into chat, a doc, or
   a screenshot.** In Google Cloud Console → IAM & Admin → Service Accounts,
   delete the old key and generate a fresh one. Never treat a key that's
   been shared outside the console as safe to keep using.
2. Share your Google Sheet with the service account's `client_email`
   (Viewer access is enough — the app only reads).
3. In the Sheet, make two tabs (default names below — change in
   `config.GSHEET_TABS` if yours differ):
   - **`HSE_Manpower`** — same columns as before: `Date, HSE, K2, Tim Besi,
     Tim Baja, Tim Begisting, Tim Bobok, Tim Cor, Total, Manhours`. Add a
     `Project` column if you'll eventually track more than one project in
     the same tab; omit it while it's JK7-only.
   - **`Document_Control`** — same columns as before: `VENDOR, Total
     Deliverable, Submitted [Vendor], ...` (see `config.DOCON_FIELD_MAP`
     for the full list). Same optional `Project` column.
4. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   locally and fill in your **new, rotated** service account JSON + your
   sheet ID. This file is git-ignored — never commit it.
5. Deploying on Streamlit Community Cloud: don't upload a secrets.toml at
   all. Paste the same TOML content into the app's **Settings → Secrets**
   box in the Cloud dashboard.

If Sheets access fails (missing secret, sheet not shared, wrong tab name),
Chapters 2 and 3 show a plain error message in the page instead of crashing
the whole app — Chapter 1 keeps working regardless, since it's local.

## Data notes — S-Curve (Chapter 1)

`scurve_main.csv` and `scurve_workbreakdown.csv` are built from the vendor's
own **"WEEKLY S-CURVE PROGRESS REPORT"** (PT. Sumaraja Indah, Structure
scope, JK7 — currently at Week 9, last updated 23 July 2026):

- `scurve_main.csv` — one row per week (25 weeks, W#1–W#25), with the
  report's own cumulative Plan % and cumulative Actual % (`PlanCumPct_%`,
  `ActualCumPct_%`). Weeks beyond the latest report (W#10 onward) carry a
  Plan value but a blank Actual — that's what makes the Actual line stop at
  the current week and the Plan line keep going. **Deviation** is always
  recomputed in-app as `Actual − Plan` (signed), so it's never trusted
  blindly from the sheet and always resolves to blank for future weeks.
- `scurve_workbreakdown.csv` — one row per work package (Preliminaries,
  Foundation, Ground Floor, 1st–3rd Roof Floor, Stair, water tanks, etc.),
  with each package's weight (`LoadPct`, its share of the total project) and
  how much of its **own** scope is actually complete (`ActualPct`), derived
  by summing the vendor's weekly actual entries for that package and
  dividing by its total weight.
- `scurve_meta.json` — small header block (contractor, service scope, week
  label, report date) shown as a caption above the KPI cards.

To refresh this chapter next week, re-derive these same 3 files from the
updated vendor report — this chapter stays local/static by design, separate
from the Sheets-backed chapters.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Adding a new project or chapter

1. Chapter 1: create `data/<project>/` with the 3 S-Curve files.
2. Chapters 2-3: add a `Project` column to the Sheet tabs if not already
   present, and make sure your new project's rows use a matching value.
3. Add the project name to `config.ACTIVE_PROJECTS`.
4. For a new chapter, add it to `config.CHAPTERS` / `config.ACTIVE_CHAPTERS`
   and create `chapters/chapterN_xxx.py` with a `render(project: str)` function.
