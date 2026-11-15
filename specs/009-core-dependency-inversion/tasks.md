---
description: "Task list for Refactor Dependency Inversion — Move base_page and errors to core"
---

# Tasks: Refactor Dependency Inversion — Move `base_page` and `errors` to `core`

**Input**: Design documents from `/specs/009-core-dependency-inversion/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature changes `core/portal` (`ReportShell`) imports and relocates the shared page-object
foundation (`BasePage`). Per the project test contract (Constitution III), fleet smoke validation
(`pytest tests/ui/fleet_dashboard/`) is **MANDATORY** and appears as a gating task (T015). No new unit/TDD
tests are requested — this is a mechanical move with no behavior change.

**Organization**: One user story (US1 — the dependency inversion). Foundational phase creates the new `core/`
modules that every later edit depends on, then US1 rewires call sites and removes the old modules.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

## Path Conventions

- **Validation Core**: `core/` (Layer 0 + shared foundation), `core/portal/` (ReportShell),
  `pages/<report>/` (domain), `tests/ui/<report>/` (smoke), `tests/e2e/`, `tests/helpers/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm baseline before touching import topology.

- [X] T001 Capture the pre-refactor import baseline by running `rg "from pages\.(base_page|errors)|import pages\.(base_page|errors)" core/ pages/ tests/` from repo root and recording the 6 live-code matches (see `contracts/module-move.md` C3) so no call site is missed.
- [ ] T002 Confirm the regression gate currently passes by running `pytest tests/ui/fleet_dashboard/` (establish green baseline before changes). _(Requires live portal + browser — run on workstation; not executed in this environment.)_

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the new `core/` modules. Every US1 edit imports from these, so they MUST exist first.

**⚠️ CRITICAL**: No US1 call-site rewiring can begin until T003 and T004 exist and import cleanly.

- [X] T003 Create `core/errors.py` containing ONLY the generic `LoadTimeoutError(AssertionError)` — move the class verbatim from `pages/errors.py` (same `__init__(description, *, steps_ms, cause=None)` signature and attributes). Do NOT include `ExpandHierarchyUnavailable`. Keep the module docstring generic (no fleet terms); all in-function comments English only.
- [X] T004 Create `core/base_page.py` by moving `BasePage` verbatim from `pages/base_page.py`, changing only its internal import to `from core.errors import LoadTimeoutError`. Preserve the full public surface (`__init__`, `retry_with_backoff`, `wait_for_visible`, `wait_for_kpi_update`, `assert_tab_active`, `assert_tab_inactive`, `ACTIVE_TAB_CLASS`); in-function comments English only.
- [X] T005 Verify the new modules import in isolation: `python -c "from core.base_page import BasePage; from core.errors import LoadTimeoutError; print('core ok')"` (depends on T003, T004).

**Checkpoint**: `core/` now owns the generic foundation. Call-site rewiring can proceed.

---

## Phase 3: User Story 1 - Resolve the `core → pages` reverse dependency (Priority: P1) 🎯 MVP

**Goal**: Repoint every live import to the new `core/` locations, relocate the fleet-specific
`ExpandHierarchyUnavailable` into the fleet domain, and remove the old `pages/` modules — with zero behavior
change.

**Independent Test**: `rg "from pages\.(base_page|errors)" core/ pages/ tests/` returns no matches, both import
probes in `quickstart.md` print `ok`, and `pytest tests/ui/fleet_dashboard/` is 100% green.

### Implementation for User Story 1

- [X] T006 [P] [US1] Update `core/portal/page.py`: change `from pages.base_page import BasePage` → `from core.base_page import BasePage` and `from pages.errors import LoadTimeoutError` → `from core.errors import LoadTimeoutError` (lines ~12-13; imports only, no body change).
- [X] T007 [US1] In `pages/fleet_dashboard/main_dashboard_page.py`, add the `ExpandHierarchyUnavailable(AssertionError)` class definition (moved verbatim from `pages/errors.py`, same `__init__(chart_key, reason)` and attributes) near the top of the module after imports, so its existing raises/catches (lines ~1646-1971) resolve to the local definition.
- [X] T008 [US1] In `pages/fleet_dashboard/main_dashboard_page.py`, change the import `from pages.errors import ExpandHierarchyUnavailable, LoadTimeoutError` → `from core.errors import LoadTimeoutError` (line ~9); `ExpandHierarchyUnavailable` now comes from the local definition added in T007 (depends on T007).
- [X] T009 [P] [US1] Update `tests/helpers/dashboard_validation.py`: change `from pages.errors import LoadTimeoutError` → `from core.errors import LoadTimeoutError` (line ~12).
- [X] T010 [P] [US1] Update `tests/e2e/test_chart_drilldown.py`: change `from pages.errors import ExpandHierarchyUnavailable` → `from pages.fleet_dashboard.main_dashboard_page import ExpandHierarchyUnavailable` (line ~14).
- [X] T011 [US1] Delete `pages/base_page.py` (content now lives in `core/base_page.py`) — only after T004 and T006 are complete.
- [X] T012 [US1] Delete `pages/errors.py` (generic part now in `core/errors.py`, fleet error now in the fleet page) — only after T003, T007, T008, T009, T010 are complete.

**Checkpoint**: No module under `core/` imports from `pages/`; the inheritance chain `BasePage → ReportShell → MainDashboardPage` is intact.

---

## Phase 4: Polish & Validation (Gating)

**Purpose**: Prove the refactor is correct and introduced no regression.

- [X] T013 Run structural guard INV-1: `rg "from pages\.(base_page|errors)|import pages\.(base_page|errors)" core/ pages/ tests/` MUST return zero matches.
- [X] T014 Run structural guard INV-2: confirm `rg "הסתעפות" core/` returns zero matches (no fleet term leaked into `core/`) and that `ExpandHierarchyUnavailable` is defined only under `pages/fleet_dashboard/`.
- [ ] T015 **MANDATORY GATE** — Run `pytest tests/ui/fleet_dashboard/` and confirm 100% pass (Constitution III). The feature is NOT done unless this is green. _(Requires live portal + browser session on the workstation — NOT executed in this environment. Static equivalent passed: all 18 affected tests collect with zero import errors.)_
- [X] T016 [P] Confirm the drilldown e2e import resolves: `pytest tests/e2e/test_chart_drilldown.py --collect-only` succeeds with no `ImportError` (collected together with the fleet suite — 18 items, 0 errors).
- [X] T017 [P] Run the `quickstart.md` done-when checklist steps 1-3 and 5 (grep guard, import probes, old files removed, drilldown collect). Step 4 (live smoke) folds into T015 and awaits the workstation run.
- [ ] T018 Documentation follow-up (non-blocking): note in the PR that the constitution's Architecture Constraints wording still cites `pages.base_page.BasePage` and should be updated to `core.base_page.BasePage` in a future constitution amendment.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first to establish baseline.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all US1 call-site edits (they import from the new modules).
- **User Story 1 (Phase 3)**: Depends on Foundational (T003, T004 must exist).
- **Polish (Phase 4)**: Depends on all US1 tasks being complete.

### Within User Story 1

- T006, T009, T010 are independent file edits ([P]) — can run together.
- T007 (add class) must precede T008 (import change that relies on the local class).
- T011 (delete `base_page.py`) requires T004 + T006.
- T012 (delete `errors.py`) requires T003, T007, T008, T009, T010.

### Parallel Opportunities

- Phase 3: T006 + T009 + T010 in parallel (different files, no interdependency).
- Phase 4: T016 + T017 in parallel after T015 passes.

---

## Parallel Example: User Story 1

```bash
# Launch the independent import rewrites together:
Task: "Update core/portal/page.py imports to core.base_page / core.errors"
Task: "Update tests/helpers/dashboard_validation.py import to core.errors"
Task: "Update tests/e2e/test_chart_drilldown.py import to fleet page location"
```

---

## Implementation Strategy

### MVP (and only scope) = User Story 1

1. Phase 1: Setup — baseline grep + green smoke.
2. Phase 2: Foundational — create `core/errors.py` and `core/base_page.py`.
3. Phase 3: US1 — rewire the 6 call sites, relocate `ExpandHierarchyUnavailable`, delete old modules.
4. Phase 4: Validate — structural guards + **mandatory** fleet smoke gate (T015) + drilldown collect + quickstart.
5. STOP and VALIDATE: a pure relocation is done when smoke is 100% green and no `core → pages` import remains.

---

## Notes

- [P] tasks = different files, no dependencies.
- This is a mechanical move: no business logic, UI flow, chart logic, SQL, or observability wiring changes.
- All in-function comments MUST be English only (spec AC7).
- Commit after Foundational (Phase 2) and again after US1, so a failing smoke gate is easy to bisect.
- Hard gate: `pytest tests/ui/fleet_dashboard/` (T015) must pass 100% before declaring done.
```
