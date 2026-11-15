# Feature Specification: Population Chart Scope

**Feature Branch**: `feature/reportportal-integration` (spec directory `022-population-chart-scope`; git checkout stays put)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Fix population page data spillage and setup timeout. Dates and hour totals must read only that chart's visual. The clear test must wait until the page is ready. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dates and hour totals stay inside one visual (Priority: P1)

A validation author totals the dates chart and the hour chart. The total uses numbers from that chart only. City names, district names, and hour ticks from a neighboring visual are not part of the sum.

**Why this priority**: Day hours plus night hours are compared with the untoggled dates total. A wide read pulls in city values that appear only on one toggle, so the identity fails.

**Independent Test**: With both hour toggles off, then day only, then night only, the day total plus the night total equals the untoggled dates total.

**Acceptance Scenarios**:

1. **Given** the dates chart, **When** its total is taken, **Then** the categories are dates, and city or district labels from other visuals are absent.
2. **Given** the hour chart, **When** its total is taken, **Then** the categories are hours, and city or district labels from other visuals are absent.
3. **Given** day mode and night mode on the dates chart, **When** those two totals are added, **Then** they equal the dates total with both toggles off.
4. **Given** Sum mode on the district chart, **When** the hour, dates, and district totals are compared, **Then** the three totals are equal.

---

### User Story 2 - The population page is ready before a test acts (Priority: P1)

A validation author opens the population page and clears filters. The test waits until the district chart is visible, then acts. A slow report does not fail the setup at 30 seconds.

**Why this priority**: The clear-and-restore test stopped in setup while the report was still loading.

**Independent Test**: `test_clear_restores_population_snapshot` gets past setup, changes the filters, clears them, and sees the arrival snapshot again.

**Acceptance Scenarios**:

1. **Given** the report iframe is still painting, **When** the population page opens, **Then** setup waits for the district chart before the test body runs.
2. **Given** the page switcher is not on screen yet, **When** setup runs, **Then** it does not spend the ready budget clicking a missing control.
3. **Given** filters are about to be cleared, **When** `clear_filters` runs, **Then** the total population card is visible first.

---

### Edge Cases

- A visual title that sits in a header with no numbers is not the read root. The read root is the nearest container that has the title and at least one number.
- A container that also contains another chart title on this page is too wide and is not the read root.
- An empty dates or hour chart still fails the total. A skipped neighboring cell is not stored as 0.
- District and settlement totals keep their current readers. This slice narrows only the dates chart and the hour chart.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Totals for the dates chart and the hour chart MUST be computed from a locator that contains that chart's title and does not contain another population-page chart title.
- **FR-002**: That locator MUST be chosen in `pages/alerts_analysis/population_page.py`. `core/components/chart.py` and every other file under `core/` MUST stay unchanged.
- **FR-003**: City, district, and hour labels that belong to a different visual MUST NOT be added into the dates total or the hour total.
- **FR-004**: A dates or hour total with no numeric cell MUST still fail. A non-numeric cell MUST NOT be added as 0.
- **FR-005**: Opening the population page MUST wait until the district chart is visible. The wait budget for that page MUST be long enough for a slow catalog open (60 seconds).
- **FR-006**: `clear_filters` MUST wait until the total population card is visible before it clicks clear.
- **FR-007**: `population_snapshot.py` MUST keep calling `chart_total`. It MUST NOT grow its own parser.

### Key Entities

- **Chart container**: The visual box for one chart title. It holds that title and that chart's numbers.
- **Spilled category**: A label from another visual (a city, a district, an hour tick, a scale caption) that a wide read attached to the dates or hour chart.
- **Ready visual**: The district chart. Setup treats the page as open when this visual is visible.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged. The longer wait is a value on the population page, not a new portal timeout.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total`, `clear_filters`, and `set_district_aggregation` keep their names and arguments.
- **AC-005**: Hebrew titles stay on the population page. `core/` gains no chart title.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_day_plus_night_equals_untoggled_sum`, `test_hour_date_and_district_sums_match`, and `test_clear_restores_population_snapshot` pass.
- **SC-002**: `test_population_suite_opens_second_page`, `test_population_cards_within_total`, and `test_settlement_series_match_legend` still pass.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 021's numeric-cell skip and single Sum click stay. This slice does not remove them.
- Git checkout remains `feature/reportportal-integration`.
- The dates chart title is `התרעות לפי תאריך`. The hour chart title is `גרף התרעות וגם ממוצע לפי שעה`.
- The nearest Power BI visual container around that title is the read root when it contains a number and no other chart title from this page.
- Inline comments in the edited Python stay English.
