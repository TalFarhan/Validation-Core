# Feature Specification: Hosen Status Screen 1 YAML Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `050-hosen-screen1-sanity`; git checkout stays put)

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Implement YAML sanity validation for the Hosen Status dashboard landing screen (Screen 1). Read filters, KPIs, the resilience table, and survey status through existing generic components. Compare that reading to `data/hosen/db_sanity.yaml`. Do not build a new comparison engine, do not copy Hasbara, Credit, or Alerts scrapers, and do not change `core/` unless a universal reader is missing."

## Clarifications

### Session 2026-11-12

- Q: Which git checkout should this slice use? → A: Spec directory `050-hosen-screen1-sanity`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. Sibling `049-hasbara-ui-validation` stays untouched.
- Q: Where do the tests live? → A: `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`. The fixture is `bind_dashboard(HosenStatusPage, "hosen_status_dashboard")`. The smoke suite under `tests/ui/hosen_status_dashboard/` stays a one-line `verify_freshness()` call.
- Q: What is the source of truth? → A: `data/hosen/db_sanity.yaml` under `hosen_dashboard.screen_1_landing`. Numbers and display strings live only in that file. There is no SQL client and no `data/hosen/hosen_contract.yaml` in this slice.
- Q: What already exists? → A: `pages/hosen_status/page.py` defines `HosenStatusPage(ReportShell)` with search `תמ"צ חוסן`, ready text `תמ"צ ארצי - דיווחי קה"א יקל"ר`, and freshness phrase `מועד רענון`. This slice adds `read_screen_1_metrics()`.
- Q: How are golden literals chosen? → A: The schema is fixed by this spec. The first implementation copies the open landing screen into the YAML once. Later runs compare against that file. Examples such as `7`, `12`, `55%`, `מחוז דרום`, and `נפת לכיש` illustrate shape, not a verified snapshot.
- Q: What does a KPI trend string mean? → A: `up`, `down`, or `flat`, taken from the arrow direction. When the direction glyph is absent and a non-canvas color is readable, green maps to `up`, red maps to `down`, and yellow maps to `flat`.
- Q: What does a resilience row status mean? → A: `green` or `yellow`, taken from the row or score-cell background color. Any other color is returned as read so the golden `green` / `yellow` string fails.
- Q: When is an empty UI a failure? → A: If the section anchor is visible and the golden block has data, an empty reader fails. `pytest.skip` is allowed only when that section's anchor is not rendered.

### Session 2026-11-15

- Q: When are Screen 1 metrics read relative to the golden filters? → A: The test loads `screen_1_landing.filters` and applies every entry before `read_screen_1_metrics()`. An unfiltered read compared with the filtered golden block is the defect this amendment removes.
- Q: Who clicks the dropdown? → A: The test iterates the YAML map and calls the page. `HosenStatusPage` resolves each id to its combobox and calls Layer 2 `Slicer.select`. The test body does not hold locators.
- Q: How does the page know the visuals have finished updating? → A: After each selection, and once more after the map, the page expects a visible report spinner (`spinner` class or `aria-busy`) to be hidden when one is showing, then expects the existing Screen 1 ready locator. No `networkidle`, no `sleep`, no `wait_for_timeout`.
- Q: What is the filter key, and in what order are values applied? → A: The golden key is `filters`, matching `data/hosen/db_sanity.yaml`. Each map key (`district`, `subdistrict`, and any later id) is the slicer id. Apply order is YAML order. A missing or empty `filters` map applies nothing.

### Session 2026-11-16

- Q: Where is a resilience authority name cleaned when the cell contains a second accessibility line? → A: In `HosenStatusPage._visible_resilience_rows`, on the authority cell only. The published `authority` is `_plain` of `extracted_text.split("\n")[0]`. `_assert_rows` keeps matching that published string. The golden file stays `קרית מלאכי`. The score cell is not split.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Landing screen matches the golden YAML (Priority: P1)

A validation author opens תמ"צ חוסן on the landing screen (no tab change), applies the golden filters, and compares survey status, KPI cards, the resilience table, and those filters to `hosen_dashboard.screen_1_landing`.

**Why this priority**: Screen 1 is the only surface in this slice. A drift in any of the four blocks is the defect the suite exists to catch.

**Independent Test**: `test_hosen_screen1_matches_golden` opens the report through `hosen_status_dashboard`, applies `screen_1_landing.filters`, waits until Screen 1 is idle, calls `read_screen_1_metrics()`, and walks `screen_1_landing`.

**Acceptance Scenarios**:

1. **Given** the golden `filters` have been applied and Screen 1 is idle, **When** the suite reads Screen 1, **Then** the returned dict has `survey_status`, `kpis`, `resilience_scores`, and `filters`.
2. **Given** a golden key, **When** it is compared, **Then** the same key exists in the UI reading and the values match. Extra UI rows, KPI categories, missing-authority names, and filter controls that are not in the YAML do not fail the test.
3. **Given** a YAML integer such as `12` or `1324`, **When** the UI shows `12`, `1,324`, or `1324`, **Then** the comparison passes. A YAML string such as `55%` or `מחוז דרום` matches the displayed text exactly after bidi marks and surrounding whitespace are removed.
4. **Given** a section anchor is visible and its golden block has data, **When** the reader returns an empty value for that block, **Then** the test fails.
5. **Given** a section anchor is not in the report, **When** the suite reaches that block, **Then** that block is skipped. Blocks whose anchors are visible are still asserted.
6. **Given** the existing smoke test, **When** this slice is added, **Then** `dashboard.verify_freshness()` remains the body of `test_dashboard_updated_within_24_hours`.

---

### User Story 2 - Survey status counts and missing authorities (Priority: P1)

A validation author reads the top-left survey block: how many authorities submitted, how many were expected, and which authorities are still missing.

**Why this priority**: The fraction and the missing list are the operational status of the landing screen.

**Independent Test**: The `survey_status` object inside `test_hosen_screen1_matches_golden`.

**Acceptance Scenarios**:

1. **Given** `survey_status.submitted` and `survey_status.total`, **When** the top-left block is visible, **Then** both integers match the displayed counts.
2. **Given** `survey_status.missing_authorities`, **When** the list is read, **Then** every golden name is present. Extra names on screen do not fail the test.

---

### User Story 3 - National assessment and eight category KPIs (Priority: P1)

A validation author reads `הערכת קה״א - ממוצע ארצי` and the category cards under that assessment. Each card contributes its title, its percentage, and its trend.

**Why this priority**: The national average and the category breakdown are the center of Screen 1.

**Independent Test**: The `kpis` object inside `test_hosen_screen1_matches_golden`.

**Acceptance Scenarios**:

1. **Given** `kpis.national_average`, **When** the national card is visible, **Then** `title`, `percentage`, and `trend` match. `percentage` keeps the percent sign (`55%` stays a string).
2. **Given** `kpis.categories`, **When** the category cards are visible, **Then** each golden category matches on `title`, and that card's `percentage` and `trend` match. Extra category cards do not fail the test.
3. **Given** a visible card whose reader returns no percentage while the golden card has one, **When** the test compares it, **Then** the test fails.

---

### User Story 4 - Resilience scores and selected filters (Priority: P1)

A validation author selects the golden district and sub-district, then reads the `ציון חוסן` table (authority, score, green or yellow status) for that slice.

**Why this priority**: The table is the per-authority score, and the filters define which slice of the country the other numbers describe. Reading before those filters are applied compares the wrong slice.

**Independent Test**: The `resilience_scores` list and the `filters` map inside `test_hosen_screen1_matches_golden`.

**Acceptance Scenarios**:

1. **Given** a golden resilience row, **When** the table is visible, **Then** the row with that `authority` has the same `score` and `status` (`green` or `yellow`). Extra authorities do not fail the test.
2. **Given** `filters`, **When** the test runs, **Then** each listed id is selected on its dropdown before any metric is read, and the later reading of that id shows the golden label. Extra slicers do not fail the test.
3. **Given** an authority cell whose `inner_text()` is `קרית מלאכי` followed by a newline and accessibility text, **When** the row is read, **Then** `authority` is `קרית מלאכי`.

### Edge Cases

- A thousands separator or a narrow no-break space inside a displayed integer still matches the YAML integer.
- A percentage string is not parsed into a float. `55%` does not match `55` or `0.55`.
- A resilience color that is neither green nor yellow does not get relabeled. The golden `green` or `yellow` fails.
- A KPI arrow that exists only as canvas pixels is not sampled. The trend comes back empty and the golden trend fails.
- The virtualized resilience table is scrolled until known authorities stop appearing. A golden authority that never appears fails.
- A resilience authority cell whose `inner_text()` has a later accessibility line publishes only the first line. The golden name stays the visible authority. The score cell is left whole.
- The landing screen is the screen `navigate()` already opens. This slice does not click a tab.
- `filters` is applied before the metric read. A parent slicer is listed before its child (`district` before `subdistrict`). An option that never appears fails inside the page timeout.
- A missing or empty `filters` map leaves the slicers as `navigate()` opened them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `HosenStatusPage.read_screen_1_metrics()` MUST return a dict whose keys are `survey_status`, `kpis`, `resilience_scores`, and `filters`, matching `hosen_dashboard.screen_1_landing`. The call MUST happen only after `filters` have been applied and the screen is idle.
- **FR-002**: `screen_1_landing.filters` MUST be applied before `read_screen_1_metrics()`. The test iterates that map and calls the page once per id. The page MUST resolve the combobox and call Layer 2 `Slicer.select`. Hebrew role names MUST stay on `pages/hosen_status/page.py`. The test body MUST NOT contain locators. A missing or empty map applies nothing. An unknown id fails the test.
- **FR-003**: The national card and each category card MUST be read through Layer 2 `KPI`. Each result MUST include `title`, `percentage`, and `trend`.
- **FR-004**: `ציון חוסן` rows MUST be collected with `collect_virtualized_rows`. The page-supplied visible-row reader MUST return `authority`, `score`, and `status`. `authority` MUST be the first line of that cell's `inner_text()`, after bidi marks and surrounding whitespace are removed. The score cell MUST NOT be split on newline.
- **FR-005**: Survey submitted count, total count, and missing-authority names MUST be read with Playwright locators on `HosenStatusPage`. Those locators MUST NOT move into `core/`.
- **FR-006**: The sanity test MUST load `data/hosen/db_sanity.yaml` and assert every key under `screen_1_landing`. Extra UI data MUST NOT fail the test.
- **FR-007**: YAML integers MUST match displayed integers with or without thousands separators. YAML strings MUST match displayed text exactly after bidi marks and outer whitespace are removed.
- **FR-008**: A visible section whose reader returns empty data while the golden block expects data MUST fail the test.
- **FR-009**: `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` MUST keep calling `dashboard.verify_freshness()` and MUST stay passing.
- **FR-010**: This slice MUST NOT add a comparison engine under `tests/helpers/`, MUST NOT add a warehouse client, and MUST NOT edit `core/`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' pages and tests.
- **FR-011**: Readers and the post-filter settle MUST wait with Playwright `expect` bounded by the page timeout. After each selection, and once more before the metric read, a visible report spinner MUST be expected hidden, then the Screen 1 ready locator MUST be expected visible. A spinner that is not showing is not a failure. The code MUST NOT call `sleep`, `wait_for_timeout`, or a network-idle wait, and it MUST NOT sample a canvas bitmap.
- **FR-012**: The golden file created by this slice MUST contain only values copied from the live landing screen. The test module and the page object MUST NOT embed those numbers.

### Key Entities

- **Screen 1 landing record**: `hosen_dashboard.screen_1_landing` in `data/hosen/db_sanity.yaml`. Nested objects: `survey_status`, `kpis`, `resilience_scores`, `filters`.
- **Survey status**: `submitted` (int), `total` (int), `missing_authorities` (list of authority names).
- **KPI card**: `title` (string), `percentage` (string, includes `%`), `trend` (`up`, `down`, or `flat`). `kpis.national_average` is one card. `kpis.categories` is a list of cards.
- **Resilience row**: `authority` (string), `score` (int when the cell is a whole number, otherwise the display string), `status` (`green` or `yellow`).
- **Filter**: English id to the Hebrew label that must be selected before the metric read. The live file uses `district` and `subdistrict`. The page maps each id to the combobox accessible name. The same map is read back after the screen is idle so `_assert_tree` can check the selection.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. This slice does not edit it. Freshness stays the inherited `verify_freshness()` path; the Hosen caption `מועד רענון` stays the existing page override.
- **AC-002**: `HosenStatusPage` MUST keep inheriting `ReportShell`. This slice MUST NOT re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: Report-ready state stays the existing locator for `תמ"צ ארצי - דיווחי קה"א יקל"ר` on the domain page.
- **AC-004**: `navigate` and `verify_freshness` keep their current contracts. `read_screen_1_metrics` is additive.
- **AC-005**: Layer 2 stays report-agnostic. This slice composes `Slicer`, `KPI`, and `collect_virtualized_rows`. It does not load the YAML from `core/` and does not add Hosen titles to `core/`.
- **AC-006**: The page object stays in `pages/hosen_status/page.py`. This slice adds no `db/clients/` module.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` applies `screen_1_landing.filters`, waits until Screen 1 is idle, then compares one live reading to `screen_1_landing` and fails with a YAML path when a golden key differs.
- **SC-002**: A golden integer matches a displayed `1,324` and a displayed `1324`. A golden percentage string matches only the same display text.
- **SC-003**: With a visible `ציון חוסן` table and a non-empty golden list, an empty row collection fails the test.
- **SC-004**: `pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` still passes through `verify_freshness()`.
- **SC-005**: The diff for this slice contains no edits under `core/`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' page and test modules. Fleet smoke is not a gate for this slice because Layer 0, Layer 2, and the fleet page are not edited.
- **SC-006**: With `filters.district` and `filters.subdistrict` set, the metric read used by `_assert_tree` is the reading taken after both dropdowns show those labels. An unfiltered read is not compared.

## Assumptions

- Screen 1 is the report `HosenStatusPage.navigate()` already opens. No page-rail click is required.
- The right-hand filters are Power BI dropdown slicers. The test selects the golden label before reading metrics. The selected label is then present in the combobox text.
- The national assessment and its category cards expose a title and a percentage as DOM text that `KPI` can address. The arrow is a non-canvas node inside that card.
- `ציון חוסן` is a virtualized grid or table whose row text and background color are available to a visible-row callback. The background is not painted only on a canvas.
- The top-left survey block exposes the two counts and the missing names as text nodes.
- Golden numbers are frozen from the live screen during implementation. This plan does not invent a warehouse figure.
- Subset comparison is implemented as private helpers in the Hosen sanity module. Those helpers are not a shared engine and are not imported from Hasbara, Credit, or Alerts.
