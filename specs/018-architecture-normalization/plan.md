# Implementation Plan: Architecture Normalization

**Branch**: `feature/reportportal-integration` (spec directory `018-architecture-normalization`) | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/018-architecture-normalization/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration`). Feature 017 stays the alerts contract slice. This
feature only moves modules and amends the constitution so the three-layer paths are mandatory.

## Summary

Report pages grew under `tests/ui/`, the root `conftest.py` imports the fleet
page for every suite, and fleet SQL still sits in `db/client.py` while alerts
SQL already lives in `db/clients/alerts.py`.

This feature relocates those modules and records the rule:

- Twelve report page classes move to `pages/<report>/page.py`. Tests, smoke
  modules, and suite conftests stay. They import the page.
- Fleet fixtures (`dashboard`, `db_client`, `filter_data`, `filter_matrix`,
  `zero_count_filters`) move to `tests/ui/fleet_dashboard/conftest.py` and
  `tests/e2e/conftest.py`. The root conftest keeps browser, session, and
  run-report fixtures.
- `DatabaseClient` moves to `db/clients/fleet.py`. `db/connection.py` stays generic.
- `dashboard_validation.py` moves beside the fleet suite. `secondary_auth.py`
  moves to `pages/secondary_auth.py`. The parity engine and `bind_dashboard`
  stay in `tests/helpers/`.
- Fleet JSON moves to `data/fleet/`. The alerts contract moves to `data/alerts/`.
  The engine still receives a path.
- Fleet tables, tooltips, and drilldowns stay on `MainDashboardPage`.
  `core/components/` is not edited.
- Constitution 1.2.0 becomes 1.3.0 and names `pages/<report>/`,
  `core/components/`, and `db/clients/`.

No SQL text, JSON, YAML, locator, or assertion logic changes.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: pytest, Playwright, SQLAlchemy (already used by
`db/connection.py` and both report clients). No new package.

**Storage**: Read-only SQL Server. No schema change. Fleet catalogs move to
`data/fleet/`. The alerts contract moves to `data/alerts/`. `data/raw/` stays.

**Testing**: `pytest`. Structural gates are import checks and `--collect-only`
(quickstart steps 1–4) plus `tests/unit/test_db_parity_engine.py` (no browser).
Constitution III: `pytest tests/ui/fleet_dashboard/` stays 100% green. Public
method names and fixture names stay; import paths change in the same change.

**Target Platform**: Windows workstation. Chromium against the organizational
Agamim Power BI portal is required only for the fleet smoke gate.

**Project Type**: Internal validation framework. Domain pages under
`pages/<report>/`. Report SQL under `db/clients/`. Suites under `tests/ui/<suite>/`.

**Performance Goals**: N/A. This is a move. Collection of alerts must not import
the fleet page.

**Constraints**:

- `core/portal/` and `core/components/` MUST NOT change (FR-015, AC-001, AC-005).
- `pages/fleet_dashboard/main_dashboard_page.py` MUST NOT lose table, tooltip,
  or drilldown methods (FR-015).
- `DatabaseClient` and `KpiType` keep their names and method signatures (FR-007, AC-004).
- `validate_dashboard_generic`, `open_report`, and `bind_dashboard` keep their signatures (FR-009).
- `db/clients/alerts.py` SQL text stays (FR-008). JSON and YAML bytes stay (FR-012, FR-013).
- Root `conftest.py` MUST NOT import a report page or a report client (FR-004, FR-006).
- ArcGIS login MUST NOT move into `core/` (FR-011, research R5).
- Specs `001`–`017` stay historical (FR-016).
- Inline comments stay English (FR-017).

**Scale/Scope**: Twelve page modules, two new conftest files, one SQL module
move, two helper moves, three data-file moves, constitution 1.3.0 plus three
templates, `README.md`, and `docs/COVERAGE_CATALOG.md`.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/<report>/page.py` (12 modules) | NEW (moved) | Report pages leave `tests/ui/` |
| `tests/ui/<suite>/page.py` | DELETE | Suite folders keep tests and conftests |
| `tests/ui/<suite>/conftest.py` | EDIT | Import the page from `pages/` |
| `conftest.py` | EDIT | Drop fleet page, fleet client, and fleet JSON fixtures |
| `tests/ui/fleet_dashboard/conftest.py` | NEW | Fleet `dashboard` and database fixtures |
| `tests/e2e/conftest.py` | NEW | Same fleet fixtures for e2e |
| `db/clients/fleet.py` | NEW (moved) | `DatabaseClient` and `KpiType` |
| `db/client.py` | DELETE | Fleet SQL leaves the package root |
| `db/__init__.py` | EDIT | Stop exporting a report client |
| `tests/ui/fleet_dashboard/dashboard_validation.py` | NEW (moved) | Fleet assertions leave `tests/helpers/` |
| `pages/secondary_auth.py` | NEW (moved) | Shared ArcGIS login leaves `tests/helpers/` |
| `data/fleet/filters.json`, `data/fleet/filter_matrix.json` | NEW (moved) | Fleet catalogs |
| `data/alerts/alerts_contract.yaml` | NEW (moved) | Alerts contract; engine still takes a path |
| `.specify/memory/constitution.md` | EDIT | 1.3.0 path rules |
| `.specify/templates/{plan,spec,tasks}-template.md` | EDIT | Same path rules |
| `README.md`, `docs/COVERAGE_CATALOG.md` | EDIT | Living paths |
| `core/`, `db/connection.py`, `db/clients/alerts.py`, `tests/helpers/db_parity_engine.py` | NONE | Boundaries |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. Moved pages still inherit `ReportShell`. Portal
  login, catalog search, iframe wait, and last-refresh stay in Layer 0. ArcGIS
  login stays outside `core/` (research R5). The amendment adds the
  `pages/<report>/` rule; it does not add portal behavior.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `core/` is not edited.
  Removing the fleet import from root `conftest.py` stops every suite from
  loading `MainDashboardPage`. `db/__init__.py` stops exporting the fleet client.
  Hebrew catalog strings move with the page modules and the YAML file.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Fixture names
  and `DatabaseClient` / `MainDashboardPage` methods stay. Call sites update
  imports in the same change. Fleet smoke remains the completion gate
  (quickstart step 5).
- **Page object discipline (IV)**: PASS. Locators stay on the page object.
  Tests still drive the browser through `dashboard`. No new locators in test bodies.
- **Warehouse as source of truth (V)**: PASS. Queries stay read-only and move
  with `DatabaseClient` into `db/clients/fleet.py`. `db/connection.py` gains no
  business SQL. The coverage catalog updates its paths. Layer 0 still has no SQL.
- **Observability (VI)**: PASS. Run-report, screenshot, trace, and video fixtures
  stay on the root conftest. No logging path changes.
- **Extract shared behavior only (VII)**: PASS. This feature does not add a
  generic API and does not move fleet tables, tooltips, or drilldowns.
  Generic KPI, gauge, and chart readers already in `core/components/` stay.
  The 1.3.0 amendment records that split so VII no longer contradicts
  features 012–015, and it still forbids pulling fleet-only UI into `core/`.

**Result**: No violations. Complexity Tracking has no rows. The constitution
edit is an authorized MINOR amendment (research R8), specified in
`contracts/constitution-amendment.md`, not a gate exception.

## Project Structure

### Documentation (this feature)

```text
specs/018-architecture-normalization/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── module-layout.md
    └── constitution-amendment.md
```

### Source Code (repository root)

```text
pages/
├── fleet_dashboard/main_dashboard_page.py   # unchanged; tables, tooltips, drilldowns
├── secondary_auth.py                        # moved from tests/helpers/
├── alerts_analysis/page.py
├── power_outages/page.py
├── maya_system/page.py
└── <report>/page.py                         # the other nine classes in FR-001

core/portal/                                 # unchanged Layer 0
core/components/                             # unchanged Layer 2 readers

db/
├── connection.py                            # generic engine factory
└── clients/
    ├── alerts.py                            # unchanged
    └── fleet.py                             # DatabaseClient, KpiType

data/
├── fleet/filters.json
├── fleet/filter_matrix.json
├── alerts/alerts_contract.yaml
└── raw/                                     # unchanged

tests/
├── helpers/
│   ├── db_parity_engine.py                  # stays; path is an argument
│   └── dashboard_fixture.py                 # stays; open_report, bind_dashboard
├── ui/<suite>/                              # smoke, conftest; no page.py
│   └── fleet_dashboard/
│       ├── conftest.py                      # fleet fixtures
│       └── dashboard_validation.py
└── e2e/conftest.py                          # the same fleet fixtures
```

**Structure Decision**: Three legal homes, matching the user steps and the
1.3.0 amendment. Report pages live in `pages/<report>/`. Generic visual readers
live in `core/components/`. Report SQL lives in `db/clients/<report>.py`.
Test packages keep execution only. The root conftest keeps session mechanics.
Fleet data and fleet fixtures stay on the fleet side of that line so alerts
collection does not import them.

## Complexity Tracking

No constitution violations. Table left empty.

## Constitution Check (Post-Design)

Re-evaluated after Phase 0 and Phase 1. Still PASS on I–VII:

- Design adds no file under `core/` and no edit to `db/connection.py`,
  `db/clients/alerts.py`, or `tests/helpers/db_parity_engine.py`.
- Page classes keep their names and their `ReportShell` inheritance. Credit
  Consumption's popup logic moves with the page and is not generalized.
- Fleet fixtures are duplicated in two directory conftests because pytest does
  not share sibling conftests. They are not loaded through the root module
  (research R2).
- `DatabaseClient` keeps its class name inside `db/clients/fleet.py`. There is
  no compatibility re-export (research R3).
- ArcGIS dialog text stays in `pages/secondary_auth.py` (research R5).
- Catalog bytes move; the engine signature does not (research R6).
- Principle VII's amendment describes readers that already exist and keeps
  fleet tables, tooltips, and drilldowns on `MainDashboardPage` (research R7).
- Unresolved `NEEDS CLARIFICATION` markers: none.
- Specs 001–017 are not part of the edit set. Living docs are.
