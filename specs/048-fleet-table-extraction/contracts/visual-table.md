# Contract: Visual Table Reader (Layer 2)

**Feature**: `048-fleet-table-extraction` | **Module**: `core/components/visual_table.py` | **Date**: 2026-11-04

Generic Power BI "Show as a table" reader. The caller supplies the visual locator.
Titles, measure names, and total-row tokens are opaque. This contract does not cover
hover, tooltips, or drill-down.

## Public surface

```python
class VisualTable:
    def __init__(
        self,
        page: Page,
        frame: FrameLocator,
        timeout_ms: int | None = None,
    ) -> None: ...

    def read_rows(
        self,
        container: Locator,
        *,
        name: str = "visual",
    ) -> list[dict[str, str]]: ...

def rows_to_label_values(
    rows: Sequence[Mapping[str, str]],
    *,
    skip_labels: Sequence[str] = (),
) -> dict[str, int]: ...
```

`core/components/__init__.py` exports `VisualTable`. `Chart` stays exported and is
not modified.

## `read_rows`

1. Right-click `container` (`button="right"`). Do not resolve a title.
2. Click the first visible exact `menuitem` named `הצג כטבלה` or, if that item does
   not appear, `Show as a table`. Search `frame`, then `page`. A short wait per
   candidate leaves time for the other label. Missing both raises `AssertionError`
   whose message may include `name`.
3. Find a visible `grid`, or else `table`, in `frame`. Read `columnheader` texts in
   order. Data cells are `gridcell` or `cell` in that same order.
4. Scroll the scrollable ancestor from the top in page steps. Store each data row
   once, keyed by the full cell tuple. Skip a row whose cells equal the headers.
   Skip a row that is not visible. Stop after two passes that add no row and do not
   move the scroll position, or at `timeout_ms`.
5. Return `list[dict[str, str]]`. Dict order is header order. Cell text is trimmed
   and has bidi marks removed. Do not parse numbers. Do not drop a total row here.

The back button step runs in `finally` when step 2 has clicked the menu item:

- Click the first visible exact `button` named `חזרה לדוח` or `Back to report`,
  searching `frame` then `page`, with the same short-wait pattern.
- Then wait until that button is hidden, bounded by `timeout_ms`.
- A missing back button raises `AssertionError` after the attempt. The row result
  is not returned in that case.

`timeout_ms` defaults to `settings.DEFAULT_TIMEOUT` when omitted. The fleet page
passes `self.timeout`.

## `rows_to_label_values`

Pure. No Playwright.

For each row, in order, read cell values in dict order:

- If any cell equals a `skip_labels` entry or starts with one, omit the row.
- Label is the first cell that is not a pure number and not only a percent. Strip one
  trailing `N` or `N (P%)` from that cell. Collapse a doubled Power BI label
  (`מחוז דןמחוז דן` → `מחוז דן`) the same way `Chart` already does.
- Value is the first pure integer cell. Remove `,`, spaces, and bidi marks before
  parsing. If no pure integer exists, use the leading integer of an `N (P%)` cell.
- `0` is stored. A missing label or missing integer omits the row.
- The first stored label wins.

## Invariants

- No fleet chart title, vehicle term, or measure header is a literal in this module.
- The four chrome strings in `read_rows` are the only new user-facing literals.
- `read_rows` does not call `rows_to_label_values`.
- Comments inside the functions are English.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Integer mapping, total-row skip, pie `N (P%)`, first-wins, zero | `tests/unit/test_visual_table_rows.py` |
| Menu, scroll, and back click | Fleet `read_chart_segments` against the live report (quickstart) |
