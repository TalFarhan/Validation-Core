---

description: "Task list for the hour-bar sum and the cleared baseline snapshot"
---

# Tasks: Population Hour Sum and Clear Baseline

**Input**: Design documents from `/specs/023-population-hour-clear/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/hour-and-clear.md, quickstart.md

**Tests**: The clear test's steps change in User Story 2. Do not add a new test file. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: User Story 1 edits the page object. User Story 2 edits the clear test. They can be written together. The live pytest run waits for both.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Hour total**: `pages/alerts_analysis/population_page.py`
- **Clear test**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Caller, unchanged**: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the two files this slice may change

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/023-population-hour-clear"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 Read `chart_total` in `pages/alerts_analysis/population_page.py` and `test_clear_restores_population_snapshot` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, and confirm `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` calls `page.chart_total`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the method names and the no-core rule before either story edits its file

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the signatures `chart_total(self, title: str, series_index: int = 0)` and `clear_filters(self)` in `pages/alerts_analysis/population_page.py`, and leave every path under `core/` unmodified, including `core/components/chart.py`

**Checkpoint**: The page methods keep their names. `core/` is out of scope.

---

## Phase 3: User Story 1 - Hour total sums the bars (Priority: P1) 🎯 MVP

**Goal**: The hour total adds integer bars. It does not add a series named with `ממוצע` and it does not add a fractional float such as `5895.54`.

**Independent Test**: The hour total is not `5895.54`. Integer bars such as `5293` are included. A whole float such as `1.0` counts as `1`.

### Implementation for User Story 1

- [X] T004 [US1] Update `chart_total` in `pages/alerts_analysis/population_page.py` per `specs/023-population-hour-clear/contracts/hour-and-clear.md`: for `HOUR_CHART`, keep the series names from `Chart._parse`; skip a series whose name contains `ממוצע`; on the remaining series add only an `int`, or a `float` whose `is_integer()` is true, and never a `bool`; raise when no cell was added; return a whole float as `int`. Do not add 0 for a skipped average. Leave dates, district, and settlement totals on their current rules. Any new comment must be English.

**Checkpoint**: The hour total is the sum of the integer bars.

---

## Phase 4: User Story 2 - Clear restores a cleared baseline (Priority: P1)

**Goal**: The clear test stores its baseline after the first clear, not at arrival.

**Independent Test**: After the second clear, the snapshot equals the snapshot taken after the first clear. The filtered snapshot differs from that baseline.

### Implementation for User Story 2

- [X] T005 [P] [US2] Update `test_clear_restores_population_snapshot` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` per `specs/023-population-hour-clear/contracts/hour-and-clear.md`: call `page.clear_filters()` first; then `before = take_snapshot(page)`; then `set_between_dates("01/09/2026", "01/10/2026")`, `set_day_night("day")`, `set_day_night("night")`, and `set_value_range(0, 349)`; assert the new snapshot is not `before`; call `page.clear_filters()` again; assert `take_snapshot(page)` equals `before`. Do not add DOM reads in the test body.

**Checkpoint**: The restored snapshot matches the post-clear baseline.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the population gate from `specs/023-population-hour-clear/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T006 Run the three population tests from `specs/023-population-hour-clear/quickstart.md`: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v`
- [ ] T007 Run the whole population file from `specs/023-population-hour-clear/quickstart.md`: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v`, including `test_population_suite_opens_second_page`, `test_population_cards_within_total`, and `test_settlement_series_match_legend`
- [ ] T008 Confirm the files changed for T004 and T005 are only `pages/alerts_analysis/population_page.py` and `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, and that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational. It does not depend on User Story 1
- **Polish (Phase 5)**: Depends on User Story 1 and User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. The three-chart test calls `chart_total` for the hour chart.
- **User Story 2 (P1)**: No dependency on the average skip. The clear test calls `chart_total` through `take_snapshot`, so the live file is green only after both stories.

### Within Each User Story

- One implementation task per story
- Live pytest runs wait until both stories are in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 and T005 edit different files and can run together after T003
- T006 then T007: the three-test run is the first gate; the full file repeats it

---

## Parallel Example: User Story 1 and User Story 2

```bash
# After T003, edit the page and the test together:
Task: "Update chart_total in pages/alerts_analysis/population_page.py to skip ממוצע and fractional floats"
Task: "Update test_clear_restores_population_snapshot in tests/ui/alerts_analysis_dashboard/test_population_invariants.py to clear before the baseline"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the hour total is the integer bar sum
3. Stop if the hour total is still `5895.54`

### Incremental Delivery

1. Setup and foundational lock the signatures and the `core/` boundary
2. User Story 1 removes the average line from the hour total
3. User Story 2 moves the clear baseline to after the first clear
4. Phase 5 runs the three tests, then the whole population file

### Parallel Team Strategy

After T003, one person can edit `pages/alerts_analysis/population_page.py` while another edits `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`.

---

## Notes

- [P] on T005 means it does not share a file with T004
- Do not edit `core/components/chart.py` to drop the average series
- Do not add 0 for a skipped average
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Inline comments in the edited Python stay English
