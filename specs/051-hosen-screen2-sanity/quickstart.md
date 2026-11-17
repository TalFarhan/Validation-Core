# Quickstart: Hosen Status Screen 2 YAML Sanity

## What this slice does

Adds an investigation-screen reader and a golden-YAML check for תמ"צ חוסן Screen 2.

The report still opens on Screen 1. The new test then:

- Opens the investigation screen whose title is `screen_2_investigation.title`.
- Applies `screen_2_investigation.date` through the existing date combobox path.
- Applies each `screen_2_investigation.filters` entry in YAML order through the existing
  smart-filter path.
- After each selection, and once more before the read, expects a visible spinner to be hidden
  and the Screen 2 title to be visible.
- Compares `title`, `date`, `filters`, the authority table, the summary/average row, and the
  trends chart (read with `VisualTable`) to `hosen_dashboard.screen_2_investigation`.

Screen 1's sanity test and the freshness smoke test stay as they are.

## Prerequisites

- Portal auth configured (the sanity test opens the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.
- Git checkout stays `feature/reportportal-integration`. The spec directory is
  `specs/051-hosen-screen2-sanity`.

## Files you will touch

- `pages/hosen_status/page.py` — `open_investigation_screen`, `select_screen_2_filter`,
  `wait_for_screen_2_idle`, `screen_2_section_visible`, `read_screen_2_metrics`. The date and
  smart-filter helpers take an optional settle that defaults to the Screen 1 settle.
  `select_screen_1_filter` does not pass one. Comments inside functions stay English.
- `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` — new `sanity` test and its
  private compare helpers.
- `docs/COVERAGE_CATALOG.md` — Screen 2 YAML keys, page methods, and
  `test_hosen_screen2_matches_golden`. Screen 1 rows stay.

The trends visual title is the page constant `מגמות המרכיבים לפי תאריך`. Any live header
spelling that differs from the Screen 1 category names is copied into a page constant. Neither
is written into the YAML or into the test.

`_mark_visual_host` marks `xpath=ancestor::div[contains(@class, 'visualContainer')][1]` from
that title. It must not stop on the first class that contains `visual` (`visualTitle`). That
title menu has no `הצג כטבלה` item, and `VisualTable` then raises
`'trends_by_date' has no show-as-table menu item`. `core/components/visual_table.py` stays as
it is.

## Do NOT touch

- `data/hosen/db_sanity.yaml`. The numbers, the `null`, and the golden title stay.
- `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` behavior.
- `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` (`dashboard.verify_freshness()`).
- `core/portal/` and `core/components/`.
- `data/hasbara/`, `data/credit/`, `data/alerts/`, and those reports' pages and tests.
- `tests/helpers/` (do not add a compare module).
- `db/`.
- The root `conftest.py`.

## Run

```powershell
pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py
pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py
```

Screen 2 fails with a YAML path when a golden value differs, when a visible anchor comes back
empty, or when a `null` cell is not empty. It skips only when every Screen 2 anchor is absent.

Screen 1 must still pass. It still applies `screen_1_landing.date` and `filters`, waits on the
Screen 1 ready locator, and compares `screen_1_landing`.

## Done when

- `open_investigation_screen` leaves Screen 1's ready locator unchanged and shows
  `תמ״צ התנהגות - מסך תחקור` (either quote spelling).
- `select_screen_2_filter("date", value)` uses the existing date combobox path and settles on
  the Screen 2 title. District and subdistrict use the existing smart-filter path and the same
  settle. `select_screen_1_filter` still settles on Screen 1.
- `read_screen_2_metrics()` returns `title`, `date`, `filters`, and the three table blocks.
  Authority rows come from `collect_virtualized_rows`. Trend rows come from
  `VisualTable.read_rows` on the `visualContainer` host, not on the title strip. A blank trend
  cell is `""`. The trends read does not raise
  `'trends_by_date' has no show-as-table menu item`.
- The Screen 2 test body has no locators. Failure messages start with
  `hosen_dashboard.screen_2_investigation`.
- `docs/COVERAGE_CATALOG.md` lists the Screen 2 keys, methods, and test name.
- Neither test file calls `sleep`, `wait_for_timeout`, or `networkidle`.
