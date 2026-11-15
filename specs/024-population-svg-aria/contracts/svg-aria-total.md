# Contract: SVG Aria-Label Total

**Feature**: 024-population-svg-aria | **Date**: 2026-10-15

`Chart.read` and `Chart._parse` are unchanged. Dates and hour totals do not call them.

## `chart_total` for `DATES_CHART` and `HOUR_CHART`

1. Resolve the tight visual container already used for that title.
2. Collect `aria-label` from `svg rect` and `svg path` inside that container. Use `get_attribute`. Do not call `inner_text`. Do not read `role="option"`.
3. If those labels include no integer, collect `aria-label` from `[role="img"]` inside the container, excluding the container node itself. Do not add this set to the shape set.
4. Skip a label that contains `ממוצע`.
5. Skip a label that contains a fractional number: digits, then `.` or `,`, then more digits (`5895.54`, `5,895.54`).
6. On a kept label, take the last integer token. Remove spaces and thousands separators. `5,293` is `5293`.
7. Add each parsed integer, including `0`.
8. If no integer was added, raise `AssertionError` naming the chart.
9. Return the sum as `int`.

`series_index` does not select a series for these two titles.

District and settlement totals keep their current rules, including the numeric skip from feature 021. The district total still uses `Chart.read` with the page title scope.

MUST NOT add `0` for a skipped average or float. MUST NOT edit `core/`. MUST NOT add a parser in `population_snapshot.py`.

## `test_hour_date_and_district_sums_match`

Unchanged. It still clears, sets district aggregation to Sum, and asserts:

1. `chart_total(HOUR_CHART) == chart_total(DATES_CHART)`
2. `chart_total(DATES_CHART) == chart_total(DISTRICT_CHART)`

## Examples (normative)

| Label | Included |
|-------|----------|
| `5293` | `5293` |
| `5,293` | `5293` |
| `00:00 4181` | `4181` |
| `0` | `0` |
| `ממוצע 5,895.54` | none |
| `5895.54` | none |
| chart title with no integer | none |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Hour and dates totals match, then dates and district totals match | `test_hour_date_and_district_sums_match` |
| No `core/` file in the slice diff | review of the edit list |
