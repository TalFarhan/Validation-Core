# Feature Specification: Scroll the Dates Table and Filter District Rows

**Feature Branch**: `feature/reportportal-integration` (spec directory `030-scroll-visible-totals`; git checkout stays put)

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "Dates returned 11 because only the first viewport was read. Scroll that table and keep is_visible(). District returned 5847 because hidden rows were included. Apply is_visible() and a settle wait there too. Keep the strict equality. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dates reaches the rows below the first screen (Priority: P1)

A validation author totals the dates chart. The page opens the data table, scrolls it, and adds each visible alert integer once, including rows that appear only after the scroll.

**Why this priority**: On 2026-10-18 the visible first screen summed to 11. The filtered dates table totals 13. Power BI virtualizes the rest of the rows.

**Independent Test**: The dates total includes the rows that were below the first viewport, and a hidden row is still not added.

**Acceptance Scenarios**:

1. **Given** the dates table is open, **When** more data rows sit below the viewport, **Then** the page scrolls the table until those rows have been visible.
2. **Given** a row fails `is_visible()`, **When** the scroll passes it, **Then** that row is not added.
3. **Given** the same visible row appears in two overlapping viewports, **When** the total is taken, **Then** its integer is added once.

---

### User Story 2 - District ignores hidden rows (Priority: P2)

A validation author totals the district chart. The page waits until the visible district integers stop changing, and hidden DOM rows are not added.

**Why this priority**: On 2026-10-18 the hour total was 13 and the district total was 5847. The district visual itself shows 13. Its reader has no `is_visible()` check.

**Independent Test**: The district total is the settled sum of visible rows inside that chart. A hidden row is not added.

**Acceptance Scenarios**:

1. **Given** the district chart has hidden rows in the DOM, **When** the total is taken, **Then** only rows that pass `is_visible()` are added.
2. **Given** the visible district integers are still changing, **When** the total is taken, **Then** the page waits until two consecutive reads match.

---

### Edge Cases

- Scrolling stops when the scroll position and the set of visible row keys both stop changing. A second unchanged pass ends the loop. `self.timeout` also ends it.
- A header row and a `סה"כ` row are not added.
- `0` in a visible alerts cell is added.
- The hour reader stays the SVG mark reader.
- The test date strings stay `01/09/2026` and `15/10/2026`.
- The test has no `pytest.mark.xfail`.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` for `DATES_CHART` MUST keep opening the table from `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent.
- **FR-002**: The dates total MUST scroll that table in steps, read `is_visible()` rows after each step, and stop at the end of the table without an infinite loop.
- **FR-003**: A dates row that fails `is_visible()` MUST NOT be added. A visible row MUST be added once, even if a later scroll still shows it.
- **FR-004**: `chart_total` for `DISTRICT_CHART` MUST stop using the unfiltered `_rows_for_total` sum. It MUST add only rows inside the district visual that pass `is_visible()`, after two consecutive visible reads match.
- **FR-005**: A header row and a row that contains `סה"כ` MUST be skipped for both totals. Visible integers include `0`.
- **FR-006**: `chart_total` for `HOUR_CHART` MUST keep `_svg_mark_total`. `SETTLEMENT_CHART` MUST keep `_rows_for_total`.
- **FR-007**: `test_hour_date_and_district_sums_match` MUST keep `hour_total == district_total == dates_total`, the date strings `01/09/2026` and `15/10/2026`, and MUST NOT gain `pytest.mark.xfail`.
- **FR-008**: This feature MUST NOT modify `core/`.
- **FR-009**: The dates table MUST still be closed with `חזרה לדוח` before `chart_total` returns.

### Key Entities

- **Visible dates row**: A `role="row"` in the dates table that passes `is_visible()` during a scroll step.
- **Row key**: The row's `aria-rowindex`, or its row-header text when that index is absent. Used so one row is stored once.
- **Visible district row**: A `role="row"` inside the district visual container that passes `is_visible()`.
- **Settled district sum**: Two identical consecutive sums of those visible district rows.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: `הצג כטבלה`, `התרעות`, `סה"כ`, and `חזרה לדוח` stay on the population page.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes.
- **SC-002**: On the filtered dashboard whose three visuals each show 13, the three totals are 13.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- The two alerts missing from the dates total of 11 are in virtualized rows below the first viewport.
- The district value 5847 comes from hidden DOM content in the district visual, and the visible rows sum to 13.
- Inline comments in edited Python stay English.
