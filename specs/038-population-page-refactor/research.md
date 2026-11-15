# Research: Population Page Internal Refactor

## Decision 1 — Do not retarget feature 037

**Decision**: Plan this refactor in `specs/038-population-page-refactor`. Leave `specs/037-screen2-chart-readers/` as it is. Stay on `feature/reportportal-integration`.

**Rationale**: Feature 037 already has a plan for hierarchy readers and the hour daily average. `.specify/feature.json` pointed at that directory when planning started. Overwriting it would replace an unrelated slice. This repository's recent plans keep the git checkout and pin the spec directory in `feature.json`.

**Alternatives considered**: Filling `specs/037-screen2-chart-readers/plan.md` with this refactor. Rejected because that spec is a different feature and its plan is already written.

## Decision 2 — One visible-row scroll collector, and delete the unused third loop

**Decision**: Replace `_sum_scrolled_visible_alert_column` and `_collect_date_counts` with one private method:

```text
_collect_scrolled_rows(table, column, *, key) -> dict[str, int]
```

`key="stable"` stores `aria-rowindex`, or the row header when the index is empty. The dates total returns `sum(values), len(map)`. `key="header"` stores the row-header text. `read_date_counts()` returns that map.

The loop scrolls to the top, collects visible rows, pages down, and stops at `self.timeout` or after two passes that add no key and report no movement.

`_sum_scrolled_alert_column` has no caller. It sums hidden rows, treats a stuck first-row key as the stop signal, then scrolls to the end and collects again. Delete it, `_collect_alert_rows`, and `_first_row_key`. Do not add a `finish_at_end` or `visible_only=False` mode.

**Rationale**: The two live loops are the same algorithm with a different key. Specs 029 and 030 moved the dates total off the hidden-row sum because that sum counted virtualized DOM text. Merging the dead method back in as a flag would make the next caller able to regress that total. A grep of `population_page.py` shows the dead method only at its definition.

**Alternatives considered**:

- *One method with a mode that still scrolls to the end*: rejected. Nothing calls that mode, and the dates total must not.
- *Leaving three methods that share a helper but keep three loops*: rejected. The user asked for one scrolling method.

## Decision 3 — One row script, caller-specific Python rules

**Decision**: One module-level script, `_ROW_CELLS_JS`, returns `null` for a header row, otherwise `{rowIndex, cells: [{role, text}]}`. `_visible_alert_entry` and `_visible_date_entry` both evaluate it. The alerts total still requires `role="gridcell"` and keys by index or header. Date counts still require `role="gridcell"` and key by the header only. Both still drop `סה"כ`.

The same script replaces the copied evaluate strings in `_visible_alert_value`, `_visible_district_value`, `_visible_district_label`, and `_sum_alert_column` if that last method is still present. Those callers keep their current role checks. `_sum_alert_column` and `_settled_visible_alert_total` have no callers; delete them if they are still unreferenced after the merge.

**Rationale**: The two named scripts differ only by whether they also return `aria-rowindex`. The cell query is identical. The key and the `gridcell` versus `cell` rules are the behavior tests depend on, so they stay in Python.

**Alternatives considered**: One Python function that both keys every row the same way. Rejected because the dates total dedupes by row index when the header text is empty, and date counts drop a row that has no header.

## Decision 4 — One hover loop, two parsers

**Decision**: Add `_hover_mark_values(container, parse) -> dict[str, int]`. It walks `svg rect, svg path, svg circle`, skips marks that are not visible, hovers with a 1 second timeout, caps the walk at 40, parses the tooltip text, and dismisses the overlay once. `_tooltip_name_counts` passes a parser that skips `ממוצע`, takes the first integer line as the value, and takes the first other line as the name. `_hour_tooltip_buckets` passes `_hour_bucket`.

`read_district_labels()` and `read_hour_buckets()` still hover only when the earlier reads returned an empty map.

**Rationale**: The two loops match. The parsers do not: the hour parser reads the whole tooltip and drops averages, and the district parser pairs a name line with an integer line. Constitution VII keeps tooltips on the domain page.

**Alternatives considered**: Moving hover into `Chart`. Rejected. The chart module documents that tooltips stay on the domain page, and the parsers are alerts-specific.

## Decision 5 — Replace `Chart._container` with the page locator, and publish `parse_container` instead of calling `Chart.read`

**Decision**: `set_district_aggregation` resolves the district visual with `_visual_container(DISTRICT_CHART)`. When that count of exact Sum or average buttons is 1, click it. Otherwise click the first exact button in the report frame. If `_visual_container` raises `AssertionError`, use the frame fallback. Do not call `Chart._container`.

`read_chart_categories` keeps using `_visual_container` and calls a new public method:

```text
Chart.parse_container(container, title) -> tuple[categories, series]
```

The method calls the existing `_parse` and returns the categories and series. It does not call `reading_state` and does not clear an empty reading. `Chart.read` is unchanged.

**Rationale**: `Chart._container` and `_visual_container` are different lookups. The page helper skips a box that contains another chart title and skips a title node that has no digit. `Chart.read` uses `_container`, waits until that node is visible, parses the displayed title rather than the anchor, and returns empty categories when the reading state is empty. Hour sum and hour average call `read_chart_categories` as a fallback. Switching them to `Chart.read` can change that fallback. A thin public wrapper removes the private call without that change. The wrapper is report-agnostic: the title and the locator are caller data.

**Alternatives considered**:

- *Call `Chart.read(title, scope=PAGE_TITLE)`*: rejected. Different container and an empty wipe.
- *Copy `_parse` onto the page with Playwright locators*: rejected. That duplicates Layer 2 and will drift.
- *Import `_parse`*: rejected. The user forbade private Chart calls.

## Decision 6 — Keep `_plain_cell`; do not import `_dedupe_doubled`

**Decision**: Leave a page-local helper that strips the string, then collapses it when `len >= 2`, the length is even, and the two halves match. Do not import `chart._dedupe_doubled`. Do not add a public dedupe function to `core/`.

**Rationale**: `_dedupe_doubled` does not strip, and it collapses only when `len >= 4`. `_plain_cell` strips first and collapses from length 2. Importing the private helper is another encapsulation leak, and swapping it in would change short doubled cells. The page helper is the one the table keys already use.

**Alternatives considered**: Export `dedupe_doubled` and call it after `strip`. Rejected for the length threshold, and because a new core helper is not required for one caller whose behavior already differs.

## Decision 7 — Catch `playwright.sync_api.Error`, not `Exception` and not `ElementHandleError`

**Decision**: Import `Error` from `playwright.sync_api` (optionally aliased). Catch `Error` where a helper today catches `Exception` around `count`, `is_visible`, `evaluate`, `inner_text`, `get_attribute`, `hover`, or `text_content`. `TimeoutError` subclasses `Error`, so one clause covers timeouts and detached nodes.

Keep `except AssertionError` in `read_district_labels` when `_visual_container` fails, and in `read_hour_daily_avg` around `read_chart_categories`. Those paths return `{}` so the existing tests can skip. Every other `AssertionError` still propagates, including an empty chart total and a missing back button.

**Rationale**: Playwright 1.61.0 is installed. `playwright.sync_api` exports `Error` and `TimeoutError`. It does not export `ElementHandleError`. A bare `Exception` also hides `AttributeError` and `AssertionError`. Narrowing the hour-average fallback to Playwright errors alone would turn a missing container into a failure instead of an empty map.

**Alternatives considered**: Catching `TimeoutError` only. Rejected because `evaluate` on a detached node raises `Error`, not `TimeoutError`.

## Decision 8 — Visibility waits for appearance; a poll for stable numbers

**Decision**: Do not add `time.sleep`. There is no `time.sleep` in the file today; `import time` stays for `time.monotonic`.

Replace appearance delays:

- The show-as-table menu and the alerts grid wait with `locator.wait_for(state="visible")` inside the existing Hebrew/English and grid/table fallbacks, bounded by `self.timeout`.
- The back button and the dates title already use `expect(...).to_be_visible`. Keep that.
- `set_hierarchy_level` drops the unconditional `wait_for_timeout(800)`. If the clicked control has `aria-pressed` or `aria-selected`, wait for the selected value with `expect(control).to_have_attribute`. If neither attribute exists, keep the district-title visibility check and do not add a new fixed sleep in front of it.

Keep a deadline poll where the success condition is two equal reads: `clear_filters`, `set_date_range`, and `_district_visible_total`. The installed `expect` object has `set_options` and `soft` and does not have `poll` (Playwright 1.61.0). The interval inside those polls may stay `page.wait_for_timeout`. Do not add new unconditional delays. After a dates scroll, poll until the first visible row key changes or the step budget ends; a row that never changes must not raise out of the collector.

**Rationale**: A card or a chart total is already visible while its number is still changing. `wait_for_selector(state="visible")` returns immediately there and would drop the settle. Upgrading Playwright to gain `expect.poll` is a dependency change this refactor does not need.

**Alternatives considered**: Busy-spinning the settle loop with no interval. Rejected because it hammers the iframe. Replacing every `wait_for_timeout` with a visibility wait. Rejected because the hierarchy title and the total card are visible before the data settles.

## Decision 9 — Do not merge `_scroll_visual` into the dates scroller

**Decision**: The district label scroll stays `_scroll_visual`. The dates table scroll stays its own script (parent walk, modes `top` / `page` / `end`). Only the three named collector methods are merged.

**Rationale**: `_scroll_visual` searches descendants and steps once. The dates script walks parents and can jump to the top or the end. Fusing them risks the district label map, which is on the public `read_district_labels` path.

**Alternatives considered**: One generic `scroll(locator, mode)` for both. Rejected for this slice. The user named the three collector methods, not the district scroller.
