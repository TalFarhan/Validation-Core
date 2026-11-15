# Feature Specification: Population Invariant Fix

**Feature Branch**: `feature/reportportal-integration` (spec directory `021-population-invariant-fix`; git checkout stays put)

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Fix Population Page UI Invariants. Chart totals must ignore non-numeric readings before summing. The district Sum control must be clicked without a strict-mode violation. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chart totals ignore stray text (Priority: P1)

A validation author totals the dates chart and the hour chart. The generic reader sometimes includes a settlement name with no number. The total uses only numeric cells.

**Why this priority**: The clear, day-plus-night, and cross-chart tests stop on that stray name before they can check the identity.

**Independent Test**: A reading that mixes numbers with a non-numeric cell returns the sum of the numbers. A chart with no numeric cell still fails.

**Acceptance Scenarios**:

1. **Given** a chart reading whose selected series has numbers and one empty cell, **When** the population page totals that chart, **Then** the result is the sum of the numbers.
2. **Given** a chart reading with no numeric cell in the selected series, **When** the page totals it, **Then** the total fails instead of returning 0.
3. **Given** the three population cards, **When** they are read, **Then** their current numeric reads stay as they are.

---

### User Story 2 - One Sum click on the district chart (Priority: P1)

A validation author sets the district chart to Sum. The page has more than one button with that label. The click hits one button and does not raise a strict-mode error.

**Why this priority**: The hour, dates, and district comparison cannot start until that control is selected.

**Independent Test**: Calling the district aggregation method with Sum completes one click. Playwright does not report two matching buttons.

**Acceptance Scenarios**:

1. **Given** two buttons labeled Sum, **When** the district chart is set to Sum, **Then** exactly one button is clicked.
2. **Given** that call, **When** it runs, **Then** it does not use a locator click that matches more than one element.

---

### Edge Cases

- A rendered 0 remains part of the sum.
- Skipping an empty cell does not add 0 for that cell.
- The settlement series totals still pass a series index. Only numeric cells in that series are added.
- The Sum label stays on the population page. It is not added under `core/`.
- Card reads and the page-open check are unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` on the population page MUST add only numeric cells in the selected series.
- **FR-002**: A cell that is not a number MUST be left out of the sum. It MUST NOT be added as 0, and it MUST NOT abort the total by itself.
- **FR-003**: When the selected series has no numeric cell, or the chart is empty, `chart_total` MUST fail.
- **FR-004**: The district Sum and average controls MUST be clicked through a locator that resolves to one element. Exact name plus `.first` is sufficient when a nearer chart scope matches nothing.
- **FR-005**: This feature MUST NOT modify `core/`, including `core/components/chart.py` and `core/components/visual.py`.
- **FR-006**: The population snapshot MUST keep calling the page's `chart_total`. It MUST NOT grow its own parser.

### Key Entities

- **Chart total**: Sum of numeric cells in one series of one chart on the population page.
- **Empty cell**: A series slot with no number. Omitted from the sum.
- **Sum control**: The button labeled Sum. More than one exists on the page. The district action clicks one of them.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`. Portal steps stay on the shell.
- **AC-003**: Report-ready state stays the district-chart anchor on the population page.
- **AC-004**: `read_card`, `chart_total`, and `set_district_aggregation` keep their names and arguments.
- **AC-005**: `core/` stays untouched. Hebrew labels stay on the population page.
- **AC-006**: No report page move and no SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_clear_restores_population_snapshot`, `test_day_plus_night_equals_untoggled_sum`, and `test_hour_date_and_district_sums_match` pass.
- **SC-002**: `test_population_cards_within_total`, `test_settlement_series_match_legend`, and `test_population_suite_opens_second_page` still pass.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 020's visible-canvas host stays in place. This slice does not redo it and does not revert it.
- Feature 019's task list stays on disk. This directory is the active plan for the two remaining UI failures.
- Git checkout remains `feature/reportportal-integration`.
- "Non-numeric" means a cell that is not an `int` or `float`, including `None`. Category labels are not added.
- The first exact-name Sum button is an acceptable click when the district chart's own container has no such button.
- Inline comments in the edited Python stay English.
