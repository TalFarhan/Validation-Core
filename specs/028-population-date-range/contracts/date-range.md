# Contract: Population Date Range

**Feature**: 028-population-date-range | **Date**: 2026-10-17

`Chart.read`, `_svg_mark_total`, and the dates menu-table reader are unchanged.
This contract adds the filter that runs before the three-chart comparison.

## `set_date_range(self, start_date: str, end_date: str) -> None`

1. Fill the input whose accessible name begins with `תאריך התחלה` with `start_date`.
2. Fill the input whose accessible name begins with `תאריך סיום` with `end_date`.
3. Use the same commit path as `set_between_dates` (click, fill, Enter).
4. Wait until the total population card is visible, up to `self.timeout`.
5. Poll `read_card("total")` until two consecutive reads are equal. Pause briefly between reads. Stop at `self.timeout` if they never match.
6. Return `None`. Do not return a chart total.

`set_between_dates` stays. Callers that do not need the settle wait keep using it.

## `test_hour_date_and_district_sums_match`

1. `clear_filters()`.
2. `set_date_range("01/01/2020", <today formatted DD/MM/YYYY>)`.
3. `set_district_aggregation("sum")`.
4. Read `HOUR_CHART`, `DATES_CHART`, and `DISTRICT_CHART` once each.
5. Assert `hour_total == district_total == dates_total`.
6. Do not mark the test expected-fail. Do not skip it.

The dates read still opens `הצג כטבלה`, sums the `התרעות` grid cells, and clicks `חזרה לדוח`.

## Out of scope

- MUST NOT edit `core/`.
- MUST NOT add a parser in `population_snapshot.py`.
- MUST NOT change `_svg_mark_total` or the district branch of `chart_total`.

## Examples (normative)

| Call | Start field | End field on 17 October 2026 |
|------|-------------|-------------------------------|
| `set_date_range("01/01/2020", today)` | `01/01/2020` | `17/10/2026` |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| The three totals are equal after the wide range | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
