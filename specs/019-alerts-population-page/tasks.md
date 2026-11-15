---
description: "Task list for the Alerts population page"
---

# Tasks: Alerts Population Page

**Input**: Design documents from `/specs/019-alerts-population-page/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/population-page.md, quickstart.md

**Tests**: The spec's independent tests are the deliverable. Write each story's unit test first
and confirm it fails before the matching production edit. UI tests live in
`tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and are not marked `db_parity`.
Do **not** edit `core/`. Do **not** add a pytest skip or a `try`/`except` around the Alerts
database connection. Fleet smoke is not a gate unless `core/` or `pages/fleet_dashboard/` changes.

**Organization**: US1–US4 are P1. US5 is P2. US1 (open page 2) is the MVP. US2 appends contract
rows and must land the page-1 `exclude_scopes` call in the same story so placeholders are not
executed on page 1. US3 and US5 touch different files and can proceed in parallel after US2.
US4 extends the US3 page methods.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths are included in each task

## Path Conventions

- Page 2: `pages/alerts_analysis/population_page.py` (`AlertsPopulationPage`)
- Page 1 (do not edit): `pages/alerts_analysis/page.py` (`AlertsAnalysisPage`)
- Contract: `data/alerts/alerts_contract.yaml`
- Alerts SQL client: `db/clients/alerts.py`
- Engine: `tests/helpers/db_parity_engine.py` (`exclude_scopes` keyword only)
- Suite fixtures: `tests/ui/alerts_analysis_dashboard/conftest.py`
- Snapshot helper: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- UI tests: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- Page-1 parity: `tests/ui/alerts_analysis_dashboard/test_db_parity.py`
- Unit tests: `tests/unit/test_population_page.py`, `tests/unit/test_db_parity_engine.py`
- Catalog: `docs/COVERAGE_CATALOG.md`
- Untouched: `core/portal/`, `core/components/`, `pages/fleet_dashboard/`

---

## Phase 1: Setup (Baseline)

**Purpose**: Confirm this slice needs no new package and does not start from a second contract file.

- [X] T001 Confirm `pytest`, `playwright`, and `pyyaml` are already in `requirements.txt`. Do not add a dependency or a pytest marker. Confirm the alerts contract path is `data/alerts/alerts_contract.yaml` and `pages/alerts_analysis/page.py` still defines `AlertsAnalysisPage`. Do not edit `core/` (plan.md Technical Context)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Let the parity engine skip a scope before any page-2 row exists. No story starts until this keyword is in place.

**⚠️ CRITICAL**: No user-story YAML work starts until `exclude_scopes` is implemented and its unit test passes.

- [X] T002 Confirm `AlertsDBRunner.scalar` and `AlertsDBRunner.rows` in `db/clients/alerts.py` still bind `start_date` and `end_date` through SQLAlchemy `text()`, include `category_id` only when the caller passes it, and that `__init__` calls `create_db_engine` with no `try`/`except`. Do not change method signatures and do not add a runner method (research.md R8, AC-006)
- [X] T003 [P] Add a failing `test_exclude_scopes_skips_matching_metrics` in `tests/unit/test_db_parity_engine.py`. Use the existing `FakePage`, `FakeDB`, `FakeKPI`, and `_write` helper. Monkeypatch `tests.helpers.db_parity_engine.KPI` the way the other tests do. Write a temporary YAML with two `visual: kpi` metrics, scopes `page-one` and `page-two`, both `sql_query: "SELECT 1"`. Call `validate_dashboard_generic` directly with `exclude_scopes={"page-two"}` (do not use `_run`; it drops extra keyword arguments). Assert one `scalar` call, for the `page-one` metric only, and that no result name is the `page-two` metric. Call again with `exclude_scopes` omitted and assert both metrics run. No browser (contracts/population-page.md §5, research.md R7, FR-014)
- [X] T004 Add optional keyword `exclude_scopes: Collection[str] | None = None` after the existing positional parameters of `validate_dashboard_generic` in `tests/helpers/db_parity_engine.py`. `None` or an empty collection excludes nothing. When a metric's `_normalize_scope` value is in the set, skip it: no UI read, no SQL call, no `ParityResult`. Do not add Hebrew. Keep `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` valid for existing callers (research.md R7, contracts/population-page.md §5) — depends on T003
- [X] T005 Run `python -m pytest tests/unit/test_db_parity_engine.py::test_exclude_scopes_skips_matching_metrics -v` and confirm it passes (research.md R7) — depends on T004

**Checkpoint**: The engine can ignore one scope. Page-1 parity is unchanged until a caller passes `exclude_scopes`.

---

## Phase 3: User Story 1 - Open the population page from the alerts report (Priority: P1) 🎯 MVP

**Goal**: The population suite opens catalog product `ניתוח התרעות` and selects the second report page. Page-1 tests still open the first page.

**Independent Test**: `python -m pytest tests/unit/test_population_page.py::test_population_page_module -v` with no browser. `AlertsPopulationPage` subclasses `AlertsAnalysisPage`, `PAGE_TITLE` is the live tab name, and `conftest.py` binds `population_dashboard` without retargeting `dashboard`. With a saved portal session, `test_population_suite_opens_second_page` shows `התרעות לפי מחוז` before any later assertion.

### Tests for User Story 1

- [X] T006 [US1] Add a failing `test_population_page_module` in `tests/unit/test_population_page.py`. Import `AlertsPopulationPage` from `pages/alerts_analysis/population_page.py` and `AlertsAnalysisPage` from `pages/alerts_analysis/page.py`. Assert the population class subclasses the page-1 class. Assert `DISTRICT_CHART == "התרעות לפי מחוז"`. Assert `PAGE_TITLE` is a non-empty string, does not contain `בין`, and is not equal to and not a substring of `ירי רקטות וטילים`, `חדירת מחבלים`, `חדירת כלי טיס עוין`, `אוכלוסייה מותרעת`, or `אזורי התרעה תחת ירי` (and none of those is a substring of `PAGE_TITLE`). Read `tests/ui/alerts_analysis_dashboard/conftest.py` and assert it still binds `dashboard` to `AlertsAnalysisPage` and also binds `population_dashboard` to `AlertsPopulationPage`. No browser (FR-001, FR-002, SC-001, research.md R1, data-model.md §1)

### Implementation for User Story 1

- [X] T007 [US1] Create `pages/alerts_analysis/population_page.py` with `class AlertsPopulationPage(AlertsAnalysisPage)`. Set `PAGE_TITLE` to the accessible name of the second report-page tab, copied from the live report per `specs/019-alerts-population-page/quickstart.md` section 1. Do not invent that Hebrew string. Set `DISTRICT_CHART = "התרעות לפי מחוז"`. Override `before_report_ready_check` so it selects the `PAGE_TITLE` tab and is safe to call twice. Override `_report_ready_locator` to `self._iframe_phrase_locator(self.DISTRICT_CHART)`, not the catalog product name. Do not reimplement login, catalog search, iframe wait, visual-load timeout, or last-refresh. Do not edit `pages/alerts_analysis/page.py`. English comments only (FR-001, FR-002, AC-002, AC-003, research.md R1, R2, contracts/population-page.md §1) — depends on T006
- [X] T008 [US1] In `tests/ui/alerts_analysis_dashboard/conftest.py`, add `population_dashboard = bind_dashboard(AlertsPopulationPage)` and import `AlertsPopulationPage` from `pages.alerts_analysis.population_page`. Leave `dashboard = bind_dashboard(AlertsAnalysisPage)` unchanged (FR-001, AC-004, contracts/population-page.md §2) — depends on T007
- [X] T009 [US1] Run `python -m pytest tests/unit/test_population_page.py::test_population_page_module -v` and confirm it passes (SC-001) — depends on T008
- [X] T010 [US1] Add `test_population_suite_opens_second_page` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Request `population_dashboard` only. Assert the district anchor `התרעות לפי מחוז` is visible inside the report iframe and that the `PAGE_TITLE` tab is selected. Do not request `alerts_db`. Do not mark `db_parity`. Run it when `auth_state.json` is present: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_population_suite_opens_second_page -v` (FR-001, SC-001, quickstart.md §4) — depends on T008

**Checkpoint**: Population tests land on page 2. Page-1 `dashboard` still constructs `AlertsAnalysisPage`.

---

## Phase 4: User Story 2 - Contract rows cannot collide with page 1 (Priority: P1)

**Goal**: Every new metric uses `PAGE_TITLE` as `scope`. Names are stable prefixes. The settlement chart is two series. Page-1 parity does not execute these rows.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py::test_population_contract_scope -v` with no browser. Eight page-2 metrics share `PAGE_TITLE`. No page-2 name contains `בין`. Page-1 metrics are still in the file. `test_db_parity.py` passes `exclude_scopes`.

### Tests for User Story 2

- [X] T011 [US2] Add a failing `test_population_contract_scope` in `tests/unit/test_db_parity_engine.py`. Load `data/alerts/alerts_contract.yaml` with `yaml.safe_load`. Import `AlertsPopulationPage` inside the test. Assert every metric with `scope == AlertsPopulationPage.PAGE_TITLE` has that exact scope and a `name` that does not contain `בין`. Assert these rows exist: `התרעות לפי מחוז` with `visual == "chart"` and no `series_index`; two rows named `אוכלוסייה לפי יישוב` with `series_index` values `0` and `1` and `label` values `מותרעות` and `לא מותרעות` (swap the expected indexes only if T012 recorded a reversed legend); three `visual: kpi` cards with distinct names; two further `visual: chart` rows for the 24-hour chart and the dates chart. Assert no page-2 metric sets `category_id` or `maximum_sql`. Assert `PAGE_TITLE` does not collide with the page-1 scopes listed in `specs/019-alerts-population-page/data-model.md` section 1. Assert page-1 rows are still present: the six category KPIs, `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`, `מפת התרעות ביישובים`, `סיכון לפי מדיניות התגוננות ברגע`, the time-bucket cards, and `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת`. Do not rename that static chart. No browser (FR-003, FR-004, FR-005, FR-006, SC-002, data-model.md §2) — depends on T009

### Implementation for User Story 2

- [ ] T012 [US2] Copy the live 24-hour chart title, dates chart title, and three card titles onto constants on `AlertsPopulationPage` in `pages/alerts_analysis/population_page.py`, using the `בין` cut in `specs/019-alerts-population-page/data-model.md` section 2.3. Confirm a `role=group` whose accessible name matches `PAGE_TITLE` contains `התרעות לפי מחוז`. If it does not, stop. Do not retarget `scope` and do not edit `core/components/visual.py`. Read `Chart.read` legend order for `אוכלוסייה לפי יישוב`: index 0 must be `מותרעות` and index 1 `לא מותרעות`. If the live legend is reversed, record the swapped indexes for T013. English comments only (quickstart.md §1, research.md R3, R4) — depends on T007
- [X] T013 [US2] Append the page-2 metrics to `data/alerts/alerts_contract.yaml` in the shape in `specs/019-alerts-population-page/contracts/population-page.md` section 3. Every `scope` is the `PAGE_TITLE` string. District `name` is `התרעות לפי מחוז`. Settlement rows use the indexes from T012. Card `sql_query` text is `SELECT 0`. Chart `sql_query` text is `SELECT CAST(NULL AS nvarchar(200)) AS category_label, CAST(NULL AS int) AS metric_value WHERE 1 = 0`. Do not set `category_id` or `maximum_sql`. Do not rewrite page-1 metrics. English comments only (FR-003, FR-004, FR-005, FR-006, data-model.md §2) — depends on T011, T012
- [X] T014 [US2] In `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, pass `exclude_scopes={AlertsPopulationPage.PAGE_TITLE}` into `validate_dashboard_generic`. Import `AlertsPopulationPage` from `pages.alerts_analysis.population_page`. Do not add `pytest.skip`, `pytest.importorskip`, or `pytest.mark.skip`. Do not catch a connection error (FR-014, SC-005, contracts/population-page.md §5) — depends on T005, T013
- [X] T015 [US2] Run `python -m pytest tests/unit/test_db_parity_engine.py::test_population_contract_scope tests/unit/test_db_parity_engine.py::test_exclude_scopes_skips_matching_metrics -v` and confirm both pass (SC-002) — depends on T014

**Checkpoint**: Page-2 rows are scoped to the page title. The page-1 parity test will not execute them.

---

## Phase 5: User Story 3 - Clear returns the page to its arrival state (Priority: P1)

**Goal**: A snapshot of the three cards and the chart totals is restored exactly after between-dates, day/night, and the range 0–349.

**Independent Test**: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot -v` with a portal session. At least one snapshotted figure changes before clear. After clear, every figure matches the arrival snapshot, including zeros.

### Tests for User Story 3

- [X] T016 [US3] Add `test_clear_restores_population_snapshot` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Request `population_dashboard`. Call `take_snapshot`, then `set_between_dates`, `set_day_night("day")`, `set_day_night("night")`, and `set_value_range(0, 349)`. Assert at least one snapshot field changed. Call `clear_filters` and assert `same_snapshot` against the arrival snapshot. Do not import `AlertsDBRunner` or call `validate_dashboard_generic`. Do not mark `db_parity` (FR-007, FR-008, SC-003, contracts/population-page.md §6) — depends on T010

### Implementation for User Story 3

- [X] T017 [US3] On `AlertsPopulationPage` in `pages/alerts_analysis/population_page.py`, add `clear_filters` (calls `Slicer.clear_all`), `set_between_dates(start, end)`, `set_day_night(mode)` with modes `off`, `day`, and `night`, `set_value_range(low, high)`, `read_card(role)` for `total`, `warned`, and `unprotected` via `KPI.number(title, scope=PAGE_TITLE)`, and `chart_total(title, series_index=0)`. `chart_total` sums numeric cells from `Chart.read(title, scope=PAGE_TITLE)` and raises if `state == "empty"` or the selected series cell is `None`. Copy slicer accessible names from the live page onto constants. Do not add a `SlicerKind` and do not edit `core/components/slicer.py`. English comments only (research.md R5, R6, contracts/population-page.md §1, AC-005) — depends on T012, T016
- [X] T018 [US3] Add `PopulationSnapshot`, `take_snapshot`, and `same_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`. `take_snapshot` stores the three `read_card` values and totals for the 24-hour chart, the dates chart, the district chart, and both series of `אוכלוסייה לפי יישוב`, as in `specs/019-alerts-population-page/data-model.md` section 3. `same_snapshot` uses `==`, including zeros. The helper calls page methods only. Do not put it under `tests/helpers/` (FR-007, FR-012, research.md R5) — depends on T017
- [ ] T019 [US3] Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot -v` when `auth_state.json` is present and confirm it passes (SC-003, quickstart.md §4) — depends on T018

**Checkpoint**: Clear restores the arrival snapshot. The test fails if the slicers change nothing.

---

## Phase 6: User Story 4 - Distribution totals agree without the warehouse (Priority: P1)

**Goal**: Day plus night equals the untoggled dates total. The 24-hour, dates, and district Sum-mode totals match. Warned and unprotected populations are each at most the total.

**Independent Test**: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -k "day_plus_night or hour_date_and_district or population_cards_within_total or settlement_series" -v` with a portal session. No database connection.

### Tests for User Story 4

- [X] T020 [US4] Add these tests to `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, each using `population_dashboard` and no `alerts_db`: `test_day_plus_night_equals_untoggled_sum` asserts dates-chart `chart_total` for `set_day_night("day")` plus `set_day_night("night")` equals `set_day_night("off")`, with between-dates and the numeric range cleared; `test_hour_date_and_district_sums_match` calls `set_district_aggregation("sum")` on a cleared page and asserts the 24-hour total, the dates total, and the district total are equal; `test_population_cards_within_total` asserts warned `<=` total and unprotected `<=` total and does not assert those two parts sum to the total; `test_settlement_series_match_legend` asserts `Chart.read("אוכלוסייה לפי יישוב", scope=PAGE_TITLE).series[0] == "מותרעות"` and index 1 is `לא מותרעות`, matching the YAML indexes from T013. Do not coerce a missing cell to 0 (FR-009, FR-010, FR-011, FR-012, research.md R4, R6) — depends on T018

### Implementation for User Story 4

- [X] T021 [US4] Add `set_district_aggregation(mode)` on `AlertsPopulationPage` in `pages/alerts_analysis/population_page.py` for `sum` and `average`. The Sum control's accessible name stays a constant on this page. Do not edit `core/`. Average mode is not used by the new tests (data-model.md §5, contracts/population-page.md §1) — depends on T017, T020
- [ ] T022 [US4] Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -k "day_plus_night or hour_date_and_district or population_cards_within_total or settlement_series" -v` when `auth_state.json` is present and confirm all four pass (SC-004, quickstart.md §4) — depends on T021

**Checkpoint**: The four UI identities pass on one population-page session. No SQL is compared.

---

## Phase 7: User Story 5 - Warehouse stubs are named, not compared (Priority: P2)

**Goal**: Card and chart placeholders are named constants with the future SQL rules in comments. The new UI tests still do not call them. Page-1 parity still excludes this scope.

**Independent Test**: `python -m pytest tests/unit/test_db_parity_engine.py::test_population_page_stubs -v` with no browser. Card SQL is `SELECT 0`. Chart SQL returns no rows and does not mention the date window. `test_db_parity.py` has no skip marker.

### Tests for User Story 5

- [X] T023 [US5] Add a failing `test_population_page_stubs` in `tests/unit/test_db_parity_engine.py`. Import `POPULATION_PAGE_KPI_STUB_SQL` and `POPULATION_PAGE_CHART_STUB_SQL` inside the test function. Load `data/alerts/alerts_contract.yaml`. For every metric whose `scope` is `AlertsPopulationPage.PAGE_TITLE`, assert `" ".join(sql_query.split())` equals the card constant when `visual == "kpi"` and the chart constant when `visual == "chart"`. Assert the chart constant does not contain `AlertDate`, `:start_date`, or `:end_date`. Read `db/clients/alerts.py` and assert the comment block above the constants states half-open dates (`>=` and `<`), one grouping grain from district down to settlement, and Average as that sum divided by the group count. Read `tests/ui/alerts_analysis_dashboard/test_db_parity.py` and assert it contains `exclude_scopes` and does not contain `pytest.skip`, `importorskip`, or `mark.skip`. No browser (FR-013, FR-014, SC-006, research.md R4, R8) — depends on T015

### Implementation for User Story 5

- [X] T024 [US5] Add `POPULATION_PAGE_KPI_STUB_SQL = "SELECT 0"` and `POPULATION_PAGE_CHART_STUB_SQL` in `db/clients/alerts.py` using the exact chart text in `specs/019-alerts-population-page/contracts/population-page.md` section 4. Put the English comment block from that section above the constants. Do not reuse `POPULATION_KPI_STUB_SQL` or `PERIOD_COMPARISON_CHART_SQL`. Do not add a method on `AlertsDBRunner`. Do not add `try`/`except`. No Hebrew in this file (FR-013, FR-015, research.md R4, R8) — depends on T023
- [X] T025 [US5] Set each page-2 `sql_query` in `data/alerts/alerts_contract.yaml` to the text of the matching constant from T024. Do not change page-1 `sql_query` values. Do not add `:start_date` to the chart stub (FR-013, contracts/population-page.md §3) — depends on T024
- [X] T026 [US5] Run `python -m pytest tests/unit/test_db_parity_engine.py::test_population_page_stubs tests/unit/test_db_parity_engine.py::test_population_contract_scope tests/unit/test_population_page.py -v` and confirm they pass (SC-006) — depends on T025

**Checkpoint**: Placeholders are named and commented. They are still excluded from the page-1 parity run and unused by the UI identity tests.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Catalog the new rows and confirm shared layers stayed untouched.

- [X] T027 [P] In `docs/COVERAGE_CATALOG.md` section 8, add page-2 rows as UI identities plus unconfirmed placeholders. Name `pages/alerts_analysis/population_page.py`, `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, and the `exclude_scopes` exclusion on `tests/ui/alerts_analysis_dashboard/test_db_parity.py`. In that same section, replace the stale page path `tests/ui/alerts_analysis_dashboard/page.py` with `pages/alerts_analysis/page.py` (FR-016, contracts/population-page.md §8) — depends on T026
- [X] T028 Run `python -m pytest tests/unit/test_db_parity_engine.py tests/unit/test_population_page.py -v` and confirm the unit file passes (quickstart.md §2) — depends on T026
- [ ] T029 [P] Run `git diff -- core/ pages/fleet_dashboard/` and confirm it is empty. Do not run `pytest tests/ui/fleet_dashboard/` unless that diff is non-empty (plan.md Constitution Check, quickstart.md §3) — depends on T026
- [ ] T030 When `auth_state.json` is present, run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v`. When the Alerts database is configured, run `python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity -v` and confirm it does not query `POPULATION_PAGE_KPI_STUB_SQL` or `POPULATION_PAGE_CHART_STUB_SQL`. A missing database must still fail that test. Do not add a skip (quickstart.md §4, §5, SC-005) — depends on T019, T022, T026

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on US2–US5
- **User Story 2 (Phase 4)**: Depends on US1 (`PAGE_TITLE` and the page class)
- **User Story 3 (Phase 5)**: Depends on US2 (stable title constants)
- **User Story 4 (Phase 6)**: Depends on US3 (`chart_total`, `read_card`, snapshot helper)
- **User Story 5 (Phase 7)**: Depends on US2 (YAML rows and `exclude_scopes` on the page-1 test). Does not depend on US3 or US4
- **Polish (Phase 8)**: Depends on the stories required by each task

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational. MVP. Page 2 opens; page 1 fixture unchanged
- **User Story 2 (P1)**: After US1. Contract scope and page-1 exclusion
- **User Story 3 (P1)**: After US2. Clear snapshot. Can run beside US5
- **User Story 4 (P1)**: After US3. UI identities
- **User Story 5 (P2)**: After US2. Named placeholders. Can run beside US3 and US4

### Within Each User Story

- The failing test is written before the production edit it describes
- A story's run task is last in that phase
- US2 must update `test_db_parity.py` in the same story as the YAML append

### Parallel Opportunities

- T003 can run beside T002 (different files)
- After US2, US3 (`population_page.py` methods, `population_snapshot.py`, UI test) and US5 (`db/clients/alerts.py`, YAML SQL text, unit test) use different files and can proceed together
- T027 and T029 touch different files and can run together after T026
- US4 cannot run beside US3: both edit `pages/alerts_analysis/population_page.py` and `test_population_invariants.py`

---

## Parallel Example: User Story 5 beside User Story 3

```text
# After T015 (US2 checkpoint):
Task: "T016 [US3] failing clear test in tests/ui/alerts_analysis_dashboard/test_population_invariants.py"
Task: "T023 [US5] failing stub test in tests/unit/test_db_parity_engine.py"

# Then implementation stays on separate files:
Task: "T017 [US3] slicer and read methods in pages/alerts_analysis/population_page.py"
Task: "T024 [US5] placeholder constants in db/clients/alerts.py"
```

Do not start T021 while T017 is still editing `pages/alerts_analysis/population_page.py`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3 (User Story 1)
3. **STOP and VALIDATE**: `test_population_page_module` passes, and with a portal session the suite is on page 2 while `dashboard` still opens page 1

### Incremental Delivery

1. Setup + Foundational → scope exclusion exists, no page-2 rows yet
2. User Story 1 → page 2 opens (MVP)
3. User Story 2 → contract rows cannot collide with page 1, and page-1 parity ignores them
4. User Story 3 → clear restores the arrival snapshot
5. User Story 4 → day/night, cross-chart, and population bounds
6. User Story 5 → named placeholders and future SQL comments
7. Polish → catalog and the quickstart unit run

### Parallel Team Strategy

1. One person finishes Setup, Foundational, US1, and US2
2. Then one person takes US3 then US4, and another takes US5
3. Polish waits until both streams finish

---

## Notes

- `[P]` tasks use different files and do not depend on an unfinished task
- `[USn]` maps the task to `spec.md`
- Do not invent `PAGE_TITLE`, the hour-chart prefix, the dates-chart prefix, or the three card prefixes
- Do not point a chart metric at a one-column `SELECT 0`
- Do not edit `core/` or `pages/alerts_analysis/page.py`
- Commit after each phase if you want a review checkpoint
