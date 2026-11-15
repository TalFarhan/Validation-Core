# Tasks: Fix Hierarchy Level Locators

**Input**: Design documents from `specs/047-hierarchy-level-locators/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/hierarchy-tabs.md, quickstart.md

**Tests**: No new test files. The spec does not ask for TDD. The check is the existing YAML sanity module in `specs/047-hierarchy-level-locators/quickstart.md`. Fleet smoke is **not** a gate: `core/portal/page.py`, `ReportShell`, and `pages/fleet_dashboard/` are not edited (plan.md).

**Organization**: Tasks are grouped by user story. US1 edits `pages/alerts_analysis/population_page.py`. US2 and US3 edit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, in that order. US2 can be written beside US1 because it is a different file.

**Status (2026-11-04)**: T001–T009 are complete. All eight hierarchy sanity tests passed on the live portal. The settlement tab is clicked as `ישוב`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US3 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Alerts population page: `pages/alerts_analysis/population_page.py`
- YAML sanity helpers: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- Alerts golden record (do not edit): `data/alerts/db_sanity_am_kalavi.yaml`
- Contract: `specs/047-hierarchy-level-locators/contracts/hierarchy-tabs.md`
- OFF-LIMITS: `core/portal/`, `core/components/`, `pages/fleet_dashboard/`, `pages/status_picture/`, `pages/credit_consumption/`, `db/`, root `conftest.py`, every file under `data/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lock the edit list and record the current locator and skip before changing them

- [x] T001 Confirm the edit list in `specs/047-hierarchy-level-locators/plan.md` and `specs/047-hierarchy-level-locators/contracts/hierarchy-tabs.md`: this slice may change `_hierarchy_control` and `set_hierarchy_level` in `pages/alerts_analysis/population_page.py`, and `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. Leave `_HIERARCHY_LEVEL_NAMES`, `district_chart_title_for`, `_wait_for_level_selection`, `set_district_aggregation`, `data/alerts/db_sanity_am_kalavi.yaml`, and `core/` untouched.
- [x] T002 [P] Inventory without editing. In `pages/alerts_analysis/population_page.py`, confirm `_hierarchy_control` returns `self._report_frame().get_by_text(label, exact=True)` as a `Locator` (no role loop, no `_visual_container`, no `None`), and `set_hierarchy_level` calls `control.first.click()` with no `force=True`. In `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, confirm both helpers assert `set_hierarchy_level` and still skip only with `returned no rows` (`specs/047-hierarchy-level-locators/research.md`). The old role lookup and the `control not visible on district chart` skip are already gone.

**Checkpoint**: Scope and the current role lookup, force click, and two skip reasons are known. No behavior change yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Keep the shared level map, title helper, and selection wait that every story uses

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Confirm in `pages/alerts_analysis/population_page.py` that `_HIERARCHY_LEVEL_NAMES` maps `nafa` to `נפה`, `rashut` to `רשות`, and `yeshuv` to `יישוב`, that `district_chart_title_for` returns `התרעות לפי ` plus that name, that `_report_frame` is inherited from `ReportShell`, and that `_wait_for_level_selection` returns true when the locator has neither `aria-pressed` nor `aria-selected`. Do not edit those methods. Do not add a locator for `ישוב`.

**Checkpoint**: The Hebrew labels, the iframe frame, the title string, and the selection wait stay the shared inputs. Story work can start.

---

## Phase 3: User Story 1 - Hierarchy tabs are selected by their labels (Priority: P1) 🎯 MVP

**Goal**: `set_hierarchy_level` clicks the custom tab whose exact text is `נפה`, `רשות`, or `יישוב` inside the report iframe

**Independent Test**: `set_hierarchy_level("nafa")` clicks exact text `נפה` via `_report_frame().get_by_text` and waits until the district title `התרעות לפי נפה` is visible. The same path serves `rashut` / `רשות` and `yeshuv` / `יישוב`. The lookup does not use a role or the district visual container.

### Implementation for User Story 1

- [x] T004 [US1] Rewrite `_hierarchy_control` in `pages/alerts_analysis/population_page.py` so it returns `self._report_frame().get_by_text(label, exact=True)` with return type `Locator`. Remove the `Locator | None` return, the `_visual_container` lookup, the `button` / `tab` / `option` role loop, the `count()` probe, and every `return None`. Update the docstring to say the locator is the exact Hebrew label in the report iframe. English only inside the function (`specs/047-hierarchy-level-locators/contracts/hierarchy-tabs.md`).
- [x] T005 [US1] In `set_hierarchy_level` in `pages/alerts_analysis/population_page.py`, keep the early `return False` when `level` is not `nafa`, `rashut`, or `yeshuv`. Delete the `if control is None: return False` branch. After `self._dismiss_overlay()`, call `control.first.click()` with no `force=True` and no `try` around the click. Pass that same `.first` locator to `_wait_for_level_selection`. Keep the wait for `district_chart_title_for(level)` via `_iframe_phrase_locator`, the false return when that title never appears, the assignment to `_active_hierarchy_level`, and the `bool` return. Replace the comment about the visual header toolbar with an English comment that the custom tab is clicked by its label and Playwright waits until the text is actionable (`specs/047-hierarchy-level-locators/contracts/hierarchy-tabs.md`).

**Checkpoint**: User Story 1 clicks the three labels by exact text and still returns `bool`. The role lookup and the force click are gone.

---

## Phase 4: User Story 2 - A missing tab fails the test (Priority: P1)

**Goal**: The hierarchy helpers fail when `set_hierarchy_level` returns false, and they no longer skip for a missing control

**Independent Test**: `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg` contain no `pytest.skip` whose message includes `control not visible on district chart`. A false return fails the test with an assertion that names the level.

### Implementation for User Story 2

- [x] T006 [P] [US2] In `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, delete the `if not page.set_hierarchy_level(level): pytest.skip(...)` branch whose message contains `control not visible on district chart`. Replace it with an assertion that `page.set_hierarchy_level(level)` is true and that the failure message includes the level. Keep `set_district_aggregation("sum")` in the sum helper and `set_district_aggregation("average")` in the daily-average helper. Keep both calls to `_assert_golden_keys`. Update the docstring and the English comment in `_assert_hierarchy_daily_avg` so they describe a failed selection as a test failure. Do not catch Playwright timeouts in either helper (`specs/047-hierarchy-level-locators/contracts/hierarchy-tabs.md`).

**Checkpoint**: User Story 2 no longer hides a locator miss behind the control-not-visible skip.

---

## Phase 5: User Story 3 - An empty drilled chart still skips (Priority: P2)

**Goal**: After a level is selected, an empty district read still skips with the existing reason

**Independent Test**: Both helpers still call `pytest.skip` with `District chart returned no rows for level {level!r} (chart empty or not rendered)` only when `read_district_labels()` is empty. Rows that are present still go to `_assert_golden_keys`.

### Implementation for User Story 3

- [x] T007 [US3] In `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, keep the block that skips when `read_district_labels()` is empty, with the reason `District chart returned no rows for level {level!r} (chart empty or not rendered)`. Do not change that reason string. Do not add a skip for a missing tab. Leave `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, `test_hierarchy_yeshuv_matches_db`, and the three `*_daily_avg_matches_db` tests calling these helpers with the same golden keys under `metrics.alerts_by_hierarchy`. Do not edit `data/alerts/db_sanity_am_kalavi.yaml`.

**Checkpoint**: User Story 3 preserves the empty-chart skip. The six hierarchy tests still call the helpers.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Run the hierarchy sanity check and prove off-limits files stayed untouched

- [X] T008 Run `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k hierarchy` from `specs/047-hierarchy-level-locators/quickstart.md` (portal auth). The six nafa / rashut / yeshuv tests must not skip with `control not visible on district chart`. A tab that never becomes clickable fails the test. An empty `read_district_labels()` result may still skip with `returned no rows`.
- [X] T009 [P] Confirm the git diff is limited to `pages/alerts_analysis/population_page.py` and `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` plus this feature's docs. Confirm `data/alerts/db_sanity_am_kalavi.yaml`, `core/`, `db/`, `pages/fleet_dashboard/`, `pages/status_picture/`, and `pages/credit_consumption/` have no diff. Confirm `set_hierarchy_level` in `pages/alerts_analysis/population_page.py` has no `click(force=True)` and no `get_by_role`, and that comments inside the edited functions are English. Do not run `pytest tests/ui/fleet_dashboard/`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational
  - US1 edits `pages/alerts_analysis/population_page.py` (T004 then T005)
  - US2 edits `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` and can run beside US1
  - US3 edits the same two helpers as US2 and starts after T006
- **Polish (Phase 6)**: Depends on US1, US2, and US3

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on US2 or US3. MVP.
- **User Story 2 (P1)**: Starts after Foundational. Different file from US1, so it does not wait for T005. The live pytest in T008 needs both stories.
- **User Story 3 (P2)**: Starts after T006 because it checks the same helpers in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. It does not edit `pages/alerts_analysis/population_page.py`.

### Within Each User Story

- This spec does not ask for new tests first
- T004 finishes before T005 because both edit `pages/alerts_analysis/population_page.py` and T005 clicks the locator T004 returns
- T007 reads the helpers T006 rewrote and does not restore the control-not-visible skip

### Parallel Opportunities

- T002 can run with T001 (inventory vs plan read)
- T006 can run with T004 and T005 (sanity helpers vs population page)
- T009 can run beside T008 (diff check vs pytest) after the stories

---

## Parallel Example: User Story 1 and User Story 2

```text
Task: "Rewrite _hierarchy_control and the click in pages/alerts_analysis/population_page.py"
Task: "Replace the control-not-visible skip in tests/sanity/alerts_analysis_dashboard/test_data_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (level map, title helper, and selection wait confirmed)
3. Complete Phase 3: User Story 1 (exact-text click)
4. **STOP and VALIDATE**: `set_hierarchy_level` clicks `נפה` / `רשות` / `יישוב` by text and still returns `bool`

### Incremental Delivery

1. Setup + Foundational → shared labels and title helper are confirmed and untouched
2. User Story 1 → custom tabs are clicked by exact text inside the report iframe
3. User Story 2 → a false return fails the sanity helper
4. User Story 3 → the empty-chart skip is still present
5. Polish → hierarchy sanity pytest and an off-limits diff check

### Parallel Team Strategy

1. One person completes Setup and Foundational
2. Then, together:
   - Developer A: T004 then T005 in `pages/alerts_analysis/population_page.py`
   - Developer B: T006 in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
3. After T006, one person completes T007 in that same test file
4. Polish runs after US1–US3

---

## Notes

- [P] tasks = different files, no dependencies
- T004 and T005 must not be edited at the same time in `pages/alerts_analysis/population_page.py`
- T006 and T007 must not be edited at the same time in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- Do not run fleet smoke as a completion gate
- The removed skip message contains `control not visible on district chart`
- The kept skip message is `District chart returned no rows for level {level!r} (chart empty or not rendered)`
- Comments inside edited functions stay English
