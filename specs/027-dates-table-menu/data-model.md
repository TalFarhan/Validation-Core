# Data Model: Dates Table from the Right-Click Menu

**Feature**: 027-dates-table-menu | **Date**: 2026-10-15

No new stored records.

## Dates menu table

Used only when `chart_total` is called with `DATES_CHART`.

| Field | Type | Rule |
|-------|------|------|
| container | locator | The tight visual container for `התרעות לפי תאריך`. It receives the right-click. |
| menu item | locator | `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent. |
| table | locator | The visible grid or table with a `התרעות` column header, rows, and at least one integer grid cell in that column. |
| column | int | Index of the `role="columnheader"` whose text is `התרעות`. |
| row | locator | One `role="row"`. A header row and a row containing `סה"כ` are skipped. |
| cell | string | The `role="gridcell"` at `column`. |
| value | `int \| none` | The cell with thousands separators removed, when the result is an integer. |
| total | `int` | Sum of included values. |

`series_index` is not used for this title.

## Other totals

| Title | Reader |
|-------|--------|
| `גרף התרעות וגם ממוצע לפי שעה` | `_svg_mark_total` |
| `התרעות לפי מחוז` and `אוכלוסייה מותרעת לפי יישוב` | `_rows_for_total` |

## Validation rules

1. The menu item is clicked only after the right-click. An already-open overlay is dismissed before the right-click, and the new menu is left up.
2. `5,293` is `5293`. `0` is included.
3. A header row contributes nothing.
4. A row that contains `סה"כ` contributes nothing, including `0`.
5. A missing menu item, a missing integer column, or a missing `חזרה לדוח` button fails the total.
6. `chart_total` returns only after the dates chart title is visible again.

## State transitions

```text
dates title
    → right-click the visual container
    → click הצג כטבלה
    → rows with an התרעות column header
         → header row → skip
         → row contains סה"כ → skip
         → else integer grid cell in that column → add
    → click חזרה לדוח
    → dates chart title visible
    → return the sum
```
