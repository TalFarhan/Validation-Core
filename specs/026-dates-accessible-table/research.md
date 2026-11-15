# Phase 0 Research: Dates Chart Accessible Table

**Feature**: 026-dates-accessible-table | **Date**: 2026-10-15

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Open the table from the dates container

**Decision**: For `DATES_CHART` only, dismiss any overlay, click the tight visual container,
then `self.page.keyboard.press("Alt+Shift+F11")`. The hour chart stays on `_svg_mark_total`.
The district chart stays on `_rows_for_total`.

**Rationale**: The visible date circles are the zoomed window. On 2026-10-15 the only labeled
circle was `תאריך 2026-10-15. התרעות 0.`, so the mark sum was `0`. The hour bars and the
district total were both `141493`. Power BI opens the visual's data table when that visual
has focus and receives `Alt+Shift+F11`. Playwright delivers the key to the focused element,
including an element inside the report iframe, after the container click.

**Alternatives considered**:

- *Scroll the zoom slider until every day is visible*: rejected. The user ruled out brittle
  scrolling.
- *Keep summing circles*: rejected. That sum is the zoomed window.
- *Send the shortcut without clicking the chart*: rejected. The shortcut applies to the
  focused visual.

## Decision 2 — Read the grid that has an התרעות column

**Decision**: After the shortcut, wait until a visible `role="grid"` or `role="table"` in the
report frame has a header cell whose text is `התרעות`. Prefer `grid`. If several match, use
the last visible one. Read each body row's cell in that column. Skip a row that contains a
column header. Skip a row whose cells include `סה"כ`. Parse an integer by removing thousands
separators. `5,293` is `5293`. `0` is included. A missing table or a missing column raises
`AssertionError` naming the dates chart.

**Rationale**: The population page already has other grids for slicers. The alert column
header identifies the data table the shortcut opened. A pre-existing slicer grid does not
use that header. Returning `0` from the circle reader would hide a failed shortcut.

**Alternatives considered**:

- *Read the first `role="grid"` on the page*: rejected. Filter grids are already on the page.
- *Fall back to the circle sum when the table is absent*: rejected. That sum is the zoomed `0`.

## Decision 3 — Close the table before returning

**Decision**: Click a visible button named `חזרה`, or if that button is absent a visible
button named `Back`. Then wait until the dates chart title is visible. If neither button is
visible, raise `AssertionError` and leave the failure on the dates total.

**Rationale**: The three-chart test reads the district chart after the dates total. An open
data table would hide that chart. The back control is how Power BI leaves the table view.

**Alternatives considered**:

- *Press Escape*: rejected. The user named the back control, and Escape can close a different
  layer.
- *Leave the table open*: rejected. The next `chart_total` must see the canvas.

## Decision 4 — The other two charts stay

**Decision**: `HOUR_CHART` still calls `_svg_mark_total`. `DISTRICT_CHART` and
`SETTLEMENT_CHART` still call `_rows_for_total`. `test_hour_date_and_district_sums_match` is
not edited.

**Rationale**: The user said those two readers already agree at `141493`. This slice changes
only the dates branch.
