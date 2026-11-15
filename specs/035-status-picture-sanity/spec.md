# Feature Specification: Status Picture Sanity Tests

**Feature Branch**: `feature/reportportal-integration` (spec directory `035-status-picture-sanity`; git checkout stays put)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Add sanity tests for Screen 1 (Status Picture) against `data/alerts/db_sanity_am_kalavi.yaml`. Add a page object at `pages/status_picture/status_picture_page.py` and a test module under `tests/sanity/status_picture_dashboard/`. Do not modify the Screen 2 sanity tests."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - All-time status cards match the golden record (Priority: P1)

A validation author opens the status-picture page, clears filters, and checks the all-time warning-zone count and the all-time alerted population.

**Why this priority**: Those two numbers are the unfiltered baseline. The filtered checks use the same page and the same file.

**Independent Test**: `test_screen_1_global_metrics` calls `clear_filters()` and compares the two all-time golden values to `read_cards()`.

**Acceptance Scenarios**:

1. **Given** the status-picture page is open, **When** filters are cleared, **Then** the warning-zone card equals `1337`.
2. **Given** filters are cleared, **When** the alerted-population card is read, **Then** it equals `10142584`.

---

### User Story 2 - Filtered status cards match the golden range (Priority: P1)

A validation author sets the golden June 2025 range and checks the warning zones under fire and the alerted population for that range.

**Why this priority**: The golden file stores those two numbers only for `2025-06-13` through `2025-06-25`.

**Independent Test**: `test_screen_1_filtered_metrics` converts the ISO dates to `DD/MM/YYYY`, calls `set_date_range`, and compares the two range cards.

**Acceptance Scenarios**:

1. **Given** the golden range, **When** the date fields are set, **Then** the page receives `13/06/2025` and `25/06/2025`.
2. **Given** that range is committed, **When** the range cards are read, **Then** warning zones under fire equal `1271` and the alerted population equals `10091037`.

---

### User Story 3 - Category totals and the top settlements match (Priority: P2)

A validation author, on the same date range, checks rockets, aircraft, and terrorists, then the ten settlements.

**Why this priority**: These are the remaining Screen 1 blocks. A missing chart reader must skip only that block.

**Independent Test**: `test_screen_1_alerts_by_category` and `test_screen_1_top_settlements` each set the golden range. A reader that cannot return labels calls `pytest.skip("Missing Page Object reader for <name>")`.

**Acceptance Scenarios**:

1. **Given** a category reader, **When** the category test runs, **Then** rockets equal `16817`, the category-2 value equals `519`, and the category-10 value equals `0`.
2. **Given** a settlement ranking reader, **When** the top-10 test runs, **Then** each golden settlement count matches, including ראשון לציון `39` and חיפה `31`.
3. **Given** either reader cannot see labels, **When** that test runs, **Then** it skips and the card tests still run.

---

### Edge Cases

- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` is not edited.
- The root `tests/conftest.py` does not import this page.
- The status-picture page does not click the control that opens page 2.
- Category key `category_2_aircraft` is golden key 2. Category key `category_10_terrorists` is golden key 10. The numeric id selects the threat section.
- A skip uses the message `Missing Page Object reader for <name>` and applies to one test.
- Comments inside functions are English.
- `core/` is not edited.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add `pages/status_picture/__init__.py` and `pages/status_picture/status_picture_page.py`. The page class inherits `AlertsAnalysisPage` so portal login stays on `ReportShell`.
- **FR-002**: The page MUST open catalog product `ניתוח התרעות` and MUST NOT switch to the population page.
- **FR-003**: The page MUST implement `clear_filters()`, `set_date_range(start, end)`, `read_cards()`, `read_alerts_by_category()`, and `read_top_10_settlements()`.
- **FR-004**: `set_date_range` MUST type `DD/MM/YYYY` into the start and end date fields. Golden ISO dates are converted in the test.
- **FR-005**: Register `status_picture_dashboard` with `bind_dashboard` in `tests/sanity/status_picture_dashboard/conftest.py`. The root `tests/conftest.py` MUST stay unchanged.
- **FR-006**: Add `tests/sanity/status_picture_dashboard/__init__.py` and `test_status_picture_validation.py`. The test module imports the fixture.
- **FR-007**: `test_screen_1_global_metrics` MUST clear filters and assert `total_warning_zones_all_time` (`1337`) and `total_alerted_population_all_time` (`10142584`).
- **FR-008**: `test_screen_1_filtered_metrics` MUST set the golden range and assert `warning_zones_under_fire` (`1271`) and `alerted_population_selected_range` (`10091037`).
- **FR-009**: Category and top-10 checks MUST be their own tests so a skip cannot hide the card asserts. They read `alerts_by_category.values` and `top_10_settlements.values`.
- **FR-010**: A reader that returns no labels MUST `pytest.skip("Missing Page Object reader for <name>")`.
- **FR-011**: Comments inside functions MUST be English.
- **FR-012**: This feature MUST NOT modify `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, `tests/ui/`, or `core/`.

### Key Entities

- **Golden screen**: `dashboard_sanity_checks.screen_1_status_picture`.
- **All-time cards**: `total_warning_zones_all_time`, `total_alerted_population_all_time`.
- **Range cards**: `warning_zones_under_fire`, `alerted_population_selected_range`.
- **Category map**: `alerts_by_category.values` with keys `category_1_rockets`, `category_2_aircraft`, `category_10_terrorists`.
- **Settlement ranking**: `top_10_settlements.values`, ten names to counts.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` stay unchanged. The page composes `Slicer` and `KPI`.
- **AC-002**: The page lives in `pages/status_picture/`. It inherits `AlertsAnalysisPage`, which inherits `ReportShell`.
- **AC-003**: Tests call page methods. They do not add Power BI locators.
- **AC-004**: The root `conftest.py` does not import `StatusPicturePage`.
- **AC-005**: The golden file stays under `data/alerts/`. `core/` does not load it.
- **AC-006**: No report SQL is added. The population page object is not edited.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The two Screen 2 card tests still pass without edits to that file.
- **SC-002**: The status-picture global test asserts `1337` and `10142584` after a clear.
- **SC-003**: The filtered card test asserts `1271` and `10091037` after `13/06/2025` through `25/06/2025`.
- **SC-004**: Category and top-10 tests either match the golden maps or skip with the missing-reader message.
- **SC-005**: The edit list does not include `tests/conftest.py`, `core/`, or the Screen 2 sanity module.

## Assumptions

- Screen 1 is the report page that opens for `ניתוח התרעות` before the population page switch.
- The ready phrase is `אזורי התרעה תחת ירי`, the page-1 card title already in the alerts contract.
- Date fields use the same accessible prefixes as page 2: `תאריך התחלה` and `תאריך סיום`.
- All-time warning zones are located by `מספר אזורי התרעה`. Range warning zones use `אזורי התרעה תחת ירי`.
- All-time alerted population is located by `כמות אוכלוסייה מותרעת`. The range card uses `אוכלוסייה מותרעת`.
- Category totals are the `סה"כ בטווח שנבחר` card in the threat section for that category id.
- The ranking visual title is `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`.
- Portal auth is required to pass. Collection is not.
