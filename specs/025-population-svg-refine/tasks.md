---

description: "Task list for circle marks, the התרעות value regex, and the visibility wait"
---

# Tasks: Population SVG Circle and Value Regex

**Input**: Design documents from `/specs/025-population-svg-refine/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/svg-value.md, quickstart.md

**Tests**: Do not add a test file. `test_hour_date_and_district_sums_match` stays as it is and is the gate. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: User Story 1 updates the mark locator and the value regex. User Story 2 adds the visibility wait. Both edit `pages/alerts_analysis/population_page.py`, so they run in that order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **SVG total**: `pages/alerts_analysis/population_page.py`
- **Gate, unchanged**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Caller, unchanged**: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the reader this slice changes

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/025-population-svg-refine"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `_integer_from_mark_label` and `_svg_mark_total` in `pages/alerts_analysis/population_page.py`, and confirm `test_hour_date_and_district_sums_match` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged and `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` calls `page.chart_total`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the method name and the no-core rule before either story edits the page

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the signature `chart_total(self, title: str, series_index: int = 0)` in `pages/alerts_analysis/population_page.py`, keep `_visual_container` as the dates and hour container, and leave every path under `core/` unmodified, including `core/components/chart.py`

**Checkpoint**: The page method keeps its name. `core/` is out of scope.

---

## Phase 3: User Story 1 - Dates total reads circle marks (Priority: P1) 🎯 MVP

**Goal**: The dates total includes circle marks. The integer after `התרעות` is the value, so a date token such as `2026` is not the value.

**Independent Test**: `תאריך 2026-10-15. התרעות 0.` contributes `0`. `התרעות 5,293` contributes `5293`. A label that is only `5293` still contributes `5293`.

### Implementation for User Story 1

- [X] T004 [US1] Update `_integer_from_mark_label` and `_svg_mark_total` in `pages/alerts_analysis/population_page.py` per `specs/025-population-svg-refine/contracts/svg-value.md`. Query `svg rect, svg path, svg circle` inside `_visual_container(title)` for `DATES_CHART` and `HOUR_CHART`. Read `aria-label` with `get_attribute`. Do not call `inner_text`. Do not add `[role="option"]` labels on top of those shapes. Skip a label that contains `ממוצע`. Skip a label that contains a fractional number (`5895.54` or `5,895.54`). When the label contains `התרעות`, add the integer from `התרעות\s*([0-9,]+)` after removing thousands separators, so `תאריך 2026-10-15. התרעות 0.` is `0` and `התרעות 5,293` is `5293`. When the label does not contain `התרעות` and the whole label is one integer, add that integer, so `5293` is `5293`. Skip every other label. If no integer was added, raise `AssertionError` naming the chart. Return the sum as `int`. `series_index` does not select a series for these titles. District and settlement titles stay on their current readers. Any new comment must be English.

**Checkpoint**: A date in the label is not the alert count. A bare hour bar stays in the sum.

---

## Phase 4: User Story 2 - Hour total waits for every bar (Priority: P1)

**Goal**: The hour total waits until an SVG mark is visible, then reads the labels.

**Independent Test**: The reader calls `expect` on the first `svg rect, svg path, svg circle` before it collects `aria-label` values. The hour total is the sum of those bars, not the single average `5895.54`.

### Implementation for User Story 2

- [X] T005 [US2] In `_svg_mark_total` in `pages/alerts_analysis/population_page.py`, wait until the first `svg rect, svg path, svg circle` inside the visual container is visible, using `expect` and `self.timeout`, before `_aria_labels` reads them. Do not edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`.

**Checkpoint**: Label collection starts after a mark is visible.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/025-population-svg-refine/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T006 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v` from `specs/025-population-svg-refine/quickstart.md`
- [ ] T007 Confirm the only file changed for T004 and T005 is `pages/alerts_analysis/population_page.py`, that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser, and that `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on User Story 1, because both edit `pages/alerts_analysis/population_page.py` and the wait wraps the reader from User Story 1
- **Polish (Phase 5)**: Depends on User Story 1 and User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. The regex and the circle locator can be checked with label examples.
- **User Story 2 (P1)**: Uses the reader from User Story 1. The live gate compares hour, dates, and district, so the file is green only after both stories.

### Within Each User Story

- One implementation task per story
- The live pytest run waits until both stories are in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 and T005 edit the same file and run in that order
- T006 then T007: the pytest gate comes before the edit-list check

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the page together:
Task: "Confirm .specify/feature.json pins specs/025-population-svg-refine"
Task: "Read _integer_from_mark_label in pages/alerts_analysis/population_page.py and the unchanged three-chart test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so `תאריך 2026-10-15. התרעות 0.` contributes `0` and `5293` still contributes `5293`
3. Stop if a date token is the value added from a label that also contains `התרעות`

### Incremental Delivery

1. Setup and foundational lock the signature and the `core/` boundary
2. User Story 1 reads circle marks and the integer after `התרעות`
3. User Story 2 waits for the first mark before collecting labels
4. Phase 5 runs `test_hour_date_and_district_sums_match`

### Parallel Team Strategy

T004 and T005 share `pages/alerts_analysis/population_page.py`. One person edits that file from User Story 1 through User Story 2.

---

## Notes

- Do not edit `core/components/chart.py`
- Do not add `0` for a skipped average or float
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Do not require `התרעות` on a label that is only an integer. The live hour bars are bare integers
- The eight hour labels printed on 2026-10-15 were `kept[:8]`. They were the first slice of the list
- Inline comments in the edited Python stay English
