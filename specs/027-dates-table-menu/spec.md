# Feature Specification: Dates Table from the Right-Click Menu

**Feature Branch**: `feature/reportportal-integration` (spec directory `027-dates-table-menu`; git checkout stays put)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Open the dates chart data table from the right-click menu item הצג כטבלה. Sum the התרעות grid cells. Go back with חזרה לדוח. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dates total comes from the menu table (Priority: P1)

A validation author totals the dates chart. The page right-clicks that chart, chooses `הצג כטבלה`, sums the alert column, and returns to the report with `חזרה לדוח`.

**Why this priority**: `Alt+Shift+F11` did not open a data table. The hour total and the district total are both `141493`. The dates total is still missing.

**Independent Test**: The dates total is the sum of the `התרעות` grid cells. A `סה"כ` row is not added. After the call, the dates chart is on the canvas again.

**Acceptance Scenarios**:

1. **Given** the dates chart is showing, **When** the page totals it, **Then** a right-click opens the menu and `הצג כטבלה` opens the data table.
2. **Given** that table, **When** the rows are read, **Then** the integers in the `התרעות` column are added and a `סה"כ` row is not added.
3. **Given** the table is open, **When** the total has been read, **Then** `חזרה לדוח` closes it and the dates chart is visible again.
4. **Given** Sum mode, **When** the hour, dates, and district totals are compared, **Then** they are equal.

---

### Edge Cases

- The English menu item `Show as a table` is used when `הצג כטבלה` is absent.
- `5,293` in a grid cell is the integer `5293`. `0` is included.
- A header row is not a data row.
- A row whose cells include `סה"כ` is not added.
- A grid that has the header and no integer cells is not the data table.
- The hour chart still uses the SVG mark reader. The district chart still uses its current reader.
- The table is closed before `chart_total` returns.
- A missing menu item or a missing table fails the total.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` for `DATES_CHART` MUST right-click that chart's visual container and click `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent.
- **FR-002**: The dates total MUST wait for `role="row"` elements in the table that this menu opens.
- **FR-003**: The dates total MUST sum the `role="gridcell"` values in the column whose `role="columnheader"` is `התרעות`.
- **FR-004**: A header row MUST be skipped. A row that contains `סה"כ` MUST be skipped.
- **FR-005**: After the sum is taken, the page MUST click `חזרה לדוח` and wait until the dates chart is visible again.
- **FR-006**: `chart_total` for `HOUR_CHART` and `DISTRICT_CHART` MUST keep their current readers.
- **FR-007**: This path MUST NOT press `Alt+Shift+F11`. A missing menu item or table MUST raise. It MUST NOT return the zoomed circle sum.
- **FR-008**: This feature MUST NOT modify `core/`.
- **FR-009**: `population_snapshot.py` MUST keep calling `chart_total`. `test_hour_date_and_district_sums_match` MUST stay as it is and MUST pass.

### Key Entities

- **Context menu item**: `הצג כטבלה` or `Show as a table` on the dates chart.
- **Alert grid cell**: An integer in the `התרעות` column. Included in the dates total.
- **Back control**: The button `חזרה לדוח`.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: The words `הצג כטבלה`, `התרעות`, `סה"כ`, and `חזרה לדוח` stay on the population page. `core/` gains no chart title.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes.
- **SC-002**: The dates total is the menu table's `התרעות` column sum. The hour total remains the SVG bar sum.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 022's tight container is the right-click target.
- The hour SVG reader and the district reader stay.
- Git checkout remains `feature/reportportal-integration`.
- The live hour total and the live district total are both `141493`.
- Inline comments in the edited Python stay English.
