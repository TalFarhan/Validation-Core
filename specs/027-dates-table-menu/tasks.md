---

description: "Task list for the dates chart total opened from the right-click menu"
---

# Tasks: Dates Table from the Right-Click Menu

**Input**: Design documents from `/specs/027-dates-table-menu/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dates-menu-table.md, quickstart.md

**Tests**: Do not add a test file. `test_hour_date_and_district_sums_match` stays as it is and is the gate. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: One user story. It edits the dates branch in `pages/alerts_analysis/population_page.py` and leaves the hour and district readers in place.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1)
- Include exact file paths in descriptions

## Path Conventions

- **Dates menu table**: `pages/alerts_analysis/population_page.py`
- **Gate, unchanged**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
- **Caller, unchanged**: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- **Do not edit**: `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and the three `chart_total` branches

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/027-dates-table-menu"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] Read `chart_total` and `_dates_table_total` in `pages/alerts_analysis/population_page.py`, and confirm `HOUR_CHART` calls `_svg_mark_total`, `DISTRICT_CHART` calls `_rows_for_total`, `test_hour_date_and_district_sums_match` in `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged, and `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` calls `page.chart_total`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the method name and the no-core rule before the dates branch changes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Keep the signature `chart_total(self, title: str, series_index: int = 0)` in `pages/alerts_analysis/population_page.py`, keep `_svg_mark_total` for `HOUR_CHART`, keep `_rows_for_total` for `DISTRICT_CHART` and `SETTLEMENT_CHART`, and leave every path under `core/` unmodified, including `core/components/chart.py`

**Checkpoint**: The hour and district readers stay. `core/` is out of scope.

---

## Phase 3: User Story 1 - Dates total comes from the menu table (Priority: P1) 🎯 MVP

**Goal**: The dates total sums the `התרעות` grid cells in the table opened by `הצג כטבלה`, then returns to the report with `חזרה לדוח`.

**Independent Test**: The dates total is that column sum. A header and a `סה"כ` row are not added. After the call, the dates chart title is visible again.

### Implementation for User Story 1

- [X] T004 [US1] Replace the `Alt+Shift+F11` path in `_dates_table_total` in `pages/alerts_analysis/population_page.py` per `specs/027-dates-table-menu/contracts/dates-menu-table.md`. Dismiss an overlay that is already open, then right-click the tight visual container for `התרעות לפי תאריך` with `click(button="right")`. Click the menu item `הצג כטבלה`. If that item is absent, click `Show as a table`. Do not press `Alt+Shift+F11`. Do not dismiss the menu before the item click. Wait up to `self.timeout` for a visible `role="grid"` or `role="table"` that has `role="row"` elements, a `role="columnheader"` whose text is `התרעות`, and at least one integer `role="gridcell"` in that column. A header-only grid is not this table. If several match, use the last visible one. Sum those grid cells. Skip a row that contains a column header. Skip a row whose cell text is `סה"כ` or starts with `סה"כ`. Remove thousands separators and spaces, so `5,293` is `5293` and `0` is included. If no integer was added, or the menu item or table is missing, raise `AssertionError` naming the dates chart. Do not return the circle-mark sum. Then click a visible button named `חזרה לדוח`. If that button is absent, raise `AssertionError`. Wait until the dates chart title is visible, then return the sum as `int`. `series_index` does not select a series for this title. Any new comment must be English.

**Checkpoint**: The dates total comes from the menu table, and the canvas is back before the method returns.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Run the gate from `specs/027-dates-table-menu/quickstart.md` and confirm this slice did not edit `core/`

- [ ] T005 Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v` from `specs/027-dates-table-menu/quickstart.md`
- [ ] T006 Confirm the only file changed for T004 is `pages/alerts_analysis/population_page.py`, that `tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total` with no new parser, and that `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks the user story
- **User Story 1 (Phase 3)**: Depends on Foundational
- **Polish (Phase 4)**: Depends on User Story 1

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on another story. The hour and district readers are left in place so the three-chart test can compare all three totals.

### Within User Story 1

- One implementation task
- The live pytest run waits until the dates reader closes the table

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T005 then T006: the pytest gate comes before the edit-list check

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the page together:
Task: "Confirm .specify/feature.json pins specs/027-dates-table-menu"
Task: "Read _dates_table_total in pages/alerts_analysis/population_page.py and the unchanged three-chart test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the dates total is the `התרעות` grid-cell sum and `חזרה לדוח` has restored the chart
3. Stop if the dates total is still the zoomed circle sum of `0`

### Incremental Delivery

1. Setup and foundational lock the signature, the hour reader, the district reader, and the `core/` boundary
2. User Story 1 opens the table from the right-click menu, sums the alert column, and goes back
3. Phase 4 runs `test_hour_date_and_district_sums_match`

### Parallel Team Strategy

T004 is the only edit, in `pages/alerts_analysis/population_page.py`. One person owns that file.

---

## Notes

- Do not edit `core/components/chart.py`
- Do not change `_svg_mark_total` or the district branch of `chart_total`
- Do not press `Alt+Shift+F11`
- Do not return the circle-mark sum when the menu or the table is missing
- Do not add a parser in `tests/ui/alerts_analysis_dashboard/population_snapshot.py`
- Inline comments in the edited Python stay English
