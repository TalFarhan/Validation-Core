---

description: "Task list for Generic Slicer Component (Layer 2 + Layer 3 contract)"
---

# Tasks: Generic Slicer Component

**Input**: Design documents from `/specs/002-generic-slicer/`

**Prerequisites**: spec.md (required), architecture.md (required). This specify
pass produced the architectural plan as `architecture.md` rather than
`plan.md` / `research.md`.

**Tests**: Do **not** add or edit files under `tests/ui/fleet_dashboard/`,
`tests/e2e/`, or `conftest.py`. Existing fleet smoke is the contract. Because
this feature touches shared page-object filter surface and `core/`,
`pytest tests/ui/fleet_dashboard/` is **MANDATORY** after each major Strangler
step and at completion.

**Organization**: Strangler Fig (architecture.md). User stories share
`core/components/slicer.py` and `pages/fleet_dashboard/main_dashboard_page.py`
— implement **sequentially** (US1 → US2 → US3 → US4). Do not start later
stories in parallel on the same files.

**Constitution**: v1.1.0 — zero domain leakage in `core/`; frozen filter APIs
on `MainDashboardPage` (FR-003). Principle VII MUST be amended before moving
filter methods (T006).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: [US1], [US2], [US3], [US4] on user-story tasks only
- Include exact file paths in descriptions

## Path Conventions

- Layer 0 (do not move filters here): `core/portal/page.py`
- Layer 2: `core/components/slicer.py`
- Domain: `pages/fleet_dashboard/main_dashboard_page.py`
- Layer 3 data (do not parse from core): `data/filters.json`, `data/filter_matrix.json`
- Domain mapping helper (do not move into core): `tests/helpers/dashboard_validation.py`
- Smoke gate: `tests/ui/fleet_dashboard/`
- Fixture (read-only): `conftest.py`
- Constitution: `.specify/memory/constitution.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline the live suite and add the Layer 2 package without moving behavior

- [x] T001 Record baseline by running `pytest tests/ui/fleet_dashboard/` and note the result (no code changes)
  — Live suite not run here (user owns the gate). Last known green: `1a5f652` ReportShell extraction 100%. Re-verify at T008.
- [x] T002 [P] Create package `core/components/__init__.py` (empty or re-export placeholder only)
- [x] T003 Confirm frozen callers in `tests/ui/fleet_dashboard/test_dashboard_filters.py`, `tests/ui/fleet_dashboard/test_dashboard_smoke.py`, `tests/helpers/dashboard_validation.py`, and `tests/e2e/test_filter_matrix.py` (`select_*`, `apply_filters`, `option`, locator aliases, `clear_all_applied_filters`) and do not edit those files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Empty composed slicer and constitution authorization. No filter methods move yet.

**⚠️ CRITICAL**: No user story method-moves until this phase is complete

- [x] T004 Create `SlicerDefinition` (fields `id`, `role_name`, `kind`, `cascade_rank`, `host`) and `Slicer` in `core/components/slicer.py` with stub methods `select`, `select_many`, `search`, `clear_search`, `clear_all`, `close_open`, `control`, `option_by_role` that are not yet called from the fleet page
- [x] T005 Compose `Slicer` on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` (`self._slicer = ...`) while leaving all current filter method bodies unchanged
- [x] T006 Amend Principle VII and Architecture Constraints in `.specify/memory/constitution.md` to authorize Layer 2 slicer chrome in `core/components/` while keeping KPI/tabs/charts/tables/drilldown on the domain page; bump constitution version per Governance (MINOR)
- [x] T007 [P] Update the layer table in `README.md` to document Layer 2 (`core/components/`) and Layer 3 (`data/filters.json`, `data/filter_matrix.json`) without moving code
- [ ] T008 Run `pytest tests/ui/fleet_dashboard/` — MUST pass (behavior still entirely on the page object)
  — **STOP**: user runs this gate before Phase 3.

**Checkpoint**: `MainDashboardPage` holds a `Slicer`. Import
`from core.components.slicer import Slicer` works. Principle VII no longer
blocks the extraction. Foundation ready.

---

## Phase 3: User Story 1 - Same filter path after extraction (Priority: P1) 🎯 MVP

**Goal**: Testers still select, apply, cascade, and clear filters through frozen
`MainDashboardPage` APIs. Interaction relocates incrementally without changing
outcomes.

**Independent Test**: `pytest tests/ui/fleet_dashboard/` is 100% green.
`select_district`, `apply_filters`, `option`, and locator aliases still resolve
on `MainDashboardPage`. `conftest.py` unchanged.

### Implementation for User Story 1

- [x] T009 [US1] Move `_close_open_slicers` from `pages/fleet_dashboard/main_dashboard_page.py` into `Slicer.close_open` in `core/components/slicer.py`; fleet method becomes a one-line delegate; run `pytest tests/ui/fleet_dashboard/`
  — Live pytest deferred to user (Phase 3 pause).
- [x] T010 [US1] Move `option(option_name, listbox_name)` body into `Slicer.option_by_role` in `core/components/slicer.py`; keep the two-arg `MainDashboardPage.option` signature tests use (including literal `"SubUnit"`); run `pytest tests/ui/fleet_dashboard/`
  — Live pytest deferred to user (Phase 3 pause).
- [x] T011 [US1] Move `_dropdown_shows_selection` and `_select_dropdown_option` into `Slicer.select` (dropdown kind) in `core/components/slicer.py`; inject a domain settle hook so the moved body does not name `total_vehicles_kpi` / `get_kpi_value`; preserve retry-once and `log_filter`; run `pytest tests/ui/fleet_dashboard/`
  — Live pytest deferred to user (Phase 3 pause).
- [x] T012 [US1] Change `select_district`, `select_sub_unit`, `select_source`, and `select_category` in `pages/fleet_dashboard/main_dashboard_page.py` into Allure wrappers that call `self._slicer.select(<id>, name)` with page-owned ids; keep method names and signatures; run `pytest tests/ui/fleet_dashboard/`
  — Live pytest deferred to user (Phase 3 pause).
- [x] T013 [US1] Move clear-all click into `Slicer.clear_all` in `core/components/slicer.py` using the generic clear-all name pattern; `clear_all_applied_filters` on `MainDashboardPage` delegates then settle; run `pytest tests/ui/fleet_dashboard/`
  — Live pytest deferred to user (Phase 3 pause).
- [x] T014 [US1] Point locator aliases `district_dropdown`, `sub_unit_dropdown`, `source_dropdown`, `category_dropdown`, and `clear_filters_btn` in `pages/fleet_dashboard/main_dashboard_page.py` at `self._slicer.control(...)` / clear-all control so `test_dashboard_smoke.py` visibility checks stay valid; run `pytest tests/ui/fleet_dashboard/`
  — **STOP**: user runs this gate before Phase 4.

**Checkpoint**: MVP — dropdown select, option lookup, close-open, and clear-all
work through `Slicer` with frozen page APIs. Smoke 100% green. Do not proceed
if T014 smoke fails.

---

## Phase 4: User Story 2 - Generic slicer knows how; domain knows what (Priority: P1)

**Goal**: Layer 2 has zero fleet terms. Settle is domain-supplied. Definitions
(role names, kinds) live on the fleet page. A second report could pass a
different definition list.

**Independent Test**: Grep `core/` for vehicles, district, subunit, fleet KPI
titles, `total_vehicles`, `select_district`, `reset_dashboard_filters`, `מחוז`,
`רכבים` — zero matches. Fleet page owns `_SLICER_LISTBOXES` / definition list
and the settle hook.

### Implementation for User Story 2

- [x] T015 [US2] Move fleet slicer accessible names into a page-owned `SlicerDefinition` list on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` (Unit, SubUnit, VehicleSource, VehicleCategory); `Slicer` in `core/components/slicer.py` reads only `definitions` and MUST NOT hardcode those role names
- [x] T016 [US2] Implement `MainDashboardPage` settle hook in `pages/fleet_dashboard/main_dashboard_page.py` (dismiss via ready/KPI locator + optional `wait_for_kpi_update` on total/in_use, matching today's post-select wait); confirm `core/components/slicer.py` only calls the hook
- [x] T017 [US2] Implement `Slicer.select_many` for `kind=checkbox` in `core/components/slicer.py` (open, tick values, dismiss, settle). No fleet wrapper rewrite. Do not change fleet dropdowns to checkboxes
- [x] T018 [US2] Search `core/` (including `core/components/slicer.py` and `core/portal/page.py`) for leakage tokens `vehicles`, `district`, `subunit`, `sub_unit`, `total_vehicles`, `select_district`, `רכבים`, `מחוז`, `reset_dashboard_filters` and remove any hits
- [ ] T019 [US2] Run `pytest tests/ui/fleet_dashboard/` — MUST pass after hook-only settle and leakage cleanup
  — **STOP**: user runs this gate before Phase 5.

**Checkpoint**: A second report could supply definitions + settle without
inheriting fleet district methods.

---

## Phase 5: User Story 3 - Filter data stays a domain catalog (Priority: P2)

**Goal**: `filters.json` / `filter_matrix.json` keep their shapes. Alias
resolution stays outside `core/`. `apply_filters` uses cascade rank from
definitions. Search is a search-kind slicer with fleet wrappers.

**Independent Test**: Existing helper `apply_filters` in
`tests/helpers/dashboard_validation.py` still resolves aliases and calls
`dashboard.apply_filters(...)`. `core/` does not import `data/filters.json`.
Cascade still applies district before sub-unit.

### Implementation for User Story 3

- [x] T020 [US3] Implement cascade-ordered apply in `Slicer` (sort requested ids by `cascade_rank`, then stable order) in `core/components/slicer.py`; change `apply_filters` in `pages/fleet_dashboard/main_dashboard_page.py` to pass only provided ids/labels — keep kwargs `district`, `sub_unit`, `category`, `source`
- [x] T021 [US3] Move vehicle search fill/submit/clear into `Slicer.search` / `clear_search` with `host=visual_sandbox` in `core/components/slicer.py`; `search_vehicle`, `clear_vehicle_search`, and `vehicle_search` on `MainDashboardPage` remain the public names
- [x] T022 [US3] Change `reset_dashboard_filters` in `pages/fleet_dashboard/main_dashboard_page.py` to orchestrate `clear_search` + `clear_all` (same short-circuit when already clear); `after_navigate` still calls `reset_dashboard_filters`
- [x] T023 [US3] Verify `tests/helpers/dashboard_validation.py` `FILTER_SECTIONS` and `resolve_filter_values` stay out of `core/`; `conftest.py` still loads `data/filters.json` and `data/filter_matrix.json`; do not change those JSON shapes
- [x] T024 [US3] Document the three-artifact contract (definitions vs catalog vs matrix) by keeping `specs/002-generic-slicer/architecture.md` Configuration Contract as the source of truth; add a short pointer in `docs/COVERAGE_CATALOG.md` section 2 that slicer *mechanics* live in Layer 2 and values stay in `data/filters.json`
- [ ] T025 [US3] Run `pytest tests/ui/fleet_dashboard/` — MUST pass
  — **STOP**: user runs this gate before Phase 6.

**Checkpoint**: Layer 3 data still drives tests; Layer 2 only sees resolved
labels. Search + reset delegate to `Slicer`.

---

## Phase 6: User Story 4 - Incremental swap stays green (Priority: P2)

**Goal**: No duplicated click-and-retry loop on the fleet page. Wrappers only.
Each prior gate already ran smoke; this phase is the final deletion audit.

**Independent Test**: `MainDashboardPage` no longer defines dropdown click
loops, Escape-close internals, or clear-all click internals except as
delegates. KPI/tab/chart/table methods remain. Smoke still passes.

### Implementation for User Story 4

- [x] T026 [US4] Delete leftover bodies of moved filter helpers (`_select_dropdown_option`, `_dropdown_shows_selection`, `_close_open_slicers` implementations) from `pages/fleet_dashboard/main_dashboard_page.py` so they resolve only via `self._slicer`
- [x] T027 [US4] Verify fleet-only APIs (`get_kpi_value`, `click_tab`, `search_vehicle` name, chart/tooltip/drilldown) remain in `pages/fleet_dashboard/main_dashboard_page.py` and were not copied into `core/components/slicer.py` or `core/portal/page.py`
- [x] T028 [US4] Verify `conftest.py` is unmodified and `after_navigate` on `MainDashboardPage` still resets filters without Layer 0 importing `Slicer`
- [ ] T029 [US4] Run `pytest tests/ui/fleet_dashboard/` — MUST pass
  — **STOP**: user runs the final smoke gate.

**Checkpoint**: Domain page is wrappers + definitions + settle. All four
stories independently checkable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Leakage, docs, and the binding gate

- [x] T030 Repeat leakage grep on `core/` (tokens from T018) and fix any remaining hits
- [x] T031 Confirm Allure steps on fleet wrappers and CSV `log_filter` / `log_ui` lines still fire for select, apply, clear, and reset
- [ ] T032 Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%. Do not declare the feature done if this fails
  — Same gate as T029; user runs live suite.
- [ ] T033 If portal/data environment allows, run `pytest tests/e2e/test_filter_matrix.py` (or the full `tests/e2e/` filter callers) and confirm green without test edits

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
  (especially T006 constitution amendment)
- **US1 (Phase 3)**: Depends on Foundational — MVP
- **US2 (Phase 4)**: Depends on US1 select/clear already delegating
- **US3 (Phase 5)**: Depends on US2 definitions + settle
- **US4 (Phase 6)**: Depends on US1–US3 moves; deletion audit only
- **Polish (Phase 7)**: Depends on US4

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational. Delivers frozen-API filter path.
- **User Story 2 (P1)**: After US1. Leakage + settle + checkbox kind.
- **User Story 3 (P2)**: After US2. Catalog/cascade/search contract.
- **User Story 4 (P2)**: After US3. Strangler completion / no dual implementation.

Stories share two files — **do not parallelize US1–US4**. T002/T007 may run
in parallel with other Setup/Foundational tasks on different files.

### Parallel Opportunities

- T002 and T003 after T001
- T007 in parallel with T004–T006 (different files)
- T017 (checkbox) may overlap with T018 only if T017 does not reintroduce
  fleet names; prefer sequential on `slicer.py`

---

## Parallel Example: Foundational

```text
Task: "Create Slicer stubs in core/components/slicer.py"
Task: "Update README.md layer table"
```

Do **not** parallelize moves inside `main_dashboard_page.py`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — includes constitution amend)
3. Complete Phase 3: User Story 1 (through T014)
4. **STOP and VALIDATE**: `pytest tests/ui/fleet_dashboard/`
5. Continue only if smoke is 100% green

### Incremental Delivery

1. Setup + Foundational → empty composed slicer, Principle VII updated
2. US1 → dropdown/clear wrappers, smoke green (MVP)
3. US2 → zero leakage + settle hook + checkbox kind
4. US3 → cascade apply + search + catalog stays in `data/`
5. US4 → delete leftover bodies
6. Polish → leakage grep + binding gate

### Strangler Fig Reminders

- After every major move (T009–T014, T019, T025, T029, T032) the smoke suite
  is a GATE, not a suggestion
- Never delete a fleet wrapper in the same task that first adds an unused stub
- Never load `data/filters.json` from `core/`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to US1–US4
- Do not edit test modules or `conftest.py`
- Commit after each GATE if the user requests commits
- Stop at any checkpoint to validate independently
- Avoid: putting Unit/SubUnit strings in `core/`, waiting on KPI names inside
  `Slicer`, renaming `apply_filters` kwargs, big-bang deletion of old methods
