# Phase 1 Data Model: Fix Skipped Hierarchy Tests and Navigation Errors for Alerts Analysis

This slice changes behavior, not schema. The "entities" below are the in-memory structures the alerts
population flow already uses; no new persistent model is added.

## Golden record (`data/alerts/db_sanity_am_kalavi.yaml`) — UNCHANGED values

Loaded by `load_sanity_data()` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` under
`dashboard_sanity_checks.screen_2_alerts_analysis`. Relevant to this slice:

- **`metrics.alerts_by_hierarchy`** — `mahoz` / `nafa` / `rashut` / `yeshuv`, each with a `sum` and a
  `daily_avg` mapping of name → count. Consumed by `test_hierarchy_*` through `read_district_labels`.
- **`metrics.alerts_by_hour`** — `sum` and `daily_avg` mappings of hour → count (`"HH:MM"` keys).
  Consumed by `test_alerts_by_hour_sum_matches_db` (`read_hour_buckets`) and
  `test_alerts_by_hour_daily_avg_matches_db` (`read_hour_daily_avg`).
- **`date_range`** — `start` / `end` applied by `_apply_golden_range` before each read.

**Validation rule**: metric values are not changed by this slice. The only edits are to page-object
locators/readers and three test references to the removed constant.

## Hierarchy level state (runtime)

- **Field**: `_active_hierarchy_level` on `AlertsPopulationPage`, default `"mahoz"`.
- **Map** (class-level): `{"mahoz": "מחוז", "nafa": "נפה", "rashut": "רשות", "yeshuv": "יישוב"}`.
- **Static builder**: `district_chart_title_for(level) -> str` returns `"התרעות לפי " + map[level]`.
- **Instance accessor**: `district_chart_title(level=None)` uses `level` or `_active_hierarchy_level`.
- **Writer**: `set_hierarchy_level(level)` sets `_active_hierarchy_level` only after the new title is
  visible. A failed selection leaves the field unchanged.
- **Invariant**: at the base level the accessor returns `"התרעות לפי מחוז"` (the value the removed
  constant held), so the smoke/unit tests keep passing against the accessor / static builder.

## Bilingual locator (runtime)

- **Page-rail switch**: `before_report_ready_check` targets `ניווט בין עמודים`.or_()`Page navigation`
  across `get_by_role("link"|"button", name=...)` / `get_by_label(...)`.
- **Date fields**: `_fill_input` fills `input[aria-label^='תאריך התחלה']`.or_()`input[aria-label^='Start date']`
  and `input[aria-label^='תאריך סיום']`.or_()`input[aria-label^='End date']`, reusing `_commit_field`.
- **Show-as-table menu** (already bilingual, keep): `הצג כטבלה` / `Show as a table`.
- **Invariant**: the Hebrew side of each `.or_()` resolves when Hebrew is rendered; neither variant is
  removed.

## Listbox / table reading (runtime)

- **Producers**: `read_district_labels() -> dict[str, int]`, `read_hour_buckets() -> dict[str, int]`,
  `read_hour_daily_avg() -> dict[str, int]`.
- **Existing paths first**: grid rows / SVG marks / categories / tooltip (unchanged when they return data).
- **Show-as-a-table path**: right-click the visual → `_click_show_as_table` →
  `_alert_column_table(header)` → `_collect_scrolled_rows(..., key="header")` → `_leave_visual_table(title)`.
  Header is `התרעות` for sums and a `ממוצע`-containing header for daily avg. Row keys are the rowheader
  text (`_visible_date_entry` is already generic). Hour keys are normalized to `HH:MM`.
- **Listbox path**: pair category `listbox` options with the `התרעות` (or `ממוצע`) series `listbox`
  options in draw order.
- **Return shape**: unchanged — a name/hour → integer-count mapping.
- **Failure mode**: an empty mapping is still returned when a control is genuinely absent, so the test's
  `pytest.skip` guard fires (preserved).

## Unchanged readers

`read_card`, `chart_total` (signature), `read_settlement_warned`, `read_date_counts`,
`set_district_aggregation` (signature), `set_date_range`, and the `_visual_container` /
`_container_is_one_chart` resolution keep their names and return types; they simply receive the dynamic
title from the accessor where they previously used the constant. `read_date_counts` keeps calling the
parameterized table helpers with `DATES_CHART` / header `התרעות`.
