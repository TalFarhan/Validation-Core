---

description: "Task list for Screen 1 status-picture golden-record checks"
---

# Tasks: Status Picture Sanity Tests

**Input**: Design documents from `/specs/035-status-picture-sanity/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/status-picture.md, quickstart.md

**Tests**: The feature is the new page object and the four sanity tests. Do not add another test module. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Three user stories. The page, fixture, clear, date range, and card reader land first. Story 1 checks the cleared cards. Story 2 checks the range cards. Story 3 checks categories and the top settlements, each in its own test so a skip cannot hide a card result.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Page**: `pages/status_picture/status_picture_page.py`
- **Fixture**: `tests/sanity/status_picture_dashboard/conftest.py`
- **Tests**: `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`
- **Golden record, unchanged**: `data/alerts/db_sanity_am_kalavi.yaml`
- **Do not edit**: `tests/conftest.py`, `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, `tests/ui/`, `core/`, `pages/alerts_analysis/population_page.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the Screen 1 golden values, and that page 1 is the alerts report before the population switch

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/035-status-picture-sanity"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `data/alerts/db_sanity_am_kalavi.yaml`, confirm `screen_1_status_picture.date_range` is `2025-06-13` through `2025-06-25`, `total_warning_zones_all_time.expected_value` is `1337`, `total_alerted_population_all_time.expected_value` is `10142584`, `warning_zones_under_fire.expected_value` is `1271`, `alerted_population_selected_range.expected_value` is `10091037`, `alerts_by_category.values` is rockets `16817`, category 2 `519`, and category 10 `0`, and `top_10_settlements.values` has ten names beginning with ראשון לציון `39` and ending with חיפה `31`. In `pages/alerts_analysis/page.py`, confirm `DASHBOARD_SEARCH_TERM` is `ניתוח התרעות`. In `pages/alerts_analysis/population_page.py`, confirm page 2 clicks `_PAGE_NAV_LABEL`. Confirm `tests/conftest.py` does not import a report page

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the status-picture package, the card and date methods, and the fixture

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create an empty `pages/status_picture/__init__.py`
- [X] T004 [P] Create an empty `tests/sanity/status_picture_dashboard/__init__.py`
- [X] T005 Create `StatusPicturePage` in `pages/status_picture/status_picture_page.py` per `specs/035-status-picture-sanity/contracts/status-picture.md`. Inherit `AlertsAnalysisPage`. Override `_report_ready_locator` to look for `אזורי התרעה תחת ירי`. Do not click `ניווט בין עמודים`. Implement `clear_filters()` with `Slicer.clear_all()` and a settle wait on that card. Implement `set_date_range(start, end)` by filling `input[aria-label^='תאריך התחלה']` and `input[aria-label^='תאריך סיום']` with dismiss, `click(force=True)`, fill, and Enter, then the same settle wait. Implement `read_cards()` with `KPI.number` for `מספר אזורי התרעה`, `אזורי התרעה תחת ירי`, `כמות אוכלוסייה מותרעת`, and `אוכלוסייה מותרעת`, omitting a title that is not visible. Do not add the category or top-10 readers in this task. Comments inside methods are English. Do not edit `pages/alerts_analysis/population_page.py` or `core/`
- [X] T006 Add `status_picture_dashboard = bind_dashboard(StatusPicturePage, "status_picture_dashboard")` to `tests/sanity/status_picture_dashboard/conftest.py`, importing `bind_dashboard` from `tests.helpers.dashboard_fixture` and `StatusPicturePage` from `pages.status_picture.status_picture_page`. Do not edit `tests/conftest.py`

**Checkpoint**: The page opens Screen 1, clears filters, sets a date range, and reads the four card keys. Stories can add tests.

---

## Phase 3: User Story 1 - All-time status cards match the golden record (Priority: P1) 🎯 MVP

**Goal**: After a clear, warning zones are `1337` and alerted population is `10142584`.

**Independent Test**: `test_screen_1_global_metrics` calls `clear_filters()` and asserts `read_cards()["total_warning_zones"]` and `read_cards()["total_alerted_population"]` against the golden `expected_value` fields.

### Implementation for User Story 1

- [X] T007 [US1] Add `test_screen_1_global_metrics(status_picture_dashboard)` to `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` per `specs/035-status-picture-sanity/contracts/status-picture.md`. Import `pytest`, `yaml`, `Path`, and `status_picture_dashboard` from `tests.sanity.status_picture_dashboard.conftest`. Decorate the test with `@pytest.mark.sanity`. Load `data/alerts/db_sanity_am_kalavi.yaml` with `yaml.safe_load` from `Path(__file__).resolve().parents[3] / "data" / "alerts" / "db_sanity_am_kalavi.yaml"`. Call `clear_filters()`. Read `read_cards()`. Assert `total_warning_zones` equals `screen_1_status_picture.metrics.total_warning_zones_all_time.expected_value`. Assert `total_alerted_population` equals `total_alerted_population_all_time.expected_value`. If a key is absent, `pytest.skip("Missing Page Object reader for <key>")`. Do not hard-code `1337` or `10142584`. Comments inside functions are English

**Checkpoint**: The cleared cards are testable. The date range and the charts are not required yet.

---

## Phase 4: User Story 2 - Filtered status cards match the golden range (Priority: P1)

**Goal**: After `13/06/2025` through `25/06/2025`, zones under fire are `1271` and alerted population is `10091037`.

**Independent Test**: `test_screen_1_filtered_metrics` converts the golden ISO dates and asserts the two range card keys. It does not read categories or settlements.

### Implementation for User Story 2

- [X] T008 [US2] Add `test_screen_1_filtered_metrics(status_picture_dashboard)` to `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` per `specs/035-status-picture-sanity/contracts/status-picture.md`. Decorate it with `@pytest.mark.sanity`. Convert `screen_1_status_picture.date_range.start` and `.end` from `YYYY-MM-DD` to `DD/MM/YYYY` with `datetime.strptime` and `strftime`, which yields `13/06/2025` and `25/06/2025` for the current file. Call `set_date_range(start, end)`. Assert `warning_zones_under_fire` equals `warning_zones_under_fire.expected_value` and `alerted_population` equals `alerted_population_selected_range.expected_value`. If a key is absent, `pytest.skip("Missing Page Object reader for <key>")`. Do not assert categories or settlements in this function. Do not hard-code `1271` or `10091037`. Comments inside the function are English

**Checkpoint**: The range cards are testable without the chart readers.

---

## Phase 5: User Story 3 - Category totals and the top settlements match (Priority: P2)

**Goal**: Threat totals and the ten settlements match the golden maps, or each missing reader skips on its own.

**Independent Test**: `test_screen_1_alerts_by_category` expects rockets `16817`, category 2 `519`, and category 10 `0`. `test_screen_1_top_settlements` expects the ten golden names. An empty map skips only that test.

### Implementation for User Story 3

- [X] T009 [US3] Add `read_alerts_by_category()` and `read_top_10_settlements()` to `pages/status_picture/status_picture_page.py` per `specs/035-status-picture-sanity/contracts/status-picture.md`. Category keys read `סה"כ בטווח שנבחר` in `ירי רקטות וטילים` (`category_1_rockets`), `חדירת מחבלים` (`category_2_aircraft`), and `חדירת כלי טיס עוין` (`category_10_terrorists`). Return `{}` when none of those scopes can be read. `read_top_10_settlements()` returns `{name: count}` from `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` and returns `{}` when names and counts cannot be paired. Do not read the chart whose title ends in `ביממה הנוכחית והקודמת`. Comments inside the methods are English
- [X] T010 [US3] Add `test_screen_1_alerts_by_category` and `test_screen_1_top_settlements` to `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` per `specs/035-status-picture-sanity/contracts/status-picture.md`. Both use `@pytest.mark.sanity`, the same ISO-to-`DD/MM/YYYY` conversion, and `set_date_range`. Compare `read_alerts_by_category()` to `alerts_by_category.values`. Compare `read_top_10_settlements()` to `top_10_settlements.values`, requiring every golden name and allowing extra UI names. An empty category map calls `pytest.skip("Missing Page Object reader for alerts_by_category")`. An empty settlement map calls `pytest.skip("Missing Page Object reader for top_10_settlements")`. Do not edit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. Comments inside the functions are English

**Checkpoint**: A missing chart reader skips one test and leaves the card tests runnable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Collect the module from `specs/035-status-picture-sanity/quickstart.md` and confirm this slice did not edit Screen 2, the root conftest, or `core/`

- [X] T011 Run `python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py --collect-only` from `specs/035-status-picture-sanity/quickstart.md` and confirm the collected tests are `test_screen_1_global_metrics`, `test_screen_1_filtered_metrics`, `test_screen_1_alerts_by_category`, and `test_screen_1_top_settlements`
- [X] T012 [P] Confirm the only new implementation files are `pages/status_picture/__init__.py`, `pages/status_picture/status_picture_page.py`, `tests/sanity/status_picture_dashboard/__init__.py`, `tests/sanity/status_picture_dashboard/conftest.py`, and `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`. Confirm `tests/conftest.py`, `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, `pages/alerts_analysis/population_page.py`, `tests/ui/`, `core/`, and `data/alerts/db_sanity_am_kalavi.yaml` are unchanged
- [ ] T013 Run `python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py -v` from `specs/035-status-picture-sanity/quickstart.md`. Portal auth is required. A pass means the cleared cards are `1337` and `10142584`, and the range cards are `1271` and `10091037`. Category and top-10 tests may skip with their missing-reader messages

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks every user story
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on User Story 2 or User Story 3
- **User Story 2 (Phase 4)**: Depends on Foundational. Implement after User Story 1 because both tests are added to `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`. The range-card asserts do not depend on the cleared-card result
- **User Story 3 (Phase 5)**: Depends on Foundational. Implement after User Story 2 so the chart methods and chart tests are added after the card path. The chart tests do not depend on the card assertions passing
- **Polish (Phase 6)**: Depends on all three user stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T006. Uses `clear_filters` and `read_cards`
- **User Story 2 (P1)**: Starts after T007. Uses `set_date_range` and `read_cards`
- **User Story 3 (P2)**: T010 starts after T009. Uses `set_date_range`, `read_alerts_by_category`, and `read_top_10_settlements`

### Within Each User Story

- User Story 3 adds the page readers before its tests
- User Story 1 and User Story 2 are test-only
- The live portal run waits until all four tests are in the module

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T003 and T004 create different package markers and can run together after Setup
- T005 then T006 stay in that order because the fixture imports the page
- T007, T008, and T010 edit `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`, so they stay sequential
- T009 edits `pages/status_picture/status_picture_page.py` after T005, so it stays after the foundational page methods
- T012 can run beside T011. T013 waits until collection succeeds

---

## Parallel Example: Package markers

```bash
# After Setup, the two empty package files can be created together:
Task: "Create empty pages/status_picture/__init__.py"
Task: "Create empty tests/sanity/status_picture_dashboard/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T007 so the cleared warning-zone and population cards are asserted
3. **STOP and VALIDATE**: run `test_screen_1_global_metrics` when portal auth is available

### Incremental Delivery

1. Setup confirms the golden Screen 1 values and that page 2 is a later switch
2. Foundational adds the page, the fixture, clear, date range, and `read_cards`
3. User Story 1 checks the all-time cards
4. User Story 2 checks the June 2025 range cards
5. User Story 3 checks categories and the top settlements, skipping a reader that returns no labels
6. Phase 6 collects the module and runs it

### Parallel Team Strategy

One person owns `pages/status_picture/status_picture_page.py` for T005 and T009. One person owns `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` for T007, T008, and T010. T006 waits until the page class exists. T010 waits until the chart readers exist.

---

## Notes

- Do not edit `tests/conftest.py`
- Do not edit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- Do not edit `pages/alerts_analysis/population_page.py`, `tests/ui/`, or `core/`
- Do not click `ניווט בין עמודים` from `StatusPicturePage`
- Do not pass ISO dates to `set_date_range`. Convert `YYYY-MM-DD` to `DD/MM/YYYY`
- Category scopes follow the numeric id: `1` rockets, `2` `חדירת מחבלים`, `10` `חדירת כלי טיס עוין`
- `pytest.skip` applies to one test. A missing chart reader must not hide the card tests
- Comments inside functions stay English
- Do not run `pytest tests/ui/fleet_dashboard/`. This slice does not change Layer 0, Layer 2, or the fleet page
