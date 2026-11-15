# Tasks: YAML-Only UI Blockers

**Input**: Design documents from `specs/045-hour-chart-table-teardown/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/yaml-only-ui-blockers.md, quickstart.md

**Tests**: No new test files. The spec does not ask for TDD. Existing unit scans, alerts UI smoke, and YAML sanity are the checks. Fleet smoke is **not** a gate: `core/portal/page.py`, `ReportShell`, and `pages/fleet_dashboard/` are not edited (plan.md). This file replaces the page-switch task list. That click is already in the page and stays (US3).

**Organization**: Tasks are grouped by user story. US1, US2, and US4 edit `pages/alerts_analysis/population_page.py`, so those edits stay sequential. US3 and US5 only confirm methods this slice does not change. The SQL skip is foundational and uses different files.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US5 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Alerts population page: `pages/alerts_analysis/population_page.py`
- Alerts SQL parity test: `tests/ui/alerts_analysis_dashboard/test_db_parity.py`
- Parity unit scans: `tests/unit/test_db_parity_engine.py`
- YAML sanity (do not skip, do not edit): `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- Alerts golden record (do not edit): `data/alerts/db_sanity_am_kalavi.yaml`
- Alerts SQL contract (do not edit): `data/alerts/alerts_contract.yaml`
- OFF-LIMITS: `core/portal/`, `core/components/`, `pages/fleet_dashboard/`, `pages/status_picture/`, `pages/credit_consumption/`, `db/clients/alerts.py`, root `conftest.py`, every file under `data/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lock the edit list and record the three live sites before changing them

- [X] T001 Confirm the edit list in `specs/045-hour-chart-table-teardown/plan.md` and `specs/045-hour-chart-table-teardown/contracts/yaml-only-ui-blockers.md`: this slice may change `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, the three `mark.skip` scans in `tests/unit/test_db_parity_engine.py`, and `set_hierarchy_level`, `_title_anchor`, and the `HOUR_CHART` branch of `_leave_visual_table` in `pages/alerts_analysis/population_page.py`. Leave YAML, `db/clients/alerts.py`, `data/alerts/alerts_contract.yaml`, `_report_ready_locator`, `before_report_ready_check`, `read_hour_daily_avg`, `set_date_range`, `_assert_golden_keys`, and `core/` untouched.
- [X] T002 [P] Inventory without editing. In `pages/alerts_analysis/population_page.py`, record that `set_hierarchy_level` calls `control.click()` with no `force`, that `_title_anchor` uses `get_by_text(title).filter(visible=True)` then a visible group, and that `_leave_visual_table` ends with `expect(visible.first).to_be_visible` on `get_by_text(title).filter(visible=True)`. In `tests/unit/test_db_parity_engine.py`, record the three `assert "mark.skip" not in` lines inside `test_remaining_visuals_use_stub_sql`, `test_alerts_stubs_do_not_hide_connection_errors`, and `test_population_page_stubs`. In `tests/ui/alerts_analysis_dashboard/test_db_parity.py`, record the in-function comment that says a missing Alerts database must fail the test and must not be skipped (`specs/045-hour-chart-table-teardown/research.md` Decisions 1–4).

**Checkpoint**: Scope and the current click, title filter, and skip ban are known. No behavior change yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Stop alerts UI smoke from executing `[FACT].[AlertsRedWeb]` while the unit file still accepts the decorator

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Remove only `assert "mark.skip" not in source` and `assert "mark.skip" not in parity_source` from `test_remaining_visuals_use_stub_sql`, `test_alerts_stubs_do_not_hide_connection_errors`, and `test_population_page_stubs` in `tests/unit/test_db_parity_engine.py`. Keep `assert "pytest.skip" not in` and `assert "importorskip" not in` in each of those three tests. Do not change stub-SQL or `exclude_scopes` asserts in that file (`specs/045-hour-chart-table-teardown/contracts/yaml-only-ui-blockers.md`).
- [X] T004 [P] Add `@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")` above `@pytest.mark.db_parity` on `test_alerts_db_parity_last_30_days` in `tests/ui/alerts_analysis_dashboard/test_db_parity.py`. Leave the function body, including `validate_dashboard_generic` and `alerts_db`. Replace the in-function sentence that says a missing database must fail and must not be skipped with an English comment that the skip is temporary while YAML validation is the focus and that `data/alerts/alerts_contract.yaml` is unchanged. Do not add `pytest.skip(` or `importorskip`.

**Checkpoint**: The parity test is skipped. Unit scans still reject a body-level skip. YAML sanity is still collected.

---

## Phase 3: User Story 1 - Hour daily averages come from the alerts column (Priority: P1) 🎯 MVP

**Goal**: The hour chart titled `גרף התרעות וגם ממוצע לפי שעה` can be anchored when Playwright marks that title hidden, and `read_hour_daily_avg` still reads integer `התרעות` values only

**Independent Test**: With the golden date range applied, `read_hour_daily_avg()` returns the golden hour keys as integers taken from the `התרעות` column. The test reports pass/fail instead of skip when data is present. Finding the chart does not require `.filter(visible=True)` on `HOUR_CHART`.

### Implementation for User Story 1

- [X] T005 [US1] In `_title_anchor` in `pages/alerts_analysis/population_page.py`, keep the current visible-text then visible-group path for every title other than `self.HOUR_CHART`. For `HOUR_CHART` (`גרף התרעות וגם ממוצע לפי שעה`), prefer a visible text match when one exists; otherwise use `get_by_text(self.HOUR_CHART)` and then the exact group **without** `.filter(visible=True)`, and return the first match that has a `visualContainer` or `visual-container` ancestor. Do not return a hidden tooltip that has no such ancestor. If nothing is attached in a visual, raise `AssertionError` that the hour chart title is not attached. Add an English comment inside the function. Do not edit `read_hour_daily_avg` (`specs/045-hour-chart-table-teardown/contracts/yaml-only-ui-blockers.md`).
- [X] T006 [US1] Confirm `read_hour_daily_avg` in `pages/alerts_analysis/population_page.py` still calls `_press_average_on_chart(self.HOUR_CHART)` and `_visual_table_map(self.HOUR_CHART, "התרעות")`, and does not read a `ממוצע` header or round floats. Do not edit that method.

**Checkpoint**: User Story 1 can find the hour chart without a visible-title filter, and the alerts-column reader is unchanged.

---

## Phase 4: User Story 2 - Show-as-a-table always returns to the canvas (Priority: P1)

**Goal**: Back to report still runs in `finally`, and the hour chart's post-back wait does not require Playwright visibility

**Independent Test**: Force the table path to return `{}` or raise. After the call, the named visual is on the canvas again. For `HOUR_CHART`, that check is attached text, not `to_be_visible`.

### Implementation for User Story 2

- [X] T007 [US2] In `_leave_visual_table` in `pages/alerts_analysis/population_page.py`, keep the bilingual Back button (`חזרה לדוח` / `Back to report`). When `title != self.HOUR_CHART`, keep `get_by_text(title).filter(visible=True)` and `expect(...).to_be_visible`. When `title == self.HOUR_CHART`, use `get_by_text(title)` without `.filter(visible=True)` and wait until it is attached. Do not call `to_be_visible` for the hour title. Leave the `try...finally` in `_visual_table_map` in the same file so Back still runs when the table was opened. English comment inside the edited function.

**Checkpoint**: User Story 2 still closes the table, and the hour title wait no longer depends on visibility.

---

## Phase 5: User Story 3 - Screen 2 becomes ready on its distance filter (Priority: P1)

**Goal**: The ready locator and the page-switch click stay as they are

**Independent Test**: `AlertsPopulationPage._report_ready_locator()` is visible text `מרחק מהגבול` inside the report frame. `before_report_ready_check` still force-clicks the inner `ניתוח התרעות` tab and does not treat three clicks as done while that filter is absent.

### Implementation for User Story 3

- [X] T008 [US3] Confirm `_report_ready_locator` and `before_report_ready_check` in `pages/alerts_analysis/population_page.py` are unchanged: the locator is `self._report_frame().get_by_text(self._SCREEN2_READY_ANCHOR).filter(visible=True).first` with `_SCREEN2_READY_ANCHOR` equal to `מרחק מהגבול`, and the hook force-clicks the inner `ניתוח התרעות` tab inside `ניווט בין עמודים` / `Page navigation`. Do not edit either method.

**Checkpoint**: User Story 3 is unchanged. Screen 2 ready is still the distance filter.

---

## Phase 6: User Story 4 - Nafa acronym quotes compare equal (Priority: P1)

**Goal**: `נפה` and `רשות` (and `יישוב` on the same method) are force-clicked through the visual header toolbar, and quote folding stays

**Independent Test**: `_assert_golden_keys` treats a key that differs only by `'` versus `"` as the same key. `set_hierarchy_level` uses `click(force=True)` so a toolbar over `נפה` or `רשות` does not fail the click. Golden YAML bytes are unchanged.

### Implementation for User Story 4

- [X] T009 [US4] In `set_hierarchy_level` in `pages/alerts_analysis/population_page.py`, change `control.click()` to `control.click(force=True)` for the control `_hierarchy_control` already resolved (`נפה`, `רשות`, and `יישוב`). Leave `_hierarchy_control` on a visible `button`, `tab`, or `option`. Do not edit `set_district_aggregation`. Add an English comment inside `set_hierarchy_level` that `force=True` bypasses the visual header toolbar that intercepts the drill-down button. Keep the `bool` return.
- [X] T010 [P] [US4] Confirm `_assert_golden_keys` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` still folds `"` to `'` with `replace('"', "'")` on keys only, and confirm `data/alerts/db_sanity_am_kalavi.yaml` has no diff. Do not edit either file. Do not add `@pytest.mark.skip` to any test in that sanity module.

**Checkpoint**: User Story 4 can click the hierarchy control through the toolbar, and nafa quote folding is unchanged.

---

## Phase 7: User Story 5 - Date filters wait until filtered data leaves zero (Priority: P1)

**Goal**: `set_date_range` still waits until `אוכלוסייה מותרעת` is neither blank nor `0`

**Independent Test**: After `set_date_range` returns for the golden range, `read_card("warned")` is not `0` and not blank.

### Implementation for User Story 5

- [X] T011 [US5] Confirm `set_date_range` in `pages/alerts_analysis/population_page.py` still waits until the warned card `אוכלוסייה מותרעת` is neither blank nor `0`, and that the wait is not `networkidle`. Do not edit that method.

**Checkpoint**: All five stories are satisfied. US1, US2, and US4 contain this slice's page edits. US3 and US5 are preserved.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Prove the skip, the unit bans, and the YAML suite, and prove off-limits files stayed untouched

- [X] T012 Run `pytest tests/unit/test_db_parity_engine.py` and confirm it passes after the `mark.skip` scans in `tests/unit/test_db_parity_engine.py` were relaxed and `tests/ui/alerts_analysis_dashboard/test_db_parity.py` gained the decorator.
- [X] T013 [P] Run `pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py --collect-only` and confirm `test_alerts_db_parity_last_30_days` is skipped with reason `Focusing strictly on YAML validation; DB checks temporarily disabled` and does not open a database.
- [X] T014 Run `pytest tests/ui/alerts_analysis_dashboard/` from `specs/045-hour-chart-table-teardown/quickstart.md`. Freshness and population invariants still run. The parity test stays skipped. Do not run `pytest tests/ui/fleet_dashboard/`.
- [X] T015 Run `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity` from `specs/045-hour-chart-table-teardown/quickstart.md` (portal auth). Hierarchy tests exercise `set_hierarchy_level`. Hour tests exercise the hour-title anchor. Do not add skips in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
- [X] T016 [P] Confirm git diff does not include `data/alerts/db_sanity_am_kalavi.yaml`, `data/alerts/alerts_contract.yaml`, `db/clients/alerts.py`, `core/`, `pages/fleet_dashboard/`, `pages/status_picture/`, or `pages/credit_consumption/`. Confirm comments inside edited functions in `pages/alerts_analysis/population_page.py` and `tests/ui/alerts_analysis_dashboard/test_db_parity.py` are English.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational
  - US1, US2, and US4 edit `pages/alerts_analysis/population_page.py` and run in that order (US1 → US2 → US4)
  - US3 and US5 do not edit code; run them after the page edits so the confirm sees the final file
- **Polish (Phase 8)**: Depends on US1–US5

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on US2–US5. MVP.
- **User Story 2 (P1)**: Starts after US1 because both edit `pages/alerts_analysis/population_page.py`. Independently about table teardown.
- **User Story 3 (P1)**: Confirm-only. No code dependency on US1, US2, or US4. Run after those edits so the confirm is against the finished page.
- **User Story 4 (P1)**: Starts after US2 (same page file). Quote-fold confirm (T010) is a different file and does not wait on the click.
- **User Story 5 (P1)**: Confirm-only. No dependency on the hierarchy click or the hour title. Run after the page edits.

### Within Each User Story

- This spec does not ask for new tests first
- Page edits stay on the method named in the task
- A confirm task does not change the method it checks

### Parallel Opportunities

- T002 can run with T001 (inventory vs plan read)
- T003 and T004 edit different files and can run together
- T010 can run beside the page edits (different file, no write to the page)
- T012 and T013 can run together after the stories (unit file vs collect-only)
- T016 can run beside T012 (diff check vs pytest)

---

## Parallel Example: Foundational skip

```text
Task: "Remove only the mark.skip asserts in tests/unit/test_db_parity_engine.py"
Task: "Add pytest.mark.skip on test_alerts_db_parity_last_30_days in tests/ui/alerts_analysis_dashboard/test_db_parity.py"
```

## Parallel Example: User Story 4

```text
Task: "Force-click in set_hierarchy_level in pages/alerts_analysis/population_page.py"
Task: "Confirm quote folding in tests/sanity/alerts_analysis_dashboard/test_data_validation.py and no YAML diff"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (SQL skip) — smoke no longer queries `[FACT].[AlertsRedWeb]`
3. Complete Phase 3: User Story 1 (hour-title anchor)
4. **STOP and VALIDATE**: `_title_anchor` accepts an attached hour title inside a visual container, and `read_hour_daily_avg` is unchanged

### Incremental Delivery

1. Setup + Foundational → parity test skipped, unit bans on `pytest.skip` and `importorskip` still hold
2. User Story 1 → hour chart anchor no longer requires visibility
3. User Story 2 → hour-chart return from Show-as-a-table no longer requires visibility
4. User Story 4 → hierarchy drill-down uses `click(force=True)`
5. User Story 3 and User Story 5 → confirm the ready locator, page-switch hook, and date wait were not reopened
6. Polish → unit, collect-only, alerts UI smoke, YAML sanity

### Parallel Team Strategy

1. One person completes Setup
2. Then, together:
   - Developer A: T003 in `tests/unit/test_db_parity_engine.py`
   - Developer B: T004 in `tests/ui/alerts_analysis_dashboard/test_db_parity.py`
3. After Foundational, page edits are one file: US1, then US2, then US4, in order
4. T010 (quote-fold confirm) can run beside those page edits

---

## Notes

- [P] tasks = different files, no dependencies
- US1, US2, and US4 must not be edited at the same time in `pages/alerts_analysis/population_page.py`
- Do not skip `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. Those tests load YAML and do not open SQL
- Do not run fleet smoke as a completion gate
- The skip reason string is exact: `Focusing strictly on YAML validation; DB checks temporarily disabled`
- Comments inside edited functions stay English
