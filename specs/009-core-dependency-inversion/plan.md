# Implementation Plan: Refactor Dependency Inversion — Move `base_page` and `errors` to `core`

**Branch**: `009-core-dependency-inversion` | **Date**: 2026-10-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-core-dependency-inversion/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by `/speckit-tasks`
(not this command).

## Summary

Eliminate the reverse dependency where Layer 0 (`core/portal/page.py`) imports from the domain `pages/`
tree. The fix is a **mechanical relocation**, not a behavioral refactor:

1. **Move** `pages/base_page.py` → `core/base_page.py` (the generic Playwright timeout/retry foundation,
   `BasePage`).
2. **Move** `pages/errors.py` → `core/errors.py`, but **only the generic** error type `LoadTimeoutError`.
3. **Extract** `ExpandHierarchyUnavailable` (chart-specific, contains the fleet Hebrew term `הסתעפות`) out of
   the generic errors module into the fleet domain (`pages/fleet_dashboard/`).
4. **Rewrite** every affected `import` in `core/`, `pages/`, and `tests/` to the new paths.
5. **Verify** `pytest tests/ui/fleet_dashboard/` stays 100% green.

Technical approach: treat this as an import-topology fix. The inheritance chain stays
`BasePage` → `ReportShell` → `MainDashboardPage`; only the *physical location* of `BasePage` and the generic
error moves from `pages/` into `core/`, so Layer 0 no longer depends on the domain tree. No function bodies,
locators, SQL, waits, or Allure/CSV/screenshot wiring change.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest. No new dependencies. Reuses `config.settings`,
`browser_session`, `reports.test_run_report` exactly as today.

**Storage**: N/A — no schema, no `data/*.json`, no `db/` change.

**Testing**: `pytest` + Playwright Chromium. Regression gate: `pytest tests/ui/fleet_dashboard/` MUST stay
100% green (Constitution III). The chart-drilldown e2e (`tests/e2e/test_chart_drilldown.py`) that catches
`ExpandHierarchyUnavailable` must still import it and pass.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal (same as
today).

**Project Type**: Internal validation framework (pytest page objects) with layered portal architecture
(Layer 0 `core/portal`, Layer 2 `core/components`, domain `pages/<report>/`).

**Performance Goals**: N/A — a pure import relocation adds zero runtime cost and no new network calls.

**Constraints**:
- Do NOT modify any business logic or UI interaction flow inside the fleet dashboard.
- Do NOT refactor chart logic; mechanical file moves + import updates only.
- All inline code comments within functions MUST be English only.

**Scale/Scope**: 2 files moved, 1 class extracted, ~5 code files with import edits. Affected code imports
(from repository grep):

| File | Current import | New import |
|------|----------------|------------|
| `core/portal/page.py` | `from pages.base_page import BasePage` | `from core.base_page import BasePage` |
| `core/portal/page.py` | `from pages.errors import LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| `core/base_page.py` (moved) | `from pages.errors import LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| `pages/fleet_dashboard/main_dashboard_page.py` | `from pages.errors import ExpandHierarchyUnavailable, LoadTimeoutError` | `from core.errors import LoadTimeoutError` + fleet-local `ExpandHierarchyUnavailable` |
| `tests/helpers/dashboard_validation.py` | `from pages.errors import LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| `tests/e2e/test_chart_drilldown.py` | `from pages.errors import ExpandHierarchyUnavailable` | fleet error location |

> Spec-doc occurrences in `specs/001-extract-report-shell/*` and `specs/002-generic-slicer/architecture.md`
> are historical records of the *old* layout, not live code. They are out of scope for import rewrites.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS — strengthened. The chain `BasePage → ReportShell → domain page` is preserved;
  moving `BasePage` into `core/` makes Layer 0 self-contained. Note: Architecture Constraints currently cite
  `pages.base_page.BasePage`; this plan relocates that foundation into `core/` and the constitution's
  Architecture Constraints wording should be updated (documentation follow-up, non-blocking).
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS — strengthened. Today `core/` imports from `pages/`
  (reverse dependency) and the generic errors module carries the fleet Hebrew term `הסתעפות` via
  `ExpandHierarchyUnavailable`. After this change `core/` imports nothing from `pages/`, and the only
  domain-specific error leaves the generic module for the fleet domain.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS — enforced by AC5/AC6. Public test-facing
  APIs (`navigate`, `reload_and_measure_ready_ms`, the `dashboard` fixture, KPI/filter/chart methods) are
  untouched; only import paths change. `pytest tests/ui/fleet_dashboard/` is the required gate.
- **Page object discipline (IV)**: PASS — no locators move into tests; `BasePage` remains the shared
  timeout/retry foundation (now under `core/`).
- **Warehouse as source of truth (V)**: PASS — no `db/`, SQL, or coverage-catalog change.
- **Observability (VI)**: PASS — Allure steps, CSV logs, screenshots, traces are not touched by an import move.
- **Extract shared behavior only (VII)**: PASS — nothing is genericized. A domain-specific error is pushed
  *down* to the domain; no new generic API is invented.

**Result**: No violations. Complexity Tracking table left empty.

## Project Structure

### Documentation (this feature)

```text
specs/009-core-dependency-inversion/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification (anchor)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (module/class topology)
├── quickstart.md        # Phase 1 output (verification steps)
└── contracts/           # Phase 1 output (import + public-API contract)
    └── module-move.md
```

### Source Code (repository root)

```text
core/
├── __init__.py
├── base_page.py          # NEW location of BasePage (moved from pages/base_page.py)
├── errors.py             # NEW location of generic errors (LoadTimeoutError)
├── portal/
│   └── page.py           # ReportShell — imports updated to core.base_page / core.errors
└── components/
    └── slicer.py         # unchanged

pages/
├── errors.py             # REMOVED (contents split: generic → core, fleet error → fleet domain)
├── base_page.py          # REMOVED (moved to core/base_page.py)
└── fleet_dashboard/
    └── main_dashboard_page.py   # hosts ExpandHierarchyUnavailable; imports LoadTimeoutError from core

tests/
├── helpers/dashboard_validation.py   # import updated to core.errors
├── e2e/test_chart_drilldown.py       # import ExpandHierarchyUnavailable from fleet location
└── ui/fleet_dashboard/               # regression gate (unchanged source)
```

**Structure Decision**: Keep the existing layered layout. The only structural change is physical: `BasePage`
and the generic error move from `pages/` into `core/` so Layer 0 has no upward dependency on the domain tree.
`ExpandHierarchyUnavailable` is relocated into `pages/fleet_dashboard/main_dashboard_page.py` (its only
producer) rather than a new module, keeping the diff minimal; the drilldown e2e imports it from there. (A
dedicated `pages/fleet_dashboard/errors.py` is a documented alternative in `contracts/module-move.md` if a
second fleet consumer appears.)

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |
