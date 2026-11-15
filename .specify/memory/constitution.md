<!--
Sync Impact Report
- Version change: 1.2.0 → 1.3.0 (MINOR)
- Modified principles:
  - I. Layered Portal Architecture — report pages live in pages/<report>/
  - II. Zero Domain Leakage — root conftest must not import a report
  - V. Warehouse as Source of Truth — report SQL lives in db/clients/
  - VII. Extract Shared Behavior Only — generic visual readers vs fleet-only UI
- Added sections: none
- Templates requiring updates:
    - ✅ .specify/templates/plan-template.md (visual-reader gate and path tree)
    - ✅ .specify/templates/spec-template.md (AC-005 data/<report>/, AC-006 paths)
    - ✅ .specify/templates/tasks-template.md (db/clients and data/<report>/)
    - ✅ README.md (layer table)
    - ✅ docs/COVERAGE_CATALOG.md (living paths)
- Follow-up TODOs: none. Folder moves live in
  specs/018-architecture-normalization/tasks.md.
-->

# Validation Core Constitution

## Core Principles

### I. Layered Portal Architecture
Shared Power BI portal behavior MUST live in Layer 0 (`core/portal`).
`ReportShell` in `core/portal/page.py` is the generic host for login/SSO,
catalog search, iframe waiting, visual-loading timeouts, and last-refresh
verification. Domain report pages (today: `MainDashboardPage` in
`pages/fleet_dashboard/`) MUST inherit from or compose `ReportShell`
instead of re-implementing those steps.
A new report MUST reuse Layer 0 rather than copy portal navigation.
Every report page MUST live in `pages/<report>/`. A report page MUST NOT be
defined under `tests/`. Test modules import the page object. The fleet page
object remains `pages/fleet_dashboard/main_dashboard_page.py`.

Shared Power BI slicer *interaction* (dropdown, checkbox, search, clear-all)
MAY live in Layer 2 (`core/components/`). Domain pages MUST compose `Slicer`
and supply definitions plus a settle hook; they MUST NOT copy click-and-retry
logic into a second report.

Rationale: `MainDashboardPage` mixed generic portal chrome with fleet-specific
KPIs, slicers, and charts. Without a hard layer boundary, every new report
forks SSO, iframe, and slicer-chrome logic.

### II. Zero Domain Leakage (NON-NEGOTIABLE)
`ReportShell`, `Slicer`, and every module under `core/` MUST remain
report-agnostic. `core/` MUST NOT contain dashboard-specific terms, locators,
or flows, including vehicles, district, subunit, fleet KPI titles, chart
titles, slicer display names, or other labels unique to one report.
Configuration values (portal URL, catalog URL, search term, timeouts)
MAY be read from settings. Generic Power BI chrome phrases (clear all
slicers, Search placeholders) MAY live in Layer 2. The standard last-refresh
caption (`הדשבורד עודכן לאחרונה ב:`) MAY live in Layer 0 as generic chrome
and MUST be located by text or regex inside the report iframe — never by
report-specific CSS or visual ids. Report-ready state and
post-select settle MUST be supplied by the domain page via a locator,
predicate, or hook — never hardcoded to a fleet visual such as
`total_vehicles_kpi`.
The root test `conftest.py` MUST NOT import a report page or a report SQL
client. Collecting one report MUST NOT load another report's page module or
warehouse client.

Rationale: Domain strings in `core/` make Layer 0 and Layer 2 unusable for
the next Power BI report and hide coupling that refactors cannot see.

### III. Existing Tests Are the Contract (NON-NEGOTIABLE)
After any change to Layer 0 or to a domain page object's navigation
surface, `pytest` on the fleet smoke suite (`tests/ui/fleet_dashboard/`)
MUST pass at 100%. Public test-facing APIs (`navigate`,
`reload_and_measure_ready_ms`, the `dashboard` fixture, KPI/filter/chart
methods) MUST keep their contracts unless tests are updated in the same
change. A refactor that "looks equivalent" but breaks smoke is rejected.

Rationale: The suite is the executable specification of portal load, SLA,
and dashboard visibility. Extraction without that gate is incomplete.

### IV. Page Object Discipline
UI tests MUST drive the browser through page objects, not ad-hoc locators
in test bodies (shared helpers MAY wrap page-object calls). Playwright
locators for a report MUST live in that report's page object. Shared
session and timeout utilities stay in `browser_session` and `BasePage`.
Once `ReportShell` exists, a domain page MUST NOT re-implement login,
catalog search, iframe wait, visual-load timeout, or last-refresh
verification.

Rationale: Locators and wait policy belong in one place so tests stay
stable when Power BI chrome changes.

### V. Warehouse as Source of Truth
End-to-end assertions MUST compare UI values to the SQL Server warehouse
through the read-only `db` client. `docs/COVERAGE_CATALOG.md` is the
mapping of KPI ↔ SQL ↔ tests and MUST be updated when a measure, slicer,
or query changes. Layer 0 MUST NOT embed business SQL or fleet invariants.
Report-specific SQL MUST live in `db/clients/<report>.py` and MUST stay
read-only. `db/connection.py` MUST remain a generic engine factory.
The `db` package root MUST NOT export a report client. `core/` MUST NOT
import `db.clients`.

Rationale: The product under test is a Power BI report over a warehouse.
Portal chrome is not a source of business truth.

### VI. Observability of Validation Runs
Every test run MUST continue to emit HTML and Hebrew CSV
artifacts under `result/`. Navigation and authentication paths
SHOULD keep CSV UI log lines. Failures MUST retain
screenshot and Playwright trace attachments. Layer 0 extraction MUST NOT
drop existing run evidence.

Rationale: BI and Validation teams use the CSV and ReportPortal as the
audit trail, not pytest stdout.

### VII. Extract Shared Behavior Only
Abstractions MUST earn their place.

Layer 0 (`core/portal`) MUST extract only login/SSO, catalog search, iframe
waiting, visual-loading timeouts, and generic last-refresh verification.

Generic Power BI visual readers MAY live in Layer 2 (`core/components/`):
slicer chrome, KPI value and scale reads, gauge scale, and chart category
reads. Those modules MUST stay report-agnostic.

Report-specific tables, tooltips, drilldowns, tabs, filter names, and value
catalogs MUST stay on the domain page and under `data/<report>/`. Fleet
tables, tooltips, and drilldowns MUST stay in
`pages/fleet_dashboard/main_dashboard_page.py`.

`tests/helpers/` MUST contain only generic engines (the parity engine and the
dashboard opener). Fleet validation helpers MUST live with the fleet suite,
not in `tests/helpers/`.

Shared ArcGIS secondary login used by more than one report MUST live in
`pages/secondary_auth.py`. It MUST NOT move into `core/`. Layer 0 keeps the
`_bypass_secondary_auth` hook as a no-op.

Do not invent unused generic APIs beyond the visual readers and last-refresh
verification already authorized.

Rationale: Premature generalization of fleet UX recreates the monolith
under a new name. Slicer chrome is shared Power BI behavior; fleet labels
are not.

## Architecture Constraints

- Layer 0 path is `core/portal/page.py` (`ReportShell`).
- Layer 2 path is `core/components/` (`Slicer`, `KPI`, `Chart`, and the visual
  reader). Domain pages compose them. They MUST NOT put report labels inside
  `core/`.
- Domain pages live in `pages/<report>/`. The fleet page object is
  `pages/fleet_dashboard/main_dashboard_page.py`.
- Layer 3 catalogs live in `data/<report>/`. Fleet catalogs are
  `data/fleet/filters.json` and `data/fleet/filter_matrix.json`. The alerts
  contract is `data/alerts/alerts_contract.yaml`. `core/` MUST NOT parse those
  files.
- Inheritance or composition of `ReportShell` is required; copy-paste of
  portal steps is forbidden after Layer 0 exists.
- `Slicer` is a collaborator, not a base class. Inheritance chain stays
  `BasePage` → `ReportShell` → domain page.
- `BasePage` remains the Playwright timeout/retry foundation; `ReportShell`
  extends or uses it, and domain pages sit above the shell.
- Settings-driven URLs and search terms are configuration, not domain logic.
- `db/connection.py` is the generic engine factory. Report SQL lives in
  `db/clients/<report>.py` and stays read-only and independent of Layer 0 and
  Layer 2.
- Root `conftest.py` owns browser, session, auth, and run-report fixtures.
  Fleet dashboard and fleet database fixtures live in
  `tests/ui/fleet_dashboard/conftest.py` and `tests/e2e/conftest.py`.

## Quality Gates

- Every implementation plan MUST include a Constitution Check against these
  principles before research and again after design.
- Layer 0, Layer 2, or navigation/filter-surface refactors MUST include a
  task to run `pytest` on `tests/ui/fleet_dashboard/` and MUST NOT be
  declared done unless that suite is 100% green.
- Reviews MUST reject `core/` changes that introduce report-specific
  locators, labels, or SQL.
- Reviews MUST reject a new report page under `tests/`, report SQL outside
  `db/clients/`, a domain label or domain file load inside `core/components/`,
  and a fleet import in the root `conftest.py`.
- Coverage catalog and Allure labels MUST stay consistent with page-object
  and query changes.

## Governance

This constitution supersedes informal practice and ad-hoc page-object
growth. Amendments MUST be written into this file, versioned, and
propagated to `.specify/templates/` (plan, spec, tasks) in the same change.
Versioning:

- MAJOR: remove or redefine a principle, or break Layer 0 / test-contract rules.
- MINOR: add a principle or materially expand a section.
- PATCH: clarification, wording, or non-semantic fix.

Compliance review: pull requests and `/speckit-plan` Constitution Checks
MUST verify layering, zero leakage, and the smoke-test contract. Complexity
beyond Layer 0 portal steps (including last-refresh verification) or
Layer 2 slicer chrome MUST be justified in
the plan's Complexity Tracking table. Runtime guidance lives in `README.md`
and `docs/COVERAGE_CATALOG.md`.

**Version**: 1.3.0 | **Ratified**: 2026-08-23 | **Last Amended**: 2026-10-14
