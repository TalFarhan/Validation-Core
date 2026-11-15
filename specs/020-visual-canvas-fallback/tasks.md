---
description: "Task list for Visual Canvas Fallback"
---

# Tasks: Visual Canvas Fallback

**Input**: Design documents from `/specs/020-visual-canvas-fallback/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/scope-host.md, quickstart.md

**Tests**: The spec's independent tests and `contracts/scope-host.md` require
`tests/unit/test_scope_host.py`. Write those tests before the matching edit. Tier-1 cases lock
behavior that already exists; the tier-2 canvas case must fail until that return is implemented.
Fleet smoke (`pytest tests/ui/fleet_dashboard/`) is the Constitution III gate because
`core/components/visual.py` changes. Alerts page 1 is the other live gate. Do not run
`tests/ui/alerts_analysis_dashboard/test_population_invariants.py` as a gate for this feature.

**Organization**: US1 (P1) locks the group host. US2 (P1) adds the visible canvas when no group
matches. US3 (P1) runs the regression suites. Feature 019 stays paused.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in each task

## Path Conventions

- Production: `core/components/visual.py`, docstring only in `core/components/kpi.py`
- Unit tests: `tests/unit/test_scope_host.py` (new), existing `tests/unit/test_visual_state.py`, `tests/unit/test_db_parity_engine.py`
- Untouched callers: `core/components/chart.py`, `tests/helpers/db_parity_engine.py`
- Untouched feature 019: `pages/alerts_analysis/population_page.py`, `data/alerts/alerts_contract.yaml`, `specs/019-alerts-population-page/`
- Live gates: `tests/ui/fleet_dashboard/`, `tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py`, `tests/ui/alerts_analysis_dashboard/test_db_parity.py`

---

## Phase 1: Setup (Baseline)

**Purpose**: Record the current readers and the `scope_host` call sites before the host rule changes.

- [X] T001 Run `python -m pytest tests/unit/test_visual_state.py tests/unit/test_kpi_normalize.py tests/unit/test_chart_shape.py tests/unit/test_db_parity_engine.py -v` from the repo root and confirm they pass before any edit to `core/components/visual.py`
- [X] T002 [P] Confirm the call sites stay delegates: `scope_host` in `core/components/kpi.py` (`KPI._scope_host`), `core/components/chart.py` (`Chart._container`), and `tests/helpers/db_parity_engine.py` (`_map_container`). Do not edit those three call patterns in this feature (per contracts/scope-host.md Signature, plan.md Structure Decision)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the generic visible-canvas locator without changing which host `scope_host` returns.

**⚠️ CRITICAL**: No user story edit to `scope_host` starts until this helper exists.

- [X] T003 Add `_VISUAL_CONTAINERS` and `_visible_canvas(frame)` in `core/components/visual.py`. The selector string is `.visualContainerHost, .visual-container-host, [class*='visualContainerHost'], .visualContainer, .visual-container, .visual-container-component, [class*='visualContainer'], [class*='visual-container']`. `_visible_canvas` returns `frame.locator(_VISUAL_CONTAINERS).filter(visible=True)` and does not take a scope string. Do not call it from `scope_host` yet. English comments only. No Hebrew letters and no report title (per data-model.md Visible canvas, research.md Decision 3, contracts/scope-host.md) — depends on T001

**Checkpoint**: The canvas helper exists and is unused. Group lookup is still the current function.

---

## Phase 3: User Story 1 - A section scope still finds that section (Priority: P1) 🎯 MVP

**Goal**: Blank scope stays the report frame. A scope that matches a `role="group"` by accessible name, or else by contained text, stays that group. The canvas selector is not queried on those paths.

**Independent Test**: `python -m pytest tests/unit/test_scope_host.py -v` with no browser. Blank and whitespace scopes return the frame and do not call `get_by_role`. A named group is returned when its count is positive. A contained-text group is returned when the named count is 0 and the contained-text count is positive. `frame.locator` is not called in any of those cases.

### Tests for User Story 1

- [X] T004 [US1] Create `tests/unit/test_scope_host.py` with a fake frame and fake locators (no Playwright browser). Record `get_by_role(role, name=None)`, `filter(**kwargs)`, `count()`, `.first`, and `locator(selector)`. `get_by_role("group", name=pattern)` returns a locator whose `count()` is the named-group count. `get_by_role("group")` without a name returns a locator whose `filter(has_text=...)` result has the contained-text count. `locator` records the selector and its `filter` records kwargs. Assert, importing `scope_host` from `core/components/visual.py`: `scope_host(frame, None)` and `scope_host(frame, "   ")` return the same frame object and `role_calls` stays empty; with named count 1, the result is that named locator's `.first` and `locator` was not called; with named count 0 and contained-text count 2, the result is the contained-text locator's `.first` and `locator` was not called. Use the stand-in scope `"Section A"` only inside this test file. These tier-1 assertions lock current behavior and are expected to pass before T005 (FR-001, FR-002, FR-003, FR-009, contracts/scope-host.md Examples)

### Implementation for User Story 1

- [X] T005 [US1] Update `scope_host` in `core/components/visual.py` so a non-blank scope builds `pattern = re.compile(re.escape(str(scope).strip()))`, then returns `named.first` only when `frame.get_by_role("group", name=pattern).count() > 0`, else returns the contained-text group's `.first` only when `frame.get_by_role("group").filter(has_text=pattern).count() > 0`. When both counts are 0, still return that contained-text `.first` (today's timeout path). Do not call `_visible_canvas` in this task. Do not use `locator("*")`. Leave `classify_presence`, `count_data_marks`, and `displayed_title_text` unchanged. English comments only (per contracts/scope-host.md Resolution steps 1–3, research.md Decision 2) — depends on T003, T004
- [X] T006 [US1] Run `python -m pytest tests/unit/test_scope_host.py tests/unit/test_visual_state.py -v` and confirm both pass (FR-001, FR-008) — depends on T005

**Checkpoint**: Section scopes still bind to a group. A missing group still returns an empty group locator until User Story 2.

---

## Phase 4: User Story 2 - A page title scopes the visible page (Priority: P1)

**Goal**: When neither group query matches, `scope_host` returns the visible visual containers and does not wait on an empty group. `KPI._scope_host` documents that rule.

**Independent Test**: `python -m pytest tests/unit/test_scope_host.py -v`. With both group counts at 0, the result is `frame.locator(_VISUAL_CONTAINERS).filter(visible=True)`. The recorded filter kwargs are `visible=True` and do not include `has_state`. `core/components/visual.py` contains no Hebrew letters. A positive group count still skips `locator`.

### Tests for User Story 2

- [X] T007 [US2] Extend `tests/unit/test_scope_host.py` with a case where named count and contained-text count are both 0. Assert the return value is the object produced by `frame.locator(...).filter(visible=True)`, the selector contains `visualContainer` and `visual-container-component`, and the filter kwargs equal `{"visible": True}` with no `has_state` and no `has_text`. Add a source test that reads `core/components/visual.py` as UTF-8 and fails if any character is in the Hebrew block `\u0590-\u05FF`. The canvas assertion must fail on the T005 fallback before T008 (FR-004, FR-005, FR-006, SC-001, SC-005, contracts/scope-host.md Tier 2) — depends on T006

### Implementation for User Story 2

- [X] T008 [US2] In `scope_host` in `core/components/visual.py`, replace the both-counts-zero return with `return _visible_canvas(frame)`. Do not filter that locator by the scope text. Do not pass `has_state`. Do not call `text_content`, `get_attribute`, `click`, or `wait_for` while choosing the host. Keep the signature `scope_host(frame, scope: str | None) -> FrameLocator | Locator`. A positive tier-1 count must still return the group (per contracts/scope-host.md Resolution step 4, research.md Decision 2 and Decision 3) — depends on T007
- [X] T009 [US2] Update the docstring of `KPI._scope_host` in `core/components/kpi.py` so it states the delegate rule: blank scope is the iframe; a matching group is that group; otherwise the host is the visible visual containers; never `locator("*")`. Do not change the method body or any `KPI` signature (`card`, `read_text`, `value`, `number`, `scale`) (per FR-007, research.md Decision 4) — depends on T008
- [X] T010 [US2] Run `python -m pytest tests/unit/test_scope_host.py tests/unit/test_visual_state.py tests/unit/test_db_parity_engine.py -v` and confirm they pass (FR-004, FR-007, FR-008, quickstart.md §1) — depends on T008, T009

**Checkpoint**: An unresolved scope resolves to the visible canvas without an action-timeout probe. Group scopes still win.

---

## Phase 5: User Story 3 - Existing suites stay green (Priority: P1)

**Goal**: Unit parity, fleet smoke, and Alerts page 1 pass after the host change. Population-page tests are not required.

**Independent Test**: The three commands below pass. `test_population_invariants.py` is not part of the command.

### Implementation for User Story 3

- [X] T011 [P] [US3] Run `python -m pytest tests/unit/ -v` from the repo root and confirm the suite passes, including `tests/unit/test_db_parity_engine.py` and `tests/unit/test_scope_host.py` (SC-004, quickstart.md §3) — depends on T010
- [X] T012 [P] [US3] Run `python -m pytest tests/ui/fleet_dashboard/ -v` and confirm 100% pass (SC-002, Constitution III, quickstart.md §4) — depends on T010
- [ ] T013 [P] [US3] Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py tests/ui/alerts_analysis_dashboard/test_db_parity.py -v` and confirm they pass. Do not include `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` (SC-003, FR-010, quickstart.md §5) — depends on T010

**Checkpoint**: Shared lookup is safe for fleet and Alerts page 1. Feature 019 population tests can resume after this.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Confirm the slice did not absorb feature 019, then walk the quickstart once.

- [X] T014 Confirm `git diff -- pages/alerts_analysis/population_page.py data/alerts/alerts_contract.yaml specs/019-alerts-population-page core/components/chart.py tests/helpers/db_parity_engine.py` is empty, and `git diff -- core/components/kpi.py` touches only the `_scope_host` docstring (FR-010, research.md Decision 1 and Decision 4) — depends on T010
- [ ] T015 Walk `specs/020-visual-canvas-fallback/quickstart.md` sections 1 through 5 using the results of T010, T011, T012, and T013. Section 2 is the Hebrew source check inside `tests/unit/test_scope_host.py` (quickstart.md) — depends on T011, T012, T013

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T001 and T002 can run together.
- **Foundational (Phase 2)**: Depends on T001. Blocks edits to `scope_host`.
- **User Story 1 (Phase 3)**: Depends on Phase 2. No dependency on US2 or US3.
- **User Story 2 (Phase 4)**: Depends on US1, because it replaces the empty-group return and extends `tests/unit/test_scope_host.py`.
- **User Story 3 (Phase 5)**: Depends on US2. T011, T012, and T013 can run together.
- **Polish (Phase 6)**: Depends on the stories required by each task.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T003. Independently testable with the fake frame. Does not need a portal.
- **User Story 2 (P1)**: Starts after T006. Same files as US1 (`core/components/visual.py`, `tests/unit/test_scope_host.py`), so it cannot run beside US1.
- **User Story 3 (P1)**: Starts after T010. No production edits. Fleet and Alerts page 1 need auth and `.env`.

### Within Each User Story

- Tests are written before the production edit they lock.
- The tier-2 canvas assertion is expected to fail after T007 and pass after T008.
- Tier-1 assertions are expected to pass before and after T005.
- US3 commands do not change source.

### Parallel Opportunities

- T001 and T002 can run together.
- T011, T012, and T013 can run together after T010.
- US1 and US2 cannot run in parallel; they share `core/components/visual.py` and `tests/unit/test_scope_host.py`.

---

## Parallel Example: User Story 3

```bash
python -m pytest tests/unit/ -v
python -m pytest tests/ui/fleet_dashboard/ -v
python -m pytest tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py tests/ui/alerts_analysis_dashboard/test_db_parity.py -v
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (group host locked by `tests/unit/test_scope_host.py`).
3. **STOP and VALIDATE**: tier-1 tests pass and `frame.locator` is not used when a group matches.

User Story 1 does not remove the timeout. The smallest change that fixes a page-title scope is Phase 3 plus Phase 4.

### Incremental Delivery

1. Setup + foundational helper → canvas locator exists and is unused.
2. User Story 1 → group scopes stay groups.
3. User Story 2 → unresolved scopes use `filter(visible=True)` and the unit files in quickstart.md §1 pass.
4. User Story 3 → unit suite, fleet smoke, and Alerts page 1 pass.
5. Polish → feature 019 files are untouched.

### Parallel Team Strategy

One person owns `core/components/visual.py` through US2. After T010, fleet smoke and Alerts page 1 can run at the same time as the full unit suite.

---

## Notes

- [P] tasks use different commands or files and do not depend on each other.
- [US1], [US2], and [US3] map to the three stories in `specs/020-visual-canvas-fallback/spec.md`.
- Do not add a report name, page title, or metric title under `core/`.
- Do not switch the git branch. Feature 019 stays paused.
- Commit after each task or logical group only when asked.
