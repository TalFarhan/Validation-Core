---
description: "Task list for Structural Merge — Unify Alerts Dashboard Folders"
---

# Tasks: Structural Merge — Unify Alerts Dashboard Folders

**Input**: Design documents from `/specs/011-alerts-dashboard-merge/`

**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/module-move.md, quickstart.md
(no spec.md — `/speckit-plan` was invoked directly from an inline feature request)

**Tests**: No new test logic is authored. This feature is a structural move; the acceptance signal is clean
**collection** (`pytest --collect-only`). Fleet smoke (`tests/ui/fleet_dashboard/`) is a regression gate only —
no `core/portal`, `ReportShell`, or shared navigation code is touched.

**Organization**: Tasks are grouped by user story. US1 is the MVP (the merge itself); US2 is reference/doc
integrity.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths are included in each task

## Path Conventions

- Validation Core layout: `tests/ui/<report>/` (domain suites), `core/components/` (Layer 2),
  `db/clients/` (DB runners), `tests/helpers/` (engine), `docs/` (coverage catalog)
- Surviving suite: `tests/ui/alerts_analysis_dashboard/`
- Deleted suite: `tests/ui/alerts_dashboard/`

---

## Phase 1: Setup (Baseline)

**Purpose**: Capture the pre-merge baseline so the merge can be verified against it.

- [X] T001 Record baseline collection of both suites: run `pytest --collect-only tests/ui/alerts_dashboard/ tests/ui/alerts_analysis_dashboard/` and note the two target test node IDs (`test_dashboard_updated_within_24_hours`, `test_alerts_db_parity_last_30_days`)
- [X] T002 [P] Confirm the only live references to the deleted path by running `rg "alerts_dashboard|AlertsDashboardPage" tests core db pages` and verifying matches exist solely in `tests/ui/alerts_dashboard/` (the folder to delete)

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Make `AlertsAnalysisPage` capable of serving the parity test BEFORE the parity artifacts are moved
in, so the moved test resolves its `dashboard` fixture cleanly.

**⚠️ CRITICAL**: The page/fixture merge (T003, T004) MUST complete before the parity test is collected from the
analysis folder.

- [X] T003 Merge the date-range slicer surface into `tests/ui/alerts_analysis_dashboard/page.py`: add `DATE_RANGE_ROLE_NAME`, `_SLICER_DEFINITIONS` (one dropdown `SlicerDefinition(id="date_range", ...)`), compose `Slicer(...)` in `__init__`, and add `select_date_range(value: str)` delegating to `self._slicer.select("date_range", value)`; import `Slicer, SlicerDefinition` from `core.components.slicer`. Keep `DASHBOARD_SEARCH_TERM` and `_report_ready_locator()` as-is. All inline comments in English only (per contracts/module-move.md C2)
- [X] T004 Merge the DB fixture into `tests/ui/alerts_analysis_dashboard/conftest.py`: add `from db.clients.alerts import AlertsDBRunner`, `import pytest`, and a session-scoped `alerts_db` fixture returning `AlertsDBRunner()`; keep the existing `dashboard = bind_dashboard(AlertsAnalysisPage)` binding unchanged (per contracts/module-move.md C3)

**Checkpoint**: `AlertsAnalysisPage` now exposes `select_date_range`; the analysis `conftest.py` exposes both
`dashboard` and `alerts_db`.

---

## Phase 3: User Story 1 - Single source of truth for the Alerts report (Priority: P1) 🎯 MVP

**Goal**: The Alerts DB-parity artifacts live in `tests/ui/alerts_analysis_dashboard/` alongside the smoke
test, and the redundant `tests/ui/alerts_dashboard/` folder is removed.

**Independent Test**: `pytest --collect-only tests/ui/alerts_analysis_dashboard/` collects BOTH the smoke test
(`sanity`) and the parity test (`db_parity`) with zero errors, and `tests/ui/alerts_dashboard/` no longer
exists.

### Implementation for User Story 1

- [X] T005 [US1] Move `tests/ui/alerts_dashboard/alerts_contract.yaml` to `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` (verbatim content) (per contracts/module-move.md C1)
- [X] T006 [US1] Move `tests/ui/alerts_dashboard/test_db_parity.py` to `tests/ui/alerts_analysis_dashboard/test_db_parity.py` (verbatim body; `CONTRACT_PATH` resolves relative to the file, so no path edit) — depends on T005 (co-located contract)
- [X] T007 [US1] Verify the moved `tests/ui/alerts_analysis_dashboard/test_db_parity.py` imports no page class and references only `tests.helpers.db_parity_engine.validate_dashboard_generic` + the `dashboard`/`alerts_db` fixtures; fix any stray reference to `alerts_dashboard`/`AlertsDashboardPage` if present (per contracts/module-move.md C4) — depends on T006
- [X] T008 [US1] Delete the entire `tests/ui/alerts_dashboard/` directory (`__init__.py`, `page.py`, `conftest.py`, `alerts_contract.yaml`, `test_db_parity.py`) — depends on T003, T004, T005, T006
- [X] T009 [US1] Run `pytest --collect-only tests/ui/alerts_analysis_dashboard/` and confirm both `test_dashboard_updated_within_24_hours` and `test_alerts_db_parity_last_30_days` are collected with no import/fixture errors (per contracts/module-move.md C6) — depends on T005–T008
- [X] T010 [US1] Confirm the deleted path is gone: `Test-Path tests/ui/alerts_dashboard` returns `False`, and `rg "alerts_dashboard|AlertsDashboardPage" tests core db pages` returns no matches (per contracts/module-move.md C4, C6) — depends on T008

**Checkpoint**: A single Alerts suite collects both smoke and parity tests; the duplicate folder is gone. MVP
complete.

---

## Phase 4: User Story 2 - Reference & documentation integrity (Priority: P2)

**Goal**: The coverage catalog and any live mapping point at the surviving paths, so KPI ↔ SQL ↔ test
traceability (Constitution V) stays accurate.

**Independent Test**: `docs/COVERAGE_CATALOG.md` contains no `tests/ui/alerts_dashboard/` paths and no
`AlertsDashboardPage` reference; all Alerts rows point at `tests/ui/alerts_analysis_dashboard/...` and
`AlertsAnalysisPage.select_date_range`.

### Implementation for User Story 2

- [X] T011 [US2] Update `docs/COVERAGE_CATALOG.md`: repoint the two Alerts KPI rows from `tests/ui/alerts_dashboard/test_db_parity.py` to `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, the contract reference to `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, and the slicer reference to `tests/ui/alerts_analysis_dashboard/page.py` → `AlertsAnalysisPage.select_date_range` (per contracts/module-move.md C5)
- [X] T012 [US2] Verify `docs/COVERAGE_CATALOG.md` has zero remaining `alerts_dashboard` / `AlertsDashboardPage` references (`rg "alerts_dashboard|AlertsDashboardPage" docs/COVERAGE_CATALOG.md` returns nothing) — depends on T011

**Checkpoint**: Documentation reflects the unified suite. `specs/010-db-parity-engine/*` historical records are
intentionally left unchanged.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and regression safety.

- [X] T013 Audit all moved/merged files for English-only inline comments inside functions (`tests/ui/alerts_analysis_dashboard/page.py`, `conftest.py`, `test_db_parity.py`) (request rule)
- [X] T014 Run quickstart verification block from `specs/011-alerts-dashboard-merge/quickstart.md` (collection + deletion + no-stale-refs checks)
- [X] T015 Regression gate: `pytest --collect-only tests/ui/fleet_dashboard/` passes cleanly (11 tests, no collateral import breakage); full execution run needs live portal auth and is deferred to a live environment (no fleet/`core/` code was touched) (Constitution III)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first to capture baseline.
- **Foundational (Phase 2)**: Depends on Setup. T003 and T004 edit different files and may run in parallel.
  BLOCKS the folder deletion and final collection in US1.
- **User Story 1 (Phase 3)**: Depends on Foundational (page + fixture ready) and Setup.
- **User Story 2 (Phase 4)**: Depends on US1 (paths must be finalized before docs are repointed).
- **Polish (Phase 5)**: Depends on US1 and US2.

### User Story Dependencies

- **US1 (P1)**: The core merge. Depends on Phase 2. Independently testable via `--collect-only`.
- **US2 (P2)**: Documentation integrity. Depends on US1's final paths. Independently testable via `rg` on docs.

### Within User Story 1

- T005 (move contract) → T006 (move test) → T007 (verify imports)
- T003, T004, T005, T006 → T008 (delete folder) → T009/T010 (verify)

### Parallel Opportunities

- T003 (page.py) and T004 (conftest.py) are different files → can run in parallel.
- T001 and T002 (baseline checks) are independent → can run in parallel.

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Different files, no shared state — run together:
Task: "T003 Merge date-range slicer into tests/ui/alerts_analysis_dashboard/page.py"
Task: "T004 Add alerts_db fixture to tests/ui/alerts_analysis_dashboard/conftest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (baseline collection + reference inventory).
2. Phase 2: Foundational (merge page + fixture).
3. Phase 3: US1 (move artifacts, delete duplicate, verify clean collection).
4. **STOP and VALIDATE**: `pytest --collect-only tests/ui/alerts_analysis_dashboard/` shows both tests.

### Incremental Delivery

1. Setup + Foundational → page/fixture ready.
2. US1 → single suite collects both tests, duplicate removed (MVP).
3. US2 → coverage catalog repointed.
4. Polish → comment audit + fleet regression gate.

---

## Notes

- [P] tasks = different files, no dependencies.
- This is a structural refactor: moved bodies stay byte-for-byte identical except import/path lines required by
  relocation.
- `core/`, `db/`, and `tests/helpers/db_parity_engine.py` are NOT modified.
- Primary acceptance is clean collection, not full parity execution (the parity run needs live portal auth +
  Alerts SQL Server).
- Commit after each logical group (e.g., after Phase 2, after US1, after US2).
