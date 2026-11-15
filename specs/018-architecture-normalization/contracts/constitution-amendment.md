# Contract: Constitution Amendment 1.3.0

Apply this amendment in the same change as the folder moves. Governance requires
the version bump and the template updates together. Do not rewrite specs 001–017.
Do not edit `.specify/templates/constitution-template.md` (it is an empty
placeholder, not a copy of these principles).

## Version

- File: `.specify/memory/constitution.md`
- Change: 1.2.0 → 1.3.0 (MINOR)
- Ratified: 2026-08-23 (unchanged)
- Last Amended: 2026-10-14

Sync impact report at the top of the file:

- Version change: 1.2.0 → 1.3.0 (MINOR)
- Modified principles: I (page path), II (root conftest), V (`db/clients/`), VII (generic readers versus fleet UI)
- Added sections: none
- Templates requiring updates: plan, spec, tasks (this change)
- README layer table and `docs/COVERAGE_CATALOG.md` paths (this change)
- Follow-up TODOs: none

MINOR because the amendment adds mandatory paths and corrects Principle VII
so it matches `core/components/{kpi,chart,visual}.py`. It does not remove a
principle and it does not weaken the fleet smoke gate.

## Principle I — add this paragraph after the domain-page sentence

Every report page MUST live in `pages/<report>/`. A report page MUST NOT be
defined under `tests/`. Test modules import the page object. The fleet page
object remains `pages/fleet_dashboard/main_dashboard_page.py`.

## Principle II — add this paragraph

The root test `conftest.py` MUST NOT import a report page or a report SQL
client. Collecting one report MUST NOT load another report's page module or
warehouse client.

## Principle V — add this paragraph

Report-specific SQL MUST live in `db/clients/<report>.py` and MUST stay
read-only. `db/connection.py` MUST remain a generic engine factory.
The `db` package root MUST NOT export a report client. `core/` MUST NOT
import `db.clients`.

## Principle VII — replace the KPI/chart paragraphs

Replace the sentences that require KPI cards, tabs, tables, charts, tooltips,
and drilldown to stay on the domain page, and the sentence that forbids
generic APIs beyond slicer kinds, with:

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

## Architecture Constraints — replace the path bullets

Use these bullets. Keep the inheritance bullet (`BasePage` → `ReportShell` →
domain page) and the settings bullet.

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
- `db/connection.py` is the generic engine factory. Report SQL lives in
  `db/clients/<report>.py` and stays read-only and independent of Layer 0 and
  Layer 2.
- Root `conftest.py` owns browser, session, auth, and run-report fixtures.
  Fleet dashboard and fleet database fixtures live in
  `tests/ui/fleet_dashboard/conftest.py` and `tests/e2e/conftest.py`.

## Quality Gates — add

Reviews MUST reject a new report page under `tests/`, report SQL outside
`db/clients/`, a domain label or domain file load inside `core/components/`,
and a fleet import in the root `conftest.py`.

The existing fleet-smoke gate stays: a Layer 0, Layer 2, or page-object
navigation change is not done unless `pytest tests/ui/fleet_dashboard/` is
100% green.

## Template propagation

### `.specify/templates/plan-template.md`

In the Constitution Check, replace the "Do not genericize KPI cards, tabs,
charts, tables, or drilldown" bullet with the Principle VII split: generic
readers MAY live in `core/components/`; report tables, tooltips, and
drilldowns stay on the domain page.

In the Validation Core tree comment, name:

- `core/components/` as Layer 2 visual readers (slicer, KPI, chart, gauge)
- `pages/<report>/` as domain pages
- `data/<report>/` as Layer 3
- `db/connection.py` as the generic factory and `db/clients/<report>.py` as report SQL

### `.specify/templates/spec-template.md`

Extend **AC-005** so `core/` MUST NOT load `data/<report>/` (not only
`data/filters.json`).

Add **AC-006**: report pages MUST live in `pages/<report>/`, and report SQL
MUST live in `db/clients/<report>.py`.

### `.specify/templates/tasks-template.md`

Replace the Validation Core path convention with:

`core/portal/` (Layer 0), `core/components/` (Layer 2 visual readers),
`pages/<report>/` (domain pages), `data/<report>/` (Layer 3),
`tests/ui/<suite>/` (smoke), `tests/e2e/`, `db/connection.py` (generic),
`db/clients/<report>.py` (report SQL).

## Living docs

### `README.md`

Update the project tree and the Hebrew layer table:

| Layer | Path | What belongs there |
|---|---|---|
| Layer 0 | `core/portal/` | SSO, catalog, iframe, timeouts, last-refresh |
| Layer 1 / Domain | `pages/<report>/` | Report page objects. Fleet: `pages/fleet_dashboard/` |
| Layer 2 | `core/components/` | Generic slicer, KPI, gauge, and chart readers |
| Layer 3 | `data/<report>/` | `data/fleet/filters.json`, `data/fleet/filter_matrix.json`, `data/alerts/alerts_contract.yaml` |
| Warehouse | `db/connection.py`, `db/clients/<report>.py` | Generic engine; report SQL stays read-only |
| Helpers | `tests/helpers/` | Parity engine and dashboard opener only |

Point the filter-not-found troubleshooting line at `data/fleet/filters.json`.

### `docs/COVERAGE_CATALOG.md`

Replace living paths only:

| Old | New |
|---|---|
| `data/filters.json` | `data/fleet/filters.json` |
| `data/filter_matrix.json` | `data/fleet/filter_matrix.json` |
| `tests/helpers/dashboard_validation.py` | `tests/ui/fleet_dashboard/dashboard_validation.py` |
| `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` | `data/alerts/alerts_contract.yaml` |

Leave historical spec directories unchanged.
