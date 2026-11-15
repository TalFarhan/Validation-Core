# Quickstart: Fix Skipped Hierarchy Tests and Navigation Errors for Alerts Analysis

## What this slice does

Turns the Alerts Analysis Screen 2 `ERROR` and `SKIPPED` results into real assertions:

- Page switch and date entry no longer raise `LoadTimeoutError` when Power BI renders English accessibility
  names (bilingual `.or_()` locators).
- The district chart is found after a drill-down because its title is evaluated dynamically
  (`התרעות לפי <level>`), not hardcoded. `set_hierarchy_level` waits for that new title instead of the
  base `מחוז` title (the current false-negative skip).
- `read_district_labels`, `read_hour_buckets`, and `read_hour_daily_avg` extract data when the visual
  renders as a `listbox`, so the `test_hierarchy_*` and `test_alerts_by_hour_*` tests stop skipping.

## Prerequisites

- Portal auth configured (the UI/sanity tests open the live Power BI report).
- Python env with `pytest`, `PyYAML`, Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by the existing alerts fixtures.

## Files you will touch

- `pages/alerts_analysis/population_page.py` — bilingual `.or_()` for the page-rail switch and date fields;
  remove `DISTRICT_CHART`, add `district_chart_title_for` / `district_chart_title()` + active-level state;
  wait for the drilled title in `set_hierarchy_level`; add a listbox / Show-as-a-table read path to
  `read_district_labels`, `read_hour_buckets`, and `read_hour_daily_avg`; parameterize the dates-table
  helpers by visual title.
- `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` — use the title accessor.
- `tests/ui/alerts_analysis_dashboard/population_snapshot.py` — use the title accessor.
- `tests/unit/test_population_page.py` — assert `district_chart_title_for("mahoz")`.
- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` — audit only.

## Do NOT touch

- `core/portal/`, `core/components/`.
- Any fleet (`pages/fleet_dashboard/`, `tests/**/fleet_dashboard/`) or status-picture
  (`pages/status_picture/`, `tests/**/status_picture_dashboard/`) module.
- The root `conftest.py`.
- Any golden metric value in `data/alerts/db_sanity_am_kalavi.yaml`.

## Run it

```powershell
# The hierarchy and hour tests (needs auth)
pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k "hierarchy or hour"

# Full alerts sanity module
pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity

# Contract gate — alerts UI smoke + unit must stay green (alerts page was edited)
pytest tests/ui/alerts_analysis_dashboard/
pytest tests/unit/test_population_page.py
```

## Done when

- Page switch and date entry work under Hebrew and English accessibility names (no `LoadTimeoutError`).
- The district readers anchor on the live `התרעות לפי <level>` title after a drill-down.
- `set_hierarchy_level` returns `True` after a successful drill-down (does not wait for `התרעות לפי מחוז`).
- `read_district_labels`, `read_hour_buckets`, and `read_hour_daily_avg` return non-empty mappings for a
  listbox visual.
- Every `test_hierarchy_*` and `test_alerts_by_hour_*` reports pass/fail (not skip) with data present; the
  guards still fire for a genuinely absent control.
- The alerts UI smoke suite and the unit test are green.
- No fleet/status/`core/`/root-conftest edit; no golden metric value changed.
- In-function comments are English.
