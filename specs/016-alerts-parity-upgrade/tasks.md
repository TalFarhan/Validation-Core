---
description: "Task list for the Alerts DB parity upgrade"
---

# Tasks: Alerts DB Parity Upgrade

**Input**: Design documents from `/specs/016-alerts-parity-upgrade/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/alerts-parity-engine.md, quickstart.md

**Tests**: Spec SC-002, SC-003, and SC-007 and the plan require `tests/unit/test_db_parity_engine.py`.
Write each story's unit tests first and confirm they fail before the matching implementation.
The live Alerts test stays `tests/ui/alerts_analysis_dashboard/test_db_parity.py`. Fleet smoke
is the Constitution III gate in polish. Do **not** edit `core/`. Do **not** add a pytest skip
for a missing Alerts database.

**Organization**: All six stories are P1. US1 (scoped KPI lookup) is the MVP. US2 adds gauge
value and maximum. US3 binds one `category_id` at a time. US4 compares chart rows. US5 removes
the date phrase from metric names. US6 adds the settlements chart, the alerts map, and the
policy status text, with stub SQL that is executed. Unit tests do not need the portal.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US6)
- Exact file paths are included in each task

## Path Conventions

- Engine: `tests/helpers/db_parity_engine.py`
- Alerts SQL client: `db/clients/alerts.py`
- Domain contract and test: `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, `tests/ui/alerts_analysis_dashboard/test_db_parity.py`
- Alerts page (leave unchanged unless a visual is slicer-gated): `tests/ui/alerts_analysis_dashboard/page.py`
- Unit tests: `tests/unit/test_db_parity_engine.py`
- Catalog: `docs/COVERAGE_CATALOG.md`
- Untouched: `core/components/kpi.py`, `core/components/chart.py`, `core/components/visual.py`, `core/portal/`

---

## Phase 1: Setup (Baseline)

**Purpose**: Confirm the Layer 2 readers this feature calls already exist, and that no new package is required.

- [X] T001 Confirm `KPI.number`, `KPI.scale`, and `Chart.read` already accept `(title, scope=None)` in `core/components/kpi.py` and `core/components/chart.py`. Do not edit those files (FR-014, research.md R1)
- [X] T002 [P] Confirm `pyyaml` is already in `requirements.txt` and the `db_parity` marker is already in `pytest.ini`. Do not add a dependency or a marker

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contract loader, `ParityResult.check`, and the Alerts bind helper that every story uses. The compare loop still treats every loaded metric as a KPI scalar until the story phases.

**⚠️ CRITICAL**: No user-story reader work starts until the loader accepts the new keys and rejects illegal combinations.

### Tests for the loader

- [X] T003 [P] Add failing tests in `tests/unit/test_db_parity_engine.py` that call `validate_dashboard_generic` with a temporary YAML file and a fake `db_client`. Monkeypatch `tests.helpers.db_parity_engine.KPI` so no browser starts. Cover loader rules from `specs/016-alerts-parity-upgrade/contracts/alerts-parity-engine.md`: unknown `visual` raises `ValueError` naming the metric before any query; `visual: gauge` without `maximum_sql` raises; `maximum_sql` on `visual: kpi` raises; a metric missing `name` or `sql_query` raises; `series_index: -1` raises. A metric with only `name` and `sql_query` still loads as `kpi` (FR-002)

### Implementation

- [X] T004 Extend `_load_metrics` in `tests/helpers/db_parity_engine.py` to validate optional `visual` (default `kpi`), `scope`, `category_id`, `label` (accepted and ignored), `maximum_sql`, and `series_index` (`int >= 0`). Raise `ValueError` for the cases in T003. Keep returning the metric dicts. English comments only (per contracts/alerts-parity-engine.md, data-model.md MetricContract) — depends on T003
- [X] T005 Add `check: str = "value"` as the last field of `ParityResult` in `tests/helpers/db_parity_engine.py` so `ParityResult(name, ui_value, db_value, passed)` still constructs. Widen `ui_value` and `db_value` to `int | float | None`. Include `check` in the `AssertionError` text. Do not change the KPI compare loop yet (per data-model.md ParityCheck) — depends on T004
- [X] T006 [P] Add a private params helper on `AlertsDBRunner` in `db/clients/alerts.py` and give `scalar` the keyword `category_id: str | None = None`. Params always include `start_date` and `end_date`. Include `category_id` only when it is not `None`. Keep NULL → `0` and `text()` execution. Do not hardcode `'1'`, `'2'`, `'10'`, Hebrew, or SQL. English comments only (per research.md R5) — can proceed beside T003

**Checkpoint**: Illegal contracts fail at load. Existing KPI metrics still compare through `KPI.number`. The runner accepts `category_id` and ignores it when the caller omits it.

---

## Phase 3: User Story 1 - Scoped visual lookup (Priority: P1) 🎯 MVP

**Goal**: A non-empty metric `scope` is passed to `KPI.number`. A missing, empty, or whitespace `scope` is passed as `None`.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py -v` with no browser. The scope cases pass. A fake KPI records the scope argument.

### Tests for User Story 1

- [X] T007 [P] [US1] Add failing tests in `tests/unit/test_db_parity_engine.py`. Monkeypatch `KPI.number` to record `(title, scope)` and return a fixed number. Fake `scalar` returns that same number. Assert a metric `scope: "Section A"` is forwarded unchanged, and that missing `scope`, `scope: ""`, and whitespace `scope` are forwarded as `None`. Assert `log_assertion` is not required for this unit test. Use a synthetic scope string, not a report title (FR-001, SC-003) — depends on T005

### Implementation for User Story 1

- [X] T008 [US1] In the KPI branch of `validate_dashboard_generic` in `tests/helpers/db_parity_engine.py`, normalize scope (missing, `""`, or whitespace → `None`) and call `kpi.number(name, scope=scope)`. Put `scope` into `log_assertion` filters when it is not `None`. Do not rewrite `name`. Do not read `label`. English comments only (per contracts/alerts-parity-engine.md section 1, research.md R1) — depends on T007
- [X] T009 [US1] Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm the loader tests and the scope tests pass (SC-003) — depends on T008

**Checkpoint**: Scoped KPI lookup is independently testable. Gauges, charts, and category binds are not wired yet.

---

## Phase 4: User Story 2 - Gauge value and denominator (Priority: P1)

**Goal**: `visual: gauge` uses `KPI.scale` and checks both `value` and `maximum`. `KPI.number` stays the reader for `visual: kpi`.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py -v`. A gauge whose value matches and whose maximum does not match fails. UI `0` equals DB `0`. An empty scale fails.

### Tests for User Story 2

- [X] T010 [P] [US2] Add failing tests in `tests/unit/test_db_parity_engine.py`. Monkeypatch `KPI.scale` to return a `GaugeScale` dict and assert `KPI.number` is not called for `visual: gauge`. Cases: value `5` vs scalar `5` and maximum `10` vs `maximum_sql` scalar `9` → `AssertionError` that names `check` `maximum` and still records the passing value check; both sides wrong → the error lists both checks; value `0` and maximum `0` pass; `state="empty"` with `value=None` fails the value check; `maximum=None` fails the maximum check. Fake `scalar` must be able to return different numbers for `sql_query` and `maximum_sql` (FR-004, SC-002) — depends on T005

### Implementation for User Story 2

- [X] T011 [US2] In `tests/helpers/db_parity_engine.py`, branch on `visual == "gauge"`: call `kpi.scale(name, scope=scope)`, run `sql_query` and `maximum_sql` through `db_client.scalar` with the same dates, and append two `ParityResult` rows (`check="value"` and `check="maximum"`). Fail the value check when `state == "empty"` or `value is None`. Fail the maximum check when `maximum is None`. Do not call `KPI.number` on this branch. Log both reads with `log_kpi_read` and both checks with `log_assertion` when a run report is active. Keep exact `==`. English comments only (per research.md R3, contracts/alerts-parity-engine.md) — depends on T010
- [X] T012 [US2] In `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, add `visual: gauge` metrics only when the report title, `scope`, `sql_query`, and `maximum_sql` are known from the report or warehouse. Use binds `:start_date`, `:end_date`, and `:category_id` when the metric sets `category_id`. English comments only. Do not invent a Hebrew title or a denominator query. If they are not known yet, add one English comment that gauge metrics are added when the title and maximum query are confirmed, and add no fake metric (research.md R9) — depends on T011
- [X] T013 [US2] Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm the gauge cases pass, including a maximum mismatch while the value matches (SC-002) — depends on T011

**Checkpoint**: Gauge parity is covered without a portal. Live gauge rows wait on confirmed titles.

---

## Phase 5: User Story 3 - One category at a time (Priority: P1)

**Goal**: Ids `1`, `2`, and `10` are validated separately. Each query binds `:category_id`. The grouped `CategoryID IN ('1', '2', '10')` predicate is gone. The engine does not know the UAV / Rockets / Terrorists pairing.

**Independent Test**: The unit test shows `category_id: 1` is forwarded as `"1"` and a metric with no `category_id` does not pass that kwarg. The Alerts contract contains one metric per id for each of the two existing measures.

### Tests for User Story 3

- [X] T014 [P] [US3] Add failing tests in `tests/unit/test_db_parity_engine.py`. The fake runner records `scalar` keywords. YAML `category_id: 1` is forwarded as the string `"1"` together with `start_date` and `end_date`. A metric with no `category_id` calls `scalar` without that keyword. Assert the engine never reads a `label` field (change the label and the call stays the same) (FR-006, FR-008, research.md R4) — depends on T006, T008

### Implementation for User Story 3

- [X] T015 [US3] In `tests/helpers/db_parity_engine.py`, stringify a present `category_id` with `str(...)` and pass it to `scalar` (and later `rows`) only when the metric sets it. Omit the keyword when it is missing or blank. Include `category_id` in `log_assertion` filters when set. Do not embed `'1'`, `'2'`, `'10'`, or the words UAV, Rockets, or Terrorists (FR-006, FR-008) — depends on T014
- [X] T016 [US3] Rewrite `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` so each of the two current measures exists once per id `"1"`, `"2"`, and `"10"` (six KPI metrics). Replace `CategoryID IN ('1', '2', '10')` with `AND CategoryID = :category_id`. Keep the existing `COUNT(DISTINCT [WarningZoneName])` query and the existing `ISNULL` / per-`LesserWarningAreaID` population query. Set `visual: kpi`. Leave `label` unset. Add an English comment that the UAV / Rockets / Terrorists pairing is filled only after it is confirmed and that the engine ignores `label`. Preserve any real gauge metrics from T012. English comments only (FR-007, research.md R4) — depends on T012
- [X] T017 [US3] Leave `tests/ui/alerts_analysis_dashboard/page.py` unchanged. In `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, keep a single `validate_dashboard_generic` call and do not pass category ids as engine arguments. Add an English comment that ids travel in the YAML. Add an `AlertsAnalysisPage` slicer method and a test loop only if a visual is absent until a category control is selected; otherwise do not add that method (research.md R8) — depends on T015
- [X] T018 [US3] Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm category forwarding passes (FR-006) — depends on T015

**Checkpoint**: KPI metrics for the three ids are declared separately. Chart rows are not compared yet.

---

## Phase 6: User Story 4 - Chart rows against the warehouse (Priority: P1)

**Goal**: `visual: chart` compares `Chart.read` categories to `AlertsDBRunner.rows` by label. SQL NULL stays `None`. An empty visual matches no rows.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py -v`. Label matches pass, a one-sided label fails, `None` matches NULL, and an empty visual fails when the query returns rows.

### Tests for User Story 4

- [X] T019 [P] [US4] Add failing tests in `tests/unit/test_db_parity_engine.py`. Monkeypatch `tests.helpers.db_parity_engine.Chart.read` to return a `ChartReading` (`categories` of `ChartCategory`, `series`, `state`) with no browser. Fake `rows` returns `(label, value)` tuples. Cases from data-model.md: matching labels pass using `values[0]`; `series_index: 1` reads the second cell; a label only on the UI or only in the rows fails; duplicate labels fail; cell `None` with SQL `None` passes; `state="empty"` and `rows=[]` passes; `state="empty"` with a row fails; categories with `rows=[]` fails; `series_index` past the row fails (FR-005, research.md R6) — depends on T005

### Implementation for User Story 4

- [X] T020 [US4] Add `AlertsDBRunner.rows` in `db/clients/alerts.py` using the T006 params helper. Return `list[tuple[str, int | float | None]]`: stripped string label, then the numeric cell. SQL NULL value stays `None` (do not reuse scalar's NULL → `0`). A NULL or blank label raises `ValueError`. Log `log_db_query` with method `alerts.rows`. Read-only `text()` only. English comments only (per contracts/alerts-parity-engine.md section 2) — depends on T006, T019
- [X] T021 [US4] In `tests/helpers/db_parity_engine.py`, build one `Chart` next to the existing `KPI` from `page.page` and `page._report_frame()`. For `visual: chart`, call `chart.read(name, scope=scope)` and `db_client.rows` with the same date and `category_id` rules as `scalar`. Match by label, compare `values[series_index]` (default `0`), and append one `ParityResult` per label in the union. Apply the empty, duplicate, and out-of-range rules from data-model.md. Log each check with `log_assertion`. English comments only (FR-005) — depends on T019, T020
- [X] T022 [US4] In `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, add `visual: chart` metrics only for titles and scopes copied from the report, one per confirmed chart and category id, with a two-column `SELECT` (label, value), `GROUP BY` the label, and the same date and `:category_id` binds. Default `series_index` may be omitted. Do not invent a Hebrew title. If no chart title is confirmed, add one English comment that chart metrics are added when the title and label column are confirmed (research.md R9) — depends on T016, T021
- [X] T023 [US4] Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm the chart cases pass (FR-005) — depends on T021

**Checkpoint**: Chart parity is covered without a portal. Live chart rows wait on confirmed titles.

---

## Phase 7: User Story 5 - Metric names survive a slicer change (Priority: P1)

**Goal**: Contract `name` values are stable anchors. The 30-day slicer option and the half-open window stay in the test. The engine does not append a date phrase to a title.

**Independent Test**: No metric `name` in `alerts_contract.yaml` contains `שלושים יום אחרונים`. `test_db_parity.py` still selects that option and passes `start_date` / `end_date`.

### Implementation for User Story 5

- [X] T024 [US5] In `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, drop the suffix ` בשלושים יום האחרונים` from every metric `name`. The two KPI anchors become `אזורי התרעה תחת ירי` and `אוכלוסייה מותרעת` (keep the contract's current spelling aside from that suffix). Apply the same rule to any gauge or chart `name` added in T012 or T022. Do not put the slicer option into `name`, `scope`, or SQL (FR-009, research.md R7) — depends on T016, T022
- [X] T025 [US5] In `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, keep `dashboard.select_date_range("שלושים יום אחרונים")` and the half-open window (`end_date = datetime.now()`, `start_date = end_date - timedelta(days=30)`). Pass those datetimes into `validate_dashboard_generic`. Add an English comment that another slicer option is a new option-plus-window in this file, not a renamed metric. Do not format dates into SQL (FR-009, SC-006) — depends on T017
- [X] T026 [US5] Add a test in `tests/unit/test_db_parity_engine.py` that loads `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` and asserts no metric `name` contains `שלושים יום`. Assert each of `"1"`, `"2"`, and `"10"` appears as `category_id` on the warning-zone metric and on the population metric, and that the file text has no `CategoryID IN` (SC-001, SC-006) — depends on T024

**Checkpoint**: The contract can be reused with another date window without renaming metrics.

---

## Phase 8: User Story 6 - Remaining report visuals (Priority: P1)

**Goal**: The Alerts contract covers the top-10 settlements chart, the alerts map, and the policy-classification status. Those three queries are the stub constants in `db/clients/alerts.py` and are executed. A missing database fails the live test. The test is not skipped.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py -v` with no browser. Map `0` is `value`, a map with no number and no marks is `empty`, and the string `placeholder` fails the presence check. A text KPI compares strings and does not call `KPI.number`. The contract file contains the three anchors. `test_db_parity.py` contains no skip.

### Tests for User Story 6

- [X] T032 [US6] In `tests/unit/test_db_parity_engine.py`, change the illegal-visual fixture from `visual: map` to `visual: sankey` so `map` is no longer the unknown token. Add failing loader cases: `compare: text` on `visual: gauge`, `visual: chart`, and `visual: map` raises `ValueError` naming the metric before any query; `compare: other` raises; `maximum_sql` on `visual: map` raises; `visual: map` with only `name` and `sql_query` loads. Extend `FakeDB` with `cell(sql, **kwargs)` that records the call and returns a scripted cell (per contracts/alerts-parity-engine.md, spec edge cases) — depends on T003
- [X] T033 [P] [US6] Add failing tests in `tests/unit/test_db_parity_engine.py` for map presence and text KPI. Monkeypatch a private reader (the function T035 will add, for example `_read_map_state`) so no browser starts, and call the real `classify_presence` for the state table. Cases: numbers `[0]` and mark count `0` yield UI `value` and pass when `cell` returns `0` with `check="presence"`; numbers `[None]` and mark count `0` yield `empty` and pass when `cell` returns `None`; the same empty visual fails when `cell` returns `"placeholder"`, and the `AssertionError` shows that raw string rather than `empty` or `0`; mark count `2` with no number yields `value`. For text: monkeypatch `KPI.read_text` to return a status phrase, assert `KPI.number` is not called, a matching `cell` passes, and `cell` `"placeholder"` fails with both strings in the error. Use a synthetic status string in this file, not a report title inside the engine (FR-002a, FR-002b, SC-007, research.md R14, R15) — depends on T032

### Implementation for User Story 6

- [X] T034 [P] [US6] In `db/clients/alerts.py`, add `AlertsDBRunner.cell` using the existing params helper. Return the first column only: SQL NULL stays `None` (not `0`), a string is stripped, a number uses the same coercion as `scalar`. Log `log_db_query` with method `alerts.cell`. Add module-level constants with no Hebrew and no category ids: `SETTLEMENTS_CHART_SQL = "SELECT 'placeholder' AS category_label, CAST(NULL AS int) AS metric_value"`, `MAP_PRESENCE_SQL = "SELECT 'placeholder'"`, `POLICY_STATUS_SQL = "SELECT 'placeholder'"`. Do not catch connection errors. English comments only (FR-016, research.md R16, contracts/alerts-parity-engine.md section 2) — depends on T006
- [X] T035 [US6] In `tests/helpers/db_parity_engine.py`, accept `visual: map` and `compare` `number` (default) or `text` (`text` only on `kpi`). Reject the loader cases from T032. Widen `ParityResult.ui_value` and `db_value` to `int | float | str | None`. For `compare: text`, call `kpi.read_text(name, scope=scope)`, strip bidi marks, collapse whitespace, compare to `db_client.cell`, and do not call `KPI.number`. For `visual: map`, locate the container with `scope_host` plus the same generic visual-container fallback `Chart` uses, count marks with `count_data_marks`, pass `[parsed number]` including `0` or `[None]`, and call `classify_presence`. Map `cell()` `None` to `empty`, numeric `0` and any other number to `value`, and any other cell (including `"placeholder"`) to a failed check whose `db_value` is that raw cell. Check name is `presence`. Import those helpers from `core.components.visual`. Do not add a `Map` class and do not edit `core/`. Log `log_assertion`. English comments only (FR-002, FR-002a, FR-002b, FR-014, research.md R14, R15) — depends on T032, T034
- [X] T036 [US6] In `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`, add three metrics and no `category_id`. Chart `name` is `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` with `visual: chart` and `sql_query` equal to `SETTLEMENTS_CHART_SQL`. Map `name` is `מפת התרעות ביישובים` with `visual: map` and `sql_query` equal to `MAP_PRESENCE_SQL`. Policy `name` is `סיכון לפי מדיניות התגוננות ברגע` with `visual: kpi`, `compare: text`, and `sql_query` equal to `POLICY_STATUS_SQL`. If that chart anchor matches two visuals, extend only the ranking chart `name` with stable words that are not `שלושים יום אחרונים`. Do not add the period-comparison chart. Replace the English comment that chart metrics wait on a confirmed title. English comments only (FR-009, FR-015, FR-016, research.md R12, R13) — depends on T024, T034, T035
- [X] T037 [P] [US6] In `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, add an English comment that a missing or refusing Alerts database must fail this test. Do not add `pytest.skip`, `pytest.importorskip`, `pytest.mark.skip`, or a `try`/`except` around `validate_dashboard_generic`. Do not change the slicer option or the half-open window (FR-017, SC-007) — depends on T025
- [X] T038 [US6] In `tests/unit/test_db_parity_engine.py`, load `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` and assert the three T036 metrics exist with those `visual` / `compare` values and that each `sql_query` equals the matching constant imported from `db/clients/alerts.py`. Assert no metric `name` contains `שלושים יום`. Read `tests/ui/alerts_analysis_dashboard/test_db_parity.py` and assert its source has no `pytest.skip`, `importorskip`, or `mark.skip` (SC-006, SC-007) — depends on T033, T035, T036, T037
- [X] T039 [US6] Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm the loader, map, text, and contract cases pass (SC-007) — depends on T035, T038

**Checkpoint**: The three visuals are in the contract and covered by unit tests. The live test still fails when the Alerts database is missing, and that failure is not skipped.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Catalog, leakage check, and the regression gates from quickstart.md.

- [X] T027 [P] Update section 8 of `docs/COVERAGE_CATALOG.md` so each Alerts measure lists visual kind, category id, SQL shape (`CategoryID = :category_id`), and `tests/ui/alerts_analysis_dashboard/test_db_parity.py`. Titles match the contract anchors from T024, including gauge and chart rows that were actually added. Note any category that has no confirmed gauge or chart (FR-012, Constitution V) — depends on T024, T026
- [X] T028 [P] Run `git diff -- core/components core/portal` and confirm it is empty for this feature. Run `rg "שלושים יום" tests/ui/alerts_analysis_dashboard` and confirm the phrase is only in `tests/ui/alerts_analysis_dashboard/test_db_parity.py` (and `page.py` only if an existing comment quotes the option), not in a metric `name` (SC-004, SC-006) — depends on T024, T025
- [X] T029 Run `python -m pytest tests/unit/test_db_parity_engine.py -v` and confirm the whole file passes (quickstart.md step 1) — depends on T009, T013, T018, T023, T026
- [X] T030 Run `python -m pytest tests/ui/fleet_dashboard/` and confirm 100% pass. This feature does not change Layer 0 or Layer 2; the run is the Constitution III non-regression gate (SC-005) — depends on T029
- [X] T031 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity -v` when a portal session and `DB_ALERTS_NAME` are available. Expect UI equals DB per category id. The settlements chart, map, and policy metric execute their stub SQL. If the Alerts database is missing, the same command must fail with the connection error and must not be skipped (quickstart.md step 3, SC-001, SC-007, FR-017) — depends on T027, T030, T039, T040
- [X] T040 [P] Update section 8 of `docs/COVERAGE_CATALOG.md` with the three T036 anchors: settlements chart (`chart`, stub `SETTLEMENTS_CHART_SQL`), alerts map (`map`, stub `MAP_PRESENCE_SQL`), and policy status (`kpi` / text, stub `POLICY_STATUS_SQL`). Mark the SQL as unconfirmed placeholder, not as a warehouse measure. Keep the existing per-id KPI rows (FR-012, Constitution V) — depends on T036
- [X] T041 [P] Run `git diff -- core/components core/portal` and confirm it is still empty. Confirm `db/clients/alerts.py` stub constants contain no Hebrew and no ids `'1'`, `'2'`, or `'10'` (SC-004, AC-005) — depends on T034, T035

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Stories (Phases 3–8)**: Depend on Foundational. Unit-test work for US1, US2, US4, and US6 can proceed after Phase 2. Live YAML edits are ordered so they do not collide: US2 comment-or-real gauges (T012) → US3 split (T016) → US4 chart entries (T022) → US5 rename (T024) → US6 remaining visuals (T036).
- **Polish (Phase 9)**: Depends on the stories required for the gate being run. T031 waits on US6.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Phase 2. No dependency on US2–US5. MVP.
- **User Story 2 (P1)**: Unit tests start after Phase 2. Gauge YAML (T012) is skipped rather than invented when titles are unknown, so the unit test is the independent proof.
- **User Story 3 (P1)**: Engine forwarding starts after US1's KPI call shape (T008) so scope and `category_id` land in one compare path. The runner helper (T006) is already in Phase 2.
- **User Story 4 (P1)**: `rows` starts after T006. The chart branch starts after the gauge branch (T011) because both edit `validate_dashboard_generic`.
- **User Story 5 (P1)**: Renames happen after KPI, gauge, and chart entries exist (T016, T022) so one pass strips every date suffix.
- **User Story 6 (P1)**: Starts after US4's chart branch and US5's stable names (T021, T024). `cell` and the stub constants (T034) do not require the engine branch. The map and text branches (T035) edit `tests/helpers/db_parity_engine.py` after the gauge and chart branches.

### Within Each User Story

- Unit tests are written and fail before the implementation they describe.
- Loader and `ParityResult` exist before story branches.
- `AlertsDBRunner` bind helper exists before `category_id` forwarding and before `rows`.
- Story unit tests pass before the next story's implementation edits the same file.

### Parallel Opportunities

- T002 beside T001.
- T003 beside T006 (test file vs `db/clients/alerts.py`).
- T007, T010, T014, and T019 each add cases to `tests/unit/test_db_parity_engine.py`. Do not edit that file in parallel; run those test tasks one after another.
- T020 (`db/clients/alerts.py`) can be written while T019's test is already in place, and does not require the engine chart branch.
- T027 beside T028 after the contract and test file are stable.
- T033 beside T034 (unit tests vs `db/clients/alerts.py`) after T032. Do not edit `tests/unit/test_db_parity_engine.py` in parallel with T032 or T038.
- T037 beside T036 (`test_db_parity.py` vs the YAML) after T035.
- T040 beside T041 after T036.

---

## Parallel Example: User Story 3

```text
# Different files, after Phase 2 and T008:
Task: "T014 [US3] category_id unit tests in tests/unit/test_db_parity_engine.py"
Task: "T006 AlertsDBRunner category_id helper in db/clients/alerts.py"  # already done in Phase 2

# Not parallel (same YAML file, ordered):
Task: "T012 [US2] gauge entries in alerts_contract.yaml"
Task: "T016 [US3] per-id KPI metrics in alerts_contract.yaml"
Task: "T022 [US4] chart entries in alerts_contract.yaml"
Task: "T024 [US5] strip date suffixes in alerts_contract.yaml"
Task: "T036 [US6] settlements chart, map, and policy metrics in alerts_contract.yaml"
```

## Parallel Example: User Story 6

```text
# Different files, after T032:
Task: "T033 [US6] map and text KPI unit tests in tests/unit/test_db_parity_engine.py"
Task: "T034 [US6] AlertsDBRunner.cell and stub SQL constants in db/clients/alerts.py"

# Different files, after T035:
Task: "T036 [US6] three metrics in alerts_contract.yaml"
Task: "T037 [US6] no-skip comment in test_db_parity.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (T007–T009).
3. **STOP and VALIDATE**: `python -m pytest tests/unit/test_db_parity_engine.py -v`.
4. Scope is forwarded. The live contract is still the grouped 30-day pilot until later stories.

### Incremental Delivery

1. Setup + Foundational → loader and bind helper ready.
2. US1 → scoped `KPI.number` (MVP).
3. US2 → gauge value and maximum in the engine.
4. US3 → one `category_id` per KPI metric in the Alerts contract.
5. US4 → chart rows.
6. US5 → date phrase removed from names; slicer option stays in the test.
7. US6 → settlements chart, map presence, policy text, and executed stub SQL. A missing database still fails the live test.
8. Polish → catalog rows for the stubs, empty `core/` diff, fleet smoke, live `db_parity` when credentials exist.

### Parallel Team Strategy

1. One person completes Phase 1 and Phase 2.
2. After that, engine stories still share `tests/helpers/db_parity_engine.py`, so implement US1 → US2 → US4's engine branch in that order.
3. A second person can own `db/clients/alerts.py` (T006, T020, then T034) and the YAML sequence (T012 → T016 → T022 → T024 → T036) without editing `core/`.

---

## Notes

- [P] tasks use different files and do not depend on an unfinished task.
- Do not edit `core/components/` or `core/portal/`.
- Do not assign UAV, Rockets, or Terrorists to ids `1`, `2`, or `10` in the engine or the runner. `label` in the YAML stays empty until the pairing is confirmed.
- Do not invent Hebrew visual titles beyond the three anchors in research.md R12, and do not invent denominator SQL.
- Do not add `pytest.skip`, `pytest.importorskip`, or `pytest.mark.skip` to `tests/ui/alerts_analysis_dashboard/test_db_parity.py`.
- Inline comments in edited Python and YAML are English only.
- `0` is a real gauge value, a real maximum, and a present map (`value`). Chart SQL NULL stays `None`. Scalar NULL stays `0`. `cell()` NULL stays `None`.
