---
description: "Task list for Hosen Status Screens 3 and 4 YAML sanity"
---

# Tasks: Hosen Status Screens 3 and 4 YAML Sanity

**Input**: Design documents from `/specs/052-hosen-screen34-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/hosen-screen34-sanity.md, quickstart.md

**Tests**: The spec requires `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` (`test_hosen_screen3_matches_golden`, marker `sanity`, fixture `hosen_status_dashboard`) and `tests/sanity/hosen_status_dashboard/test_screen4_sanity.py` (`test_hosen_screen4_matches_golden`). Those files are the deliverable, written in the user-story phases. Pytest runs in Polish. Screen 1 and Screen 2 sanity must still pass. Hosen smoke stays `dashboard.verify_freshness()` and is not edited. Fleet smoke is a gate because `core/components/virtual_grid.py` changes.

**Organization**: Three P1 stories. US1 opens the geographic screen, applies `date_range` then non-null `filters`, and compares `title`, `date_range`, and `filters`. US2 reads `graphs.final_resilience_score` and `graphs.categories` with `VisualTable` on the existing graph body. Row identity is `date`. US3 opens the Excel export screen and compares `title`, `date`, `filters`, and `data_table`. Row identity is `authority`. US1 and US2 share `pages/hosen_status/page.py` and `test_screen3_sanity.py` in that order. US3 adds methods to the same page and a separate test file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US3 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page: `pages/hosen_status/page.py` (`HosenStatusPage`)
- Golden record (do not edit): `data/hosen/db_sanity.yaml` (`hosen_dashboard.screen_3_geographic_investigation`, `hosen_dashboard.screen_4_excel_export`)
- New sanity tests: `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py`, `tests/sanity/hosen_status_dashboard/test_screen4_sanity.py`
- Existing fixture (do not edit): `tests/sanity/hosen_status_dashboard/conftest.py` (`hosen_status_dashboard`)
- Existing Screen 1 and Screen 2 tests (do not change behavior): `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`
- Existing smoke (do not edit): `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`
- Scroll stop: `core/components/virtual_grid.py` (`collect_virtualized_rows` only)
- Catalog: `docs/COVERAGE_CATALOG.md` section 11
- Contract: `specs/052-hosen-screen34-sanity/contracts/hosen-screen34-sanity.md`
- OFF-LIMITS: `core/portal/`, `core/components/visual_table.py`, `core/components/slicer.py`, `core/components/chart.py`, `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, those reports' pages and tests, `tests/helpers/`, `db/`, root `conftest.py`, `specs/050-hosen-screen1-sanity/`, `specs/051-hosen-screen2-sanity/`

Do not add `pages/hosen_status/__init__.py`. Comments inside functions stay English. Hebrew stays in locator constants or the YAML. Do not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`. Do not import Hasbara, Credit, Alerts, `test_screen1_sanity`, or `test_screen2_sanity`. Do not edit `open_investigation_screen`, `select_screen_1_filter`, `select_screen_2_filter`, `read_screen_1_metrics`, `read_screen_2_metrics`, `section_anchor_visible`, `_mark_visual_host`, `_FILTER_ROLES`, `_SCREEN2_HEADERS`, or `_field_for_header`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Pin this slice and record the readers and golden keys that must stay intact

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/052-hosen-screen34-sanity"` and the git checkout stays `feature/reportportal-integration`. Do not edit `specs/050-hosen-screen1-sanity/`, `specs/051-hosen-screen2-sanity/`, `data/hosen/db_sanity.yaml`, `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`, `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`, or `core/portal/`.
- [X] T002 [P] Inventory without editing. In `pages/hosen_status/page.py`, confirm `_hide_visible_spinner` expects a visible `[class*='spinner']` or `[aria-busy='true']` to be hidden, `_select_smart_filter` and `_select_date_combobox` default their settle to `_screen_1_settle`, `select_screen_1_filter` does not pass `settle`, `section_anchor_visible` returns `False` for an unknown section, and `_mark_visual_host` marks `vcGroupBody` with width at least 200 and height at least 120 (it does not mark `visualHeaderAbove`). In `data/hosen/db_sanity.yaml`, confirm `hosen_dashboard.screen_3_geographic_investigation` has `title`, `date_range.start`, `date_range.end`, `filters` (`level_selected`, `district`, `subdistrict`, `authority: null`), `graphs.final_resilience_score` (`title`, `legend`, `data` of `date` and `score`), and `graphs.categories` (each `title` and `data` of `date` and `score`). Confirm `hosen_dashboard.screen_4_excel_export` has `title`, `date`, `filters` (`sector: null`, `district`, `subdistrict`, `authority: null`), and `data_table` rows keyed by `authority` with percent strings such as `75.0%`. In `core/components/virtual_grid.py`, confirm `collect_virtualized_rows` starts at `scrollTop` 0, advances `scrollTop` by about one client height, and breaks when that assignment does not change `scrollTop` or when `sweep_horizontal()` returns 0. In `core/components/visual_table.py`, confirm `VisualTable.read_rows` right-clicks its container, clicks `הצג כטבלה`, calls `collect_virtualized_rows`, and leaves the table before returning.

**Checkpoint**: The golden blocks, the graph-body climb, and the current scroll stop are known. No files changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Keep walking a virtualized grid while `scrollTop` can still increase, and give Screens 3 and 4 their own settles without moving Screen 1 or Screen 2.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] In `core/components/virtual_grid.py`, change only the stop rule of `collect_virtualized_rows`. Keep the signature `(grid, read_visible, row_id, *, timeout_ms)`. Still start with `_scroll(grid, "top")` and still dedupe by `row_id`, including filling a blank cell from a later viewport. In the page-down step, read `scrollTop` back after the assignment. If the largest overflow node did not move, try the other overflow nodes in that same family, the way `_SCROLL_JS` mode `x` already tries more than one node. If no node's `scrollTop` changed, stop. If `scrollTop` increased, store the painted rows and continue even when `sweep_horizontal()` added no new id. Also stop when `timeout_ms` elapses. Do not add a Hosen date, an authority name, a Hebrew string, or a new public function. Do not edit `core/components/visual_table.py`. `VisualTable._collect_rows` stays a call to `collect_virtualized_rows`.
- [X] T004 [P] In `pages/hosen_status/page.py`, add `_screen_3_title` and `_screen_4_title` (each initially `""`), `_screen_3_anchor`, `_screen_4_anchor`, `_screen_3_settle`, `_screen_4_settle`, `wait_for_screen_3_idle`, and `wait_for_screen_4_idle`. Each anchor is `self._report_frame().get_by_text(stored_title, exact=False)` and is used only after that title is stored. Each settle `(self, kind="after_select", **_kwargs)` calls the existing `_hide_visible_spinner`, then `expect` that anchor visible within `self.timeout`, and returns `False`. Each wait method calls its settle. Do not edit `_screen_2_settle`, `_wait_for_screen_1_settled`, `_report_ready_locator`, or the default `settle or self._screen_1_settle`. Do not add `sleep`, `wait_for_timeout`, or `networkidle`. Comments inside the new methods stay English.

**Checkpoint**: `collect_virtualized_rows` still returns the rows Screen 1 and Screen 2 already match, and it no longer stops solely because one viewport repeated known ids while `scrollTop` moved. Screen 3 and Screen 4 have settles that expect a stored title. `select_screen_1_filter` still settles on Screen 1.

---

## Phase 3: User Story 1 - Geographic screen matches the golden YAML (Priority: P1) 🎯 MVP

**Goal**: Open the geographic screen, apply `date_range.start` then `date_range.end`, then each non-null filter in YAML order, and compare `title`, `date_range`, and `filters`.

**Independent Test**: `test_hosen_screen3_matches_golden` in `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` for `title`, `date_range`, and `filters` under `hosen_dashboard.screen_3_geographic_investigation`.

### Implementation for User Story 1

- [X] T005 [US1] Add `open_geographic_screen(self, title: str)` to `pages/hosen_status/page.py`. Store `title` on `_screen_3_title`. Reuse `_navigation_scopes` and `_click_named_control`. Candidate labels are the full title and, when `title` contains ` - `, the segment after the last separator. Treat `"` and `״` (U+05F4) as the same character when matching the control and when expecting the heading. Expect the full title (either quote spelling) to be visible, then call `_screen_3_settle`. Do not edit `open_investigation_screen`. Do not change `navigate` or `_report_ready_locator`. Do not hard-code a date or a percent. The test will pass the YAML title `תמ״צ התנהגות - תחקור גיאוגרפי`.
- [X] T006 [US1] Add `select_screen_3_date_range(self, start: str, end: str)` to `pages/hosen_status/page.py`. Apply `start`, then `end`, each through the existing `_select_date_combobox` with `settle=self._screen_3_settle`. When two date comboboxes are visible, visual order (top, then left) is start, then end. Put the live accessible names of those controls in page constants. Do not call `select_screen_2_filter`. Do not import a date-range method from `pages/alerts_analysis/` or `pages/public_inquiries/`. The existing check that raises `AssertionError` when the combobox text does not contain the value stays. Do not call `page.wait_for_timeout`.
- [X] T007 [US1] Add `select_screen_3_filter(self, slicer_id: str, value: str)` to `pages/hosen_status/page.py`. For `level_selected`, `district`, `subdistrict`, and `authority`, call `_select_smart_filter(role_names, value, settle=self._screen_3_settle)` and raise `KeyError` naming the id when that returns false. Keep the placeholder hints in a Screen 3 tuple. Do not append those ids to `_FILTER_ROLES` and do not change `_smart_filter_label`. `level_selected` (`מחוז`) must be typed into the level control, not the district control that holds `מחוז דרום`. Any other id raises `KeyError`. Do not call `_select_unnamed_combobox`. The caller will not pass a `null` value.
- [X] T008 [US1] Add `screen_3_section_visible(self, section: str) -> bool` and a first `read_screen_3_metrics(self) -> dict` to `pages/hosen_status/page.py`. Do not add a `title` branch to `section_anchor_visible`. `"title"` is true when the stored geographic title is visible. `"date_range"` is true when both date controls from T006 are visible. `"filters"` is true when a `ul.TokensContainer` or a combobox is visible. `"final_resilience_score"` and `"categories"` return `False` in this task. Any other section returns `False`. `read_screen_3_metrics` returns `title` (visible heading, bidi marks removed), `date_range` with `start` and `end` from the two date controls, `filters` for `level_selected`, `district`, `subdistrict`, and `authority` (the chip for that id's own placeholder, or `""` when the box still shows the placeholder), and `graphs` with `final_resilience_score: {"title": "", "legend": "", "data": []}` and `categories: []`. Read filters with a Screen 3 reader. Do not call `_smart_filter_label`. Do not embed golden percents.
- [X] T009 [US1] Create `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py`. Load `data/hosen/db_sanity.yaml` with `yaml.safe_load` and return `["hosen_dashboard"]` from `load_sanity_data`. Marker `@pytest.mark.sanity` on `test_hosen_screen3_matches_golden(hosen_status_dashboard)`. The body calls `open_geographic_screen(str(expected["title"]))`, then `select_screen_3_date_range(str(date_range["start"]), str(date_range["end"]))`, then for each `filters` item in YAML order calls `select_screen_3_filter` only when `value is not None` (do not pass `str(None)`), then `wait_for_screen_3_idle()`, then `read_screen_3_metrics()`. Private helpers in this file, not imported from `test_screen1_sanity.py` or `test_screen2_sanity.py`: bidi trim, a string compare that does not parse percents (`"88%"` does not match `"88"` or `"0.88"`), and a title compare that treats `"` and `״` as equal. Compare `title`, `date_range` (`start`, `end`), and `filters`. A YAML `null` requires the reading to be `""` and fails when the chip is `"0%"`. Every listed filter id is checked. Extra slicers are ignored. A visible anchor and an empty reader raise `AssertionError` whose message starts with `hosen_dashboard.screen_3_geographic_investigation`. A missing anchor skips that block. If every compared block is skipped, `pytest.skip` names the skipped sections. The test body has no locators. Do not compare `graphs` yet. Do not edit `conftest.py`.

**Checkpoint**: The test opens Screen 3, applies the golden range and the non-null filters, and checks `title`, `date_range`, and `filters`. `authority: null` is not typed into a control. Chart blocks are still empty and are not asserted yet.

---

## Phase 4: User Story 2 - Geographic charts read as tables (Priority: P1)

**Goal**: Read the final resilience chart and each category chart with the existing `VisualTable` reader. Match each golden `date`. Extra dates do not fail. A missing golden date does.

**Independent Test**: `graphs.final_resilience_score` and `graphs.categories` inside `test_hosen_screen3_matches_golden`. The right-click target is the `vcGroupBody` from `_mark_visual_host`, and the read does not raise `'<name>' has no show-as-table menu item`.

### Implementation for User Story 2

- [X] T010 [US2] In `pages/hosen_status/page.py`, add a chart reader that takes a visible title locator. Call the existing `_mark_visual_host(node, attr)` and pass that locator to `VisualTable(self.page, self._report_frame(), timeout_ms=self.timeout).read_rows(host, name=...)`. Do not edit `_mark_visual_host` and do not pass the title text node or a `visualHeaderAbove` node. Before `read_rows`, take the legend string from the marked host's text (the final-score legend lives inside the chart, not in the district chip). Clear the mark in a `finally`, including when `read_rows` raises. When `_mark_visual_host` returns `None`, return no rows. Do not call `rows_to_label_values`. Do not reimplement the right-click or the `הצג כטבלה` menu. Map each header→cell dict on the page. The cell matching `DD/MM/YYYY` is `date` (the first such cell). The percent cell is `_percent_token` of that cell, so `85%` stays `85%` and a decimal such as `75.0%` stays `75.0%`. A cell with no percent is `""`. Do not embed golden dates or scores.
- [X] T011 [US2] In `read_screen_3_metrics` in `pages/hosen_status/page.py`, publish `graphs.final_resilience_score` as `title`, `legend`, and `data` (`date`, `score`), and `graphs.categories` as a list of `title` plus `data`. Discover chart titles that are visible in the report iframe. Do not hard-code the eight category titles or the final-score title. Read one chart, let `VisualTable` return to the report, then read the next. `screen_3_section_visible("final_resilience_score")` is true when that chart title is visible. `screen_3_section_visible("categories")` is true when at least one category chart title is visible. Do not call the chart reader when its title is absent.
- [X] T012 [US2] In `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py`, compare `graphs.final_resilience_score` and `graphs.categories`. Failure paths start with `hosen_dashboard.screen_3_geographic_investigation`. Chart rows match on `date`. Category charts match on `title`. Extra dates and extra charts are ignored. A missing golden `date` or a missing golden category `title` fails when that block's anchor is visible. `score` matches as display text: `"88%"` does not match `"88"` or `"0.88"`. YAML `null` (`None` from `yaml.safe_load`) requires the cell to be `""` and fails when the cell is `"0%"`. `legend` matches the string inside the final-score chart. A visible anchor and an empty `data` list fail when the golden list is non-empty. A missing anchor skips only that block. If every Screen 3 block is skipped, `pytest.skip`. Do not call `VisualTable` from the test.

**Checkpoint**: A golden date that never appears fails. An extra date does not. The chart read right-clicks `vcGroupBody` and finds `הצג כטבלה`. A later date that sits below the first viewport is present because `collect_virtualized_rows` kept moving `scrollTop`.

---

## Phase 5: User Story 3 - Excel export screen matches the golden table (Priority: P1)

**Goal**: Open the export screen, apply `date` then each non-null filter, and match `data_table` by `authority`. The check is the on-screen grid. No workbook is downloaded.

**Independent Test**: `test_hosen_screen4_matches_golden` in `tests/sanity/hosen_status_dashboard/test_screen4_sanity.py` against `hosen_dashboard.screen_4_excel_export`.

### Implementation for User Story 3

- [X] T013 [US3] Add `open_excel_export_screen(self, title: str)` to `pages/hosen_status/page.py`. Store `title` on `_screen_4_title`. Use the same candidate-label, quote-fold, and `_click_named_control` rules as `open_geographic_screen`. Expect the full title, then call `_screen_4_settle`. Do not edit `open_geographic_screen` or `open_investigation_screen`. The test will pass the YAML title `תמ״צ התנהגות - ייצוא נתונים לאקסל`.
- [X] T014 [US3] Add `select_screen_4_filter(self, slicer_id: str, value: str)` to `pages/hosen_status/page.py`. For `date`, resolve the combobox and call `_select_date_combobox(control, value, settle=self._screen_4_settle)`. For `sector`, `district`, `subdistrict`, and `authority`, call `_select_smart_filter` with `settle=self._screen_4_settle` and a Screen 4 placeholder tuple that is not `_FILTER_ROLES`. Raise `KeyError` for an unknown id or a missing control. Do not call `_select_unnamed_combobox`. The caller will not pass a `null` value. Do not edit `select_screen_3_filter`.
- [X] T015 [US3] Add `screen_4_section_visible(self, section: str) -> bool` and `read_screen_4_metrics(self) -> dict` to `pages/hosen_status/page.py`. `"title"` is the stored export title. `"date"` is the date combobox. `"filters"` is a smart-filter shell or a combobox. `"data_table"` is a visible column header containing `רשות`. Any other section returns `False`. The reader returns `title`, `date` (selected combobox label), `filters` for `sector`, `district`, `subdistrict`, and `authority` (`""` when that chip is empty), and `data_table`. Collect `data_table` with `collect_virtualized_rows` on the grid that owns the `רשות` header. Do not call `VisualTable` for this grid and do not start a download. `authority` is `_plain(cell.split("\n")[0])`. Map metric columns with a new Screen 4 header tuple to `care_for_welfare`, `effective_behavior`, `information_and_communication`, `community_resources`, `leadership`, `narrative`, `final_score`, `functional_continuity`, and `belonging_and_solidarity`. Copy a live header spelling that differs into that tuple only. Do not change `_SCREEN2_HEADERS` or `_field_for_header`. Metric cells go through `_percent_token`, so `75.0%` stays `75.0%` and a cell with no percent is `""`.
- [X] T016 [US3] Create `tests/sanity/hosen_status_dashboard/test_screen4_sanity.py`. Load `hosen_dashboard.screen_4_excel_export` the same way Screen 3 loads its block. Marker `@pytest.mark.sanity` on `test_hosen_screen4_matches_golden(hosen_status_dashboard)`. The body calls `open_excel_export_screen(str(expected["title"]))`, then `select_screen_4_filter("date", str(report_date))` when `date` is present, then `select_screen_4_filter` for each `filters` item in YAML order only when `value is not None`, then `wait_for_screen_4_idle()`, then `read_screen_4_metrics()`. Private compare helpers stay in this file. Do not import the Screen 1, Screen 2, or Screen 3 test module. Compare `title`, `date`, `filters`, and `data_table`. Failure paths start with `hosen_dashboard.screen_4_excel_export`. Rows match on `authority`. Treat `"` and `״` as the same character for the title and for authority names such as `בני עי"ש`. Extra authority rows are ignored. A missing golden `authority` fails. Each metric matches as display text: `"75.0%"` does not match `"75%"`, `"75.0"`, or `"0.75"`. YAML `null` requires `""` and fails on `"0%"`. A visible anchor and an empty `data_table` fail when the golden list is non-empty. A missing anchor skips that block. If every block is skipped, `pytest.skip`. The test body has no locators and does not assert a downloaded file.

**Checkpoint**: Each golden authority matches, including one-decimal percents. An extra authority does not fail. `sector: null` and `authority: null` are not typed into a control. No `.xlsx` download is started.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Catalog the new keys and prove Screens 1 and 2, plus fleet, still pass

- [X] T017 [P] Update section 11 of `docs/COVERAGE_CATALOG.md`. Keep the Screen 1 and Screen 2 rows. Add rows for `screen_3_geographic_investigation.title`, `date_range`, `filters`, `graphs.final_resilience_score`, and `graphs.categories`, naming `open_geographic_screen`, `select_screen_3_date_range`, `select_screen_3_filter`, `read_screen_3_metrics` (`VisualTable.read_rows` on `vcGroupBody` from `_mark_visual_host`), and `test_hosen_screen3_matches_golden`. Add rows for `screen_4_excel_export.title`, `date`, `filters`, and `data_table`, naming `open_excel_export_screen`, `select_screen_4_filter`, `read_screen_4_metrics` (`collect_virtualized_rows`), and `test_hosen_screen4_matches_golden`. State that the source is `data/hosen/db_sanity.yaml`, not SQL, and that Screen 4 does not download a workbook.
- [X] T018 Run `pytest tests/sanity/hosen_status_dashboard/test_screen3_sanity.py -m sanity` from the repo root. A mismatch must name `hosen_dashboard.screen_3_geographic_investigation`. A visible anchor with an empty reader fails. A `null` chip or cell that shows `0%` fails. A missing golden `date` fails. An extra date does not. The run must not raise a `has no show-as-table menu item` error. The run must not skip every block when the geographic title is on screen.
- [X] T019 Run `pytest tests/sanity/hosen_status_dashboard/test_screen4_sanity.py -m sanity` from the repo root. A mismatch must name `hosen_dashboard.screen_4_excel_export`. A missing golden `authority` fails. An extra authority does not. `"75.0%"` matches only that display text. The run must not download a workbook and must not skip every block when the export title is on screen.
- [X] T020 Run `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py -m sanity` and `pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py -m sanity` from the repo root. Both must still pass. `test_hosen_screen1_matches_golden` still applies Screen 1 filters through `select_screen_1_filter` and reads `read_screen_1_metrics`. `test_hosen_screen2_matches_golden` still opens the investigation screen and reads `read_screen_2_metrics`.
- [X] T021 Run `pytest tests/ui/fleet_dashboard/` from the repo root. It must pass at 100% because `core/components/virtual_grid.py` changed. This gates completion.
- [X] T022 Confirm the diff does not edit `core/portal/`, `core/components/visual_table.py`, `core/components/slicer.py`, `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, those reports' page and test modules, `db/`, `tests/helpers/`, `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`, `tests/sanity/hosen_status_dashboard/conftest.py`, `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`, `specs/050-hosen-screen1-sanity/`, or `specs/051-hosen-screen2-sanity/`. `select_screen_1_filter` still does not pass `settle`. `_mark_visual_host` still marks `vcGroupBody` and does not mark `visualHeaderAbove`. The only `core/` edit is the `scrollTop` stop in `core/components/virtual_grid.py`, and that file contains no Hebrew and no Hosen date. New comments inside functions are English. `pages/hosen_status/page.py`, `test_screen3_sanity.py`, and `test_screen4_sanity.py` contain no `sleep`, `wait_for_timeout`, or `networkidle`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Story 1 (Phase 3)**: Depends on T004. Opens the geographic screen and checks `title`, `date_range`, and `filters`.
- **User Story 2 (Phase 4)**: Depends on T009 and T003. The chart reader runs after the geographic screen is open and the filters are applied, and it needs the `scrollTop` continuation.
- **User Story 3 (Phase 5)**: Depends on T004 and T003. It does not depend on the chart reader. It edits `pages/hosen_status/page.py` after US2 so two editors do not share that file.
- **Polish (Phase 6)**: T018 needs T012. T019 needs T016. T020 needs T004 and the page edits that must leave Screen 1 and Screen 2 methods unchanged. T021 needs T003. T017 can run once the method names in T005–T015 exist. T022 runs last.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T004. No dependency on US2 or US3. This is the MVP.
- **User Story 2 (P1)**: Starts after T009. Uses `open_geographic_screen`, `select_screen_3_date_range`, `select_screen_3_filter`, and `read_screen_3_metrics` from US1, and `collect_virtualized_rows` from T003. Independently checked by the two graph blocks.
- **User Story 3 (P1)**: Starts after T004 and T003. Does not call Screen 3 methods. Independently checked by `test_hosen_screen4_matches_golden`. Sequence it after US2 only because both stories edit `pages/hosen_status/page.py`.

### Within Each User Story

- T002 before T003 and T004 (know the current scroll stop and the spinner helper before editing them).
- T005 before T006. T006 before T007. T007 before T008. T008 before T009.
- T010 before T011. T011 before T012.
- T013 before T014. T014 before T015. T015 before T016.
- T012 before T018. T016 before T019. T020 and T021 before T022.

### Parallel Opportunities

- T001 and T002 can run together (read-only).
- T003 (`core/components/virtual_grid.py`) and T004 (`pages/hosen_status/page.py`) can run together.
- T017 edits `docs/COVERAGE_CATALOG.md` and can run beside T018 once the method names exist. Do not edit `pages/hosen_status/page.py` in parallel with T004–T015.
- T018, T019, T020, and T021 share one portal or one pytest session. Run them one after another.

---

## Parallel Example: User Story 1

```bash
# Foundational pair, different files, before US1:
Task: "T003 scrollTop continuation in core/components/virtual_grid.py"
Task: "T004 Screen 3 and Screen 4 settles in pages/hosen_status/page.py"

# US1 is one file, in order:
Task: "T005 open_geographic_screen in pages/hosen_status/page.py"
Task: "T009 compare title, date_range, and filters in tests/sanity/hosen_status_dashboard/test_screen3_sanity.py"
```

---

## Parallel Example: User Story 3

```bash
# After T004 and T003. Same page file, in order:
Task: "T013 open_excel_export_screen in pages/hosen_status/page.py"
Task: "T015 read_screen_4_metrics in pages/hosen_status/page.py"

# Different file, after the reader publishes rows:
Task: "T016 compare data_table in tests/sanity/hosen_status_dashboard/test_screen4_sanity.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1: Setup.
2. Complete Phase 2: `scrollTop` continuation and Screen 3 / Screen 4 settles.
3. Complete Phase 3: open the geographic screen, apply `date_range` then non-null `filters`, compare `title`, `date_range`, and `filters`.
4. **STOP and VALIDATE**: `pytest tests/sanity/hosen_status_dashboard/test_screen3_sanity.py -m sanity` against those three blocks, then `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py -m sanity`.

### Incremental Delivery

1. Setup + Foundational → Screen 1 still settles on its ready locator, and a virtualized grid keeps scrolling while `scrollTop` increases.
2. User Story 1 → the geographic title, the two dates, and the filter chips match the YAML. `authority: null` is an empty chip.
3. User Story 2 → each golden chart `date` matches. Extra dates are ignored. The right-click hits `vcGroupBody`.
4. User Story 3 → each golden `authority` matches, including `75.0%`. No workbook is downloaded.
5. Polish → coverage catalog, both new sanity modules, Screen 1 and Screen 2 sanity, fleet smoke, diff check.

### Parallel Team Strategy

One developer owns `pages/hosen_status/page.py` from T004 through T015. A second developer can take T003 (`core/components/virtual_grid.py`) during Phase 2 and, after T015, T017 (`docs/COVERAGE_CATALOG.md`). Do not split the page file across two editors. `test_screen3_sanity.py` stays with T009 then T012. `test_screen4_sanity.py` is T016 only.

---

## Notes

- [P] tasks = different files, no dependencies on an unfinished edit.
- [US1]–[US3] map to spec.md. Setup, Foundational, and Polish have no story label.
- The golden numbers stay in `data/hosen/db_sanity.yaml`. The page returns display text. The test owns the `null` means empty rule. `"0%"` is not empty. `"88%"` is not `88` or `0.88`. `"75.0%"` is not `"75%"`.
- Extra UI rows do not fail. A missing golden `date` or `authority` does.
- A visible anchor with an empty reader fails when the golden block has data. A missing anchor skips that block. Every block on that screen skipped calls `pytest.skip`.
- Chart row identity is `date`. Export row identity is `authority`.
- The chart right-click target is the existing `_mark_visual_host` result (`vcGroupBody`). Do not right-click `visualHeaderAbove`.
- Commit after each task or logical group.
- Stop at the US1 checkpoint and run the Screen 3 test before adding the charts.
- Avoid: editing `core/portal` or `visual_table.py`, rewriting the YAML, calling `select_screen_1_filter` from the new tests, adding a `title` branch to `section_anchor_visible`, parsing percents to floats, using `rows_to_label_values` for a chart, copying `_SCROLL_JS` onto the page, and downloading an Excel file.
