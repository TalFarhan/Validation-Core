# Implementation Plan: Fleet DB Sanity and Validation Tests

**Branch**: `feature/reportportal-integration` (spec directory `039-fleet-db-sanity`) | **Date**: 2026-10-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/039-fleet-db-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The previous pin, `038-population-page-refactor`, stays as its own slice.

## Summary

Add a fleet sanity package that checks `data/fleet/db_sanity_all.yaml` two ways.
A pure checker loads the file and reconciles summary counters, breakdown sums,
category rates, and the credited-vehicle ledger. UI tests open the existing fleet
report through the current `dashboard` fixture, clear filters, and compare KPI
cards, chart segments, and credited rows to that same record. The citation
suffixes on the four rate lines are removed so the file parses. `core/`, the
fleet page, `tests/ui/`, `tests/e2e/`, and `db/clients/fleet.py` are not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML` (already in `requirements.txt`),
Playwright through the existing `dashboard` fixture in
`tests/ui/fleet_dashboard/conftest.py`. No new package.

**Storage**: Golden record `data/fleet/db_sanity_all.yaml`. No warehouse query
in this slice. `settings.DB_ENVIRONMENT` is not read.

**Testing**: `pytest` on `tests/sanity/fleet_dashboard/`. Structural tests do
not request `dashboard`. UI tests do. Auth state is required only for the UI
tests. Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not
edited.

**Target Platform**: Windows workstation; Chromium against the organizational
Power BI portal for the UI tests.

**Project Type**: One new sanity package plus a one-line data repair in the
golden file. No page-object or `core/` change.

**Performance Goals**: Structural tests only parse one small YAML file. Each UI
test reads the cards or the one chart it asserts. The ledger UI test searches
one vehicle number per golden row (six rows in the current file).

**Constraints**:

- **Generic checker** (FR-001–FR-007). Sums, rates, and ledger rules iterate
  the loaded document. Category names, unit names, and the four integers are
  not written into the assertion source.
- **No environment pin** (FR-001, FR-008). No `DB_ENVIRONMENT`, district, or
  portal URL in the new modules. UI tests call `reset_dashboard_filters()` and
  do not apply a slicer.
- **Existing page API** (FR-009, FR-012, AC-004). UI tests call
  `get_kpi_value`, `hover_chart_segment` / `parse_tooltip_entries` /
  `get_chart_segment_labels`, `select_tab("withdrawn")`, `search_vehicle`,
  and `table_contains_text` / `get_table_row_text`.
- **Skip only an empty visual** (FR-010). One UI test per chart.
- **Suite location** (FR-011). Checker and tests live under
  `tests/sanity/fleet_dashboard/`, not `tests/helpers/` or `core/`.
- **Golden repair only** (FR-013). Delete `[cite: 1]` from the four `rate`
  lines. The percent strings stay.
- **English comments** inside new functions.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `data/fleet/db_sanity_all.yaml` | EDIT | Remove `[cite: 1]` so the file parses. Values stay. |
| `tests/sanity/fleet_dashboard/__init__.py` | ADD | Package marker |
| `tests/sanity/fleet_dashboard/contract.py` | ADD | Load, normalize, reconcile. No Playwright. |
| `tests/sanity/fleet_dashboard/test_db_sanity.py` | ADD | Structural tests and UI tests |
| `pages/fleet_dashboard/main_dashboard_page.py` | UNCHANGED | Existing KPI, chart, and table methods |
| `tests/ui/fleet_dashboard/` | UNCHANGED | `dashboard` fixture is imported, not edited |
| `tests/e2e/` | UNCHANGED | Live SQL parity stays there |
| `db/clients/fleet.py` | UNCHANGED | No new query |
| `core/` | UNCHANGED | No layer change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. UI tests open the fleet report through the existing fixture.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Fleet labels and the golden file stay in the sanity package and `data/fleet/`. `core/` does not load them. The root `conftest.py` does not import the new package.
- **Existing tests are the contract (III)**: PASS. `tests/ui/` and the fleet page are not edited. Public methods keep their names and arguments. Fleet smoke is not the gate: Layer 0, Layer 2, and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. UI tests call existing page methods. They do not add locators.
- **Warehouse as source of truth (V)**: PASS with a recorded deviation. These tests compare the report to the checked-in golden file, not to a live SQL query. The deviation is justified in Complexity Tracking. No SQL is added.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay on the existing pytest run path. Assertion messages name the section, the key, and both values.
- **Extract shared behavior only (VII)**: PASS. The checker is fleet-specific and lives under `tests/sanity/fleet_dashboard/`. It is not placed in `tests/helpers/` and it does not add a `core/` API.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/039-fleet-db-sanity/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── fleet-sanity.md
```

### Source Code (repository root)

```text
data/fleet/db_sanity_all.yaml                 # rates lose the [cite: 1] suffix

tests/sanity/fleet_dashboard/
├── __init__.py
├── contract.py
│     ├── load_sanity_record()
│     ├── assert_summary()
│     ├── assert_breakdowns()
│     ├── assert_category_rates()
│     └── assert_ledger()
└── test_db_sanity.py
      ├── structural tests (no dashboard fixture)
      └── UI tests (import dashboard from the fleet UI conftest)

tests/ui/fleet_dashboard/conftest.py          # UNCHANGED; fixture is imported
pages/fleet_dashboard/main_dashboard_page.py  # UNCHANGED
core/                                         # UNCHANGED
db/clients/fleet.py                           # UNCHANGED
```

**Structure Decision**: Put the pure checker and the tests in
`tests/sanity/fleet_dashboard/`. Import `dashboard` from
`tests.ui.fleet_dashboard.conftest` the same way the alerts sanity module
imports `population_dashboard`. Leave the page object, the e2e suite, and
`core/` as they are. The live warehouse comparison stays in `tests/e2e/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: tests compare the fleet report to `data/fleet/db_sanity_all.yaml` instead of a live warehouse query | The user named that file as the baseline for summary counters, breakdowns, category rates, and the credited ledger. The numbers are a snapshot. | Calling `db/clients/fleet.py` would ignore the file and fail whenever the warehouse moves past the snapshot. `tests/e2e/` already compares the same KPI cards and charts to live SQL. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The checker loads only `data/fleet/db_sanity_all.yaml` and does not read `settings.DB_ENVIRONMENT`.
- Summary, breakdown, rate, and ledger rules iterate the loaded document. The four integers and the Hebrew names are not copied into the assertion source.
- UI tests call `reset_dashboard_filters()`, then `get_kpi_value`, chart reads, `select_tab("withdrawn")`, and `search_vehicle`. No slicer value is applied.
- `received` is not asserted as `in_use + credited + transferred`.
- Ledger pull sources are not required to appear in `pull_source_breakdown`.
- An empty chart skips only that chart's UI test. Structural tests do not skip.
- `core/`, `pages/fleet_dashboard/main_dashboard_page.py`, `tests/ui/`, `tests/e2e/`, and `db/clients/fleet.py` are absent from the edit list.
- No SQL client and no `core/` parser is added.
