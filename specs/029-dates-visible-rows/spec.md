# Feature Specification: Visible Dates Table Rows

**Feature Branch**: `feature/reportportal-integration` (spec directory `029-dates-visible-rows`; git checkout stays put)

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "The hours, districts, and dates table all sum to 13 on the dashboard. chart_total for the dates chart returns 5847 because it reads hidden or stale rows. Sum only visible cells after the table has settled. Remove any xfail. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The dates total is the visible table (Priority: P1)

A validation author totals the dates chart after the date range is applied. The page opens the data table, waits until the visible alert cells stop changing, and adds only those visible integers.

**Why this priority**: Manual reading of the filtered dashboard shows 13 for the hour chart, the district chart, and the dates table. The automation returns 5847 for the dates chart.

**Independent Test**: `test_hour_date_and_district_sums_match` has no expected-fail mark, and `hour_total == district_total == dates_total`. On the current filtered dashboard that shared value is 13.

**Acceptance Scenarios**:

1. **Given** the dates table has just opened, **When** the visible `התרעות` integers are still changing, **Then** the total waits until two consecutive reads of those visible integers match.
2. **Given** a row is in the DOM and is not visible, **When** the dates total is taken, **Then** that row is not added.
3. **Given** a visible data row, **When** its `התרעות` grid cell is an integer, **Then** that integer is added, including `0`.
4. **Given** the three charts on the filtered page, **When** the test compares them, **Then** the assertion is strict and the test is not marked expected-fail.

---

### Edge Cases

- A header row is not a data row.
- A visible row whose cells include `סה"כ` is not added.
- A hidden row that still contains an old integer is not added.
- The hour reader and the district reader stay as they are.
- The table is closed with `חזרה לדוח` before `chart_total` returns.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` for `DATES_CHART` MUST keep opening the table from the right-click menu item `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent.
- **FR-002**: After that table is open, the dates total MUST wait until the visible integers in the `התרעות` column are the same on two consecutive reads, up to `self.timeout`.
- **FR-003**: The dates total MUST add an integer only when its row is visible according to Playwright `is_visible()`.
- **FR-004**: A header row MUST be skipped. A row that contains `סה"כ` MUST be skipped. The dates total MUST NOT scroll the table to load more rows.
- **FR-005**: After the sum is taken, the page MUST click `חזרה לדוח` and wait until the dates chart is visible again.
- **FR-006**: `chart_total` for `HOUR_CHART` and `DISTRICT_CHART` MUST keep their current readers.
- **FR-007**: `test_hour_date_and_district_sums_match` MUST NOT have `pytest.mark.xfail`. Its assertion MUST stay `hour_total == district_total == dates_total`.
- **FR-008**: This feature MUST NOT modify `core/`.
- **FR-009**: The date strings already passed by that test MUST stay as they are.

### Key Entities

- **Visible alert cell**: A `role="gridcell"` in the `התרעות` column whose row passes `is_visible()`.
- **Settled visible column**: Two identical consecutive sums of those visible cells.
- **Hidden row**: A `role="row"` that is still in the DOM and fails `is_visible()`.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: The words `הצג כטבלה`, `התרעות`, `סה"כ`, and `חזרה לדוח` stay on the population page.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes without an expected-fail mark.
- **SC-002**: On the filtered dashboard whose three visuals each total 13, the dates reader returns 13.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- The value 5847 is the sum of hidden or stale DOM rows, and the visible filtered table sums to 13.
- Playwright `is_visible()` is the visibility check for each row.
- The test's current range, `01/09/2026` through `15/10/2026`, is the filter the user already proved.
- Inline comments in edited Python stay English.
