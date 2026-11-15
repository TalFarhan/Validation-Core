# Data Model: Dates Chart Accessible Table

**Feature**: 026-dates-accessible-table | **Date**: 2026-10-15

No new stored records.

## Dates table total

Used only when `chart_total` is called with `DATES_CHART`.

| Field | Type | Rule |
|-------|------|------|
| container | locator | The tight visual container for `התרעות לפי תאריך`. It receives the click. |
| table | locator | The visible `role="grid"`, or else `role="table"`, whose header cell is `התרעות`. |
| column | int | Index of the header cell whose text is `התרעות`. |
| row | locator | One body row. A header row and a row containing `סה"כ` are skipped. |
| cell | string | The text of that row in `column`. |
| value | `int \| none` | The cell with thousands separators removed, when the result is an integer. |
| total | `int` | Sum of included values. |

`series_index` is not used for this title.

## Other totals

| Title | Reader |
|-------|--------|
| `גרף התרעות וגם ממוצע לפי שעה` | `_svg_mark_total` |
| `התרעות לפי מחוז` and `אוכלוסייה מותרעת לפי יישוב` | `_rows_for_total` |

## Validation rules

1. The shortcut runs only after the dates container is clicked.
2. `5,293` is `5293`. `0` is included.
3. A header row contributes nothing.
4. A row that contains `סה"כ` contributes nothing, including `0`.
5. A missing table, a missing `התרעות` column, or a missing back button fails the total.
6. `chart_total` returns only after the dates chart title is visible again.

## State transitions

```text
dates title
    → click the visual container
    → Alt+Shift+F11
    → grid or table with an התרעות header
         → header row → skip
         → row contains סה"כ → skip
         → else integer in the התרעות column → add
    → click חזרה, or Back
    → dates chart title visible
    → return the sum
```
