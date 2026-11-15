---

description: "Task list for narrowing the dates and hour chart reads and waiting for the population page"
---

# Tasks: Population Chart Scope

**Input**: Design documents from `/specs/022-population-chart-scope/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/chart-container.md, quickstart.md

**Tests**: Existing population UI tests are the gate. Do not add a new test file. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

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

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/022-population-chart-scope"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 Read `chart_total`, `before_report_ready_check`, and `clear_filters` in `pages/alerts_analysis/population_page.py` and confirm `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` calls `page.chart_total` for hour, dates, district, and both settlement series

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the method names and the no-core rule before either story edits the page

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the signatures `chart_total(self, title: str, series_index: int = 0)`, `clear_filters(self)`, and `before_report_ready_check(self)` in `pages/alerts_analysis/population_page.py`, and leave every path under `core/` unmodified, including `core/components/chart.py` and `core/components/visual.py`

**Checkpoint**: The page methods keep their names. `core/` is out of scope.

---

## Phase 3: User Story 1 - Dates and hour totals stay inside one visual (Priority: P1) 🎯 MVP

**Goal**: The dates total and the hour total are parsed from the nearest visual container that holds that chart's title and a number, and that does not also hold another chart title from this page.

**Independent Test**: Day hours plus night hours equal the untoggled dates total. The dates reading does not include `אשדוד` or `נתניה`.

### Implementation for User Story 1

- [X] T004 [US1] Add `_visual_container(self, title: str)` in `pages/alerts_analysis/population_page.py` per `specs/022-population-chart-scope/contracts/chart-container.md`: start at the title text in the report frame; walk ancestors whose class contains `visualContainer` or `visual-container`, nearest first, including `visualContainerHost`; accept the first ancestor that has a numeric token and whose text does not contain another title from `DISTRICT_CHART`, `DATES_CHART`, `HOUR_CHART`, or `SETTLEMENT_CHART`; raise `AssertionError` when none qualifies. Do not fall back to `Chart.read`. Any new comment must be English.
- [X] T005 [US1] Update `chart_total` in `pages/alerts_analysis/population_page.py` per `specs/022-population-chart-scope/contracts/chart-container.md`: for `DATES_CHART` and `HOUR_CHART`, parse `_visual_container(title)` with `Chart._parse` and do not call `Chart.read`; for every other title, keep `Chart.read(title, scope=PAGE_TITLE)`; still skip non-numeric cells, including `None` and `bool`, without adding 0; still raise when the reading is empty or no numeric cell was added; still return a whole float as `int`.

**Checkpoint**: A dates or hour total no longer includes a city or district row from a neighboring visual.

---

## Phase 4: User Story 2 - The population page is ready before a test acts (Priority: P1)

**Goal**: Setup waits until the district chart is visible, with a 60 second budget on this page. Clear waits until the total population card is visible.

**Independent Test**: `test_clear_restores_population_snapshot` gets past setup, changes filters, clears them, and the arrival snapshot returns.

### Implementation for User Story 2

- [X] T006 [US2] In `AlertsPopulationPage.__init__` in `pages/alerts_analysis/population_page.py`, set `self.timeout = 60_000` after `super().__init__` and before `KPI` and `Chart` are constructed, per `specs/022-population-chart-scope/contracts/chart-container.md`
- [X] T007 [US2] Update `before_report_ready_check` in `pages/alerts_analysis/population_page.py` per `specs/022-population-chart-scope/contracts/chart-container.md`: return when the district chart is visible; click the page switcher only when that switcher is visible and the district chart is not
- [X] T008 [US2] Update `clear_filters` in `pages/alerts_analysis/population_page.py` per `specs/022-population-chart-scope/contracts/chart-container.md`: wait until the total population card is visible, then call `Slicer.clear_all`

**Checkpoint**: A slow report does not fail setup at 30 seconds, and clear does not click before the total card is on screen.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the population gate from `specs/022-population-chart-scope/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T009 Run the three previously red tests from `specs/022-population-chart-scope/quickstart.md`: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v`
- [ ] T010 Run the whole population file from `specs/022-population-chart-scope/quickstart.md`: `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v`, including `test_population_suite_opens_second_page`, `test_population_cards_within_total`, and `test_settlement_series_match_legend`
- [ ] T011 Confirm the files changed for T004 through T008 are only `pages/alerts_analysis/population_page.py`, and that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on Foundational. Run after User Story 1 because both edit `pages/alerts_analysis/population_page.py`
- **Polish (Phase 5)**: Depends on User Story 1 and User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. Day-plus-night and the three-chart comparison use the tight container.
- **User Story 2 (P1)**: No dependency on the container walk. The clear test needs the ready wait as well as the dates total, so the live file is green only after both stories.

### Within Each User Story

- T004 before T005: `chart_total` calls `_visual_container`
- T006, T007, and T008 edit the same file and run in that order
- Live pytest runs wait until both stories are in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 through T008 cannot run together: same function file
- T009 then T010: the three-test run is the first gate; the full file repeats it

---

## Parallel Example: Setup

```bash
# Read the pin and the two Python files together:
Task: "Confirm .specify/feature.json pins specs/022-population-chart-scope"
Task: "Read chart_total in pages/alerts_analysis/population_page.py and take_snapshot in tests/ui/alerts_analysis_dashboard/population_snapshot.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 and T005 so dates and hour totals use the tight container
3. Stop if a dates total still includes `אשדוד` or `נתניה`

### Incremental Delivery

1. Setup and foundational lock the signatures and the `core/` boundary
2. User Story 1 removes the neighboring-visual spill
3. User Story 2 extends the ready wait and the clear wait
4. Phase 5 runs the three red tests, then the whole population file

### Parallel Team Strategy

One implementer. User Story 2 starts after User Story 1 is saved in `pages/alerts_analysis/population_page.py`.

---

## Notes

- [P] is unused on T004 through T008 because they share one file
- Do not edit `core/components/chart.py` to change `Chart._container`
- Do not fall back to the page-wide canvas when no ancestor qualifies
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Inline comments in the edited Python stay English
