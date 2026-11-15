---
description: "Task list for Complete Alerts DB Sanity Validations"
---

# Tasks: Complete Alerts DB Sanity Validations

**Input**: Design documents from `specs/040-alerts-db-sanity-completion/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: This feature *is* test coverage — the deliverables are pytest sanity tests plus a
domain-page timeout value change. It does **not** touch `core/portal`, `ReportShell`, or shared
page-object navigation, so fleet smoke validation (`pytest tests/ui/fleet_dashboard/`) is **not**
a mandatory gate for this slice (see plan Constitution Check III).

**Organization**: Tasks are grouped by user story so each story can be implemented and verified
independently against the golden file `data/alerts/db_sanity_am_kalavi.yaml`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Alerts Screen 2 tests: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- Alerts Screen 1 tests: `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`
- Alerts domain pages: `pages/alerts_analysis/population_page.py`, `pages/status_picture/status_picture_page.py`
- Golden source (read-only): `data/alerts/db_sanity_am_kalavi.yaml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the feature is pinned and the golden source holds the shapes the new tests read.

- [X] T001 Verify the golden file parses and exposes the needed maps by running `python -c "import yaml; s=yaml.safe_load(open('data/alerts/db_sanity_am_kalavi.yaml',encoding='utf-8'))['dashboard_sanity_checks']; h=s['screen_2_alerts_analysis']['metrics']['alerts_by_hierarchy']; assert set(h['nafa']['daily_avg'].values())=={1} and set(h['rashut']['daily_avg'].values())=={1} and set(h['yeshuv']['daily_avg'].values())=={1}; assert sorted(s['screen_1_status_picture']['metrics']['top_10_settlements']['values'].values())==[31,31,31,31,32,32,34,35,36,39]; print('golden ok')"` from repo root (PowerShell: use `python -m` if needed).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the one helper shared by the Screen 2 daily-average stories (US1, US2).

**⚠️ CRITICAL**: US1 and US2 depend on this helper. US3 and US4 do not.

- [X] T002 In `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, add helper `_assert_hierarchy_daily_avg(page, level, expected)` that mirrors the existing `_assert_hierarchy_sum`: call `page.set_hierarchy_level(level)` (skip with `pytest.skip(f"Missing page object method for hierarchy level {level}")` when it returns False), call `page.set_district_aggregation("average")`, read `actual = page.read_district_labels()` (skip when empty), then call the existing `_assert_golden_keys(actual, expected)`. English-only in-function comments. (Do not add any new page-object reader.)

**Checkpoint**: Shared daily-average helper ready — US1 and US2 can proceed.

---

## Phase 3: User Story 1 - Screen 2 nafa daily averages (Priority: P1) 🎯 MVP

**Goal**: Validate `alerts_by_hierarchy.nafa.daily_avg` on the district chart in per-day-average mode.

**Independent Test**: `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -k nafa_daily_avg -m sanity -v` (portal auth) passes when נפת חירם and חטמ'ר צפונית - 7643 each read `1`; skips if the נפה control or reader is unavailable.

### Implementation for User Story 1

- [X] T003 [US1] In `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, add `@pytest.mark.sanity` test `test_hierarchy_nafa_daily_avg_matches_db(population_dashboard)` that calls `_apply_golden_range(population_dashboard)` then `_assert_hierarchy_daily_avg(population_dashboard, "nafa", screen["metrics"]["alerts_by_hierarchy"]["nafa"]["daily_avg"])`. Expected values come only from the YAML. English-only comments. (depends on T002)

**Checkpoint**: Screen 2 nafa daily-average coverage is complete and independently testable.

---

## Phase 4: User Story 2 - Screen 2 rashut and yeshuv daily averages (Priority: P1)

**Goal**: Validate `alerts_by_hierarchy.rashut.daily_avg` and `alerts_by_hierarchy.yeshuv.daily_avg` in average mode.

**Independent Test**: `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -k "rashut_daily_avg or yeshuv_daily_avg" -m sanity -v` (portal auth) passes when every golden rashut and yeshuv daily-average name reads `1`; skips if a level or reader is unavailable.

### Implementation for User Story 2

- [X] T004 [US2] In `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, add `@pytest.mark.sanity` test `test_hierarchy_rashut_daily_avg_matches_db(population_dashboard)` that applies the golden range and calls `_assert_hierarchy_daily_avg(population_dashboard, "rashut", screen["metrics"]["alerts_by_hierarchy"]["rashut"]["daily_avg"])`. English-only comments. (depends on T002; same file as T003 — sequential)
- [X] T005 [US2] In the same file, add `@pytest.mark.sanity` test `test_hierarchy_yeshuv_daily_avg_matches_db(population_dashboard)` that applies the golden range and calls `_assert_hierarchy_daily_avg(population_dashboard, "yeshuv", screen["metrics"]["alerts_by_hierarchy"]["yeshuv"]["daily_avg"])`. English-only comments. (depends on T002; same file as T003/T004 — sequential)

**Checkpoint**: All three Screen 2 hierarchy daily-average levels are covered.

---

## Phase 5: User Story 3 - Screen 1 tied settlements verified by exact name (Priority: P1)

**Goal**: Change `test_screen_1_top_settlements` so the tie slots are checked by exact name (unordered set equality against the golden tie names) instead of only counting four rows.

**Independent Test**: `python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py::test_screen_1_top_settlements -m sanity -v` (portal auth) passes when the stable settlements match and the four UI tie slots carry the four golden tie names in any order; skips on an empty ranking map.

### Implementation for User Story 3

- [X] T006 [P] [US3] In `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`, edit only `test_screen_1_top_settlements` (and add a small helper reading the YAML, e.g. `_golden_tie_names(expected)` / reuse `_tie_count`): keep the empty-map skip (`Missing Page Object reader for top_10_settlements`); keep exact name-and-count assertions for the stable set (golden count above the tie value, derived from the file, not hard-coded); compute the golden tie names (entries whose count equals the tie value) and the UI tie slots (UI names outside the stable set); assert `set(ui_tie_names) == set(golden_tie_names)` and that every UI tie count equals the tie value. Do not edit the golden YAML or `StatusPicturePage`. English-only comments. (different file from US1/US2 — parallelizable)

**Checkpoint**: Screen 1 tie slots are verified by name.

---

## Phase 6: User Story 4 - Larger Power BI locator budget (Priority: P2)

**Goal**: Raise the Alerts domain-page locator/navigation timeout above 60s so Power BI rendering is less likely to raise `LoadTimeoutError`, while a never-rendering visual still raises it.

**Independent Test**: Inspect both Alerts pages — `self.timeout` is `120_000`, and `page.set_default_timeout` / `set_default_navigation_timeout` follow it. A cold load gets the larger budget; the `LoadTimeoutError` raise paths are unchanged.

### Implementation for User Story 4

- [X] T007 [P] [US4] In `pages/alerts_analysis/population_page.py` `__init__`, change `self.timeout = 60_000` to `self.timeout = 120_000` so the paired `page.set_default_navigation_timeout(self.timeout)` and `page.set_default_timeout(self.timeout)` use the larger budget. Do not remove any progressive wait step and do not change any reader signature. English-only comments. (different file — parallelizable)
- [X] T008 [P] [US4] In `pages/status_picture/status_picture_page.py` `__init__`, change `self.timeout = 60_000` to `self.timeout = 120_000` so `set_default_navigation_timeout` / `set_default_timeout` use it. Keep `LoadTimeoutError` behavior intact. English-only comments. (different file — parallelizable)

**Checkpoint**: Both Alerts screens have the larger rendering budget.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify scope and run the quickstart checks.

- [ ] T009 ⏸️ DEFERRED (needs portal auth + browser; not runnable in this environment). Run the Alerts sanity suite with portal auth: `python -m pytest tests/sanity/alerts_analysis_dashboard tests/sanity/status_picture_dashboard -m sanity -v`. Confirm the three new daily-average tests and the edited tie test pass (or skip only for an unavailable control/reader). Collection-only verification already passed (18 tests collected, no import/lint errors).
- [X] T010 [P] Confirm scope: `git status` / `git diff --name-only` shows edits only under `tests/sanity/alerts_analysis_dashboard/`, `tests/sanity/status_picture_dashboard/`, and the two Alerts page objects — and that no fleet module, `core/`, `db/clients/`, `data/`, or root `conftest.py` is changed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS US1 and US2 only (shared helper).
- **US1 (Phase 3)** and **US2 (Phase 4)**: Depend on Foundational (T002). Same file, so sequential among themselves (T003 → T004 → T005).
- **US3 (Phase 5)**: Independent of Foundational — different module. Can run anytime after Setup.
- **US4 (Phase 6)**: Independent of all other stories — different files (page objects).
- **Polish (Phase 7)**: After the desired stories are complete.

### User Story Dependencies

- **US1 (P1)**: Needs T002. No dependency on other stories.
- **US2 (P1)**: Needs T002. Shares the file with US1 (sequential edits).
- **US3 (P1)**: No dependency on US1/US2/US4.
- **US4 (P2)**: No dependency on US1/US2/US3; improves reliability of all.

### Parallel Opportunities

- T006 (US3), T007 (US4), T008 (US4) touch distinct files and can run in parallel with each other and with the US1/US2 work on the Screen 2 module.
- T010 can run in parallel with T009's manual review once edits are staged.
- Within US1/US2 the edits share one file, so T003 → T004 → T005 are sequential.

---

## Parallel Example: independent files

```bash
# These three touch different files and can proceed concurrently:
Task: "T006 [US3] edit tie check in tests/sanity/status_picture_dashboard/test_status_picture_validation.py"
Task: "T007 [US4] raise timeout in pages/alerts_analysis/population_page.py"
Task: "T008 [US4] raise timeout in pages/status_picture/status_picture_page.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup (T001).
2. Phase 2 Foundational (T002 helper).
3. Phase 3 US1 (T003).
4. **STOP and VALIDATE**: run the nafa daily-average test with auth.

### Incremental Delivery

1. Setup + Foundational → helper ready.
2. US1 (T003) → nafa daily average → validate.
3. US2 (T004, T005) → rashut + yeshuv daily averages → validate.
4. US3 (T006) → Screen 1 tie by name → validate.
5. US4 (T007, T008) → larger budget → validate no `LoadTimeoutError` regression.
6. Polish (T009, T010).

### Parallel Team Strategy

- Developer A: Phase 2 + US1 + US2 (Screen 2 module).
- Developer B: US3 (Screen 1 module) in parallel.
- Developer C: US4 (page-object timeouts) in parallel.

---

## Notes

- Expected values are read only from `data/alerts/db_sanity_am_kalavi.yaml`; no name or count is hard-coded in a test.
- No new page object, reader, or SQL client is added; only `self.timeout` changes on the two Alerts pages.
- Screen 1 reverses feature 036's count-only tie decision at the user's direction; set equality keeps load-order shuffling of equal counts passing (see research.md).
- Comments inside new or edited functions are English only.
- Fleet smoke is not a mandatory gate for this slice (no Layer 0 / navigation change).
