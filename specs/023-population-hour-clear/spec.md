# Feature Specification: Population Hour Sum and Clear Baseline

**Feature Branch**: `feature/reportportal-integration` (spec directory `023-population-hour-clear`; git checkout stays put)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "The hour chart total must sum the bars, not the average line. The clear test must clear once before it takes the baseline snapshot. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hour total sums the bars (Priority: P1)

A validation author totals the hour chart. The average line is not part of the sum. The integer bars are.

**Why this priority**: The hour total was `5895.54`, the average drawn on that chart, so it could not match the dates total.

**Independent Test**: The hour total is the sum of the integer bars. A non-integer average such as `5895.54` is absent from that sum.

**Acceptance Scenarios**:

1. **Given** the hour chart shows integer bars and an average line, **When** the page totals that chart, **Then** the average is not added.
2. **Given** a series whose name contains `ממוצע`, **When** the hour chart is totaled, **Then** that series is not added.
3. **Given** Sum mode on the district chart, **When** the hour, dates, and district totals are compared, **Then** the three totals are equal.

---

### User Story 2 - Clear restores a cleared baseline (Priority: P1)

A validation author opens the population page. The report arrives with default filters, so the warned card is not the total population. Clear removes those defaults. The test's baseline is the state after that first clear, not the state at arrival.

**Why this priority**: Arrival warned was `10136795`. After clear, warned equaled the total population `10142584`. Comparing arrival with the cleared state failed.

**Independent Test**: The clear test clears first, snapshots that state, applies dates, day/night, and the 0–349 range, clears again, and sees the baseline snapshot return.

**Acceptance Scenarios**:

1. **Given** the page has just opened, **When** the clear test starts, **Then** it clears filters before it stores the baseline.
2. **Given** that baseline, **When** the test applies its filters, **Then** the snapshot differs from the baseline.
3. **Given** those filters, **When** the test clears again, **Then** the snapshot equals the baseline.

---

### Edge Cases

- A whole float such as `1.0` remains a bar. A fractional float such as `5895.54` does not.
- A rendered `0` remains part of the sum.
- Skipping the average does not store it as `0`.
- Dates, district, and settlement totals keep their current readers. Only the hour total drops the average line.
- The day-plus-night test is unchanged.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The hour-chart total MUST omit a series whose name contains `ממוצע`.
- **FR-002**: The hour-chart total MUST omit a cell that is a float and is not a whole number.
- **FR-003**: Integer bar cells on the hour chart MUST still be added. An hour chart with no integer bar MUST still fail.
- **FR-004**: `test_clear_restores_population_snapshot` MUST call `clear_filters` before it stores the baseline snapshot.
- **FR-005**: After that baseline, the test MUST apply the existing date range, day/night toggles, and 0–349 range, assert the snapshot changed, clear again, and assert the baseline returned.
- **FR-006**: This feature MUST NOT modify `core/`.
- **FR-007**: `population_snapshot.py` MUST keep calling `chart_total`. It MUST NOT grow its own parser.

### Key Entities

- **Hour bar**: An integer cell on the hour chart. Included in the total.
- **Average line**: The series named with `ממוצע`, or a fractional value such as `5895.54`. Excluded from the hour total.
- **Cleared baseline**: The snapshot taken after the first `clear_filters` in the clear test.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` and `clear_filters` keep their names and arguments.
- **AC-005**: The word `ממוצע` stays on the population page. `core/` gains no chart title.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_clear_restores_population_snapshot`, `test_day_plus_night_equals_untoggled_sum`, and `test_hour_date_and_district_sums_match` pass.
- **SC-002**: `test_population_suite_opens_second_page`, `test_population_cards_within_total`, and `test_settlement_series_match_legend` still pass.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 022's tight container for the dates and hour charts stays.
- Git checkout remains `feature/reportportal-integration`.
- The live average that was summed was `5895.54`. The hourly bars beside it were integers.
- Arrival filters are a report default. Clear is the unfiltered state. The test baseline is the unfiltered state.
- Inline comments in the edited Python stay English.
