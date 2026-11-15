---

description: "Task list for scrolling the dates table and filtering district rows"
---

# Tasks: Scroll the Dates Table and Filter District Rows

**Input**: Design documents from `/specs/030-scroll-visible-totals/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/scroll-visible.md, quickstart.md

**Tests**: Do not add a test file and do not edit `test_hour_date_and_district_sums_match`. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Two user stories. Both edit `pages/alerts_analysis/population_page.py`, so the district story follows the dates story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Both readers**: `pages/alerts_analysis/population_page.py`
- **Gate, unchanged**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the two current readers

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/030-scroll-visible-totals"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `chart_total` in `pages/alerts_analysis/population_page.py` and confirm `DATES_CHART` calls `_dates_table_total`, `DISTRICT_CHART` falls through to `_rows_for_total`, `HOUR_CHART` calls `_svg_mark_total`, and `test_hour_date_and_district_sums_match` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` still passes `01/09/2026` and `15/10/2026` with `hour_total == district_total == dates_total` and no `pytest.mark.xfail`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the hour reader, the settlement reader, and the no-core rule

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep `_svg_mark_total` for `HOUR_CHART`, keep `_rows_for_total` for `SETTLEMENT_CHART`, keep the dates right-click, `הצג כטבלה`, and `חזרה לדוח` in `pages/alerts_analysis/population_page.py`, and leave every path under `core/` unmodified, including `core/components/chart.py`

**Checkpoint**: The hour reader stays. `core/` is out of scope.

---

## Phase 3: User Story 1 - Dates reaches the rows below the first screen (Priority: P1) 🎯 MVP

**Goal**: The dates total scrolls the accessible table and stores each visible alert row once.

**Independent Test**: A row below the first viewport is included after it becomes visible. A hidden row is not added. The same visible row is not added twice.

### Implementation for User Story 1

- [X] T004 [US1] Change `_dates_table_total` in `pages/alerts_analysis/population_page.py` per `specs/030-scroll-visible-totals/contracts/scroll-visible.md`. Keep the right-click and the click on `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent. Find the visible grid whose `התרעות` column header is present. Scroll that table in overlapping steps. After each step, call `is_visible()` on each `role="row"`. Skip a row that fails that check. Skip a header row. Skip a row whose cell text is `סה"כ` or starts with `סה"כ`. Read the `role="gridcell"` at the `התרעות` header index. Remove thousands separators and spaces. Include `0`. Store the integer under `aria-rowindex`, or under the row-header text when that index is absent. Do not store the same key twice. Stop when two passes in a row add no key and do not move the scroll position. Also stop at `self.timeout`. If no visible integer was stored, raise `AssertionError` naming the dates chart. Click a visible button named `חזרה לדוח`, wait until the dates chart title is visible, and return the sum as `int`. Any new comment must be English.

**Checkpoint**: The dates total includes the virtualized rows and still ignores hidden rows.

---

## Phase 4: User Story 2 - District ignores hidden rows (Priority: P2)

**Goal**: The district total is the settled sum of visible rows inside that chart.

**Independent Test**: A hidden district row is not added. The total waits until two consecutive visible reads match.

### Implementation for User Story 2

- [X] T005 [US2] Change the `DISTRICT_CHART` branch of `chart_total` in `pages/alerts_analysis/population_page.py` per `specs/030-scroll-visible-totals/contracts/scroll-visible.md`. Do not sum `_rows_for_total` for this title. Use the tight visual container for `התרעות לפי מחוז`. Add integers only from `role="row"` elements in that container that pass `is_visible()`. Use the `התרעות` column when that header is present. Skip a header row and a `סה"כ` row. Include `0`. Poll until two consecutive visible reads return the same sum and the same included count. Pause briefly between reads. Stop at `self.timeout`. Do not scroll the district visual. If no visible integer was added, raise `AssertionError` naming the district chart. Return the settled sum as `int`. Leave `SETTLEMENT_CHART` on `_rows_for_total`. Any new comment must be English.

**Checkpoint**: The district total no longer includes hidden DOM rows.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/030-scroll-visible-totals/quickstart.md` and confirm this slice did not edit `core/`

- [X] T006 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v` from `specs/030-scroll-visible-totals/quickstart.md`
- [X] T007 Confirm the only file changed for T004 and T005 is `pages/alerts_analysis/population_page.py`, that `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged, and that no path under `core/` changed for this slice

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks the user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on User Story 1 because both edit `pages/alerts_analysis/population_page.py`
- **Polish (Phase 5)**: Depends on User Story 2

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on User Story 2. The hour reader stays so the equality can still compare the dates total with it.
- **User Story 2 (P2)**: Follows User Story 1 in the same page file. The district visual is not the dates table.

### Within Each User Story

- Each story has one implementation task
- The live pytest run waits until both readers are in place

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 then T005 then T006 then T007 stay in that order

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the page together:
Task: "Confirm .specify/feature.json pins specs/030-scroll-visible-totals"
Task: "Read chart_total in pages/alerts_analysis/population_page.py and the unchanged three-chart test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the dates total scrolls and stores each visible row once
3. Stop if a hidden dates row is still added

### Incremental Delivery

1. Setup and foundational lock the hour reader, the settlement reader, and the `core/` boundary
2. User Story 1 scrolls the dates table
3. User Story 2 filters the district total by `is_visible()`
4. Phase 5 runs `test_hour_date_and_district_sums_match`

### Parallel Team Strategy

T004 and T005 both edit `pages/alerts_analysis/population_page.py`. One person owns that file, dates first and district second.

---

## Notes

- Do not edit `core/components/chart.py`
- Do not change `_svg_mark_total` or the settlement branch of `chart_total`
- Do not add a hidden dates row while scrolling
- Do not scroll the district visual
- Do not edit `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- Do not mark the three-chart test expected-fail
- Inline comments in the edited Python stay English
