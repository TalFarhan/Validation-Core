---

description: "Task list for Extract Generic ReportShell (Layer 0)"
---

# Tasks: Extract Generic ReportShell

**Input**: Design documents from `/specs/001-extract-report-shell/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/report-shell-api.md, quickstart.md

**Tests**: Do **not** add or edit files under `tests/ui/fleet_dashboard/`, `tests/e2e/`, or `conftest.py`. Existing fleet smoke is the contract. Because this feature touches `core/portal` / `ReportShell`, `pytest tests/ui/fleet_dashboard/` is **MANDATORY** after each major Strangler step and at completion.

**Organization**: Strangler Fig (plan.md). User stories share `core/portal/page.py` and `pages/fleet_dashboard/main_dashboard_page.py` — implement **sequentially** (US1 → US2 → US3). Do not start US2/US3 in parallel.

**Constitution**: v1.0.0 — zero domain leakage in `core/`; frozen `navigate(self, *, force_reload: bool = False) -> None`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: [US1], [US2], [US3] on user-story tasks only
- Include exact file paths in descriptions

## Path Conventions

- Layer 0: `core/portal/page.py`
- Domain: `pages/fleet_dashboard/main_dashboard_page.py`
- Foundation: `pages/base_page.py` (do not rewrite)
- Smoke gate: `tests/ui/fleet_dashboard/`
- Fixture (read-only): `conftest.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline the live suite and add the Layer 0 package without moving behavior

- [x] T001 Record baseline by running `pytest tests/ui/fleet_dashboard/` and note the result (no code changes)
- [x] T002 [P] Create package `core/portal/__init__.py` (empty or re-export placeholder only)
- [x] T003 Confirm fixture callers in `conftest.py` (`navigate`, `_dashboard_ready`, `_recover_from_portal_glitch`, `_is_portal_profile_error`) and do not edit that file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Empty inheriting shell so later moves have a home. No portal methods move yet.

**⚠️ CRITICAL**: No user story method-moves until this phase is complete

- [x] T004 Create `ReportShell(BasePage)` in `core/portal/page.py` with `_report_ready_locator(self)` raising `NotImplementedError` and `after_navigate(self)` as a no-op
- [x] T005 Change `MainDashboardPage` to inherit `ReportShell` instead of `BasePage` in `pages/fleet_dashboard/main_dashboard_page.py`
- [x] T006 Override `_report_ready_locator` on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` to return `self.total_vehicles_kpi` (locator only; do not move methods)
- [x] T007 Run `pytest tests/ui/fleet_dashboard/` — MUST pass (behavior still entirely on the subclass)

**Checkpoint**: `MainDashboardPage` is a `ReportShell`. Import `from core.portal.page import ReportShell` works. Foundation ready.

---

## Phase 3: User Story 1 - Same fleet open-and-ready path (Priority: P1) 🎯 MVP

**Goal**: Testers still open the fleet report via `navigate(*, force_reload=False)`. Portal login, catalog, iframe, and ready-wait keep working while methods migrate. Filter reset still runs after open/reuse.

**Independent Test**: `pytest tests/ui/fleet_dashboard/` is 100% green. `conftest.py` still constructs `MainDashboardPage` and calls `navigate` unchanged.

### Tests for User Story 1

Existing smoke is the test. Do not write new test modules.

- [x] T008 [US1] Rewire `_dashboard_ready` in `pages/fleet_dashboard/main_dashboard_page.py` to use iframe wait plus `self._report_ready_locator()` (stop naming `self.total_vehicles_kpi` inside `_dashboard_ready`)
- [x] T009 [US1] Implement `after_navigate` on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` as `self.reset_dashboard_filters()` and switch both `navigate` call sites that reset filters to `self.after_navigate()`
- [x] T010 [US1] Rewire the ready-wait loop in `navigate` and in `reload_and_measure_ready_ms` in `pages/fleet_dashboard/main_dashboard_page.py` to poll `_report_ready_locator()` instead of `self.total_vehicles_kpi`
- [x] T011 [US1] Run `pytest tests/ui/fleet_dashboard/` after in-place hooks (Strangler step 2 GATE)

### Implementation for User Story 1

- [x] T012 [US1] Move leaf helpers `_portal_search_box`, `_all_products_control`, `_dashboard_iframe`, `_click_even_if_hidden`, `_is_portal_home`, `_hitachbrut_button`, `_is_login_page`, `_page_debug_summary`, `_is_portal_profile_error` from `pages/fleet_dashboard/main_dashboard_page.py` to `core/portal/page.py`; delete the fleet copies; run `pytest tests/ui/fleet_dashboard/`
- [x] T013 [US1] Move `_recover_from_portal_glitch` and `_wait_for_dashboard_iframe` from `pages/fleet_dashboard/main_dashboard_page.py` to `core/portal/page.py` (auth may still resolve on the subclass); run `pytest tests/ui/fleet_dashboard/`
- [x] T014 [US1] Move `_open_all_products_catalog` and `_open_dashboard_via_portal_search` from `pages/fleet_dashboard/main_dashboard_page.py` to `core/portal/page.py`; comments must use `settings.DASHBOARD_SEARCH_TERM` only (no fleet product name); run `pytest tests/ui/fleet_dashboard/`
- [x] T015 [US1] Move `_auto_click_hitachbrut` and `_ensure_authenticated` from `pages/fleet_dashboard/main_dashboard_page.py` to `core/portal/page.py`; they MUST call hook-based `_dashboard_ready` / `_report_ready_locator`, never `total_vehicles_kpi`; run `pytest tests/ui/fleet_dashboard/`
- [x] T016 [US1] Move `navigate` and `reload_and_measure_ready_ms` to `core/portal/page.py` with frozen signatures `navigate(self, *, force_reload: bool = False) -> None` and `reload_and_measure_ready_ms(self) -> int`; `navigate` MUST call `after_navigate()` on reuse and after cold load; keep `_dashboard_ready` name for `conftest.py`; run `pytest tests/ui/fleet_dashboard/`

**Checkpoint**: MVP — open/reuse/auth/catalog/ready path works from the shell. Smoke 100% green. Do not proceed if T016 smoke fails.

---

## Phase 4: User Story 2 - Report-ready comes from the domain page (Priority: P1)

**Goal**: Layer 0 waits only on the domain hook. `core/` has zero fleet terms. Reload timing uses the same hook as `navigate`.

**Independent Test**: Grep `core/` for vehicles, district, subunit, fleet KPI/chart titles, `total_vehicles`, `reset_dashboard_filters` — zero matches. `MainDashboardPage._report_ready_locator` is the only ready visual binding. `reload_and_measure_ready_ms` still feeds `test_dashboard_loads_within_sla` in `tests/ui/fleet_dashboard/test_dashboard_smoke.py`.

### Implementation for User Story 2

- [x] T017 [US2] Implement `_dashboard_ready` / `_report_ready` on `ReportShell` in `core/portal/page.py` as iframe visible AND `_report_ready_locator()` visible; remove any remaining `_dashboard_ready` body from `pages/fleet_dashboard/main_dashboard_page.py`
- [x] T018 [US2] Confirm `reload_and_measure_ready_ms` in `core/portal/page.py` polls only `_report_ready_locator()` (no fleet KPI attribute or title)
- [x] T019 [US2] Search `core/` (including `core/portal/page.py`) for leakage tokens `vehicles`, `district`, `subunit`, `sub_unit`, `total_vehicles`, `רכבים`, `מחוז`, `reset_dashboard_filters` and remove any hits
- [x] T020 [US2] Run `pytest tests/ui/fleet_dashboard/` — MUST pass after hook-only ready and leakage cleanup

**Checkpoint**: A second report could override `_report_ready_locator` without inheriting fleet KPI names.

---

## Phase 5: User Story 3 - Fleet page is a report on top of the shell (Priority: P2)

**Goal**: Fleet page owns only domain visuals. Portal methods live once, on `ReportShell`. Allure/CSV evidence remains. Inheritance is `BasePage` → `ReportShell` → `MainDashboardPage`.

**Independent Test**: `MainDashboardPage` no longer defines moved portal methods (except hook overrides and optional Allure wrappers). KPI, slicer, table, and chart methods remain in `pages/fleet_dashboard/main_dashboard_page.py`. Smoke still passes.

### Implementation for User Story 3

- [x] T021 [US3] Add a thin `navigate` wrapper on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` with `@allure.step("Navigate to Fleet Dashboard")` that only calls `super().navigate(*, force_reload=force_reload)` (same signature)
- [x] T022 [US3] Add a thin `reload_and_measure_ready_ms` wrapper on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` if the current Allure title must stay fleet-specific; otherwise leave the shell method and keep CSV `log_ui` lines in `core/portal/page.py` generic
- [x] T023 [US3] Delete any leftover bodies of FR-010 portal methods from `pages/fleet_dashboard/main_dashboard_page.py` so they resolve only via inheritance from `core/portal/page.py`
- [x] T024 [US3] Verify fleet-only APIs (`select_district`, `apply_filters`, `get_kpi_value`, `search_vehicle`, `hover_chart`, drilldown) remain in `pages/fleet_dashboard/main_dashboard_page.py` and were not copied into `core/portal/page.py`
- [x] T025 [US3] Verify `conftest.py` is unmodified and still resolves `_dashboard_ready`, `_recover_from_portal_glitch`, and `_is_portal_profile_error` on `MainDashboardPage`
- [x] T026 [US3] Run `pytest tests/ui/fleet_dashboard/` — MUST pass

**Checkpoint**: Domain page is a report on the shell. All three stories independently checkable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final contract and docs. Depends on US1–US3.

- [x] T027 Re-run leakage scan on `core/` per `specs/001-extract-report-shell/contracts/report-shell-api.md`
- [x] T028 Confirm `pages/base_page.py` and `db/` were not modified
- [x] T029 [P] Tick the Done-when checklist in `specs/001-extract-report-shell/quickstart.md`
- [x] T030 Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100% (final constitution gate)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — MVP
- **US2 (Phase 4)**: Depends on US1 T016 (orchestrators on the shell) — same files, not parallel
- **US3 (Phase 5)**: Depends on US1 T016 (and should follow US2 leakage cleanup)
- **Polish (Phase 6)**: Depends on US1–US3

### User Story Dependencies

- **User Story 1 (P1)**: After Phase 2. Delivers the frozen `navigate` path. MVP.
- **User Story 2 (P1)**: After US1. Hook purity + leakage. Not a second parallel track.
- **User Story 3 (P2)**: After US1 (wrappers + leftover deletion). After US2 preferred so wrappers are not added into a leaking shell.

### Within Each User Story

- In-place hooks before any method move (US1 T008–T011 before T012–T016)
- Leaves → recovery → catalog → auth → orchestrators (never skip to `navigate` first)
- Smoke after each move group
- Do not import `pages.fleet_dashboard` from `core/`

### Parallel Opportunities

- T002 can run beside T001/T003 (different files)
- T029 can run beside T027/T028
- **No parallel user stories**: both implementation files are shared
- Do not mark move tasks [P]

---

## Parallel Example: Setup only

```text
Task: "T001 Record baseline pytest tests/ui/fleet_dashboard/"
Task: "T002 Create core/portal/__init__.py"
```

Do **not** parallelize US1 move groups.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (empty shell + inherit)
3. Complete Phase 3: US1 (hooks in place, then Strangler moves)
4. **STOP and VALIDATE**: `pytest tests/ui/fleet_dashboard/`
5. Demo: same `navigate` signature, smoke green

### Incremental Delivery (Strangler Fig)

1. Setup + Foundational → inheriting empty shell
2. US1 in-place hooks → smoke
3. US1 leaf → recovery → catalog → auth → orchestrators (smoke after each)
4. US2 hook-only ready + leakage grep → smoke
5. US3 Allure wrappers + leftover deletion → smoke
6. Polish final gate

### Parallel Team Strategy

Single implementer recommended. Two people on the same two files will conflict. If staffed: one person owns `core/portal/page.py` moves, the other only reviews leakage and runs smoke — do not split US1/US2/US3 across writers.

---

## Notes

- [P] tasks = different files, no dependencies
- [USn] maps to spec.md user stories
- Commit after each GATE task (T007, T011, T012–T016, T020, T026, T030)
- Never edit `conftest.py` or test modules to make a task pass
- `core/` MUST stay free of vehicles, district, and fleet KPI titles
- Formal sample tasks from the template were replaced; do not reintroduce them
