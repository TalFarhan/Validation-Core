# Feature Specification: Fix Skipped Tests and Load Errors for Alerts and Status Dashboards

**Feature Branch**: `feature/reportportal-integration` (spec directory `041-fix-dashboard-data-rendering`; git checkout stays put)

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "Resolve the skipped UI chart tests (`pytest.skip`) and `LoadTimeoutError` in the Alerts Analysis and Status Picture dashboards. The root cause is empty data preventing charts (like 'התרעות לפי מחוז') from rendering in the DOM. (1) Alerts Analysis: read the golden `date_range` and set it in the UI date picker before reading charts. (2) Status Picture: refactor `_apply_golden_range` to select the operation by name (e.g. 'עם כלביא') through the slicer/combobox instead of passing `start`/`end` dates. (3) Ensure the data-loading fixes clear the 'Missing Page Object reader' skips and the DOM groups/titles render. (4) Make `navigate()`'s report-ready locator target a consistently visible element (e.g. the main dashboard title) instead of a dynamic chart title. (5) All in-function code comments in English."

## Clarifications

### Session 2026-11-01

- Q: Why do the Alerts chart tests raise `LoadTimeoutError` even though the tests already apply the golden date range? → A: `navigate()` runs in the fixture *before* any test body. The population page's report-ready locator is the `התרעות לפי מחוז` district chart, a data-dependent visual that does not render under the default 7-day empty filter, so navigation times out before the golden range can be applied. The ready locator must be a filter-independent, screen-2-specific element.
- Q: Which element should be the population page's report-ready anchor? → A: The `סה"כ אוכלוסייה` total card (`TOTAL_CARD`). It is an all-time total shown regardless of the date filter and only appears on Screen 2, so it confirms the screen is loaded without depending on filtered data. The `before_report_ready_check()` page-switch decision keeps using the district chart.
- Q: How should Status Picture select its window after the refactor? → A: The test reads an explicit operation name from the golden record and the page selects that option on the `FilterName` slicer directly. The date-to-operation reverse mapping (`_OPERATION_RANGES`) and the `_date_fields_visible()` branch are no longer the selection path for the golden run.
- Q: Where does the operation name live? → A: A new `operation` key under `screen_1_status_picture` in `data/alerts/db_sanity_am_kalavi.yaml`, read by the test. No operation name is hard-coded in the test or page body.
- Q: Is the locator timeout increased again? → A: No. Both Alerts pages already run at `self.timeout = 120_000` (above the former 60s). This slice changes *which* locator is awaited, not the budget. A never-rendering ready anchor still raises `LoadTimeoutError`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Alerts Analysis charts render after the golden range is applied (Priority: P1)

A validation author runs the Screen 2 sanity suite. Navigation reaches the population page even though the default filter shows no chart data, then the test applies the golden `date_range` (`2026-09-01` → `2026-10-18`) and every district/hierarchy/date/hour chart reader returns rows instead of skipping.

**Why this priority**: This is the primary failure. If `navigate()` times out on the empty district chart, no Screen 2 chart test can run.

**Independent Test**: Run `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` with portal auth. It passes when the suite reaches its assertions without `LoadTimeoutError` and no chart test skips with an empty-reader message.

**Acceptance Scenarios**:

1. **Given** the default empty 7-day filter, **When** the population page is navigated, **Then** `navigate()` resolves on a filter-independent anchor (`TOTAL_CARD`) and does not raise `LoadTimeoutError`.
2. **Given** a navigated population page, **When** a chart test applies the golden `date_range` before reading, **Then** the district chart `התרעות לפי מחוז` renders rows and the test asserts against the golden values.
3. **Given** the ready anchor never appears (a genuine load failure), **When** the budget is exhausted, **Then** `navigate()` still raises `LoadTimeoutError`.

---

### User Story 2 - Status Picture selects the operation by name (Priority: P1)

A validation author runs the Screen 1 sanity suite. The setup selects the named operation (`עם כלביא`) on the slicer/combobox directly, the status-picture visuals populate, and the card/category/ranking readers return values.

**Why this priority**: Screen 1 charts stay empty until the operation is selected. Selecting by name removes the brittle date-to-operation reverse mapping and makes the intent explicit.

**Independent Test**: Run `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` with auth. It passes when the operation is selected by name and the Screen 1 readers (`read_cards`, `read_alerts_by_category`, `read_top_10_settlements`) return populated maps.

**Acceptance Scenarios**:

1. **Given** the Screen 1 golden record with an `operation` name, **When** the setup runs, **Then** the page selects that option on the `FilterName` slicer and the warning-zones gauge settles on the new value.
2. **Given** the operation is selected, **When** `read_top_10_settlements` runs, **Then** it returns the ten settlements instead of skipping with `Missing Page Object reader for top_10_settlements`.
3. **Given** the operation name is absent from the slicer options, **When** selection is attempted, **Then** the page raises a clear assertion naming the missing operation.

---

### User Story 3 - Skipped tests resolve and required DOM renders (Priority: P1)

The data-loading fixes above remove the `pytest.skip` paths that fired on empty readers, and the required groups/titles (district chart, category cards, ranking group) are present for the locators.

**Why this priority**: The request explicitly asks that the fixes turn skips into real assertions, not that the skip guards are deleted.

**Independent Test**: Run both sanity modules. No test reports a skip caused by an empty reader when data is present; the skip guards remain only as a safety net for a genuinely absent control.

**Acceptance Scenarios**:

1. **Given** data is loaded, **When** the Screen 2 and Screen 1 readers run, **Then** no test skips with an empty-reader or missing-reader message.
2. **Given** a control is genuinely not rendered, **When** the reader returns nothing, **Then** the existing skip guard still fires with its descriptive message (behavior preserved).

---

### User Story 4 - Report-ready locator is a consistently visible element (Priority: P1)

Every report page's `navigate()` waits for a consistently visible, filter-independent element rather than a dynamic chart title that depends on data.

**Why this priority**: A data-dependent ready anchor couples navigation success to filter state, which is the root cause of the Alerts `LoadTimeoutError`.

**Independent Test**: Inspect `_report_ready_locator()` on the Alerts pages. The population page's anchor is filter-independent (`TOTAL_CARD`), not the district chart; a cold load reaches `after_navigate()`.

**Acceptance Scenarios**:

1. **Given** the population page, **When** `_report_ready_locator()` is evaluated, **Then** it returns a consistently visible Screen 2 element (`TOTAL_CARD`), not `DISTRICT_CHART`.
2. **Given** the status-picture page, **When** its ready anchor is evaluated, **Then** it is a consistently visible Screen 1 element (the warning-zones gauge card), not a data-dependent chart title.

---

### Edge Cases

- The default 7-day empty filter must not cause navigation failure; the ready anchor is filter-independent.
- A genuinely never-rendering report still raises `LoadTimeoutError` so a real failure is not hidden.
- An operation name that is not in the slicer options fails with a clear message, not a silent skip.
- The page-switch heuristic in `before_report_ready_check()` keeps using the district chart to decide Screen 1 → Screen 2 navigation; only the *ready* anchor changes.
- The golden file is edited only to add the `operation` name under Screen 1; no metric value changes.
- Fleet modules are not edited.
- Comments inside new or edited functions are English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Alerts Analysis Screen 2 chart tests MUST read the golden `date_range` from `data/alerts/db_sanity_am_kalavi.yaml` and apply it to the UI date picker before reading any chart. No date is hard-coded in the test body.
- **FR-002**: `AlertsPopulationPage._report_ready_locator()` MUST target a consistently visible, filter-independent Screen 2 element (`TOTAL_CARD`) so `navigate()` does not raise `LoadTimeoutError` under the default empty filter. A never-rendering anchor MUST still raise `LoadTimeoutError`.
- **FR-003**: The status-picture setup (`_apply_golden_range`) MUST select the operation by name through the slicer/combobox, using an operation name read from the golden record, instead of passing `start`/`end` dates.
- **FR-004**: `data/alerts/db_sanity_am_kalavi.yaml` MUST gain an `operation` name under `screen_1_status_picture`; no existing metric value is changed.
- **FR-005**: After the data-loading fixes, the Screen 1 and Screen 2 chart readers MUST return populated values so tests assert instead of skipping, while the existing skip guards remain as a safety net for a genuinely absent control.
- **FR-006**: Selecting an operation name that is not present in the slicer options MUST fail with a message naming the missing operation.
- **FR-007**: The report-ready anchor on each Alerts page MUST be a consistently visible element, not a data-dependent chart title; `before_report_ready_check()` MAY keep using the district chart only for the Screen 1 → Screen 2 page-switch decision.
- **FR-008**: This slice MUST NOT edit any fleet module, `core/portal`, `core/components`, or the root `conftest.py`. The only `data/` edit is the Screen 1 `operation` name.
- **FR-009**: Comments inside new or edited functions MUST be English.

### Key Entities

- **Report-ready anchor**: A filter-independent, screen-specific element a page waits for in `navigate()` (`TOTAL_CARD` for Screen 2; the warning-zones gauge card for Screen 1).
- **Operation selection**: A named option on the `FilterName` slicer (e.g. `עם כלביא`) read from the golden record and selected directly.
- **Golden date range**: The Screen 2 `date_range` (`2026-09-01` → `2026-10-18`) applied to the date picker before chart reads.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` are not edited. The ready-locator change is an override on the domain page, which already overrides `_report_ready_locator()`.
- **AC-002**: The Alerts page objects keep inheriting `AlertsAnalysisPage` → `ReportShell`. No portal step is added or removed; only which locator is awaited changes.
- **AC-003**: Public reader names and return types on the Alerts pages are unchanged (`read_district_labels`, `read_cards`, `read_alerts_by_category`, `read_top_10_settlements`, `set_hierarchy_level`, `set_district_aggregation`, `set_date_range`). A new operation-selection method, if added, is additive.
- **AC-004**: `core/` does not load `data/alerts/`. The sanity tests load the golden file.
- **AC-005**: No new report page and no new SQL client.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With auth, the Screen 2 sanity suite reaches its assertions without `LoadTimeoutError` under the default empty filter.
- **SC-002**: With auth, no Screen 1 or Screen 2 chart test skips with an empty-reader or missing-reader message when data is present.
- **SC-003**: The status-picture setup selects the operation by name read from the golden record, and the warning-zones gauge settles on the new value.
- **SC-004**: `AlertsPopulationPage._report_ready_locator()` is `TOTAL_CARD`, and a deliberately broken anchor still raises `LoadTimeoutError`.
- **SC-005**: No fleet module, `core/`, or root `conftest.py` is edited; the only `data/` change is the Screen 1 `operation` name.

## Assumptions

- The `FilterName` slicer exposes `עם כלביא` as a selectable option on Screen 1, as the existing `_OPERATION_RANGES` path already assumes.
- `TOTAL_CARD` (`סה"כ אוכלוסייה`, all-time total) renders on Screen 2 independent of the date filter.
- The golden date range and operation window describe the same underlying data the readers expect; only the selection mechanism changes for Screen 1.
- Portal auth is required to run the UI tests. This plan does not run the browser.
