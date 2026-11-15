# Feature Specification: Population Chart SVG Aria Labels

**Feature Branch**: `feature/reportportal-integration` (spec directory `024-population-svg-aria`; git checkout stays put)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "The dates chart totals 0 and the hour chart totals 141493 because the page reads text instead of the SVG bar aria-labels. Read those labels on the population page. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dates total reads the bar labels (Priority: P1)

A validation author totals the dates chart. Power BI draws each bar as an SVG node. The number is on that node's `aria-label`. The page sums those integers.

**Why this priority**: On 2026-10-15 `chart_total` for the dates chart returned `0`. The visible text did not carry the bar values.

**Independent Test**: The dates total is the sum of integer `aria-label` values on the SVG marks inside that chart. It is not a sum of text nodes that are all zero.

**Acceptance Scenarios**:

1. **Given** the dates chart draws its bars as SVG nodes, **When** the page totals that chart, **Then** each included value comes from an `aria-label`.
2. **Given** a mark label that contains a float, **When** the dates chart is totaled, **Then** that mark is not added.
3. **Given** no integer mark label, **When** the dates chart is totaled, **Then** the total fails instead of returning `0`.

---

### User Story 2 - Hour total reads the bar labels (Priority: P1)

A validation author totals the hour chart. The average line is drawn with the bars. The page sums the integer bar labels and leaves out the average.

**Why this priority**: On 2026-10-15 the hour total was `141493`, which is `5895.54` times 24. That figure came from the average line, not from the bar labels.

**Independent Test**: The hour total is not `141493` and not `5895.54`. A label containing `ממוצע` is absent from the sum.

**Acceptance Scenarios**:

1. **Given** the hour chart shows integer bars and an average line, **When** the page totals that chart, **Then** the average label is not added.
2. **Given** Sum mode on the district chart, **When** the hour total and the dates total are compared, **Then** they are equal.
3. **Given** that same mode, **When** the dates total and the district total are compared, **Then** they are equal.

---

### Edge Cases

- A label containing `ממוצע` is skipped. It is not stored as `0`.
- A label containing a float, such as `5895.54`, is skipped.
- An integer with thousands separators, such as `5,293`, is one bar.
- A rendered integer `0` remains part of the sum.
- The same bar is not added twice when a shape and a parent image expose one label.
- District and settlement totals keep their current readers.
- `core/` is not modified.
- The day-plus-night test and the clear test keep their steps. They call `chart_total`, so the dates total uses this reader.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` for `DATES_CHART` and `HOUR_CHART` MUST read `aria-label` from SVG data marks inside that chart's visual container.
- **FR-002**: Those reads MUST NOT use `inner_text`.
- **FR-003**: A mark label containing `ממוצע` MUST be omitted.
- **FR-004**: A mark label containing a float MUST be omitted.
- **FR-005**: An integer parsed from a kept label MUST be added. Thousands separators are part of that integer.
- **FR-006**: When no integer mark was added, `chart_total` MUST raise. It MUST NOT return `0` for that empty read.
- **FR-007**: District and settlement totals MUST keep their current readers.
- **FR-008**: This feature MUST NOT modify `core/`.
- **FR-009**: `population_snapshot.py` MUST keep calling `chart_total`. It MUST NOT grow its own parser.
- **FR-010**: `test_hour_date_and_district_sums_match` MUST stay as it is and MUST pass.

### Key Entities

- **SVG mark**: A `rect` or `path` inside the dates or hour visual, or an image role used only when those shapes yield no integer. Its `aria-label` is the source of the value.
- **Bar integer**: The integer parsed from a mark label. Included in the total.
- **Average label**: A mark label containing `ממוצע` or a float such as `5895.54`. Excluded.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: The word `ממוצע` stays on the population page. `core/` gains no chart title.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes.
- **SC-002**: The hour total is not `141493` and not `5895.54`. The dates total is the sum of its SVG bar labels, not a text-node total of `0`.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 022's tight container for the dates and hour charts stays.
- Git checkout remains `feature/reportportal-integration`.
- The live hour figure `141493` is `5895.54` times 24 and came from the average line's text.
- The live dates figure `0` came from text nodes. The bar values are on `aria-label`.
- Inline comments in the edited Python stay English.
