# Feature Specification: Authorities Status Screen 1 YAML Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `053-authorities-screen1-sanity`; git checkout stays put)

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Add a Screen 1 sanity check for Authorities Status against `data/reshuyot/db_sanity.yaml`, block `dashboard.screen_1_national_status` only. Do not touch Screen 2. `AuthoritiesStatusPage` already opens the report (`DASHBOARD_SEARCH_TERM = הערכת מצב רשויות`) and waits for that phrase. Leave the smoke suite in `tests/ui/authorities_status_dashboard/` unchanged. Mirror Hosen Screen 1. Do not edit `core/`, do not edit Hosen, and do not add a new comparison engine."

## Clarifications

### Session 2026-11-17

- Q: Which git checkout should this slice use? → A: Spec directory `053-authorities-screen1-sanity`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. `specs/052-hosen-screen34-sanity/` and the Hosen page and tests stay untouched.
- Q: Where do the tests live? → A: `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`. The fixture is `bind_dashboard(AuthoritiesStatusPage, "authorities_status_dashboard")`. The smoke suite under `tests/ui/authorities_status_dashboard/` stays a one-line `verify_freshness()` call on the fixture named `dashboard`.
- Q: What is the source of truth? → A: `data/reshuyot/db_sanity.yaml` under `dashboard.screen_1_national_status` only. Numbers, authority names, and filter values live only in that file. This slice does not edit the YAML and does not invent replacement numbers. `dashboard.screen_2_service_targets` is not loaded, opened, or compared. There is no SQL client.
- Q: What already exists? → A: `AuthoritiesStatusPage` subclasses `ReportShell`, searches `הערכת מצב רשויות`, and its ready locator is that same phrase. It has no slicer, reader, or idle method. Hosen Screen 1 already has `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, `section_anchor_visible`, and a private `_assert_tree` in its sanity test.
- Q: What must stay unchanged? → A: `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `data/hosen/`, `tests/ui/authorities_status_dashboard/`, and `dashboard.screen_2_service_targets`. No new comparison module under `tests/helpers/`.
- Q: In what order are controls applied? → A: If `date` is present, apply it first through `select_screen_1_filter("date", value)`. Then walk `filters` in YAML key order. A value may be a string or a list; apply each list item in order. `sub_district` is a list of two names and is two selections, not one stringified list. After every selection, and once more before the read, call `wait_for_screen_1_idle()`.
- Q: How does a selection happen? → A: `select_screen_1_filter(slicer_id, value)` resolves the id on the page and calls the existing Layer 2 `Slicer`. Hebrew role names stay on `pages/authorities_status/page.py`. The test body does not hold locators. A later list item does not clear the labels already selected on that slicer.
- Q: When is the screen idle? → A: A visible report spinner is gone and the existing Screen 1 ready locator is visible. No `sleep`, no `wait_for_timeout`, and no `networkidle`.
- Q: What does the reader return? → A: `read_screen_1_metrics()` returns a dict in the YAML shape for the keys that are read: `date`, `filters`, `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report`. `title` stays in the YAML. It is not a reader key. `section_anchor_visible("title")` is false, so the walk skips it.
- Q: Which metric keys are required? → A: `survey_status` (`filled`, `out_of`); `authorities_status` (`coping_well`, `may_struggle`, `struggling`) each with `count` and `authorities` of `name`, `score`, and `trend` only when the YAML row has `trend`; `facilities` (`operation_centers` including `unknown_in`, `protection_facilities` including `partially_open_count`, `call_centers_106`) each with `open` and `closed` of `count` and authority names; `missing_daily_report` (`count` and authority names).
- Q: How does the compare work? → A: A private walk in the sanity module, the same shape as Hosen `_assert_tree`. Every YAML key under a checked block must match. Extra UI rows are ignored. An integer matches grouped digits. A YAML float matches the displayed number. A string matches display text after bidi marks are stripped. Authority object rows match on `name`. A missing anchor skips that block. A visible anchor with an empty read fails. If every block is skipped, the test calls `pytest.skip`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - National status matches the golden YAML (Priority: P1)

A validation author opens הערכת מצב רשויות on the screen `navigate()` already shows, applies the golden date and filters, and compares that screen to `dashboard.screen_1_national_status`.

**Why this priority**: Screen 1 is the only surface in this slice. Screen 2 stays out of the suite.

**Independent Test**: `test_authorities_screen1_matches_golden` opens the report through `authorities_status_dashboard`, applies `date` then `filters`, waits until Screen 1 is idle, calls `read_screen_1_metrics()`, and walks `screen_1_national_status`.

**Acceptance Scenarios**:

1. **Given** `date` is present, **When** the suite starts, **Then** it calls `select_screen_1_filter("date", value)` before any `filters` entry and then waits for idle.
2. **Given** `filters`, **When** the suite applies them, **Then** it walks the map in YAML key order. A string is one selection. A list is one selection per item, in list order. `sub_district` therefore selects both names. After each selection the suite waits for idle.
3. **Given** the last selection has settled, **When** the suite is about to read, **Then** it waits for idle once more and only then calls `read_screen_1_metrics()`.
4. **Given** a golden key under a block whose anchor is visible, **When** it is compared, **Then** the same key exists in the UI reading and the values match. Extra UI rows do not fail the test.
5. **Given** a YAML integer, **When** the UI shows grouped or plain digits, **Then** the comparison passes. A YAML string matches the displayed text after bidi marks and surrounding whitespace are removed.
6. **Given** an authority row, **When** the YAML row has `trend`, **Then** that trend is compared. A YAML row without `trend` does not fail because the UI also shows a trend.
7. **Given** a section anchor is missing, **When** the walk reaches that block, **Then** the block is skipped. **Given** the anchor is visible and the golden block has data, **When** the reader returns an empty value, **Then** the test fails.
8. **Given** `title` is in the YAML, **When** the walk reaches it, **Then** it is skipped because that anchor is not defined. The YAML file is not edited.

### User Story 2 - Smoke and Screen 2 stay as they are (Priority: P1)

A validation author can still run the Authorities freshness smoke, and nothing in this slice opens or asserts Screen 2.

**Why this priority**: The smoke suite and Screen 2 are explicit non-goals. A Screen 1 reader that changes either of them is out of scope.

**Independent Test**: `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` still calls `dashboard.verify_freshness()` only. The new sanity module does not reference `screen_2_service_targets`.

**Acceptance Scenarios**:

1. **Given** the smoke module, **When** this slice is done, **Then** its body is still `dashboard.verify_freshness()` and its fixture is still `dashboard`.
2. **Given** the golden file, **When** the sanity test loads it, **Then** it reads `dashboard.screen_1_national_status` and does not apply or compare `screen_2_service_targets`.

### Edge Cases

- A missing or empty `date` applies no date. A missing or empty `filters` map applies nothing. The idle wait before the read still runs.
- An unknown slicer id fails inside the page before the metric read.
- `struggling.authorities` is an empty list and `struggling.count` is `0`. The count is compared. Extra UI names on an empty golden list do not fail. A visible block whose whole read is empty does fail.
- `sub_district` must remain two selections. `str(list)` is not a slicer label.
- A second `sub_district` selection must not clear the first name.
- Facility authority lists and `missing_daily_report.authorities` are lists of names, not objects. Every golden name must be present. Extra UI names do not fail.
- The test, the page, and this spec do not embed the live numbers, authority names, or filter values from the YAML.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `AuthoritiesStatusPage` MUST keep `DASHBOARD_SEARCH_TERM = הערכת מצב רשויות` and the ready locator that waits for that phrase. `navigate` and `verify_freshness` keep their current contracts.
- **FR-002**: `select_screen_1_filter(slicer_id, value)` MUST select one label through the existing `Slicer`. Hebrew role names MUST stay on the page. The test MUST NOT contain locators.
- **FR-003**: `wait_for_screen_1_idle()` MUST return only when a visible spinner is gone and the Screen 1 ready locator is visible. It MUST NOT call `sleep`, `wait_for_timeout`, or `networkidle`.
- **FR-004**: The sanity test MUST apply `date` first when present, then each `filters` value in YAML key order. A list value MUST be applied one item at a time, in order. After every selection, and once more before the read, it MUST call `wait_for_screen_1_idle()`.
- **FR-005**: `read_screen_1_metrics()` MUST return `date`, `filters`, `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report` under those names, in the YAML shape described in the clarifications. It MUST NOT change a slicer.
- **FR-006**: `section_anchor_visible(section)` MUST answer for `date`, `filters`, `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report`. `title` MUST stay false so the walk skips it.
- **FR-007**: The sanity test MUST load `dashboard.screen_1_national_status` and walk it with private helpers in `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`. Every golden key in a checked block MUST match. Extra UI rows MUST NOT fail the test. Authority object rows MUST match on `name`. `trend` is compared only when that golden row has it.
- **FR-008**: A YAML integer MUST match displayed digits with or without grouping separators. A YAML float MUST match the displayed number. A YAML string MUST match displayed text after bidi marks and outer whitespace are removed.
- **FR-009**: A missing anchor MUST skip that block. A visible anchor whose reader returns empty data while the golden block has data MUST fail. If every block is skipped, the test MUST call `pytest.skip`.
- **FR-010**: This slice MUST NOT edit `data/reshuyot/db_sanity.yaml`, MUST NOT open or compare Screen 2, MUST NOT edit `core/` or Hosen, and MUST NOT add a comparison engine under `tests/helpers/`.
- **FR-011**: The page and the test MUST NOT embed golden numbers, authority names, or filter values. Those literals stay in the YAML.
- **FR-012**: `tests/ui/authorities_status_dashboard/` MUST stay unchanged.

### Key Entities

- **Screen 1 national status record**: `dashboard.screen_1_national_status` in `data/reshuyot/db_sanity.yaml`. `title` is stored and not checked. `date` and `filters` are applied, then read back. The metric blocks are `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report`.
- **Survey status**: `filled` (int), `out_of` (int).
- **Authority status bucket**: `coping_well`, `may_struggle`, or `struggling`. Each has `count` (int) and `authorities` (list of `{name, score}`, plus `trend` only on rows that have it).
- **Facility**: `operation_centers` (includes `unknown_in`), `protection_facilities` (includes `partially_open_count`), or `call_centers_106`. Each has `open` and `closed` with `count` and a list of authority names.
- **Missing daily report**: `count` (int) and `authorities` (list of names).
- **Filter**: English id to a Hebrew label or a list of Hebrew labels. The live file uses `district` (string) and `sub_district` (list of two names). The page maps each id to the slicer accessible name.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) stays report-agnostic. This slice does not edit it. Freshness stays the inherited `verify_freshness()` path.
- **AC-002**: `AuthoritiesStatusPage` keeps inheriting `ReportShell`. This slice does not re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: Report-ready state stays the existing locator for `הערכת מצב רשויות` on the domain page.
- **AC-004**: `navigate` and `verify_freshness` keep their current contracts. The Screen 1 methods are additive.
- **AC-005**: Layer 2 stays report-agnostic. This slice composes `Slicer` and, when a name list is a virtualized grid, the existing `collect_virtualized_rows`. It does not load the YAML from `core/` and does not add Authorities titles to `core/`.
- **AC-006**: The page object stays in `pages/authorities_status/page.py`. This slice adds no `db/clients/` module and no Screen 2 method.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/sanity/authorities_status_dashboard -m sanity` applies `screen_1_national_status.date` and `filters`, waits until Screen 1 is idle, then compares one live reading to that block and fails with a YAML path when a golden key differs.
- **SC-002**: A golden integer matches grouped digits. A golden string matches only the same display text after bidi marks are stripped. A golden authority `trend` is checked only when that YAML row has `trend`.
- **SC-003**: With a visible anchor and a non-empty golden block, an empty read fails. With no anchor, that block is skipped.
- **SC-004**: `pytest tests/ui/authorities_status_dashboard/ -m sanity` still passes through `verify_freshness()`, and the smoke module is unchanged.
- **SC-005**: The diff for this slice contains no edits under `core/`, `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`, `tests/ui/hosen_status_dashboard/`, `data/hosen/`, or `data/reshuyot/db_sanity.yaml`. Screen 2 is not opened.

## Assumptions

- Screen 1 is the report `AuthoritiesStatusPage.navigate()` already opens. No Screen 2 tab click is required.
- Date, district, and sub-district are slicers `Slicer` can select once the page supplies the Hebrew role name. Exact accessible names are copied from the live report onto the page during implementation. They are not golden values and they are not written into the YAML.
- A list-valued slicer keeps earlier labels when a later label is selected. The page does not press a clear-all control between those calls.
- Survey counts, status buckets, facility counts, and authority names are DOM text on Screen 1. A long name list may be virtualized; in that case the page uses `collect_virtualized_rows` without changing it.
- `trend` is `up` or `down` as stored in the YAML, taken from an arrow on that authority row when the golden row has the key.
- Subset comparison stays private in the Authorities sanity module. It is not imported from Hosen and it is not a new shared engine.
- Golden numbers are already in `data/reshuyot/db_sanity.yaml`. This slice does not recopy the live screen over that file.
