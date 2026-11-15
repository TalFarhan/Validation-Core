# Tasks: Centralize Show as a Table Extraction (Fleet MVP)

**Input**: Design documents from `specs/048-fleet-table-extraction/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/visual-table.md, contracts/fleet-chart-table.md, quickstart.md

**Tests**: The spec's independent test for User Story 1 is a unit test of `rows_to_label_values` (no browser). Write that test first. Fleet smoke (`pytest tests/ui/fleet_dashboard/`) is a completion gate because this slice adds a Layer 2 module and edits the fleet page (plan.md, constitution VII). The four golden chart tests in quickstart.md are the User Story 2 check and need portal auth.

**Organization**: Tasks are grouped by user story. US1 creates `core/components/visual_table.py`. US2 adds `read_chart_segments` on the fleet page and points the golden and label-coverage helpers at it. US3 proves hover and hierarchy still use the canvas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US3 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Layer 2 reader: `core/components/visual_table.py`
- Layer 2 export: `core/components/__init__.py`
- Fleet page: `pages/fleet_dashboard/main_dashboard_page.py`
- Mapper unit test: `tests/unit/test_visual_table_rows.py`
- Golden helper: `tests/sanity/fleet_dashboard/test_db_sanity.py`
- Label-coverage helpers: `tests/ui/fleet_dashboard/dashboard_validation.py`
- Contracts: `specs/048-fleet-table-extraction/contracts/visual-table.md`, `specs/048-fleet-table-extraction/contracts/fleet-chart-table.md`
- OFF-LIMITS: `core/portal/page.py`, `core/components/chart.py`, `pages/alerts_analysis/`, `pages/credit_consumption/`, `pages/status_picture/`, `data/fleet/db_sanity_all.yaml`, `db/`, `tests/e2e/test_chart_drilldown.py`, `tests/e2e/test_chart_tooltips.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Lock the edit list and record the canvas and hover paths before adding the table reader

- [X] T001 Confirm the edit list in `specs/048-fleet-table-extraction/plan.md`, `specs/048-fleet-table-extraction/contracts/visual-table.md`, and `specs/048-fleet-table-extraction/contracts/fleet-chart-table.md`: this slice may add `core/components/visual_table.py`, export `VisualTable` from `core/components/__init__.py`, add `read_chart_segments` in `pages/fleet_dashboard/main_dashboard_page.py`, add `tests/unit/test_visual_table_rows.py`, and edit `assert_chart_matches` in `tests/sanity/fleet_dashboard/test_db_sanity.py` plus `assert_chart_labels_match_db_sample` and `assert_unit_drilldown_matches_db` in `tests/ui/fleet_dashboard/dashboard_validation.py`. Do not edit `core/portal/page.py`, `core/components/chart.py`, `get_chart_segment_labels`, `hover_chart_segment`, or `expand_chart_hierarchy`.
- [X] T002 [P] Inventory without editing. In `pages/fleet_dashboard/main_dashboard_page.py`, confirm `get_chart_segment_labels` reads `svg title` and legend/axis text, `hover_chart_segment` hovers for a tooltip, and `expand_chart_hierarchy` snapshots labels with `get_chart_segment_labels` then polls `wait_for_chart_labels_change`. In `tests/sanity/fleet_dashboard/test_db_sanity.py`, confirm `assert_chart_matches` calls `get_chart_segment_labels` and `hover_chart_segment`, and skips with `exposed golden labels but no tooltip appeared`. Record that those three page methods stay on the canvas (`specs/048-fleet-table-extraction/research.md` R6).

**Checkpoint**: Scope is locked. The canvas harvest, hover, and expand paths are known and not yet changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the fleet page inputs the new method will call, without moving Show as a table onto `ReportShell`

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Confirm in `pages/fleet_dashboard/main_dashboard_page.py` that `_CHART_TITLES` contains `unit`, `source`, `category`, and `withdrawal`, that `chart_section(chart_key)` returns the exclusive visual host, that `dismiss_tooltip` exists, and that `__init__` sets `self.dashboard` to `page.frame_locator("main iframe")` and inherits `self.timeout`. Do not edit those methods. Do not add the table workflow to `core/portal/page.py` (`specs/048-fleet-table-extraction/research.md` R2, `specs/048-fleet-table-extraction/contracts/fleet-chart-table.md`).

**Checkpoint**: Chart keys, the right-click host, the iframe, and the page timeout are the shared inputs. Story work can start.

---

## Phase 3: User Story 1 - A shared reader opens a visual as a table (Priority: P1) 🎯 MVP

**Goal**: `VisualTable.read_rows` right-clicks a caller-supplied visual, opens Show as a table, returns header-to-cell rows, and clicks Back to report. `rows_to_label_values` maps those rows to label → int with no fleet literals in the module.

**Independent Test**: `pytest tests/unit/test_visual_table_rows.py` passes with no browser. The module file contains no fleet chart title and no `התרעות` measure header.

### Tests for User Story 1

> Write this test first. It fails on import until T005 adds `rows_to_label_values`.

- [X] T004 [US1] Create `tests/unit/test_visual_table_rows.py` that imports `rows_to_label_values` from `core.components.visual_table`. Cover, with no Playwright: a text cell plus an integer cell; integer `0`; thousands separators and a bidi mark `\u200f` stripped before parsing; a row omitted when any cell equals or starts with a caller-supplied `סה"כ` in `skip_labels`; a pie cell `name 3 (50.0%)` becoming label `name` and value `3` when no pure integer cell exists; a doubled label `מחוז דןמחוז דן` collapsed to `מחוז דן`; the first value kept when the same label appears twice; a percent-only cell not used as the value; a row with no integer omitted; an empty list returning `{}`. Docstrings in this file are English (`specs/048-fleet-table-extraction/contracts/visual-table.md`, `specs/048-fleet-table-extraction/data-model.md`).

### Implementation for User Story 1

- [X] T005 [US1] Create `core/components/visual_table.py` with `VisualTable(page, frame, timeout_ms=None)` and `read_rows(self, container, *, name="visual") -> list[dict[str, str]]`. Right-click `container`. Click the exact visible `menuitem` `הצג כטבלה`, else `Show as a table`, searching `frame` then `page`, with a short wait per candidate inside `timeout_ms` (default `settings.DEFAULT_TIMEOUT`). Read a visible `grid` or else `table`: headers from `columnheader`, cells from `gridcell` or `cell`, dict order equal to header order, bidi marks stripped. Scroll the scrollable ancestor from the top in page steps, store each data row once by its cell tuple, skip a row whose cells equal the headers, skip hidden rows, and stop after two passes that add no row and do not move, or at the timeout. In `finally`, when the menu item was clicked, click exact `button` `חזרה לדוח` or `Back to report` (frame then page) and wait until that button is hidden. A missing menu, grid, or back button raises `AssertionError` and may include `name`. Do not parse integers inside `read_rows`. Add pure `rows_to_label_values(rows, *, skip_labels=()) -> dict[str, int]` implementing the cases in T004. The only user-facing literals in this module are the four chrome strings. Do not import the fleet page. Comments inside the functions are English (`specs/048-fleet-table-extraction/contracts/visual-table.md`).
- [X] T006 [US1] In `core/components/__init__.py`, import `VisualTable` from `core.components.visual_table` and add it to `__all__` beside the existing `Chart` export. Do not remove `Chart`. Do not edit `core/components/chart.py`.

**Checkpoint**: User Story 1 is testable with `pytest tests/unit/test_visual_table_rows.py`. The reader does not know fleet chart titles.

---

## Phase 4: User Story 2 - Fleet chart counts come from the table (Priority: P1)

**Goal**: `read_chart_segments` returns `dict[str, int]` for one fleet chart, and the golden helper compares those integers instead of hovering

**Independent Test**: `assert_chart_matches` calls `read_chart_segments` and does not call `hover_chart_segment`. On the live portal, the four golden chart tests fail when a table integer differs from the golden count, and they do not skip with `no tooltip appeared`.

### Implementation for User Story 2

- [X] T007 [US2] Add `read_chart_segments(self, chart_key: str) -> dict[str, int]` to `pages/fleet_dashboard/main_dashboard_page.py`. Unknown `chart_key` raises `ValueError` before any click. Call `assert_chart_visible(chart_key)`, then `dismiss_tooltip()`, then `VisualTable(self.page, self.dashboard, timeout_ms=self.timeout).read_rows(self.chart_section(chart_key), name=chart_key)`, then `rows_to_label_values(rows, skip_labels=('סה"כ',))`. Do not read SVG titles or legend text in this method. Do not change `get_chart_segment_labels`, `hover_chart_segment`, `expand_chart_hierarchy`, `wait_for_chart_labels_change`, `drill_up_chart`, `reset_chart_hierarchy`, or `expand_via_tooltip_drilldown`. English comments only (`specs/048-fleet-table-extraction/contracts/fleet-chart-table.md`).
- [X] T008 [P] [US2] In `assert_chart_matches` in `tests/sanity/fleet_dashboard/test_db_sanity.py`, replace the `get_chart_segment_labels` plus `hover_chart_segment` plus `parse_tooltip_entries` loop with one `read_chart_segments(chart_key)` call. Keep `normalize_label`. If no golden name is present in the mapping, keep `pytest.skip` with `chart {chart_key} exposed no golden labels`. If any golden name is present, every golden name must be present or the helper raises `AssertionError` naming the chart and the segment. Compare the mapped integer to the golden count; on mismatch raise `AssertionError` that includes the chart key, the segment, the UI integer, and the golden count. Delete the `LoadTimeoutError` branch and both skips whose message is `exposed golden labels but no tooltip appeared`. Do not edit `test_ui_credited_ledger_rows` or the KPI summary test (`specs/048-fleet-table-extraction/contracts/fleet-chart-table.md`).
- [X] T009 [P] [US2] In `tests/ui/fleet_dashboard/dashboard_validation.py`, change `assert_chart_labels_match_db_sample` and `assert_unit_drilldown_matches_db` so the UI label list is `list(dashboard.read_chart_segments(chart_key))` (use `"unit"` for the drilldown helper). Keep `labels_cover_segments`, the sample-size threshold, and the assertion messages. Do not change `assert_chart_tooltip_segment_matches_db` or `assert_chart_tooltips_match_db_sample`; those must still call `hover_chart_segment` (`specs/048-fleet-table-extraction/contracts/fleet-chart-table.md`).

**Checkpoint**: User Story 2 reads fleet chart counts from the table. Tooltip helpers still hover.

---

## Phase 5: User Story 3 - Hover and hierarchy stay on the canvas (Priority: P1)

**Goal**: Hierarchy polling and tooltip checks do not open Show as a table

**Independent Test**: `expand_chart_hierarchy` and `wait_for_chart_labels_change` still call `get_chart_segment_labels`. `hover_chart_segment` is still the tooltip path. `tests/e2e/test_chart_drilldown.py` still snapshots canvas labels.

### Implementation for User Story 3

- [X] T010 [US3] In `pages/fleet_dashboard/main_dashboard_page.py`, confirm `get_chart_segment_labels` still collects `svg title` and legend/axis text, and that `expand_chart_hierarchy`, `expand_via_tooltip_drilldown`, `drill_up_chart`, `reset_chart_hierarchy`, and `wait_for_chart_labels_change` still call `get_chart_segment_labels` and do not call `read_chart_segments`. Confirm `hover_chart_segment` still hovers and does not right-click Show as a table. If any of those calls were switched, point them back at `get_chart_segment_labels` or `hover_chart_segment`. Do not rewrite the hover or expand bodies (`specs/048-fleet-table-extraction/research.md` R6).
- [X] T011 [P] [US3] Confirm `assert_chart_tooltip_segment_matches_db` and `assert_chart_tooltips_match_db_sample` in `tests/ui/fleet_dashboard/dashboard_validation.py` still call `hover_chart_segment`. Confirm `tests/e2e/test_chart_drilldown.py` still calls `get_chart_segment_labels` for its before/after snapshots. Do not edit `tests/e2e/test_chart_drilldown.py` or `tests/e2e/test_chart_tooltips.py`. If T009 moved a tooltip helper onto `read_chart_segments`, move that helper back to `hover_chart_segment`.

**Checkpoint**: User Story 3 leaves hover and hierarchy on the canvas. Only the extraction callers use the table.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Run the mapper, the fleet smoke gate, and the golden chart check, and prove off-limits files stayed untouched

- [X] T012 Run `pytest tests/unit/test_visual_table_rows.py` from `specs/048-fleet-table-extraction/quickstart.md`. All mapper cases in T004 must pass. No browser and no portal auth.
- [X] T013 Run `pytest tests/ui/fleet_dashboard/` from `specs/048-fleet-table-extraction/quickstart.md`. This is the completion gate for the Layer 2 module and the fleet page edit. The suite must pass. Do not treat a golden-chart skip as a substitute for this run.
- [X] T014 [P] Run `pytest tests/sanity/fleet_dashboard/test_db_sanity.py -m sanity -k "unit_breakdown or pull_source or credit_reasons or category_actuals"` from `specs/048-fleet-table-extraction/quickstart.md` (portal auth). The four tests must take counts from `read_chart_segments`. A mismatched integer fails. They must not skip with `no tooltip appeared`. A chart that exposes none of the golden names may still skip with `exposed no golden labels`.
- [X] T015 [P] Confirm the code diff is limited to `core/components/visual_table.py`, `core/components/__init__.py`, `pages/fleet_dashboard/main_dashboard_page.py`, `tests/unit/test_visual_table_rows.py`, `tests/sanity/fleet_dashboard/test_db_sanity.py`, `tests/ui/fleet_dashboard/dashboard_validation.py`, and this feature's docs. Confirm `core/portal/page.py`, `core/components/chart.py`, `pages/alerts_analysis/`, `pages/credit_consumption/`, `data/fleet/db_sanity_all.yaml`, and `db/` have no diff. Confirm `core/components/visual_table.py` has no fleet chart title and no `התרעות` literal, and that comments inside the new functions are English.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational
  - US1 creates the reader and the unit test (T004, then T005, then T006)
  - US2 starts after T006 because it calls `VisualTable` and `rows_to_label_values`
  - US3 starts after T007 and T009 so it can catch a canvas or tooltip caller that was switched by mistake
- **Polish (Phase 6)**: Depends on US1, US2, and US3

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on US2 or US3. MVP.
- **User Story 2 (P1)**: Starts after T006. T008 and T009 start after T007 and edit different files.
- **User Story 3 (P1)**: Starts after the fleet page and the validation helpers have been edited. It does not add a new read path.

### Within Each User Story

- T004 is written first and fails until T005 implements `rows_to_label_values`
- T005 finishes before T006 because the export imports the new class
- T007 finishes before T008 and T009 because those helpers call `read_chart_segments`
- T010 reads `pages/fleet_dashboard/main_dashboard_page.py` after T007 and must not run while T007 is editing that file
- T011 reads `tests/ui/fleet_dashboard/dashboard_validation.py` after T009

### Parallel Opportunities

- T002 can run with T001 (inventory vs plan read)
- T008 and T009 can run together after T007 (sanity helper vs label-coverage helpers)
- T010 can run with T008 after T007 (page guard vs sanity helper) and must not overlap T007
- T012, T013, T014, and T015 can run together after US3 (unit pytest, fleet smoke, golden pytest, diff check)

---

## Parallel Example: User Story 2

```text
Task: "Point assert_chart_matches at read_chart_segments in tests/sanity/fleet_dashboard/test_db_sanity.py"
Task: "Point the two label-coverage helpers at read_chart_segments in tests/ui/fleet_dashboard/dashboard_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (chart host and iframe confirmed, `ReportShell` left alone)
3. Complete Phase 3: User Story 1 (unit test, `VisualTable`, export)
4. **STOP and VALIDATE**: `pytest tests/unit/test_visual_table_rows.py`

### Incremental Delivery

1. Setup + Foundational → fleet chart host and timeout are confirmed and untouched
2. User Story 1 → shared reader and pure mapper, proven without a browser
3. User Story 2 → fleet `read_chart_segments` and the golden / label-coverage callers
4. User Story 3 → hover and hierarchy still use the canvas
5. Polish → unit pytest, fleet smoke, golden chart pytest, off-limits diff

### Parallel Team Strategy

1. One person completes Setup and Foundational
2. One person completes T004, then T005, then T006
3. After T007, together:
   - Developer A: T008 in `tests/sanity/fleet_dashboard/test_db_sanity.py`
   - Developer B: T009 in `tests/ui/fleet_dashboard/dashboard_validation.py`
4. After those edits, one person completes T010 and T011
5. Polish runs after US1–US3

---

## Notes

- [P] tasks = different files, no dependencies on an unfinished edit of that same file
- T004 must exist and fail before T005 is considered done
- T007, T010 must not be edited at the same time in `pages/fleet_dashboard/main_dashboard_page.py`
- T009 and T011 must not be edited at the same time in `tests/ui/fleet_dashboard/dashboard_validation.py`
- Do not put `read_rows` on `ReportShell`
- The removed skip message is `exposed golden labels but no tooltip appeared`
- The kept skip message is `chart {chart_key} exposed no golden labels`
- Comments inside edited functions stay English
