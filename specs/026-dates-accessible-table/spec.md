# Feature Specification: Dates Chart Accessible Table

**Feature Branch**: `feature/reportportal-integration` (spec directory `026-dates-accessible-table`; git checkout stays put)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "The dates chart shows only the zoomed days, which are 0. Open its accessible table with Alt+Shift+F11, sum the התרעות column, then go back. Leave the hour and district readers alone. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dates total comes from the accessible table (Priority: P1)

A validation author totals the dates chart. The visible circles are the current zoom, and those days are 0. The page focuses that chart, opens Power BI's accessible data table, sums the alert column, and returns to the canvas.

**Why this priority**: The hour total and the district total are both `141493`. The dates total is `0` because the visible circles are only the days in the current zoom.

**Independent Test**: The dates total is the sum of the `התרעות` cells in the accessible table. A header and a `סה"כ` row are not added. After the total returns, the dates chart is on the canvas again.

**Acceptance Scenarios**:

1. **Given** the dates chart is showing, **When** the page totals it, **Then** the chart is focused and `Alt+Shift+F11` opens its data table.
2. **Given** that table, **When** the rows are read, **Then** the integers in the `התרעות` column are added and a header or `סה"כ` row is not added.
3. **Given** the table is open, **When** the total has been read, **Then** the back control closes it and the dates chart is visible again.
4. **Given** Sum mode, **When** the hour, dates, and district totals are compared, **Then** they are equal.

---

### Edge Cases

- `5,293` in the alert column is the integer `5293`. `0` is included.
- A header row is not a data row.
- A row whose cells include `סה"כ` is not added.
- The hour chart still uses the SVG mark reader. The district chart still uses its current reader.
- The table is closed before `chart_total` returns, so the next chart read sees the canvas.
- A missing table or a missing `התרעות` column fails the total.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` for `DATES_CHART` MUST focus that chart's visual container and press `Alt+Shift+F11`.
- **FR-002**: The dates total MUST be the sum of the integer cells in the `התרעות` column of the accessible table that the shortcut opens.
- **FR-003**: The reader MUST wait until a `role="grid"` or `role="table"` with that column is visible before it reads rows.
- **FR-004**: A header row MUST be skipped. A row that contains `סה"כ` MUST be skipped.
- **FR-005**: After the sum is taken, the page MUST activate the back control and wait until the dates chart is visible again.
- **FR-006**: `chart_total` for `HOUR_CHART` and `DISTRICT_CHART` MUST keep their current readers.
- **FR-007**: When the table or the `התרעות` column is missing, the dates total MUST raise. It MUST NOT return the zoomed circle sum.
- **FR-008**: This feature MUST NOT modify `core/`.
- **FR-009**: `population_snapshot.py` MUST keep calling `chart_total`. `test_hour_date_and_district_sums_match` MUST stay as it is and MUST pass.

### Key Entities

- **Accessible table**: The grid or table Power BI opens for the focused dates chart.
- **Alert cell**: An integer in the `התרעות` column. Included in the dates total.
- **Summary row**: A row that contains `סה"כ`. Excluded.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: The words `התרעות` and `סה"כ` stay on the population page. `core/` gains no chart title.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes.
- **SC-002**: The dates total is the accessible-table sum. The hour total remains the SVG bar sum.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 022's tight container stays the dates chart focus target.
- The hour SVG reader and the district reader from the current page stay.
- Git checkout remains `feature/reportportal-integration`.
- The live hour total and the live district total are both `141493`.
- The back control's accessible name is `חזרה` or `Back`.
- Inline comments in the edited Python stay English.
