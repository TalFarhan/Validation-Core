---

description: "Task list for fleet golden-record sanity and validation tests"
---

# Tasks: Fleet DB Sanity and Validation Tests

**Input**: Design documents from `/specs/039-fleet-db-sanity/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/fleet-sanity.md, quickstart.md

**Tests**: This feature is the sanity package. The structural tests and the UI tests in `tests/sanity/fleet_dashboard/test_db_sanity.py` are the implementation. Do not add a second test module. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or `pages/fleet_dashboard/main_dashboard_page.py`.

**Organization**: Stories US1–US4 are file checks and share `tests/sanity/fleet_dashboard/contract.py`. User Story 5 compares the open fleet report to the same file. The loader lands in the foundational phase so each story only adds its check and its test.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Path Conventions

- **New package**: `tests/sanity/fleet_dashboard/__init__.py`
- **Pure checker**: `tests/sanity/fleet_dashboard/contract.py`
- **Tests**: `tests/sanity/fleet_dashboard/test_db_sanity.py`
- **Golden record**: `data/fleet/db_sanity_all.yaml` (citation suffixes removed; counts stay)
- **Fixture, unchanged**: `tests/ui/fleet_dashboard/conftest.py` (`dashboard` is imported)
- **Page, unchanged**: `pages/fleet_dashboard/main_dashboard_page.py`
- **Do not edit**: `core/`, `tests/ui/`, `tests/e2e/`, `db/clients/fleet.py`, `tests/helpers/`, `tests/conftest.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the page methods this slice calls, and the broken rate lines

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/039-fleet-db-sanity"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `pages/fleet_dashboard/main_dashboard_page.py`, confirm `reset_dashboard_filters`, `get_kpi_value` for roles `total`, `in_use`, `withdrawn`, and `allocated`, `get_chart_segment_labels`, `hover_chart_segment(chart_key, label, expected_value=...)`, `parse_tooltip_entries`, `select_tab`, `search_vehicle`, and `get_table_row_text` exist, and that chart keys `unit`, `source`, `category`, and `withdrawal` are the keys in `_CHART_TITLES`. In `data/fleet/db_sanity_all.yaml`, confirm `summary` has `total_vehicles_in_use`, `total_vehicles_received`, `vehicles_transferred`, and `vehicles_credited`, and that each `vehicle_categories` rate still ends with `[cite: 1]`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Make the golden file parse and add the loader every story calls

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create an empty `tests/sanity/fleet_dashboard/__init__.py`. Leave the existing `tests/sanity/__init__.py` unchanged
- [X] T004 [P] In `data/fleet/db_sanity_all.yaml`, change the four rate lines so the values are `"0.57%"`, `"16.92%"`, `"34.24%"`, and `"10.74%"` for `אוטובוס`, `אמבולנס`, `אמצעי הובלה`, and `רכב קל`. Delete only the trailing `[cite: 1]`. Leave every count, name, and ledger row as it is. `yaml.safe_load` of the file must succeed
- [X] T005 Create `tests/sanity/fleet_dashboard/contract.py` per `specs/039-fleet-db-sanity/contracts/fleet-sanity.md` with `load_sanity_record(path=None)` and no assert functions yet. Default path is `Path(__file__).resolve().parents[3] / "data" / "fleet" / "db_sanity_all.yaml"`. Open it UTF-8 and return `yaml.safe_load`. If any of `summary`, `units_breakdown`, `pull_source_breakdown`, `vehicle_categories`, `credit_reasons_summary`, or `credited_vehicles_details` is missing, raise `AssertionError` that names the missing key. Add a private helper that builds `"{section}.{key}: actual={actual!r} expected={expected!r}"`. Import only `pathlib.Path` and `yaml`. Do not import Playwright, `pages`, `db`, or `config.settings`. Comments inside functions are English

**Checkpoint**: `load_sanity_record()` returns the fleet golden dict. Story checks can be added to `contract.py`.

---

## Phase 3: User Story 1 - Summary balances hold (Priority: P1) 🎯 MVP

**Goal**: The four summary counters are non-negative integers, and vehicles in use are not above vehicles received.

**Independent Test**: `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_summary_balances -v` loads the golden file and checks `summary` only. It does not open a browser and does not assert that received equals in use plus credited plus transferred.

### Implementation for User Story 1

- [X] T006 [US1] Add `assert_summary(record)` to `tests/sanity/fleet_dashboard/contract.py` per `specs/039-fleet-db-sanity/contracts/fleet-sanity.md`. Require `total_vehicles_in_use`, `total_vehicles_received`, `vehicles_transferred`, and `vehicles_credited`. Each value must be an `int` and `>= 0`. Reject `bool` (`isinstance(value, bool)`). Require `total_vehicles_in_use <= total_vehicles_received`. Do not compare `total_vehicles_received` to any sum of the other three counters. Failures use the helper from T005 with section `summary`
- [X] T007 [US1] Create `tests/sanity/fleet_dashboard/test_db_sanity.py` and add `test_summary_balances()` with `@pytest.mark.sanity` only. Call `load_sanity_record()` and `assert_summary`. The function takes no fixture. Do not hard-code `358`, `363`, `1`, or `6`. Do not import `dashboard`. Comments inside the function are English

**Checkpoint**: User Story 1 passes with no browser. Breakdown, rate, ledger, and UI tests are not required yet.

---

## Phase 4: User Story 2 - Breakdowns reconcile to the counters (Priority: P1)

**Goal**: Unit counts and pull-source counts each add up to vehicles in use. Credit-reason counts add up to vehicles credited.

**Independent Test**: `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_breakdowns_integrity -v` sums the three mappings from the file. It does not open a browser.

### Implementation for User Story 2

- [X] T008 [US2] Add `assert_breakdowns(record)` to `tests/sanity/fleet_dashboard/contract.py` per `specs/039-fleet-db-sanity/contracts/fleet-sanity.md`. Sum `units_breakdown` and `pull_source_breakdown` to `summary.total_vehicles_in_use`. Sum `credit_reasons_summary` to `summary.vehicles_credited`. Every mapped value is an `int` `>= 0` and is not a `bool`. Iterate the keys that are in the file. Do not sum anything to `vehicles_transferred`. Failure shape: `"{section}: sum={total} expected {summary_key}={expected}"`
- [X] T009 [US2] Add `test_breakdowns_integrity()` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `load_sanity_record()` and `assert_breakdowns`. No `dashboard` fixture. Do not hard-code unit names, source names, or the totals. Comments inside the function are English

**Checkpoint**: Summary and breakdown checks both pass without a browser.

---

## Phase 5: User Story 3 - Category rates match the standard (Priority: P1)

**Goal**: Each category rate equals actual divided by standard, and the actuals add up to vehicles received.

**Independent Test**: `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_vehicle_category_rates -v` checks every `vehicle_categories` row from the file. It does not open a browser and does not read the category chart.

### Implementation for User Story 3

- [X] T010 [US3] Add `assert_category_rates(record)` to `tests/sanity/fleet_dashboard/contract.py` per `specs/039-fleet-db-sanity/contracts/fleet-sanity.md` and `specs/039-fleet-db-sanity/data-model.md`. For each row require a non-empty `category`, an `int` `actual` `>= 0`, an `int` `standard` `>= 1`, and a `rate` string. Reject `bool`. A `standard` of `0` fails with that category name and does not divide. Parse a leading percent token from `rate` and ignore a trailing `[cite: …]` if one is still on the string. Compute `(actual / standard) * 100` with `decimal.Decimal` and `ROUND_HALF_UP` to two decimal places, then format it with a `%` suffix. The stored rate's numeric text must equal that string. The sum of `actual` must equal `summary.total_vehicles_received`. Do not hard-code `אוטובוס`, `אמבולנס`, `אמצעי הובלה`, or `רכב קל`. Failure shape: `"vehicle_categories.{category}: rate={stored!r} computed={rate!r} (actual={actual}, standard={standard})"`
- [X] T011 [US3] Add `test_vehicle_category_rates()` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `load_sanity_record()` and `assert_category_rates`. No `dashboard` fixture. Comments inside the function are English

**Checkpoint**: Summary, breakdown, and category-rate checks pass without a browser.

---

## Phase 6: User Story 4 - Credited ledger is complete (Priority: P1)

**Goal**: Every credited row has its six fields, vehicle numbers are unique, and the reason counts match the reason summary.

**Independent Test**: `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_credited_vehicles_ledger -v` walks `credited_vehicles_details`. It does not open a browser and does not require a ledger pull source to appear in `pull_source_breakdown`.

### Implementation for User Story 4

- [X] T012 [US4] Add `assert_ledger(record)` to `tests/sanity/fleet_dashboard/contract.py` per `specs/039-fleet-db-sanity/contracts/fleet-sanity.md`. Required fields, in order: `סיבת זיכוי`, `תאריך זיכוי`, `מקור משיכה`, `יחידה`, `יחידת משנה`, `מספר רכב`. Require `len(credited_vehicles_details) == summary.vehicles_credited`. Each text field is a non-empty string. `תאריך זיכוי` matches `DD/MM/YYYY` with day `01`–`31` and month `01`–`12`. `מספר רכב` is an `int`, is not a `bool`, and is unique. `סיבת זיכוי` is a key of `credit_reasons_summary`. Counts of `סיבת זיכוי` equal `credit_reasons_summary` with no extra reason and no missing reason. Do not join `מקור משיכה` to `pull_source_breakdown` or `יחידה` to `units_breakdown`. Failure names the vehicle number and the field, using `"credited_vehicles_details.{vehicle}: missing {field}"` or the actual/expected helper
- [X] T013 [US4] Add `test_credited_vehicles_ledger()` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `load_sanity_record()` and `assert_ledger`. No `dashboard` fixture. Do not hard-code vehicle numbers. Comments inside the function are English

**Checkpoint**: All four file checks pass without a browser. The report is not opened yet.

---

## Phase 7: User Story 5 - The open fleet report matches the golden baseline (Priority: P2)

**Goal**: With slicers and vehicle search cleared, the four KPI cards, the three breakdown charts, the category actuals, and the credited rows match the loaded record.

**Independent Test**: `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py -v -k ui` with portal auth. Each UI test calls `reset_dashboard_filters()` and does not call `apply_filters`. A chart that shows no golden label skips only that test. A visible label with a different count fails.

### Implementation for User Story 5

- [X] T014 [US5] In `tests/sanity/fleet_dashboard/test_db_sanity.py`, add the UI binding from `specs/039-fleet-db-sanity/contracts/fleet-sanity.md`. Import `dashboard` from `tests.ui.fleet_dashboard.conftest`. Add `normalize_label` that replaces `״` and `"` with `"`, strips, and collapses whitespace. Map `total_vehicles_received` → `total`, `total_vehicles_in_use` → `in_use`, `vehicles_credited` → `withdrawn`, `vehicles_transferred` → `allocated`. Add a helper that, given a chart key and an expected name-to-count mapping, reads `dashboard.get_chart_segment_labels(chart_key)`. If no expected name is visible after normalization, `pytest.skip` with that chart key. If any expected name is visible, every expected name must match: call `hover_chart_segment(chart_key, label, expected_value=count)` and `parse_tooltip_entries()`, and accept the count when the entries contain the label or the tooltip text contains the integer. A mismatch message includes the chart key, the segment, `ui=`, and `golden=` using the original strings. Do not import `db.clients.fleet` or `config.settings`. Comments inside the functions are English
- [X] T015 [US5] Add `test_ui_summary_kpis_match_golden(dashboard)` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `dashboard.reset_dashboard_filters()`, load the record, and assert `get_kpi_value` for `total`, `in_use`, `withdrawn`, and `allocated` against the four `summary` keys from T014. Do not call `apply_filters`. Failure message includes the summary key, `ui=`, and `golden=`. Comments inside the function are English
- [X] T016 [US5] Add `test_ui_unit_breakdown_matches_golden(dashboard)` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `dashboard.reset_dashboard_filters()` and compare `units_breakdown` to chart key `unit` with the helper from T014
- [X] T017 [US5] Add `test_ui_pull_source_matches_golden(dashboard)` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `dashboard.reset_dashboard_filters()` and compare `pull_source_breakdown` to chart key `source` with the helper from T014
- [X] T018 [US5] Add `test_ui_credit_reasons_match_golden(dashboard)` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `dashboard.reset_dashboard_filters()` and compare `credit_reasons_summary` to chart key `withdrawal` with the helper from T014
- [X] T019 [US5] Add `test_ui_category_actuals_match_golden(dashboard)` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `dashboard.reset_dashboard_filters()` and compare each `vehicle_categories` row's `category` and `actual` to chart key `category` with the helper from T014. Do not read `standard` or `rate` from the page
- [X] T020 [US5] Add `test_ui_credited_ledger_rows(dashboard)` to `tests/sanity/fleet_dashboard/test_db_sanity.py`. Decorate it with `@pytest.mark.sanity` only. Call `dashboard.reset_dashboard_filters()` and `dashboard.select_tab("withdrawn")`. For each `credited_vehicles_details` row, call `dashboard.search_vehicle(str(row["מספר רכב"]))` and require `get_table_row_text` to contain the reason, date, pull source, unit, and subunit after `normalize_label`. A missing piece names the vehicle number and the field. Do not hard-code the six vehicle numbers

**Checkpoint**: The ten tests in the contract exist. Structural tests still pass without a browser. UI tests need portal auth.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Collect the module from `specs/039-fleet-db-sanity/quickstart.md` and confirm the untouched paths

- [X] T021 Run `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py --collect-only` from `specs/039-fleet-db-sanity/quickstart.md` and confirm the ten node ids named there: `test_summary_balances`, `test_breakdowns_integrity`, `test_vehicle_category_rates`, `test_credited_vehicles_ledger`, `test_ui_summary_kpis_match_golden`, `test_ui_unit_breakdown_matches_golden`, `test_ui_pull_source_matches_golden`, `test_ui_credit_reasons_match_golden`, `test_ui_category_actuals_match_golden`, `test_ui_credited_ledger_rows`
- [X] T022 [P] Confirm the only code edits for this slice are `data/fleet/db_sanity_all.yaml` (rate suffixes), `tests/sanity/fleet_dashboard/__init__.py`, `tests/sanity/fleet_dashboard/contract.py`, and `tests/sanity/fleet_dashboard/test_db_sanity.py`. Confirm `core/`, `pages/fleet_dashboard/main_dashboard_page.py`, `tests/ui/`, `tests/e2e/`, `db/clients/fleet.py`, `tests/helpers/`, and `tests/conftest.py` are unchanged
- [X] T023 Run `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py -v -k "not ui"` from `specs/039-fleet-db-sanity/quickstart.md`. These four tests need no portal auth. A pass means the file checks in User Stories 1–4 hold, including rates `0.57%`, `16.92%`, `34.24%`, and `10.74%`
- [X] T024 Run `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py -v -k ui` from `specs/039-fleet-db-sanity/quickstart.md`. Portal auth is required. A pass means the cleared report matches `summary` and each chart that shows golden labels matches those counts. A chart with no golden labels skips only that test. A failure names the section, the key or vehicle, and both values

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks every user story
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on later stories
- **User Story 2 (Phase 4)**: Depends on Foundational. Append it after User Story 1 because both edit `contract.py` and `test_db_sanity.py`. The breakdown sums do not depend on the summary inequality beyond the shared loader
- **User Story 3 (Phase 5)**: Depends on Foundational. Append it after User Story 2 because it edits the same two files. The rate check does not depend on the breakdown sums
- **User Story 4 (Phase 6)**: Depends on Foundational. Append it after User Story 3 because it edits the same two files. The ledger check does not depend on category rates
- **User Story 5 (Phase 7)**: Depends on Foundational and on T007, because the UI tests are appended to `test_db_sanity.py`. It reads the golden file through `load_sanity_record` and does not call `assert_summary`, `assert_breakdowns`, `assert_category_rates`, or `assert_ledger`
- **Polish (Phase 8)**: Depends on User Stories 1–5

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T005. Uses `load_sanity_record` and `assert_summary`
- **User Story 2 (P1)**: Starts after T007 so the edits to `contract.py` and `test_db_sanity.py` do not overlap
- **User Story 3 (P1)**: Starts after T009 for the same reason
- **User Story 4 (P1)**: Starts after T011 for the same reason
- **User Story 5 (P2)**: Starts after T013 so the six UI tests are appended after the four structural tests. T015–T020 stay in order because they edit `test_db_sanity.py`

### Within Each User Story

- The check function in `contract.py` lands before the test that calls it
- User Story 5 adds the chart helper in T014 before the six UI tests
- The live portal run waits until T020

### Parallel Opportunities

- T002 can run with T001
- T003 and T004 touch different files and can run together
- T005 waits until T004, because `load_sanity_record` must be able to parse the file
- T006–T020 stay sequential because they edit `contract.py` or `test_db_sanity.py`
- T022 can run beside T021. T023 waits until collection succeeds. T024 waits until T023 passes

---

## Parallel Example: Setup and package marker

```bash
# Phase 1 confirmation and the two foundational file edits can proceed together:
Task: "Confirm page methods in pages/fleet_dashboard/main_dashboard_page.py and the rate suffixes in data/fleet/db_sanity_all.yaml"
Task: "Create empty tests/sanity/fleet_dashboard/__init__.py"
Task: "Remove [cite: 1] from the four rate lines in data/fleet/db_sanity_all.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T006 and T007 so `test_summary_balances` checks the four counters and `in use <= received`
3. **STOP and VALIDATE**: `python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_summary_balances -v`

### Incremental Delivery

1. Setup confirms the page API and the citation suffixes
2. Foundational makes the YAML parse and adds `load_sanity_record`
3. User Story 1 checks summary balances
4. User Story 2 checks breakdown sums
5. User Story 3 checks category rates
6. User Story 4 checks the credited ledger
7. User Story 5 compares the cleared fleet report to the same file
8. Phase 8 collects all ten tests, runs the four file checks, then runs the UI checks with portal auth

### Parallel Team Strategy

T006–T020 edit `tests/sanity/fleet_dashboard/contract.py` or `tests/sanity/fleet_dashboard/test_db_sanity.py`. One person owns those two files. T003 and T004 can be done by anyone before T005.

---

## Notes

- Keep fleet labels and the golden path out of `core/`
- Call `reset_dashboard_filters()` in every UI test. Do not call `apply_filters` and do not select a district
- Do not assert `total_vehicles_received = total_vehicles_in_use + vehicles_credited + vehicles_transferred`
- Do not join ledger pull sources to `pull_source_breakdown` or ledger units to `units_breakdown`
- Do not call `DatabaseClient` or read `settings.DB_ENVIRONMENT`
- Do not edit `pages/fleet_dashboard/main_dashboard_page.py`
- Mark tests with `@pytest.mark.sanity` only
- Comments inside functions in `tests/sanity/fleet_dashboard/contract.py` and `tests/sanity/fleet_dashboard/test_db_sanity.py` stay English
- Do not run `pytest tests/ui/fleet_dashboard/`. This slice does not change Layer 0, Layer 2, or the fleet page
