# Phase 0 Research: Dates Table from the Right-Click Menu

**Feature**: 027-dates-table-menu | **Date**: 2026-10-15

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Right-click, then הצג כטבלה

**Decision**: For `DATES_CHART` only, dismiss any overlay that is already open, right-click
the tight visual container with `click(button="right")`, then click the menu item
`הצג כטבלה`. If that item is absent, click `Show as a table`. Do not press
`Alt+Shift+F11`. Do not dismiss the menu overlay before the item click.

**Rationale**: On 2026-10-15 the shortcut did not open a table whose `התרעות` column
contained integers. The context menu is the visible command for the same Power BI view.
The hour chart stays on `_svg_mark_total`. The district chart stays on `_rows_for_total`.

**Alternatives considered**:

- *Send `Alt+Shift+F11` again*: rejected. The live run raised `has no accessible table`.
- *Scroll the zoom slider*: rejected. The user ruled that out.

## Decision 2 — Rows and grid cells under the alerts header

**Decision**: After the menu click, wait until a visible grid or table has a
`role="columnheader"` whose text is `התרעות`, has `role="row"` elements, and has at least
one integer in that column's `role="gridcell"` list. A grid that only has the header is
ignored. Skip a row that contains a column header. Skip a row whose cell text is `סה"כ`
or starts with `סה"כ`. The cell index matches the header index. `5,293` is `5293`. `0` is
included. A missing menu item or a table with no integer raises `AssertionError` naming
the dates chart.

**Rationale**: Power BI draws the data table with ARIA roles. The population page already
has other grids. The chart chrome can expose a header named `התרעות` without integer body
cells. That grid was matched on the shortcut run and is not the data table.

**Alternatives considered**:

- *Read the first `role="row"` on the page*: rejected. Slicer grids are already present.
- *Fall back to the circle sum*: rejected. That sum is the zoomed `0`.

## Decision 3 — Back to report is חזרה לדוח

**Decision**: Click a visible button whose accessible name is `חזרה לדוח`. Then wait until
the dates chart title is visible. If that button is absent, raise `AssertionError`.

**Rationale**: The previous reader looked for a button named exactly `חזרה` or `Back`.
The control that leaves this view is `חזרה לדוח`. The three-chart test reads the district
chart after the dates total, so the table must be closed first.

**Alternatives considered**:

- *Press Escape*: rejected. The user named `חזרה לדוח`.
- *Leave the table open*: rejected. The district reader must see the canvas.

## Decision 4 — The other two charts stay

**Decision**: `HOUR_CHART` still calls `_svg_mark_total`. `DISTRICT_CHART` and
`SETTLEMENT_CHART` still call `_rows_for_total`. The three-chart test is not edited.

**Rationale**: Those two readers already agree at `141493`. This slice changes the way the
dates table is opened and closed.
