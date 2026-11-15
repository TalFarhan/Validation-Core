# Feature Specification: Population SVG Circle and Value Regex

**Feature Branch**: `feature/reportportal-integration` (spec directory `025-population-svg-refine`; git checkout stays put)

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Read circle marks with rect and path. Take the integer after התרעות. Wait until the SVG marks are visible. Do not edit core/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dates total reads circle marks (Priority: P1)

A validation author totals the dates chart. Power BI draws that chart with circle marks. The page sums the integer that follows `התרעות` on each mark label.

**Why this priority**: On 2026-10-15 the dates total was `0` from one circle label, `תאריך 2026-10-15. התרעות 0.` A reader that takes the last integer can treat `2026` as the value when the alert count is not last.

**Independent Test**: The dates total uses circle `aria-label` values. The number added from a label is the integer after `התרעות`, so `2026` in the date is not the value.

**Acceptance Scenarios**:

1. **Given** a dates mark whose label contains a date and `התרעות`, **When** the page totals that chart, **Then** the added number is the integer after `התרעות`.
2. **Given** the dates chart draws circles, **When** the page totals that chart, **Then** those circles are included with `rect` and `path`.
3. **Given** no mark supplies an integer after `התרעות` or a bare integer label, **When** the chart is totaled, **Then** the total fails.

---

### User Story 2 - Hour total waits for every bar (Priority: P1)

A validation author totals the hour chart. The page waits until the SVG marks are visible, then sums each bar. The average line stays out of the sum.

**Why this priority**: The cross-chart total is `141493`, which is `5895.54` times 24. A log line showed the first eight bar labels only. The reader must wait for the marks before it counts them.

**Independent Test**: The hour total is `141493` when those 24 bars are on the page. It is not the single average `5895.54`.

**Acceptance Scenarios**:

1. **Given** the hour chart is still drawing, **When** the page totals it, **Then** it waits until an SVG mark is visible before it reads labels.
2. **Given** a bar label that is only an integer, such as `5293`, **When** the hour chart is totaled, **Then** that integer is added.
3. **Given** a label that contains `ממוצע` or a float such as `5895.54`, **When** the hour chart is totaled, **Then** that label is not added.
4. **Given** Sum mode, **When** the hour, dates, and district totals are compared, **Then** they are equal.

---

### Edge Cases

- `תאריך 2026-10-15. התרעות 0.` contributes `0`, not `2026`.
- `התרעות 5,293` contributes `5293`.
- A label that is only `5293` contributes `5293`.
- A label containing `ממוצע` contributes nothing, including `0`.
- A float such as `5895.54` contributes nothing.
- Circle, rect, and path labels are not added twice for one mark.
- District and settlement totals keep their current readers.
- `core/` is not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chart_total` for `DATES_CHART` and `HOUR_CHART` MUST read `aria-label` from `svg rect`, `svg path`, and `svg circle` inside that chart's visual container.
- **FR-002**: Those reads MUST NOT use `inner_text`.
- **FR-003**: The reader MUST wait until the first of those marks is visible before it collects labels.
- **FR-004**: When a label contains `התרעות`, the added value MUST be the integer immediately after that word. Thousands separators are removed.
- **FR-005**: When a label is only an integer, that integer MUST be added.
- **FR-006**: A label containing `ממוצע`, and a label containing a float, MUST be omitted.
- **FR-007**: When no integer was added, `chart_total` MUST raise. It MUST NOT return `0` for that empty read.
- **FR-008**: District and settlement totals MUST keep their current readers.
- **FR-009**: This feature MUST NOT modify `core/`.
- **FR-010**: `population_snapshot.py` MUST keep calling `chart_total`. The three-chart test MUST stay as it is and MUST pass.

### Key Entities

- **SVG mark**: A `rect`, `path`, or `circle` inside the dates or hour visual. Its `aria-label` is the source of the value.
- **Alert count**: The integer after `התרעות`, or the whole label when the label is only an integer.
- **Average label**: A label containing `ממוצע` or a float such as `5895.54`. Excluded.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` keeps its name and arguments.
- **AC-005**: The words `התרעות` and `ממוצע` stay on the population page. `core/` gains no chart title.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hour_date_and_district_sums_match` passes.
- **SC-002**: The hour total is the sum of the bar labels. It is not the single value `5895.54`.
- **SC-003**: The diff for this slice contains no path under `core/`.

## Assumptions

- Feature 022's tight container stays. Feature 024's page-local SVG reader stays the place this slice edits.
- Git checkout remains `feature/reportportal-integration`.
- The live cross-chart total the bars add up to is `141493`.
- A debug print of the first eight hour labels was a slice of the list. The wait is still required before the labels are collected.
- Inline comments in the edited Python stay English.
