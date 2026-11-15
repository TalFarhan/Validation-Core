# Contract: Fleet Chart Table Extraction

**Feature**: `048-fleet-table-extraction` | **Date**: 2026-11-04

How `MainDashboardPage` turns one chart into label → count, and which callers move
to that method. Hover and hierarchy stay on the canvas.

## Page

`pages/fleet_dashboard/main_dashboard_page.py`

Class `MainDashboardPage`. Existing inheritance stays: `ReportShell`.

### `read_chart_segments(self, chart_key: str) -> dict[str, int]` — NEW

1. `chart_key` outside `_CHART_TITLES` raises `ValueError`. No click.
2. `assert_chart_visible(chart_key)`.
3. `dismiss_tooltip()`.
4. `VisualTable(self.page, self.dashboard, timeout_ms=self.timeout).read_rows(self.chart_section(chart_key), name=chart_key)`.
5. Return `rows_to_label_values(rows, skip_labels=("סה\"כ",))`.

The chart titles stay in `_CHART_TITLES`. This method does not read SVG titles or
legend text. It does not hover.

Comments inside the method are English.

## Unchanged page methods

| Method | Role that stays |
|--------|-----------------|
| `get_chart_segment_labels(chart_key) -> list[str]` | SVG `<title>` and legend/axis text for hierarchy snapshots and the label poll |
| `hover_chart_segment(...)` | Tooltip checks and drill-down focus |
| `expand_chart_hierarchy(...)` | Header `הסתעפות`, then tooltip fallback |
| `wait_for_chart_labels_change` | Polls `get_chart_segment_labels` |
| `drill_up_chart`, `reset_chart_hierarchy`, `expand_via_tooltip_drilldown` | Keep calling `get_chart_segment_labels` |

Do not rewrite those bodies in this slice.

## Callers that switch to `read_chart_segments`

| Caller | What it uses |
|--------|----------------|
| `tests/sanity/fleet_dashboard/test_db_sanity.py` `assert_chart_matches` | Keys for golden name presence. Values for the count. No `hover_chart_segment`. No `parse_tooltip_entries`. The "no tooltip appeared" skip is removed from this helper. The skip when no golden name is present stays. A present name with a different integer fails. |
| `tests/ui/fleet_dashboard/dashboard_validation.py` `assert_chart_labels_match_db_sample` | Mapping keys as the UI label list |
| `tests/ui/fleet_dashboard/dashboard_validation.py` `assert_unit_drilldown_matches_db` | Mapping keys as the UI label list after expand has already run |

`normalize_label` stays the comparison fold. It is not moved into core.

## Callers that keep hovering

| Caller | Why |
|--------|-----|
| `assert_chart_tooltip_segment_matches_db` | The check is the tooltip |
| `assert_chart_tooltips_match_db_sample` | The check is the tooltip |
| `tests/e2e/test_chart_drilldown.py` direct `get_chart_segment_labels` calls | Before/after canvas snapshot for the drill itself |

## Out of scope

- `pages/alerts_analysis/population_page.py`
- `pages/credit_consumption/credit_consumption_page.py`
- `core/portal/page.py`
- `core/components/chart.py`
- `data/fleet/db_sanity_all.yaml`
- `db/`
