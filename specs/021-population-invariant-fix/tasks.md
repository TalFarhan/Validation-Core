---

description: "Task list for the population chart-total and Sum-click fix"
---

# Tasks: Population Invariant Fix

**Input**: Design documents from `/specs/021-population-invariant-fix/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/population-total.md, quickstart.md

**Tests**: Existing population UI tests are the gate. Do not add a new test file. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or shared navigation.

**Organization**: Tasks follow user-story order. Both stories edit `pages/alerts_analysis/population_page.py`, so they run one after the other.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Edit**: `pages/alerts_analysis/population_page.py` only
- **Caller, unchanged**: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- **Gate**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the single file this slice may change

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/021-population-invariant-fix"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 Read `chart_total` and `set_district_aggregation` in `pages/alerts_analysis/population_page.py` and confirm `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` calls `page.chart_total` for hour, dates, district, and both settlement series

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the method names and the no-core rule before either story edits the page

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the signatures `chart_total(self, title: str, series_index: int = 0)` and `set_district_aggregation(self, mode)` in `pages/alerts_analysis/population_page.py`, and leave every path under `core/` unmodified, including `core/components/chart.py` and `core/components/visual.py`

**Checkpoint**: The page methods keep their names. `core/` is out of scope.

---

## Phase 3: User Story 1 - Chart totals ignore stray text (Priority: P1) 🎯 MVP

**Goal**: `chart_total` adds only numeric cells. A settlement name with an empty cell does not abort the sum and is not stored as 0.

**Independent Test**: A selected series of `[4, None, 6]` returns `10`. A series of `[None]` raises `AssertionError`. A whole float such as `1.0` returns `1`.

### Implementation for User Story 1

- [X] T004 [US1] Update `chart_total` in `pages/alerts_analysis/population_page.py` per `specs/021-population-invariant-fix/contracts/population-total.md`: still raise when the chart state is empty or there are no categories; skip a cell that is missing, `None`, `bool`, or any non-number; add only `int` and `float`; raise when no cell was added; return a whole float as `int`. Do not add 0 for a skipped cell. Any new comment in this function must be English.

**Checkpoint**: Chart totals no longer raise on a non-numeric cell. An all-empty series still fails.

---

## Phase 4: User Story 2 - One Sum click on the district chart (Priority: P1)

**Goal**: Setting the district chart to Sum clicks one button. Playwright strict mode does not see two `סכום` matches on one click.

**Independent Test**: `set_district_aggregation("sum")` clicks a locator whose match count is 1. A second exact-name Sum button on the page does not make the click strict.

### Implementation for User Story 2

- [X] T005 [US2] Update `set_district_aggregation` in `pages/alerts_analysis/population_page.py` per `specs/021-population-invariant-fix/contracts/population-total.md`: resolve the label from `SUM_MODE` or `AVERAGE_MODE`; click `get_by_role("button", name=label, exact=True)` inside the district chart container only when that count is exactly 1; otherwise click `self._report_frame().get_by_role("button", name=label, exact=True).first`. Do not click a locator with count greater than 1. Do not edit `core/components/slicer.py`. Any new comment must be English.

**Checkpoint**: The district Sum action has one click target.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the population gate from `specs/021-population-invariant-fix/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T006 Run the three previously failing tests from `specs/021-population-invariant-fix/quickstart.md`: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v`
- [ ] T007 Run the whole population file from `specs/021-population-invariant-fix/quickstart.md`: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v`, including `test_population_suite_opens_second_page`, `test_population_cards_within_total`, and `test_settlement_series_match_legend`
- [ ] T008 Confirm the files changed for T004 and T005 are only `pages/alerts_analysis/population_page.py`, and that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational. Run after User Story 1 because both edit `pages/alerts_analysis/population_page.py`
- **Polish (Phase 5)**: Depends on User Story 1 and User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. The snapshot and the three chart identities use `chart_total`.
- **User Story 2 (P1)**: No dependency on the numeric filter. The clear, day/night, and three-chart tests call `set_district_aggregation` as well as `chart_total`, so the live file is green only after both stories.

### Within Each User Story

- One implementation task per story, in the same page file
- Live pytest runs wait until both stories are in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 and T005 cannot run together: same function file
- T006 then T007: the three-test run is the first gate; the full file repeats it

---

## Parallel Example: Setup

```bash
# Read the pin and the two Python files together:
Task: "Confirm .specify/feature.json pins specs/021-population-invariant-fix"
Task: "Read chart_total in pages/alerts_analysis/population_page.py and take_snapshot in tests/ui/alerts_analysis_dashboard/population_snapshot.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so `chart_total` skips non-numeric cells
3. Stop if a chart total still raises on a settlement name with no number

### Incremental Delivery

1. Setup and foundational lock the signatures and the `core/` boundary
2. User Story 1 removes the chart-text crash
3. User Story 2 removes the strict Sum click
4. Phase 5 runs the three failing tests, then the whole population file

### Parallel Team Strategy

One implementer. User Story 2 starts after User Story 1 is saved in `pages/alerts_analysis/population_page.py`.

---

## Notes

- [P] is unused on T004 and T005 because they share one file
- Do not edit `core/components/chart.py` to drop settlement labels
- Do not treat a skipped cell as 0
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Inline comments in the edited Python stay English
