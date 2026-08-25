---

description: "Task list for Dashboard Freshness Verification (Layer 0 + fleet smoke)"
---

# Tasks: Dashboard Freshness Verification

**Input**: Design documents from `/specs/003-dashboard-freshness/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/freshness-api.md, quickstart.md

**Tests**: Feature explicitly adds `test_dashboard_updated_within_24_hours` in `tests/ui/fleet_dashboard/test_dashboard_smoke.py`. Because this feature touches `core/portal` / `ReportShell`, `pytest tests/ui/fleet_dashboard/` is **MANDATORY** at completion. Do not edit `conftest.py` or existing smoke tests.

**Organization**: Additive method (not Strangler Fig). User Story 1 (generic `verify_freshness`) then User Story 2 (fleet smoke caller). Sequential: both stories touch the same public API.

**Constitution**: v1.2.0 (amended in this feature) — last-refresh chrome authorized on Layer 0; zero fleet domain leakage in `core/`; frozen `navigate` / `reload_and_measure_ready_ms`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: [US1], [US2] on user-story tasks only
- Include exact file paths in descriptions

## Path Conventions

- Layer 0: `core/portal/page.py`
- Domain: `pages/fleet_dashboard/main_dashboard_page.py` (inherit only)
- Smoke: `tests/ui/fleet_dashboard/test_dashboard_smoke.py`
- Constitution: `.specify/memory/constitution.md`
- Templates: `.specify/templates/`
- Fixture (read-only): `conftest.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing Layer 0 host and smoke file without moving behavior

- [x] T001 Confirm `ReportShell` in `core/portal/page.py` is inherited by `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` and that `_dashboard_iframe` / `_wait_for_dashboard_iframe` already exist (no behavior change)
- [x] T002 [P] Confirm the binding smoke file `tests/ui/fleet_dashboard/test_dashboard_smoke.py` and `conftest.py` `dashboard` fixture; do not edit `conftest.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Authorize last-refresh chrome on Layer 0 before adding the method

**⚠️ CRITICAL**: No `verify_freshness` implementation until this phase is complete

- [x] T003 Amend Principles I and VII in `.specify/memory/constitution.md` to v1.2.0 so Layer 0 MAY verify generic last-refresh chrome (phrase `הדשבורד עודכן לאחרונה ב:`) while KPI/chart/table/slicer extraction stays forbidden
- [x] T004 [P] Update Layer 0 / extract-shared wording in `.specify/templates/plan-template.md` Constitution Check to include last-refresh verification
- [x] T005 [P] Update `.specify/templates/spec-template.md` architectural constraints so generic last-refresh chrome MAY live in Layer 0 and dashboard-specific CSS is forbidden
- [x] T006 [P] Update `.specify/templates/tasks-template.md` Layer 0 sample task so freshness verification is in scope (not "timeout only")

**Checkpoint**: Constitution v1.2.0 and templates agree. User story implementation can begin.

---

## Phase 3: User Story 1 - Generic last-refresh check on any report (Priority: P1) 🎯 MVP

**Goal**: `ReportShell.verify_freshness(max_hours: int = 24)` locates the standard caption inside the Power BI iframe, parses the timestamp, and asserts age ≤ `max_hours`.

**Independent Test**: Call `verify_freshness()` on an open report. Missing / unparseable / stale captions fail with distinct messages. `core/` has no fleet CSS or business terms.

### Implementation for User Story 1

- [x] T007 [US1] Implement `verify_freshness(self, max_hours: int = 24) -> None` on `ReportShell` in `core/portal/page.py`: wait for the generic iframe, locate text containing `הדשבורד עודכן לאחרונה ב:` via regex or `get_by_text` inside a `FrameLocator` (no dashboard-specific CSS), parse with `datetime`, assert `(datetime.now() - parsed) <= timedelta(hours=max_hours)`, Allure step, distinct AssertionError messages
- [x] T008 [US1] Confirm `MainDashboardPage` in `pages/fleet_dashboard/main_dashboard_page.py` does not override `verify_freshness` and does not add last-refresh locators

**Checkpoint**: MVP — any `ReportShell` subclass can verify freshness. Do not add the smoke test until this method exists.

---

## Phase 4: User Story 2 - Fleet smoke asserts freshness within 24 hours (Priority: P1)

**Goal**: Fleet smoke has a thin sanity test that calls the shell method with the default 24-hour window.

**Independent Test**: `test_dashboard_updated_within_24_hours(dashboard)` in `tests/ui/fleet_dashboard/test_dashboard_smoke.py` calls `dashboard.verify_freshness()` only.

### Tests for User Story 2

- [x] T009 [US2] Add `@pytest.mark.sanity` test `test_dashboard_updated_within_24_hours(dashboard)` in `tests/ui/fleet_dashboard/test_dashboard_smoke.py` whose body is `dashboard.verify_freshness()`; do not add locators, parsing, or CSS; do not edit existing tests in that file

**Checkpoint**: Layer 3 caller exists. Existing smoke tests unchanged.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Leakage audit, binding gate, docs

- [x] T010 Search `core/` (including `core/portal/page.py`) for leakage tokens `vehicles`, `district`, `subunit`, `sub_unit`, `total_vehicles`, `רכבים`, `מחוז` and remove any hits; the last-refresh phrase is allowed
- [x] T011 Run `pytest tests/ui/fleet_dashboard/` — MUST pass 100% when the live report caption is within 24 hours
- [x] T012 [P] Mark done-when checkboxes in `specs/003-dashboard-freshness/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 (`verify_freshness` must exist)
- **Polish (Phase 5)**: Depends on User Stories 1 and 2

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependency on US2
- **User Story 2 (P1)**: Depends on US1 method existing on `ReportShell`

### Parallel Opportunities

- T002 can run with T001
- T004, T005, T006 can run in parallel after T003
- T012 can run with T010 once code is in place (T011 is the live gate)

---

## Parallel Example: Foundational templates

```bash
Task: "Update plan-template.md Constitution Check"
Task: "Update spec-template.md architectural constraints"
Task: "Update tasks-template.md Layer 0 sample task"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Constitution + templates
3. Complete Phase 3: `verify_freshness` on `ReportShell`
4. **STOP and VALIDATE**: Method exists, no fleet override, no leakage
5. Add User Story 2 smoke test
6. Run `pytest tests/ui/fleet_dashboard/`

### Incremental Delivery

1. Setup + Foundational → Layer 0 authorized
2. US1 → generic freshness API (MVP)
3. US2 → fleet smoke caller
4. Polish → leakage + 100% smoke gate

---

## Notes

- [P] tasks = different files, no dependencies
- Do not edit `conftest.py`
- Do not put freshness logic in `core/components/slicer.py`
- A stale live report is a correct fail of T009/T011, not a framework bug
- Commit after each logical group if the user asks; this command does not auto-commit
