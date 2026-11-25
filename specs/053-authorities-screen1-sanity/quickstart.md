# Quickstart: Authorities Status Screen 1 YAML Sanity

## What this slice does

Adds a Screen 1 reader and a golden-YAML check for הערכת מצב רשויות:

- The report still opens through `AuthoritiesStatusPage` (`DASHBOARD_SEARCH_TERM = הערכת מצב רשויות`).
- `date` is applied first when `dashboard.screen_1_national_status.date` is present.
- `filters` are applied in YAML order. A string is one selection. A list is one selection per
  item. `sub_district` is two selections, and the second does not clear the first.
- After every selection, and once more before the read, the page waits until a visible spinner
  is gone and the ready phrase is visible. No sleep and no network-idle wait.
- `read_screen_1_metrics()` returns `date`, `filters`, `survey_status`, `authorities_status`,
  `facilities`, and `missing_daily_report`.
- One sanity test walks that dict against `data/reshuyot/db_sanity.yaml`. `title` stays in the
  file and is skipped. Screen 2 is not opened.

The smoke test still calls `verify_freshness()` only.

## Prerequisites

- Portal auth configured (the sanity test opens the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.

## Files you will touch

- `pages/authorities_status/page.py` — `select_screen_1_filter`, `wait_for_screen_1_idle`,
  `read_screen_1_metrics`, `section_anchor_visible`. Hebrew role names and block headings stay
  here. District and sub-district go through `Slicer`. The open date dropdown is clicked by
  `_pick_open_date`: at most 20 steps, visible row then click, otherwise `PageDown` or
  `scrollTop += 150`, stop early when `scrollTop` does not move, and raise `AssertionError`
  with the visible rows if the date never appears. That method does not call
  `collect_virtualized_rows`. Comments inside functions stay English.
- `tests/sanity/authorities_status_dashboard/__init__.py` — package marker.
- `tests/sanity/authorities_status_dashboard/conftest.py` — `authorities_status_dashboard =
  bind_dashboard(AuthoritiesStatusPage, "authorities_status_dashboard")`.
- `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` — load
  `screen_1_national_status`, apply date then filters, wait for idle, private tree walk.
- `docs/COVERAGE_CATALOG.md` — YAML block ↔ reader ↔ test rows. Screen 2 is listed as not
  covered by this slice.

Copied from the live report during implementation (not invented in the plan): slicer
accessible names and the Hebrew heading of each block. Numbers, authority names, and filter
values stay in the YAML. They are not copied into the page or the test.

## Do NOT touch

- `data/reshuyot/db_sanity.yaml`. Do not change numbers. Do not change `screen_2_service_targets`.
- `core/portal/` and `core/components/`. Do not add a scroll-and-search method to `Slicer`.
  Do not call `collect_virtualized_rows` from `_pick_open_date`. Name-list reads may still
  use that helper.
- `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`,
  `data/hosen/`.
- `tests/ui/authorities_status_dashboard/` (smoke fixture name stays `dashboard`).
- `tests/helpers/` (no new comparison helper).
- The root `conftest.py`.
- `db/`.

## Run

After the page and the sanity module exist:

```powershell
pytest tests/sanity/authorities_status_dashboard -m sanity
```

The smoke suite is unchanged. It is not part of the command above.

## Failure you should see when the screen drifts

A mismatch names the YAML path, the UI value, and the golden value, for example
`dashboard.screen_1_national_status.survey_status.filled`. An unknown slicer id fails before
the read. A visible block with an empty read fails. A block with no anchor is skipped. If
every block is skipped, the test skips.

## Empty `survey_status.filled` (2026-11-19)

Current failure:

```text
AssertionError: dashboard.screen_1_national_status.survey_status.filled: ui='' golden=18
```

The golden file already says `filled: 18`. Change the reader, then re-run:

```powershell
pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py::test_authorities_screen1_matches_golden -m sanity
```

What changes:

- `pages/authorities_status/page.py` — `filled` waits for the digit text node inside `svg[aria-label^='GOALS_COUNT_MUNI']` on the report frame. `out_of` does the same for `svg[aria-label*='Muni_Code']`. The wait is `expect` (`to_be_visible`, then `to_have_text` with a digit) and `self.timeout`. A timeout still returns `""`.
- `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` — `assert_value` and `_assert_tree` stay synchronous. They already fail this empty string on the YAML path.

A later run that reads a digit other than `18` is still a failure. Do not edit the YAML to absorb it.
