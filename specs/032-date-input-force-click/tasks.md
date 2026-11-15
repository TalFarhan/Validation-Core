---

description: "Task list for forcing the date field click past the overlay"
---

# Tasks: Force the Date Field Click Past the Overlay

**Input**: Design documents from `/specs/032-date-input-force-click/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/field-click.md, quickstart.md

**Tests**: Do not edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Do not add a test file. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: One user story. It edits `_commit_field` only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

## Path Conventions

- **Click**: `pages/alerts_analysis/population_page.py`
- **Gate, unchanged**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the current click

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/032-date-input-force-click"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `_commit_field` in `pages/alerts_analysis/population_page.py` and confirm it calls `field.click()` with no `force` argument, calls `_dismiss_overlay()` before and after that click, and that `test_clear_restores_population_snapshot` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` already calls `set_date_range("01/09/2026", "15/10/2026")` after each `clear_filters()`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the test file, the dismiss selector, and the no-core rule

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Leave `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and every path under `core/` unmodified, and leave `_dismiss_overlay` in `pages/alerts_analysis/population_page.py` matching `.cdk-overlay-backdrop-showing` only

**Checkpoint**: The invariant test stays. `core/` is out of scope.

---

## Phase 3: User Story 1 - Date inputs accept the range after a clear (Priority: P1) 🎯 MVP

**Goal**: A leftover `cdk-overlay-backdrop` does not hold the date click for 60 seconds.

**Independent Test**: `test_clear_restores_population_snapshot` passes without a click timeout, and the test file is unchanged.

### Implementation for User Story 1

- [X] T004 [US1] In `_commit_field` in `pages/alerts_analysis/population_page.py`, replace `field.click()` with `field.click(force=True)` per `specs/032-date-input-force-click/contracts/field-click.md`. Keep `_dismiss_overlay()` before the click. Keep `expect(field).to_be_visible(timeout=self.timeout)`. Keep `field.fill(value)` and `field.press("Enter")`. Keep `_dismiss_overlay()` after Enter. Do not add a date-only click path. Do not change `set_date_range` or `set_between_dates`. Any new comment must be English.

**Checkpoint**: Date inputs and value-range inputs both commit through the forced click.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/032-date-input-force-click/quickstart.md` and confirm this slice did not edit the test or `core/`

- [X] T005 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot -v` from `specs/032-date-input-force-click/quickstart.md`
- [X] T006 Confirm the only file changed for T004 is `pages/alerts_analysis/population_page.py`, and that `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and every path under `core/` are unchanged for this slice

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks the user story
- **User Story 1 (Phase 3)**: Depends on Foundational
- **Polish (Phase 4)**: Depends on User Story 1

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on another story. The clear-restore test already applies the date range after each clear.

### Within Each User Story

- The story has one implementation task
- The live pytest run waits until the forced click is in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 then T005 then T006 stay in that order

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the page together:
Task: "Confirm .specify/feature.json pins specs/032-date-input-force-click"
Task: "Read _commit_field in pages/alerts_analysis/population_page.py and the unchanged clear-restore test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so `_commit_field` uses `field.click(force=True)`
3. Complete T005 with `test_clear_restores_population_snapshot`

### Incremental Delivery

1. Setup and foundational lock the test file, `_dismiss_overlay`, and the `core/` boundary
2. User Story 1 forces the field click
3. Phase 4 runs the clear-restore test

### Parallel Team Strategy

T004 edits `pages/alerts_analysis/population_page.py`. One person owns that method.

---

## Notes

- Do not edit `core/`
- Do not edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- Do not widen `_dismiss_overlay` beyond `.cdk-overlay-backdrop-showing`
- Do not mark `test_clear_restores_population_snapshot` expected-fail
- Inline comments in the edited Python stay English
