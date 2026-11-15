# Contract: Population Chart Total and Sum Click

**Feature**: 021-population-invariant-fix | **Module**: `pages/alerts_analysis/population_page.py` | **Date**: 2026-10-14

Page-local behavior. `Chart.read` and `scope_host` are unchanged.

## `chart_total(self, title: str, series_index: int = 0) -> int | float`

1. Read `self._chart.read(title, scope=self.PAGE_TITLE)`.
2. If `state == "empty"` or `categories` is empty, raise `AssertionError`.
3. For each category, take `values[series_index]` when that index exists. If the index is missing,
   skip the category.
4. Add the cell only when `isinstance(cell, (int, float))` and `not isinstance(cell, bool)`.
5. If no cell was added, raise `AssertionError`.
6. If the sum is a float that is a whole number, return `int`. Otherwise return the sum.

MUST NOT add 0 for a skipped cell. MUST NOT import or edit `core/`.

## `set_district_aggregation(self, mode)`

`mode` stays `"sum"` or `"average"`. The label stays `SUM_MODE` or `AVERAGE_MODE`.

1. Look for `get_by_role("button", name=label, exact=True)` inside the district chart container.
2. If that count is exactly 1, click that button.
3. Otherwise click `self._report_frame().get_by_role("button", name=label, exact=True).first`.

MUST NOT click a locator with count greater than 1. MUST NOT change `core/components/slicer.py`.

## Examples (normative)

| Selected cells | Result |
|----------------|--------|
| `[4, None, 6]` | `10` |
| `[0, None]` | `0` |
| `[None]` | raise |
| `[]` with empty state | raise |
| `[1.0]` | `1` |

The Sum click with two exact-name buttons clicks `.first` and does not raise strict mode.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Dates, hour, and district totals no longer raise on a settlement label | `test_clear_restores_population_snapshot`, `test_day_plus_night_equals_untoggled_sum`, `test_hour_date_and_district_sums_match` |
| Cards and settlement legend still pass | the other tests in `test_population_invariants.py` |
| No `core/` file in the slice diff | review of the edit; only `pages/alerts_analysis/population_page.py` |
