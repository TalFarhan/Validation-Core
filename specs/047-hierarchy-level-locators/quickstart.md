# Quickstart: Fix Hierarchy Level Locators

## What this slice does

Clicks the custom hierarchy tabs above the district chart by their exact Hebrew labels,
and stops the sanity helpers from skipping when that old role lookup missed.

- `נפה`, `רשות`, and `יישוב` are found with `get_by_text(..., exact=True)` in the report iframe.
- The click waits until Playwright can act on the text.
- A missing tab fails the test.
- An empty district read after a successful selection still skips.
- The golden YAML file is not edited.

## Prerequisites

- Portal auth configured (the sanity tests open the live Power BI report).
- Python env with `pytest` and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by the existing alerts sanity fixture.

## Files you will touch

- `pages/alerts_analysis/population_page.py` — `_hierarchy_control` and
  `set_hierarchy_level`.
- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` —
  `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg`.

## Leave unchanged

- `core/portal/` and `core/components/`.
- `data/alerts/db_sanity_am_kalavi.yaml`.
- `db/` and the root `conftest.py`.
- Fleet, status-picture, and credit pages and tests.
- `set_district_aggregation` and the two `מחוז` hierarchy tests.

## Check

From the repo root, with portal auth available:

```powershell
pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k hierarchy
```

Expect:

- The six nafa / rashut / yeshuv tests (sum and daily average) no longer skip with
  `control not visible on district chart`.
- They compare rows to `metrics.alerts_by_hierarchy` when the chart has rows.
- A tab that never becomes clickable fails the test (timeout or assertion).
- An empty `read_district_labels()` result still skips with `returned no rows`.

Comments inside the edited functions are English.
