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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Landing screen matches the golden YAML (Priority: P1)

A validation author opens תמ"צ חוסן on the landing screen (no tab change) and compares survey status, KPI cards, the resilience table, and the selected filters to `hosen_dashboard.screen_1_landing`.

**Why this priority**: Screen 1 is the only surface in this slice. A drift in any of the four blocks is the defect the suite exists to catch.

**Independent Test**: `test_hosen_screen1_matches_golden` opens the report through `hosen_status_dashboard`, calls `read_screen_1_metrics()`, and walks `screen_1_landing`.

**Acceptance Scenarios**:

1. **Given** the landing screen is ready, **When** the suite reads Screen 1, **Then** the returned dict has `survey_status`, `kpis`, `resilience_scores`, and `active_filters`.
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

A validation author reads the `ציון חוסן` table (authority, score, green or yellow status) and the right-hand filters that are already selected.

**Why this priority**: The table is the per-authority score, and the filters define which slice of the country the other numbers describe.

**Independent Test**: The `resilience_scores` list and the `active_filters` map inside `test_hosen_screen1_matches_golden`.

**Acceptance Scenarios**:

1. **Given** a golden resilience row, **When** the table is visible, **Then** the row with that `authority` has the same `score` and `status` (`green` or `yellow`). Extra authorities do not fail the test.
2. **Given** `active_filters`, **When** the right-hand slicers are read, **Then** each listed id shows its golden label. The test does not click the slicer. Extra slicers do not fail the test.

### Edge Cases

- A thousands separator or a narrow no-break space inside a displayed integer still matches the YAML integer.
- A percentage string is not parsed into a float. `55%` does not match `55` or `0.55`.
- A resilience color that is neither green nor yellow does not get relabeled. The golden `green` or `yellow` fails.
- A KPI arrow that exists only as canvas pixels is not sampled. The trend comes back empty and the golden trend fails.
- The virtualized resilience table is scrolled until known authorities stop appearing. A golden authority that never appears fails.
- The landing screen is the screen `navigate()` already opens. This slice does not click a tab.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `HosenStatusPage.read_screen_1_metrics()` MUST return a dict whose keys are `survey_status`, `kpis`, `resilience_scores`, and `active_filters`, matching `hosen_dashboard.screen_1_landing`.
- **FR-002**: Selected filter labels MUST be read through Layer 2 `Slicer` (`control` plus the control's displayed text). Hebrew role names MUST stay on `pages/hosen_status/page.py`. The test MUST NOT change a slicer selection.
- **FR-003**: The national card and each category card MUST be read through Layer 2 `KPI`. Each result MUST include `title`, `percentage`, and `trend`.
- **FR-004**: `ציון חוסן` rows MUST be collected with `collect_virtualized_rows`. The page-supplied visible-row reader MUST return `authority`, `score`, and `status`.
- **FR-005**: Survey submitted count, total count, and missing-authority names MUST be read with Playwright locators on `HosenStatusPage`. Those locators MUST NOT move into `core/`.
- **FR-006**: The sanity test MUST load `data/hosen/db_sanity.yaml` and assert every key under `screen_1_landing`. Extra UI data MUST NOT fail the test.
- **FR-007**: YAML integers MUST match displayed integers with or without thousands separators. YAML strings MUST match displayed text exactly after bidi marks and outer whitespace are removed.
- **FR-008**: A visible section whose reader returns empty data while the golden block expects data MUST fail the test.
- **FR-009**: `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` MUST keep calling `dashboard.verify_freshness()` and MUST stay passing.
- **FR-010**: This slice MUST NOT add a comparison engine under `tests/helpers/`, MUST NOT add a warehouse client, and MUST NOT edit `core/`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' pages and tests.
- **FR-011**: Readers MUST wait with Playwright `expect` bounded by the page timeout. They MUST NOT call `sleep`, `wait_for_timeout`, or a network-idle wait, and they MUST NOT sample a canvas bitmap.
- **FR-012**: The golden file created by this slice MUST contain only values copied from the live landing screen. The test module and the page object MUST NOT embed those numbers.

### Key Entities

- **Screen 1 landing record**: `hosen_dashboard.screen_1_landing` in `data/hosen/db_sanity.yaml`. Nested objects: `survey_status`, `kpis`, `resilience_scores`, `active_filters`.
- **Survey status**: `submitted` (int), `total` (int), `missing_authorities` (list of authority names).
- **KPI card**: `title` (string), `percentage` (string, includes `%`), `trend` (`up`, `down`, or `flat`). `kpis.national_average` is one card. `kpis.categories` is a list of cards.
- **Resilience row**: `authority` (string), `score` (int when the cell is a whole number, otherwise the display string), `status` (`green` or `yellow`).
- **Active filter**: English id to selected Hebrew label. The landing examples are a district and a sub-district. The live accessible names decide the ids that are written.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. This slice does not edit it. Freshness stays the inherited `verify_freshness()` path; the Hosen caption `מועד רענון` stays the existing page override.
- **AC-002**: `HosenStatusPage` MUST keep inheriting `ReportShell`. This slice MUST NOT re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: Report-ready state stays the existing locator for `תמ"צ ארצי - דיווחי קה"א יקל"ר` on the domain page.
- **AC-004**: `navigate` and `verify_freshness` keep their current contracts. `read_screen_1_metrics` is additive.
- **AC-005**: Layer 2 stays report-agnostic. This slice composes `Slicer`, `KPI`, and `collect_virtualized_rows`. It does not load the YAML from `core/` and does not add Hosen titles to `core/`.
- **AC-006**: The page object stays in `pages/hosen_status/page.py`. This slice adds no `db/clients/` module.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` compares one live Screen 1 reading to `screen_1_landing` and fails with a YAML path when a golden key differs.
- **SC-002**: A golden integer matches a displayed `1,324` and a displayed `1324`. A golden percentage string matches only the same display text.
- **SC-003**: With a visible `ציון חוסן` table and a non-empty golden list, an empty row collection fails the test.
- **SC-004**: `pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` still passes through `verify_freshness()`.
- **SC-005**: The diff for this slice contains no edits under `core/`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' page and test modules. Fleet smoke is not a gate for this slice because Layer 0, Layer 2, and the fleet page are not edited.

## Assumptions

- Screen 1 is the report `HosenStatusPage.navigate()` already opens. No page-rail click is required.
- The right-hand filters are Power BI dropdown slicers whose selected label is present in the combobox text.
- The national assessment and its category cards expose a title and a percentage as DOM text that `KPI` can address. The arrow is a non-canvas node inside that card.
- `ציון חוסן` is a virtualized grid or table whose row text and background color are available to a visible-row callback. The background is not painted only on a canvas.
- The top-left survey block exposes the two counts and the missing names as text nodes.
- Golden numbers are frozen from the live screen during implementation. This plan does not invent a warehouse figure.
- Subset comparison is implemented as private helpers in the Hosen sanity module. Those helpers are not a shared engine and are not imported from Hasbara, Credit, or Alerts.
