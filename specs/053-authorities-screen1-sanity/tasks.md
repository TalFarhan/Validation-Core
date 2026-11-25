---
description: "Task list for Authorities Status Screen 1 YAML sanity"
---

# Tasks: Authorities Status Screen 1 YAML Sanity

**Input**: Design documents from `/specs/053-authorities-screen1-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/authorities-screen1-sanity.md, quickstart.md

**Tests**: The sanity test is the feature (spec.md User Story 1). Write it in this slice. Fleet smoke is not a gate: `core/portal` and `core/components` are not edited. Authorities smoke stays `dashboard.verify_freshness()` and is not edited.

**Organization**: Tasks follow user stories in spec.md. US1 is the Screen 1 reader and the golden walk. US2 keeps the smoke suite and Screen 2 untouched.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 or US2 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page: `pages/authorities_status/page.py` (`AuthoritiesStatusPage`)
- Golden record (do not edit): `data/reshuyot/db_sanity.yaml` (`dashboard.screen_1_national_status` only; leave `dashboard.screen_2_service_targets`)
- Sanity package: `tests/sanity/authorities_status_dashboard/`
- Existing smoke (do not edit): `tests/ui/authorities_status_dashboard/`
- Contract: `specs/053-authorities-screen1-sanity/contracts/authorities-screen1-sanity.md`
- OFF-LIMITS: `core/portal/`, `core/components/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `data/hosen/`, `data/reshuyot/db_sanity.yaml`, `tests/helpers/` (no new compare helper), `db/`, root `conftest.py`

Do not add `pages/authorities_status/__init__.py`. Comments inside functions stay English. Hebrew stays in locator constants on the page or in the YAML. Do not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`. Do not embed golden numbers, authority names, or filter values in the page or the test. Do not call `collect_virtualized_rows` from `_pick_open_date`. That helper stays only for a virtualized authority-name list inside the reader.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Pin this slice and record the files that already exist

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/053-authorities-screen1-sanity"`. Git checkout stays `feature/reportportal-integration`. Do not edit `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `tests/ui/authorities_status_dashboard/`, or `data/reshuyot/db_sanity.yaml`.
- [X] T002 [P] Create `tests/sanity/authorities_status_dashboard/__init__.py` as an empty package marker.
- [X] T003 [P] Inventory without editing. In `pages/authorities_status/page.py`, confirm `DASHBOARD_SEARCH_TERM` is `הערכת מצב רשויות` and `_report_ready_locator` uses that phrase. In `data/reshuyot/db_sanity.yaml`, confirm `dashboard.screen_1_national_status` has `title`, `date`, `filters.district` (string), `filters.sub_district` (list), `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report`, and that `dashboard.screen_2_service_targets` is a sibling block. In `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py`, confirm the body is `dashboard.verify_freshness()`. In `tests/sanity/hosen_status_dashboard/conftest.py` and `test_screen1_sanity.py`, read the `bind_dashboard` name and the private `_assert_tree` shape. Do not edit those Hosen files.

**Checkpoint**: The slice directory is pinned. No product code changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Idle wait and the sanity fixture that both stories rely on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 In `pages/authorities_status/page.py`, keep `DASHBOARD_SEARCH_TERM` and `_report_ready_locator` as they are. Add a page-level role table for slicer ids `date`, `district`, and `sub_district`. Copy each accessible name from the open הערכת מצב רשויות report. Do not copy filter values out of `data/reshuyot/db_sanity.yaml`. Do not copy `_select_smart_filter` or `_select_date_combobox` from `pages/hosen_status/page.py`. Add `wait_for_screen_1_idle()`: if the report iframe has a visible `[class*='spinner']` or `[aria-busy='true']` node, expect it hidden within `self.timeout`; then expect `_report_ready_locator()` visible. A spinner that is not showing is not a failure. Do not call `sleep`, `wait_for_timeout`, or `networkidle`. Do not add a Screen 2 method.
- [X] T005 [P] Create `tests/sanity/authorities_status_dashboard/conftest.py` with `authorities_status_dashboard = bind_dashboard(AuthoritiesStatusPage, "authorities_status_dashboard")`, importing `AuthoritiesStatusPage` from `pages.authorities_status.page` and `bind_dashboard` from `tests.helpers.dashboard_fixture`. Do not edit `tests/ui/authorities_status_dashboard/conftest.py`.

**Checkpoint**: The page can wait for Screen 1, and the sanity fixture name is `authorities_status_dashboard`. The smoke fixture name is still `dashboard`.

---

## Phase 3: User Story 1 - National status matches the golden YAML (Priority: P1) 🎯 MVP

**Goal**: Apply `dashboard.screen_1_national_status` date and filters, read Screen 1, and walk that block with a private compare. The date click is the page-local scroll loop in `_pick_open_date`.

**Independent Test**: `pytest tests/sanity/authorities_status_dashboard -m sanity` runs `test_authorities_screen1_matches_golden`.

### Tests for User Story 1

- [X] T006 [P] [US1] Create `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`. Mark `test_authorities_screen1_matches_golden` with `@pytest.mark.sanity` and the fixture `authorities_status_dashboard`. Load `data/reshuyot/db_sanity.yaml` with `yaml.safe_load` and take `["dashboard"]["screen_1_national_status"]` only. Do not read `screen_2_service_targets`. If `date` is present and non-empty, call `select_screen_1_filter("date", str(date))` then `wait_for_screen_1_idle()`. For each `filters` item in YAML order, select a string once, or each list item in order via `str(item)`. Never pass `str(list)` as the label. After every selection, and once more before the read, call `wait_for_screen_1_idle()`, then `read_screen_1_metrics()`. Walk every golden key with private helpers in this file (do not import `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` and do not add a helper under `tests/helpers/`). An int matches grouped or plain digits. A float matches the displayed number (`93.0` matches `93` or `93.0`; `86.9` stays `86.9`). A string matches display text after bidi marks `U+200E`, `U+200F`, `U+202A`–`U+202C` and outer whitespace are removed. A list of strings is membership. A list of objects matches on `name`, and `trend` is compared only when that golden row has `trend`. Extra UI rows do not fail. Skip a key when `section_anchor_visible` is false, including `title`. A visible anchor whose read is empty while the golden value has data fails, and the message includes the path `dashboard.screen_1_national_status...`. If every key is skipped, call `pytest.skip`. Do not embed golden numbers, authority names, or filter values.

### Implementation for User Story 1

- [X] T007 [US1] In `pages/authorities_status/page.py`, add `select_screen_1_filter(self, slicer_id: str, value: str)`. Resolve `slicer_id` from the role table added in T004. An unknown id raises `KeyError` before any metric read. For `district` and `sub_district`, when the control is a combobox, build `core.components.slicer.Slicer` with one `SlicerDefinition` (`kind="dropdown"`, that id, the page role name) and a settle hook that calls `wait_for_screen_1_idle()` on `after_select` and returns false, then call `Slicer.select(slicer_id, value)`. A sandbox input that is not a combobox keeps the page-local input path. For `date`, open the date control and call `_pick_open_date` when the open list is the virtualized dropdown (the scroll loop is T016). Do not call `collect_virtualized_rows` for the date. Do not clear labels already selected on that slicer, so two `sub_district` calls leave both names. Do not edit `core/components/slicer.py`.
- [X] T008 [US1] In `pages/authorities_status/page.py`, add `section_anchor_visible(self, section: str) -> bool`. Return true for `date` when the date control is visible, for `filters` when a Screen 1 filter control is visible, and for `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report` when that block's heading on the live report is visible. Copy those headings from the open report onto the page. Return false for `title` and for any other section. A locator error returns false and does not raise.
- [X] T009 [US1] In `pages/authorities_status/page.py`, add `read_screen_1_metrics(self) -> dict` and the private readers it calls. Return `date` (selected label), `filters` (`district` string and `sub_district` list of selected labels), `survey_status` (`filled`, `out_of`), `authorities_status` (`coping_well`, `may_struggle`, `struggling`, each with `count` and `authorities` of `name`, `score`, and `trend` when that row shows an arrow), `facilities` (`operation_centers` including `unknown_in`, `protection_facilities` including `partially_open_count`, `call_centers_106`, each with `open` and `closed` of `count` and authority-name lists), and `missing_daily_report` (`count` and authority-name list). Do not return `title`. Do not change a slicer. Do not open Screen 2. Do not embed golden literals. If a name list is a virtualized grid, call `collect_virtualized_rows` from `core/components/virtual_grid.py` without editing that file. A short plain-text list is read from the block. Do not call `collect_virtualized_rows` from `_pick_open_date`.
- [X] T016 [US1] In `pages/authorities_status/page.py`, replace the wait-only body of `_pick_open_date(self, control, value)` with a bounded scroll loop. Do not import or call `collect_virtualized_rows` on this path. Do not edit `core/components/slicer.py` or `core/components/virtual_grid.py`. Keep the existing import only if T009 name-list readers still use it. Locate the scrollable container inside the open slicer; prefer a node whose class contains `scrollRegion`. If that node is absent, send `PageDown` to the focused dropdown list. Loop at most 20 times. On each pass, if a locator for `value` is visible (`is_visible()`), click it and return. Otherwise scroll with `press("PageDown")` on the list container, or `evaluate("node => node.scrollTop += 150")` on the scrollable container. When the container exposes `scrollTop`, read it before and after the scroll; if it does not change, break. If the loop ends without a click, raise `AssertionError` whose message includes the texts of the rows visible then, in the shape `Open date option {value!r} was not visible. rows=...`. After a successful click, the existing caller still waits for Screen 1 idle and checks that the combobox text contains `value`.

**Checkpoint**: `test_authorities_screen1_matches_golden` can apply the golden date by scrolling the open dropdown, wait for idle, and walk `screen_1_national_status`.

---

## Phase 4: User Story 2 - Smoke and Screen 2 stay as they are (Priority: P1)

**Goal**: The freshness smoke is unchanged, and this slice does not open or compare Screen 2.

**Independent Test**: `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` is still only `dashboard.verify_freshness()`. The sanity module does not reference `screen_2_service_targets`.

### Implementation for User Story 2

- [X] T010 [P] [US2] Leave `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` and `tests/ui/authorities_status_dashboard/conftest.py` unchanged. The test body stays `dashboard.verify_freshness()`. The fixture stays `dashboard = bind_dashboard(AuthoritiesStatusPage)` with no fixture-name argument.
- [X] T011 [US2] Confirm `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` never reads `screen_2_service_targets`, and `pages/authorities_status/page.py` has no method that opens Screen 2. Do not edit `data/reshuyot/db_sanity.yaml`, including `dashboard.screen_2_service_targets`.

**Checkpoint**: Smoke and Screen 2 are the same as before this slice. US1 still owns the Screen 1 check.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Catalog the new reader and run the sanity command from quickstart.md

- [X] T012 [P] Append an Authorities Status section to `docs/COVERAGE_CATALOG.md` after the Hosen section. Map `screen_1_national_status` keys `date`, `filters`, `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report` to `AuthoritiesStatusPage.read_screen_1_metrics()` and `test_authorities_screen1_matches_golden`. State the source is `data/reshuyot/db_sanity.yaml`, not SQL, and that `screen_2_service_targets` has no reader in this slice. Name `pages/authorities_status/page.py`, `tests/sanity/authorities_status_dashboard/conftest.py`, and `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py`.
- [X] T013 Run `pytest tests/sanity/authorities_status_dashboard -m sanity` from the repo root. A mismatch must name a path under `dashboard.screen_1_national_status`. Do not edit `data/reshuyot/db_sanity.yaml` to make this pass.
- [X] T014 Run `pytest tests/ui/authorities_status_dashboard/ -m sanity` from the repo root. `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` must still call `dashboard.verify_freshness()` only.
- [X] T015 Confirm the diff does not edit `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `tests/ui/authorities_status_dashboard/`, `data/hosen/`, `data/reshuyot/db_sanity.yaml`, `tests/helpers/`, `db/`, or root `conftest.py`. Comments inside new functions in `pages/authorities_status/page.py` are English. Fleet smoke is not required.
- [X] T017 After T016, run `pytest tests/sanity/authorities_status_dashboard -m sanity` from the repo root. A mismatch must name a path under `dashboard.screen_1_national_status`. A missing date must fail from `_pick_open_date` with the visible rows, not from `collect_virtualized_rows`. Do not edit `data/reshuyot/db_sanity.yaml` to make this pass. Do not edit `core/`.

---

## Phase 6: User Story 1 - Survey `filled` text node (Priority: P1)

**Goal**: `read_screen_1_metrics()` returns the painted digit for `survey_status.filled` and `survey_status.out_of`. The current failure is `AssertionError: dashboard.screen_1_national_status.survey_status.filled: ui='' golden=18` because `_read_survey_status` stores `""`.

**Independent Test**: `pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py::test_authorities_screen1_matches_golden -m sanity` from the repo root. `data/reshuyot/db_sanity.yaml` stays at `survey_status.filled: 18`.

### Implementation for User Story 1

- [X] T018 [P] [US1] In `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, read `assert_value` and `_assert_tree` and leave both functions unchanged. `assert_value` already parses an int with `re.search(r"-?\d+")` and, when that search misses, compares the original `actual`, so `''` fails against `18` and is not stored as `0`. `_assert_tree` already recurses into a non-empty dict and fails on `survey_status.filled`. Neither helper calls `sleep`, `wait_for_timeout`, `expect`, or a page locator. Do not add a retry. The test body keeps its existing `wait_for_screen_1_idle()` calls and the single `read_screen_1_metrics()` call. Do not embed `18`.
- [X] T019 [US1] In `pages/authorities_status/page.py`, change `_read_survey_status` so `filled` and `out_of` are read from the report frame, not from `_section("רשויות הזינו את הסקר")`. `filled` is `svg[aria-label^='GOALS_COUNT_MUNI']`. `out_of` is `svg[aria-label*='Muni_Code']`. A missing `_section` result must not force both fields to `""` while those SVGs are on the frame. For each SVG, `expect` it `to_be_visible` within `self.timeout`. Prefer a descendant `tspan` or `text` filtered with `has_text=re.compile(r"\d")`: `expect` that node `to_be_visible`, then `to_have_text` with the same digit pattern, then return `_plain` of its `text_content`. When no digit text node appears, `expect` the SVG `to_have_text` with that digit pattern and return `_plain` of the SVG `text_content`. On timeout, return `""` so the assertion can still print `ui='' golden=18`. Do not write `18` into the page. Do not call `sleep`, `wait_for_timeout`, or `networkidle`. Do not change `wait_for_screen_1_idle`. Leave `_svg_text` section-scoped for `count_records`, `unknownCenter`, and `openPartMigun`. Do not edit `_facility_sides`. Comments inside the new helper stay English.

**Checkpoint**: The survey reader waits for a digit text node. `assert_value` and `_assert_tree` are the same functions as before this phase.

---

## Phase 7: User Story 2 - Smoke and Screen 2 stay closed (Priority: P1)

**Goal**: The survey-count edit does not reopen Screen 2 or the freshness smoke.

**Independent Test**: `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` is still only `dashboard.verify_freshness()`. `data/reshuyot/db_sanity.yaml` still has `survey_status.filled: 18` and an untouched `dashboard.screen_2_service_targets`.

### Implementation for User Story 2

- [X] T020 [US2] After T019, confirm the only product edit is `pages/authorities_status/page.py`. Leave these paths unmodified: `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py`, `tests/ui/authorities_status_dashboard/conftest.py`, `data/reshuyot/db_sanity.yaml`, `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `tests/helpers/`, `db/`, and the root `conftest.py`. `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` stays unmodified because T018 leaves `assert_value` and `_assert_tree` in place. `pages/authorities_status/page.py` still has no Screen 2 method, and `wait_for_screen_1_idle` still only hides a visible spinner and shows the ready phrase.

**Checkpoint**: Smoke, the golden YAML, Hosen, and `core/` are outside the survey-count diff.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Re-run the failing sanity test from `specs/053-authorities-screen1-sanity/quickstart.md`

- [X] T021 After T019, run `pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py::test_authorities_screen1_matches_golden -m sanity` from the repo root. A pass means `survey_status.filled` and `survey_status.out_of` were digit strings and matched the golden integers. If the text node never paints, the failure stays `dashboard.screen_1_national_status.survey_status.filled: ui='' golden=18`. A different digit is still a failure. Do not edit `data/reshuyot/db_sanity.yaml` to make this pass. Do not edit `core/`. Fleet smoke is not required.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Story 1 (Phase 3)**: Depends on T004 and T005. T006 can be written before T007–T009 and fails until those methods exist. T016 replaces the body of `_pick_open_date` after T007.
- **User Story 2 (Phase 4)**: T010 depends only on Phase 2. T011 depends on T006 and T009.
- **Polish (Phase 5)**: T013 needs T006–T009. T014 needs T010. T015 runs after T013 and T014. T017 re-runs the sanity command after T016. T001–T017 are already done.
- **Survey count (Phase 6)**: T018 and T019 start from the checked page and test. They do not reopen T004–T017.
- **Boundary (Phase 7)**: T020 runs after T018 and T019.
- **Polish (Phase 8)**: T021 runs after T019. T020 can finish before or after T021; it does not change the reader.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T004 and T005. No dependency on US2. This is the MVP. The open US1 work is T018 and T019.
- **User Story 2 (P1)**: T010 starts after Phase 2 and does not need the reader. T011 checks the files US1 added. US2 does not change Screen 1 behavior. T020 only checks that the survey edit stayed inside the page.

### Within Each User Story

- T006 (the test) is written before T007–T009 (the page methods that make it pass).
- T007, T008, T009, and T016 all edit `pages/authorities_status/page.py`. T007–T009 run in that order. T016 runs after T007 and does not edit `core/`.
- T009 before T013. T016 before T017.
- T010 before T014.
- T013 and T014 before T015. T017 is the sanity re-run after the date scroll loop.
- T018 does not block T019. Both finish before T020. T021 runs after T019.

### Parallel Opportunities

- T002 and T003 can run together (new empty package vs read-only inventory).
- T004 and T005 touch different files and can run together after Setup.
- T006 (test file) can be written while T010 confirms the smoke files. Do not edit `pages/authorities_status/page.py` in parallel with T007, T008, T009, or T016.
- T012 touches only `docs/COVERAGE_CATALOG.md` and can be drafted from the contract once the method names in T009 are stable.
- T016 is done. T019 is the only open edit of `pages/authorities_status/page.py`. It does not run beside another edit of that file.
- T018 touches only `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, and only to confirm it stays as it is. It can run beside T019.

---

## Parallel Example: User Story 1

```bash
# After T004 and T005, the test file and the smoke guard are different files:
Task: "T006 Create tests/sanity/authorities_status_dashboard/test_screen1_sanity.py"
Task: "T010 Leave tests/ui/authorities_status_dashboard/ unchanged"

# Same page file, one after another:
Task: "T007 select_screen_1_filter in pages/authorities_status/page.py"
Task: "T008 section_anchor_visible in pages/authorities_status/page.py"
Task: "T009 read_screen_1_metrics in pages/authorities_status/page.py"
Task: "T016 replace _pick_open_date in pages/authorities_status/page.py"

# Open survey-count work. Different files, so these two start together:
Task: "T018 Leave assert_value and _assert_tree in tests/sanity/authorities_status_dashboard/test_screen1_sanity.py"
Task: "T019 Read survey filled and out_of from the digit text node in pages/authorities_status/page.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: `wait_for_screen_1_idle` and the `authorities_status_dashboard` fixture.
3. Complete Phase 3: User Story 1 (test, then select, anchors, reader, then the `_pick_open_date` scroll loop).
4. **STOP and VALIDATE**: `pytest tests/sanity/authorities_status_dashboard -m sanity` (T017 after T016).
5. The walk matches `dashboard.screen_1_national_status` or fails with that YAML path. The date click does not call `collect_virtualized_rows`.

### Incremental Delivery

1. Setup + Foundational → idle wait and fixture exist. Smoke is still untouched.
2. User Story 1 → Screen 1 date, filters, read, and private walk, then the page-local date scroll loop (the MVP).
3. User Story 2 → smoke file and Screen 2 stay out of the diff.
4. Polish → coverage catalog, sanity pytest, smoke pytest, diff check, then re-run sanity after T016.
5. Survey count → T019 reads `filled` and `out_of` from the digit text node, T018 leaves the walk synchronous, T021 re-runs the one failing test.

### Parallel Team Strategy

One developer owns `pages/authorities_status/page.py` for T004, T007, T008, T009, T016, and T019. A second developer can take T002, T005, T006, T010, and T018. Do not split T007–T009, T016, or T019 across two editors.

---

## Notes

- [P] tasks = different files, no dependencies on an unfinished edit of that same file.
- [US1] and [US2] map to spec.md. Setup, Foundational, and Polish have no story label.
- The code change is `pages/authorities_status/page.py` plus the new sanity package. The YAML file is not a task to edit.
- Commit after each task or logical group.
- Stop at the US1 checkpoint and run the sanity test before polishing.
- `sub_district` is two `select_screen_1_filter` calls. The second call does not clear the first label.
- T016 is done. `_pick_open_date` scrolls at most 20 steps, clicks `value` when it is visible, and raises `AssertionError` with the visible rows when it is not. It does not call `collect_virtualized_rows`.
- T001–T017 stay checked. They already match the page, the sanity package, the catalog, and the smoke guard.
- T018–T021 are the open survey-count work. T019 is the only code change: report-frame `GOALS_COUNT_MUNI` and `Muni_Code`, digit `tspan` or `text`, `expect` visible then `to_have_text` with a digit, `text_content`, and `""` on timeout. T018 and T020 do not edit files when the current code already matches. T021 runs the single sanity test and does not edit the YAML.
