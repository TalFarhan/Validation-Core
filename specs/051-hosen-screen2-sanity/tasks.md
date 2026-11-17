---
description: "Task list for Hosen Status Screen 2 YAML sanity"
---

# Tasks: Hosen Status Screen 2 YAML Sanity

**Input**: Design documents from `/specs/051-hosen-screen2-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/hosen-screen2-sanity.md, quickstart.md

**Tests**: The spec requires `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` (`test_hosen_screen2_matches_golden`, marker `sanity`). That file is the deliverable, written in the user-story phases. Pytest runs in Polish. Screen 1 sanity must still pass. Hosen smoke stays `dashboard.verify_freshness()` and is not edited. Fleet smoke is not a gate: `core/` is not edited.

**Organization**: Three P1 stories. US1 opens the investigation screen, applies `date` then `filters`, and compares `title`, `date`, and `filters`. US2 reads the authority grid and the summary row. US3 reads the trends chart with `VisualTable` after `_mark_visual_host` marks the nearest `visualContainer`. All three stories edit `pages/hosen_status/page.py` in order. The test file grows in the same order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US3 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page: `pages/hosen_status/page.py` (`HosenStatusPage`)
- Golden record (do not edit): `data/hosen/db_sanity.yaml` (`hosen_dashboard.screen_2_investigation`)
- New sanity test: `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`
- Existing fixture (do not edit): `tests/sanity/hosen_status_dashboard/conftest.py` (`hosen_status_dashboard`)
- Existing Screen 1 test (do not change behavior): `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
- Existing smoke (do not edit): `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`
- Catalog: `docs/COVERAGE_CATALOG.md` section 11
- Contract: `specs/051-hosen-screen2-sanity/contracts/hosen-screen2-sanity.md`
- OFF-LIMITS: `core/portal/`, `core/components/` (including `slicer.py`, `visual_table.py`, `chart.py`, `virtual_grid.py`), `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, those reports' pages and tests, `tests/helpers/`, `db/`, root `conftest.py`, `specs/050-hosen-screen1-sanity/`

Do not add `pages/hosen_status/__init__.py`. Comments inside functions stay English. Hebrew stays in locator constants or the YAML. Do not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`. Do not import Hasbara, Credit, Alerts, or `test_screen1_sanity`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Pin this slice and record the Screen 1 paths that must keep working

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/051-hosen-screen2-sanity"` and the git checkout stays `feature/reportportal-integration`. Do not edit `specs/050-hosen-screen1-sanity/`, `data/hosen/db_sanity.yaml`, `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`, or `core/`.
- [X] T002 [P] Inventory without editing. In `pages/hosen_status/page.py`, confirm `_wait_for_screen_1_settled` expects a visible `[class*='spinner']` or `[aria-busy='true']` to be hidden, then expects `_report_ready_locator()` (`תמ"צ ארצי - דיווחי קה"א יקל"ר`). Confirm `_select_smart_filter` and `_select_date_combobox` call `_screen_1_settle("after_select")`, and `_select_slicer_date` passes `settle=self._screen_1_settle`. Confirm `section_anchor_visible` returns `False` for an unknown section. Confirm `_mark_visual_host` walks parents with `className` containing `visual` and returns on the first hit. In `data/hosen/db_sanity.yaml`, confirm `hosen_dashboard.screen_2_investigation` has `title` `תמ״צ התנהגות - מסך תחקור`, `date`, `filters` (`district` then `subdistrict`), and `tables.authorities_breakdown_table`, `tables.totals_row`, `tables.trends_by_date_table` (including a `null` metric). In `core/components/visual_table.py`, confirm `VisualTable.read_rows` right-clicks its container and clicks `הצג כטבלה`, and raises `AssertionError` naming the visual when that menu item is absent.

**Checkpoint**: The golden block, the Screen 1 settle sites, and the current visual-host walk are known. No files changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Let Screen 2 reuse the date and smart-filter clicks while Screen 1 still settles on its own ready text.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 In `pages/hosen_status/page.py`, extract the spinner wait from `_wait_for_screen_1_settled` into `_hide_visible_spinner`. The locator stays `frame.locator("[class*='spinner'], [aria-busy='true']").filter(visible=True)`. When `count() > 0`, `expect(spinner.first).to_be_hidden(timeout=self.timeout)` inside the existing `try/except`. A count of zero is not a failure. `_wait_for_screen_1_settled` calls `_hide_visible_spinner` and then `expect(self._report_ready_locator()).to_be_visible(timeout=self.timeout)`. Do not change `_report_ready_locator`. Do not add `sleep`, `wait_for_timeout`, or `networkidle`.
- [X] T004 In `pages/hosen_status/page.py`, add an optional `settle=None` parameter to `_select_smart_filter`, `_select_date_combobox`, and `_select_slicer_date`. The hook is `settle or self._screen_1_settle`. `_select_smart_filter` calls `hook("after_select")` where it currently calls `_screen_1_settle("after_select")`. `_select_date_combobox` passes that hook into `_select_slicer_date` and calls `hook("after_select")` where it currently calls `_screen_1_settle`. `_select_slicer_date` passes the hook as `Slicer(..., settle=hook)`. `select_screen_1_filter` does not pass `settle`. Do not edit `core/components/slicer.py`. After the date hook, the existing check that raises `AssertionError` when the combobox text does not contain `value` stays.
- [X] T005 In `pages/hosen_status/page.py`, add `_screen_2_title` (initially `""`), `_screen_2_anchor`, `_screen_2_settle`, and `wait_for_screen_2_idle`. `_screen_2_anchor` is `self._report_frame().get_by_text(self._screen_2_title, exact=False)` and is only used after a title is stored. `_screen_2_settle(self, kind="after_select", **_kwargs)` calls `_hide_visible_spinner`, then `expect` the anchor visible within `self.timeout`, and returns `False`. `wait_for_screen_2_idle` calls `_screen_2_settle`. Do not point `_report_ready_locator` at Screen 2. Comments inside the new methods stay English.

**Checkpoint**: `select_screen_1_filter("date", value)` and `select_screen_1_filter("district", value)` still settle on the Screen 1 ready locator. Screen 2 has a settle that expects a stored title.

---

## Phase 3: User Story 1 - Investigation screen matches the golden YAML (Priority: P1) 🎯 MVP

**Goal**: Open the investigation screen, apply `screen_2_investigation.date` then `filters` in YAML order, and compare `title`, `date`, and `filters`.

**Independent Test**: `test_hosen_screen2_matches_golden` in `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` for `title`, `date`, and `filters`.

### Implementation for User Story 1

- [X] T006 [US1] Add `open_investigation_screen(self, title: str)` to `pages/hosen_status/page.py`. Store `title` on `_screen_2_title`. Candidate labels are the full title and, when `title` contains ` - `, the segment after the last separator. Treat `"` and `״` (U+05F4) as the same character when matching. Click the first visible `button`, `tab`, `link`, or `option` in the report iframe whose accessible name equals a candidate. Search a visible group named `ניווט בין עמודים` or `Page navigation` first, then the iframe. Expect the full title (either quote spelling) to be visible, then call `_screen_2_settle`. Do not hard-code `08/06/2026` or a percent. Do not change `navigate` or `_report_ready_locator`. The test will pass `תמ״צ התנהגות - מסך תחקור` from the YAML.
- [X] T007 [US1] Add `select_screen_2_filter(self, slicer_id: str, value: str)` to `pages/hosen_status/page.py`. Resolve role names with `_filter_role_names`. For `district` and `subdistrict`, call `_select_smart_filter(role_names, value, settle=self._screen_2_settle)` and raise `KeyError` naming the id and the role names when that returns false. For `date`, resolve the combobox with `_filter_control` and call `_select_date_combobox(control, value, settle=self._screen_2_settle)`. Raise `KeyError` when the date control is missing. Any other id raises `KeyError`. Do not call `_select_unnamed_combobox`. Do not call `page.wait_for_timeout`.
- [X] T008 [US1] Add `screen_2_section_visible(self, section: str) -> bool` and `read_screen_2_metrics(self) -> dict` to `pages/hosen_status/page.py`. Do not add a `title` branch to `section_anchor_visible`. `screen_2_section_visible("title")` is true when the stored investigation title is visible. `"date"` is true when `_filter_control("date", self._filter_role_names("date"))` is visible. `"filters"` is true when a `ul.TokensContainer` or a combobox is visible. Any other section returns `False` in this task. `read_screen_2_metrics` returns `title` (visible heading text, bidi marks removed), `date` from `_read_screen_1_date`, `filters` from `_read_active_filters`, and `tables` with `authorities_breakdown_table: []`, `totals_row: {}`, and `trends_by_date_table: []`. Call it only after the screen is idle. Do not embed golden percents.
- [X] T009 [US1] Create `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`. Load `data/hosen/db_sanity.yaml` with `yaml.safe_load` and return `["hosen_dashboard"]` from `load_sanity_data`. Marker `@pytest.mark.sanity` on `test_hosen_screen2_matches_golden(hosen_status_dashboard)`. The body calls `open_investigation_screen(str(expected["title"]))`, then `select_screen_2_filter("date", str(report_date))` when `date` is present, then `select_screen_2_filter(str(slicer_id), str(value))` for each `filters` item in YAML order, then `wait_for_screen_2_idle()`, then `read_screen_2_metrics()`. Private helpers in this file: `_plain` (bidi marks and outer strip), string compare that does not parse percents, and a title compare that also treats `"` and `״` as equal. Compare blocks `title`, `date`, and `filters`. Every listed filter id must match. Extra slicers are ignored. A visible anchor and an empty reader raise `AssertionError` whose message starts with `hosen_dashboard.screen_2_investigation`. A missing anchor skips that block. If every compared block is skipped, `pytest.skip` names the skipped sections. The test body has no locators. Do not import `tests.sanity.hosen_status_dashboard.test_screen1_sanity` or any Hasbara, Credit, or Alerts module. Do not edit `conftest.py`.

**Checkpoint**: The test opens Screen 2, applies the golden date and filters, and checks `title`, `date`, and `filters`. Table blocks are still empty and are not asserted yet.

---

## Phase 4: User Story 2 - Authority breakdown and the average row (Priority: P1)

**Goal**: Match each golden authority and the summary/average row. Extra authority rows are ignored. Percent strings stay display text.

**Independent Test**: `tables.authorities_breakdown_table` and `tables.totals_row` inside `test_hosen_screen2_matches_golden`.

### Implementation for User Story 2

- [X] T010 [US2] In `pages/hosen_status/page.py`, add a header map from Hebrew column titles to the YAML fields `authority` (`רשות`), `leadership` (`מנהיגות`), `welfare` (`דאגה לרווחה`), `effective_behavior` (`התנהגות אפקטיבית`), `belonging` (`שייכות וסולידריות`), `functional_continuity` (`רציפות תפקודית`), `narrative` (`נרטיב`), `community_resources` (`מיצוי משאבי קהילה`), `information` (`מידע ותקשורת`), and `resilience_score` (`ציון חוסן`). If a live header spelling differs, update the page constant only. Add a visible-row reader for the grid whose column header contains `רשות`. `authority` is `_plain(extracted_text.split("\n")[0])`. A metric cell is the compact percent token (`88%`, internal spaces removed) or `""` when the cell has no percent. Collect rows with `collect_virtualized_rows` from `core.components.virtual_grid`, `row_id` = `authority`. Do not edit `_visible_resilience_rows` or `core/components/virtual_grid.py`. Do not read pixels from a `canvas`.
- [X] T011 [US2] In `pages/hosen_status/page.py`, read `totals_row` from the summary row of that same grid. The label cell, quote-folded, is one of `ממוצע`, `ממוצע ארצי`, `סה"כ`, `סה״כ`, or `Total`. Publish the nine metric fields and do not include that row in `authorities_breakdown_table`. If the live grid has no such row, read the sibling visual that shows those nine percents and store its live accessible name as a page constant. `screen_2_section_visible("authorities_breakdown_table")` is true when the `רשות` header is visible. `screen_2_section_visible("totals_row")` is true when the summary label or that sibling visual is visible. Do not edit `data/hosen/db_sanity.yaml`.
- [X] T012 [US2] In `read_screen_2_metrics` in `pages/hosen_status/page.py`, set `tables.authorities_breakdown_table` and `tables.totals_row` from T010 and T011. In `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`, compare those two blocks. Authority rows match on `authority`. Extra UI rows are ignored. Each golden field (`leadership`, `welfare`, `effective_behavior`, `belonging`, `functional_continuity`, `narrative`, `community_resources`, `information`, `resilience_score`) matches as display text. A visible anchor and an empty list or empty totals dict fail when the golden node has data. Failure paths look like `hosen_dashboard.screen_2_investigation.tables.authorities_breakdown_table[authority=<name>].leadership` and `hosen_dashboard.screen_2_investigation.tables.totals_row.leadership`. Do not parse percents to floats.

**Checkpoint**: A golden authority that is missing fails. An extra authority on screen does not. The summary row is not indexed as an authority.

---

## Phase 5: User Story 3 - Trends chart read as a table (Priority: P1)

**Goal**: Right-click the trends `visualContainer`, read it with the existing `VisualTable` reader, and match each golden `creation_date`. A YAML `null` is an empty cell. Extra dates are ignored.

**Independent Test**: `tables.trends_by_date_table` inside `test_hosen_screen2_matches_golden`. The read completes without `AssertionError: 'trends_by_date' has no show-as-table menu item`.

### Implementation for User Story 3

- [X] T013 [US3] Replace `_mark_visual_host` in `pages/hosen_status/page.py`. The nearest `visualContainer` above `מגמות המרכיבים לפי תאריך` is a 38px header (`visualHeaderAbove`); right-clicking it has no show-as-table item. Mark the ancestor whose class contains `vcGroupBody` and whose box is at least 200 by 120, set the caller's attribute on that node, and return `self._report_frame().locator(f"[{attr}='active']").first`. Return `None` when that ancestor is missing. Do not mark the title text node. `_clear_mark` stays. `_read_totals_sibling` keeps calling this helper with `data-hosen-totals`. Do not edit `core/components/visual_table.py` or `core/components/chart.py`.
- [X] T014 [US3] In `pages/hosen_status/page.py`, read the Screen 2 trends chart with `VisualTable` from `core.components.visual_table`. Set `_TRENDS_VISUAL_TITLE` to `מגמות המרכיבים לפי תאריך`. `_trends_container` finds that visible title and returns `_mark_visual_host(node, "data-hosen-trend")`. Construct `VisualTable(self.page, self._report_frame(), timeout_ms=self.timeout)` and call `read_rows(container, name="trends_by_date")`. In a `finally`, call `_clear_mark(container, "data-hosen-trend")`. When `_trends_container` returns `None`, `_read_trends` returns `[]`. Do not call `rows_to_label_values`. Do not reimplement the right-click or the `הצג כטבלה` menu. Map each returned header→cell dict on the page. The cell matching `DD/MM/YYYY` is `creation_date` (the first such cell). Metric columns use the T010 Hebrew header map. A cell with no visible value is `""`. `screen_2_section_visible("trends_by_date_table")` is true when that title is visible. `read_screen_2_metrics` publishes the rows under `tables.trends_by_date_table` only when that section is visible.
- [X] T015 [US3] In `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`, compare `tables.trends_by_date_table`. Rows match on `creation_date`. Extra dates are ignored. A string field matches display text. YAML `null` (`None` from `yaml.safe_load`) requires `_plain(actual) == ""` and fails when the cell is `0%`. The failure path is `hosen_dashboard.screen_2_investigation.tables.trends_by_date_table[creation_date=<date>].<field>` and includes `golden=null` for a null. A visible trends anchor and an empty row list fail when the golden list is non-empty. Do not call the trends reader from the test. If this anchor and every other anchor are missing, `pytest.skip`.

**Checkpoint**: `13/06/2025` / `functional_continuity` passes only when that cell is empty. A golden date that never appears fails. An extra date does not. The trends read right-clicks the `visualContainer` and finds `הצג כטבלה`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Catalog the Screen 2 keys and run both Hosen sanity modules

- [X] T016 [P] Update section 11 of `docs/COVERAGE_CATALOG.md`. Keep the Screen 1 rows. Add rows for `screen_2_investigation.title` (`open_investigation_screen` / `read_screen_2_metrics`, `test_hosen_screen2_matches_golden`), `date` (`select_screen_2_filter("date", ...)` then `read_screen_2_metrics`), `filters` (`select_screen_2_filter` per id), `tables.authorities_breakdown_table` (`collect_virtualized_rows`), `tables.totals_row`, and `tables.trends_by_date_table` (`VisualTable.read_rows` on the `visualContainer` from `_mark_visual_host`). State that the source is `data/hosen/db_sanity.yaml`, not SQL.
- [ ] T017 Run `pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` from the repo root. A mismatch must name `hosen_dashboard.screen_2_investigation`. A visible anchor with an empty reader fails. A `null` cell that shows `0%` fails. The run must not raise `'trends_by_date' has no show-as-table menu item`. The run must not skip every block when the investigation title is on screen.
- [X] T018 Run `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` from the repo root. It must still pass. `test_hosen_screen1_matches_golden` still applies `screen_1_landing.date` and `filters`, calls `wait_for_screen_1_idle`, and reads `read_screen_1_metrics`.
- [ ] T019 Confirm the diff does not edit `core/`, `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, those reports' page and test modules, `db/`, `tests/helpers/`, `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, `tests/sanity/hosen_status_dashboard/conftest.py`, or `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`. `select_screen_1_filter` still does not pass `settle`. `_mark_visual_host` in `pages/hosen_status/page.py` uses `xpath=ancestor::div[contains(@class, 'visualContainer')][1]` and contains no `includes('visual')` walk. New comments inside functions are English. `pages/hosen_status/page.py` and `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` contain no `sleep`, `wait_for_timeout`, or `networkidle`. Fleet smoke is not required.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Story 1 (Phase 3)**: Depends on T005. Opens the screen and checks `title`, `date`, and `filters`.
- **User Story 2 (Phase 4)**: Depends on T009. The authority and totals readers run after the screen is open and the filters are applied.
- **User Story 3 (Phase 5)**: Depends on T009. The trends host (T013) is independent of the authority header map. The row mapper (T014) uses the T010 header map when metric columns use those Hebrew titles.
- **Polish (Phase 6)**: T017 needs T015. T018 can run once T004 has left Screen 1's settle as the default. T016 can run once the method names in T006–T014 exist. T019 runs last.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T005. No dependency on US2 or US3. This is the MVP.
- **User Story 2 (P1)**: Starts after T009. Uses `open_investigation_screen`, `select_screen_2_filter`, and `read_screen_2_metrics` from US1. Independently checked by the two table blocks.
- **User Story 3 (P1)**: Starts after T009 for the open/filter/read path. T013 can start as soon as `_mark_visual_host` exists. T014 uses the US2 header map for metric columns. Independently checked by `trends_by_date_table`.

### Within Each User Story

- T002 before T003 (know the spinner site and the golden keys before extracting the helper).
- T003 before T004. T004 before T005. T005 before T006.
- T006 before T007. T007 before T008. T008 before T009.
- T010 before T011. T011 before T012.
- T013 before T014. T014 before T015. T010 before T014 when the trends metric headers reuse that map.
- T015 before T017. T017 and T018 before T019.

### Parallel Opportunities

- T001 and T002 can run together (read-only, different files).
- T016 edits `docs/COVERAGE_CATALOG.md` and can run beside T017 once the method names exist. Do not edit `pages/hosen_status/page.py` in parallel with T003–T014.
- T017 and T018 are separate pytest modules. Run T018 after T004 so Screen 1's default settle is already in place. They share one portal, so run them one after the other.

---

## Parallel Example: User Story 3

```bash
# Same file, in order. T013 is the host fix. T014 consumes it.
Task: "T013 replace _mark_visual_host in pages/hosen_status/page.py"
Task: "T014 VisualTable.read_rows on that host in pages/hosen_status/page.py"

# Different file, after the reader publishes rows:
Task: "T015 compare trends_by_date_table in tests/sanity/hosen_status_dashboard/test_screen2_sanity.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1: Setup.
2. Complete Phase 2: spinner helper and optional settle defaulting to Screen 1.
3. Complete Phase 3: open the investigation screen, apply `date` then `filters`, compare `title`, `date`, and `filters`.
4. **STOP and VALIDATE**: `pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` against those three blocks, then `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`.

### Incremental Delivery

1. Setup + Foundational → Screen 1 still settles on `תמ"צ ארצי - דיווחי קה"א יקל"ר`.
2. User Story 1 → the investigation title, the selected date, and the two filters match the YAML.
3. User Story 2 → each golden authority and the summary row match. Extra authorities are ignored.
4. User Story 3 → `_mark_visual_host` marks `visualContainer`, each golden date matches, and the YAML `null` is an empty cell.
5. Polish → coverage catalog, both sanity pytest modules, diff check.

### Parallel Team Strategy

One developer owns `pages/hosen_status/page.py` for T003 through T014. A second developer can take T002 and, after T014, T016 (`docs/COVERAGE_CATALOG.md`). Do not split the page file across two editors. The test file stays with the same sequence: T009, then T012, then T015.

---

## Notes

- [P] tasks = different files, no dependencies on an unfinished edit.
- [US1]–[US3] map to spec.md. Setup, Foundational, and Polish have no story label.
- The golden numbers stay in `data/hosen/db_sanity.yaml`. The page returns display text. The test owns the `null` means empty rule.
- The trends right-click target is the nearest `div` whose class contains `visualContainer`. The title strip (`visualTitle`) is the node that opens a menu without `הצג כטבלה`.
- Commit after each task or logical group.
- Stop at the US1 checkpoint and run the Screen 2 test before adding the tables.
- Avoid: editing `core/`, rewriting the YAML, calling `select_screen_1_filter` from the Screen 2 test, adding a `title` branch to `section_anchor_visible`, parsing percents to floats, using `rows_to_label_values` for the trends chart, and marking the title text node when `visualContainer` is missing.
