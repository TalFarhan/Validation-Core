# Data Model: Population SVG Circle and Value Regex

**Feature**: 025-population-svg-refine | **Date**: 2026-10-15

No new stored records.

## SVG mark total

Used only when `chart_total` is called with `DATES_CHART` or `HOUR_CHART`.

| Field | Type | Rule |
|-------|------|------|
| title | string | `התרעות לפי תאריך` or `גרף התרעות וגם ממוצע לפי שעה`. |
| container | locator | The tight visual container from feature 022. |
| marks | locator | `svg rect, svg path, svg circle` inside that container. The first mark must be visible before labels are read. |
| label | string | The mark's `aria-label`. Empty labels are skipped. |
| value | `int \| none` | The integer after `התרעות`, or the whole label when it is only an integer. |
| total | `int` | Sum of included values. |

`series_index` is not used for these two titles.

## Other totals

District and settlement totals keep the current category-cell sum. They do not use this mark table.

## Validation rules

1. A label containing `ממוצע` contributes nothing, including `0`.
2. A label containing a float, such as `5895.54`, contributes nothing.
3. `תאריך 2026-10-15. התרעות 0.` contributes `0`.
4. `התרעות 5,293` contributes `5293`.
5. A label that is only `5293` contributes `5293`.
6. If no integer was included, `chart_total` raises.

## State transitions

```text
dates or hour title
    → tight visual container
    → wait until the first svg rect, path, or circle is visible
    → aria-label on each of those marks
         → label contains ממוצע or a float → skip
         → label contains התרעות → add the integer after that word
         → label is only an integer → add it
         → otherwise → skip
no integer added → fail
else → return the sum
```
