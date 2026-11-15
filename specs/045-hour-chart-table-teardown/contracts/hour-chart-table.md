# Contract: Hour Chart Alerts Column

Page-object contract for daily-average hour extraction. No `core/` contract changes.
Show-as-a-table teardown is unchanged and restated so it is not dropped.
This behavior is already in the page object. This slice preserves it.

## Page object: `AlertsPopulationPage` (`pages/alerts_analysis/population_page.py`)

### `read_hour_daily_avg(self) -> dict[str, int]` — UNCHANGED (preserve)

- **Signature / return type**: unchanged.
- **Current body** (keep):
  1. `_press_average_on_chart(self.HOUR_CHART)` so the hour chart's own `ממוצע ליום` button is
     pressed. This is not `set_district_aggregation`. The district toggle does not change this
     chart.
  2. Show-as-a-table with header exact `התרעות` (`contains` stays false).
  3. `_hour_keyed` so keys are `HH:MM`.
  4. Return that mapping, or `{}` when the column has no integer hour rows.
- **Not on this path**: `_hour_average`, a series whose name contains `ממוצע`, `_whole_count`,
  and a `ממוצע` column header. Those helpers stay deleted.
- **Guarantee**: bucket values are integers from the `התרעות` column. A decimal such as `0.54` is
  not parsed and not rounded. `{}` only when that column contributes no hour rows, so
  `test_alerts_by_hour_daily_avg_matches_db` can still skip on a genuinely empty chart.

### `_visual_table_map(self, title, header, *, contains=False) -> dict[str, int]` — UNCHANGED

- Right-click + `_click_show_as_table(title)`.
- `opened = True` as soon as that click succeeds.
- `_alert_column_table(...)` + `_collect_scrolled_rows(...)` inside `try`.
- `finally`: if `opened`, `_leave_visual_table(title)`.
- Hour daily avg calls it as `_visual_table_map(self.HOUR_CHART, "התרעות")`.

### `read_date_counts` / `_dates_table_total` / `_leave_visual_table` — UNCHANGED

- Header remains `התרעות` where a column is read.
- Back control remains bilingual: `חזרה לדוח` and `Back to report`.
- After Back, the calling visual title is visible, or no table was opened.

### `set_district_aggregation(self, mode) -> None` — UNCHANGED

- Still the district-chart Sum / daily-average control. `read_hour_daily_avg` does not call it.

## Callers

- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` —
  `test_alerts_by_hour_daily_avg_matches_db` still calls `read_hour_daily_avg()` after
  `_apply_golden_range`. It does not gain an aggregation toggle. Skip guard stays.
- `data/alerts/db_sanity_am_kalavi.yaml` — `alerts_by_hour.daily_avg` values unchanged.
- `read_hour_buckets` and `read_district_labels` public signatures unchanged.

## Invariants

- `core/portal`, `core/components`, and the root `conftest.py` are not edited.
- No fleet, status-picture, or credit module is edited.
- Comments inside edited functions are English.
