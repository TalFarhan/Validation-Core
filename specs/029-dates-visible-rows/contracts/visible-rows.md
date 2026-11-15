# Contract: Visible Dates Table Rows

**Feature**: 029-dates-visible-rows | **Date**: 2026-10-18

`Chart.read` and `_svg_mark_total` are unchanged. Only `DATES_CHART` uses this contract.

## `chart_total` for `DATES_CHART`

1. Keep the right-click on the dates visual container and the click on `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent.
2. Wait until a visible grid or table has a `התרעות` column header and at least one visible integer grid cell in that column. Use `self.timeout`.
3. Poll the visible rows until two consecutive reads produce the same sum and the same included count. Pause briefly between reads. Stop at `self.timeout` if they never match.
4. On each read, call `is_visible()` on the `role="row"`. A row that fails that check is omitted, even when its text is still in the DOM.
5. Skip a row that contains a column header. Skip a row whose cell text is `סה"כ` or starts with `סה"כ`.
6. Read the `role="gridcell"` at the `התרעות` header index. Remove thousands separators and spaces. Add the value when it is an integer, including `0`.
7. Do not scroll the table. Do not call `_sum_scrolled_alert_column`.
8. If no visible integer was added, raise `AssertionError` naming the dates chart.
9. Click a visible button named `חזרה לדוח`. Wait until the dates chart title is visible, then return the sum as `int`.

## `chart_total` for the other titles

- `HOUR_CHART` still calls `_svg_mark_total`.
- `DISTRICT_CHART` and `SETTLEMENT_CHART` still call `_rows_for_total`.

MUST NOT edit `core/`.

## `test_hour_date_and_district_sums_match`

- The assertion stays `hour_total == district_total == dates_total`.
- The test MUST NOT be decorated with `pytest.mark.xfail`. On 2026-10-18 that decorator is already absent; leave it absent.
- The date strings stay `01/09/2026` and `15/10/2026`.

## Examples (normative)

| Row | Visible | התרעות grid cell | Included |
|-----|---------|------------------|----------|
| header `תאריך`, `התרעות` | yes | — | none |
| `2026-09-02` | yes | `13` | `13` |
| an older date still in the DOM | no | `5847` | none |
| `סה"כ` | yes | `13` | none |

The filtered dashboard the user read totals 13 on the hour chart, the district chart, and this visible dates column.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour, dates, and district totals match | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
