# Feature Specification: Advanced Power BI Visual Components

**Feature Branch**: `015-advanced-visual-components`

**Created**: 2026-10-13

**Status**: Ready for tasks

**Input**: Inline `/speckit-plan` request — expand `core/components` for recurring Power BI patterns: gauge scale (numerator / denominator or min / max), true zero versus an empty visual, a generic bar/column `Chart` (sort, Top-N row count, legend series), and the dynamic displayed title of a visual. Domain strings and business rules stay out of `core/`.

## Problem Statement

Layer 2 can read a titled KPI's current figure (`KPI.number`) and, since feature 013, can ignore Gauge min/max chrome so that figure stays correct. Callers still cannot read the scale itself (minimum, maximum, or a denominator). They also cannot tell a visual that rendered **0** from a visual that rendered **nothing** (a blank chart or map). Bar/column charts — category order, how many categories rendered, and legend series — are still parsed inside domain page objects. Visual titles that grow or change when a slicer changes are not returned as data; callers only use them as locators.

The project rule for this framework is: when the same Power BI behavior shows up on another dashboard, it belongs in `core/components` as a generic reader. Report names, metric titles, and concrete scale constants stay with the caller.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Gauge scale as structured data (Priority: P1)

As a validation engineer, I read a Gauge or ratio visual and get the primary figure **and** its scale limits (minimum and maximum, or a denominator) in one structured result. `KPI.number` still returns only the current figure it returns today.

**Why this priority**: Parity against a ratio or a bounded gauge is wrong if the caller can see only one of the numbers.

**Independent Test**: Pure parsing, no browser. A labeled gauge string yields current, minimum, and maximum. A compact three-number string yields the same triple in the order already defined by feature 013 (minimum, maximum, current). A slash pair yields the left number as the value and the right number as the maximum. A single-figure KPI yields the value with both limits absent. No report title or literal denominator is required for the test.

**Acceptance Scenarios**:

1. **Given** a labeled Gauge string that contains generic min/max chrome and three figures, **When** the scale is parsed, **Then** the result carries the current value, the minimum, and the maximum as separate fields.
2. **Given** a compact three-number Gauge string, **When** the scale is parsed, **Then** the first token is the minimum, the second is the maximum, and the last is the current value.
3. **Given** a slash-separated pair, **When** the scale is parsed, **Then** the left number is the value and the right number is the maximum (the denominator); the minimum is absent.
4. **Given** a standard one-figure KPI label, **When** the scale is parsed, **Then** only the value is present.
5. **Given** existing callers of `KPI.number` / `extract_kpi_value_text`, **When** this feature is added, **Then** those results stay the same.

---

### User Story 2 — True zero versus empty visual (Priority: P1)

As a validation engineer, I can tell a visual that successfully rendered **0** from a visual that is blank (no data marks and no numeric reading), including a chart or map with no points.

**Why this priority**: Treating a blank visual as 0 produces a false pass against a warehouse zero.

**Independent Test**: A numeric token `0`, or a data mark whose value is 0, classifies as a value. A container with no numeric token and no data mark classifies as empty. The empty result is not the number 0.

**Acceptance Scenarios**:

1. **Given** a visual whose reading is the number 0, **When** presence is classified, **Then** the state is a rendered value and the number is 0.
2. **Given** a visual with no numeric token and no data mark, **When** presence is classified, **Then** the state is empty and no numeric value is reported.
3. **Given** a chart category whose mark is missing, **When** a series slot is recorded, **Then** that slot is absent, not coerced to 0.
4. **Given** a blank map or chart that still shows its title, **When** presence is classified, **Then** the title does not count as data and the state stays empty.

---

### User Story 3 — Generic bar/column chart (Priority: P1)

As a validation engineer, I use one `Chart` component to read a bar or column visual: category order, whether values are sorted descending, how many category rows rendered (Top-N), and the legend series (including two bars for one category).

**Why this priority**: This is the recurring visual the next dashboards need, and it must not be copied per report.

**Independent Test**: Given parsed categories and series (no live portal), descending order is true only when each value is greater than or equal to the next; the row count is the number of categories, not the number of bars; two series produce two values per category and two legend names. Locating the visual uses an opaque title string supplied by the caller.

**Acceptance Scenarios**:

1. **Given** category values in non-increasing order, **When** descending sort is checked, **Then** the check passes, including ties.
2. **Given** a later category whose value is greater than an earlier one, **When** descending sort is checked, **Then** the check fails.
3. **Given** a Top-N visual, **When** rows are counted, **Then** the count is the number of categories.
4. **Given** two legend series, **When** the chart is read, **Then** each category exposes one value per series and the series names are returned as opaque strings for the caller to interpret.

---

### User Story 4 — Dynamic visual title (Priority: P2)

As a validation engineer, I read the title currently displayed on a visual after slicers have changed it, without embedding that dynamic phrase in `core/`.

**Why this priority**: Titles are locators and assertions. The displayed text often adds a slicer-dependent suffix; only the caller knows which suffix is correct.

**Independent Test**: A visual located by an opaque anchor returns the full displayed title text, which may be longer than the anchor. A known dynamic phrase is asserted only in the caller's test, never stored in `core/`.

**Acceptance Scenarios**:

1. **Given** a visual whose accessible title contains the caller's anchor plus extra text, **When** the displayed title is read, **Then** the full current title is returned.
2. **Given** any dynamic phrase that depends on slicer state, **When** `core/` is inspected, **Then** that phrase does not appear.

---

### Edge Cases

- A minimum of 0 is a real bound. Missing minimum and maximum are empty fields, not 0.
- Compact Gauge detection stays at exactly three numeric tokens so a two-token space-thousands label is not treated as a scale.
- Slash parsing must not treat a report-specific denominator as a constant; any right-hand number is accepted.
- An empty visual that still has axis chrome or a title is empty when it has no data marks and no numeric data label.
- Sort comparison is numeric. Category labels are not sorted inside `core/`.
- Series are identified by legend order and legend text, not by metric meaning.
- `scope` follows feature 014: omitted or blank means the whole iframe; a non-empty scope is an opaque section name.
- Inline comments in production and test code stay English only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A pure scale parser MUST return a structured result with `value`, `minimum`, and `maximum`. A denominator MUST be reported as `maximum`. Absent limits MUST be null, not 0.
- **FR-002**: `KPI` MUST expose that scale for a titled visual. `KPI.number`, `extract_kpi_value_text`, and `normalize_kpi_text` MUST keep their current results.
- **FR-003**: A generic presence classifier MUST distinguish a rendered numeric value, including 0, from an empty visual (no numeric token and no data mark).
- **FR-004**: A missing series mark on a category MUST be recorded as absent, not as 0.
- **FR-005**: A new `Chart` component in `core/components/` MUST read bar/column categories, check numeric descending order (ties allowed), count category rows, and return legend series names plus one value per series.
- **FR-006**: Chart lookup MUST take an opaque title and an optional opaque `scope`. `core/` MUST NOT contain report titles, metric names, or Top-N constants.
- **FR-007**: Callers MUST be able to read the full displayed title of a located visual. Dynamic title text MUST remain a caller assertion.
- **FR-008**: `core/` MUST NOT contain domain terms or business constants (report names, metric titles, or a specific denominator).
- **FR-009**: New behavior MUST be covered by unit tests that do not require the portal. `pytest tests/ui/fleet_dashboard/` MUST remain the regression gate.
- **FR-010**: Inline comments MUST be English only.

### Key Entities

- **GaugeScale**: Current value plus optional minimum and maximum. A denominator is the maximum. A rendered 0 is a value; a blank visual has no value.
- **VisualPresence**: `value` or `empty`. `value` includes numeric 0. `empty` has no number.
- **ChartCategory**: Opaque category label and one optional number per legend series, in legend order.
- **ChartReading**: Displayed title, ordered categories, legend series names, and presence.
- **VisualTitle**: The full title string currently shown on the visual. The lookup anchor is not the title.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) is unchanged. No report-specific labels are added there.
- **AC-002**: Domain pages keep composing `ReportShell`. This feature does not re-implement login, catalog search, iframe wait, or last-refresh.
- **AC-003**: Report-ready locators stay on the domain page.
- **AC-004**: Existing `KPI.number(title)` and `KPI.number(title, scope)` callers keep their contracts. Fleet chart methods (tooltips, drilldown, hover) stay on the fleet page.
- **AC-005**: Layer 2 stays report-agnostic. `core/` MUST NOT load `data/` catalogs or hardcode filter names, chart titles, or KPI titles. Generic Power BI gauge chrome already allowed by feature 013 may still be recognized.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Scale parsing returns separate value and limits for labeled gauges, compact gauges, and slash pairs, with null limits when a bound is not present.
- **SC-002**: A rendered 0 and a blank visual produce different presence results, and the blank result is not the number 0.
- **SC-003**: Chart row count equals the category count; descending order is a numeric check; two series yield two values per category.
- **SC-004**: Displayed-title reads return the visual's current title text, and no slicer-dependent phrase is stored under `core/`.
- **SC-005**: `pytest tests/ui/fleet_dashboard/` MUST pass at 100%. Existing KPI unit extract/normalize cases stay green.

## Assumptions

- Feature 013's Gauge text shapes remain the labeled and compact inputs. Compact order stays minimum, maximum, current.
- A slash pair is an additional scale shape. It does not change `extract_kpi_value_text`.
- "Another dashboard needs this" is the trigger in Constitution VII for a generic chart reader. Fleet drilldown and tooltips are not part of that shared behavior.
- Power BI bar/column data is readable from mark accessible names first, then from numeric text paired with category ticks. Pixel geometry is a fallback, not the contract.
- Empty detection is structural (marks and numeric tokens). A caption that means "no data" is not hardcoded.
- Top-N is whatever count the caller asserts. `core/` only returns the count.
- New public methods may add an optional `scope` argument. Existing one-argument KPI methods stay valid.
