# Quickstart: Hosen Status Screens 3 and 4 YAML Sanity

## What this slice does

Adds a geographic-screen reader, an Excel-export reader, and a golden-YAML check for each.

The report still opens on Screen 1. The Screen 3 test then:

- Opens the geographic screen whose title is `screen_3_geographic_investigation.title`.
- Applies `date_range.start`, then `date_range.end`, through the existing date combobox path.
- Applies each non-null `filters` entry in YAML order through the existing smart-filter path.
  `authority: null` is not typed into a control.
- After each selection, and once more before the read, expects a visible spinner to be hidden
  and the Screen 3 title to be visible.
- Compares `title`, `date_range`, `filters`, the final resilience chart, and the category
  charts to `hosen_dashboard.screen_3_geographic_investigation`.

Each chart is read with `VisualTable.read_rows`. The right-click target is the graph body
`_mark_visual_host` already marks (`vcGroupBody`), not the `visualHeaderAbove` header.

The Screen 4 test then, from its own fresh open on Screen 1:

- Opens the export screen whose title is `screen_4_excel_export.title`.
- Applies `date`, then each non-null `filters` entry. `sector` and `authority` are `null` and
  are not typed into a control.
- Reads `data_table` with `collect_virtualized_rows`. It does not download a workbook.

`collect_virtualized_rows` keeps moving `scrollTop` while that value can still increase, so a
later date or authority is collected. The page does not copy that loop.

Screen 1's sanity test, Screen 2's sanity test, and the freshness smoke test stay as they are.

## Prerequisites

- Portal auth configured (the sanity tests open the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.
- Git checkout stays `feature/reportportal-integration`. The spec directory is
  `specs/052-hosen-screen34-sanity`.

## Files you will touch

- `pages/hosen_status/page.py` — `open_geographic_screen`, `open_excel_export_screen`,
  `select_screen_3_date_range`, `select_screen_3_filter`, `select_screen_4_filter`,
  `wait_for_screen_3_idle`, `wait_for_screen_4_idle`, `screen_3_section_visible`,
  `screen_4_section_visible`, `read_screen_3_metrics`, `read_screen_4_metrics`.
  Comments inside functions stay English. Hebrew stays in page constants or in the YAML.
- `core/components/virtual_grid.py` — the `scrollTop` stop inside `collect_virtualized_rows`
  only. The signature stays. No Hebrew is added.
- `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` — new `sanity` test and its
  private compare helpers.
- `tests/sanity/hosen_status_dashboard/test_screen4_sanity.py` — new `sanity` test and its
  private compare helpers.
- `docs/COVERAGE_CATALOG.md` — Screen 3 and Screen 4 YAML keys, page methods, and the two test
  names. Screen 1 and Screen 2 rows stay.

`_mark_visual_host` is called and not edited. `open_investigation_screen`,
`select_screen_1_filter`, `select_screen_2_filter`, `read_screen_1_metrics`, and
`read_screen_2_metrics` are not edited. `_FILTER_ROLES` is not extended.

## Files you will not touch

- `data/hosen/db_sanity.yaml`
- `core/portal/`
- `core/components/visual_table.py`
- `core/components/slicer.py`
- `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
- `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`
- `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`
- `data/hasbara/`, `data/credit/`, `data/alerts/`, and those reports' pages and tests
- `tests/helpers/` (do not add a compare module)
- `db/clients/` (do not add `hosen.py`)

## Run

Screen 3, then Screen 4:

```text
pytest tests/sanity/hosen_status_dashboard/test_screen3_sanity.py -m sanity
pytest tests/sanity/hosen_status_dashboard/test_screen4_sanity.py -m sanity
```

Regression for this page:

```text
pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py -m sanity
pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py -m sanity
```

Layer 2 gate, because `virtual_grid.py` changes:

```text
pytest tests/ui/fleet_dashboard/
```

These need portal auth and a live browser. A failure message starts with
`hosen_dashboard.screen_3_geographic_investigation` or
`hosen_dashboard.screen_4_excel_export`.

## Done when

- Screen 3 matches `title`, `date_range`, `filters`, `graphs.final_resilience_score`, and
  `graphs.categories`. A missing golden date fails. Extra dates do not.
- Screen 4 matches `title`, `date`, `filters`, and `data_table` by `authority`. `75.0%` matches
  only `75.0%`. No workbook is downloaded.
- A YAML `null` matches an empty chip or an empty cell, and the selector was not called with
  `None`.
- A visible anchor with an empty reader fails. A missing anchor skips that block. Every block
  on that screen skipped calls `pytest.skip`.
- Screen 1, Screen 2, and fleet smoke pass. The Hosen smoke module still calls
  `verify_freshness()`.
