# Phase 0 Research: Dependency Inversion Relocation

All Technical Context items were resolvable from the repository; there were no `NEEDS CLARIFICATION`
markers. This document records the decisions that shape the mechanical move.

## Decision 1: Where does `ExpandHierarchyUnavailable` live?

- **Decision**: Define `ExpandHierarchyUnavailable` inside
  `pages/fleet_dashboard/main_dashboard_page.py` (its only producer today).
- **Rationale**: The class message embeds the fleet-specific Hebrew term `הסתעפות` ("expand hierarchy"),
  which is a Power BI *chart* concept for the fleet dashboard — not generic portal chrome. Keeping it in the
  generic errors module violates Constitution II (Zero Domain Leakage). Grep shows it is raised/caught only in
  `main_dashboard_page.py` and `tests/e2e/test_chart_drilldown.py`. Co-locating it with its producer keeps the
  diff minimal and avoids creating a module with a single symbol.
- **Alternatives considered**:
  - *New file `pages/fleet_dashboard/errors.py`* — cleaner if a second fleet module raises the error later,
    but currently adds a file for one class. Documented as the fallback in `contracts/module-move.md`.
  - *Leave it in `core/errors.py`* — rejected; it reintroduces domain leakage into `core/`.

## Decision 2: Split generic vs. domain errors

- **Decision**: `core/errors.py` keeps only `LoadTimeoutError` (generic load/wait failure). The old
  `pages/errors.py` is removed.
- **Rationale**: `LoadTimeoutError` is raised by `BasePage.retry_with_backoff` / `wait_for_kpi_update` and by
  `ReportShell` — both generic Layer 0 behavior. It is report-agnostic (its Hebrew text is generic
  load-timeout chrome, not a dashboard label), so it belongs in `core/`.
- **Alternatives considered**: Keeping a thin `pages/errors.py` re-export shim — rejected; it would preserve
  the exact reverse-dependency smell this feature exists to remove and leave a dead compatibility layer.

## Decision 3: Move `BasePage` into `core/` (not a shared `pages` util)

- **Decision**: Move `pages/base_page.py` → `core/base_page.py` verbatim, changing only its internal import
  (`from pages.errors import LoadTimeoutError` → `from core.errors import LoadTimeoutError`).
- **Rationale**: `BasePage` is the generic Playwright timeout/retry foundation and the base of the
  `BasePage → ReportShell → domain page` chain. `ReportShell` (Layer 0) already depends on it; hosting it in
  `core/` removes the upward `core → pages` edge entirely. No behavior changes.
- **Alternatives considered**: Leaving `BasePage` in `pages/` and importing it into `core/` via a protocol —
  rejected as over-engineering for a pure relocation; still leaves `core` depending on `pages`.

## Decision 4: Scope of import rewrites

- **Decision**: Rewrite only live-code imports in `core/`, `pages/`, and `tests/`. Leave `specs/**` historical
  docs untouched.
- **Rationale**: The `specs/001-*` and `specs/002-*` references describe the architecture *at the time those
  features shipped*; rewriting them would falsify history and is outside this feature's scope.

## Decision 5: Regression strategy

- **Decision**: After edits, run `pytest tests/ui/fleet_dashboard/` as the hard gate; additionally confirm
  `tests/e2e/test_chart_drilldown.py` imports resolve.
- **Rationale**: Constitution III makes the fleet smoke suite the executable contract. A static import-only
  change is low risk, but Python import errors (e.g. a missed reference) only surface at collection/run time, so
  the suite is the definitive check.

## Verification tooling note

A fast structural guard: `rg "from pages\.(base_page|errors)|import pages\.(base_page|errors)" core/ pages/ tests/`
must return no matches after the refactor (except the intended fleet-local definition of
`ExpandHierarchyUnavailable`, which is a class definition, not a `pages.errors` import).
