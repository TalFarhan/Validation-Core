---
description: "Task list for Generic DB Parity Engine + Alerts Dashboard Pilot"
---

# Tasks: Generic DB Parity Engine + Alerts Dashboard Pilot

**Input**: Design documents from `/specs/010-db-parity-engine/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: This feature does NOT touch `core/portal`, `ReportShell`, or shared navigation, so broad test
coverage is OPTIONAL. The pilot parity test (`test_db_parity.py`) IS the feature deliverable, not an optional
test. One optional unit test for the KPI normalizer is included. The fleet smoke gate
(`pytest tests/ui/fleet_dashboard/`) is MANDATORY as a final regression check (AC8 / Constitution III).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every task

## Path Conventions

Validation Core layout: `core/components/` (Layer 2), `db/` (read-only warehouse clients),
`tests/helpers/` (shared engines), `tests/ui/<report>/` (domain suites), `config/`, `docs/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies and package scaffolding.

- [X] T001 [P] Add `pyyaml>=6.0` to `requirements.txt` (YAML contract loading per research R5)
- [X] T002 [P] Create package markers: `db/clients/__init__.py` and `tests/ui/alerts_dashboard/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config + marker that the DB runner and pilot test collection depend on.

**⚠️ CRITICAL**: Complete before user-story work.

- [X] T003 [P] Register the `db_parity` marker in `pytest.ini` under `markers` (e.g. `db_parity: UI-vs-DB parity checks driven by a YAML contract`); `--strict-markers` is on
- [X] T004 [P] Add `DB_ALERTS_NAME = _env("DB_ALERTS_NAME", "<alerts_db_name>")` to `config/settings.py` (Alerts database name per research R3)

**Checkpoint**: Config + marker ready — user stories can begin.

---

## Phase 3: User Story 1 - Generic KPI reader (Priority: P1) 🎯 MVP

**Goal**: A report-agnostic Layer 2 `KPI` component that locates a KPI card by title and normalizes its value
(strip commas, whitespace/NBSP, and `\u200f`/`\u200e`), returning clean string + numeric forms (AC1, FR-001).

**Independent Test**: Unit-test `normalize_kpi_text` with comma/RTL/whitespace inputs; the component holds no
report-specific strings (grep `core/components/kpi.py`).

### Tests for User Story 1 (OPTIONAL)

- [X] T005 [P] [US1] Unit test `normalize_kpi_text` (commas, `\u200f`/`\u200e`, NBSP, int vs float) in `tests/unit/test_kpi_normalize.py`

### Implementation for User Story 1

- [X] T006 [US1] Implement `normalize_kpi_text(raw)` and the `KPI` class (`__init__(page, frame, timeout_ms=None)`, `card(title)`, `read_text(title)`, `value(title)`, `number(title)`) in `core/components/kpi.py`, mirroring the `Slicer` composition pattern; card lookup `frame.get_by_role("button", name=re.compile(re.escape(title)))`, value node `card.locator("p").last`; English-only inline comments (AC1, AC7, FR-001)

**Checkpoint**: KPI component usable by any report; MVP building block complete.

---

## Phase 4: User Story 2 - Declarative parity engine + Alerts DB access (Priority: P2)

**Goal**: A YAML-driven engine that, for each contract metric, reads the UI via `KPI`, runs the parameterized
SQL via an Alerts DB runner using SQLAlchemy `text()` binds, and asserts equality (AC2, AC3, AC4, AC6,
FR-002/003/004).

**Independent Test**: Point the engine at `alerts_contract.yaml` with a known date window and a live/stub DB;
confirm it loads metrics, binds `:start_date`/`:end_date`, and reports per-metric pass/fail.

### Implementation for User Story 2

- [X] T007 [P] [US2] Implement `AlertsDBRunner` in `db/clients/alerts.py`: `__init__(engine=None)` defaulting to `create_db_engine(database=settings.DB_ALERTS_NAME)`; `scalar(sql, *, start_date, end_date)` executing `conn.execute(text(sql), {"start_date": ..., "end_date": ...}).scalar()`, numeric coercion, and `log_db_query` via `get_current_report()`; read-only, no date string-formatting (AC4, AC6, FR-004)
- [X] T008 [P] [US2] Create `tests/ui/alerts_dashboard/alerts_contract.yaml` with the two pilot metrics (`name` + parameterized `sql_query` using `:start_date`/`:end_date`) exactly as in data-model.md (AC3, FR-003)
- [X] T009 [US2] Implement `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` in `tests/helpers/db_parity_engine.py`: `yaml.safe_load` the contract, build `KPI` from the page's report iframe `FrameLocator`, per metric read `KPI.number(name)` + `db_client.scalar(sql_query, start_date, end_date)`, record `ParityResult`, log `log_kpi_read`/`log_db_query`/`log_assertion`, and assert all match (raise one `AssertionError` listing every mismatch); English-only comments (AC2, AC7, FR-002, FR-007) — depends on T006, T007

**Checkpoint**: Engine + Alerts DB access work against the contract independently of the UI wiring.

---

## Phase 5: User Story 3 - Alerts Dashboard 30-day pilot (Priority: P3)

**Goal**: End-to-end pilot: navigate to the Alerts Dashboard, select "שלושים יום אחרונים" via the `Slicer`,
compute the 30-day window in Python, and run the engine (AC5, AC8, FR-005/006).

**Independent Test**: `pytest tests/ui/alerts_dashboard/test_db_parity.py -m db_parity -v` passes with UI == DB
for both metrics.

### Implementation for User Story 3

- [X] T010 [US3] Implement `AlertsDashboardPage(ReportShell)` in `tests/ui/alerts_dashboard/page.py`: set `DASHBOARD_SEARCH_TERM`, override `_report_ready_locator()`, compose a `Slicer` with one dropdown `SlicerDefinition` for the date-range control, and expose `select_date_range(value)` (reuse the `AlertsAnalysisPage` pattern; domain strings stay here, not in `core/`) (AC5, FR-005, Constitution IV)
- [X] T011 [US3] Add fixtures in `tests/ui/alerts_dashboard/conftest.py`: `dashboard = bind_dashboard(AlertsDashboardPage)` (from `tests.helpers.dashboard_fixture`) and an `alerts_db` fixture returning `AlertsDBRunner()`
- [X] T012 [US3] Implement `tests/ui/alerts_dashboard/test_db_parity.py`: `@pytest.mark.db_parity` test that computes `end_date = datetime.now()` / `start_date = end_date - timedelta(days=30)`, calls `dashboard.select_date_range("שלושים יום אחרונים")`, then `validate_dashboard_generic(CONTRACT_PATH, dashboard, alerts_db, start_date, end_date)`; English-only comments (AC5, AC6, AC7, FR-005) — depends on T009, T010, T011

**Checkpoint**: Pilot runs green end-to-end; engine proven on a second report.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Catalog, verification, and the mandatory regression gate.

- [X] T013 [P] Update `docs/COVERAGE_CATALOG.md` to map both Alerts KPIs ↔ SQL ↔ `test_db_parity.py` (Constitution V)
- [ ] T014 Run the pilot: `pytest tests/ui/alerts_dashboard/test_db_parity.py -m db_parity -v` — UI == DB for both metrics (AC5) — **BLOCKED in this env**: requires live portal auth + Alerts SQL Server; run locally after setting `DB_ALERTS_NAME` and confirming the date-range slicer `role_name`
- [ ] T015 Run the fleet smoke gate: `pytest tests/ui/fleet_dashboard/` — MUST be 100% green (AC8 / Constitution III) — **BLOCKED in this env**: requires live portal auth; run locally
- [X] T016 Run quickstart.md verification: `rg "אזורי התרעה|AlertsRedWeb|alerts_contract" core/` returns nothing (verified); `db_parity` marker recognized under `--strict-markers` (collection passes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: After Setup — blocks DB runner + test collection.
- **User Stories (Phase 3–5)**: After Foundational. US1 is independent; US2 depends on US1 (T006); US3 depends
  on US2 (T009).
- **Polish (Phase 6)**: After US3.

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories (MVP building block).
- **US2 (P2)**: Uses `KPI` from US1 (T006). Contract YAML (T008) and DB runner (T007) are independent of US1.
- **US3 (P3)**: Uses the engine from US2 (T009).

### Within Each Story

- Models/components before services; services before the end-to-end test.
- T009 after T006 + T007; T012 after T009 + T010 + T011.

### Parallel Opportunities

- Setup: T001, T002 in parallel.
- Foundational: T003, T004 in parallel.
- US1: T005 (test) parallel with planning; T006 is the single implementation file.
- US2: T007 (DB runner) and T008 (YAML) in parallel; T009 after both + T006.
- US3: T010 and T011 in parallel; T012 after T009/T010/T011.
- Polish: T013 parallel with nothing blocking; T014–T016 run sequentially last.

---

## Parallel Example: User Story 2

```bash
# After US1 (T006) is done, launch independent US2 files together:
Task: "Implement AlertsDBRunner in db/clients/alerts.py"
Task: "Create tests/ui/alerts_dashboard/alerts_contract.yaml"
# Then:
Task: "Implement validate_dashboard_generic in tests/helpers/db_parity_engine.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 (`KPI` component) → validate with the normalizer
   unit test. This is the reusable core other reports will adopt.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 (`KPI`) → unit-test independently.
3. US2 (engine + DB runner + contract) → run engine against the contract.
4. US3 (Alerts pilot) → `pytest -m db_parity` green.
5. Polish → catalog + fleet smoke gate.

---

## Notes

- All contract SQL MUST bind `:start_date`/`:end_date` via `sqlalchemy.text()`; no f-strings on dates (AC6).
- `core/components/kpi.py` MUST stay report-agnostic (no Alerts/fleet titles or SQL) — Constitution II.
- All inline comments within functions MUST be English only (AC7).
- Commit after each task or logical group.
