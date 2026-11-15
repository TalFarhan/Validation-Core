# Contract: Hour Bar Sum and Clear Baseline

**Feature**: 023-population-hour-clear | **Date**: 2026-10-15

`Chart.read` and `Chart._parse` are unchanged. The page uses the series tuple `_parse` already returns.

## `chart_total` for `HOUR_CHART`

1. Parse the tight container from feature 022 with `Chart._parse` and keep both the categories and the series names.
2. A series whose name contains `ממוצע` is not summed.
3. On the remaining series, add a cell only when it is an `int`, or a `float` whose `is_integer()` is true, and it is not a `bool`.
4. If no cell was added, raise `AssertionError`.
5. If the sum is a whole float, return `int`.

Dates, district, and settlement totals keep their current rules, including the numeric skip from feature 021 and the tight dates container from feature 022.

MUST NOT add 0 for a skipped average. MUST NOT edit `core/`.

## `test_clear_restores_population_snapshot`

In `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`:

1. `page.clear_filters()`.
2. `before = take_snapshot(page)`.
3. `page.set_between_dates("01/09/2026", "01/10/2026")`.
4. `page.set_day_night("day")` then `page.set_day_night("night")`.
5. `page.set_value_range(0, 349)`.
6. Assert `take_snapshot(page)` is not `before`.
7. `page.clear_filters()`.
8. Assert `take_snapshot(page)` equals `before`.

The test body still calls page methods and `take_snapshot`. It does not read the DOM itself.

## Examples (normative)

| Hour cells | Series name | Included |
|------------|-------------|----------|
| `5293`, `4181` | alerts | both |
| `5895.54` | `ממוצע` | none |
| `5895.54` | unlabeled | none, because it is a fractional float |
| `1.0` | alerts | `1` |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour, dates, and district totals match in Sum mode | `test_hour_date_and_district_sums_match` |
| Clear returns the post-clear baseline | `test_clear_restores_population_snapshot` |
| Day plus night still matches | `test_day_plus_night_equals_untoggled_sum` |
| No `core/` file in the slice diff | review of the edit list |
