# Feature Specification: Hosen Status Screens 3 and 4 YAML Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `052-hosen-screen34-sanity`; git checkout stays put)

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Extend the Hosen Status Dashboard automation to Screen 3 (Geographic Investigation) and Screen 4 (Excel Export). The source of truth is the existing blocks in `data/hosen/db_sanity.yaml`. Reuse `collect_virtualized_rows`, `VisualTable.read_rows`, and `_select_smart_filter`. Do not rewrite them. Do not modify `core/portal` or `core/components` unless a generic reader is actually missing. Keep Hebrew in the page object or the YAML. For virtualized tables, use dynamic `scrollTop` evaluation to reach missing rows such as dates. For graphs, right-click the graph body and avoid the `visualHeaderAbove` container. Screens 1 and 2 tests stay untouched and fully functional."

## Clarifications

### Session 2026-11-17

- Q: Which git checkout should this slice use? → A: Spec directory `052-hosen-screen34-sanity`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. `specs/050-hosen-screen1-sanity/` and `specs/051-hosen-screen2-sanity/` stay untouched.
- Q: Where do the tests live? → A: `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` and `test_screen4_sanity.py`. Both use the existing `hosen_status_dashboard` fixture. Marker: `sanity`. Private compare helpers stay inside each file. No `tests/helpers/` module is added. Neither test imports the Screen 1 or Screen 2 module.
- Q: What is the source of truth? → A: The existing `hosen_dashboard.screen_3_geographic_investigation` and `hosen_dashboard.screen_4_excel_export` blocks. This slice does not edit `data/hosen/db_sanity.yaml` and does not invent replacement numbers. There is no SQL client.
- Q: What already exists? → A: `HosenStatusPage.navigate()` opens תמ"צ חוסן and Screen 1 only. Screen 2 already opens by title, applies a single date and smart filters, settles on its own anchor, reads a grid with `collect_virtualized_rows`, and reads a chart with `VisualTable.read_rows` after `_mark_visual_host` marks `vcGroupBody`. Screens 3 and 4 are not opened or read.
- Q: What must stay unchanged? → A: `test_screen1_sanity.py`, `test_screen2_sanity.py`, `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` (`dashboard.verify_freshness()`), `navigate`, `_report_ready_locator`, `verify_freshness`, `select_screen_1_filter`, `read_screen_1_metrics`, `open_investigation_screen`, `select_screen_2_filter`, `read_screen_2_metrics`, and `section_anchor_visible`. Hasbara, Credit, and Alerts data, pages, and tests stay untouched.
- Q: How does a YAML `null` compare? → A: The cell or the filter chip is empty on screen. The page returns display text. The test treats `null` as empty. A percent string stays display text, including a trailing decimal such as `75.0%`.
- Q: When is a `null` filter applied? → A: It is not sent to the selector. `str(None)` is not a label. The read-back of that id is an empty string.
- Q: When does an empty read fail? → A: A visible anchor plus an empty reader fails. A missing anchor skips that block. If every block on that screen is skipped, the test calls `pytest.skip`. Failure messages name the YAML path.
- Q: What is Screen 4's "Excel" check? → A: The on-screen `data_table`. This slice does not download a workbook. The golden block has no file name and no file bytes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Geographic screen matches the golden YAML (Priority: P1)

A validation author opens תמ"צ חוסן, leaves the landing screen, opens the geographic investigation screen titled by `screen_3_geographic_investigation.title`, applies the golden date range and filters, and compares that screen to `hosen_dashboard.screen_3_geographic_investigation`.

**Why this priority**: Screen 3 is half of this slice. Screens 1 and 2 already have tests and must keep passing.

**Independent Test**: `test_hosen_screen3_matches_golden` opens the report through `hosen_status_dashboard`, opens the geographic screen, applies `date_range` then `filters`, waits until Screen 3 is idle, reads the screen, and walks `screen_3_geographic_investigation`.

**Acceptance Scenarios**:

1. **Given** the report opens on Screen 1, **When** the suite starts the Screen 3 test, **Then** a page method opens the geographic screen whose title is the golden title `תמ״צ התנהגות - תחקור גיאוגרפי`.
2. **Given** that screen is open, **When** the suite applies the range, **Then** it applies `date_range.start` and then `date_range.end` through the existing date combobox path, each on its own control, with settle on the Screen 3 anchor.
3. **Given** the range is applied, **When** the suite applies filters, **Then** each `filters` entry whose value is not `null` is applied in YAML order (`level_selected`, `district`, `subdistrict`, `authority`) through the existing smart-filter path. A `null` value, including `authority`, is not typed into a control.
4. **Given** a selection has just been made, and again just before the read, **When** the page waits, **Then** a visible spinner is hidden and the Screen 3 anchor is visible. The wait does not sleep, does not call `wait_for_timeout`, and does not wait for network idle.
5. **Given** the golden block, **When** the suite compares the reading, **Then** `title`, `date_range`, `filters`, `graphs.final_resilience_score`, and `graphs.categories` are checked. The test body does not hold locators.
6. **Given** Screen 1's sanity test, Screen 2's sanity test, and the freshness smoke test, **When** this slice is added, **Then** all three keep their current behavior.

---

### User Story 2 - Geographic charts read as tables (Priority: P1)

A validation author reads the final resilience chart and each category chart. Each chart is a graph until it is shown as a table. The row identity is `date`.

**Why this priority**: The golden scores live in those graphs. They are not in a grid that is already a table.

**Independent Test**: The `graphs.final_resilience_score` and `graphs.categories` checks inside `test_hosen_screen3_matches_golden`.

**Acceptance Scenarios**:

1. **Given** a chart title is visible, **When** the page reads it, **Then** it uses the existing `VisualTable.read_rows` (right-click, then `הצג כטבלה`) and does not reimplement that menu.
2. **Given** the title text sits in a short header, **When** the page chooses the right-click target, **Then** the target is the graph body. The ~38px `visualHeaderAbove` container is not the click target. The existing `_mark_visual_host` climb to `vcGroupBody` is the host that is passed in.
3. **Given** the show-as-table grid is virtualized, **When** rows are collected, **Then** collection uses `collect_virtualized_rows`, which evaluates `scrollTop` and moves it until a further evaluation does not change it or the timeout elapses. A golden `date` that is still below the painted viewport is collected when `scrollTop` can still increase. The page does not copy that scroll loop.
4. **Given** `graphs.final_resilience_score`, **When** the chart is read, **Then** `title`, `legend`, and each golden `date` with its `score` match. The legend is text inside that chart, not the district chip. Extra dates do not fail the test.
5. **Given** `graphs.categories`, **When** each golden `title` is visible, **Then** that chart's `date` and `score` rows match. Extra charts do not fail the test. A missing golden title fails.
6. **Given** a chart anchor is visible and the golden list has rows, **When** the reader returns no rows, **Then** the test fails. **Given** the anchor is missing, **Then** that block is skipped.

---

### User Story 3 - Excel export screen matches the golden table (Priority: P1)

A validation author opens the Excel export screen titled by `screen_4_excel_export.title`, applies the golden date and filters, and compares the on-screen authority table to `hosen_dashboard.screen_4_excel_export`.

**Why this priority**: Screen 4 is the other half of this slice. The golden file stores the grid, not a downloaded file.

**Independent Test**: `test_hosen_screen4_matches_golden` opens the export screen, applies `date` then `filters`, waits until Screen 4 is idle, and walks `screen_4_excel_export`.

**Acceptance Scenarios**:

1. **Given** the report opens on Screen 1, **When** the suite starts the Screen 4 test, **Then** a page method opens the export screen whose title is the golden title `תמ״צ התנהגות - ייצוא נתונים לאקסל`.
2. **Given** that screen is open, **When** the suite applies filters, **Then** it applies `date` through the existing date combobox path, then each non-null `filters` entry in YAML order (`sector`, `district`, `subdistrict`, `authority`) through the existing smart-filter path. `sector` and `authority` are `null` in the golden file and are not typed into a control.
3. **Given** the authority grid is already a table, **When** the page reads `data_table`, **Then** it uses `collect_virtualized_rows` and does not open `הצג כטבלה`. The row identity is `authority`.
4. **Given** a golden authority, **When** the row is collected, **Then** `care_for_welfare`, `effective_behavior`, `information_and_communication`, `community_resources`, `leadership`, `narrative`, `final_score`, `functional_continuity`, and `belonging_and_solidarity` match as display text. `75.0%` does not match `75%`. Extra UI rows do not fail the test.
5. **Given** the grid is virtualized, **When** an authority is below the first viewport, **Then** the same `scrollTop` evaluation used on Screen 3 collects it. The page does not copy that loop.
6. **Given** the table anchor is visible and the golden list has rows, **When** the reader returns no rows, **Then** the test fails. **Given** the anchor is missing, **Then** that block is skipped.

### Edge Cases

- A percent string is not parsed into a float. `85%` does not match `85` or `0.85`. `75.0%` does not match `75%` or `75.0`.
- A YAML `null` matches an empty cell or an empty filter chip. It does not match `0%`, and it is not applied as the label `None`.
- Extra dates, extra category charts, and extra authority rows do not fail the test. A missing golden date, a missing golden category title, or a missing golden authority fails.
- Extra slicers that are not listed under `filters` do not fail the test. Every listed id must show the golden label, or be empty when the golden value is `null`.
- `level_selected` is `מחוז`. That word also appears inside the district label `מחוז דרום`. The level control and the district control stay distinct. The level value is not typed into the district box.
- The Screen 3 and Screen 4 titles use Hebrew gershayim in the YAML (`תמ״צ`). The open and title check accept that spelling and the ASCII-quote spelling (`תמ"צ`). The YAML text is not edited to force one quote character.
- An authority cell that carries a second accessibility line publishes the first line only. The authority `בני עי"ש` matches the gershayim spelling after quote folding.
- A visible spinner that never hides fails inside the page timeout. A spinner that is not showing is not a failure.
- If every block on that screen is absent, the test skips. A present anchor is still asserted.
- Screen 1's ready text stays the landing-screen locator. Opening Screen 3 or Screen 4 does not change what `navigate()` or the smoke test wait for.
- Screen 4 does not assert a downloaded `.xlsx`. The golden block has no file payload.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `HosenStatusPage` MUST gain a method that opens the geographic screen. The title it opens is `screen_3_geographic_investigation.title`. The test passes that string. The test body MUST NOT contain a locator. `open_investigation_screen` MUST keep its current signature and Screen 2 settle.
- **FR-002**: `HosenStatusPage` MUST gain a method that opens the Excel export screen. The title it opens is `screen_4_excel_export.title`. The same click helpers Screen 2 already uses MAY be called. Their Screen 2 behavior MUST stay.
- **FR-003**: After Screen 3 is open, the test MUST apply `date_range.start` and then `date_range.end` through the existing date combobox path, with settle on the Screen 3 anchor. It MUST then apply each non-null `filters` entry in YAML order through the existing smart-filter path. A `null` entry MUST NOT be passed to the selector.
- **FR-004**: After Screen 4 is open, the test MUST apply `date` through the existing date combobox path, then each non-null `filters` entry in YAML order through the existing smart-filter path, with settle on the Screen 4 anchor. `select_screen_1_filter` MUST keep settling on Screen 1. `select_screen_2_filter` MUST keep settling on Screen 2.
- **FR-005**: After each selection, and once more before the read, the page MUST expect a visible report spinner (`spinner` class or `aria-busy`) to be hidden when one is showing, then expect that screen's title to be visible. The code MUST NOT call `sleep`, `wait_for_timeout`, or a network-idle wait.
- **FR-006**: The Screen 3 reader MUST return `title`, `date_range` (`start`, `end`), `filters`, and `graphs` with `final_resilience_score` (`title`, `legend`, `data`) and `categories` (each `title` and `data`).
- **FR-007**: Each Screen 3 chart MUST be read with the existing `VisualTable.read_rows`. The right-click target MUST be the graph body from `_mark_visual_host`, which marks `vcGroupBody` and does not mark `visualHeaderAbove`. The menu implementation MUST stay in `VisualTable`.
- **FR-008**: Chart rows and the Screen 4 authority rows MUST be collected with `collect_virtualized_rows`. That function evaluates `scrollTop`. While a further evaluation can still increase `scrollTop` and the timeout has not elapsed, collection continues so a later golden `date` or `authority` is stored. The page MUST NOT copy that loop. `VisualTable.read_rows` stays the chart caller.
- **FR-009**: A golden chart `date` MUST match `score` as display text. Extra dates MUST NOT fail the test. The final-score `legend` MUST match the legend inside that chart.
- **FR-010**: `data_table` MUST match each golden `authority` and the nine metric fields as display text. Extra UI rows MUST NOT fail the test. The reader MUST NOT download a workbook.
- **FR-011**: A visible anchor whose reader returns empty data while the golden block has data MUST fail. A missing anchor MUST skip that block only. If every block on that screen is skipped, the test MUST `pytest.skip`. Failure messages MUST name the YAML path, starting at `hosen_dashboard.screen_3_geographic_investigation` or `hosen_dashboard.screen_4_excel_export`.
- **FR-012**: The tests MUST live in `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` and `test_screen4_sanity.py`, use `hosen_status_dashboard`, and carry the `sanity` marker. Compare helpers MUST stay private to the file that uses them.
- **FR-013**: This slice MUST NOT add a comparison engine under `tests/helpers/`, MUST NOT add a warehouse client, MUST NOT import Hasbara, Credit, or Alerts pages or tests, and MUST NOT edit `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports.
- **FR-014**: `core/portal` MUST stay unchanged. `core/components` stays unchanged except the `scrollTop` stop inside `collect_virtualized_rows` described in FR-008. No Hosen title, date, or header is added to `core/`.
- **FR-015**: `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` MUST keep calling `dashboard.verify_freshness()`. `test_screen1_sanity.py` and `test_screen2_sanity.py` MUST keep their current behavior. `section_anchor_visible` MUST NOT gain a `title` branch.
- **FR-016**: `data/hosen/db_sanity.yaml` MUST NOT be edited. Numbers, `null`, and the golden titles stay as they are checked in.
- **FR-017**: Hebrew MUST stay in locator constants and in the YAML. New Python identifiers and comments inside functions MUST stay English.
- **FR-018**: `docs/COVERAGE_CATALOG.md` MUST gain the Screen 3 and Screen 4 YAML keys, the page methods that read them, and the two test names. The Screen 1 and Screen 2 rows stay.

### Key Entities

- **Screen 3 geographic record**: `hosen_dashboard.screen_3_geographic_investigation`. Fields: `title`, `date_range`, `filters`, `graphs`.
- **Date range**: `start` and `end`, applied in that order before `filters`. Both are display labels.
- **Screen 3 filter map**: `level_selected`, `district`, `subdistrict`, `authority`. `authority` is `null` in the golden file, which means the chip is empty and the selector is not called for that id.
- **Final resilience chart**: `title`, `legend`, and `data` rows of `date` plus `score`.
- **Category chart**: `title` plus `data` rows of `date` plus `score`. The golden list has eight titles.
- **Screen 4 export record**: `hosen_dashboard.screen_4_excel_export`. Fields: `title`, `date`, `filters`, `data_table`.
- **Screen 4 filter map**: `sector`, `district`, `subdistrict`, `authority`. `sector` and `authority` are `null` in the golden file.
- **Export row**: `authority` plus the nine metric fields. Percent values are display strings, including one decimal place.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. This slice does not edit it. `navigate()` still lands on Screen 1. The freshness caption stays `מועד רענון`.
- **AC-002**: `HosenStatusPage` MUST keep inheriting `ReportShell`. This slice MUST NOT re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: The Screen 1 ready locator stays `תמ"צ ארצי - דיווחי קה"א יקל"ר`. Screen 3 and Screen 4 use their own title anchors. The smoke test still waits on the Screen 1 locator.
- **AC-004**: `navigate`, `verify_freshness`, `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, `open_investigation_screen`, `select_screen_2_filter`, `wait_for_screen_2_idle`, and `read_screen_2_metrics` keep their current contracts. Screen 3 and Screen 4 methods are additive.
- **AC-005**: Layer 2 stays report-agnostic. This slice composes the existing date combobox path, `_select_smart_filter`, `collect_virtualized_rows`, and `VisualTable`. The only Layer 2 edit is the `scrollTop` continuation inside `collect_virtualized_rows`. It does not load the YAML from `core/` and does not add Hosen titles to `core/`.
- **AC-006**: The page object stays in `pages/hosen_status/page.py`. This slice adds no `db/clients/` module.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` opens the geographic screen, applies `date_range` then the non-null filters, waits until Screen 3 is idle, and fails with a YAML path when a golden value differs.
- **SC-002**: `pytest tests/sanity/hosen_status_dashboard/test_screen4_sanity.py` opens the export screen, applies `date` then the non-null filters, and fails with a YAML path when a golden authority or percent differs.
- **SC-003**: A golden percent string matches only the same display text. A golden `null` matches only an empty cell or an empty chip. Extra dates and extra authority rows do not fail the test.
- **SC-004**: With a visible chart anchor and a non-empty golden list, an empty `VisualTable` read fails. With a visible export-table anchor and a non-empty golden list, an empty `collect_virtualized_rows` result fails. A missing anchor skips only that block. Every block on that screen skipped calls `pytest.skip`.
- **SC-005**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` and `test_screen2_sanity.py` still pass. `test_dashboard_updated_within_24_hours` still calls `dashboard.verify_freshness()`.
- **SC-006**: Because `collect_virtualized_rows` changes, `pytest tests/ui/fleet_dashboard/` passes at 100%. The diff contains no edits under `core/portal`, `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' page and test modules, and no edits that change Screen 1 or Screen 2 test behavior.

## Assumptions

- Screens 3 and 4 are pages inside the same תמ"צ חוסן report. `navigate()` still opens Screen 1. A page method then switches by the golden title, using the page-navigation control Screen 2 already clicks.
- Screen 3 has two date controls. Screen 4 has one date control, the same kind Screen 2 already drives. Each call goes through `_select_date_combobox`. Another report's date-range method is not imported.
- `level_selected`, `sector`, and `authority` are smart filters on these screens. Their Hebrew search placeholders are copied into page constants from the live control. They are not added to the Screen 1 role map, so `_smart_filter_label`'s district and subdistrict indexes stay as they are.
- Screen 3 charts are graphs until `VisualTable` opens `הצג כטבלה`. `_mark_visual_host` already skips the 38px `visualHeaderAbove` header and marks `vcGroupBody`. Screen 3 calls that helper and does not change the climb, because Screen 2's trends read uses it.
- Screen 4 `data_table` is a grid already shown as a table. `VisualTable` is not used for it.
- `collect_virtualized_rows` today stops when one viewport adds no new row id, even if `scrollTop` can still increase. That stop drops later dates on a show-as-table grid. The continuation stays inside that function so Screen 3 charts and Screen 4 authorities share it, and so the page does not grow a second scroller.
- Hebrew chart titles and column headers on the live screen match the golden titles and the category names already stored on the page. Implementation copies any live spelling that differs into a page constant. It does not copy that spelling into the YAML, and it does not put it in the test.
- Subset comparison is private to each new test file. It is not imported from the Screen 1 or Screen 2 module.
