<!--
Sync Impact Report
- Version change: (unratified template) → 1.0.0
- Modified principles:
  - [PRINCIPLE_1_NAME] → I. Layered Portal Architecture
  - [PRINCIPLE_2_NAME] → II. Zero Domain Leakage
  - [PRINCIPLE_3_NAME] → III. Existing Tests Are the Contract
  - [PRINCIPLE_4_NAME] → IV. Page Object Discipline
  - [PRINCIPLE_5_NAME] → V. Warehouse as Source of Truth
  - (expanded from single catch-all) → VI. Observability of Validation Runs
  - (expanded from single catch-all) → VII. Extract Shared Behavior Only
- Added sections:
  - Architecture Constraints
  - Quality Gates
  - Governance (ratified)
- Removed sections: none (template placeholders replaced)
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check gates)
  - ✅ .specify/templates/spec-template.md (Architectural Constraints)
  - ✅ .specify/templates/tasks-template.md (Layer 0 + mandatory smoke gate)
  - ✅ README.md (layered architecture pointer)
  - ⚠ .specify/templates/commands/*.md — directory does not exist; skipped
- Follow-up TODOs: none. Feature implementation of ReportShell is out of
  scope for this ratification (specify → plan → tasks next).
-->

# Validation Core Constitution

## Core Principles

### I. Layered Portal Architecture
Shared Power BI portal behavior MUST live in Layer 0 (`core/portal`).
`ReportShell` in `core/portal/page.py` is the generic host for login/SSO,
catalog search, iframe waiting, and visual-loading timeouts. Domain report
pages (today: `MainDashboardPage` in `pages/fleet_dashboard/`) MUST inherit
from or compose `ReportShell` instead of re-implementing those steps.
A new report MUST reuse Layer 0 rather than copy portal navigation.

Rationale: `MainDashboardPage` currently mixes generic portal chrome with
fleet-specific KPIs, slicers, and charts. Without a hard layer boundary,
every new report will fork SSO and iframe logic.

### II. Zero Domain Leakage (NON-NEGOTIABLE)
`ReportShell` and every module under `core/` MUST remain report-agnostic.
Layer 0 MUST NOT contain dashboard-specific terms, locators, or flows,
including vehicles, district, subunit, fleet KPI titles, chart titles,
slicer display names, or other labels unique to one report.
Configuration values (portal URL, catalog URL, search term, timeouts)
MAY be read from settings. Report-ready state MUST be supplied by the
domain page via a locator, predicate, or override — never hardcoded to a
fleet visual such as `total_vehicles_kpi`.

Rationale: Domain strings in the shell make Layer 0 unusable for the next
Power BI report and hide coupling that refactors cannot see.

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
catalog search, iframe wait, or visual-load timeout.

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
Abstractions MUST earn their place. Layer 0 MUST extract only login/SSO,
catalog search, iframe waiting, and visual-loading timeouts. Fleet
filters, KPI cards, tabs, tables, charts, tooltips, and drilldown MUST
stay on the domain page until a second report requires the same behavior.
Do not invent unused generic APIs.

Rationale: Premature generalization of fleet UX recreates the monolith
under a new name.

## Architecture Constraints

- Layer 0 path is `core/portal/page.py` (`ReportShell`).
- Domain path remains `pages/<report>/` (fleet today: `pages/fleet_dashboard/`).
- Inheritance or composition of `ReportShell` is required; copy-paste of
  portal steps is forbidden after Layer 0 exists.
- `BasePage` remains the Playwright timeout/retry foundation; `ReportShell`
  extends or uses it, and domain pages sit above the shell.
- Settings-driven URLs and search terms are configuration, not domain logic.
- The warehouse client (`db/`) stays read-only and independent of Layer 0.

## Quality Gates

- Every implementation plan MUST include a Constitution Check against these
  principles before research and again after design.
- Layer 0 or navigation refactors MUST include a task to run
  `pytest` on `tests/ui/fleet_dashboard/` and MUST NOT be declared done
  unless that suite is 100% green.
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
beyond "extract shared portal steps" MUST be justified in the plan's
Complexity Tracking table. Runtime guidance lives in `README.md` and
`docs/COVERAGE_CATALOG.md`.

**Version**: 1.0.0 | **Ratified**: 2026-08-23 | **Last Amended**: 2026-08-23
