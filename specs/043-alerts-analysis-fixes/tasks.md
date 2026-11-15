# Tasks: Fix Skipped Hierarchy Tests and Navigation Errors for Alerts Analysis

**Input**: Design documents from `specs/043-alerts-analysis-fixes/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/population-fixes.md, quickstart.md

**Tests**: This feature edits the alerts domain page object (`pages/alerts_analysis/population_page.py`), so the alerts UI smoke suite (`pytest tests/ui/alerts_analysis_dashboard/`) is the MANDATORY completion gate (Constitution III / FR-010). Fleet smoke is **not** a gate (no `core/` or fleet navigation change). The target behavior is exercised by existing sanity and unit tests; no new test files are created. Three existing references to the removed `DISTRICT_CHART` constant are updated in the same change.

**Organization**: Tasks are grouped by the four user stories from spec.md so each can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Alerts population page: `pages/alerts_analysis/population_page.py`
- Alerts UI smoke: `tests/ui/alerts_analysis_dashboard/` (`test_population_invariants.py`, `population_snapshot.py`)
- Alerts unit test: `tests/unit/test_population_page.py`
- Alerts sanity: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- Alerts golden record: `data/alerts/db_sanity_am_kalavi.yaml` (read-only)
- OFF-LIMITS (do not edit): `core/portal/`, `core/components/` (incl. `chart.py`), `pages/fleet_dashboard/`, `pages/status_picture/`, `tests/**/fleet_dashboard/`, `tests/**/status_picture_dashboard/`, `db/clients/`, root `conftest.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm scope and inventory the live call sites before changing behavior

- [X] T001 Confirm scope guard in `specs/043-alerts-analysis-fixes/plan.md`: the edit list is limited to `pages/alerts_analysis/population_page.py`, `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, `tests/ui/alerts_analysis_dashboard/population_snapshot.py`, and `tests/unit/test_population_page.py`; sanity `test_data_validation.py` is audit-only; no fleet/`core/`/root-conftest/golden-value file is in scope.
- [X] T002 [P] Inventory live call sites (read-only): every `DISTRICT_CHART`, `_PAGE_NAV_LABEL`, `_fill_input`, `set_hierarchy_level`, `read_district_labels`, `read_hour_buckets`, `read_hour_daily_avg`, `_click_show_as_table`, `_leave_dates_table`, and `_alert_column_table` in `pages/alerts_analysis/population_page.py`; the three `DISTRICT_CHART` test references; and every `pytest.skip` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. Do not edit.

**Checkpoint**: Scope confirmed; call sites listed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared title map and active-level field that US2/US3/US4 all use

**⚠️ CRITICAL**: No user story work that needs a live district title can begin until this phase is complete

- [X] T003 In `pages/alerts_analysis/population_page.py`, add a class-level map `_HIERARCHY_LEVEL_NAMES = {"mahoz": "מחוז", "nafa": "נפה", "rashut": "רשות", "yeshuv": "יישוב"}`, a `@staticmethod district_chart_title_for(level: str) -> str` that returns `"התרעות לפי " + map[level]`, and `self._active_hierarchy_level = "mahoz"` in `__init__`. Do **not** remove `DISTRICT_CHART` yet and do not rewire callers. English comments only.

**Checkpoint**: Title builder and active-level field exist; user story work can begin.

---

## Phase 3: User Story 1 - Page navigation and date entry survive an English render (Priority: P1) 🎯 MVP

**Goal**: The page-rail switch and start/end date fields resolve through a Playwright `.or_()` over Hebrew and English names, so Screen 2 opens and dates fill without `LoadTimeoutError`.

**Independent Test**: `pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py` opens Screen 2 and applies a date range with no `LoadTimeoutError` (Hebrew still works; English names are covered by the `.or_()`).

### Implementation for User Story 1

- [X] T004 [US1] In `pages/alerts_analysis/population_page.py::before_report_ready_check`, wrap the page-rail locator in a Playwright `.or_()` over `ניווט בין עמודים` (`_PAGE_NAV_LABEL`) and `Page navigation` across the existing `get_by_role("link"|"button")` / `get_by_label` strategies. Keep the attempt/cooldown/`force=True` click sequence. English comments only (FR-001).
- [X] T005 [US1] In `pages/alerts_analysis/population_page.py::_fill_input`, resolve the field through `input[aria-label^='{hebrew}']`.or_()`input[aria-label^='{english}']`. `set_between_dates` must fill `תאריך התחלה`/`Start date` and `תאריך סיום`/`End date`. Keep `_commit_field`. English comments only (FR-002).
- [ ] T006 [US1] Run the independent test `pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and confirm Screen 2 opens and `set_date_range` / `set_between_dates` complete with no `LoadTimeoutError`. **(BLOCKED: requires portal auth + live browser — run locally.)**

**Checkpoint**: Page switch and date entry work under Hebrew and English accessibility names; US1 testable on its own.

---

## Phase 4: User Story 2 - District chart title follows drill-down (Priority: P1)

**Goal**: `DISTRICT_CHART` is removed. Readers anchor on `district_chart_title()` (`"התרעות לפי " + level_name`). `set_hierarchy_level` waits for the *new* title and records the active level, so a successful drill-down no longer returns `False`.

**Independent Test**: `pytest tests/unit/test_population_page.py` asserts the base title; `test_population_suite_opens_second_page` finds the base title via the accessor. Drill-down visibility is inspectable in `set_hierarchy_level` (waits for `התרעות לפי נפה` after `"nafa"`). Full hierarchy golden matches wait for US3.

### Implementation for User Story 2

- [X] T007 [US2] In `pages/alerts_analysis/population_page.py`, add instance method `district_chart_title(self, level: str | None = None) -> str` that delegates to `district_chart_title_for(level or self._active_hierarchy_level)`. Remove class constant `DISTRICT_CHART`. Replace every remaining `self.DISTRICT_CHART` with `self.district_chart_title()` in `before_report_ready_check`, `set_district_aggregation`, `_hierarchy_control`, `chart_total`, `read_district_labels`, `_district_visible_total`, and the `others` list in `_visual_container`. Public reader signatures stay unchanged. English comments only (FR-003, FR-004).
- [X] T008 [US2] In `pages/alerts_analysis/population_page.py::set_hierarchy_level`, keep the `bool` return. Resolve the control inside the *current* `district_chart_title()` container. After a successful `_wait_for_level_selection`, wait until `district_chart_title_for(level)` is visible (the *new* title, not `התרעות לפי מחוז`). Only then set `_active_hierarchy_level = level` and return `True`. On a missing control or a title that never appears, leave the field unchanged and return `False`. English comments only (FR-004).
- [X] T009 [P] [US2] In `tests/unit/test_population_page.py`, replace `assert AlertsPopulationPage.DISTRICT_CHART == "התרעות לפי מחוז"` with `assert AlertsPopulationPage.district_chart_title_for("mahoz") == "התרעות לפי מחוז"`. Keep the subclass and `PAGE_TITLE` assertions (FR-010).
- [X] T010 [P] [US2] In `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, replace both `AlertsPopulationPage.DISTRICT_CHART` / `page.DISTRICT_CHART` uses with `population_dashboard.district_chart_title()` / `page.district_chart_title()` (`test_population_suite_opens_second_page` and `test_hour_date_and_district_sums_match`) (FR-010).
- [X] T011 [P] [US2] In `tests/ui/alerts_analysis_dashboard/population_snapshot.py`, replace `page.chart_total(page.DISTRICT_CHART)` with `page.chart_total(page.district_chart_title())` (FR-010).
- [X] T012 [US2] Run `pytest tests/unit/test_population_page.py` (no browser) and confirm it passes. Confirm `rg DISTRICT_CHART pages tests` no longer hits the three updated files or `population_page.py`.

**Checkpoint**: Live title accessor is the only district-chart anchor; unit + smoke references updated; US2 testable on its own.

---

## Phase 5: User Story 3 - Listbox district and hour data is extracted (Priority: P1)

**Goal**: When the district/hour visual renders as a Power BI `listbox` (no grid rows, no numeric SVG `aria-label`), `read_district_labels`, `read_hour_buckets`, and `read_hour_daily_avg` still return a name/hour → count mapping via Show-as-a-table (primary) or listbox pairing (secondary).

**Independent Test**: `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k "hierarchy_mahoz or alerts_by_hour"` returns non-empty mappings that match the golden record (no empty-read skip).

### Implementation for User Story 3

- [X] T013 [US3] In `pages/alerts_analysis/population_page.py`, parameterize the dates-table helpers without changing dates behavior: `_click_show_as_table` keeps bilingual menu items `("הצג כטבלה", "Show as a table")` and names the calling visual in errors; `_alert_column_table(self, header: str = "התרעות")` uses that header; add `_leave_visual_table(self, title: str)` (click `חזרה לדוח`, wait for `title`); point `read_date_counts` and `_dates_table_total` at `_leave_visual_table(self.DATES_CHART)`. Add private `_visual_table_map(self, title: str, header: str) -> dict[str, int]` (right-click → show-as-table → `_collect_scrolled_rows(..., key="header")` → leave) and `_listbox_name_counts(self, container, measure: str) -> dict[str, int]` (zip category `listbox` options with the measure `listbox` named `measure` or containing `ממוצע`). English comments only. Do not edit `core/components/chart.py`.
- [X] T014 [US3] In `pages/alerts_analysis/population_page.py::read_district_labels`, keep the existing row/mark/tooltip paths first. If they return empty, try `_visual_table_map(self.district_chart_title(), "התרעות")`, then `_listbox_name_counts` on the district container with measure `התרעות`. Return `{}` only when every path is empty. Signature `-> dict[str, int]` unchanged (FR-005).
- [X] T015 [US3] In `pages/alerts_analysis/population_page.py::read_hour_buckets`, keep the existing SVG/category/tooltip paths first. If empty, try `_visual_table_map(self.HOUR_CHART, "התרעות")` then `_listbox_name_counts` with measure `התרעות`. Normalize hour keys to `HH:MM` via the existing `_HOUR_TOKEN`. Signature unchanged (FR-006).
- [X] T016 [US3] In `pages/alerts_analysis/population_page.py::read_hour_daily_avg`, keep the existing average-series paths first. If empty, try `_visual_table_map(self.HOUR_CHART, header containing "ממוצע")` then `_listbox_name_counts` for the average series. Normalize hour keys to `HH:MM`. Signature unchanged (FR-007 companion to FR-006).
- [ ] T017 [US3] Run the independent test `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k "hierarchy_mahoz or alerts_by_hour"` and confirm non-empty mappings (no empty-read skip). **(BLOCKED: requires portal auth + live browser — run locally.)**

**Checkpoint**: District and hour listbox visuals yield mappings; US3 testable on its own (mahoz + hour, no drill-down required).

---

## Phase 6: User Story 4 - Skipped hierarchy and hour tests become real assertions (Priority: P1)

**Goal**: Every `test_hierarchy_*` and `test_alerts_by_hour_*` reports pass/fail (not skip) when data is present; the `pytest.skip` guards remain as a safety net for a genuinely absent control.

**Independent Test**: `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k "hierarchy or hour"` — named tests resolve to pass/fail; guards still exist in the source.

### Implementation for User Story 4

- [X] T018 [US4] Audit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`: confirm `test_hierarchy_*` and `test_alerts_by_hour_*` still read expected values only from `load_sanity_data()` (no golden literals in test bodies) and still call `pytest.skip` when `set_hierarchy_level` is false or a reader returns `{}`. Make a minimal edit only if a stale `DISTRICT_CHART` string or a deleted-method call remains. Do not delete the skip guards (FR-007, FR-009).
- [ ] T019 [US4] Run `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k "hierarchy or hour" -rs` and confirm no target test skips with an empty-read or "control not visible" message when data is present. **(BLOCKED: requires portal auth + live browser — run locally.)**

**Checkpoint**: Hierarchy and hour tests are real assertions; guards preserved.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Comment-language compliance, constitution gate, and final validation

- [X] T020 [P] Review every new or edited function in `pages/alerts_analysis/population_page.py` and the three updated test modules; ensure all in-function comments are English only (FR-011).
- [X] T021 [P] Verify no off-limits file was changed: `git status` / `git diff --name-only` shows no edits under `core/`, `pages/fleet_dashboard/`, `pages/status_picture/`, `tests/**/fleet_dashboard/`, `tests/**/status_picture_dashboard/`, `db/clients/`, or root `conftest.py`, and no metric value changed in `data/alerts/db_sanity_am_kalavi.yaml` (FR-008, FR-009).
- [ ] T022 Run the alerts UI smoke gate `pytest tests/ui/alerts_analysis_dashboard/` — MUST pass (Constitution III / FR-010, because the alerts page object was edited). **(BLOCKED: requires portal auth + live browser — run locally.)**
- [X] T023 Run `pytest tests/unit/test_population_page.py` and confirm it stays green after the accessor change (no browser).
- [ ] T024 Run quickstart validation per `specs/043-alerts-analysis-fixes/quickstart.md` (hierarchy + hour tests, full alerts sanity module, alerts UI smoke, unit test) and confirm the Done-When checklist. **(BLOCKED: requires portal auth + live browser — run locally.)**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. The title builder (T003) blocks US2 and is used by US3 district reads.
- **User Stories (Phase 3–6)**: Depend on Foundational.
  - US1 (Phase 3), US2 (Phase 4), and US3 (Phase 5) all edit `pages/alerts_analysis/population_page.py` → run sequentially (US1 → US2 → US3), not in parallel.
  - US2's three test-file updates (T009–T011) can run in parallel with each other after T007.
  - US4 (Phase 6) depends on US1–US3 being functional (it validates the resolved tests).
- **Polish (Phase 7)**: Depends on all desired user stories; T022 is the mandatory alerts UI smoke gate.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on other stories. Unblocks every later UI test (page must open).
- **US2 (P1)**: After US1 (same file; also needs Screen 2 open). Independent in behavior (different root cause) but not parallelizable in this file.
- **US3 (P1)**: After US2 (district readers need the live title). Hour readers do not need the title accessor but share the table helpers introduced in T013.
- **US4 (P1)**: After US1, US2, and US3 (validates their outcome); skip guards stay in the sanity file.

### Within Each User Story

- Implementation before its independent-test run.
- US1: page-rail (T004) → date fields (T005) → test (T006).
- US2: accessor + remove constant (T007) → `set_hierarchy_level` (T008) → three test files (T009–T011) → unit grep (T012).
- US3: parameterize helpers (T013) → district (T014) → hour sum (T015) → hour avg (T016) → test (T017).
- US4: audit guards (T018) → run hierarchy + hour (T019).

---

## Parallel Opportunities

- T001 and T002 (plan check vs code inventory) touch different files and can run in parallel.
- T009, T010, T011 (unit / invariants / snapshot) are three different test files and can run in parallel after T007.
- T020 and T021 (comment audit vs git scope check) can run in parallel.
- Cross-story parallelism is limited: US1, US2, and US3 all touch `pages/alerts_analysis/population_page.py`, so file-level coordination is required.

## Parallel Example: Phase 1 / US2 test updates / Phase 7

```bash
# Phase 1
Task: "Confirm scope guard in plan.md (T001)"
Task: "Inventory DISTRICT_CHART / skip / locator call sites (T002)"

# After T007
Task: "Update unit test title assertion (T009)"
Task: "Update test_population_invariants.py accessor (T010)"
Task: "Update population_snapshot.py accessor (T011)"

# Phase 7
Task: "Audit in-function comments are English (T020)"
Task: "Verify no off-limits file changed via git status (T021)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (scope + inventory).
2. Phase 2: Foundational (title builder + active-level field).
3. Phase 3: US1 (bilingual page-rail and date fields).
4. **STOP and VALIDATE**: alerts UI suite opens Screen 2 and fills dates with no `LoadTimeoutError`.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 → page opens / dates fill (MVP; kills ERRORs).
3. US2 → live district title; drill-down no longer false-skips.
4. US3 → listbox / show-as-table reads fill district and hour mappings.
5. US4 → confirm skips resolved, guards kept.
6. Polish → English comments, alerts UI smoke gate, unit test, quickstart.

---

## Notes

- [P] tasks = different files, no dependencies.
- The alerts UI smoke gate (T022) MUST pass before this slice is done.
- Keep every `pytest.skip` guard as a safety net for a genuinely absent control.
- Do not edit fleet/status modules, `core/` (incl. `core/components/chart.py`), or the root `conftest.py`; do not change any golden metric value.
- Comments inside new or edited functions are English.
- Commit after each task or logical group.
