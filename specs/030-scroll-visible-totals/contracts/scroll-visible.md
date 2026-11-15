# Contract: Scroll the Dates Table and Filter District Rows

**Feature**: 030-scroll-visible-totals | **Date**: 2026-10-18

`Chart.read` and `_svg_mark_total` are unchanged. `core/` is not edited.

## `chart_total` for `DATES_CHART`

1. Keep the right-click and the click on `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent.
2. Find the visible grid whose `התרעות` column header is present.
3. Scroll that table in overlapping steps. After each step, read rows with `is_visible()`.
4. Skip a row that fails `is_visible()`. Skip a header row. Skip a row whose cell text is `סה"כ` or starts with `סה"כ`.
5. Read the `role="gridcell"` at the `התרעות` header index. Remove thousands separators and spaces. Include `0`.
6. Store the integer under `aria-rowindex`, or under the row-header text when that index is absent. Do not store the same key twice.
7. Stop when two passes in a row add no key and do not move the scroll position. Also stop at `self.timeout`. Do not loop without one of those stops.
8. If no visible integer was stored, raise `AssertionError` naming the dates chart.
9. Click a visible button named `חזרה לדוח`. Wait until the dates chart title is visible, then return the sum as `int`.

## `chart_total` for `DISTRICT_CHART`

1. Do not sum `_rows_for_total` for this title.
2. Use the tight visual container for `התרעות לפי מחוז`.
3. Add integers only from `role="row"` elements in that container that pass `is_visible()`.
4. Use the `התרעות` column when that header is present. Skip a header row and a `סה"כ` row. Include `0`.
5. Poll until two consecutive visible reads return the same sum and the same included count. Pause briefly between reads. Stop at `self.timeout`.
6. Do not scroll the district visual.
7. If no visible integer was added, raise `AssertionError` naming the district chart.
8. Return the settled sum as `int`.

## Other titles

- `HOUR_CHART` still calls `_svg_mark_total`.
- `SETTLEMENT_CHART` still calls `_rows_for_total`.

## `test_hour_date_and_district_sums_match`

Unchanged. It still uses `01/09/2026` and `15/10/2026`, asserts `hour_total == district_total == dates_total`, and has no `pytest.mark.xfail`.

## Examples (normative)

| Chart | What the automation returned | What the visible dashboard shows |
|-------|------------------------------|----------------------------------|
| Hour | `13` | `13` |
| Dates, first viewport only | `11` | `13` after the lower rows are included |
| District, hidden rows included | `5847` | `13` |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour, dates, and district totals match | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
