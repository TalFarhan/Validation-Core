---

description: "Task list for bounding the day/night and clear-restore tests by date"
---

# Tasks: Bound the Global Invariant Tests by Date

**Input**: Design documents from `/specs/031-invariant-date-bounds/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/invariant-dates.md, quickstart.md

**Tests**: The work is the two existing tests in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Do not add a test file. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Two user stories. Both edit the same test file, so the clear-restore story follows the day/night story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Both stories**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Unchanged**: `pages/alerts_analysis/population_page.py`, `tests/ui/alerts_analysis_dashboard/population_snapshot.py`, `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the two tests that still read an unfiltered dates chart

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/031-invariant-date-bounds"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `test_day_plus_night_equals_untoggled_sum` and `test_clear_restores_population_snapshot` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and confirm neither calls `set_date_range` before its dates read, both start with `clear_filters()`, and neither has `pytest.mark.xfail`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the page methods and the files this slice must not edit

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep `set_date_range` and `clear_filters` in `pages/alerts_analysis/population_page.py` as the only calls these tests add, leave every path under `core/` and `pages/` unmodified, and leave `tests/ui/alerts_analysis_dashboard/population_snapshot.py` unmodified

**Checkpoint**: The tests will call methods that already exist. `core/` and `pages/` are out of scope.

---

## Phase 3: User Story 1 - Day plus night stays inside one date window (Priority: P1) 🎯 MVP

**Goal**: The day/night identity runs on `01/09/2026` through `15/10/2026`.

**Independent Test**: The untoggled dates total is read only after that window is applied, and `day + night == untoggled` still holds. The test has no `pytest.mark.xfail`.

### Implementation for User Story 1

- [X] T004 [US1] In `test_day_plus_night_equals_untoggled_sum` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, keep the opening `clear_filters()`, then call `set_date_range("01/09/2026", "15/10/2026")` before `chart_total` for `DATES_CHART`. Keep `set_day_night("day")`, `set_day_night("off")`, and `set_day_night("night")` in that order. Keep `assert day + night == untoggled`. Do not add `pytest.mark.xfail`. Do not call `filter_dates`. Any new comment must be English.

**Checkpoint**: The day/night test no longer reads the unfiltered dates table.

---

## Phase 4: User Story 2 - Clear restore stays inside the same window (Priority: P2)

**Goal**: The before snapshot and the after snapshot both use `01/09/2026` through `15/10/2026`.

**Independent Test**: The after snapshot is taken only after `clear_filters()` and a second `set_date_range("01/09/2026", "15/10/2026")`. It matches the before snapshot. The during snapshot still differs. The test has no `pytest.mark.xfail`.

### Implementation for User Story 2

- [X] T005 [US2] In `test_clear_restores_population_snapshot` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, keep the opening `clear_filters()`, then call `set_date_range("01/09/2026", "15/10/2026")` before the before `take_snapshot`. Keep `set_between_dates("01/09/2026", "01/10/2026")`, `set_day_night("day")`, `set_day_night("night")`, and `set_value_range(0, 349)`. Keep `assert not same_snapshot(before, during)`. After the later `clear_filters()`, call `set_date_range("01/09/2026", "15/10/2026")` again before the after `take_snapshot`. Keep `assert same_snapshot(before, take_snapshot(page))`. Do not add `pytest.mark.xfail`. Do not call `filter_dates` or `clear_all_filters`. Any new comment must be English.

**Checkpoint**: The after snapshot is not taken on the unfiltered page.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/031-invariant-date-bounds/quickstart.md` and confirm this slice did not edit `core/` or `pages/`

- [X] T006 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot -v` from `specs/031-invariant-date-bounds/quickstart.md`
- [X] T007 Confirm the only file changed for T004 and T005 is `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, and that no path under `core/` or `pages/` changed for this slice

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks the user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on User Story 1 because both edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Polish (Phase 5)**: Depends on User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. The day/night assertion stands on its own inside the bounded window.
- **User Story 2 (P2)**: Follows User Story 1 in the same test file. The clear-restore check uses `take_snapshot` and does not depend on the day/night totals.

### Within Each User Story

- Each story has one implementation task
- The live pytest run waits until both tests have the date window

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 then T005 then T006 then T007 stay in that order

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the tests together:
Task: "Confirm .specify/feature.json pins specs/031-invariant-date-bounds"
Task: "Read the day/night and clear-restore tests in tests/ui/alerts_analysis_dashboard/test_population_invariants.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the day/night test applies `01/09/2026` through `15/10/2026` before the untoggled dates total
3. Stop if that test still reads the unfiltered dates table

### Incremental Delivery

1. Setup and foundational lock `set_date_range`, `clear_filters`, and the `core/` and `pages/` boundary
2. User Story 1 bounds the day/night test
3. User Story 2 bounds both snapshots in the clear-restore test
4. Phase 5 runs both tests

### Parallel Team Strategy

T004 and T005 both edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. One person owns that file, day/night first and clear-restore second.

---

## Notes

- Do not edit `core/` or `pages/`
- Do not add `filter_dates` or `clear_all_filters`
- Do not edit `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Do not edit `test_hour_date_and_district_sums_match`, `test_population_cards_within_total`, `test_settlement_series_match_legend`, or `test_population_suite_opens_second_page`
- Do not mark either invariant test expected-fail
- The after snapshot in the clear test runs only after the second `set_date_range("01/09/2026", "15/10/2026")`
- Inline comments in the edited Python stay English
