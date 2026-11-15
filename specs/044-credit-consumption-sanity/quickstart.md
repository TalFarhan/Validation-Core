# Quickstart: Credit Consumption Dashboard UI Sanity

## What this slice does

Adds page-object readers and a sanity suite for the Credit Consumption report:

- Screen 1 KPIs, four daily-trend toggle combinations (Show as a table), authority chart.
- Screen 2 export matrix.
- Fixture applies `active_filters` from `data/credit/db_sanity_purim2026.yaml` (`פורים 2026`).
- Bilingual `.or_()` locators for page navigation and date fields so English chrome does not
  raise `LoadTimeoutError`.

## Prerequisites

- Portal auth configured (the UI/sanity tests open the live Power BI report).
- Python env with `pytest`, `PyYAML`, Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.

## Files you will touch

- `pages/credit_consumption/credit_consumption_page.py` — class `CreditConsumptionPage`
  (popup dismiss + Screen 1/2 readers, bilingual locators, toggles, Show-as-a-table).
- `pages/credit_consumption/page.py` — re-export the class for the smoke conftest.
- `tests/sanity/credit_consumption_dashboard/conftest.py` — fixture.
- `tests/sanity/credit_consumption_dashboard/test_data_validation.py` — golden assertions.
- `docs/COVERAGE_CATALOG.md` — credit YAML ↔ method rows.

Live-copied during implementation (not guessed here): KPI titles other than
`ממוצע הוצאות לקנייה בשגרה`, toggle accessible names, slicer `role_name`s, trend/authority
chart titles, export column headers.

## Do NOT touch

- `core/portal/`, `core/components/`.
- Any alerts (`pages/alerts_analysis/`, `tests/**/alerts_analysis_dashboard/`),
  status-picture (`pages/status_picture/`, `tests/**/status_picture_dashboard/`),
  or fleet (`pages/fleet_dashboard/`, `tests/**/fleet_dashboard/`) module.
- The root `conftest.py`.
- Any golden metric value in `data/credit/db_sanity_purim2026.yaml`.
- `db/`.

## Run it

```powershell
# Sanity suite (needs auth)
pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity

# Credit smoke — navigation surface must stay green
pytest tests/ui/credit_consumption_dashboard/

# One trend combination while iterating
pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k daily_trends
```

## Done when

- Fixture applies `time_range` / `period` `פורים 2026` from YAML (`הכל` is not re-clicked).
- `read_kpi_metrics()` matches nested `kpi_metrics` (percents stay `"3.23%"` / `"4.23%"`).
- All four `daily_trends_by_toggle` keys match via Show-as-a-table, including
  `transactions_count_bar.values` lists.
- Authority amounts and export-table golden rows match; extra UI rows are ignored.
- Screen 2 opens under Hebrew or English page-rail names (no `LoadTimeoutError`).
- Credit smoke stays green. Skip guards fire only for a genuinely absent visual.
- No alerts / status-picture / fleet / `core/` / root-conftest edit; no golden value change.
- In-function comments are English.
