---

description: "Task list for dates and hour totals read from SVG aria-labels"
---

# Tasks: Population Chart SVG Aria Labels

**Input**: Design documents from `/specs/024-population-svg-aria/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/svg-aria-total.md, quickstart.md

**Tests**: Do not add a test file. `test_hour_date_and_district_sums_match` stays as it is and is the gate. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: User Story 1 adds the SVG reader and uses it for the dates chart. User Story 2 points the hour chart at that reader. Both edit `pages/alerts_analysis/population_page.py`, so they run in that order.

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

**Purpose**: Confirm the pin and the page methods this slice replaces

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/024-population-svg-aria"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `chart_total`, `_hour_bar_total`, and `_visual_container` in `pages/alerts_analysis/population_page.py`, and confirm `test_hour_date_and_district_sums_match` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged and `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` calls `page.chart_total`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the method name and the no-core rule before either story edits the page

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the signature `chart_total(self, title: str, series_index: int = 0)` in `pages/alerts_analysis/population_page.py`, keep `_visual_container` as the dates and hour container, and leave every path under `core/` unmodified, including `core/components/chart.py`

**Checkpoint**: The page method keeps its name. `core/` is out of scope.

---

## Phase 3: User Story 1 - Dates total reads the bar labels (Priority: P1) 🎯 MVP

**Goal**: The dates total sums integer `aria-label` values on the SVG marks. It does not sum text nodes that are all zero.

**Independent Test**: `chart_total` for `DATES_CHART` returns the sum of those integers. A missed label raises instead of returning `0`.

### Implementation for User Story 1

- [X] T004 [US1] Add the SVG reader in `pages/alerts_analysis/population_page.py` per `specs/024-population-svg-aria/contracts/svg-aria-total.md` and call it from `chart_total` when `title` is `DATES_CHART`. Inside `_visual_container(title)`, read `aria-label` with `get_attribute` from `svg rect` and `svg path`. Do not call `inner_text`. Do not read `role="option"`. If those labels include no integer, read `[role="img"]` inside the container and exclude the container node itself. Do not add the image labels to the shape labels. Skip a label that contains `ממוצע`. Skip a label that contains a fractional number (`5895.54` or `5,895.54`). On a kept label, take the last integer token and strip spaces and thousands separators so `5,293` is `5293` and `00:00 4181` is `4181`. Include `0`. If no integer was added, raise `AssertionError` naming the chart. Return the sum as `int`. `series_index` does not select a series for this title. Any new comment must be English.

**Checkpoint**: The dates total is the sum of its SVG bar labels.

---

## Phase 4: User Story 2 - Hour total reads the bar labels (Priority: P1)

**Goal**: The hour total uses the same SVG reader. The average line is not part of the sum.

**Independent Test**: The hour total is not `141493` and not `5895.54`. A label containing `ממוצע` is absent from the sum.

### Implementation for User Story 2

- [X] T005 [US2] In `pages/alerts_analysis/population_page.py`, call the User Story 1 SVG reader from `chart_total` when `title` is `HOUR_CHART`. Remove `_hour_bar_total` and `_hour_option_value`. Drop the `parse_mark_label` import when nothing else in the file uses it. District and settlement titles stay on their current readers. Do not edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`.

**Checkpoint**: The hour total and the dates total both come from SVG mark labels.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/024-population-svg-aria/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T006 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v` from `specs/024-population-svg-aria/quickstart.md`
- [ ] T007 Confirm the only file changed for T004 and T005 is `pages/alerts_analysis/population_page.py`, that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser, and that `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on User Story 1, because both edit `pages/alerts_analysis/population_page.py` and the hour chart calls the dates chart's reader
- **Polish (Phase 5)**: Depends on User Story 1 and User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. The dates total can be read on its own.
- **User Story 2 (P1)**: Uses the reader from User Story 1. The live gate compares the hour total with the dates total, so the file is green only after both stories.

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
Task: "Confirm .specify/feature.json pins specs/024-population-svg-aria"
Task: "Read chart_total in pages/alerts_analysis/population_page.py and the unchanged three-chart test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the dates total comes from SVG `aria-label` values
3. Stop if that total is still the text-node `0` from a missed label

### Incremental Delivery

1. Setup and foundational lock the signature and the `core/` boundary
2. User Story 1 reads dates-chart bar labels
3. User Story 2 points the hour chart at that reader and removes the option-text total
4. Phase 5 runs `test_hour_date_and_district_sums_match`

### Parallel Team Strategy

T004 and T005 share `pages/alerts_analysis/population_page.py`. One person edits that file from User Story 1 through User Story 2.

---

## Notes

- Do not edit `core/components/chart.py` to read these `aria-label` values
- Do not add `0` for a skipped average or float
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Do not sum `role="option"` text. That path returned `141493`
- Inline comments in the edited Python stay English
