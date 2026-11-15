# Contract: Dates Accessible Table

**Feature**: 026-dates-accessible-table | **Date**: 2026-10-15

`Chart.read` and `_svg_mark_total` are unchanged. Only `DATES_CHART` uses this contract.

## `chart_total` for `DATES_CHART`

1. Dismiss an open overlay, then click the tight visual container for `התרעות לפי תאריך`.
2. Press `Alt+Shift+F11` with `self.page.keyboard.press("Alt+Shift+F11")`.
3. In the report frame, wait until a visible `role="grid"` has a header cell whose text is `התרעות`. If no grid matches, wait for a visible `role="table"` with that header. Use `self.timeout`. If several match, use the last visible one.
4. Take the column index of that header.
5. For each body row, skip the row when it contains a column header, or when any cell text is `סה"כ` or starts with `סה"כ`.
6. Read the cell at the alert column. Remove thousands separators and spaces. Add the value when the result is an integer, including `0`.
7. If no integer was added, raise `AssertionError` naming the dates chart.
8. Click a visible button named `חזרה`. If that button is absent, click a visible button named `Back`.
9. Wait until the dates chart title is visible, then return the sum as `int`.
10. If the table, the column, or the back button is missing, raise `AssertionError`. Do not return the circle-mark sum.

`series_index` does not select a series for this title.

## `chart_total` for the other titles

- `HOUR_CHART` still calls `_svg_mark_total`.
- `DISTRICT_CHART` and `SETTLEMENT_CHART` still call `_rows_for_total`.

MUST NOT edit `core/`. MUST NOT add a parser in `population_snapshot.py`.

## `test_hour_date_and_district_sums_match`

Unchanged. It still clears, sets district aggregation to Sum, and asserts:

1. `chart_total(HOUR_CHART) == chart_total(DATES_CHART)`
2. `chart_total(DATES_CHART) == chart_total(DISTRICT_CHART)`

## Examples (normative)

| Row | התרעות cell | Included |
|-----|-------------|----------|
| header `תאריך`, `התרעות` | — | none |
| `2026-10-09` | `5,293` | `5293` |
| `2026-10-15` | `0` | `0` |
| `סה"כ` | `141493` | none |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour, dates, and district totals match | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
