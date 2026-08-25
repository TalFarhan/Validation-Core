<!--
Sync Impact Report
- Version change: 1.1.0 → 1.2.0 (MINOR)
- Modified principles:
  - I. Layered Portal Architecture — Layer 0 last-refresh verification
  - II. Zero Domain Leakage — last-refresh caption is generic chrome
  - VII. Extract Shared Behavior Only — authorize last-refresh chrome on Layer 0
- Added sections: none
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Layer 0 last-refresh in gates)
  - ✅ .specify/templates/spec-template.md (last-refresh AC)
  - ✅ .specify/templates/tasks-template.md (Layer 0 freshness in scope)
  - ✅ README.md (Layer 0 table)
- Follow-up TODOs: none. Method + smoke test live in
  specs/003-dashboard-freshness/tasks.md.
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

Rationale: The product under test is a Power BI report over a warehouse.
Portal chrome is not a source of business truth.

### VI. Observability of Validation Runs
Every test run MUST continue to emit HTML, Hebrew CSV, and Allure
artifacts under `test-results/`. Navigation and authentication paths
SHOULD keep Allure steps and CSV UI log lines. Failures MUST retain
screenshot and Playwright trace attachments. Layer 0 extraction MUST NOT
drop existing run evidence.

Rationale: BI and Validation teams use the CSV and Allure report as the
audit trail, not pytest stdout.

### VII. Extract Shared Behavior Only
Abstractions MUST earn their place.

Layer 0 (`core/portal`) MUST extract only login/SSO, catalog search, iframe
waiting, visual-loading timeouts, and generic last-refresh verification.

Layer 2 (`core/components/`) MAY extract Power BI slicer interaction
(dropdown, checkbox, search, clear-all) when it is report-agnostic. Domain
filter *names*, value catalogs, and scenario matrices remain on the domain
page and in `data/`. `core/` MUST NOT load those files.

KPI cards, tabs, tables, charts, tooltips, and drilldown MUST stay on the
domain page until a second report requires the same behavior.

Do not invent unused generic APIs beyond the slicer kinds and last-refresh
verification authorized here.

Rationale: Premature generalization of fleet UX recreates the monolith
under a new name. Slicer chrome is shared Power BI behavior; fleet labels
are not.

## Architecture Constraints

- Layer 0 path is `core/portal/page.py` (`ReportShell`).
- Layer 2 path is `core/components/slicer.py` (`Slicer`). Domain pages compose
  it; they MUST NOT put fleet labels inside `core/`.
- Layer 3 data stays in `data/` (`filters.json`, `filter_matrix.json`) plus
  domain mapping. `core/` MUST NOT parse those files.
- Domain path remains `pages/<report>/` (fleet today: `pages/fleet_dashboard/`).
- Inheritance or composition of `ReportShell` is required; copy-paste of
  portal steps is forbidden after Layer 0 exists.
- `Slicer` is a collaborator, not a base class. Inheritance chain stays
  `BasePage` → `ReportShell` → domain page.
- `BasePage` remains the Playwright timeout/retry foundation; `ReportShell`
  extends or uses it, and domain pages sit above the shell.
- Settings-driven URLs and search terms are configuration, not domain logic.
- The warehouse client (`db/`) stays read-only and independent of Layer 0
  and Layer 2.

## Quality Gates

- Every implementation plan MUST include a Constitution Check against these
  principles before research and again after design.
- Layer 0, Layer 2, or navigation/filter-surface refactors MUST include a
  task to run `pytest` on `tests/ui/fleet_dashboard/` and MUST NOT be
  declared done unless that suite is 100% green.
- Reviews MUST reject `core/` changes that introduce report-specific
  locators, labels, or SQL.
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

**Version**: 1.2.0 | **Ratified**: 2026-08-23 | **Last Amended**: 2026-08-25
