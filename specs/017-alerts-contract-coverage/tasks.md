---
description: "Task list for Alerts contract coverage"
---

# Tasks: Alerts Contract Coverage

**Input**: Design documents from `/specs/017-alerts-contract-coverage/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/alerts-contract-coverage.md, quickstart.md

**Tests**: Spec independent tests and the plan require extensions of
`tests/unit/test_db_parity_engine.py`. Write each story's assertions first and confirm they fail
before the matching YAML and SQL constants. The live test file
`tests/ui/alerts_analysis_dashboard/test_db_parity.py` is not edited. Do **not** edit `core/` or
`tests/helpers/db_parity_engine.py`. Do **not** add a pytest skip or a `try`/`except` around the
Alerts database connection.

**Organization**: All four stories are P1. US1 (threat time-bucket cards) is the MVP. US2 adds the
general population and warning-area cards. US3 adds the static comparison chart. US4 locks the
stub-execution and connection-error rules. US1–US3 share `alerts_contract.yaml`,
`db/clients/alerts.py`, and the unit test file, so implement them in order even though each story's
assertions can pass on their own rows.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths are included in each task

## Path Conventions

- Domain contract: `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`
- Alerts SQL client: `db/clients/alerts.py`
- Unit tests: `tests/unit/test_db_parity_engine.py`
- Live parity test (do not edit): `tests/ui/alerts_analysis_dashboard/test_db_parity.py`
- Catalog: `docs/COVERAGE_CATALOG.md`
- Untouched: `core/components/kpi.py`, `core/components/chart.py`, `core/components/visual.py`, `core/portal/`, `tests/helpers/db_parity_engine.py`, `tests/ui/alerts_analysis_dashboard/page.py`

---

## Phase 1: Setup (Baseline)

**Purpose**: Confirm this slice needs no new package and no engine change.

- [X] T001 Confirm `pyyaml` and `sqlalchemy` are already in `requirements.txt` and the `db_parity` marker is already in `pytest.ini`. Do not add a dependency or a marker (plan.md Technical Context)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the runner that every new `sql_query` will execute. No story starts until this check is done.

**⚠️ CRITICAL**: No user-story YAML work starts until the runner contract is confirmed unchanged.

- [X] T002 Confirm `AlertsDBRunner.scalar` and `AlertsDBRunner.rows` in `db/clients/alerts.py` still bind `start_date` and `end_date` through SQLAlchemy `text()`, and include `category_id` only when the caller passes it. Confirm `__init__` calls `create_db_engine` with no `try`/`except`. Do not change method signatures and do not add a `try`/`except` (FR-009, AC-004, research.md R5)

**Checkpoint**: The engine and runner already accept scoped KPI and chart metrics. Stories only add contract rows and stub constants.

---

## Phase 3: User Story 1 - Threat cards inside their section (Priority: P1) 🎯 MVP

**Goal**: Nine KPI metrics, three threat scopes times the three stable card titles, each with its category id.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_contract_threat_time_buckets -v` with no browser. The test loads `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` and finds nine rows keyed by `(name, scope)`.

### Tests for User Story 1

- [X] T003 [US1] Add a failing `test_alerts_contract_threat_time_buckets` in `tests/unit/test_db_parity_engine.py`. Load the Alerts contract with `yaml.safe_load`. Import `THREAT_KPI_STUB_SQL` inside the test function so the rest of the module still collects. Assert exactly these nine `(name, scope, category_id)` tuples, each with `visual == "kpi"` and `" ".join(sql_query.split()) == THREAT_KPI_STUB_SQL`: scopes `ירי רקטות וטילים` / `חדירת מחבלים` / `חדירת כלי טיס עוין` with `category_id` strings `"1"` / `"2"` / `"10"`, and names `היום`, `אתמול`, and `סה"כ בטווח שנבחר` on every scope. Assert `label` is `Rockets`, `Terrorists`, and `UAV` for those ids. Assert no threat `name` or `scope` contains `שלושים יום`. Key the new rows by `(name, scope)`, not by `name` alone. Do not start a browser (FR-001, FR-003, SC-001, research.md R6)

### Implementation for User Story 1

- [X] T004 [US1] Add `THREAT_KPI_STUB_SQL = "SELECT 0"` next to the existing stubs in `db/clients/alerts.py`. Comment in English that the statement is executed and a missing database must surface as a connection error. Do not put Hebrew, `'1'`, `'2'`, or `'10'` in this file. Do not add `try`/`except` (FR-005, FR-008, AC-005, contracts/alerts-contract-coverage.md) — depends on T003
- [X] T005 [US1] Add the nine threat metrics to `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` using the shape in `specs/017-alerts-contract-coverage/contracts/alerts-contract-coverage.md`. `category_id` values are the quoted strings `"1"`, `"2"`, and `"10"`. Quote `סה"כ בטווח שנבחר` so the double quote is data (`'סה"כ בטווח שנבחר'`). Set `sql_query` to `SELECT 0`. Add an English comment that these names are stable card titles and the scopes are the threat sections. Do not remove or rewrite the six existing category KPIs, the ranking chart, the map, or the policy status (FR-001, FR-006, data-model.md ThreatCard) — depends on T004
- [X] T006 [US1] Run `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_contract_threat_time_buckets tests/unit/test_db_parity_engine.py::test_alerts_contract_names_and_category_ids -v` and confirm both pass (SC-001) — depends on T005

**Checkpoint**: Threat cards are in the contract. The six existing category measures still match ids `1`, `2`, and `10`.

---

## Phase 4: User Story 2 - Population and warning-area cards (Priority: P1)

**Goal**: Six general KPI metrics under the stable bases `אוכלוסייה מותרעת` and `אזורי התרעה תחת ירי`, with no category id and no slicer suffix.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_contract_general_time_buckets -v`. Six rows, `visual: kpi`, no `category_id`. This test does not require the threat rows from US1.

### Tests for User Story 2

- [X] T007 [US2] Add a failing `test_alerts_contract_general_time_buckets` in `tests/unit/test_db_parity_engine.py`. Import `POPULATION_KPI_STUB_SQL` and `AREA_KPI_STUB_SQL` inside the test. Assert scope `אוכלוסייה מותרעת` has names `היום`, `אתמול`, and `סה"כ בטווח שנבחר`, `visual == "kpi"`, no `category_id` key, and SQL equal to `POPULATION_KPI_STUB_SQL`. Assert the same three names under scope `אזורי התרעה תחת ירי` with SQL equal to `AREA_KPI_STUB_SQL`. Assert neither scope contains `שלושים יום`. Do not treat these rows as the existing metrics whose `name` is the base and whose `category_id` is set (FR-002, FR-003, research.md R3, R4) — depends on T002

### Implementation for User Story 2

- [X] T008 [US2] Add `POPULATION_KPI_STUB_SQL = "SELECT 0"` and `AREA_KPI_STUB_SQL = "SELECT 0"` in `db/clients/alerts.py`, separate constants even though the text matches `THREAT_KPI_STUB_SQL`. English comment only. No Hebrew and no category ids (FR-005, data-model.md StubStatement) — depends on T007
- [X] T009 [US2] Add the six general metrics to `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` as in `specs/017-alerts-contract-coverage/contracts/alerts-contract-coverage.md`. `scope` is the stable base. `name` is the time-bucket title. `visual: kpi`. Do not set `category_id` or `maximum_sql`. Do not rename the existing six category measures that use those Hebrew strings as `name` (FR-002, research.md R3) — depends on T008
- [X] T010 [US2] Run `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_contract_general_time_buckets tests/unit/test_db_parity_engine.py::test_alerts_contract_names_and_category_ids -v` and confirm both pass (SC-001) — depends on T009

**Checkpoint**: General time-bucket cards are in the contract. The existing per-id population and warning-area queries are unchanged.

---

## Phase 5: User Story 3 - Static settlement comparison chart (Priority: P1)

**Goal**: One chart metric whose full title is permanent, with SQL that does not filter on the slicer window.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_contract_static_comparison_chart -v`. The chart name matches the exact static title. Its SQL has no date predicate. The ranking chart is still a different metric.

### Tests for User Story 3

- [X] T011 [US3] Add a failing `test_alerts_contract_static_comparison_chart` in `tests/unit/test_db_parity_engine.py`. Import `PERIOD_COMPARISON_CHART_SQL` inside the test. Assert one metric with `name` exactly `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת` (one yod in `ישובים`), `visual == "chart"`, no `scope`, no `category_id`, and `" ".join(sql_query.split()) == PERIOD_COMPARISON_CHART_SQL`. Assert that SQL text does not contain `:start_date`, `:end_date`, or `AlertDate`. Assert the ranking chart `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` (two yods) is still present and was not renamed to the new title (FR-004, FR-006, SC-002, SC-003, research.md R2) — depends on T002

### Implementation for User Story 3

- [X] T012 [US3] Add `PERIOD_COMPARISON_CHART_SQL` in `db/clients/alerts.py` as `SELECT CAST(NULL AS nvarchar(200)) AS category_label, CAST(NULL AS int) AS metric_value WHERE 1 = 0`. English comment: this statement ignores the slicer window and must not reference `AlertDate`, `:start_date`, or `:end_date`; `WHERE 1 = 0` returns no rows so `rows()` does not see a blank label. No Hebrew (FR-005, research.md R5, contracts/alerts-contract-coverage.md) — depends on T011
- [X] T013 [US3] Add the chart metric to `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` with that exact `name`, `visual: chart`, and `sql_query` equal to the constant. Do not set `scope` or `category_id`. Do not change the ranking chart's two-yod spelling. English comment that this title is static and does not follow the time slicer (FR-004, data-model.md StaticComparisonChart) — depends on T012
- [X] T014 [US3] Run `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_contract_static_comparison_chart tests/unit/test_db_parity_engine.py::test_remaining_visuals_use_stub_sql -v` and confirm both pass (SC-002) — depends on T013

**Checkpoint**: The static chart is contracted. The ranking chart, map, and policy stubs still match their existing constants.

---

## Phase 6: User Story 4 - Stubs run, connection errors surface (Priority: P1)

**Goal**: Every new stub is the constant from the Alerts client, and a missing database still fails the parity test.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py::test_alerts_stubs_do_not_hide_connection_errors -v`. The client source has no Hebrew and no `except`. `test_db_parity.py` has no skip.

### Tests for User Story 4

- [X] T015 [US4] Add `test_alerts_stubs_do_not_hide_connection_errors` in `tests/unit/test_db_parity_engine.py`. Read `db/clients/alerts.py` as text and assert it contains `THREAT_KPI_STUB_SQL`, `POPULATION_KPI_STUB_SQL`, `AREA_KPI_STUB_SQL`, and `PERIOD_COMPARISON_CHART_SQL`, and that it does not contain `ירי רקטות`, `חדירת מחבלים`, `חדירת כלי טיס`, `אוכלוסייה`, `אזורי התרעה`, or `except`. Read `tests/ui/alerts_analysis_dashboard/test_db_parity.py` and assert it does not contain `pytest.skip`, `importorskip`, or `mark.skip` (FR-007, FR-009, SC-006) — depends on T006, T010, T014

### Implementation for User Story 4

- [X] T016 [US4] Leave `tests/ui/alerts_analysis_dashboard/test_db_parity.py` unchanged so it still loads the full contract through `validate_dashboard_generic` and executes the new stubs. If a `pytest.skip`, `importorskip`, `mark.skip`, or a `try`/`except` around `create_db_engine` or `connect` was added in `db/clients/alerts.py`, remove it. Do not catch a connection error to force a pass (FR-009, SC-006, contracts/alerts-contract-coverage.md section 3) — depends on T015

**Checkpoint**: Stubs are real statements. A missing Alerts database fails the live test.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Catalog the new rows and run the regression gates from quickstart.md.

- [X] T017 [P] Update section 8 of `docs/COVERAGE_CATALOG.md` so the nine threat cards, the six general cards, and the static comparison chart are listed with visual kind, scope, category id (or none), and stub SQL. Keep the existing six category rows, the ranking chart, the map, and the policy status. Mark the new SQL as unconfirmed stubs (FR-010, Constitution V) — depends on T005, T009, T013
- [X] T018 Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm the full file passes, including the four new contract tests and the existing loader tests (quickstart.md section 1) — depends on T016
- [X] T019 [P] Confirm `git diff -- core/components core/portal tests/helpers/db_parity_engine.py` is empty (SC-004, FR-007) — depends on T016
- [X] T020 Run `python -m pytest tests/ui/fleet_dashboard/ -v` and confirm it is 100% green (SC-005, quickstart.md section 4) — depends on T016
- [X] T021 Walk `specs/017-alerts-contract-coverage/quickstart.md` sections 1, 2, and 5. Section 3 (live `test_db_parity.py`) may fail the new stubs against a populated report; do not add a skip to make that failure pass (FR-009, quickstart.md section 3) — depends on T017, T018, T019, T020

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks all user stories.
- **User Stories (Phases 3–6)**: Depend on Foundational. US1, US2, and US3 all edit `alerts_contract.yaml`, `db/clients/alerts.py`, and `tests/unit/test_db_parity_engine.py`, so run them in that order to avoid overlapping edits. US4 depends on the constants and rows from US1–US3.
- **Polish (Phase 7)**: Depends on US4. T017 and T019 can run in parallel after US4. T021 runs last.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on US2–US4. MVP.
- **User Story 2 (P1)**: Starts after Foundational. Its test does not require threat rows. Implement after US1 because both edit the same files.
- **User Story 3 (P1)**: Starts after Foundational. Its test does not require US1 or US2 rows. Implement after US2 because both edit the same files.
- **User Story 4 (P1)**: Starts after US1, US2, and US3. It locks constants and the no-skip rule; it does not add metrics.

### Within Each User Story

- The failing unit test is written before the constant and the YAML.
- The constant is added before the YAML row that must equal it.
- The story's pytest command runs after the YAML edit.
- Existing feature-016 metrics are not removed in any story.

### Parallel Opportunities

- T017 and T019 touch different files and can run together after T016.
- US1, US2, and US3 are not parallel: they share the contract, the SQL client, and the unit test module.
- No `[P]` marker inside a story, because each story's test, constant, and YAML are ordered.

---

## Parallel Example: Polish

```text
Task: "T017 [P] Update section 8 of docs/COVERAGE_CATALOG.md"
Task: "T019 [P] Confirm git diff -- core/components core/portal tests/helpers/db_parity_engine.py is empty"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and run `test_alerts_contract_threat_time_buckets` plus `test_alerts_contract_names_and_category_ids`.

### Incremental Delivery

1. Setup + Foundational.
2. US1 threat cards → nine scoped KPIs with category ids.
3. US2 general population and warning-area cards → six KPIs, no category id.
4. US3 static comparison chart → one chart whose SQL ignores the date window.
5. US4 → stubs stay executable and connection errors stay visible.
6. Polish → catalog, full unit file, empty `core/` diff, fleet smoke.

### Sequential File Strategy

One implementer should take US1, then US2, then US3, then US4. Splitting those stories across people conflicts on `alerts_contract.yaml`.

---

## Notes

- `[P]` tasks use different files and have no ordering dependency.
- `[USn]` maps the task to the spec user story.
- Do not normalize `ישובים` (comparison chart, one yod) to `יישובים` (ranking chart, two yods).
- Do not put `שלושים יום אחרונים` into any new `name` or `scope`. Keep `ביממה הנוכחית והקודמת` on the comparison chart.
- New cards are `visual: kpi`. Do not invent `maximum_sql`.
- `SELECT 0` and the empty chart statement are executed. A mismatch against the live report is expected until real SQL replaces the stubs.
