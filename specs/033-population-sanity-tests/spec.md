# Feature Specification: Population Screen Data Validation Tests

**Feature Branch**: `feature/reportportal-integration` (spec directory `033-population-sanity-tests`; git checkout stays put)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Implement data validation (sanity) tests for the population screen. The golden record is `data/alerts/db_sanity_am_kalavi.yaml`. Add package markers under `tests/sanity/`, add `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, and assert the population cards against that file. Do not modify `tests/ui/` or `core/`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - All-time population cards match the golden record (Priority: P1)

A validation author opens the population screen with no slicers applied and checks the total population and the unprotected population against the golden record for screen 2.

**Why this priority**: Those two cards are the unfiltered baseline. Every later filtered check depends on the same page and the same file.

**Independent Test**: `test_global_metrics_match_db` clears filters, reads the population cards, and compares `total` and `unprotected` to the golden `expected_value` fields. It does not set a date range.

**Acceptance Scenarios**:

1. **Given** the population screen is open, **When** the test clears every slicer, **Then** the total card equals `total_population_all_time.expected_value` (`10142584`).
2. **Given** filters are cleared, **When** the unprotected card is read, **Then** it equals `unprotected_population.expected_value` (`3389879`).

---

### User Story 2 - Warned population in the golden date range matches (Priority: P1)

A validation author applies the golden start and end dates and checks the warned population against the golden record for that range.

**Why this priority**: The golden file stores a selected-range population that is only meaningful after the date fields are set.

**Independent Test**: `test_filtered_population_matches_db` reads `date_range.start` and `date_range.end`, sets that range, and compares the warned card to `alerted_population_selected_range.expected_value` (`9474`).

**Acceptance Scenarios**:

1. **Given** the golden date range, **When** the test sets that range on the population screen, **Then** the warned card equals `9474`.
2. **Given** the golden dates are stored as `YYYY-MM-DD`, **When** they are sent to the page, **Then** the page receives them as `DD/MM/YYYY`.

---

### Edge Cases

- The page method that clears every slicer is `clear_filters()`. There is no `clear_all_filters()`.
- The golden `date_range.end` (`2025-10-18`) is earlier than `date_range.start` (`2026-09-01`). The test passes the pair in file order after format conversion. This slice does not edit the golden file.
- Screen 1, settlement rows, geographic hierarchy, alerts-by-date, and alerts-by-hour in the same file are not asserted.
- `tests/ui/` and `core/` stay unchanged. Comments inside the new test functions are English.
- The tests need portal auth to pass. Collection does not need a browser.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `tests/sanity/__init__.py` and `tests/sanity/alerts_analysis_dashboard/__init__.py` MUST exist so both directories are Python packages. Missing files are created empty.
- **FR-002**: The new module MUST be `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
- **FR-003**: That module MUST import `pytest`, `yaml`, `Path`, and the existing `population_dashboard` fixture.
- **FR-004**: A helper in that module MUST load `data/alerts/db_sanity_am_kalavi.yaml` with `yaml.safe_load`. The test function signatures stay `test_global_metrics_match_db(population_dashboard)` and `test_filtered_population_matches_db(population_dashboard)`.
- **FR-005**: `test_global_metrics_match_db` MUST clear every slicer, read the population cards, and assert `cards['total']` and `cards['unprotected']` against `screen_2_alerts_analysis.metrics.total_population_all_time.expected_value` and `unprotected_population.expected_value`.
- **FR-006**: `test_filtered_population_matches_db` MUST read `screen_2_alerts_analysis.date_range.start` and `.end`, call `set_date_range` with those dates in page format, read the population cards, and assert `cards['warned']` against `alerted_population_selected_range.expected_value`.
- **FR-007**: Comments inside functions in the new test module MUST be English.
- **FR-008**: This feature MUST NOT modify `tests/ui/` or `core/`.
- **FR-009**: Golden dates MUST be converted from `YYYY-MM-DD` to `DD/MM/YYYY` before `set_date_range`. The file order start-then-end is kept.

### Key Entities

- **Golden record**: `data/alerts/db_sanity_am_kalavi.yaml`. This slice reads `dashboard_sanity_checks.screen_2_alerts_analysis` only.
- **Population cards**: `total`, `warned`, and `unprotected` on the population page.
- **Golden date range**: `date_range.start` and `date_range.end` on screen 2, stored as ISO dates.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` stay unchanged.
- **AC-002**: The population page is not edited. Tests call `clear_filters`, `set_date_range`, and `read_card`.
- **AC-003**: The new tests do not locate Power BI nodes themselves.
- **AC-004**: `tests/ui/alerts_analysis_dashboard/` stays unchanged, including its `conftest.py` and `population_snapshot.py`.
- **AC-005**: The golden file stays under `data/alerts/`. `core/` does not load it.
- **AC-006**: No report SQL is added or changed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The two new tests assert the three golden `expected_value` fields named in FR-005 and FR-006.
- **SC-002**: `pytest` collects `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` without a fixture error.
- **SC-003**: The edit list for this slice is the new sanity package plus this spec directory. `tests/ui/` and `core/` are absent from it.

## Assumptions

- `population_dashboard` in `tests/ui/alerts_analysis_dashboard/conftest.py` is the fixture these tests reuse. Importing it into the new module registers it for that module.
- `clear_filters()` is the clear-all operation the request called `clear_all_filters()`.
- Card roles `total`, `unprotected`, and `warned` are the UI counterparts of the three golden metrics this slice asserts.
- The page date format is day/month/year, matching the existing `set_date_range("01/09/2026", "15/10/2026")` calls.
- `PyYAML` is already installed. No dependency is added.
- Running the tests requires the same portal auth as the other population tests. This plan does not change auth.
- The rest of the golden file is reserved for a later slice.
