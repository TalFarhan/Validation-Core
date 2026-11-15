# Contract: Bound the Global Invariant Tests by Date

**Feature**: 031-invariant-date-bounds | **Date**: 2026-10-18

`set_date_range` and `clear_filters` are unchanged. `core/` and `pages/` are not edited.

## `test_day_plus_night_equals_untoggled_sum`

1. Keep the opening `clear_filters()`.
2. Call `set_date_range("01/09/2026", "15/10/2026")` before the untoggled `chart_total` for the dates chart.
3. Keep the day toggle, the off toggle, and the night toggle in their current order.
4. Keep `assert day + night == untoggled`.
5. Do not add `pytest.mark.xfail`.

## `test_clear_restores_population_snapshot`

1. Keep the opening `clear_filters()`.
2. Call `set_date_range("01/09/2026", "15/10/2026")` before the before `take_snapshot`.
3. Keep `set_between_dates("01/09/2026", "01/10/2026")`, `set_day_night("day")`, `set_day_night("night")`, and `set_value_range(0, 349)`.
4. Keep the during snapshot and `assert not same_snapshot(before, during)`.
5. After the later `clear_filters()`, call `set_date_range("01/09/2026", "15/10/2026")` before the after snapshot.
6. Keep `assert same_snapshot(before, after)`.
7. Do not add `pytest.mark.xfail`.

## Unchanged

- `test_hour_date_and_district_sums_match` still uses `01/09/2026` and `15/10/2026` and `hour_total == district_total == dates_total`.
- `test_population_cards_within_total`, `test_settlement_series_match_legend`, and `test_population_suite_opens_second_page` stay as they are.
- `tests/ui/alerts_analysis_dashboard/population_snapshot.py` stays as it is.
- `pages/alerts_analysis/population_page.py` stays as it is.
- `core/` stays as it is.

## Examples (normative)

| Step | Dates chart the test reads |
|------|----------------------------|
| Day/night untoggled total, before this slice | Unfiltered table, more than 11,000 rows |
| Day/night untoggled total, after this slice | `01/09/2026` through `15/10/2026` |
| After snapshot immediately after `clear_filters()` | Unfiltered table |
| After snapshot after the second `set_date_range` | `01/09/2026` through `15/10/2026` |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Day plus night equals the untoggled dates total inside the window | `test_day_plus_night_equals_untoggled_sum` |
| Clear restore matches inside the window, and the during snapshot differs | `test_clear_restores_population_snapshot` |
| No `core/` or `pages/` file in the slice diff | review of the edit list |
