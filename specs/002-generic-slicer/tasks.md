---

description: "Task list for Generic Slicer Component (Layer 2 + Layer 3 contract)"
---

# Tasks: Generic Slicer Component

**Input**: Design documents from `/specs/002-generic-slicer/`

**Prerequisites**: spec.md (required), architecture.md (required). This feature's
architectural plan is `architecture.md` rather than `plan.md` / `research.md`.

**Tests**: Do **not** add or edit files under `tests/ui/fleet_dashboard/`,
`tests/e2e/`, or `conftest.py`. Existing fleet smoke is the contract. Because
this feature touches shared page-object filter surface and `core/`,
`pytest tests/ui/fleet_dashboard/` is **MANDATORY** as the Quality Gate at the
end of each phase except P2 and P8.

**Organization**: Chronological Strangler Fig (architecture.md), phases **P0–P9**.
User stories are **tags only** (`[US1]`, `[US2]`, `[US3]`, `[US4]`) on the
tasks they trace to. They are **not** phases, headers, or execution units.
US4 is cleanup metadata on P9 tasks, not a delivery phase.

Implement **strictly P0 → P9**. Do not start a later phase in parallel on
`core/components/slicer.py` or `pages/fleet_dashboard/main_dashboard_page.py`.

**Constitution**: v1.1.0 — zero domain leakage in `core/`; frozen filter APIs
on `MainDashboardPage` (FR-003). Principle VII MUST be amended in P1 before
any filter method moves (P3+).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: `[US1]`, `[US2]`, `[US3]`, `[US4]` metadata on the implementing
  task only — never a section heading
- **GATE**: Exactly one Quality Gate task ends P0, P1, P3, P4, P5, P6, P7, and
  P9. P2 and P8 have no fleet pytest gate. Implementation tasks MUST NOT embed
  a `pytest` run
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

## Quality Gates (normative)

| Phase | Fleet pytest gate? | Command |
|-------|--------------------|---------|
| P0, P1, P3, P4, P5, P6, P7 | Yes — exactly one GATE task | `pytest tests/ui/fleet_dashboard/` |
| P2, P8 | **No** | — |
| P9 | Yes — smoke **and** e2e in the single GATE task | `pytest tests/ui/fleet_dashboard/` and, if the environment allows, `pytest tests/e2e/test_filter_matrix.py` |

**STOP** at every GATE. The user runs the live suite. Do not start the next
phase if the gate is red.

---

## P0: Baseline

**Purpose**: Record the live suite and frozen callers. No code changes.

- [ ] T001 Confirm frozen callers in `tests/ui/fleet_dashboard/test_dashboard_filters.py`, `tests/ui/fleet_dashboard/test_dashboard_smoke.py`, `tests/helpers/dashboard_validation.py`, and `tests/e2e/test_filter_matrix.py` (`select_*`, `apply_filters`, `option`, locator aliases, `clear_all_applied_filters`) and do not edit those files
- [ ] T002 GATE: Run `pytest tests/ui/fleet_dashboard/` and record the baseline result (no code changes)

**Checkpoint**: Callers and baseline are known. Behavior is unchanged.

---

## P1: Empty Compose & Constitution

**Purpose**: Introduce Layer 2 unused, authorize it in the constitution, and
compose it on the fleet page. No filter methods move yet.

**⚠️ CRITICAL**: No method-moves (P3+) until this phase is complete, including
its GATE.

- [ ] T003 [P] Create package `core/components/__init__.py` (empty or re-export placeholder only)
- [ ] T004 Create `Slicer` in `core/components/slicer.py` with stub methods `select`, `select_many`, `search`, `clear_search`, `clear_all`, `close_open`, `control`, `option_by_role` that are not yet called from the fleet page
- [ ] T005 Compose `Slicer` on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` (`self._slicer = ...`) while leaving all current filter method bodies unchanged
- [ ] T006 Amend Principle VII and Architecture Constraints in `.specify/memory/constitution.md` to authorize Layer 2 slicer chrome in `core/components/` while keeping KPI/tabs/charts/tables/drilldown on the domain page; bump constitution version per Governance (MINOR)
- [ ] T007 [P] Update the layer table in `README.md` to document Layer 2 (`core/components/`) and Layer 3 (`data/filters.json`, `data/filter_matrix.json`) without moving code
- [ ] T008 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100% (behavior still entirely on the page object)

**Checkpoint**: `MainDashboardPage` holds a `Slicer`. Import
`from core.components.slicer import Slicer` works. Principle VII no longer
blocks the extraction. Stubs are unused.

---

## P2: Definitions + Settle

**Purpose**: Domain supplies *what* (definitions) and *when settled* (hook)
before any interaction moves. Tag: US2. **No fleet pytest gate.**

- [ ] T009 [US2] Introduce `SlicerDefinition` (fields `id`, `role_name`, `kind`, `cascade_rank`, `host`) in `core/components/slicer.py` and move fleet slicer accessible names into a page-owned definition list on `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` (Unit, SubUnit, VehicleSource, VehicleCategory); `Slicer` reads only `definitions` and MUST NOT hardcode those role names
- [ ] T010 [US2] Implement `MainDashboardPage` settle hook in `pages/fleet_dashboard/main_dashboard_page.py` (dismiss via ready/KPI locator + optional `wait_for_kpi_update` on total/in_use, matching today's post-select wait); wire it into `Slicer` construction so `core/components/slicer.py` only calls the hook

**Checkpoint**: A second report could supply definitions + settle without
inheriting fleet district methods. Interaction still lives on the page.

---

## P3: Close-open + Option

**Purpose**: First Strangler move — close leftover lists and option lookup.
Tag: US1.

- [ ] T011 [US1] Move `_close_open_slicers` from `pages/fleet_dashboard/main_dashboard_page.py` into `Slicer.close_open` in `core/components/slicer.py`; fleet method becomes a one-line delegate
- [ ] T012 [US1] Move `option(option_name, listbox_name)` body into `Slicer.option_by_role` in `core/components/slicer.py`; keep the two-arg `MainDashboardPage.option` signature tests use (including literal `"SubUnit"`)
- [ ] T013 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%

**Checkpoint**: Close-open and option lookup go through `Slicer` with frozen
page APIs. Smoke green.

---

## P4: Dropdown select + wrappers

**Purpose**: Move dropdown select into Layer 2; fleet `select_*` methods become
Allure wrappers; dropdown locator aliases point at `Slicer.control`. Tag: US1.

- [ ] T014 [US1] Move `_dropdown_shows_selection` and `_select_dropdown_option` into `Slicer.select` (dropdown kind) in `core/components/slicer.py`; call the domain settle hook so the moved body does not name `total_vehicles_kpi` / `get_kpi_value`; preserve retry-once and `log_filter`
- [ ] T015 [US1] Change `select_district`, `select_sub_unit`, `select_source`, and `select_category` in `pages/fleet_dashboard/main_dashboard_page.py` into Allure wrappers that call `self._slicer.select(<id>, name)` with page-owned ids; keep method names and signatures
- [ ] T016 [US1] Point locator aliases `district_dropdown`, `sub_unit_dropdown`, `source_dropdown`, and `category_dropdown` in `pages/fleet_dashboard/main_dashboard_page.py` at `self._slicer.control(...)` so `test_dashboard_smoke.py` visibility checks stay valid
- [ ] T017 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%

**Checkpoint**: MVP path — dropdown select works through `Slicer` with frozen
page APIs. Smoke green. Do not proceed if T017 fails.

---

## P5: Clear-all

**Purpose**: Move clear-all click into Layer 2. Tag: US1.

- [ ] T018 [US1] Move clear-all click into `Slicer.clear_all` in `core/components/slicer.py` using the generic clear-all name pattern; `clear_all_applied_filters` on `MainDashboardPage` delegates then settle; point `clear_filters_btn` at the slicer clear-all control
- [ ] T019 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%

**Checkpoint**: Clear-all delegates to `Slicer`. Search clear still on the
page until P6. Smoke green.

---

## P6: Search + reset

**Purpose**: Move search fill/submit/clear; fleet reset orchestrates both
delegates. Tag: US3.

- [ ] T020 [US3] Move vehicle search fill/submit/clear into `Slicer.search` / `clear_search` with `host=visual_sandbox` in `core/components/slicer.py`; `search_vehicle`, `clear_vehicle_search`, and `vehicle_search` on `MainDashboardPage` remain the public names
- [ ] T021 [US3] Change `reset_dashboard_filters` in `pages/fleet_dashboard/main_dashboard_page.py` to orchestrate `clear_search` + `clear_all` (same short-circuit when already clear); `after_navigate` still calls `reset_dashboard_filters`
- [ ] T022 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%

**Checkpoint**: Search + reset delegate to `Slicer`. Smoke green.

---

## P7: Cascade apply + Layer 3 contract

**Purpose**: Config-driven apply uses cascade rank; JSON catalogs stay outside
`core/`. Tag: US3.

- [ ] T023 [US3] Implement cascade-ordered apply in `Slicer` (sort requested ids by `cascade_rank`, then stable order) in `core/components/slicer.py`; change `apply_filters` in `pages/fleet_dashboard/main_dashboard_page.py` to pass only provided ids/labels — keep kwargs `district`, `sub_unit`, `category`, `source`
- [ ] T024 [P] [US3] Verify `tests/helpers/dashboard_validation.py` `FILTER_SECTIONS` and `resolve_filter_values` stay out of `core/`; `conftest.py` still loads `data/filters.json` and `data/filter_matrix.json`; do not change those JSON shapes
- [ ] T025 [P] [US3] Document the three-artifact contract (definitions vs catalog vs matrix) by keeping `specs/002-generic-slicer/architecture.md` Configuration Contract as the source of truth; add a short pointer in `docs/COVERAGE_CATALOG.md` section 2 that slicer *mechanics* live in Layer 2 and values stay in `data/filters.json`
- [ ] T026 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%

**Checkpoint**: Layer 3 data still drives tests; Layer 2 only sees resolved
labels. Cascade still applies parent before child via rank, not fleet names
in `core/`. Smoke green.

---

## P8: Checkbox select_many

**Purpose**: Generic checkbox path exists for a future report. Tag: US2.
**No fleet pytest gate.**

- [ ] T027 [US2] Implement `Slicer.select_many` for `kind=checkbox` in `core/components/slicer.py` (open, tick values, dismiss, settle). No fleet wrapper rewrite. Do not change fleet dropdowns to checkboxes

**Checkpoint**: Layer 2 matches the spec for checkbox kind. Fleet wrappers
still call single-select dropdown behavior.

---

## P9: Cleanup, Leakage, Allure

**Purpose**: Delete leftover bodies, one leakage grep, observability check,
then the binding gates. Tag: US4 is cleanup metadata only — not a phase name
for delivery.

- [ ] T028 [US4] Delete leftover bodies of moved filter helpers (`_select_dropdown_option`, `_dropdown_shows_selection`, `_close_open_slicers` implementations) from `pages/fleet_dashboard/main_dashboard_page.py` so they resolve only via `self._slicer`
- [ ] T029 [US4] Verify fleet-only APIs (`get_kpi_value`, `click_tab`, `search_vehicle` name, chart/tooltip/drilldown) remain in `pages/fleet_dashboard/main_dashboard_page.py` and were not copied into `core/components/slicer.py` or `core/portal/page.py`
- [ ] T030 [US4] Verify `conftest.py` is unmodified and `after_navigate` on `MainDashboardPage` still resets filters without Layer 0 importing `Slicer`
- [ ] T031 [US4] Run a **single** leakage grep on `core/` (including `core/components/slicer.py` and `core/portal/page.py`) for tokens `vehicles`, `district`, `subunit`, `sub_unit`, `total_vehicles`, `select_district`, `רכבים`, `מחוז`, `reset_dashboard_filters` and remove any hits
- [ ] T032 [US4] Confirm Allure steps on fleet wrappers and CSV `log_filter` / `log_ui` lines still fire for select, apply, clear, and reset
- [ ] T033 GATE: Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100%. If portal/data environment allows, also run `pytest tests/e2e/test_filter_matrix.py` (or the full `tests/e2e/` filter callers) and confirm green without test edits. Do not declare the feature done if smoke fails

**Checkpoint**: Domain page is wrappers + definitions + settle. One leakage
grep, observability intact, smoke (and e2e when run) green.

---

## Dependencies & Execution Order

### Phase Dependencies

Phases are sequential. Do not skip ahead.

- **P0 Baseline**: No dependencies — start immediately
- **P1 Empty Compose & Constitution**: Depends on P0. BLOCKS all method-moves
  (especially T006 constitution amendment)
- **P2 Definitions + Settle**: Depends on P1. No GATE. BLOCKS P3+ moves that
  need definitions or the settle hook
- **P3 Close-open + Option**: Depends on P2. First interaction move (US1)
- **P4 Dropdown select + wrappers**: Depends on P3. Uses the P2 settle hook (US1)
- **P5 Clear-all**: Depends on P4 (US1)
- **P6 Search + reset**: Depends on P5 so reset can orchestrate both delegates (US3)
- **P7 Cascade apply + Layer 3 contract**: Depends on P6 (US3)
- **P8 Checkbox select_many**: Depends on P2 definitions/kinds. May follow P7
  so it does not block apply. No GATE (US2)
- **P9 Cleanup, Leakage, Allure**: Depends on P3–P8 moves being complete (US4
  tags only)

### User Story Tags (not phases)

- **US1**: Frozen-API filter path — tagged on P3, P4, P5 tasks
- **US2**: Zero leakage, definitions, settle, checkbox — tagged on P2 and P8 tasks
- **US3**: Catalog, cascade, search, reset — tagged on P6 and P7 tasks
- **US4**: Strangler completion / no dual implementation — tagged on P9 tasks only

Stories share two files — **do not parallelize phases**. T003/T007 and
T024/T025 may run in parallel with other tasks **in the same phase** on
different files.

### Parallel Opportunities

- T003 (`core/components/__init__.py`) in parallel with T006 (constitution)
  and T007 (`README.md`)
- T024 and T025 in P7 (helper/JSON verify vs docs) after T023
- T029–T032 in P9 after T028, on review/grep/docs rather than the same edit
  to `slicer.py`
- Do **not** parallelize moves inside `main_dashboard_page.py`

---

## Parallel Example: P1

```text
Task: "Create Slicer stubs in core/components/slicer.py"
Task: "Update README.md layer table"
```

Do **not** parallelize moves inside `main_dashboard_page.py`.

---

## Implementation Strategy

### MVP First (through P4)

1. Complete P0: Baseline GATE
2. Complete P1: Empty compose + constitution GATE
3. Complete P2: Definitions + settle (no GATE)
4. Complete P3: Close-open + option GATE
5. Complete P4: Dropdown select + wrappers GATE
6. **STOP and VALIDATE**: `pytest tests/ui/fleet_dashboard/` (T017)
7. Continue only if smoke is 100% green

### Incremental Delivery

1. P0 → recorded baseline
2. P1 → empty composed slicer, Principle VII updated
3. P2 → definitions + settle hook (no suite gate)
4. P3–P5 → close-open, option, select, clear-all; each phase one smoke GATE
5. P6–P7 → search, reset, cascade apply, Layer 3 contract; each phase one smoke GATE
6. P8 → checkbox kind (no suite gate)
7. P9 → delete leftovers, one leakage grep, Allure, smoke + e2e GATE

### Strangler Fig Reminders

- After every major move phase (P0, P1, P3–P7, P9) the smoke suite is a GATE,
  not a suggestion. P2 and P8 have no fleet pytest gate
- Never delete a fleet wrapper in the same task that first adds an unused stub
- Never load `data/filters.json` from `core/`
- Never put a `pytest` command on an implementation task — gates are the
  T002 / T008 / T013 / T017 / T019 / T022 / T026 / T033 tasks only

---

## Legacy ID Map (previous US-grouped list → this file)

Redundant per-task and per-story `pytest` runs (old T008 duplicates, T009–T014
inline gates, T019, T025, T029, T032 as extra copies of the same smoke) are
replaced by the single GATE at the end of each gated phase.

| Previous | Now |
|----------|-----|
| T001 baseline pytest | T002 (P0 GATE) |
| T002 `core/components/__init__.py` | T003 |
| T003 frozen callers | T001 |
| T004 stubs + `SlicerDefinition` | T004 stubs (P1) + T009 definitions (P2) |
| T005 `self._slicer` | T005 |
| T006 Principle VII | T006 |
| T007 README | T007 |
| T008 foundational pytest | T008 (P1 GATE only) |
| T009 `close_open` + pytest | T011 (pytest removed) |
| T010 `option_by_role` + pytest | T012 (pytest removed) |
| T011 `Slicer.select` + pytest | T014 (pytest removed) |
| T012 `select_*` wrappers + pytest | T015 (pytest removed) |
| T013 `clear_all` + pytest | T018 (pytest removed; includes `clear_filters_btn`) |
| T014 locator aliases + pytest | T016 dropdown aliases (P4); `clear_filters_btn` with T018 (P5) |
| T015 page-owned definitions | T009 |
| T016 settle hook | T010 |
| T017 `select_many` | T027 |
| T018 leakage grep | T031 (single grep; old T030 merged here) |
| T019 US2 pytest | **dropped** (P2/P8 have no gate; later phases have their own) |
| T020 cascade apply | T023 |
| T021 search / `clear_search` | T020 |
| T022 `reset_dashboard_filters` | T021 |
| T023 JSON contract verify | T024 |
| T024 three-artifact docs | T025 |
| T025 US3 pytest | T026 (P7 GATE only) |
| T026 delete leftover bodies | T028 |
| T027 fleet-only API verify | T029 |
| T028 `conftest` / Layer 0 verify | T030 |
| T029 US4 pytest | **dropped** (covered by T033) |
| T030 second leakage grep | **dropped** (covered by T031) |
| T031 Allure / CSV logs | T032 |
| T032 polish pytest | T033 (P9 GATE, combined with e2e) |
| T033 e2e | T033 (same GATE task) |

---

## Notes

- [P] tasks = different files, no dependencies
- [US1]–[US4] labels are traceability tags, not phases
- Do not edit test modules or `conftest.py`
- Commit after each GATE if the user requests commits
- Stop at any checkpoint to validate independently
- Avoid: putting Unit/SubUnit strings in `core/`, waiting on KPI names inside
  `Slicer`, renaming `apply_filters` kwargs, big-bang deletion of old methods
