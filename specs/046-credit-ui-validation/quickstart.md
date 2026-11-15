# Quickstart: Credit Consumption UI Sanity Validation

## What this slice does

Expands the existing Credit Consumption page and sanity tests so they compare the live
report to `data/credit/db_sanity_purim2026.yaml`:

- Screen 1 title, last-updated caption, KPIs, four trend toggles, daily alerts, authority amounts.
- Screen 2 title and export rows.
- Filters come from `active_filters`. `הכל` is not clicked. The period is not hardcoded.
- Golden keys and rows must match. Extra UI keys and rows are ignored.
- An empty read fails when the golden block has data. Skip only when that visual is not on the page.
- Failures print the JSON path, the UI value, and the golden value.

The page class, fixture, and Show as a table flow from feature 044 stay. This slice does not
rebuild them.

## Prerequisites

- Portal auth configured (the sanity tests open the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.

## Files you will touch

- `pages/credit_consumption/credit_consumption_page.py` — `title_is_visible`,
  `visual_is_rendered`, `export_grid_is_rendered`, `any_kpi_card_rendered`. Keep
  `quantity` as int, `amount` as a comma string, and `transactions_count_bar` `values`
  as a list.
- `tests/sanity/credit_consumption_dashboard/test_data_validation.py` — subset asserts,
  fail-on-empty, Screen 1 title and last-updated, Screen 2 title.
- `docs/COVERAGE_CATALOG.md` — section 9 rows for title and last-updated.

## Do NOT touch

- `core/portal/`, `core/components/`.
- `pages/alerts_analysis/`, `pages/status_picture/`, `pages/fleet_dashboard/`, and their tests.
- `db/` and the root `conftest.py`.
- `data/credit/db_sanity_purim2026.yaml` and any other YAML file.
- `tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py` (`verify_freshness` stays).
- Do not add a date parser. Do not parse SVG charts or tooltips. Do not copy alerts helpers.

## Run it

```powershell
# Sanity suite (needs auth)
pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity

# Credit smoke — verify_freshness must stay green
pytest tests/ui/credit_consumption_dashboard/

# One block while iterating
pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k "dashboard_info or kpi or daily_trends or export_table"
```

## Done when

- Screen 1 calls `apply_filters` with the YAML `active_filters` before the title, caption,
  KPIs, trends, alerts, and authority reads.
- The visible titles equal `dashboard_info.title` and `screen_2_data_export.title`.
- `dashboard_info.last_updated` is found in `_last_refresh_caption_text()` as
  `DD/MM/YYYY HH:MM`.
- KPI percents stay strings. `day` stays a string. `transactions_count_bar` values stay
  lists such as `[3, 1]`. Export `quantity` is an int and `amount` keeps commas
  (`"1,944.97"`).
- A rendered visual with golden rows and an empty reader fails, and the message contains
  the JSON path, `ui=`, and `golden=`.
- A visual whose existing title or grid is absent skips.
- Credit smoke still calls `verify_freshness()` and is not edited.
- No alerts, status-picture, fleet, `core/`, `db/`, root conftest, or YAML edit.
- In-function comments are English.
