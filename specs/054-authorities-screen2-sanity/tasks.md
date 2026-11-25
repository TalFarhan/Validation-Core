---
description: "Task list for Authorities Status Screen 2 YAML sanity"
---

# Tasks: Authorities Status Screen 2 YAML Sanity

**Input**: Design documents from `/specs/054-authorities-screen2-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/authorities-screen2-sanity.md, quickstart.md

**Tests**: The sanity test is the feature (spec.md User Story 1). Write it in this slice. Fleet smoke is not a gate: `core/portal` and `core/components` are not edited. Authorities smoke stays `dashboard.verify_freshness()` and is not edited. Screen 1 sanity stays `test_authorities_screen1_matches_golden` and is not edited.

**Organization**: Tasks follow user stories in spec.md. US1 is the Screen 2 reader and the golden walk. US2 keeps Screen 1, smoke, and closed files untouched.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 or US2 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page: `pages/authorities_status/page.py` (`AuthoritiesStatusPage`)
- Golden record (do not edit): `data/reshuyot/db_sanity.yaml` (`dashboard.screen_2_service_targets` only; do not load `dashboard.screen_1_national_status` from the Screen 2 test)
- New sanity module: `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`
- Existing sanity fixture (do not recreate): `tests/sanity/authorities_status_dashboard/conftest.py`
- Existing Screen 1 test (do not edit): `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`
- Existing smoke (do not edit): `tests/ui/authorities_status_dashboard/`
- Contract: `specs/054-authorities-screen2-sanity/contracts/authorities-screen2-sanity.md`
- OFF-LIMITS: `core/portal/`, `core/components/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `data/hosen/`, `data/reshuyot/db_sanity.yaml`, `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, `tests/ui/authorities_status_dashboard/`, `specs/053-authorities-screen1-sanity/`, `tests/helpers/` (no new compare helper), `db/`, root `conftest.py`

Do not add `pages/authorities_status/__init__.py`. Comments inside functions stay English. Hebrew stays in locator constants on the page or in the YAML. Do not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`. Do not embed golden numbers, service names, dates, or filter values in the page or the test. Do not hardcode `title`. Do not copy or import Hosen. Do not import `test_screen1_sanity.py`. Do not switch git branches. Do not route Screen 2 selections through `select_screen_1_filter`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Pin this slice and record the files that already exist

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/054-authorities-screen2-sanity"`. Git checkout stays `feature/reportportal-integration`. Do not edit `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `tests/ui/authorities_status_dashboard/`, `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, `specs/053-authorities-screen1-sanity/`, or `data/reshuyot/db_sanity.yaml`.
- [X] T002 [P] Inventory without editing. In `pages/authorities_status/page.py`, confirm `DASHBOARD_SEARCH_TERM` is `הערכת מצב רשויות`, `_report_ready_locator` uses that phrase, and public Screen 1 methods `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, `section_anchor_visible`, and `_pick_open_date` exist. In `data/reshuyot/db_sanity.yaml`, load `dashboard.screen_2_service_targets` with `yaml.safe_load` and confirm keys `title`, `date`, `filters.district` (string), `filters.sub_district` (string), `sector_profile`, `protection_data`, `service_targets`, `grade_trends` (`None`), and sibling `data` (list of `{date, scores}`). Do not indent `data` under `grade_trends`. In `tests/sanity/authorities_status_dashboard/conftest.py`, confirm `authorities_status_dashboard = bind_dashboard(AuthoritiesStatusPage, "authorities_status_dashboard")`. In `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py`, confirm the body is `dashboard.verify_freshness()`. Do not copy helpers from `pages/hosen_status/page.py` or `tests/sanity/hosen_status_dashboard/`.

**Checkpoint**: The slice directory is pinned. No product code changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Screen 2 idle and a Screen 1-safe settle hook so later stories can select and read

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 In `pages/authorities_status/page.py`, keep `DASHBOARD_SEARCH_TERM`, `_report_ready_locator`, and `wait_for_screen_1_idle` as they are. Add `_screen_2_title` (start as `""`) and `_screen_2_settle(kind="after_select", **_kwargs)` that, on `after_select`, calls `wait_for_screen_2_idle()` and returns false. Add `wait_for_screen_2_idle()`: if the report iframe has a visible `[class*='spinner']` or `[aria-busy='true']` node, expect it hidden within `self.timeout`; then expect the Screen 2 ready locator visible. The Screen 2 ready locator is the page-name segment of `_screen_2_title` (text after the last ` - `, with ASCII `"` and Hebrew gershayim as locator variants). Do not use `_report_ready_locator()` here. A spinner that is not showing is not a failure. Do not call `sleep`, `wait_for_timeout`, or `networkidle`. Do not copy Hosen `_hide_visible_spinner` or `_quote_variants`.
- [X] T004 In `pages/authorities_status/page.py`, give private `_slicer` and `_select_date` an optional settle callable that defaults to `_screen_1_settle`. `select_screen_1_filter` must still wait for Screen 1 idle after a date or sandbox selection. Do not change the public signatures of `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, or `section_anchor_visible`. Do not copy `_pick_open_date`. Do not edit `core/components/slicer.py`. Do not add `select_screen_2_filter` yet (that is T008).
- [X] T005 [P] Leave `tests/sanity/authorities_status_dashboard/conftest.py` unchanged. The fixture stays `authorities_status_dashboard = bind_dashboard(AuthoritiesStatusPage, "authorities_status_dashboard")`. Do not edit `tests/ui/authorities_status_dashboard/conftest.py`.

**Checkpoint**: The page can wait for Screen 2 without replacing Screen 1 idle. The sanity fixture name is still `authorities_status_dashboard`.

---

## Phase 3: User Story 1 - Service targets screen matches the golden YAML (Priority: P1) 🎯 MVP

**Goal**: Open Screen 2 with the golden title, apply `dashboard.screen_2_service_targets` date and filters, read Screen 2, and walk that block with a private compare.

**Independent Test**: `pytest tests/sanity/authorities_status_dashboard/test_screen2_sanity.py -m sanity --reportportal` runs `test_authorities_screen2_matches_golden`.

### Tests for User Story 1

- [X] T006 [P] [US1] Create `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`. Mark `test_authorities_screen2_matches_golden` with `@pytest.mark.sanity` and the fixture `authorities_status_dashboard`. Load `data/reshuyot/db_sanity.yaml` with `yaml.safe_load` and take `["dashboard"]["screen_2_service_targets"]` only. Do not read `screen_1_national_status`. If `title` is present, call `open_screen_2(str(title))` and do not assert `title`. If `date` is present and non-empty, call `select_screen_2_filter("date", str(date))` then `wait_for_screen_2_idle()`. For each `filters` item in YAML order, select a string once, or each list item in order via `str(item)`. Never pass `str(list)` as the label. After every selection, and once more before the read, call `wait_for_screen_2_idle()`, then `read_screen_2_metrics()`. Walk every golden key with private helpers in this file (do not import `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, do not import `tests/sanity/hosen_status_dashboard/`, and do not add a helper under `tests/helpers/`). Duplicate Screen 1 `assert_value`, `_assert_rows`, and `_assert_tree`. An int matches grouped or plain digits. A float matches the displayed number (`100.0` matches `100` or `100.0`; `94.46` stays `94.46`). A string matches display text after bidi marks `U+200E`, `U+200F`, `U+202A`–`U+202C` and outer whitespace are removed. Object rows match on `name` if that field exists, else on `date` if that field exists, else `title`. Nested `scores` maps walk every golden key. Extra UI rows do not fail. Skip a key when `screen_2_section_visible` is false, including `title` and `grade_trends`. A visible anchor whose read is empty while the golden value has data fails, and the message includes the path `dashboard.screen_2_service_targets...`. If every key is skipped, call `pytest.skip`. Do not embed golden numbers, service names, dates, or filter values.

### Implementation for User Story 1

- [X] T007 [US1] In `pages/authorities_status/page.py`, add `open_screen_2(self, title: str) -> None`. Store `title` in `_screen_2_title`. Click a visible page-navigation control whose accessible name equals `title` or the trailing segment after ` - `. Treat ASCII `"` and Hebrew gershayim as locator variants. Do not hardcode `'הערכת מצב רשויות - תמ"צ יעדי השירות'`. If the control is missing and the Screen 2 ready locator is not already visible, raise `AssertionError` naming the title. Then call `wait_for_screen_2_idle()`. Do not copy `open_investigation_screen` from `pages/hosen_status/page.py`.
- [X] T008 [US1] In `pages/authorities_status/page.py`, add `select_screen_2_filter(self, slicer_id: str, value: str)`. Resolve `slicer_id` from the existing Screen 1 role table (`date`, `district`, `sub_district`). An unknown id raises `KeyError` before any metric read. For `district` and `sub_district`, when the control is a combobox, build `core.components.slicer.Slicer` with one `SlicerDefinition` (`kind="dropdown"`, that id, the page role name) and settle `_screen_2_settle`, then call `Slicer.select(slicer_id, value)`. A sandbox input that is not a combobox keeps the existing page-local input path, then `wait_for_screen_2_idle()`. For `date`, reuse `_select_date` / `_pick_open_date` with Screen 2 settle (T004). Do not call `collect_virtualized_rows` for the date. Do not call `select_screen_1_filter`. Do not clear labels already selected on that slicer. Do not edit `core/components/slicer.py`.
- [X] T009 [US1] In `pages/authorities_status/page.py`, add `screen_2_section_visible(self, section: str) -> bool`. Do not change `section_anchor_visible`. Return true for `date` when the Screen 2 date control is visible, for `filters` when a Screen 2 filter control is visible, and for `sector_profile`, `protection_data`, `service_targets`, and `data` when that block's heading or visual on the live Screen 2 report is visible. Copy those headings from the open Screen 2 report onto the page. Return false for `title`, `grade_trends`, and any other section. A locator error returns false and does not raise.
- [X] T010 [US1] In `pages/authorities_status/page.py`, add `read_screen_2_metrics(self) -> dict` returning `date` (selected label), `filters` (`district` string and `sub_district` string, not Screen 1's `sub_district` list), `sector_profile` (`average_final_score`, `national_average_score`, `number_of_residents`, `resilience_score_percentage`, `defense_policy`, `total_alerts_last_24h`), `protection_data` (`mamad_mamak`, `shared_shelter`, `public_shelters_capacity`, `without_shelter`, each with `count` and `population_percentage`), `service_targets` (placeholder `[]` until T011), `grade_trends` (`None`), and `data` (placeholder `[]` until T012). Do not return `title`. Do not change a slicer. Do not embed golden literals. Copy card headings and aria prefixes from the live Screen 2 report. For digit fields, `expect` the node `to_be_visible` then `to_have_text` with a digit pattern within `self.timeout`, then read `text_content`. On timeout return `""`. Do not call `sleep`, `wait_for_timeout`, or `networkidle`. Do not change `wait_for_screen_2_idle` to wait for these cards.
- [X] T011 [US1] In `pages/authorities_status/page.py`, fill `service_targets` in `read_screen_2_metrics` as a list of `{name, score}`. If the visual is a `role=grid`, call `collect_virtualized_rows` from `core/components/virtual_grid.py` without editing that file. Do not hardcode the fourteen service names. Do not call `collect_virtualized_rows` from `_pick_open_date`.
- [X] T012 [US1] In `pages/authorities_status/page.py`, fill `data` in `read_screen_2_metrics` from Layer 2 `VisualTable`. Import `VisualTable` from `core.components.visual_table`. Locate the trends visual host from the live Screen 2 heading with a page-local climb to a `visualContainer` / `vcGroupBody` large enough to right-click (not a header strip). Call `VisualTable(self.page, self._report_frame(), timeout_ms=self.timeout).read_rows(host, name=...)`. Map each header→cell dict on the page: the `DD/MM/YYYY` cell is `date`; remaining numeric cells become `scores` keyed by displayed header text. Do not hardcode category names. Keep `grade_trends` as `None`. When the host cannot be marked, return `[]`. Do not copy `_mark_visual_host` from `pages/hosen_status/page.py`. Do not edit `core/components/visual_table.py`.

**Checkpoint**: `test_authorities_screen2_matches_golden` can open Screen 2, apply the golden date, wait for Screen 2 idle, and walk `screen_2_service_targets`.

---

## Phase 4: User Story 2 - Screen 1, smoke, and closed files stay as they are (Priority: P1)

**Goal**: Screen 1 sanity, the freshness smoke, and the listed closed files stay the Screen 1 contract.

**Independent Test**: `pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py -m sanity --reportportal` still passes. `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` is still only `dashboard.verify_freshness()`.

### Implementation for User Story 2

- [X] T013 [P] [US2] Leave `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` and `tests/ui/authorities_status_dashboard/conftest.py` unchanged. The test body stays `dashboard.verify_freshness()`. The fixture stays `dashboard = bind_dashboard(AuthoritiesStatusPage)` with no fixture-name argument.
- [X] T014 [US2] Confirm `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` is not edited and still loads only `screen_1_national_status`. Confirm `test_screen2_sanity.py` never reads `screen_1_national_status`. Confirm public Screen 1 methods `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, and `section_anchor_visible` in `pages/authorities_status/page.py` keep their signatures and Screen 1 settle. Do not edit `data/reshuyot/db_sanity.yaml`. Do not edit `specs/053-authorities-screen1-sanity/`.

**Checkpoint**: Smoke and Screen 1 are the same contract as before this slice. US1 still owns the Screen 2 check.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Catalog the new reader and run both sanity commands from quickstart.md

- [X] T015 [P] Update section 12 of `docs/COVERAGE_CATALOG.md`. Keep the existing Screen 1 rows. Add Screen 2 rows mapping `screen_2_service_targets` keys `date`, `filters`, `sector_profile`, `protection_data`, `service_targets`, and as-loaded `data` to `open_screen_2`, `select_screen_2_filter`, `read_screen_2_metrics` (`VisualTable.read_rows` for `data`, `collect_virtualized_rows` for `service_targets` when the list is a grid), and `test_authorities_screen2_matches_golden`. State the source is `data/reshuyot/db_sanity.yaml`, not SQL, that `title` is navigation-only, and that `grade_trends` is null so trend rows are compared on `data`. Name `pages/authorities_status/page.py`, `tests/sanity/authorities_status_dashboard/conftest.py`, `test_screen2_sanity.py`, and `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py`.
- [ ] T016 Run `pytest tests/sanity/authorities_status_dashboard/test_screen2_sanity.py -m sanity --reportportal` from the repo root. A mismatch must name a path under `dashboard.screen_2_service_targets`. Do not edit `data/reshuyot/db_sanity.yaml` to make this pass.
- [X] T017 Run `pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py -m sanity --reportportal` from the repo root. Do not edit `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` to make this pass.
- [ ] T018 Confirm the diff does not edit `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `tests/ui/authorities_status_dashboard/`, `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, `data/hosen/`, `data/reshuyot/db_sanity.yaml`, `specs/053-authorities-screen1-sanity/`, `tests/helpers/`, `db/`, or root `conftest.py`. Comments inside new functions in `pages/authorities_status/page.py` are English. Hebrew is limited to locator constants. Fleet smoke is not required.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. This is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational. Verify after US1 so Screen 1 settle changes are included. Independently testable via the existing Screen 1 command.
- **Polish (Phase 5)**: Depends on US1 and US2

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No dependency on US2.
- **User Story 2 (P1)**: Can start after Foundational (Phase 2). Does not implement Screen 2. Validates that US1 did not break Screen 1 or smoke.

### Within User Story 1

1. T006 (test) may start in parallel with T007 because it is a different file.
2. T007 `open_screen_2` before T008–T012 that assume Screen 2 is showing.
3. T008 `select_screen_2_filter` before the reader (filters must be selectable).
4. T009 anchors before the test walk can skip/fail correctly.
5. T010 reader skeleton before T011 and T012 fill `service_targets` and `data`.

### Parallel Opportunities

- T001 then T002 (T002 is [P] inventory).
- T005 [P] with T003/T004 (different file; T003 and T004 share `page.py` so they are sequential).
- T006 [P] with T007 (test file vs page file). T008–T012 are sequential on `page.py`.
- T013 [P] with T014 after US1 page work, or T013 anytime after Foundational (smoke files are untouched).
- T015 [P] with the pytest runs only after the page and tests exist; T016 then T017 then T018 are sequential gates.

---

## Parallel Example: User Story 1

```bash
# Different files after Foundational:
Task: "Create test_screen2_sanity.py in tests/sanity/authorities_status_dashboard/test_screen2_sanity.py"
Task: "Add open_screen_2 in pages/authorities_status/page.py"
```

Then on the page, in order: `select_screen_2_filter` → `screen_2_section_visible` → `read_screen_2_metrics` cards → `service_targets` → `VisualTable` trends.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `pytest tests/sanity/authorities_status_dashboard/test_screen2_sanity.py -m sanity --reportportal`
5. Then US2 + Polish, including the Screen 1 command

### Incremental Delivery

1. Setup + Foundational → Screen 2 idle exists, Screen 1 settle still defaults
2. User Story 1 → Screen 2 golden walk (MVP)
3. User Story 2 → confirm Screen 1 and smoke unchanged
4. Polish → catalog + both pytest commands

### Parallel Team Strategy

This slice is one page file plus one new test file. One implementer should own `pages/authorities_status/page.py`. A second person can write T006 in parallel, then wait for T007–T012 before T016.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to US1 or US2
- PyYAML loads `grade_trends` as `null` and trend rows as sibling `data`. Do not edit the YAML to nest them.
- `title` is passed into `open_screen_2` and is never asserted
- `wait_for_screen_2_idle` uses the Screen 2 page-name locator, not `הערכת מצב רשויות`
- Done when T016 and T017 both pass
- Avoid: importing Hosen, importing Screen 1 test helpers, `str(list)`, `sleep` / `networkidle`, editing `core/`
