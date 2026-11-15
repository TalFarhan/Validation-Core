# Data Model: Visible Dates Table Rows

**Feature**: 029-dates-visible-rows | **Date**: 2026-10-18

No new stored records.

## Visible dates column

Used only when `chart_total` is called with `DATES_CHART`.

| Field | Type | Rule |
|-------|------|------|
| table | locator | The visible grid or table opened by `הצג כטבלה`. |
| column | int | Index of the `role="columnheader"` whose text is `התרעות`. |
| row | locator | One `role="row"`. Included only when `is_visible()` is true. |
| cell | string | The `role="gridcell"` at `column` on that visible row. |
| value | `int \| none` | The cell with thousands separators removed, when the result is an integer. `0` counts. |
| settled | pair of ints | Two consecutive `(total, included)` reads that are equal. |
| total | `int` | Sum of the visible included values from the settled read. |

## Other totals

| Title | Reader |
|-------|--------|
| `גרף התרעות וגם ממוצע לפי שעה` | `_svg_mark_total` |
| `התרעות לפי מחוז` and `אוכלוסייה מותרעת לפי יישוב` | `_rows_for_total` |

## Validation rules

1. A row that fails `is_visible()` contributes nothing.
2. A header row contributes nothing.
3. A row that contains `סה"כ` contributes nothing.
4. The table is not scrolled while the dates total is taken.
5. The sum is returned only after the visible column has repeated.
6. `chart_total` returns only after `חזרה לדוח` and the dates title is visible again.

## State transitions

```text
dates title
    → right-click
    → click הצג כטבלה
    → visible התרעות integers
         → still changing → wait
         → same sum twice → that sum
         → hidden row → skip
         → header or סה"כ → skip
         → visible integer grid cell → add
    → click חזרה לדוח
    → dates chart title visible
    → return the sum
```
