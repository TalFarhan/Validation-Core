---

description: "Task list for population screen golden-record sanity tests"
---

# Tasks: Population Screen Data Validation Tests

**Input**: Design documents from `/specs/033-population-sanity-tests/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sanity-tests.md, quickstart.md

**Tests**: The feature is the two sanity tests. Do not add a second test module. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Two P1 stories share one new module. User Story 1 asserts the cleared cards. User Story 2 asserts the warned card after the golden date range. Helpers land in the foundational phase so each story only adds its test function.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **New package**: `tests/sanity/__init__.py`, `tests/sanity/alerts_analysis_dashboard/__init__.py`
- **New tests**: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- **Golden record, unchanged**: `data/alerts/db_sanity_am_kalavi.yaml`
- **Fixture, unchanged**: `tests/ui/alerts_analysis_dashboard/conftest.py`
- **Page, unchanged**: `pages/alerts_analysis/population_page.py`
- **Do not edit**: `tests/ui/`, `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the golden keys, and the page methods this slice calls

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/033-population-sanity-tests"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `data/alerts/db_sanity_am_kalavi.yaml`, confirm `dashboard_sanity_checks.screen_2_alerts_analysis.date_range.start` is `2026-09-01`, `date_range.end` is `2025-10-18`, `metrics.total_population_all_time.expected_value` is `10142584`, `metrics.unprotected_population.expected_value` is `3389879`, and `metrics.alerted_population_selected_range.expected_value` is `9474`. In `pages/alerts_analysis/population_page.py`, confirm `clear_filters`, `set_date_range`, and `read_card` exist, `CardRole` is `total` / `warned` / `unprotected`, and there is no `clear_all_filters` method

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the sanity package and the shared helpers both stories call

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create an empty `tests/sanity/__init__.py`
- [X] T004 [P] Create an empty `tests/sanity/alerts_analysis_dashboard/__init__.py`
- [X] T005 Create `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` with the imports and helpers from `specs/033-population-sanity-tests/contracts/sanity-tests.md` and no test functions yet. Import `pytest`, `yaml`, `Path` from `pathlib`, `datetime`, and `population_dashboard` from `tests.ui.alerts_analysis_dashboard.conftest`. `load_sanity_data()` opens `Path(__file__).resolve().parents[3] / "data" / "alerts" / "db_sanity_am_kalavi.yaml"` as UTF-8 and returns `yaml.safe_load`. `to_page_date(iso_date)` parses `YYYY-MM-DD` with `datetime.strptime` and returns `DD/MM/YYYY` via `strftime`. `read_population_cards(page)` returns `{role: page.read_card(role)}` for `total`, `warned`, and `unprotected`. Comments inside these functions are English. Do not edit `tests/ui/`, `core/`, `pages/alerts_analysis/population_page.py`, or `data/alerts/db_sanity_am_kalavi.yaml`

**Checkpoint**: The sanity package imports. Both stories can add a test function to the same module.

---

## Phase 3: User Story 1 - All-time population cards match the golden record (Priority: P1) 🎯 MVP

**Goal**: With every slicer cleared, the total and unprotected cards match the golden record.

**Independent Test**: `test_global_metrics_match_db` calls `clear_filters()`, reads the three cards, and asserts `cards['total']` and `cards['unprotected']` against the golden `expected_value` fields. It does not call `set_date_range`.

### Implementation for User Story 1

- [X] T006 [US1] Add `test_global_metrics_match_db(population_dashboard)` to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/033-population-sanity-tests/contracts/sanity-tests.md`. Decorate it with `@pytest.mark.sanity` only. Load the golden dict with `load_sanity_data()`. Read `data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]["metrics"]`. Call `population_dashboard.clear_filters()` (not `clear_all_filters`). Set `cards = read_population_cards(population_dashboard)`. Assert `cards["total"]` equals `metrics["total_population_all_time"]["expected_value"]`. Assert `cards["unprotected"]` equals `metrics["unprotected_population"]["expected_value"]`. Do not call `set_date_range`. Do not hard-code `10142584` or `3389879`. Comments inside the function are English

**Checkpoint**: User Story 1 is testable on its own. The warned-card test is not required yet.

---

## Phase 4: User Story 2 - Warned population in the golden date range matches (Priority: P1)

**Goal**: After the golden start and end dates are applied in page format, the warned card matches the golden selected-range value.

**Independent Test**: `test_filtered_population_matches_db` translates `date_range.start` and `date_range.end` to `DD/MM/YYYY`, calls `set_date_range(start, end)`, and asserts `cards['warned']` against `alerted_population_selected_range.expected_value`.

### Implementation for User Story 2

- [X] T007 [US2] Add `test_filtered_population_matches_db(population_dashboard)` to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/033-population-sanity-tests/contracts/sanity-tests.md`. Decorate it with `@pytest.mark.sanity` only. Load the golden dict with `load_sanity_data()`. Read `data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]`. Set `start = to_page_date(screen["date_range"]["start"])` and `end = to_page_date(screen["date_range"]["end"])`, which yields `01/09/2026` then `18/10/2025`. Call `population_dashboard.set_date_range(start, end)`. Set `cards = read_population_cards(population_dashboard)`. Assert `cards["warned"]` equals `screen["metrics"]["alerted_population_selected_range"]["expected_value"]`. Do not call `clear_filters`. Do not swap the dates. Do not edit `data/alerts/db_sanity_am_kalavi.yaml`. Do not hard-code `9474`. Comments inside the function are English

**Checkpoint**: Both sanity tests are in the module and can be collected separately.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Collect the module from `specs/033-population-sanity-tests/quickstart.md` and confirm this slice did not edit `tests/ui/` or `core/`

- [X] T008 Run `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only` from `specs/033-population-sanity-tests/quickstart.md` and confirm the collected node ids are `test_global_metrics_match_db` and `test_filtered_population_matches_db`
- [X] T009 [P] Confirm the only new files for this slice are `tests/sanity/__init__.py`, `tests/sanity/alerts_analysis_dashboard/__init__.py`, and `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. Confirm `tests/ui/`, `core/`, `pages/alerts_analysis/population_page.py`, `db/clients/alerts.py`, and `data/alerts/db_sanity_am_kalavi.yaml` are unchanged
- [X] T010 Run `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -v` from `specs/033-population-sanity-tests/quickstart.md`. Portal auth is required. A pass means the cleared total card is `10142584`, the cleared unprotected card is `3389879`, and the warned card after `set_date_range("01/09/2026", "18/10/2025")` is `9474`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on User Story 2
- **User Story 2 (Phase 4)**: Depends on Foundational. Implement it after User Story 1 because both functions are appended to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. The warned-card assertion does not depend on the clear-filters assertion
- **Polish (Phase 5)**: Depends on User Story 1 and User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T005. Uses `load_sanity_data`, `clear_filters`, and `read_population_cards`
- **User Story 2 (P1)**: Starts after T005 and after T006 so the two edits to `test_data_validation.py` do not overlap. Uses `load_sanity_data`, `to_page_date`, `set_date_range`, and `read_population_cards`

### Within Each User Story

- Each story adds one test function to the module created in T005
- The live portal run waits until both functions exist

### Parallel Opportunities

- T002, T003, and T004 touch different files and can run together after T001
- T005 waits until T003 and T004 have created the package directories
- T006 and T007 stay sequential because they edit the same file
- T009 can run beside T008. T010 waits until collection succeeds

---

## Parallel Example: Setup and package markers

```bash
# Phase 1 and the package markers can proceed together:
Task: "Confirm golden keys in data/alerts/db_sanity_am_kalavi.yaml and page methods in pages/alerts_analysis/population_page.py"
Task: "Create empty tests/sanity/__init__.py"
Task: "Create empty tests/sanity/alerts_analysis_dashboard/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T006 so `test_global_metrics_match_db` asserts the cleared total and unprotected cards
3. **STOP and VALIDATE**: collect `test_global_metrics_match_db` and run it when portal auth is available

### Incremental Delivery

1. Setup confirms the golden keys and that `clear_filters` is the clear-all method
2. Foundational adds the package and the YAML, date, and card helpers
3. User Story 1 checks the all-time cards
4. User Story 2 checks the warned card for `01/09/2026` through `18/10/2025`
5. Phase 5 collects both tests and runs them

### Parallel Team Strategy

T006 and T007 both edit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. One person owns that file. T003 and T004 can be done by anyone before T005.

---

## Notes

- Do not edit `tests/ui/` or `core/`
- Do not edit `pages/alerts_analysis/population_page.py` or `data/alerts/db_sanity_am_kalavi.yaml`
- Do not add `clear_all_filters`. Call `clear_filters()`
- Do not pass ISO dates to `set_date_range`. Convert `YYYY-MM-DD` to `DD/MM/YYYY` and keep file order
- Do not mark the tests `data` or `db_parity`. Use `@pytest.mark.sanity` only
- Do not assert settlement rows, hierarchy, alerts-by-date, alerts-by-hour, or screen 1
- Comments inside functions in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` stay English
- Do not run `pytest tests/ui/fleet_dashboard/`. This slice does not change Layer 0, Layer 2, or the fleet page
