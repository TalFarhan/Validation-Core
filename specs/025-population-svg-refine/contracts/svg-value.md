# Contract: SVG Value After התרעות

**Feature**: 025-population-svg-refine | **Date**: 2026-10-15

`Chart.read` and `Chart._parse` are unchanged. Dates and hour totals do not call them.

## `chart_total` for `DATES_CHART` and `HOUR_CHART`

1. Resolve the tight visual container already used for that title.
2. Locate `svg rect, svg path, svg circle` inside that container.
3. Wait until the first of those marks is visible, with the population page timeout.
4. Collect `aria-label` with `get_attribute`. Do not call `inner_text`.
5. Skip a label that contains `ממוצע`.
6. Skip a label that contains a fractional number (`5895.54`, `5,895.54`).
7. If the label contains `התרעות`, add the integer from `התרעות\s*([0-9,]+)`. Remove thousands separators. `התרעות 5,293` is `5293`. `תאריך 2026-10-15. התרעות 0.` is `0`.
8. If the label does not contain `התרעות` and the whole label is one integer, add that integer. `5293` is `5293`.
9. Skip every other label.
10. If no integer was added, raise `AssertionError` naming the chart.
11. Return the sum as `int`.

Do not add `[role="option"]` labels on top of the shape labels. `series_index` does not select a series for these two titles.

District and settlement totals keep their current rules. The district total still uses `Chart.read` with the page title scope.

MUST NOT add `0` for a skipped average or float. MUST NOT edit `core/`. MUST NOT add a parser in `population_snapshot.py`.

## `test_hour_date_and_district_sums_match`

Unchanged. It still clears, sets district aggregation to Sum, and asserts:

1. `chart_total(HOUR_CHART) == chart_total(DATES_CHART)`
2. `chart_total(DATES_CHART) == chart_total(DISTRICT_CHART)`

## Examples (normative)

| Label | Included |
|-------|----------|
| `תאריך 2026-10-15. התרעות 0.` | `0` |
| `התרעות 5,293` | `5293` |
| `5293` | `5293` |
| `ממוצע 5,895.54` | none |
| `5895.54` | none |
| `2026-10-15` | none |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour, dates, and district totals match | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
