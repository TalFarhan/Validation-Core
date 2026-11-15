# Feature Specification: Hasbara Dashboard UI Sanity Validation

**Feature Branch**: `feature/reportportal-integration` (spec directory `049-hasbara-ui-validation`; git checkout stays put)

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Create an E2E sanity suite that validates the Hasbara Dashboard UI (Written Response, Written Response Investigation, Satisfaction Feedback, Feedback Investigation) against the unified golden YAML for October 2026. Check the date range and default secondary filters on every tab, then match KPIs, charts, and detail grids to `screen_1_written_response`, `investigation_table_data`, `screen_3_satisfaction_feedback`, and `feedback_investigation_table_data`. Wait for each tab to finish rendering. Keep test names, locators, and comments in English."

## Clarifications

### Session 2026-11-04

- Q: Which git checkout should this slice use? → A: Spec directory `049-hasbara-ui-validation`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. Sibling `048-fleet-table-extraction` stays untouched.
- Q: Where do the tests live? → A: `tests/sanity/public_inquiries_dashboard/`. The browser flow is end to end against the live report. This repository keeps warehouse compares in `tests/e2e/` and golden-YAML compares in `tests/sanity/`.
- Q: What is the source of truth? → A: `data/hasbara/db_sanity.yaml` under `hasbara_dashboard`. The October range is read from each screen's `dashboard_info.date_range`. It is not a literal in the test. The YAML file is not edited. No SQL and no `db/clients/` module.
- Q: What already exists? → A: `PublicInquiriesPage` opens the report and exposes freshness only. This slice adds readers and a new sanity module. The smoke test stays a one-line `verify_freshness()` call.
- Q: How are detail grids compared? → A: Golden rows are a sample. Screen 2 matches on `request_id`. Screen 4 matches on `inquiry_id`. Every golden field on that row must be equal, including handling time, platform, topic, comments, and empty cells. Extra UI rows are ignored. A missing golden id fails.
- Q: What does the hourly trend assert? → A: `requests_by_hour_trend` stores series names and `x_axis_labels` only. Those match. Point values are absent from the golden file and are not invented.
- Q: When is an empty UI a failure? → A: If the golden block has keys or rows and the reader returns empty, the test fails. `pytest.skip` is allowed only when that visual or grid is genuinely not rendered.

### Session 2026-11-05

- Q: What happens to `dashboard_info.last_updated`? → A: The key was removed from `data/hasbara/db_sanity.yaml`. Sanity tests do not read it and do not call a last-updated assertion. `verify_freshness` stays the smoke check. The page does not add a caption parser.
- Q: Where does virtualized grid scrolling live? → A: A report-agnostic collector in Layer 2 (`core/components/`). The caller supplies the visible-row reader and the row id. `request_id` and `inquiry_id` stay on `PublicInquiriesPage`. `core/portal/` is not edited.
- Q: When does Show as a table start reading? → A: After the menu click, the reader waits until the table body has a visible data cell (`tr` / `row` with `td`, `gridcell`, or `cell`). Then the same collector scrolls.
- Q: What makes screen 4 count as rendered? → A: A visible feedback-grid header (`הערות` or `הערה`), confirmed against the live screen 4 DOM during implementation. The full parenthetical title is not the rendered gate.

### Session 2026-11-11

- Q: How are screen 2 and screen 4 rows read when the canvas grid clips columns such as handling time? → A: `read_investigation_rows` and `read_feedback_rows` locate that grid's visual container and call `VisualTable.read_rows`. The reader right-clicks (`button="right"`), chooses `הצג כטבלה` or `Show as a table`, and reads every column from the expanded grid. Back to report closes that view before the method returns. Scrolling the canvas grid is not the source of those cells. Locators, waits, method names, and comments stay English.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Date range and default filters on every tab (Priority: P1)

A validation author opens ניתוח פניות הסברה and checks all four tabs. The date control shows the golden `dashboard_info.date_range` (`01/10/2026 - 31/10/2026` in the current file). Secondary slicers that the golden file lists show `הכל`. The author does not click `הכל` again.

**Why this priority**: Every later number is meaningless if the October window or a slicer has drifted.

**Independent Test**: `test_hasbara_screen1_filters_match_golden` through `test_hasbara_screen4_filters_match_golden` each open their tab, apply the YAML date range, and read the slicers.

**Acceptance Scenarios**:

1. **Given** a screen's `dashboard_info.date_range`, **When** that tab is ready, **Then** the visible date control equals that string. The test reads the string from YAML.
2. **Given** `active_filters` on screens 1, 2, and 4, **When** the tab is ready, **Then** each listed slicer displays its golden value. Every current value is `הכל`, and the test does not re-select it.
3. **Given** screen 3 has a date range and no `active_filters` block, **When** that tab is ready, **Then** the date control matches `dashboard_info.date_range`. Hours, Language, Platform, Topic, and Settlement are checked only when that control is visible, and a visible one reads `הכל`.
4. **Given** a tab click, **When** the suite reads the screen, **Then** it has waited until that screen's title or grid locator is visible.

---

### User Story 2 - Written Response matches the golden KPIs and charts (Priority: P1)

A validation author stays on the landing Written Response screen and compares the KPI cards and charts to `screen_1_written_response`.

**Why this priority**: Screen 1 is the summary contract for wait times, open and closed totals, and the breakdown charts.

**Independent Test**: `test_hasbara_screen1_kpi_match_golden` and `test_hasbara_screen1_charts_match_golden`.

**Acceptance Scenarios**:

1. **Given** the October range is applied, **When** the KPI cards are read, **Then** `inquiries_summary`, `request_closing_times`, and `response_wait_times` equal `kpi_metrics`. Counts stay integers. Duration strings such as `"00:04:16:36"` stay strings.
2. **Given** the charts are rendered, **When** they are read, **Then** `written_media_breakdown`, `language_breakdown`, `recurring_requests_breakdown`, and `leading_topics` match the golden rows. Percentages stay strings such as `"59%"` and `"100.0%"`.
3. **Given** `requests_by_hour_trend`, **When** the hourly chart is read, **Then** the series names and `x_axis_labels` match. No point value is required.
4. **Given** `dashboard_info.title` and `data_source` on screen 1, **When** they are read, **Then** both phrases are visible. The golden file has no `last_updated` key, and this test does not read the last-refresh caption.

---

### User Story 3 - Written investigation rows match the golden sample (Priority: P1)

A validation author opens the `תחקור מענה כתוב` tab and compares the grid to `investigation_table_data`.

**Why this priority**: The investigation grid is the row-level contract for handling time, platform, topic, and request id.

**Independent Test**: `test_hasbara_screen2_investigation_rows_match_golden`.

**Acceptance Scenarios**:

1. **Given** screen 1 is open, **When** the suite selects `תחקור מענה כתוב`, **Then** it waits until the investigation grid is visible before reading rows.
2. **Given** the golden rows, **When** the grid is read, **Then** each `request_id` is found and `handling_time`, `platform`, `topic`, and `request_id` equal the golden row, along with every other field on that row. Empty `agent_name` stays an empty string.
3. **Given** the live grid contains more rows than the golden sample, **When** comparison runs, **Then** those extra rows do not fail the test. A golden `request_id` that never appears fails the test.

---

### User Story 4 - Satisfaction feedback matches the golden cards and bars (Priority: P1)

A validation author opens `ניתוח משובי שביעות רצון` and compares the survey cards, distribution bars, and contact channels to `screen_3_satisfaction_feedback`.

**Why this priority**: Screen 3 is a different report page with its own cards and no detail grid.

**Independent Test**: `test_hasbara_screen3_surveys_match_golden` and `test_hasbara_screen3_distributions_match_golden`.

**Acceptance Scenarios**:

1. **Given** the satisfaction tab is ready, **When** the survey cards are read, **Then** phone, written, and quality-control values match `surveys_summary`. `"1,062"` stays a string. `surveys_filled` stays an integer. `"לא ידוע"` and `"אין מידע"` stay exact strings.
2. **Given** `message_reception`, **When** the "did the info help" bars are read, **Then** each `level` matches `count` and `percentage`.
3. **Given** `service_reception.active_tab`, **When** that tab is selected, **Then** the courtesy distribution matches `service_reception.responses`.
4. **Given** `leading_contact_channels` and `platforms_breakdown`, **When** those visuals are read, **Then** each channel and platform matches. `"Whatsapp"` stays spelled as in the YAML.

---

### User Story 5 - Feedback investigation rows match the golden sample (Priority: P1)

A validation author opens `תחקור משובים` and compares the grid to `feedback_investigation_table_data`.

**Why this priority**: Comments and inquiry ids are the fields that a loose column map would corrupt.

**Independent Test**: `test_hasbara_screen4_feedback_rows_match_golden`.

**Acceptance Scenarios**:

1. **Given** the feedback tab is ready, **When** the grid is read, **Then** each `inquiry_id` is found and every golden field equals the UI cell.
2. **Given** a golden `comments` value, **When** the comments cell is read, **Then** the Hebrew text matches exactly, and a golden `""` matches a blank cell.
3. **Given** the grid has more rows than the golden sample, **When** comparison runs, **Then** extra rows are ignored and a missing `inquiry_id` fails.

---

### User Story 6 - Existing freshness smoke stays green (Priority: P2)

A validation author runs the existing Public Inquiries smoke test. `verify_freshness` still passes.

**Why this priority**: The golden timestamp check is a separate exact match. The smoke test remains the 24-hour freshness gate.

**Independent Test**: `pytest tests/ui/public_inquiries_dashboard/` still calls `dashboard.verify_freshness()` and is not edited.

**Acceptance Scenarios**:

1. **Given** the smoke module, **When** this slice is implemented, **Then** `test_dashboard_updated_within_24_hours` still calls `dashboard.verify_freshness()`.
2. **Given** Layer 0 last-refresh parsing, **When** the sanity tests run, **Then** they do not read `last_updated` and the page does not add a caption parser. Freshness stays `verify_freshness` on the smoke test.

---

### Edge Cases

- `הכל` is the landing default and is asserted, not applied as a named choice.
- Screen 1 and screen 2 share one dashboard title. The tab label and the grid or KPI locator tell them apart.
- Screen 3 has no `active_filters` map. Its date range still comes from `dashboard_info.date_range`.
- Screen 4's golden slicers include Information, Service orientation, and Professionalism in addition to Hours, Platform, and Settlement. Those three are asserted too.
- `agent_name` and `comments` may be empty strings. The comparison treats a blank cell as `""`.
- Topic cells may contain several Hebrew topics separated by commas. The whole cell matches.
- Platform spelling differs by screen (`WhatsApp` on screen 1, `Whatsapp` on screens 3 and 4). Comparison does not case-fold.
- Duration fields stay `DD:HH:MM:SS` strings. They are not converted to timedeltas.
- A thousands separator in an integer golden field (`1324`) may appear on screen as `1,324` and still matches the integer. A golden string that already contains a comma (`"1,062"`) must match that display string.
- The hourly trend golden block has no Y values. A numeric series on screen does not fail the test and is not required.
- Golden investigation rows are the longest-handling sample, not the full 1,324 requests. Grid length is not compared.
- A rendered visual whose reader returns empty while the golden block has data fails. Skip only when that visual's title or the grid is absent.
- Power BI bidi marks in a cell are stripped before compare. The remaining Hebrew text, including comment punctuation, stays exact.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each tab's visible date control MUST equal that screen's `dashboard_info.date_range` from `data/hasbara/db_sanity.yaml`. The test MUST read the string from YAML.
- **FR-002**: Screens 1, 2, and 4 MUST show every `active_filters` value. The current file uses `הכל` for each. The suite MUST NOT re-select `הכל`.
- **FR-003**: On every tab, Hours, Language, Platform, Topic, and Settlement MUST read `הכל` when that control is visible. A control that the screen does not render is not a failure.
- **FR-004**: Screen 1 KPI cards MUST match `kpi_metrics`, including open and closed totals and both wait-time pairs.
- **FR-005**: Screen 1 charts MUST match `charts`, including media, language, recurring requests, leading topics, and the hourly series names plus `x_axis_labels`.
- **FR-006**: Screen 2 MUST match each `investigation_table_data` row on `request_id`, including `handling_time`, `platform`, `topic`, and `request_id`. Those cells MUST be read from the grid visual's Show as a table view. The view MUST be closed before the reader returns.
- **FR-007**: Screen 3 MUST match `surveys_summary`, `message_reception`, `service_reception` (after selecting `active_tab`), `leading_contact_channels`, and `platforms_breakdown`.
- **FR-008**: Screen 4 MUST match each `feedback_investigation_table_data` row on `inquiry_id`, including `comments`. Those cells MUST be read from the grid visual's Show as a table view. The view MUST be closed before the reader returns.
- **FR-009**: Switching tabs MUST wait until the destination title or grid is visible before any read. A fixed sleep is not the ready signal.
- **FR-010**: Test function names, locator variable names, and comments inside new or edited functions MUST be English. Hebrew text is limited to Power BI labels and golden values.
- **FR-011**: A golden block that contains data MUST fail the test when its reader returns empty. `pytest.skip` MUST run only when that visual or grid is not rendered.
- **FR-012**: Each mismatch MUST name the YAML path, the UI value, and the golden value.
- **FR-013**: Integer golden fields MUST compare as integers. String golden fields MUST compare as display strings, including percents, durations, `"1,062"`, `"לא ידוע"`, and `"אין מידע"`.
- **FR-014**: Sanity tests MUST NOT read `dashboard_info.last_updated` and MUST NOT call a last-updated assertion. The page MUST NOT add a date parser and MUST NOT override `verify_freshness`.
- **FR-015**: This slice MUST expand `PublicInquiriesPage` and the sanity module. It MAY add a report-agnostic virtualized-grid collector under `core/components/` and a data-row wait inside `VisualTable.read_rows`. Detail-grid reads MUST call that reader on the visual container. `VisualTable` MAY prefer the expanded data-view grid when more than one grid is visible. Its public signature MUST stay unchanged. This slice MUST leave `core/portal/`, `db/`, the golden YAML, the root `conftest.py`, and the smoke module unchanged. Hasbara labels MUST stay out of `core/`.
- **FR-016**: The smoke test `test_dashboard_updated_within_24_hours` MUST keep calling `dashboard.verify_freshness()`.

### Key Entities

- **Hasbara golden record**: `hasbara_dashboard` in `data/hasbara/db_sanity.yaml`. Four screen blocks share the October 2026 date range.
- **Written Response screen**: KPI groups plus five chart blocks. Landing screen of the report.
- **Written investigation row**: One request, identified by `request_id`, with handling time, platform, topic, and the remaining golden columns.
- **Satisfaction screen**: Survey cards, two distribution questions, leading channels, and a platform breakdown.
- **Feedback investigation row**: One inquiry, identified by `inquiry_id`, with a comments cell that may be empty or a long Hebrew note.
- **Tab**: One of the four report pages. Screen 2, 3, and 4 are reached by the Hebrew tab labels in this spec. Screen 1 is the landing page.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. Hasbara titles, tab labels, and slicer names stay on `PublicInquiriesPage`.
- **AC-002**: `PublicInquiriesPage` MUST keep inheriting `ReportShell`. Login, catalog search, iframe wait, and last-refresh verification stay in Layer 0.
- **AC-003**: Report-ready state stays the page's `_report_ready_locator`. This slice MUST NOT hardcode a Hasbara visual inside `ReportShell`.
- **AC-004**: The smoke fixture's import of `PublicInquiriesPage` and its `verify_freshness()` call MUST keep working.
- **AC-005**: Layer 2 stays report-agnostic. The page MAY compose `Slicer`, `KPI`, `VisualTable`, and the virtualized-grid collector. It MUST NOT add Hasbara labels, including `request_id` and `inquiry_id`, to `core/components/`.
- **AC-006**: The page stays in `pages/public_inquiries/`. This slice MUST NOT add `db/clients/hasbara.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The sanity module covers four tabs and the golden blocks named in FR-004 through FR-008, with one English test name per block group in the contract.
- **SC-002**: A mismatched KPI, chart row, or grid cell fails with the YAML path, the UI value, and the golden value in the assertion text.
- **SC-003**: `pytest tests/ui/public_inquiries_dashboard/` still executes `verify_freshness()` and the module file is unchanged.
- **SC-004**: `core/portal/`, `db/`, and `data/hasbara/db_sanity.yaml` have no diff from this slice. `core/components/` may add the virtualized-grid collector, the Show-as-a-table data-row wait, and the data-view grid choice. `VisualTable.read_rows` keeps its public signature.
- **SC-005**: Because Layer 2 changes, `pytest tests/ui/fleet_dashboard/` and `pytest tests/unit/test_visual_table_rows.py` are gates. The Public Inquiries smoke module remains the freshness gate and is not edited.

## Assumptions

- The report catalog term remains `ניתוח פניות הסברה`, and `PublicInquiriesPage` already opens it.
- Screen 1 is the page shown when the report becomes ready. Screens 2, 3, and 4 are the tabs `תחקור מענה כתוב`, `ניתוח משובי שביעות רצון`, and `תחקור משובים`.
- The October range in the current YAML is the scenario the suite applies. Later edits to the YAML change the expected range without a test edit.
- Hebrew visual titles for KPI cards and chart containers are copied from the live report onto the page object during implementation. They are not invented in `core/`.
- Screen 2 and screen 4 rows are read by right-clicking the grid visual and opening Show as a table. The expanded grid supplies every column, including handling time. Back to report closes that view before the reader returns. Vertical virtualization inside that expanded grid still uses the Layer 2 collector. The page maps Hebrew headers and supplies `request_id` or `inquiry_id`.
- Chart numbers are read through the same Show as a table reader (`VisualTable`). The reader waits until a data row is visible before it scrolls. Titles are supplied by the page.
- Screen 4 is rendered when its feedback grid header is visible. The long parenthetical title is not that check.
- Coverage for this report is added to `docs/COVERAGE_CATALOG.md`. `docs/PROJECT_GUIDE.md` is left as-is in this slice.
