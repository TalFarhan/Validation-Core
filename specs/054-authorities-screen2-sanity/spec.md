# Feature Specification: Authorities Status Screen 2 YAML Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `054-authorities-screen2-sanity`; git checkout stays put)

**Created**: 2026-11-24

**Status**: Draft

**Input**: User description: "Add a Screen 2 sanity test for Authorities Status against `data/reshuyot/db_sanity.yaml` (`dashboard.screen_2_service_targets` only), extending `pages/authorities_status/page.py` without breaking Screen 1. Navigate with the golden title as a target only (do not assert it). Add `select_screen_2_filter`, `wait_for_screen_2_idle`, `read_screen_2_metrics`, and Screen 2 section anchors. Reuse Layer 2 `Slicer` (including Screen 1 virtualized date-pick), `VisualTable`, and `collect_virtualized_rows`. Load only `dashboard.screen_2_service_targets`. Apply `date` first, then `filters` in YAML key order. Private assertion helpers matching Screen 1 rules. Do not touch Screen 1 tests, smoke, `core/`, Hosen, or the golden YAML. Do not switch git branches."

## Clarifications

### Session 2026-11-24

- Q: Which git checkout should this slice use? → A: Spec directory `054-authorities-screen2-sanity`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. `specs/053-authorities-screen1-sanity/` is not edited.
- Q: Where do the tests live? → A: `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`. Function `test_authorities_screen2_matches_golden` with `@pytest.mark.sanity` and fixture `authorities_status_dashboard` from the existing sanity conftest. The smoke suite under `tests/ui/authorities_status_dashboard/` stays a one-line `verify_freshness()` call.
- Q: What is the source of truth? → A: `data/reshuyot/db_sanity.yaml` under `dashboard.screen_2_service_targets` only. Numbers, names, dates, and filter values live only in that file. This slice does not edit the YAML. `dashboard.screen_1_national_status` is not loaded, opened, or compared by the Screen 2 test. There is no SQL client.
- Q: What already exists? → A: `AuthoritiesStatusPage` already opens the report, waits for `הערכת מצב רשויות`, and has Screen 1 select, idle, read, date-pick, and anchors. Sanity fixture `authorities_status_dashboard` already binds the page. Screen 1 private `_assert_tree` lives in `test_screen1_sanity.py` and is not edited.
- Q: What must stay unchanged? → A: `data/reshuyot/db_sanity.yaml`, `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, `tests/ui/authorities_status_dashboard/`, `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `data/hosen/`, and `specs/053-authorities-screen1-sanity/`. No new comparison module under `tests/helpers/`. No generic YAML loader in `core/`. Do not copy or import Hosen code. Do not switch git branches.
- Q: How is Screen 2 opened? → A: A page method takes the golden `title` and uses it only as a navigation target (page-navigation control and/or page-name text). The test does not assert `title`. `screen_2_section_visible("title")` is false, so the walk skips it.
- Q: In what order are controls applied? → A: After Screen 2 is showing, if `date` is present, apply it first through `select_screen_2_filter("date", value)`. Then walk `filters` in YAML key order. A string is one selection. A list is one selection per item, in order, without clearing prior selections on the same slicer. Never pass `str(list)`. After every selection, and once more before the read, call `wait_for_screen_2_idle()`.
- Q: How does a selection happen? → A: `select_screen_2_filter(slicer_id, value)` resolves the id on the page and reuses Screen 1's Layer 2 `Slicer` path, including `_pick_open_date` for the virtualized date dropdown. Hebrew role names stay on `pages/authorities_status/page.py`. The test body does not hold locators.
- Q: When is the screen idle? → A: A visible report spinner is gone and the Screen 2 ready locator is visible. No `sleep`, no `wait_for_timeout`, and no `networkidle`. Screen 1 idle and ready locators stay as they are.
- Q: What does the reader return? → A: `read_screen_2_metrics()` returns a dict in the YAML shape as loaded by PyYAML for the keys that are read: `date`, `filters`, `sector_profile`, `protection_data`, `service_targets`, and the as-loaded trend keys (`grade_trends` is null in the checked-in file; the trend rows live under sibling `data`). `title` stays in the YAML and is not returned.
- Q: How does the compare work? → A: Private helpers in `test_screen2_sanity.py` matching Screen 1 rules. Every YAML key under a checked block must match. Extra UI rows are ignored. An integer matches grouped digits. A YAML float matches the displayed number. A string matches display text after bidi marks are stripped. `service_targets` rows match on `name`. Trend rows match on `date`, then score keys. A missing anchor skips that block. A visible anchor with an empty read fails. If every block is skipped, the test calls `pytest.skip`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Service targets screen matches the golden YAML (Priority: P1)

A validation author opens הערכת מצב רשויות, navigates to Screen 2 using the golden title as a click target, applies the golden date and filters, and compares that screen to `dashboard.screen_2_service_targets`.

**Why this priority**: Screen 2 is the only new surface in this slice. Screen 1 must keep passing.

**Independent Test**: `test_authorities_screen2_matches_golden` opens the report through `authorities_status_dashboard`, opens Screen 2 with the golden title, applies `date` then `filters`, waits until Screen 2 is idle, calls `read_screen_2_metrics()`, and walks `screen_2_service_targets`.

**Acceptance Scenarios**:

1. **Given** the golden `title`, **When** the suite starts, **Then** it passes that string to the page as a navigation target only and does not assert `title`.
2. **Given** `date` is present, **When** Screen 2 is showing, **Then** it calls `select_screen_2_filter("date", value)` before any `filters` entry and then waits for Screen 2 idle.
3. **Given** `filters`, **When** the suite applies them, **Then** it walks the map in YAML key order. A string is one selection. A list is one selection per item, in list order. After each selection the suite waits for Screen 2 idle. A later list item does not clear labels already selected on that slicer.
4. **Given** the last selection has settled, **When** the suite is about to read, **Then** it waits for Screen 2 idle once more and only then calls `read_screen_2_metrics()`.
5. **Given** a golden key under a block whose Screen 2 anchor is visible, **When** it is compared, **Then** the same key exists in the UI reading and the values match. Extra UI rows do not fail the test.
6. **Given** a YAML integer, **When** the UI shows grouped or plain digits, **Then** the comparison passes. A YAML float matches the displayed number. A YAML string matches displayed text after bidi marks and surrounding whitespace are removed.
7. **Given** a `service_targets` row, **When** it is compared, **Then** identity is `name`. **Given** a trend row, **When** it is compared, **Then** identity is `date`, then each golden score key.
8. **Given** a section anchor is missing, **When** the walk reaches that block, **Then** the block is skipped. **Given** the anchor is visible and the golden block has data, **When** the reader returns an empty value, **Then** the test fails.
9. **Given** `title` is in the YAML, **When** the walk reaches it, **Then** it is skipped because that Screen 2 anchor is not defined. The YAML file is not edited.

### User Story 2 - Screen 1, smoke, and closed files stay as they are (Priority: P1)

A validation author can still run the Screen 1 sanity test and the Authorities freshness smoke. This slice does not open Screen 1's golden block and does not edit the listed closed files.

**Why this priority**: Screen 1 is already the contract. Breaking it, or editing `core/` / Hosen / the YAML, is out of scope.

**Independent Test**: `test_authorities_screen1_matches_golden` is not edited and still passes. `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` still calls `dashboard.verify_freshness()` only.

**Acceptance Scenarios**:

1. **Given** the Screen 1 sanity module, **When** this slice is done, **Then** it is byte-for-byte the existing file: same function, same fixture, same Screen 1 methods.
2. **Given** Screen 1 public methods, **When** Screen 2 methods are added, **Then** `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, and `section_anchor_visible` keep their current contracts.
3. **Given** the golden file, **When** the Screen 2 test loads it, **Then** it reads `dashboard.screen_2_service_targets` and does not apply or compare `screen_1_national_status`.
4. **Given** the smoke module, **When** this slice is done, **Then** its body is still `dashboard.verify_freshness()` and its fixture is still `dashboard`.

### Edge Cases

- A missing or empty `date` applies no date. A missing or empty `filters` map applies nothing. The idle wait before the read still runs.
- An unknown slicer id fails inside the page before the metric read.
- `filters.sub_district` in the live Screen 2 block is a string, not a list. A string remains one selection. A later YAML list on the same slicer would still be one selection per item.
- `str(list)` is not a slicer label.
- A second selection on the same slicer must not clear the first label.
- PyYAML loads `grade_trends` as `null` and the trend rows as sibling `data` because `data` is not indented under `grade_trends` in the checked-in file. The file is not edited. The reader returns that as-loaded shape. Trend rows are compared on the `data` key.
- `title` is used to navigate and is not a checked block.
- The test, the page, and this spec do not embed the live numbers, service names, dates, or filter values from the YAML.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `AuthoritiesStatusPage` MUST keep `DASHBOARD_SEARCH_TERM = הערכת מצב רשויות` and the Screen 1 ready locator that waits for that phrase. `navigate`, `verify_freshness`, and all Screen 1 public methods MUST keep their current contracts.
- **FR-002**: The page MUST add a Screen 2 open method that takes the golden `title` and uses it only as a navigation target. The test MUST NOT assert `title`.
- **FR-003**: `select_screen_2_filter(slicer_id, value)` MUST select one label. Hebrew role names MUST stay on the page. The test MUST NOT contain locators. Date selection MUST reuse Screen 1's `_pick_open_date` virtualized list walk. District and sub-district MUST compose Layer 2 `Slicer` (or the existing sandbox input when the control is not a combobox). A later call MUST NOT clear labels already selected on that slicer.
- **FR-004**: `wait_for_screen_2_idle()` MUST return only when a visible spinner is gone and the Screen 2 ready locator is visible. It MUST NOT call `sleep`, `wait_for_timeout`, or `networkidle`. It MUST NOT replace Screen 1 idle.
- **FR-005**: The sanity test MUST apply `date` first when present, then each `filters` value in YAML key order. A list value MUST be applied one item at a time, in order. After every selection, and once more before the read, it MUST call `wait_for_screen_2_idle()`.
- **FR-006**: `read_screen_2_metrics()` MUST return `date`, `filters`, `sector_profile`, `protection_data`, `service_targets`, and the as-loaded trend keys, in the YAML shape described in the clarifications. It MUST NOT change a slicer. It MUST NOT return `title`.
- **FR-007**: `sector_profile` MUST include `average_final_score`, `national_average_score`, `number_of_residents`, `resilience_score_percentage`, `defense_policy`, and `total_alerts_last_24h`. `protection_data` MUST include `mamad_mamak`, `shared_shelter`, `public_shelters_capacity`, and `without_shelter`, each with `count` and `population_percentage`.
- **FR-008**: `service_targets` rows MUST match on `name`. Trend rows under as-loaded `data` MUST match on `date`, then each golden key under `scores`. Extra UI rows MUST NOT fail the test.
- **FR-009**: Screen 2 section anchors MUST answer for `date`, `filters`, `sector_profile`, `protection_data`, `service_targets`, and `data`. `title` MUST stay false. `grade_trends` MUST stay false because the checked-in node is null.
- **FR-010**: The sanity test MUST load `dashboard.screen_2_service_targets` and walk it with private helpers in `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`. Those helpers MUST match Screen 1 integer, float, string, mapping, and extra-row rules. They MUST NOT be imported from Hosen. They MUST NOT live under `tests/helpers/`.
- **FR-011**: A missing anchor MUST skip that block. A visible anchor whose reader returns empty data while the golden block has data MUST fail. If every block is skipped, the test MUST call `pytest.skip`.
- **FR-012**: The page and the test MUST NOT embed golden numbers, service names, dates, or filter values. Those literals stay in the YAML.
- **FR-013**: This slice MUST NOT edit `data/reshuyot/db_sanity.yaml`, `test_screen1_sanity.py`, `tests/ui/authorities_status_dashboard/`, `core/`, Hosen pages or tests, `data/hosen/`, or `specs/053-authorities-screen1-sanity/`.
- **FR-014**: Locators and Hebrew accessible names MUST live only on `pages/authorities_status/page.py`. Zero locators in tests.
- **FR-015**: `service_targets` collection MUST reuse `collect_virtualized_rows` when that list is a virtualized grid. Trend collection MUST reuse Layer 2 `VisualTable.read_rows` on the trends visual. `core/` MUST NOT be edited.

### Key Entities

- **Screen 2 service targets record**: `dashboard.screen_2_service_targets` in `data/reshuyot/db_sanity.yaml`. `title` is stored and used only to navigate. `date` and `filters` are applied, then read back. The metric blocks are `sector_profile`, `protection_data`, `service_targets`, and as-loaded `data` (trend rows). `grade_trends` is stored as null.
- **Sector profile**: `average_final_score` (int), `national_average_score` (int), `number_of_residents` (int), `resilience_score_percentage` (int), `defense_policy` (string), `total_alerts_last_24h` (int).
- **Protection bucket**: `mamad_mamak`, `shared_shelter`, `public_shelters_capacity`, or `without_shelter`. Each has `count` (int) and `population_percentage` (float).
- **Service target row**: `{name, score}` with `score` a float. Identity is `name`.
- **Trend row**: `{date, scores}` where `scores` is a map of Hebrew category name to float. Identity is `date`.
- **Filter**: English id to a Hebrew label or a list of Hebrew labels. The live Screen 2 file uses `district` (string) and `sub_district` (string). The page maps each id to the slicer accessible name.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) stays report-agnostic. This slice does not edit it. Freshness stays the inherited `verify_freshness()` path.
- **AC-002**: `AuthoritiesStatusPage` keeps inheriting `ReportShell`. This slice does not re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: Screen 1 report-ready state stays the existing locator for `הערכת מצב רשויות`. Screen 2 ready state is a domain locator supplied by the page from the navigation title, not a Layer 0 change.
- **AC-004**: `navigate`, `verify_freshness`, and Screen 1 methods keep their current contracts. The Screen 2 methods are additive.
- **AC-005**: Layer 2 stays report-agnostic. This slice composes `Slicer`, `VisualTable`, and `collect_virtualized_rows`. It does not load the YAML from `core/` and does not add Authorities titles to `core/`.
- **AC-006**: The page object stays in `pages/authorities_status/page.py`. This slice adds no `db/clients/` module and does not add helpers under `tests/helpers/` or generic readers in `core/`.
- **AC-007**: `data/<report>/` stays `data/reshuyot/db_sanity.yaml`. The file is not edited.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/sanity/authorities_status_dashboard/test_screen2_sanity.py -m sanity --reportportal` applies `screen_2_service_targets.date` and `filters` on Screen 2, waits until Screen 2 is idle, then compares one live reading to that block and fails with a YAML path when a golden key differs.
- **SC-002**: `pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py -m sanity --reportportal` still passes. Screen 1 methods and that test file are unchanged in contract.
- **SC-003**: A golden integer matches grouped digits. A golden float matches the displayed number. A golden string matches only the same display text after bidi marks are stripped. Service-target rows match on `name`. Trend rows match on `date`.
- **SC-004**: With a visible Screen 2 anchor and a non-empty golden block, an empty read fails. With no anchor, that block is skipped. If every block is skipped, the test skips.
- **SC-005**: The diff for this slice contains no edits under `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/authorities_status_dashboard/`, `data/hosen/`, `data/reshuyot/db_sanity.yaml`, `test_screen1_sanity.py`, or `specs/053-authorities-screen1-sanity/`.

## Assumptions

- Screen 1 is the report `AuthoritiesStatusPage.navigate()` already opens. Screen 2 is a second Power BI page reached by clicking a page-navigation control whose name is the golden title or its trailing segment after ` - `.
- Date, district, and sub-district on Screen 2 are the same English ids as Screen 1. Exact accessible names are copied from the live report onto the page during implementation. They are not golden values and they are not written into the YAML.
- A list-valued slicer keeps earlier labels when a later label is selected. The page does not press a clear-all control between those calls.
- Sector-profile and protection cards are DOM text or SVG digits on Screen 2. `service_targets` may be a virtualized grid. `data` trend rows come from `VisualTable.read_rows` on the trends visual.
- Subset comparison stays private in the Screen 2 sanity module. It is not imported from Screen 1, is not imported from Hosen, and is not a new shared engine.
- Golden numbers are already in `data/reshuyot/db_sanity.yaml`. This slice does not recopy the live screen over that file.
- Git checkout stays `feature/reportportal-integration`.
