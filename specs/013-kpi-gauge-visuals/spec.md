# Feature Specification: Support Power BI Gauge Visual Parsing in KPI Component

**Feature Branch**: `013-kpi-gauge-visuals`
**Created**: 2026-10-12
**Status**: Ready for tasks
**Input**: Inline `/speckit-plan` request — Gauge labels embed current/min/max in one string; the generic
KPI extractor concatenates them. Isolate the current value and keep standard KPI-card extraction unchanged.

## Problem Statement

`extract_kpi_value_text` in `core/components/kpi.py` returns the longest numeric run and allows ASCII space
inside a number. Power BI Gauge visuals put the current value, minimum, and maximum in the same label
(labeled: `"… 3. ערך מינימלי 0. ערך מקסימלי 1,337."`; compact: `"0 1,337 3"`). The extractor concatenates
those figures (`"1337133733"`), so UI↔DB parity compares garbage to the warehouse.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Labeled Gauge current value (Priority: P1)

As a validation engineer, I want labeled Gauge accessibility strings (Hebrew or English min/max chrome) to
yield only the current value so `KPI.number(title)` matches the warehouse scalar.

**Why this priority**: This is the observed Alerts Gauge `aria-label` and the primary failure.

**Independent Test**: `extract_kpi_value_text("distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337.")`
returns `"3"` (not `"1,337"` / `"1337133733"`). English chrome (`Minimum value` / `Maximum value`) also
yields the current value. `normalize_kpi_text(...)` → `"3"`.

**Acceptance Scenarios**:

1. **Given** a Hebrew labeled Gauge string with title, current, min, and max, **When** extracted, **Then**
   only the current figure is returned.
2. **Given** an English labeled Gauge string, **When** extracted, **Then** only the current figure is
   returned.
3. **Given** the extracted token, **When** normalized, **Then** the result is a parseable integer/float.

---

### User Story 2 — Compact Gauge current value (Priority: P2)

As a validation engineer, I want compact three-number Gauge labels (`min max current`) to yield the last
token so visuals without chrome words still parse.

**Why this priority**: Same visual, second observed rendering; independent of bound-label detection.

**Independent Test**: `extract_kpi_value_text("0 1,337 3")` returns `"3"`. Two-token space-thousands strings
are **not** treated as compact Gauges.

**Acceptance Scenarios**:

1. **Given** `"0 1,337 3"`, **When** extracted, **Then** the result is `"3"`.
2. **Given** `"Population 1 234"` (two compact tokens), **When** extracted, **Then** fallback keeps
   `"1 234"`.

---

### User Story 3 — Standard KPI fallback (Priority: P3)

As a validation engineer, I want existing single-figure and space-thousands labels to keep feature-012
behavior so fleet cards and non-Gauge groups do not regress.

**Why this priority**: Safety net; required by the request and Constitution III.

**Independent Test**: Existing `test_extract_*` / `test_normalize_*` cases in
`tests/unit/test_kpi_normalize.py` stay green. Public `KPI` signatures and
`tests/helpers/db_parity_engine.py` are unchanged.

**Acceptance Scenarios**:

1. **Given** a mixed title+one-figure label, **When** extracted, **Then** the single figure is returned.
2. **Given** a no-digit label (`"N/A"`), **When** extracted, **Then** the cleaned text is returned.
3. **Given** the button-rendered fleet path, **When** smoke runs, **Then** it remains 100% green.

---

### Edge Cases

- Bound chrome must not be treated as a report title (Constitution II).
- Compact detection is **exactly three** tokens; two tokens stay on the space-thousands path.
- `_NUMBER_TOKEN` (space-as-thousands) MUST remain the fallback regex.

## Requirements

### Functional Requirements

- **FR-001**: `extract_kpi_value_text` MUST detect labeled Gauges via generic chrome (`ערך מינימלי`,
  `ערך מקסימלי`, `Minimum value`, `Maximum value`) plus the following number, strip those pairs, and
  extract the remaining current value.
- **FR-002**: `extract_kpi_value_text` MUST treat exactly three compact numeric tokens as a Gauge and
  return the last token.
- **FR-003**: Non-Gauge strings MUST keep the feature-012 longest-token / cleaned-text fallback.
- **FR-004**: Unit tests in `tests/unit/test_kpi_normalize.py` MUST cover labeled Hebrew, labeled English,
  compact, and extract→normalize for Gauge strings.
- **FR-005**: Public `KPI` method signatures and locators MUST NOT change.
- **FR-006**: All inline comments in production and test code MUST be English only.

### Non-Goals

- No new `GaugeKPI` class or `kind == "gauge"` locator branch.
- No change to Layer 0 portal navigation or the parity engine.
- No tightening of `_NUMBER_TOKEN` globally.

## Success Criteria

- Gauge strings yield the current value only; concatenated min/max/current MUST NOT occur.
- Existing unit extract/normalize cases remain green.
- `pytest tests/ui/fleet_dashboard/` stays 100% green (regression gate).
