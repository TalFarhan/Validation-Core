# Contract: Dates Table from the Right-Click Menu

**Feature**: 027-dates-table-menu | **Date**: 2026-10-15

`Chart.read` and `_svg_mark_total` are unchanged. Only `DATES_CHART` uses this contract.

## `chart_total` for `DATES_CHART`

1. Dismiss an overlay that is already open. Right-click the tight visual container for `התרעות לפי תאריך` with `click(button="right")`.
2. Click the menu item `הצג כטבלה`. If it is absent, click `Show as a table`. Do not press `Alt+Shift+F11`. Do not dismiss the menu before this click.
3. Wait until a visible `role="grid"` or `role="table"` has `role="row"` elements, a `role="columnheader"` whose text is `התרעות`, and at least one integer `role="gridcell"` in that column. Use `self.timeout`. A header-only grid is not this table. If several match, use the last visible one.
4. Take the column index of that header.
5. For each `role="row"`, skip the row when it contains a column header, or when any cell text is `סה"כ` or starts with `סה"כ`.
6. Read the `role="gridcell"` at that column index. Remove thousands separators and spaces. Add the value when the result is an integer, including `0`.
7. If no integer was added, raise `AssertionError` naming the dates chart.
8. Click a visible button named `חזרה לדוח`.
9. Wait until the dates chart title is visible, then return the sum as `int`.
10. If the menu item, the table, or `חזרה לדוח` is missing, raise `AssertionError`. Do not return the circle-mark sum.

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

| Row | התרעות grid cell | Included |
|-----|------------------|----------|
| header `תאריך`, `התרעות` | — | none |
| `2026-10-09` | `5,293` | `5293` |
| `2026-10-15` | `0` | `0` |
| `סה"כ` | `141493` | none |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour, dates, and district totals match | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
