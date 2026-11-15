# Data Model: Population Chart SVG Aria Labels

**Feature**: 024-population-svg-aria | **Date**: 2026-10-15

No new stored records.

## SVG mark total

Used only when `chart_total` is called with `DATES_CHART` or `HOUR_CHART`.

| Field | Type | Rule |
|-------|------|------|
| title | string | `התרעות לפי תאריך` or `גרף התרעות וגם ממוצע לפי שעה`. |
| container | locator | The tight visual container from feature 022. |
| marks | locator | `svg rect, svg path` inside that container. `[role="img"]` only when the shapes yield no integer. |
| label | string | The mark's `aria-label`. Empty labels are skipped. |
| value | `int \| none` | The last integer token after the skip rules. Thousands separators are removed. |
| total | `int` | Sum of included values. |

`series_index` is not used for these two titles.

## Other totals

District and settlement totals keep the current category-cell sum. They do not use this mark table.

## Validation rules

1. A label containing `ממוצע` contributes nothing, including `0`.
2. A label containing a float, such as `5895.54`, contributes nothing.
3. `5,293` is the integer `5293`. `0` is included when it is the integer on a kept label.
4. Shape labels and image labels are not added in the same total.
5. If no integer was included, `chart_total` raises.

## State transitions

```text
dates or hour title
    → tight visual container
    → svg rect and svg path aria-label values
         → label contains ממוצע or a float → skip
         → else last integer token → add
    → no integer from shapes → same rules on role=img inside the container
no integer added → fail
else → return the sum
```
