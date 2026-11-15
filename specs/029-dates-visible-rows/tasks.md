---

description: "Task list for summing only the visible dates-table rows"
---

# Tasks: Visible Dates Table Rows

**Input**: Design documents from `/specs/029-dates-visible-rows/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/visible-rows.md, quickstart.md

**Tests**: Do not add a test file. `test_hour_date_and_district_sums_match` stays a strict equality. Remove `pytest.mark.xfail` if it is present. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: One user story. It changes the dates branch in `pages/alerts_analysis/population_page.py` and leaves the hour and district readers in place.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

## Path Conventions

- **Visible dates rows**: `pages/alerts_analysis/population_page.py`
- **Gate**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the current dates sum

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/029-dates-visible-rows"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `_dates_table_total` in `pages/alerts_analysis/population_page.py` and confirm it calls `_sum_scrolled_alert_column`, `HOUR_CHART` calls `_svg_mark_total`, `DISTRICT_CHART` calls `_rows_for_total`, and `test_hour_date_and_district_sums_match` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` passes `01/09/2026` and `15/10/2026` with `hour_total == district_total == dates_total`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the menu, the back button, and the no-core rule before the sum changes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the right-click and `הצג כטבלה` open path, keep `חזרה לדוח`, keep `_svg_mark_total` for `HOUR_CHART`, keep `_rows_for_total` for `DISTRICT_CHART` and `SETTLEMENT_CHART` in `pages/alerts_analysis/population_page.py`, and leave every path under `core/` unmodified, including `core/components/chart.py`

**Checkpoint**: The hour and district readers stay. `core/` is out of scope.

---

## Phase 3: User Story 1 - The dates total is the visible table (Priority: P1) 🎯 MVP

**Goal**: The dates total is the settled sum of visible `התרעות` grid cells.

**Independent Test**: A hidden row is not added. After the visible column repeats, `hour_total == district_total == dates_total`. On the filtered dashboard that shared value is 13.

### Implementation for User Story 1

- [X] T004 [US1] Change `_dates_table_total` in `pages/alerts_analysis/population_page.py` per `specs/029-dates-visible-rows/contracts/visible-rows.md`. Keep the right-click and the click on `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent. Wait until a visible grid or table has a `התרעות` column header and at least one visible integer grid cell in that column, up to `self.timeout`. Then poll the visible rows until two consecutive reads produce the same sum and the same included count. Pause briefly between reads, and stop at `self.timeout` if they never match. Call `is_visible()` on each `role="row"`. Omit a row that fails that check even when its text is still in the DOM. Skip a row that contains a column header. Skip a row whose cell text is `סה"כ` or starts with `סה"כ`. Read the `role="gridcell"` at the `התרעות` header index. Remove thousands separators and spaces. Add the integer, including `0`. Do not scroll the table and do not call `_sum_scrolled_alert_column`. If no visible integer was added, raise `AssertionError` naming the dates chart. Click a visible button named `חזרה לדוח`, wait until the dates chart title is visible, and return the sum as `int`. Any new comment must be English.
- [X] T005 [P] [US1] In `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, remove `@pytest.mark.xfail` from `test_hour_date_and_district_sums_match` if that decorator is present. Leave the assertion `hour_total == district_total == dates_total`. Leave the date strings `01/09/2026` and `15/10/2026`.

**Checkpoint**: The dates total comes from the visible settled column, and the test is not marked expected-fail.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/029-dates-visible-rows/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T006 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v` from `specs/029-dates-visible-rows/quickstart.md`
- [ ] T007 Confirm the only files changed for T004 and T005 are `pages/alerts_analysis/population_page.py` and, only if an xfail decorator was removed, `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, and that no path under `core/` changed for this slice

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks the user story
- **User Story 1 (Phase 3)**: Depends on Foundational
- **Polish (Phase 4)**: Depends on User Story 1

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on another story. The hour and district readers stay so the equality still compares those three totals.

### Within User Story 1

- T004 and T005 edit different files and can run together
- The live pytest run waits until both are done

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 and T005 can run together
- T006 then T007 stay in that order

---

## Parallel Example: User Story 1

```bash
# The reader and the xfail check edit different files:
Task: "Sum only visible dates rows in pages/alerts_analysis/population_page.py"
Task: "Remove pytest.mark.xfail from tests/ui/alerts_analysis_dashboard/test_population_invariants.py when it is present"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 and T005 so the dates total is the settled visible column and the test is strict
3. Stop if the dates total still includes a hidden row

### Incremental Delivery

1. Setup and foundational lock the menu, the back button, the hour reader, the district reader, and the `core/` boundary
2. User Story 1 sums visible rows only and keeps the three-chart assertion strict
3. Phase 4 runs `test_hour_date_and_district_sums_match`

### Parallel Team Strategy

T004 edits `pages/alerts_analysis/population_page.py`. T005 edits the test file only when an xfail decorator is present. Those two files are independent.

---

## Notes

- Do not edit `core/components/chart.py`
- Do not change `_svg_mark_total` or the district branch of `chart_total`
- Do not call `_sum_scrolled_alert_column` from the dates total
- Do not mark the three-chart test expected-fail
- Do not change the date strings `01/09/2026` and `15/10/2026`
- Inline comments in the edited Python stay English
