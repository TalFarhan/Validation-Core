# Feature Specification: Population Date Range for the Three-Chart Total

**Feature Branch**: `feature/reportportal-integration` (spec directory `028-population-date-range`; git checkout stays put)

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Set an explicit wide date range before comparing the hour, dates, and district totals. The 1,000 alert gap may be the default date slider. Keep the equality assertion strict. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The three charts share one explicit date range (Priority: P1)

A validation author compares the hour, dates, and district totals only after the population page has applied a wide start and end date. The comparison stays a strict equality.

**Why this priority**: On 2026-10-15 the dates column summed to `140493` and the hour chart summed to `141493`. The default date slider can hide part of one chart. An explicit range makes that comparison deterministic.

**Independent Test**: After `clear_filters`, the test sets `01/01/2020` through the current day, waits until the total card stops changing, sets district Sum, and requires the three totals to be equal.

**Acceptance Scenarios**:

1. **Given** the population page, **When** `set_date_range` is called with a start and an end, **Then** those values are committed in `תאריך התחלה` and `תאריך סיום`.
2. **Given** the dates were committed, **When** the method returns, **Then** the total population card has been read twice with the same value.
3. **Given** filters were cleared and the wide range was applied, **When** the hour, dates, and district totals are read in Sum mode, **Then** `hour_total == district_total == dates_total`.
4. **Given** the dates total is still different after that range, **When** the assertion runs, **Then** the test fails. The assertion is not marked expected-fail.

---

### Edge Cases

- `clear_filters` runs before `set_date_range`. A range set earlier would be cleared.
- The page date text is day/month/year. `01/01/2020` is 1 January 2020. The end value is the current day in that same form, `17/10/2026` on 17 October 2026.
- The hour reader, the dates menu-table reader, and the district reader stay as they are.
- `set_between_dates` remains available for tests that already pass a narrower pair.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `AlertsPopulationPage` MUST expose `set_date_range(start_date: str, end_date: str)`.
- **FR-002**: That method MUST fill `תאריך התחלה` with `start_date` and `תאריך סיום` with `end_date`, using the page's existing date inputs.
- **FR-003**: After both fields are committed, the method MUST wait until `read_card("total")` returns the same value on two consecutive reads, or until `self.timeout` elapses.
- **FR-004**: `test_hour_date_and_district_sums_match` MUST call `clear_filters`, then `set_date_range("01/01/2020", <today as DD/MM/YYYY>)`, then `set_district_aggregation("sum")`, then read each of the three charts once.
- **FR-005**: The test MUST assert `hour_total == district_total == dates_total`. It MUST NOT mark the test expected-fail.
- **FR-006**: The hour, dates, and district readers MUST stay as they are. This slice changes the filter that is applied before those reads.
- **FR-007**: This feature MUST NOT modify `core/`.
- **FR-008**: `population_snapshot.py` MUST keep calling `chart_total` and MUST NOT gain a date parser.

### Key Entities

- **Date range**: A start string and an end string in day/month/year form.
- **Start field**: The input whose accessible name begins with `תאריך התחלה`.
- **End field**: The input whose accessible name begins with `תאריך סיום`.
- **Settled total**: Two identical consecutive reads of the total population card.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: `תאריך התחלה` and `תאריך סיום` stay on the population page. `core/` gains no slicer label.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes with the strict three-way equality.
- **SC-002**: The three totals are read only after the wide range has been committed and the total card has settled.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- The 1,000-alert gap is the default date slider, so a range from 1 January 2020 through today includes the alerts the hour and district charts already show.
- The date fields already used by `set_between_dates` are the date range control for this page.
- Inline comments in edited Python stay English.
