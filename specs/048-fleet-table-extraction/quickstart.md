# Quickstart: Centralize Show as a Table Extraction (Fleet MVP)

## What this slice does

Reads fleet chart segment names and counts from Power BI "Show as a table" instead of
SVG titles, legend text, and hover tooltips.

- `VisualTable` in `core/components/visual_table.py` right-clicks a visual, opens
  `הצג כטבלה` / `Show as a table`, scrolls the grid, and clicks `חזרה לדוח` /
  `Back to report`.
- `MainDashboardPage.read_chart_segments(chart_key)` returns `dict[str, int]` for
  `unit`, `source`, `category`, and `withdrawal`.
- Golden chart tests compare those integers to `data/fleet/db_sanity_all.yaml`.
- `hover_chart_segment` and `expand_chart_hierarchy` stay for tooltip and drill-down
  checks. `get_chart_segment_labels` stays the canvas label list those checks poll.

## Prerequisites

- Portal auth configured (the sanity and e2e tests open the live Power BI report).
- Python env with `pytest` and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by the existing fleet fixture.

## Files you will touch

- `core/components/visual_table.py` — new reader and pure mapper.
- `core/components/__init__.py` — export `VisualTable`.
- `pages/fleet_dashboard/main_dashboard_page.py` — add `read_chart_segments` only.
- `tests/unit/test_visual_table_rows.py` — mapper unit test.
- `tests/sanity/fleet_dashboard/test_db_sanity.py` — `assert_chart_matches`.
- `tests/ui/fleet_dashboard/dashboard_validation.py` — the two label-coverage helpers.

## Leave unchanged

- `get_chart_segment_labels`, `hover_chart_segment`, `expand_chart_hierarchy`.
- `core/portal/page.py` and `core/components/chart.py`.
- `pages/alerts_analysis/` and `pages/credit_consumption/`.
- `data/fleet/db_sanity_all.yaml` and `db/`.
- Tooltip helpers and `tests/e2e/test_chart_drilldown.py` canvas snapshots.

## Check

From the repo root.

Mapper only (no portal):

```powershell
pytest tests/unit/test_visual_table_rows.py
```

Fleet smoke gate (Layer 2 and the fleet page changed):

```powershell
pytest tests/ui/fleet_dashboard/
```

Golden chart extraction (needs portal auth):

```powershell
pytest tests/sanity/fleet_dashboard/test_db_sanity.py -m sanity -k "unit_breakdown or pull_source or credit_reasons or category_actuals"
```

A golden count that differs from the table value fails those four tests. They no
longer skip because a tooltip did not open. Hover-based tooltip tests are a separate
run and are not the gate for this slice.
