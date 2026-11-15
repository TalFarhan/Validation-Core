# Implementation Plan: Alerts Population Page

**Branch**: `feature/reportportal-integration` (spec directory `019-alerts-population-page`) | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/019-alerts-population-page/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration`). Feature 018 stays the layout move. This slice adds
the second alerts page, its contract rows, UI identities, and SQL placeholders. It does not run
those placeholders against the UI.

## Summary

The Alerts Analysis report already has a first page (`AlertsAnalysisPage`) and a contract at
`data/alerts/alerts_contract.yaml`. The second page is population and distribution: three
population cards, a district chart, hour and date distributions, and a two-series settlement
chart. Slicers on that page include between-dates, day/night, and a numeric range.

This feature checks the page before any warehouse comparison:

- A new page object opens the same catalog product and selects the second page. The existing
  `dashboard` fixture stays on page 1.
- Every new contract row uses that page's tab title as `scope`. Names drop a dynamic `בין` suffix.
  `אוכלוסייה לפי יישוב` is two rows with different `series_index` values for `מותרעות` and
  `לא מותרעות`.
- UI tests snapshot the three cards and the chart totals, disturb the slicers (dates, day/night,
  range 0–349), clear, and require the same numbers. Separate tests check day+night, the three
  distribution totals in Sum mode, and the two population bounds. They do not open the database.
- `db/clients/alerts.py` gains placeholder constants. Cards are `SELECT 0`. Charts return no rows.
  Comments record half-open dates, one grouping grain at a time, and the average/sum rule.
  The page-1 parity test excludes this page's scope so the placeholders are not executed there.

`core/` is not edited. Clear uses the existing generic clear-all control. Between-dates, day/night,
and the numeric range stay on the domain page.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (page and UI tests), PyYAML (contract load), pytest.
SQLAlchemy 2.0.51 `text()` is already used by `AlertsDBRunner` and is not called for the new
identities. No new package.

**Storage**: Read-only SQL Server, database `settings.DB_ALERTS_NAME`. No schema change. New
statements are placeholders in `db/clients/alerts.py`. They are not executed by the new UI tests.
The page-1 parity test must not execute them either.

**Testing**: `pytest`.

- Unit: extend `tests/unit/test_db_parity_engine.py` for the new rows, the page-title scope, the
  distinct series indexes, placeholder SQL, and `exclude_scopes`. No browser.
- UI: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` against the portal.
  These tests are not marked `db_parity`.
- Page-1 gate stays `pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity`
  and must still ignore the new rows. No skip is added.
- `core/` and `pages/fleet_dashboard/` are not edited, so the fleet smoke suite is not a required
  gate for this slice. A diff under `core/` or the fleet page would make that gate required.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal
for the population UI tests and the existing parity test.

**Project Type**: Internal validation framework. Domain page under `pages/alerts_analysis/`.
Contract under `data/alerts/`. SQL constants in `db/clients/alerts.py`. UI tests under
`tests/ui/alerts_analysis_dashboard/`.

**Performance Goals**: N/A. One extra report-page click and a handful of visual reads per test.

**Constraints**:

- Do not edit `core/portal` or `core/components` (Constitution II, VII, FR-015).
- Do not add a `SlicerKind` for between-dates, toggles, or numeric ranges (VII, AC-005).
- Hebrew, the page title, and series names stay in the page module and the YAML (FR-015).
- New `scope` values MUST equal `AlertsPopulationPage.PAGE_TITLE` (FR-003).
- New `name` values MUST NOT contain `בין` (FR-004). The district name is `התרעות לפי מחוז`.
- Card placeholders are the text `SELECT 0`. Chart placeholders return no rows and use two
  columns (FR-013, research R4). Do not point a chart metric at `SELECT 0`.
- `validate_dashboard_generic` keeps its positional parameters. `exclude_scopes` is an optional
  keyword. The page-1 test passes `{AlertsPopulationPage.PAGE_TITLE}` (FR-014).
- Do not add `pytest.skip`, `pytest.importorskip`, or `pytest.mark.skip` on
  `test_alerts_db_parity_last_30_days`. Do not catch a connection error.
- Inline comments in edited Python and YAML MUST be English only (FR-015).
- The snapshot helper lives beside the alerts UI tests, not in `tests/helpers/` (VII).
- Do not invent the page title, the hour-chart prefix, the dates-chart prefix, or the three card
  prefixes. Copy them from the live report (research R1).

**Scale/Scope**: One new page class, one contract appendix, two SQL constants, one engine
keyword, four UI tests, catalog rows. No drilldown and no real warehouse SQL.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | NEW | Second-page object. Tab select, card and chart reads, slicer actions |
| `pages/alerts_analysis/page.py` | NONE | Page 1 stays `AlertsAnalysisPage` |
| `tests/ui/alerts_analysis_dashboard/conftest.py` | EDIT | Add `population_dashboard`. Keep `dashboard` on page 1 |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | NEW | Arrival snapshot and exact restore comparison |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | NEW | Clear, day/night, cross-chart sums, population bounds |
| `data/alerts/alerts_contract.yaml` | EDIT | Page-2 rows only. Page-1 rows unchanged |
| `db/clients/alerts.py` | EDIT | Two placeholder constants and the future-rule comments |
| `tests/helpers/db_parity_engine.py` | EDIT | Optional `exclude_scopes` keyword |
| `tests/ui/alerts_analysis_dashboard/test_db_parity.py` | EDIT | Pass `exclude_scopes` for the page title |
| `tests/unit/test_db_parity_engine.py` | EDIT | Contract shape and exclusion |
| `docs/COVERAGE_CATALOG.md` | EDIT | Page-2 rows as UI checks and unconfirmed placeholders |
| `core/` | NONE | Readers and clear-all already exist |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `AlertsPopulationPage` subclasses `AlertsAnalysisPage`, which
  subclasses `ReportShell`. Tab selection uses `before_report_ready_check`. Login, catalog
  search, iframe wait, and last-refresh stay in Layer 0. The ready locator is the district
  chart phrase on the domain page.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The page title, Hebrew titles, and series
  names live in `population_page.py` and the YAML. `core/` is not edited. `exclude_scopes` is a
  set of opaque strings.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. `dashboard` still builds
  `AlertsAnalysisPage`. `validate_dashboard_generic`'s positional signature is unchanged.
  `exclude_scopes` defaults to no exclusion, and the page-1 test opts in so new rows cannot
  fail that run. Fleet navigation is untouched.
- **Page object discipline (IV)**: PASS. UI tests call the population page and the snapshot
  helper. Locators for the tab, between-dates, day/night, range, and Sum mode stay on the page
  object. Clear goes through `Slicer.clear_all`.
- **Warehouse as source of truth (V)**: PASS for the boundary this slice draws. UI identities
  do not pretend to be warehouse proof. Placeholders live in `db/clients/alerts.py`, are
  executed by nobody in the new tests, and are excluded from the page-1 run. The catalog marks
  them unconfirmed. Layer 0 still has no business SQL.
- **Observability (VI)**: PASS. No logging path is removed. New UI tests use the same page
  session and failure screenshot/trace fixtures as the other alerts tests.
- **Extract shared behavior only (VII)**: PASS. No new generic slicer kind. The snapshot helper
  is alerts-specific and stays under `tests/ui/alerts_analysis_dashboard/`. `exclude_scopes` is
  a filter on the existing engine, not a new visual reader.

**Post-design re-check**: Data model, contract, and quickstart introduce no Layer 0 edit, no
Hebrew in `core/`, no page-2 SQL inside the page-1 run, and no second clear-all implementation.
Complexity Tracking stays empty.

**Result**: No violations.

## Project Structure

### Documentation (this feature)

```text
specs/019-alerts-population-page/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── population-page.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/
├── page.py                         # unchanged — AlertsAnalysisPage (page 1)
└── population_page.py              # NEW — AlertsPopulationPage (page 2)

data/alerts/alerts_contract.yaml    # EDIT — append page-2 metrics

db/clients/alerts.py                # EDIT — placeholder constants

tests/helpers/db_parity_engine.py   # EDIT — optional exclude_scopes

tests/ui/alerts_analysis_dashboard/
├── conftest.py                     # EDIT — population_dashboard fixture
├── population_snapshot.py          # NEW
├── test_population_invariants.py   # NEW
└── test_db_parity.py               # EDIT — exclude the page-2 scope

tests/unit/test_db_parity_engine.py # EDIT
docs/COVERAGE_CATALOG.md            # EDIT
```

**Structure Decision**: Validation Core layout. The second page is another class in
`pages/alerts_analysis/`, not a new catalog product and not a module under `tests/`. The
contract file stays the single alerts YAML. Page-2 rows are kept out of the page-1 run by
scope, not by a second file.

## Complexity Tracking

> No constitution violations. Between-dates, day/night, and the numeric range stay on the
> domain page because Layer 2 is limited to dropdown, checkbox, search, and clear-all, and
> this slice must not invent a generic range API for one report.
