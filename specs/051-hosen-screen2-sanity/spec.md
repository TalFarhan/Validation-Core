# Feature Specification: Hosen Status Screen 2 YAML Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `051-hosen-screen2-sanity`; git checkout stays put)

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Implement YAML sanity for Hosen Status Screen 2 (investigation) and leave Screen 1 unchanged. Source of truth is the existing block `data/hosen/db_sanity.yaml` → `hosen_dashboard.screen_2_investigation`. Do not invent or edit those numbers. There is no SQL client and no new comparison engine."

## Clarifications

### Session 2026-11-16

- Q: Which git checkout should this slice use? → A: Spec directory `051-hosen-screen2-sanity`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. `specs/050-hosen-screen1-sanity/` stays untouched.
- Q: Where does the test live? → A: `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`. It uses the existing `hosen_status_dashboard` fixture. Marker: `sanity`. Private compare helpers stay in that file. No `tests/helpers/` module is added.
- Q: What is the source of truth? → A: The existing `hosen_dashboard.screen_2_investigation` block. This slice does not edit `data/hosen/db_sanity.yaml` and does not invent replacement numbers. There is no SQL client.
- Q: What already exists? → A: `HosenStatusPage.navigate()` opens תמ"צ חוסן and Screen 1 only. Screen 1 date selection, smart-filter selection, spinner settle, `VisualTable`, and `collect_virtualized_rows` already exist. Screen 2 is not the landing screen.
- Q: What must stay unchanged? → A: `test_screen1_sanity.py` behavior, `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` (`dashboard.verify_freshness()`), `core/portal`, `core/components` unless a universal reader is actually missing, and Hasbara, Credit, and Alerts data, pages, and tests.
- Q: How does a YAML `null` compare? → A: The cell is empty on screen. The page returns display text. The test treats `null` as an empty cell. A percent string stays display text.
- Q: When does an empty read fail? → A: A visible anchor plus an empty reader fails. A missing anchor skips that block. If every block is skipped, the test calls `pytest.skip`. Failure messages name the YAML path.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Investigation screen matches the golden YAML (Priority: P1)

A validation author opens תמ"צ חוסן, leaves the landing screen, opens the investigation screen titled by `screen_2_investigation.title`, applies the golden date and filters, and compares that screen to `hosen_dashboard.screen_2_investigation`.

**Why this priority**: Screen 2 is the whole slice. Screen 1 already has its own test and must keep passing.

**Independent Test**: `test_hosen_screen2_matches_golden` opens the report through `hosen_status_dashboard`, opens the investigation screen, applies `date` then `filters`, waits until Screen 2 is idle, reads the screen, and walks `screen_2_investigation`.

**Acceptance Scenarios**:

1. **Given** the report opens on Screen 1, **When** the suite starts the Screen 2 test, **Then** a page method opens the investigation screen whose title is the golden title `תמ״צ התנהגות - מסך תחקור`.
2. **Given** that screen is open, **When** the suite applies filters, **Then** it applies `screen_2_investigation.date` through the existing date combobox path, then each `screen_2_investigation.filters` entry in YAML order (`district`, then `subdistrict`) through the existing smart-filter path.
3. **Given** a selection has just been made, and again just before the read, **When** the page waits, **Then** a visible spinner is hidden and the Screen 2 anchor is visible. The wait does not sleep, does not call `wait_for_timeout`, and does not wait for network idle.
4. **Given** the golden block, **When** the suite compares the reading, **Then** `title`, `date`, `filters`, `tables.authorities_breakdown_table`, `tables.totals_row`, and `tables.trends_by_date_table` are checked. The test body does not hold locators.
5. **Given** Screen 1's sanity test and the freshness smoke test, **When** this slice is added, **Then** both keep their current behavior.

---

### User Story 2 - Authority breakdown and the average row (Priority: P1)

A validation author reads the bottom authority table and the summary/average row for the filtered slice.

**Why this priority**: Those two blocks are the per-authority grades and the slice average.

**Independent Test**: The `tables.authorities_breakdown_table` and `tables.totals_row` checks inside `test_hosen_screen2_matches_golden`.

**Acceptance Scenarios**:

1. **Given** a golden authority row, **When** the table is visible, **Then** the row with that `authority` matches `leadership`, `welfare`, `effective_behavior`, `belonging`, `functional_continuity`, `narrative`, `community_resources`, `information`, and `resilience_score`. Percent strings stay display text. Extra UI rows do not fail the test.
2. **Given** `tables.totals_row`, **When** the summary/average row is visible, **Then** the same metric fields match. The row is not required to carry an `authority` name.
3. **Given** the table anchor is visible and the golden list has rows, **When** the reader returns no authority rows, **Then** the test fails. **Given** the anchor is missing, **When** the suite reaches that block, **Then** that block is skipped.

---

### User Story 3 - Trends chart read as a table (Priority: P1)

A validation author reads the trends visual, which is a chart until it is shown as a table.

**Why this priority**: The date series is not in the authority grid. The golden file already stores it as rows, including one empty cell.

**Independent Test**: The `tables.trends_by_date_table` check inside `test_hosen_screen2_matches_golden`.

**Acceptance Scenarios**:

1. **Given** the trends chart is visible, **When** the page reads it, **Then** it uses the existing `VisualTable` reader (right-click, then `הצג כטבלה`) and does not reimplement that menu.
2. **Given** a golden `creation_date`, **When** the table is read, **Then** that date's metric fields match. Extra dates on screen do not fail the test.
3. **Given** a YAML `null` such as `functional_continuity` on `13/06/2025`, **When** the cell is compared, **Then** the on-screen cell is empty. The page does not invent `0%` for that cell.
4. **Given** the chart anchor is visible and the golden list has rows, **When** the reader returns no rows, **Then** the test fails. **Given** the anchor is missing, **Then** that block is skipped.

### Edge Cases

- A percent string is not parsed into a float. `88%` does not match `88` or `0.88`.
- A YAML `null` matches an empty cell. It does not match `0%`.
- Extra authority rows and extra trend dates do not fail the test. A missing golden authority or a missing golden date fails.
- Extra slicers that are not listed under `filters` do not fail the test. Every listed id must show the golden label.
- The Screen 2 title uses Hebrew gershayim in the YAML (`תמ״צ`). The open and title check accept that spelling and the ASCII-quote spelling (`תמ"צ`). The YAML text is not edited to force one quote character.
- An authority cell that carries a second accessibility line publishes the first line only, the same rule Screen 1 already uses for `קרית מלאכי`. Screen 1's reader is not rewritten for this.
- A visible spinner that never hides fails inside the page timeout. A spinner that is not showing is not a failure.
- If the title, date, filters, authority table, totals row, and trends chart anchors are all absent, the test skips. A present anchor is still asserted.
- Screen 1's ready text stays the landing-screen locator. Opening Screen 2 does not change what `navigate()` or the smoke test wait for.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `HosenStatusPage` MUST gain a method that opens the investigation screen. The title it opens is `screen_2_investigation.title` (`תמ״צ התנהגות - מסך תחקור`). The test passes that string. The test body MUST NOT contain a locator.
- **FR-002**: After the screen is open, the test MUST apply `screen_2_investigation.date` through the existing date combobox path, then each entry in `screen_2_investigation.filters` in YAML order through the existing smart-filter path. `district` stays before `subdistrict`. The page resolves each id. An unknown id fails the test.
- **FR-003**: After each selection, and once more before the read, the page MUST expect a visible report spinner (`spinner` class or `aria-busy`) to be hidden when one is showing, then expect the Screen 2 anchor to be visible. The code MUST NOT call `sleep`, `wait_for_timeout`, or a network-idle wait.
- **FR-004**: The Screen 2 reader MUST return `title`, `date` (the selected combobox label), `filters`, and `tables` with `authorities_breakdown_table`, `totals_row`, and `trends_by_date_table`.
- **FR-005**: `authorities_breakdown_table` MUST match each golden `authority`. Extra UI rows MUST NOT fail the test. Each matched row MUST compare `leadership`, `welfare`, `effective_behavior`, `belonging`, `functional_continuity`, `narrative`, `community_resources`, `information`, and `resilience_score` as display text.
- **FR-006**: `totals_row` MUST be the summary/average row and MUST compare those same metric fields.
- **FR-007**: `trends_by_date_table` MUST be read with the existing `VisualTable` reader (right-click, then `הצג כטבלה`). Each golden `creation_date` MUST match. Extra dates MUST NOT fail the test. A YAML `null` MUST mean that cell is empty on screen.
- **FR-008**: A visible anchor whose reader returns empty data while the golden block has data MUST fail. A missing anchor MUST skip that block only. If every block is skipped, the test MUST `pytest.skip`. Failure messages MUST name the YAML path, starting at `hosen_dashboard.screen_2_investigation`.
- **FR-009**: The test MUST live in `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`, use `hosen_status_dashboard`, and carry the `sanity` marker. Compare helpers MUST stay private to that file.
- **FR-010**: This slice MUST NOT add a comparison engine under `tests/helpers/`, MUST NOT add a warehouse client, MUST NOT import Hasbara, Credit, or Alerts pages or tests, and MUST NOT edit `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports.
- **FR-011**: `core/portal` and `core/components` MUST stay unchanged unless a universal reader is actually missing. `VisualTable` and the Screen 1 date and smart-filter paths already exist, so this slice does not add one.
- **FR-012**: `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` MUST keep calling `dashboard.verify_freshness()`. `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` MUST keep its current behavior.
- **FR-013**: `data/hosen/db_sanity.yaml` MUST NOT be edited. Numbers, `null`, and the golden title stay as they are checked in.
- **FR-014**: Hebrew MUST stay in locator constants and in the YAML. New Python identifiers and comments inside functions MUST stay English.
- **FR-015**: `docs/COVERAGE_CATALOG.md` MUST gain the Screen 2 YAML keys, the page methods that read them, and the Screen 2 test name. The Screen 1 rows stay.

### Key Entities

- **Screen 2 investigation record**: `hosen_dashboard.screen_2_investigation` in `data/hosen/db_sanity.yaml`. Fields: `title`, `date`, `filters`, `tables`.
- **Filter map**: `district` and `subdistrict`, applied in YAML order after `date`. The same map is read back after the screen is idle.
- **Authority row**: `authority` plus the nine metric fields. Percent values are display strings.
- **Totals row**: the nine metric fields for the summary/average row. No `authority` key in the golden file.
- **Trend row**: `creation_date` plus the nine metric fields. A metric MAY be YAML `null`, which means an empty cell.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. This slice does not edit it. `navigate()` still lands on Screen 1. The freshness caption stays `מועד רענון`.
- **AC-002**: `HosenStatusPage` MUST keep inheriting `ReportShell`. This slice MUST NOT re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: The Screen 1 ready locator stays `תמ"צ ארצי - דיווחי קה"א יקל"ר`. Screen 2 uses its own anchor, the investigation title. The smoke test still waits on the Screen 1 locator because it never opens Screen 2.
- **AC-004**: `navigate`, `verify_freshness`, `select_screen_1_filter`, `wait_for_screen_1_idle`, and `read_screen_1_metrics` keep their current contracts. Screen 2 methods are additive.
- **AC-005**: Layer 2 stays report-agnostic. This slice composes the existing date combobox path, the existing smart-filter path, `collect_virtualized_rows`, and `VisualTable`. It does not load the YAML from `core/` and does not add Hosen titles to `core/`.
- **AC-006**: The page object stays in `pages/hosen_status/page.py`. This slice adds no `db/clients/` module.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` opens the investigation screen, applies `date` then `filters`, waits until Screen 2 is idle, and fails with a YAML path when a golden value differs.
- **SC-002**: A golden percent string matches only the same display text. A golden `null` matches only an empty cell. Extra authority rows and extra trend dates do not fail the test.
- **SC-003**: With a visible authority-table anchor and a non-empty golden list, an empty row collection fails. With a visible trends-chart anchor and a non-empty golden list, an empty `VisualTable` read fails. A missing anchor skips only that block. Every block skipped calls `pytest.skip`.
- **SC-004**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` still passes. `test_dashboard_updated_within_24_hours` still calls `dashboard.verify_freshness()`.
- **SC-005**: The diff for this slice contains no edits under `core/`, `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' page and test modules, and no edits that change Screen 1 test behavior.

## Assumptions

- Screen 2 is a page inside the same תמ"צ חוסן report. `navigate()` still opens Screen 1. A page method then switches to the investigation screen.
- The date control and the district and subdistrict smart filters on Screen 2 are the same controls Screen 1 already drives. Screen 2 waits on the investigation title, not on the Screen 1 ready text.
- The authority breakdown is a grid already shown as a table. The trends visual is a chart until `VisualTable` opens `הצג כטבלה`.
- The totals row is the summary/average row of that authority breakdown, or a sibling visual of the same nine percents if the live grid keeps the average outside the body. The golden file has no authority name on that row.
- Hebrew column titles on the live grid match the Screen 1 category names already stored on the page (`מנהיגות`, `דאגה לרווחה`, and the rest). Implementation copies any live spelling that differs into a page constant. It does not copy that spelling into the YAML, and it does not put it in the test.
- Subset comparison is private to `test_screen2_sanity.py`. It is not imported from the Screen 1 module and not imported from Hasbara, Credit, or Alerts.
