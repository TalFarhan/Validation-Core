---
description: "Task list for architecture normalization and folder alignment"
---

# Tasks: Architecture Normalization

**Input**: Design documents from `/specs/018-architecture-normalization/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/module-layout.md, contracts/constitution-amendment.md, quickstart.md

**Tests**: The spec does not ask for new test modules. Do not add test files. Each story ends
with the check named in its independent test. Page modules move, so Constitution III makes
`pytest tests/ui/fleet_dashboard/` a completion gate (T041). Do not edit `core/`,
`db/connection.py`, `db/clients/alerts.py`, or `tests/helpers/db_parity_engine.py`.

**Organization**: US1 (pages under `pages/`) is the MVP. US3 (fleet SQL module) and US5 (data
paths) run before US2 so the new fleet fixtures import `db.clients.fleet` and read `data/fleet/`
on the first write. US4 moves helpers after the pages exist. US6 confirms the fleet-only UI
boundary. US7 amends the constitution after the paths are real. Specs `001`–`017` stay historical.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US7)
- Exact file paths are included in each task

## Path Conventions

- Report pages: `pages/<report>/page.py` (fleet stays `pages/fleet_dashboard/main_dashboard_page.py`)
- Suites: `tests/ui/<suite>/` keep smoke tests and `conftest.py`; they lose `page.py`
- Fleet fixtures: `tests/ui/fleet_dashboard/conftest.py` and `tests/e2e/conftest.py`
- Fleet SQL: `db/clients/fleet.py` (`DatabaseClient`, `KpiType`)
- Generic connection: `db/connection.py` (do not edit)
- Alerts SQL: `db/clients/alerts.py` (do not edit)
- Catalogs: `data/fleet/filters.json`, `data/fleet/filter_matrix.json`, `data/alerts/alerts_contract.yaml`
- Generic helpers that stay: `tests/helpers/db_parity_engine.py`, `tests/helpers/dashboard_fixture.py`
- Contracts: `specs/018-architecture-normalization/contracts/module-layout.md`, `specs/018-architecture-normalization/contracts/constitution-amendment.md`

---

## Phase 1: Setup (Baseline)

**Purpose**: Confirm this slice adds no package and does not retarget pytest.

- [X] T001 Confirm `pytest`, `playwright`, and `sqlalchemy` are already in `requirements.txt` and `testpaths = tests` is already in `pytest.ini`. Do not add a dependency, a marker, or a path (plan.md Technical Context)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the destination directories every story writes into. No story starts until they exist.

**⚠️ CRITICAL**: No user-story move starts until these directories exist. Do not add `__init__.py` (`pages/` is already a namespace package).

- [X] T002 Create these directories if they are missing: `pages/alerts_analysis/`, `pages/authorities_status/`, `pages/credit_consumption/`, `pages/hosen_status/`, `pages/life_saving_guidelines/`, `pages/marsal/`, `pages/mass_events/`, `pages/maya_system/`, `pages/power_outages/`, `pages/public_inquiries/`, `pages/public_shelters/`, `pages/rescue_capabilities/`, `data/fleet/`, `data/alerts/`. Do not create `pages/fleet/` and do not add `__init__.py` (contracts/module-layout.md §1, research.md R1)

**Checkpoint**: Destination folders exist. Story work can start with US1.

---

## Phase 3: User Story 1 - Report pages live under `pages/` (Priority: P1) 🎯 MVP

**Goal**: Every report page class under `tests/ui/` lives in `pages/<report>/page.py`. Suite folders keep their smoke tests and conftests.

**Independent Test**: `Get-ChildItem -Recurse tests/ui -Filter page.py` returns nothing. `from pages.alerts_analysis.page import AlertsAnalysisPage` succeeds. `pages/fleet_dashboard/main_dashboard_page.py` is still the fleet page.

### Implementation for User Story 1

- [X] T003 [P] [US1] Move `tests/ui/alerts_analysis_dashboard/page.py` to `pages/alerts_analysis/page.py`. Keep class `AlertsAnalysisPage` and the file body, including the `Slicer` composition. In `tests/ui/alerts_analysis_dashboard/conftest.py`, replace the page import with `from pages.alerts_analysis.page import AlertsAnalysisPage`. Keep `from db.clients.alerts import AlertsDBRunner`, `bind_dashboard`, `dashboard = bind_dashboard(AlertsAnalysisPage)`, and the `alerts_db` fixture. Delete the old `page.py` (FR-001, FR-002, contracts/module-layout.md §1) — depends on T002
- [X] T004 [P] [US1] Move `tests/ui/authorities_status_dashboard/page.py` to `pages/authorities_status/page.py`. Keep class `AuthoritiesStatusPage` and the file body. In `tests/ui/authorities_status_dashboard/conftest.py`, import `from pages.authorities_status.page import AuthoritiesStatusPage` and keep `dashboard = bind_dashboard(AuthoritiesStatusPage)`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T005 [P] [US1] Move `tests/ui/credit_consumption_dashboard/page.py` to `pages/credit_consumption/page.py`. Keep class `CreditConsumptionPage` and the popup methods (`before_report_ready_check`, `after_navigate`, `_close_info_popup`) in that file. Do not extract them into `core/`. In `tests/ui/credit_consumption_dashboard/conftest.py`, import `from pages.credit_consumption.page import CreditConsumptionPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002, spec edge case) — depends on T002
- [X] T006 [P] [US1] Move `tests/ui/hosen_status_dashboard/page.py` to `pages/hosen_status/page.py`. Keep class `HosenStatusPage` and the file body. In `tests/ui/hosen_status_dashboard/conftest.py`, import `from pages.hosen_status.page import HosenStatusPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T007 [P] [US1] Move `tests/ui/life_saving_guidelines_dashboard/page.py` to `pages/life_saving_guidelines/page.py`. Keep class `LifeSavingGuidelinesPage` and the file body, including `from tests.helpers.secondary_auth import bypass_secondary_auth` (T032 changes that import). In `tests/ui/life_saving_guidelines_dashboard/conftest.py`, import `from pages.life_saving_guidelines.page import LifeSavingGuidelinesPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T008 [P] [US1] Move `tests/ui/marsal_dashboard/page.py` to `pages/marsal/page.py`. Keep class `MarsalPage` and the file body. In `tests/ui/marsal_dashboard/conftest.py`, import `from pages.marsal.page import MarsalPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T009 [P] [US1] Move `tests/ui/mass_events_dashboard/page.py` to `pages/mass_events/page.py`. Keep class `MassEventsPage` and the file body, including `from tests.helpers.secondary_auth import bypass_secondary_auth` (T032 changes that import). In `tests/ui/mass_events_dashboard/conftest.py`, import `from pages.mass_events.page import MassEventsPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T010 [P] [US1] Move `tests/ui/maya_system_dashboard/page.py` to `pages/maya_system/page.py`. Keep class `MayaSystemPage` and the file body, including `from tests.helpers.secondary_auth import bypass_secondary_auth` (T032 changes that import). In `tests/ui/maya_system_dashboard/conftest.py`, import `from pages.maya_system.page import MayaSystemPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T011 [P] [US1] Move `tests/ui/power_outages_dashboard/page.py` to `pages/power_outages/page.py`. Keep class `PowerOutagesPage` and the file body. In `tests/ui/power_outages_dashboard/conftest.py`, import `from pages.power_outages.page import PowerOutagesPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T012 [P] [US1] Move `tests/ui/public_inquiries_dashboard/page.py` to `pages/public_inquiries/page.py`. Keep class `PublicInquiriesPage` and the file body. In `tests/ui/public_inquiries_dashboard/conftest.py`, import `from pages.public_inquiries.page import PublicInquiriesPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T013 [P] [US1] Move `tests/ui/public_shelters_dashboard/page.py` to `pages/public_shelters/page.py`. Keep class `PublicSheltersPage` and the file body, including `from tests.helpers.secondary_auth import bypass_secondary_auth` (T032 changes that import). In `tests/ui/public_shelters_dashboard/conftest.py`, import `from pages.public_shelters.page import PublicSheltersPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T014 [P] [US1] Move `tests/ui/rescue_capabilities_dashboard/page.py` to `pages/rescue_capabilities/page.py`. Keep class `RescueCapabilitiesPage` and the file body. In `tests/ui/rescue_capabilities_dashboard/conftest.py`, import `from pages.rescue_capabilities.page import RescueCapabilitiesPage` and keep `bind_dashboard`. Delete the old `page.py` (FR-001, FR-002) — depends on T002
- [X] T015 [US1] Confirm `pages/fleet_dashboard/main_dashboard_page.py` still defines `MainDashboardPage` and was not renamed. Run `Get-ChildItem -Recurse tests/ui -Filter page.py` and confirm it prints nothing. Run `python -c "from pages.alerts_analysis.page import AlertsAnalysisPage; from pages.power_outages.page import PowerOutagesPage; from pages.maya_system.page import MayaSystemPage; print(AlertsAnalysisPage.__name__)"` and confirm it prints `AlertsAnalysisPage` (FR-003, SC-001, quickstart.md step 1) — depends on T003–T014

**Checkpoint**: Report pages import from `pages/`. Suite smoke modules are still under `tests/ui/<suite>/`. The fleet page path is unchanged.

---

## Phase 4: User Story 3 - Report SQL lives under `db/clients/` (Priority: P1)

**Goal**: Fleet SQL is `db/clients/fleet.py`. `db/client.py` is gone. Alerts SQL and the connection factory stay put.

**Independent Test**: `from db.clients.fleet import DatabaseClient, KpiType` works. `import db` has no `DatabaseClient` attribute. `db/client.py` does not exist. `db/connection.py` and `db/clients/alerts.py` have no diff.

### Implementation for User Story 3

- [X] T016 [US3] Create `db/clients/fleet.py` by moving `DatabaseClient`, `KpiType`, `_DIM_STATUS_FILTERS`, and the class helpers out of `db/client.py`. Keep these public methods and their signatures: `count_vehicles`, `get_dashboard_kpis`, `get_vehicle_by_id`, `get_sample_vehicle_id`, `get_unique_vehicle_id_for_search`, `count_vehicles_by_id_contains`, `count_grouped_by`, `count_by_source`, `count_by_unit`, `count_by_sub_unit`, `count_by_category`, `count_by_withdrawal_reason`, `find_zero_count_filters`. Keep imports of `config.settings`, `db.connection.create_db_engine`, and `reports.test_run_report`. Do not change SQL text. Do not rename the class to `FleetDBRunner` (FR-007, data-model.md ReportSqlClient, research.md R3)
- [X] T017 [P] [US3] Delete `db/client.py` (FR-007, research.md R3) — depends on T016
- [X] T018 [P] [US3] Edit `db/__init__.py` so it does not import `DatabaseClient` or `AlertsDBRunner` and does not export them. Replace the docstring `Database package for QA Fleet validation.` with `Read-only warehouse clients.` (FR-007, research.md R3) — depends on T016
- [X] T019 [P] [US3] In `tests/helpers/dashboard_validation.py` and root `conftest.py`, replace `from db.client import DatabaseClient` with `from db.clients.fleet import DatabaseClient`. In `tests/helpers/dashboard_validation.py`, also import `KpiType` from `db.clients.fleet`. Do not edit `db/connection.py` or `db/clients/alerts.py` (FR-007, FR-008, contracts/module-layout.md §4) — depends on T016
- [X] T020 [US3] Run `python -c "from db.clients.fleet import DatabaseClient, KpiType; import db; assert not hasattr(db, 'DatabaseClient'); print(DatabaseClient.__name__)"` and confirm it prints `DatabaseClient`. Confirm `db/client.py` is absent (quickstart.md step 3) — depends on T017, T018, T019

**Checkpoint**: Fleet SQL imports from `db.clients.fleet`. Root `conftest.py` still owns the fleet fixtures; US2 removes them.

---

## Phase 5: User Story 5 - Report data lives under `data/<report>/` (Priority: P2)

**Goal**: Fleet catalogs live in `data/fleet/`. The alerts contract lives in `data/alerts/`. The parity engine still receives a path.

**Independent Test**: The three new paths exist, the three old paths do not, and `python -m pytest tests/unit/test_db_parity_engine.py -q --tb=line` passes.

### Implementation for User Story 5

- [X] T021 [P] [US5] Move `data/filters.json` to `data/fleet/filters.json` and `data/filter_matrix.json` to `data/fleet/filter_matrix.json`. Do not change file bytes. Leave `data/raw/` where it is (FR-012, FR-014, research.md R6) — depends on T002
- [X] T022 [P] [US5] Move `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` to `data/alerts/alerts_contract.yaml`. Do not change file bytes (FR-013, research.md R6) — depends on T002
- [X] T023 [US5] Point the remaining readers at the new files. In root `conftest.py`, open `data/fleet/filters.json` and `data/fleet/filter_matrix.json` from the fixtures that still live there (`filter_data`, `filter_matrix`). In `tests/e2e/test_filter_matrix.py`, set `MATRIX_PATH = Path(__file__).resolve().parents[2] / "data" / "fleet" / "filter_matrix.json"`. In `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, set `CONTRACT_PATH = Path(__file__).resolve().parents[3] / "data" / "alerts" / "alerts_contract.yaml"`. In `tests/unit/test_db_parity_engine.py`, set `CONTRACT = Path(__file__).resolve().parents[2] / "data" / "alerts" / "alerts_contract.yaml"`. Keep passing that path into `validate_dashboard_generic`. Do not change the function signature in `tests/helpers/db_parity_engine.py` and do not add a skip (FR-012, FR-013, contracts/module-layout.md §6) — depends on T021, T022
- [X] T024 [US5] Run `python -m pytest tests/unit/test_db_parity_engine.py -q --tb=line` and confirm it passes with no browser (SC-004 unit portion, quickstart.md step 4) — depends on T023

**Checkpoint**: Catalog bytes moved. Root fixtures still load fleet JSON until US2 relocates those fixtures.

---

## Phase 6: User Story 2 - Alerts collection does not load the fleet page (Priority: P1)

**Goal**: Root `conftest.py` keeps browser, session, and run-report fixtures only. Fleet `dashboard` and database fixtures live in the fleet suite and in `tests/e2e/`.

**Independent Test**: A search of root `conftest.py` finds no `MainDashboardPage`, `DatabaseClient`, `db.client`, or `db.clients.fleet`. Importing `tests.ui.alerts_analysis_dashboard.conftest` leaves `pages.fleet_dashboard.main_dashboard_page` and `db.clients.fleet` out of `sys.modules`. Collecting fleet and e2e still resolves `dashboard`, `db_client`, `filter_data`, `filter_matrix`, and `zero_count_filters`.

### Implementation for User Story 2

- [X] T025 [P] [US2] Create `tests/ui/fleet_dashboard/conftest.py` with fixtures `dashboard`, `db_client`, `filter_data`, `filter_matrix`, and `zero_count_filters` exactly as in `specs/018-architecture-normalization/contracts/module-layout.md` §3. Set `FLEET_DATA = Path(__file__).resolve().parents[3] / "data" / "fleet"`. Import `DatabaseClient` from `db.clients.fleet`, `MainDashboardPage` from `pages.fleet_dashboard.main_dashboard_page`, and `open_report` from `tests.helpers.dashboard_fixture`. `dashboard` calls `open_report(MainDashboardPage, auth_page, browser_context)`. `zero_count_filters` skips with `No zero-count filter combination found in test data` when the combo is `None` (FR-005, data-model.md FleetFixtureSet) — depends on T016, T021
- [X] T026 [P] [US2] Create `tests/e2e/conftest.py` with the same five fixtures. Set `FLEET_DATA = Path(__file__).resolve().parents[2] / "data" / "fleet"`. Use the same imports as T025. Do not set `pytest_plugins` (FR-005, research.md R2) — depends on T016, T021
- [X] T027 [US2] Edit root `conftest.py`. Remove `from db.clients.fleet import DatabaseClient` (or any `db.client` import), `from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage`, `from tests.helpers.dashboard_fixture import open_report`, `DATA_DIR`, and the fixtures `db_client`, `filter_data`, `filter_matrix`, `zero_count_filters`, and `dashboard`. Keep `save_auth_state`, `browser_context`, `session_page`, `auth_page`, `run_report_book`, `test_run_report`, `video_run_dir`, failure screenshots, traces, and the HTML/report hooks (FR-004, contracts/module-layout.md §2) — depends on T025, T026
- [X] T028 [US2] Run the quickstart step 2 commands from `specs/018-architecture-normalization/quickstart.md`: `rg -n "MainDashboardPage|DatabaseClient|db\.client|db\.clients\.fleet|filters\.json" conftest.py` prints nothing, and the `python -c` import of `tests.ui.alerts_analysis_dashboard.conftest` prints `alerts collection is fleet-free`. Then run `python -m pytest tests/ui/alerts_analysis_dashboard tests/ui/fleet_dashboard tests/e2e --collect-only -q` and confirm exit code 0 (FR-006, SC-002, SC-003, SC-004) — depends on T015, T027

**Checkpoint**: Collecting alerts does not import the fleet page or the fleet SQL client. Fleet UI and e2e still have the five fixtures.

---

## Phase 7: User Story 4 - Helpers stay generic (Priority: P2)

**Goal**: `tests/helpers/` keeps the parity engine and the dashboard opener. Fleet assertions sit with the fleet suite. ArcGIS login sits in `pages/secondary_auth.py`.

**Independent Test**: `tests/helpers/` contains only `db_parity_engine.py` and `dashboard_fixture.py`. `from pages.secondary_auth import bypass_secondary_auth` works. E2E modules import `tests.ui.fleet_dashboard.dashboard_validation`.

### Implementation for User Story 4

- [X] T029 [P] [US4] Move `tests/helpers/dashboard_validation.py` to `tests/ui/fleet_dashboard/dashboard_validation.py`. Keep every function signature, including `KPI_TYPES`, `apply_filters`, `db_filter_kwargs`, and `assert_all_kpis_match_db`. The `DatabaseClient` and `KpiType` import must stay `from db.clients.fleet import DatabaseClient, KpiType` (FR-010, research.md R4, data-model.md GenericHelper) — depends on T019
- [X] T030 [US4] Replace `from tests.helpers.dashboard_validation import` with `from tests.ui.fleet_dashboard.dashboard_validation import` in `tests/e2e/test_chart_drilldown.py`, `tests/e2e/test_chart_tooltips.py`, `tests/e2e/test_chart_validation.py`, `tests/e2e/test_edge_cases.py`, `tests/e2e/test_filter_matrix.py`, `tests/e2e/test_kpi_validation.py`, `tests/e2e/test_table_validation.py`, and `tests/ui/fleet_dashboard/test_dashboard_smoke.py`. Leave `from pages.fleet_dashboard.main_dashboard_page import ExpandHierarchyUnavailable` in `tests/e2e/test_chart_drilldown.py`. Do not add an import to `tests/e2e/test_data_invariants.py` (FR-010, contracts/module-layout.md §5) — depends on T029
- [X] T031 [P] [US4] Move `tests/helpers/secondary_auth.py` to `pages/secondary_auth.py`. Keep `bypass_secondary_auth` and its signature. Update the module docstring so it names `pages/secondary_auth.py` and still says the flow stays outside `core/`. Do not move the file under `core/` (FR-011, research.md R5) — depends on T002
- [X] T032 [US4] In `pages/mass_events/page.py`, `pages/life_saving_guidelines/page.py`, `pages/maya_system/page.py`, and `pages/public_shelters/page.py`, replace `from tests.helpers.secondary_auth import bypass_secondary_auth` with `from pages.secondary_auth import bypass_secondary_auth`. Do not change the `_bypass_secondary_auth` method bodies (FR-011, contracts/module-layout.md §1) — depends on T007, T009, T010, T013, T031
- [X] T033 [US4] Confirm `tests/helpers/` contains `db_parity_engine.py` and `dashboard_fixture.py` and does not contain `dashboard_validation.py` or `secondary_auth.py`. Confirm `open_report` in `tests/helpers/dashboard_fixture.py` still lazily imports `save_auth_state` from `conftest`. Do not change `validate_dashboard_generic`, `open_report`, or `bind_dashboard` signatures (FR-009, research.md R9) — depends on T029, T031

**Checkpoint**: Helpers are generic. Fleet validation and ArcGIS login have their new homes.

---

## Phase 8: User Story 6 - Fleet-only UI stays on the fleet page (Priority: P2)

**Goal**: Tables, tooltips, and drilldowns stay on `MainDashboardPage`. Generic visual readers stay in `core/components/` and are not edited.

**Independent Test**: The methods listed below are still defined on `MainDashboardPage`. `git diff` for `core/components`, `core/portal`, `db/connection.py`, `db/clients/alerts.py`, and `tests/helpers/db_parity_engine.py` is empty.

### Implementation for User Story 6

- [X] T034 [P] [US6] Confirm `pages/fleet_dashboard/main_dashboard_page.py` still defines `get_table_row_count`, `search_vehicle`, `tooltip`, `expand_chart_hierarchy`, `drill_up_chart`, `get_chart_segment_labels`, and `expand_via_tooltip_drilldown` on `MainDashboardPage`. Do not move those methods and do not edit the file (FR-015, research.md R7)
- [X] T035 [P] [US6] Confirm `git diff -- core/components core/portal db/connection.py db/clients/alerts.py tests/helpers/db_parity_engine.py` is empty. Do not edit those paths (FR-008, FR-009, FR-015, contracts/module-layout.md §7)

**Checkpoint**: Layer 2 and the fleet-only UI boundary are unchanged.

---

## Phase 9: User Story 7 - The constitution names the three paths (Priority: P1)

**Goal**: Constitution 1.3.0 requires `pages/<report>/`, `core/components/`, and `db/clients/<report>.py`. Templates and living docs use the same paths.

**Independent Test**: `.specify/memory/constitution.md` shows version 1.3.0, last amended 2026-10-14, and the architecture constraints name those three paths plus `data/<report>/`.

### Implementation for User Story 7

- [X] T036 [P] [US7] Amend `.specify/memory/constitution.md` from 1.2.0 to 1.3.0 (MINOR) using `specs/018-architecture-normalization/contracts/constitution-amendment.md`. Update the sync impact report, the added paragraphs in Principles I, II, and V, the Principle VII replacement, the architecture-constraint bullets, and the quality-gate sentence. Set Last Amended to 2026-10-14. Keep Ratified 2026-08-23 (FR-016, SC-006)
- [X] T037 [P] [US7] Update `.specify/templates/plan-template.md`, `.specify/templates/spec-template.md`, and `.specify/templates/tasks-template.md` as specified in `specs/018-architecture-normalization/contracts/constitution-amendment.md` (Constitution Check bullet, Validation Core tree comment, AC-005, new AC-006, tasks path convention). Do not edit `.specify/templates/constitution-template.md` (FR-016) — depends on T002
- [X] T038 [P] [US7] Update the project tree and the Hebrew layer table in `README.md` to the rows in `specs/018-architecture-normalization/contracts/constitution-amendment.md`. Point the filter-not-found troubleshooting line at `data/fleet/filters.json` (FR-016) — depends on T021
- [X] T039 [US7] In `docs/COVERAGE_CATALOG.md`, replace `data/filters.json` with `data/fleet/filters.json`, `data/filter_matrix.json` with `data/fleet/filter_matrix.json`, `tests/helpers/dashboard_validation.py` with `tests/ui/fleet_dashboard/dashboard_validation.py`, and `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` with `data/alerts/alerts_contract.yaml`. Do not edit `specs/001-*` through `specs/017-*` (FR-016, research.md R8) — depends on T022, T029

**Checkpoint**: A reviewer can reject a page under `tests/`, report SQL outside `db/clients/`, or a domain label in `core/components/` by citing constitution 1.3.0.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Run the structural quickstart and the fleet smoke gate.

- [X] T040 Run steps 1–4 of `specs/018-architecture-normalization/quickstart.md` (page import, root conftest search, client import, path existence, `--collect-only`, and `tests/unit/test_db_parity_engine.py`). All of them pass with no browser (SC-001, SC-002, SC-003, SC-004) — depends on T028, T033, T035
- [X] T041 Run `python -m pytest tests/ui/fleet_dashboard/ -q --tb=short` and confirm it is 100% green. This needs the saved portal session. The feature is not done until this passes (SC-005, Constitution III, quickstart.md step 5) — depends on T040
- [X] T042 Confirm `.specify/memory/constitution.md` is version 1.3.0, last amended 2026-10-14, and names `pages/<report>/`, `core/components/`, `db/clients/<report>.py`, and `data/<report>/` (SC-006, quickstart.md step 6) — depends on T036, T039

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every move.
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on other stories. MVP.
- **User Story 3 (Phase 4)**: Depends on Foundational. No dependency on US1. Runs before US2 so fixture files import `db.clients.fleet` once.
- **User Story 5 (Phase 5)**: Depends on Foundational. Runs before US2 so fixture files read `data/fleet/` once. Edits root `conftest.py` paths that US2 then deletes.
- **User Story 2 (Phase 6)**: Depends on US3 (T016) and US5 (T021). The collection check (T028) also depends on US1 (T015).
- **User Story 4 (Phase 7)**: Page import edits depend on US1. The validation-module move depends on US3's import update (T019).
- **User Story 6 (Phase 8)**: Can start after Foundational. It only reads files. Run it after the moves so the empty-diff check is meaningful.
- **User Story 7 (Phase 9)**: Constitution text can be written from the contract at any time. README and the coverage catalog depend on US4 and US5 so the paths they name exist.
- **Polish (Phase 10)**: Depends on US1–US7.

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational. MVP. Does not wait for SQL, fixtures, or data.
- **User Story 3 (P1)**: After Foundational. Does not wait for US1.
- **User Story 5 (P2)**: After Foundational. Scheduled before US2 because both would otherwise edit the same path strings.
- **User Story 2 (P1)**: After US3 and US5. Pytest cannot share fixtures between `tests/ui/fleet_dashboard/` and `tests/e2e/`, so both conftests are required before the root fixtures are removed.
- **User Story 4 (P2)**: After US1 (four page imports) and US3 (fleet client import inside the validation module).
- **User Story 6 (P2)**: No code dependency. Its diff check is valid only after the other stories have stopped touching `core/`.
- **User Story 7 (P1)**: Catalog and README tasks follow US4 and US5. The constitution file itself does not import code.

### Within Each User Story

- US1 page moves touch different suite folders and run in parallel. T015 runs after all twelve.
- US3 creates `db/clients/fleet.py` before the delete, the package export edit, and the import edits.
- US5 moves the bytes before any path constant changes. The unit file runs after the path edit.
- US2 creates both conftests before it strips the root module.
- US4 moves each helper before updating its callers.
- No new tests are written first. The spec's checks are the story checkpoints.

### Parallel Opportunities

- T003–T014 move different page modules and can run together.
- T017, T018, and T019 touch different files and can run together after T016.
- T021 and T022 move different data files and can run together.
- T025 and T026 create different conftest files and can run together.
- T029 and T031 move different helpers and can run together.
- T034 and T035 are read-only checks and can run together.
- T036, T037, and T038 edit different docs and can run together. T039 waits for the validation module and the alerts contract to be in their new paths.

---

## Parallel Example: User Story 1

```text
Task: "T003 [P] [US1] Move alerts page to pages/alerts_analysis/page.py"
Task: "T004 [P] [US1] Move authorities status page to pages/authorities_status/page.py"
Task: "T011 [P] [US1] Move power outages page to pages/power_outages/page.py"
Task: "T010 [P] [US1] Move Maya page to pages/maya_system/page.py"
```

## Parallel Example: User Story 2

```text
Task: "T025 [P] [US2] Create tests/ui/fleet_dashboard/conftest.py"
Task: "T026 [P] [US2] Create tests/e2e/conftest.py"
```

## Parallel Example: User Story 7

```text
Task: "T036 [P] [US7] Amend .specify/memory/constitution.md to 1.3.0"
Task: "T037 [P] [US7] Update plan, spec, and tasks templates"
Task: "T038 [P] [US7] Update README.md layer table"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and run T015. Pages import from `pages/`. No `page.py` remains under `tests/ui/`.

### Incremental Delivery

1. Setup + Foundational.
2. US1 moves the twelve page classes. Suite tests stay put.
3. US3 moves `DatabaseClient` to `db/clients/fleet.py` and deletes `db/client.py`.
4. US5 moves fleet JSON and the alerts contract. The unit parity file still passes.
5. US2 removes fleet fixtures from root `conftest.py` after both suite conftests define them.
6. US4 moves fleet validation and ArcGIS login out of `tests/helpers/`.
7. US6 confirms fleet tables, tooltips, and drilldowns stayed on `MainDashboardPage`.
8. US7 publishes constitution 1.3.0 and updates living docs.
9. Polish runs the quickstart and requires fleet smoke at 100%.

### Parallel Team Strategy

After Foundational:

- One implementer can take all of US1 (twelve page folders).
- Another can take US3, then US5, while US1 is in progress. They meet at US2, which needs both the fleet client and `data/fleet/`.
- US4 starts once US1 has moved the four ArcGIS pages and US3 has retargeted the validation import.
- US7's constitution and template edits can proceed from the contract while code moves. README and the coverage catalog wait until the files are in place.

---

## Notes

- `[P]` tasks use different files and have no ordering dependency.
- `[USn]` maps the task to the spec user story.
- Do not rename `pages/fleet_dashboard/main_dashboard_page.py` to `pages/fleet/page.py`.
- Do not rename test directories. They keep the `_dashboard` suffix.
- Do not rename `DatabaseClient`.
- Do not add a re-export in `db/client.py`.
- Do not register fleet fixtures with `pytest_plugins` or from root `conftest.py`.
- JSON and YAML contents move unchanged. SQL text does not change.
- `data/raw/` stays.
- Specs `001` through `017` are not rewritten.
