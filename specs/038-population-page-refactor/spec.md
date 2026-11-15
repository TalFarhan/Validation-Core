# Feature Specification: Population Page Internal Refactor

**Feature Branch**: `feature/reportportal-integration` (spec directory `038-population-page-refactor`; git checkout stays put)

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Internal refactoring and consolidation of AlertsPopulationPage. Preserve the public API. Do not edit tests under tests/sanity/ or tests/ui/. Comments inside functions must be English."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Existing readers keep their results (Priority: P1)

A validation author runs the alerts population sanity and UI suites exactly as they are written today. Every public method on `AlertsPopulationPage` still accepts the same arguments and returns the same kind of result: card numbers, chart totals, district and hour maps, date counts, and settlement counts.

**Why this priority**: The file is about 1,450 lines of technical debt, but the suites are the contract. A cleaner private implementation that changes a sum, a skip, or a method signature is a failed refactor.

**Independent Test**: Run the existing population unit check and the existing sanity and UI modules without editing those files. Public signatures match the list in the contract.

**Acceptance Scenarios**:

1. **Given** the current tests under `tests/sanity/` and `tests/ui/`, **When** this slice is implemented, **Then** those files are byte-for-byte unchanged and the public methods listed in the contract keep their names, parameters, and defaults.
2. **Given** a dates, district, hour, or card read that succeeds today, **When** the private helpers are consolidated, **Then** the same read still returns that value, including `0`.
3. **Given** a missing district container or an hour average that cannot be paired, **When** the reader runs, **Then** it still returns an empty map instead of raising, so the existing skip messages stay.

---

### User Story 2 - One scroll loop, one row script, one hover loop (Priority: P1)

A maintainer changes how a virtualized dates table is scrolled, or how a bar tooltip is parsed, in one place. The dates total and the date-count map share that scroll loop. District and hour tooltips share one hover loop. Row evaluation uses one script.

**Why this priority**: The duplicated loops are the debt that makes the next chart fix easy to apply in one path and miss in another.

**Independent Test**: The dates total and `read_date_counts()` both call the single scroll collector. `read_district_labels()` and `read_hour_buckets()` call the single hover helper only on their existing empty-map fallback. No second copy of the row script remains in the two entry helpers.

**Acceptance Scenarios**:

1. **Given** the dates chart opened as a table, **When** the total and the date map are collected, **Then** both scroll from the top, keep each visible row once, and stop after two passes that add nothing and do not move.
2. **Given** a row that is in the DOM but not visible, **When** either dates read runs, **Then** that row is not stored.
3. **Given** district rows or hour mark labels that already produced a map, **When** those readers run, **Then** they do not hover.
4. **Given** both of those reads are empty, **When** a visible bar has a tooltip, **Then** one shared hover loop supplies the district name map or the hour sum map.

---

### User Story 3 - Private Chart access, broad catches, and blind waits are gone (Priority: P2)

A maintainer can see which failures are a missing control and which are a Playwright timeout. The population page does not call private methods on `Chart`. Fixed delays that only wait for an element to appear become visibility waits.

**Why this priority**: Encapsulation leaks and `except Exception` hide the next failure. They are safe to clean up only after the public results in Story 1 stay put.

**Independent Test**: Search `population_page.py` for `_chart._container`, `_chart._parse`, `except Exception`, and `time.sleep`. None remain. Appearance waits use a visible state. Numeric settle loops still wait until two reads match.

**Acceptance Scenarios**:

1. **Given** Sum or average mode on the district chart, **When** `set_district_aggregation` runs, **Then** it scopes the button with the page's own visual locator and still clicks the single exact button, or the first frame button when that count is not 1.
2. **Given** `read_chart_categories`, **When** it parses a chart, **Then** it calls a public `Chart` method with the page-scoped container and gets the same categories and series the private parse returns today.
3. **Given** a locator timeout or a detached node, **When** a helper used to swallow `Exception`, **Then** it swallows `playwright.sync_api.Error` (which includes `TimeoutError`) and still lets `AssertionError` propagate except where a reader already turns a missing chart into an empty map.
4. **Given** a menu item or a chart title that must appear, **When** the page waits, **Then** it waits for that locator to be visible. A loop that waits for two equal numbers stays a poll.

---

### Edge Cases

- `tests/sanity/` and `tests/ui/` are not edited.
- `data/alerts/db_sanity_am_kalavi.yaml` is not edited.
- Comments inside new and edited functions are English.
- `_sum_scrolled_alert_column` has no caller. Its hidden-row sum and final scroll-to-end must not become the dates total.
- `_plain_cell` strips text and collapses a doubled label from length 2. `Chart._dedupe_doubled` does not strip and collapses from length 4. The page helper stays. The private core helper is not imported.
- There is no `time.sleep` in the page today. The fixed delays are `page.wait_for_timeout`. Playwright 1.61's Python `expect` has no `poll`.
- There is no `ElementHandleError` in Playwright 1.61. Detached nodes and timeouts are `playwright.sync_api.Error`.
- The district chart scroll (`_scroll_visual`) is a different script from the dates-table scroll. This slice does not merge those two scripts.
- A tooltip hover still runs only after the cheaper district or hour read is empty.
- `0` remains a real count. A summary row (`סה"כ`) stays omitted. Average and fractional hour labels stay out of the sum reader.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Public methods on `AlertsPopulationPage` MUST keep the names, parameters, and defaults in `contracts/population-page.md`. No test file under `tests/sanity/` or `tests/ui/` is edited.
- **FR-002**: `_sum_scrolled_visible_alert_column`, `_collect_date_counts`, and the unused `_sum_scrolled_alert_column` MUST be replaced by one private scroll collector. The dates total and the date-count map MUST use it. The collector MUST scroll to the top, then page down, store only visible rows, and stop at `self.timeout` or after two passes that add no key and do not move.
- **FR-003**: The dates total MUST still return the sum of the collected integers and the included count. `read_date_counts()` MUST still return `{date header: int}`. A hidden row MUST NOT be stored. The unused scroll-to-end path MUST NOT be called.
- **FR-004**: `_visible_alert_entry` and `_visible_date_entry` MUST evaluate one shared row script. Python key policy stays: the alerts total keys by `aria-rowindex` or the row header; date counts key by the row header only. Header rows and `סה"כ` rows stay omitted. The alerts cell MUST still be a `gridcell`.
- **FR-005**: The same row script MUST replace the other copies of that cell query in this file. Each caller's skip rules stay as they are.
- **FR-006**: District name tooltips and hour-sum tooltips MUST share one private hover method. The district parser and `_hour_bucket` stay separate. The hover still skips hidden marks, caps the walk, and dismisses the overlay afterward. It still runs only when the earlier read is empty.
- **FR-007**: `population_page.py` MUST NOT call `Chart._container` or `Chart._parse`. `set_district_aggregation` MUST locate the district visual with the page locator. `read_chart_categories` MUST call a public report-agnostic `Chart` method that parses a caller-supplied container and returns the same categories and series as today's private parse, including a reading `Chart.read` would blank as empty.
- **FR-008**: `_plain_cell` MUST remain the page's strip-and-collapse helper. It MUST NOT call `Chart._dedupe_doubled`. `core/` MUST NOT gain alerts titles or Hebrew labels.
- **FR-009**: Bare `except Exception` MUST be removed from `population_page.py`. Playwright failures MUST be caught as `playwright.sync_api.Error`. `AssertionError` from a missing visual MUST still become an empty map in `read_district_labels` and in the hour-average category fallback, and MUST still propagate everywhere else that raises it today.
- **FR-010**: `time.sleep` MUST NOT be introduced. A wait whose target is a menu item, a grid, or a title MUST use `locator.wait_for(state="visible")` or `expect(...).to_be_visible`. A wait whose target is two equal numeric reads MUST stay a deadline poll. The interval inside that poll MAY be `page.wait_for_timeout` because this Playwright build has no `expect.poll`. New unconditional delays MUST NOT be added.
- **FR-011**: After a hierarchy click, the page MUST NOT sleep a fixed 800 ms before a check that does not observe the new level. It MUST wait for `aria-pressed` or `aria-selected` on the clicked control when that attribute exists, and otherwise keep the district-title visibility check.
- **FR-012**: Comments inside new and edited functions MUST be English. The dates table MUST still close with `חזרה לדוח` before the public dates methods return.

### Key Entities

- **Public page method**: A method tests already call. Its signature and observable result stay.
- **Scrolled row map**: `dict[str, int]` built while a table scrolls. Keys are either a stable row identity or a date header. Values are alert integers, including `0`.
- **Visible row payload**: `rowIndex` plus the row's header and grid cells (`role`, `text`) from one script.
- **Hover map**: `dict[str, int]` from visible bar tooltips. District keys are names. Hour keys are `HH:MM`.
- **Chart categories**: The pair `(categories, series)` for one page-scoped visual container.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) is not edited. No alerts label is added to `core/`.
- **AC-002**: `AlertsPopulationPage` still inherits `AlertsAnalysisPage` and does not re-implement login, catalog search, iframe wait, or last-refresh.
- **AC-003**: Report-ready state stays the district-chart locator on this page.
- **AC-004**: Public test-facing methods keep their contracts. Tests are not updated in this change.
- **AC-005**: The only Layer 2 edit is a report-agnostic public wrapper around the existing chart parse. It accepts a locator and an opaque title. It does not load `data/alerts/` and does not contain report titles.
- **AC-006**: The page stays `pages/alerts_analysis/population_page.py`. No SQL move.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every public signature in the contract is unchanged, and no file under `tests/sanity/` or `tests/ui/` differs from the parent revision.
- **SC-002**: `population_page.py` contains one scroll collector for the two dates reads, one row-cell script, and one hover loop. It contains no call to `Chart._container` or `Chart._parse`, no `except Exception`, and no `time.sleep`.
- **SC-003**: The existing population unit test passes without a browser. The existing sanity and UI tests are the live check and are not rewritten.
- **SC-004**: Because `core/components/chart.py` gains one public method, `pytest` on `tests/ui/fleet_dashboard/` is the Layer 2 gate and MUST pass at 100%. Fleet page objects are not edited.
- **SC-005**: A missing chart still produces the empty map the current skip tests already handle. A present `0` is still stored.

## Assumptions

- The git checkout stays `feature/reportportal-integration`. This slice does not create or switch a branch.
- "Public API" means the methods and class constants tests and other pages already import. Private helpers may be renamed, merged, or deleted.
- `_sum_scrolled_alert_column`, `_collect_alert_rows`, `_first_row_key`, `_sum_alert_column`, and `_settled_visible_alert_total` have no callers in this file. Unreferenced private methods are deleted after the merge. A method that a public reader still calls stays.
- Live portal auth is required for sanity and UI. The unit test is the check that does not need it.
- Installing a newer Playwright only to obtain `expect.poll` is out of scope.
