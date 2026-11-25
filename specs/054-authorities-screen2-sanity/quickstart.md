# Quickstart: Authorities Status Screen 2 YAML Sanity

## What this slice does

Adds a Screen 2 reader and a golden-YAML check for הערכת מצב רשויות Screen 2:

- The report still opens through `AuthoritiesStatusPage` (`DASHBOARD_SEARCH_TERM = הערכת מצב רשויות`).
- `open_screen_2(title)` uses golden `dashboard.screen_2_service_targets.title` as a
  navigation target only. The test does not assert `title`.
- `date` is applied first when `dashboard.screen_2_service_targets.date` is present.
- `filters` are applied in YAML order. A string is one selection. A list is one selection
  per item. A later selection does not clear the first. Never pass `str(list)`.
- After every selection, and once more before the read, the page waits until a visible
  spinner is gone and the Screen 2 ready locator is visible. No sleep and no network-idle
  wait.
- `read_screen_2_metrics()` returns `date`, `filters`, `sector_profile`, `protection_data`,
  `service_targets`, as-loaded `grade_trends` (`None`), and sibling `data` (trend rows).
- One sanity test walks that dict against `data/reshuyot/db_sanity.yaml`. `title` stays in
  the file and is skipped. Screen 1 is not loaded by this test.

Screen 1 sanity and the smoke test stay as they are.

## Prerequisites

- Portal auth configured (the sanity test opens the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.
- Stay on git branch `feature/reportportal-integration`. Do not switch branches.

## Files you will touch

- `pages/authorities_status/page.py` — `open_screen_2`, `select_screen_2_filter`,
  `wait_for_screen_2_idle`, `read_screen_2_metrics`, `screen_2_section_visible`. Hebrew
  role names and block headings stay here. District and sub-district go through `Slicer`.
  Date reuses `_pick_open_date`. `service_targets` may use `collect_virtualized_rows`.
  Trend rows use `VisualTable.read_rows`. Comments inside functions stay English. Screen 1
  public methods keep their contracts.
- `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py` — load
  `screen_2_service_targets`, open Screen 2, apply date then filters, wait for Screen 2
  idle, private tree walk with `name` and `date` row identity.
- `docs/COVERAGE_CATALOG.md` — Screen 2 YAML block ↔ reader ↔ test rows. Screen 1 rows stay.

Copied from the live report during implementation (not invented in the plan): Screen 2
slicer accessible names, block headings, and the page-navigation control's quote spelling.
Numbers, service names, dates, and filter values stay in the YAML. They are not copied into
the page or the test. The golden title is passed from YAML into `open_screen_2`.

As-loaded YAML quirk (do not "fix" it): `grade_trends` is `null`; trend rows are sibling
`data`. Compare those rows on `data` by `date`, then score keys.

## Do NOT touch

- `data/reshuyot/db_sanity.yaml`. Do not change numbers. Do not indent `data` under
  `grade_trends`.
- `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`.
- `core/portal/` and `core/components/`. Compose `Slicer`, `VisualTable`, and
  `collect_virtualized_rows`. Do not edit them.
- `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`,
  `tests/ui/hosen_status_dashboard/`, `data/hosen/`. Do not copy or import Hosen code.
- `tests/ui/authorities_status_dashboard/` (smoke fixture name stays `dashboard`).
- `tests/helpers/` (no new comparison helper).
- `specs/053-authorities-screen1-sanity/`.
- The root `conftest.py`.
- `db/`.

## Run

After the page methods and the Screen 2 sanity module exist:

```powershell
pytest tests/sanity/authorities_status_dashboard/test_screen2_sanity.py -m sanity --reportportal
pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py -m sanity --reportportal
```

Both must pass. The smoke suite is unchanged. It is not part of the commands above.

## Failure you should see when the screen drifts

A mismatch names the YAML path, the UI value, and the golden value, for example
`dashboard.screen_2_service_targets.sector_profile.average_final_score`. An unknown slicer
id fails before the read. A visible block with an empty read fails. A block with no anchor
is skipped. If every block is skipped, the test skips. A missing golden service `name` or
trend `date` fails when that anchor is visible.
