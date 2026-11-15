---

description: "Task list for the explicit date range before the three-chart total"
---

# Tasks: Population Date Range for the Three-Chart Total

**Input**: Design documents from `/specs/028-population-date-range/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/date-range.md, quickstart.md

**Tests**: Update the existing three-chart test. Do not add a test file. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: One user story. It adds `set_date_range` on the population page and calls it from the three-chart test before the totals are read.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

## Path Conventions

- **Date range**: `pages/alerts_analysis/population_page.py`
- **Gate**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Caller, unchanged**: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the date fields that already exist

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/028-population-date-range"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `set_between_dates` and `clear_filters` in `pages/alerts_analysis/population_page.py`, and confirm `תאריך התחלה` and `תאריך סיום` are the date inputs, `HOUR_CHART` still calls `_svg_mark_total`, `DATES_CHART` still calls `_dates_table_total`, `DISTRICT_CHART` still calls `_rows_for_total`, and `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the readers and the no-core rule before the date range is added

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep `set_between_dates` in `pages/alerts_analysis/population_page.py`, keep `_svg_mark_total` for `HOUR_CHART`, keep `_dates_table_total` for `DATES_CHART`, keep `_rows_for_total` for `DISTRICT_CHART` and `SETTLEMENT_CHART`, and leave every path under `core/` unmodified, including `core/components/slicer.py`

**Checkpoint**: The chart readers stay. `core/` is out of scope.

---

## Phase 3: User Story 1 - The three charts share one explicit date range (Priority: P1) 🎯 MVP

**Goal**: The three-chart test compares hour, dates, and district only after a wide date range has settled.

**Independent Test**: After `clear_filters`, the wide range is committed, the total card has repeated, district Sum is on, and `hour_total == district_total == dates_total`.

### Implementation for User Story 1

- [X] T004 [US1] Add `set_date_range(self, start_date: str, end_date: str) -> None` to `pages/alerts_analysis/population_page.py` per `specs/028-population-date-range/contracts/date-range.md`. Fill the input whose accessible name begins with `תאריך התחלה` with `start_date`, then the input whose accessible name begins with `תאריך סיום` with `end_date`, using the same click, fill, and Enter path as `set_between_dates`. Then wait until the total population card is visible, up to `self.timeout`. Poll `read_card("total")` until two consecutive reads are equal, pausing briefly between reads, and stop at `self.timeout` if they never match. Return `None`. Leave `set_between_dates` in place. Any new comment must be English.
- [X] T005 [US1] Update `test_hour_date_and_district_sums_match` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` per `specs/028-population-date-range/contracts/date-range.md`. Call `clear_filters()`, then `set_date_range("01/01/2020", <today formatted DD/MM/YYYY>)`, then `set_district_aggregation("sum")`. Build the end value from the local date so 17 October 2026 is `17/10/2026`. Read `HOUR_CHART`, `DATES_CHART`, and `DISTRICT_CHART` once each. Assert `hour_total == district_total == dates_total`. Do not mark the test expected-fail and do not skip it.

**Checkpoint**: The three totals are compared only after the wide range has settled.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/028-population-date-range/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T006 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v` from `specs/028-population-date-range/quickstart.md`
- [ ] T007 Confirm the only files changed for T004 and T005 are `pages/alerts_analysis/population_page.py` and `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser, and that no path under `core/` changed for this slice

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks the user story
- **User Story 1 (Phase 3)**: Depends on Foundational
- **Polish (Phase 4)**: Depends on User Story 1

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on another story. The hour, dates, and district readers stay so the equality still compares those three totals.

### Within User Story 1

- T004 adds the page method
- T005 calls that method from the test, so it follows T004
- The live pytest run waits until both edits are in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 then T005 then T006 then T007 stay in that order

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the page together:
Task: "Confirm .specify/feature.json pins specs/028-population-date-range"
Task: "Read set_between_dates in pages/alerts_analysis/population_page.py and the three-chart test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 and T005 so the wide range is set before the three totals are compared
3. Stop if the assertion is weaker than `hour_total == district_total == dates_total`

### Incremental Delivery

1. Setup and foundational lock the date fields, the three readers, and the `core/` boundary
2. User Story 1 adds `set_date_range` and calls it from the three-chart test
3. Phase 4 runs `test_hour_date_and_district_sums_match`

### Parallel Team Strategy

T004 edits `pages/alerts_analysis/population_page.py`. T005 edits the test after that method exists. One person owns that sequence.

---

## Notes

- Do not edit `core/components/slicer.py`
- Do not change `_svg_mark_total`, `_dates_table_total`, or the district branch of `chart_total`
- Do not mark the three-chart test expected-fail
- Do not apply the date range before `clear_filters`
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Inline comments in the edited Python stay English
