# Feature Specification: Centralize Show as a Table Extraction (Fleet MVP)

**Feature Branch**: `feature/reportportal-integration` (spec directory `048-fleet-table-extraction`; git checkout stays put)

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Centralize Show as a table Data Extraction (Phase 1: Fleet MVP). Replace the fragile SVG/legend reading in the fleet dashboard with the Show as a table workflow. Extract that workflow into a shared core method, and apply it only to the fleet dashboard. Leave hover_chart_segment and expand_chart_hierarchy intact. Comments inside functions stay in English."

## Clarifications

### Session 2026-11-04

- Q: Which git checkout should this slice use? → A: Spec directory `048-fleet-table-extraction`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. Sibling `047-hierarchy-level-locators` stays untouched.
- Q: Where does the shared reader live? → A: Layer 2, `core/components/visual_table.py`. The brief's `ReportShell` example is not the home. Layer 0 stays portal chrome only. The menu phrases `הצג כטבלה` / `Show as a table` and `חזרה לדוח` / `Back to report` are generic Power BI chrome and may live in Layer 2.
- Q: Does `get_chart_segment_labels` open the table? → A: No. `expand_chart_hierarchy`, `drill_up_chart`, `reset_chart_hierarchy`, and `wait_for_chart_labels_change` call it, including a 200ms poll. Opening Show as a table on that poll would leave the canvas and break drill. Those methods keep the existing SVG/legend harvest. A new `read_chart_segments` is the extraction API for labels and values.
- Q: Do hover and drill-down stay? → A: Yes. `hover_chart_segment` and `expand_chart_hierarchy` keep their current interaction logic. Tooltip and drill-down checks still hover. Golden chart counts no longer depend on a tooltip.
- Q: Which other reports change? → A: None. Alerts and credit keep their private Show as a table helpers. This slice does not edit those page objects.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A shared reader opens a visual as a table (Priority: P1)

A validation author asks the shared reader to read one visual. It right-clicks that visual, chooses `הצג כטבלה` or `Show as a table`, reads the grid or table rows, and clicks `חזרה לדוח` or `Back to report` before it returns. The reader does not know fleet chart titles, KPI names, or which column is a measure.

**Why this priority**: The menu, the grid read, and the return to the canvas are the same Power BI chrome on every report. Fleet is the first caller. Later reports can adopt the same method without copying it again.

**Independent Test**: A unit test feeds header-and-cell rows to the pure mapper and checks labels, integers, total-row skips, and pie-style `"name N (P%)"` cells. No browser is required for that mapper.

**Acceptance Scenarios**:

1. **Given** a visual locator, **When** the reader runs, **Then** it right-clicks that locator and clicks the exact menu item `הצג כטבלה`, or `Show as a table` when the Hebrew item is absent.
2. **Given** the table is open, **When** rows are collected, **Then** each data row is a header-to-cell-text mapping, and rows that appear only after scrolling are included once.
3. **Given** the table was opened, **When** the read finishes or fails, **Then** the reader clicks `חזרה לדוח` or `Back to report` before returning.
4. **Given** the reader module, **When** it is inspected, **Then** it contains no fleet chart title, vehicle term, or report-specific column name.

---

### User Story 2 - Fleet chart counts come from the table (Priority: P1)

A validation author compares a fleet chart to a golden name-to-count mapping. The page reads that chart through the shared reader and returns segment label to integer value. The comparison uses those integers. It does not hover each segment to obtain the count.

**Why this priority**: SVG titles and legend text drop or garble segment names, and hover often never opens a tooltip. The four golden chart checks then skip or compare the wrong text.

**Independent Test**: Run the four fleet golden chart tests (`unit`, `source`, `withdrawal`, `category`). Each count comes from `read_chart_segments`. A count that differs from the golden value fails the test.

**Acceptance Scenarios**:

1. **Given** a fleet chart key, **When** `read_chart_segments(chart_key)` runs, **Then** it right-clicks that chart's visual host, reads the table, and returns `dict[str, int]`.
2. **Given** a row whose cells are a category and an integer, **When** the row is mapped, **Then** the category is the key and the integer is the value, including `0`.
3. **Given** a pie-style cell such as a reason name plus `N (P%)`, **When** the row is mapped, **Then** the key is the reason name and the value is `N`.
4. **Given** a total row, **When** the fleet page maps rows, **Then** a cell equal to `סה"כ` or starting with `סה"כ` is omitted. That token is supplied by the fleet page, not stored as a core literal that selects a fleet column.
5. **Given** the golden chart helper, **When** a mapped value differs from the golden count, **Then** the test fails. It does not skip because a tooltip failed to open.

---

### User Story 3 - Hover and hierarchy stay on the canvas (Priority: P1)

A validation author still hovers a segment for a tooltip check and still expands the chart hierarchy. Those paths do not open Show as a table.

**Why this priority**: Tooltips and drill-down are interactions. The table is a data read. Mixing them makes the hierarchy poll open and close the table on every tick.

**Independent Test**: `hover_chart_segment` and `expand_chart_hierarchy` keep their current steps. `get_chart_segment_labels` still reads SVG and legend text for those steps.

**Acceptance Scenarios**:

1. **Given** a tooltip or drill-down check, **When** it needs a segment, **Then** it still calls `hover_chart_segment`.
2. **Given** hierarchy expand, drill-up, or reset, **When** it snapshots or polls labels, **Then** it still uses `get_chart_segment_labels` and does not call `read_chart_segments`.
3. **Given** this slice, **When** the alerts population page and the credit consumption page are compared, **Then** their Show as a table helpers are unchanged.

---

### Edge Cases

- The Hebrew menu item is missing and the English item is present. The reader clicks the English item. The same applies to the back button.
- The context menu or the back button is rendered in the report iframe or in the outer page. The reader searches the frame first, then the outer page.
- Two passes in a row add no new row and the scroll position does not move. Collection stops. The timeout also stops collection.
- A row repeats a label. The first value is kept.
- A row has no category or no integer. That row is omitted.
- Thousands separators, spaces, and bidi marks around a number are removed before parsing. `0` is kept.
- The menu item never appears, the grid never appears, or the back button never appears. The reader raises. It does not fall back to SVG text. If the table was opened, it still attempts to leave the table.
- An unknown fleet chart key raises `ValueError`, the same way `hover_chart_segment` does.
- Duplicate header text is possible. Cells stay in header order; a repeated header does not drop the later cell from the value scan.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Show as a table workflow MUST live in a new Layer 2 type `VisualTable` in `core/components/visual_table.py`. `ReportShell` MUST NOT gain this workflow.
- **FR-002**: `VisualTable.read_rows(container, *, name="visual")` MUST right-click `container`, click menuitem `הצג כטבלה` or `Show as a table` (exact), collect data rows from the visible `grid` or `table`, scroll to include rows that are not in the first viewport, and click button `חזרה לדוח` or `Back to report` (exact) before returning.
- **FR-003**: Each returned row MUST be a `dict[str, str]` from column header text to cell text, in header order. The reader MUST NOT parse integers and MUST NOT choose a measure column.
- **FR-004**: The back click MUST run when the table was opened, including when the row read fails. A missing menu, grid, or back button MUST raise `AssertionError`. The `name` argument MAY appear in that message and MUST be treated as opaque caller text.
- **FR-005**: `core/components/visual_table.py` MUST NOT contain fleet chart titles, vehicle terms, slicer names, or a hardcoded measure header. The bilingual menu and back labels in FR-002 are the only Power BI chrome phrases it adds.
- **FR-006**: A pure function `rows_to_label_values(rows, *, skip_labels=())` MUST map those rows to `dict[str, int]` using the edge-case rules above. `skip_labels` MUST come from the caller.
- **FR-007**: `MainDashboardPage.read_chart_segments(chart_key) -> dict[str, int]` MUST call `VisualTable` on `chart_section(chart_key)` and map the rows with `skip_labels` containing `סה"כ`. It MUST dismiss a visible tooltip before the right-click.
- **FR-008**: `get_chart_segment_labels`, `hover_chart_segment`, and `expand_chart_hierarchy` MUST keep their current behavior. Hierarchy snapshots and the label poll MUST keep using `get_chart_segment_labels`.
- **FR-009**: The fleet golden chart helper MUST take labels and counts from `read_chart_segments`. It MUST NOT hover to obtain the count. Label-coverage helpers that compare chart categories to the warehouse MUST use the same mapping's keys. Tooltip helpers MUST keep hovering.
- **FR-010**: `pages/alerts_analysis/`, `pages/credit_consumption/`, `core/portal/page.py`, golden YAML, and `db/` MUST stay unchanged.
- **FR-011**: Comments inside functions added or edited in this slice MUST be English.

### Key Entities

- **Visual table row**: One data row from Show as a table. Fields are the grid's own column headers. Values are cell strings. No fleet meaning.
- **Chart segment**: A fleet category and one integer count, produced from a visual table row. The chart key (`unit`, `source`, `category`, `withdrawal`) selects the visual. The golden blocks `units_breakdown`, `pull_source_breakdown`, `credit_reasons_summary`, and `vehicle_categories[].actual` are the comparison targets and are not edited.
- **Canvas label list**: The existing `list[str]` from SVG titles and legend text. It remains the input to hierarchy change detection and hover targeting.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) stays report-agnostic and is not edited. Login, catalog search, iframe wait, and last-refresh verification stay on `ReportShell`.
- **AC-002**: `VisualTable` is composed by `MainDashboardPage` the same way `Slicer` is composed: the page passes `page` and the report iframe. `VisualTable` is not a base class.
- **AC-003**: Fleet chart titles stay on `MainDashboardPage._CHART_TITLES`. The right-click target is the existing `chart_section(chart_key)` host.
- **AC-004**: `read_chart_segments(chart_key: str) -> dict[str, int]` is new. Existing public methods keep their names and return types.
- **AC-005**: Tooltips and drill-down stay on the fleet page. Layer 2 does not hover and does not click `הסתעפות`.
- **AC-006**: The only page edit is `pages/fleet_dashboard/main_dashboard_page.py`. The test edits are the fleet golden chart helper, the fleet label-coverage helpers, a unit test for the pure mapper, and the `core.components` export. Alerts and credit page objects are out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `read_chart_segments` returns a label-to-count mapping for `unit`, `source`, `withdrawal`, and `category` without reading SVG titles or legend text.
- **SC-002**: The four golden chart tests compare those integers to the golden YAML. A mismatch fails. A missing tooltip is not a skip on those tests.
- **SC-003**: `hover_chart_segment` and `expand_chart_hierarchy` still perform hover and hierarchy clicks. `get_chart_segment_labels` still returns the canvas label list.
- **SC-004**: After the table read, the visual is back on the canvas (the back control has been clicked).
- **SC-005**: `pytest tests/ui/fleet_dashboard/` stays green. Alerts and credit modules are not edited.
- **SC-006**: In-function comments added or edited in this slice are English.

## Assumptions

- Fleet charts are single-measure visuals. The first integer cell in a row is the segment count. A later percent cell is not a second series.
- `chart_section(chart_key)` is a right-click target that opens that visual's context menu. The page already uses it as the exclusive visual host.
- Power BI may virtualize the table. Scrolling is required for the unit chart, which can have more categories than the first viewport.
- The page timeout already set on `MainDashboardPage` is the budget for the menu, the grid, the scroll, and the back button.
- Golden YAML files stay the recorded source for the fleet sanity suite. This slice does not open SQL.
- Phase 1 does not migrate alerts or credit onto `VisualTable`. Their private helpers remain the behavior for those reports.
