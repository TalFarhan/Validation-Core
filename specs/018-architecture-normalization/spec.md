# Feature Specification: Architecture Normalization

**Feature Branch**: `018-architecture-normalization` (spec directory; git checkout is unchanged)

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Architecture Normalization and Folder Structure Alignment (7 Steps). Move report pages from `tests/ui/` to `pages/<report>/`. Isolate fleet fixtures from the root `conftest.py`. Split the fleet SQL client into `db/clients/`. Keep generic helpers in `tests/helpers/` and move fleet validation plus shared ArcGIS login out. Consolidate report data under `data/<report>/`. Keep fleet-specific tables, tooltips, and drilldowns on the fleet page. Update the constitution so report pages, visual components, and report SQL have one legal path each."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Report pages live under `pages/` (Priority: P1)

An engineer opening a report suite finds the page object next to the fleet page, under `pages/<report>/`, and finds only tests, fixtures, and (until Story 5) no page class inside `tests/ui/<suite>/`.

**Why this priority**: Page objects under test packages are the break in the three-layer layout. Every other move assumes a page can be imported from `pages/`.

**Independent Test**: Import each moved page class from `pages.<report>.page` and collect that suite's smoke test. No `page.py` remains under `tests/ui/`.

**Acceptance Scenarios**:

1. **Given** `AlertsAnalysisPage` is defined in `tests/ui/alerts_analysis_dashboard/page.py`, **When** this story is done, **Then** the class lives in `pages/alerts_analysis/page.py` and `tests/ui/alerts_analysis_dashboard/conftest.py` imports it from there.
2. **Given** the other report page modules under `tests/ui/` (`power_outages`, `maya_system`, and the rest of the suite list in FR-001), **When** this story is done, **Then** each class keeps its name and lives in `pages/<report>/page.py`, and that suite's smoke test and conftest stay in `tests/ui/<suite>/`.
3. **Given** the fleet page already lives in `pages/fleet_dashboard/main_dashboard_page.py`, **When** this story is done, **Then** that path and `MainDashboardPage` are unchanged.

---

### User Story 2 - Alerts collection does not load the fleet page (Priority: P1)

An engineer runs the alerts suite. Pytest still starts the shared browser, session, and run-report fixtures. It does not import `MainDashboardPage` or the fleet SQL client.

**Why this priority**: The root `conftest.py` currently imports the fleet page and `DatabaseClient` for every test, including alerts.

**Independent Test**: Collect `tests/ui/alerts_analysis_dashboard` and assert `pages.fleet_dashboard.main_dashboard_page` and `db.clients.fleet` are not loaded. Collect `tests/ui/fleet_dashboard` and `tests/e2e` and assert the fixtures `dashboard`, `db_client`, `filter_data`, `filter_matrix`, and `zero_count_filters` still exist.

**Acceptance Scenarios**:

1. **Given** a root conftest that imports `MainDashboardPage` and `DatabaseClient`, **When** this story is done, **Then** the root module keeps browser, session, auth, video, trace, screenshot, and run-report fixtures and does not import a report page or a report SQL client.
2. **Given** fleet UI tests and `tests/e2e/` request `dashboard` and the fleet data fixtures, **When** this story is done, **Then** those fixtures are defined in `tests/ui/fleet_dashboard/conftest.py` and `tests/e2e/conftest.py` with the same names.
3. **Given** an alerts test requests `dashboard`, **When** pytest resolves fixtures, **Then** it uses `AlertsAnalysisPage` from the alerts conftest, not `MainDashboardPage`.

---

### User Story 3 - Report SQL lives under `db/clients/` (Priority: P1)

An engineer looking for warehouse queries finds a generic connection factory in `db/connection.py`, alerts SQL in `db/clients/alerts.py`, and fleet SQL in `db/clients/fleet.py`.

**Why this priority**: `DatabaseClient` in `db/client.py` is fleet SQL (vehicles, district, subunit) sitting on the package root. Alerts already has its own runner.

**Independent Test**: `from db.clients.fleet import DatabaseClient, KpiType` exposes the same public methods as today's `db.client.DatabaseClient`. `db/connection.py` still only builds an engine. `import db` does not import the fleet client.

**Acceptance Scenarios**:

1. **Given** `DatabaseClient` and `KpiType` in `db/client.py`, **When** this story is done, **Then** they live in `db/clients/fleet.py`, method signatures are unchanged, and `db/client.py` is gone.
2. **Given** `AlertsDBRunner` in `db/clients/alerts.py`, **When** this story is done, **Then** that module's SQL text and method signatures are unchanged.
3. **Given** `db/__init__.py` exports `DatabaseClient`, **When** this story is done, **Then** it does not import a report client.

---

### User Story 4 - Helpers stay generic (Priority: P2)

An engineer opening `tests/helpers/` finds the parity engine and the shared dashboard opener, and does not find fleet KPI assertions or the ArcGIS login flow.

**Why this priority**: Those two modules are report-specific, but they are not the page/fixture/SQL moves in Stories 1–3.

**Independent Test**: `tests/helpers/` contains `db_parity_engine.py` and `dashboard_fixture.py` only. `bypass_secondary_auth` imports from `pages.secondary_auth`. Fleet e2e tests import validation helpers from `tests.ui.fleet_dashboard.dashboard_validation`.

**Acceptance Scenarios**:

1. **Given** `dashboard_validation.py` under `tests/helpers/`, **When** this story is done, **Then** the module lives at `tests/ui/fleet_dashboard/dashboard_validation.py` and its function signatures are unchanged.
2. **Given** `secondary_auth.py` under `tests/helpers/`, **When** this story is done, **Then** it lives at `pages/secondary_auth.py` and the four gated report pages call `bypass_secondary_auth` from that module.
3. **Given** `validate_dashboard_generic` and `open_report` / `bind_dashboard`, **When** this story is done, **Then** they stay in `tests/helpers/` with the same signatures.

---

### User Story 5 - Report data lives under `data/<report>/` (Priority: P2)

An engineer looking for fleet filter catalogs and the alerts contract finds them under `data/fleet/` and `data/alerts/`. The parity engine still receives a path argument.

**Why this priority**: The files are domain data. Moving them does not depend on the page-class move, but the fleet fixtures in Story 2 must open the new paths.

**Independent Test**: JSON and YAML bytes are unchanged aside from path. `validate_dashboard_generic` is still called with a path. Unit tests that load the alerts contract read `data/alerts/alerts_contract.yaml`.

**Acceptance Scenarios**:

1. **Given** `data/filters.json` and `data/filter_matrix.json`, **When** this story is done, **Then** they live at `data/fleet/filters.json` and `data/fleet/filter_matrix.json`.
2. **Given** `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, **When** this story is done, **Then** it lives at `data/alerts/alerts_contract.yaml` and the parity test passes that path into the engine.
3. **Given** spreadsheets under `data/raw/`, **When** this story is done, **Then** they stay where they are.

---

### User Story 6 - Fleet-only UI stays on the fleet page (Priority: P2)

An engineer changing a fleet table, tooltip, or drilldown edits `pages/fleet_dashboard/main_dashboard_page.py`. Generic slicer, KPI, gauge, and chart readers stay in `core/components/`.

**Why this priority**: This story is the boundary that the moves must not cross. It is satisfied by not moving those methods.

**Independent Test**: `core/components/` has no diff. Fleet table, tooltip, and drilldown methods remain on `MainDashboardPage`.

**Acceptance Scenarios**:

1. **Given** table, tooltip, and drilldown methods on `MainDashboardPage`, **When** this feature is done, **Then** those methods are still defined on that class.
2. **Given** `Slicer`, `KPI`, `Chart`, and the visual reader in `core/components/`, **When** this feature is done, **Then** those modules are not edited and gain no fleet labels.

---

### User Story 7 - The constitution names the three paths (Priority: P1)

A reviewer can reject a new report page under `tests/`, a visual component outside `core/components/`, or report SQL outside `db/clients/` by citing the constitution.

**Why this priority**: Folder moves drift unless the constitution states the rule. This is a governance change, versioned with the template updates the constitution already requires.

**Independent Test**: `.specify/memory/constitution.md` is version 1.3.0 and its architecture constraints name `pages/<report>/`, `core/components/`, `db/clients/`, and `data/<report>/`. The plan, spec, and tasks templates repeat those paths.

**Acceptance Scenarios**:

1. **Given** constitution 1.2.0, **When** this story is done, **Then** the version is 1.3.0 (MINOR) and the amendment is recorded in the sync impact report.
2. **Given** the plan, spec, and tasks templates, **When** this story is done, **Then** their layer wording matches the amended constraints.
3. **Given** `README.md` and `docs/COVERAGE_CATALOG.md`, **When** this story is done, **Then** living path references point at `data/fleet/`, `data/alerts/`, `db/clients/fleet.py`, and `pages/<report>/`. Specs `001` through `017` stay as historical records.

---

### Edge Cases

- Pytest does not share fixtures between `tests/ui/fleet_dashboard/` and `tests/e2e/`. Both directories register the fleet fixtures. The root conftest does not.
- `filter_matrix` is defined in the root conftest and is not requested by a test parameter today. `tests/e2e/test_filter_matrix.py` reads the JSON through its own path. Both the fixture and that path move to `data/fleet/`.
- `open_report` lazily imports `save_auth_state` from the root conftest. That helper stays on the root module.
- Collecting the whole suite must not bind the fleet `dashboard` fixture onto an alerts test. Directory-scoped conftest fixtures already override `dashboard` per suite.
- Credit Consumption is larger than a search-term binding because it closes an info popup. That logic moves with `CreditConsumptionPage`. It is not extracted into `core/`.
- The ArcGIS flow contains organizational dialog text. It stays out of `core/`. The Layer 0 hook `_bypass_secondary_auth` stays a no-op on `ReportShell`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each page module under `tests/ui/<suite>/page.py` MUST move to `pages/<report>/page.py`. Class names MUST NOT change. Destination packages drop the `_dashboard` suffix. The suite directory name under `tests/ui/` MUST NOT change. The map is:

  | Current module | Class | Destination |
  |---|---|---|
  | `tests/ui/alerts_analysis_dashboard/page.py` | `AlertsAnalysisPage` | `pages/alerts_analysis/page.py` |
  | `tests/ui/authorities_status_dashboard/page.py` | `AuthoritiesStatusPage` | `pages/authorities_status/page.py` |
  | `tests/ui/credit_consumption_dashboard/page.py` | `CreditConsumptionPage` | `pages/credit_consumption/page.py` |
  | `tests/ui/hosen_status_dashboard/page.py` | `HosenStatusPage` | `pages/hosen_status/page.py` |
  | `tests/ui/life_saving_guidelines_dashboard/page.py` | `LifeSavingGuidelinesPage` | `pages/life_saving_guidelines/page.py` |
  | `tests/ui/marsal_dashboard/page.py` | `MarsalPage` | `pages/marsal/page.py` |
  | `tests/ui/mass_events_dashboard/page.py` | `MassEventsPage` | `pages/mass_events/page.py` |
  | `tests/ui/maya_system_dashboard/page.py` | `MayaSystemPage` | `pages/maya_system/page.py` |
  | `tests/ui/power_outages_dashboard/page.py` | `PowerOutagesPage` | `pages/power_outages/page.py` |
  | `tests/ui/public_inquiries_dashboard/page.py` | `PublicInquiriesPage` | `pages/public_inquiries/page.py` |
  | `tests/ui/public_shelters_dashboard/page.py` | `PublicSheltersPage` | `pages/public_shelters/page.py` |
  | `tests/ui/rescue_capabilities_dashboard/page.py` | `RescueCapabilitiesPage` | `pages/rescue_capabilities/page.py` |

- **FR-002**: Each suite `conftest.py` MUST import its page class from `pages.<report>.page` and MUST keep `dashboard = bind_dashboard(...)`. Smoke tests MUST stay in `tests/ui/<suite>/`.
- **FR-003**: After the move, `tests/ui/**/page.py` MUST NOT exist. `pages/fleet_dashboard/main_dashboard_page.py` MUST stay.
- **FR-004**: Root `conftest.py` MUST keep session browser, `auth_page`, video, tracing, failure screenshots, and the run-report fixtures and hooks. It MUST NOT import `MainDashboardPage`, `DatabaseClient`, or a report client, and it MUST NOT open `filters.json` or `filter_matrix.json`.
- **FR-005**: `dashboard`, `db_client`, `filter_data`, `filter_matrix`, and `zero_count_filters` MUST be defined with the same names in both `tests/ui/fleet_dashboard/conftest.py` and `tests/e2e/conftest.py`. `dashboard` MUST still call `open_report(MainDashboardPage, ...)`. `db_client` MUST return `DatabaseClient` from `db.clients.fleet`. The data fixtures MUST read `data/fleet/`.
- **FR-006**: Importing the alerts suite conftest MUST NOT load `pages.fleet_dashboard.main_dashboard_page` or `db.clients.fleet`.
- **FR-007**: `DatabaseClient` and `KpiType` MUST move from `db/client.py` to `db/clients/fleet.py` with the same public methods. `db/client.py` MUST be removed. `db/__init__.py` MUST NOT import a report client. `db/connection.py` MUST remain the generic engine factory and MUST NOT gain vehicle, district, or alerts SQL.
- **FR-008**: `db/clients/alerts.py` SQL constants and `AlertsDBRunner` method signatures MUST NOT change.
- **FR-009**: `tests/helpers/db_parity_engine.py` and `tests/helpers/dashboard_fixture.py` MUST stay. `validate_dashboard_generic`, `open_report`, and `bind_dashboard` signatures MUST NOT change.
- **FR-010**: `tests/helpers/dashboard_validation.py` MUST move to `tests/ui/fleet_dashboard/dashboard_validation.py`. Callers in `tests/e2e/` and `tests/ui/fleet_dashboard/test_dashboard_smoke.py` MUST update imports. Function signatures MUST NOT change.
- **FR-011**: `tests/helpers/secondary_auth.py` MUST move to `pages/secondary_auth.py`. `bypass_secondary_auth` MUST keep its signature. `MassEventsPage`, `LifeSavingGuidelinesPage`, `MayaSystemPage`, and `PublicSheltersPage` MUST import it from `pages.secondary_auth`. The module MUST NOT move into `core/`.
- **FR-012**: `data/filters.json` MUST move to `data/fleet/filters.json`. `data/filter_matrix.json` MUST move to `data/fleet/filter_matrix.json`. File contents MUST be unchanged. `tests/e2e/test_filter_matrix.py` MUST read the new matrix path.
- **FR-013**: `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` MUST move to `data/alerts/alerts_contract.yaml` with contents unchanged. `test_db_parity.py` and `tests/unit/test_db_parity_engine.py` MUST load that path and still pass it into `validate_dashboard_generic`.
- **FR-014**: Files under `data/raw/` MUST stay.
- **FR-015**: Table, tooltip, and drilldown methods on `MainDashboardPage` MUST stay in `pages/fleet_dashboard/main_dashboard_page.py`. `core/components/` MUST NOT be edited. No fleet label, locator, or SQL MAY be added to `core/`.
- **FR-016**: `.specify/memory/constitution.md` MUST be amended from 1.2.0 to 1.3.0 (MINOR). It MUST require report pages in `pages/<report>/`, generic visual components in `core/components/`, and report SQL in `db/clients/<report>.py`. The same change MUST update `.specify/templates/plan-template.md`, `.specify/templates/spec-template.md`, `.specify/templates/tasks-template.md`, `README.md`, and the living paths in `docs/COVERAGE_CATALOG.md`. Specs `001`–`017` MUST NOT be rewritten.
- **FR-017**: Moved Python MUST keep English comments. Navigation behavior, SQL text, JSON, YAML, and assertion logic MUST NOT change except for import paths and file paths.

### Key Entities

- **Report page**: A `ReportShell` subclass in `pages/<report>/page.py`. Tests in `tests/ui/<suite>/` bind it with `bind_dashboard`.
- **Fleet fixture set**: `dashboard`, `db_client`, `filter_data`, `filter_matrix`, `zero_count_filters`. Owned by the fleet UI conftest and the e2e conftest, not the root.
- **Report SQL client**: A read-only runner in `db/clients/<report>.py`. Fleet keeps the class name `DatabaseClient`. Alerts keeps `AlertsDBRunner`. Both use `db.connection.create_db_engine`.
- **Report data catalog**: Domain files under `data/<report>/`. The parity engine receives the path; it does not choose the report.
- **Shared secondary auth**: `pages/secondary_auth.py`, called from a page's `_bypass_secondary_auth` override.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. This feature MUST NOT add vehicles, district, fleet titles, ArcGIS dialog text, or alerts labels to `core/`. The generic last-refresh caption stays in Layer 0 and stays a text or regex lookup inside the report iframe.
- **AC-002**: Every moved page MUST still inherit `ReportShell` and MUST NOT re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: Report-ready locators stay on the domain page. `ReportShell` MUST NOT gain a fleet or alerts ready locator.
- **AC-004**: Public page methods and `DatabaseClient` methods MUST keep their contracts. Tests change import paths in the same change. Fixture names used by fleet UI and e2e tests MUST stay.
- **AC-005**: `core/components/` MUST stay report-agnostic. This feature MUST NOT edit it. `core/` MUST NOT load `data/fleet/` or `data/alerts/`.
- **AC-006**: Report pages MUST live in `pages/<report>/`. Report SQL MUST live in `db/clients/<report>.py`. Generic visual readers MUST stay in `core/components/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `Get-ChildItem -Recurse tests/ui -Filter page.py` returns no files. Each class in FR-001 imports from `pages.<report>.page`.
- **SC-002**: A search of root `conftest.py` finds no `MainDashboardPage`, `DatabaseClient`, `db.client`, or `db.clients.fleet`.
- **SC-003**: Importing `tests.ui.alerts_analysis_dashboard.conftest` leaves `pages.fleet_dashboard.main_dashboard_page` and `db.clients.fleet` out of `sys.modules`.
- **SC-004**: `python -m pytest tests/unit/test_db_parity_engine.py tests/ui/alerts_analysis_dashboard tests/ui/fleet_dashboard tests/e2e --collect-only -q` succeeds.
- **SC-005**: `pytest tests/ui/fleet_dashboard/` passes at 100% (Constitution III). This feature moves page modules and fixture registration; the fleet smoke suite is the navigation-surface gate.
- **SC-006**: Constitution version is 1.3.0 and names `pages/<report>/`, `core/components/`, and `db/clients/`.

## Assumptions

- "Thin reports" includes every page module under `tests/ui/`, including Credit Consumption's popup dismissal. That behavior stays on the page object.
- Page packages drop `_dashboard`. Test directories keep it, so existing pytest paths stay stable.
- The fleet page is already in the right tree. This feature does not rename `pages/fleet_dashboard/main_dashboard_page.py` to `pages/fleet/`.
- `DatabaseClient` keeps its class name so e2e type hints and call sites change only their import module.
- Fleet fixtures are duplicated as short wrappers in the two conftest files. They are not registered from the root and they are not placed in `tests/helpers/`.
- Historical feature specs record the layout at the time they were written. Living docs (`README.md`, `docs/COVERAGE_CATALOG.md`, the constitution, and the three templates) are the documents that change.
- No new third-party package is required.
