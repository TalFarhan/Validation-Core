# Data Model: Scroll the Dates Table and Filter District Rows

**Feature**: 030-scroll-visible-totals | **Date**: 2026-10-18

No new stored records.

## Scrolled dates column

Used when `chart_total` is called with `DATES_CHART`.

| Field | Type | Rule |
|-------|------|------|
| table | locator | The grid opened by `הצג כטבלה`. |
| column | int | Index of the `התרעות` column header. |
| row | locator | One `role="row"`. Added only when `is_visible()` is true. |
| key | string | `aria-rowindex`, or the row-header text when the index is absent. |
| value | int | The visible `התרעות` grid cell, including `0`. |
| collected | map of key to int | One entry per visible row. A later viewport does not add the same key again. |
| total | int | Sum of `collected` after the scroll stops. |

## Visible district column

Used when `chart_total` is called with `DISTRICT_CHART`.

| Field | Type | Rule |
|-------|------|------|
| container | locator | The tight visual container for `התרעות לפי מחוז`. |
| row | locator | A `role="row"` in that container. Added only when `is_visible()` is true. |
| settled | pair of ints | Two consecutive `(total, included)` reads that are equal. |
| total | int | The settled sum. |

## Other totals

| Title | Reader |
|-------|--------|
| `גרף התרעות וגם ממוצע לפי שעה` | `_svg_mark_total` |
| `אוכלוסייה מותרעת לפי יישוב` | `_rows_for_total` |

## Validation rules

1. A dates row that fails `is_visible()` contributes nothing, including during a later scroll step.
2. A dates key already in `collected` is not added again.
3. The dates scroll ends after two passes with no new key and no scroll movement, or at `self.timeout`.
4. A district row that fails `is_visible()` contributes nothing.
5. The district sum is returned only after the visible read has repeated.
6. A header row and a `סה"כ` row contribute nothing for either total.
7. The dates method returns only after `חזרה לדוח` and the dates title is visible.

## State transitions

```text
dates title
    → right-click → הצג כטבלה
    → visible rows → store by key
    → scroll one step
         → new visible key → store
         → hidden row → skip
         → no movement and no new key, twice → stop
    → חזרה לדוח
    → return the sum

district title
    → visible rows inside the district container
         → still changing → wait
         → same sum twice → return that sum
         → hidden row → skip
```
