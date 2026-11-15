# Implementation Plan: Structural Merge — Unify Alerts Dashboard Folders

**Branch**: `011-alerts-dashboard-merge` | **Date**: 2026-10-11 | **Spec**: inline feature request (no `spec.md`; `/speckit-plan` invoked directly)

**Input**: Feature request — merge the DB-parity suite from `tests/ui/alerts_dashboard/` into the existing
`tests/ui/alerts_analysis_dashboard/` smoke suite, then delete the redundant folder.

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command).

## Summary

Feature 010 introduced a **second** Alerts folder — `tests/ui/alerts_dashboard/` — for the DB-parity pilot,
even though a smoke suite for the same Power BI report already lived in `tests/ui/alerts_analysis_dashboard/`
(the 010 plan explicitly flagged this as a path-matching compromise). This feature removes that duplication:
it folds the parity artifacts (contract YAML + parity test), the date-range `Slicer` wiring, and the
`alerts_db` fixture into the existing **`AlertsAnalysisPage`** suite, then deletes `tests/ui/alerts_dashboard/`.

The result is a single source of truth per report, consistent with the one-folder-per-report convention used by
every other dashboard under `tests/ui/`. This is a **pure structural refactor**: no production `core/`, `db/`,
or engine logic changes — only relocation, a page-object merge, a fixture merge, and doc-path updates. The two
suites exercise the **same report** (`DASHBOARD_SEARCH_TERM = "ניתוח התרעות"` is identical in both page
objects), so no behavioral divergence is introduced.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, PyYAML (contract loading), SQLAlchemy + pyodbc
(Alerts DB runner). All already present; this feature adds **no** new dependency.

**Storage**: Read-only SQL Server (Alerts DB via `db/clients/alerts.py`). No schema or query changes.

**Testing**: `pytest` + Playwright Chromium. Markers unchanged (`sanity` for smoke, `db_parity` for parity).
Primary acceptance gate for this feature is **collection**, not execution:
`pytest --collect-only tests/ui/alerts_analysis_dashboard/` MUST cleanly collect both the smoke test and the
parity test. Regression gate: `pytest tests/ui/fleet_dashboard/` stays 100% green (Constitution III) — though
no fleet or `core/` code is touched here.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework (pytest page objects), layered portal architecture
(Layer 0 `core/portal`, Layer 2 `core/components`, domain `pages/<report>/` + `tests/ui/<report>/`).

**Performance Goals**: N/A — structural move; runtime behavior of both tests is unchanged.

**Constraints**:
- No logic drift: moved files keep byte-for-byte bodies except import/path lines required by relocation.
- `core/` and `db/` MUST NOT change (Constitution II). Alerts titles, SQL, slicer `role_name`, and the
  contract path remain under `tests/ui/alerts_analysis_dashboard/` and the YAML.
- All inline code comments within functions MUST be English only (request rule).
- After the move, `tests/ui/alerts_dashboard/` MUST NOT exist and MUST have zero live references.

**Scale/Scope**: 2 file moves + 2 merges + 1 deletion + doc updates:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` | NEW (moved) | Two pilot metrics; relocated verbatim |
| `tests/ui/alerts_analysis_dashboard/test_db_parity.py` | NEW (moved) | Parity test; relocated (no import edits needed) |
| `tests/ui/alerts_analysis_dashboard/page.py` | EDIT (merge) | Add date-range `Slicer` + `select_date_range()` to `AlertsAnalysisPage` |
| `tests/ui/alerts_analysis_dashboard/conftest.py` | EDIT (merge) | Add `alerts_db` session fixture; keep `dashboard = bind_dashboard(AlertsAnalysisPage)` |
| `tests/ui/alerts_dashboard/` | DELETE | Redundant folder (`__init__.py`, `page.py`, `conftest.py`, `alerts_contract.yaml`, `test_db_parity.py`) |
| `docs/COVERAGE_CATALOG.md` | EDIT | Repoint Alerts rows to the analysis-folder paths and `AlertsAnalysisPage` |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `AlertsAnalysisPage` already composes `ReportShell` (Layer 0). The merge adds a
  Layer 2 `Slicer` composition (the same pattern `AlertsDashboardPage` used) — no portal/SSO/iframe logic is
  re-implemented.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Nothing moves *into* `core/`. Alerts domain strings
  (search term, slicer `role_name`, KPI titles, SQL, contract path) stay in the domain suite and the YAML.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. No fleet or `core/` source changes; fleet
  smoke contract is unaffected. The feature's own contract is clean collection of both Alerts tests.
- **Page object discipline (IV)**: PASS. The parity test continues to drive the browser through the page
  object (`dashboard.select_date_range`) and the `Slicer`/`KPI` components — no ad-hoc locators added.
- **Warehouse as source of truth (V)**: PASS. Parity still compares UI to the read-only Alerts DB runner.
  `docs/COVERAGE_CATALOG.md` is updated so the KPI ↔ SQL ↔ test mapping points at the surviving paths.
- **Observability (VI)**: PASS. Run-report hooks, HTML/CSV artifacts, screenshots, and traces are untouched.
- **Extract shared behavior only (VII)**: PASS. No new generic API; this feature *reduces* surface area by
  deleting a duplicate suite and reusing the existing `AlertsAnalysisPage`.

**Result**: No violations. Complexity Tracking table left empty.

## Project Structure

### Documentation (this feature)

```text
specs/011-alerts-dashboard-merge/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (merge strategy decisions)
├── data-model.md        # Phase 1 output (file inventory + merged surface)
├── quickstart.md        # Phase 1 output (run + collection verification)
└── contracts/
    └── module-move.md   # Phase 1 output (move + import/collection contract)
```

### Source Code (repository root)

```text
tests/ui/alerts_analysis_dashboard/     # SURVIVES — unified suite
├── __init__.py                         # unchanged (empty package marker)
├── page.py                             # EDIT — AlertsAnalysisPage gains date-range Slicer + select_date_range
├── conftest.py                         # EDIT — add alerts_db fixture; dashboard binding unchanged
├── test_dashboard_smoke.py             # unchanged (freshness / sanity)
├── alerts_contract.yaml                # NEW (moved from alerts_dashboard)
└── test_db_parity.py                   # NEW (moved from alerts_dashboard)

tests/ui/alerts_dashboard/              # DELETED in full
├── __init__.py
├── page.py                             # AlertsDashboardPage — logic folded into AlertsAnalysisPage
├── conftest.py                         # alerts_db fixture folded into analysis conftest
├── alerts_contract.yaml                # moved
└── test_db_parity.py                   # moved

docs/COVERAGE_CATALOG.md                # EDIT — repoint Alerts rows to the analysis-folder paths
```

**Structure Decision**: Keep the established one-folder-per-report layout. `tests/ui/alerts_analysis_dashboard/`
is the canonical Alerts suite because it predates the pilot and matches every sibling dashboard's naming. The
parity artifacts move into it unchanged; `AlertsAnalysisPage` absorbs the date-range slicer so a single page
object serves both smoke and parity tests. `core/`, `db/`, and `tests/helpers/db_parity_engine.py` are
untouched — the engine already consumes the page via `page._report_frame()` and `select_date_range`, both
satisfied by the merged `AlertsAnalysisPage`.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |
