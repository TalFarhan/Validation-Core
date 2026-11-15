# Contract: Virtualized Power BI Grid Collector

**Feature**: `049-hasbara-ui-validation` | **Module**: `core/components/virtual_grid.py` | **Date**: 2026-11-05

Report-agnostic reader for a Power BI grid that mounts only the rows inside the
viewport. The caller supplies the grid locator, the visible-row extractor, and the
row id. This module does not open Show as a table, does not click Back to report,
and does not know which report it is reading.

`VisualTable.read_rows` keeps the signature in `specs/048-fleet-table-extraction/contracts/visual-table.md`.
The data-cell wait and the call into this collector are internal. `rows_to_label_values`
is unchanged.

## Public surface

```python
def collect_virtualized_rows(
    grid: Locator,
    read_visible: Callable[[Locator], Sequence[Mapping[str, str]]],
    row_id: Callable[[Mapping[str, str]], str],
    *,
    timeout_ms: int,
) -> list[dict[str, str]]: ...
```

`core/components/__init__.py` exports `collect_virtualized_rows` beside `VisualTable`.

## `collect_virtualized_rows`

1. Call `read_visible(grid)` and copy each row into a dict. The key is `row_id(row)`.
   An empty key is ignored. The first row for a key wins. Later passes do not overwrite it.
2. Find the scroll container: the grid element, a descendant, or an ancestor (depth at
   most 12) whose computed `overflow-y` is `auto`, `scroll`, or `overlay`, and whose
   `scrollHeight - clientHeight` is greater than 1. When several match, the largest
   extra height wins.
3. Set that node's `scrollTop` forward by its `clientHeight` (one container height, not
   `clientHeight - 24`). When no container matches, or `scrollTop` does not change, stop.
4. Call `read_visible` again. Stop when the pass adds no new key.
5. Repeat until a stop above, or until `timeout_ms` has elapsed since the call started.
6. Return the stored rows in first-seen order.

`read_visible` and `row_id` are opaque. This module does not mention `request_id`,
`inquiry_id`, Hasbara titles, or fleet labels. Comments and names inside the module
are English. The function does not call `page.wait_for_timeout` and does not call
`wait_for_load_state("networkidle")`.

## Callers

| Caller | `read_visible` | `row_id` |
|--------|----------------|----------|
| `VisualTable._collect_rows` | Existing header-to-cell mapper. Header rows and hidden rows stay skipped there. The grid is the expanded Show-as-a-table grid. | Full cell tuple, joined, so two different rows are not collapsed. |

`PublicInquiriesPage._read_grid` does not call this function on the canvas grid.
It calls `VisualTable.read_rows`, then maps headers and dedupes on `request_id` or
`inquiry_id` on the page. It deletes its private scroll script and does not keep a
second loop. A horizontal sweep inside this collector is not how `handling_time`
is obtained.

## Show as a table wait

Inside `VisualTable.read_rows`, immediately after the Show as a table menu item is
clicked and the visible `grid` or `table` is located, and before `collect_virtualized_rows`:

- Wait until a data cell is visible in that table: `td`, `[role="gridcell"]`, or
  `[role="cell"]` inside a `tr` or `[role="row"]`.
- The wait is `expect(...).to_be_visible`, bounded by the reader's `timeout_ms`.
- Do not read rows before that cell is visible.
- Do not call `wait_for_timeout`.

The menu click, the back button, and the error text stay as they are. A missing data
cell raises through the existing `read_rows` error path. Hasbara chart readers that
catch that error still return `[]`, and the sanity test then fails with `ui=[]` when
the golden block has rows.

After the Back to report button is visible, the grid passed to this collector is the
data-view grid. When more than one visible grid or table has a data cell,
`VisualTable._visible_table` chooses the grid that shares an ancestor with that
button. If several still match, it chooses the one with the most column headers.
A single visible grid is unchanged. Detail-grid callers do not catch a missing menu
item and read the canvas grid instead.

## Screen 4 rendered check

Not part of this module. On `PublicInquiriesPage`:

- `grid_is_rendered("screen_4")` is true only when a feedback-grid column header named
  `הערות` or `הערה` is visible. Implementation confirms that node on the live screen 4
  DOM. If the header has no accessible name, the locator is the visible text `הערות`
  inside the grid.
- `_wait_until_ready("screen_4")` uses that same locator and `expect(...).to_be_visible`
  with `self.timeout`.
- The full parenthetical screen title is not this check.
- Screen 2 keeps its current grid-or-row ready check.

## Invariants

- No report label is a literal in `virtual_grid.py`.
- `core/portal/page.py` is not edited.
- `rows_to_label_values` and the `VisualTable.read_rows` signature are not edited.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Pure label mapping still holds | `pytest tests/unit/test_visual_table_rows.py` |
| Fleet Show as a table still returns chart rows | `pytest tests/ui/fleet_dashboard/` |
| Hasbara grids and charts include golden ids and chart rows | `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity` |
| Screen 4 is not skipped while the comments header is visible | `test_hasbara_screen4_feedback_rows_match_golden` |
