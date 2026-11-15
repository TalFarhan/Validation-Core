# Feature Specification: Fix Skipped Hierarchy Tests and Navigation Errors for Alerts Analysis

**Feature Branch**: `feature/reportportal-integration` (spec directory `043-alerts-analysis-fixes`; git checkout stays put)

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Resolve the ERROR (LoadTimeout) and SKIPPED results in the Alerts Analysis dashboard UI tests. The failures are caused by bilingual accessibility names, hardcoded dynamic titles, and unhandled listbox DOM structures. Do NOT touch the fleet or status picture modules. (1) Bilingual Locators: update the locators in population_page.py for page navigation and date fields to use Playwright `.or_()` supporting Hebrew and English (`ניווט בין עמודים`/`Page navigation`, `תאריך התחלה`/`Start date`). (2) Dynamic Chart Titles: remove the hardcoded `DISTRICT_CHART = 'התרעות לפי מחוז'` constant; refactor `set_hierarchy_level` and related functions to dynamically evaluate the expected title from the active hierarchy level (`'התרעות לפי ' + level_name`). (3) Refactor Data Extraction: the bar chart renders data in a listbox DOM rather than rows or SVG aria-labels, so `read_district_labels` and `read_hour_buckets` return empty; update them to map the category listbox to the 'התרעות' listbox OR use the Right-click → Show as a table fallback (already used by the dates chart). (4) Resolve Skipped Tests: allow all `test_hierarchy_*` and `test_alerts_by_hour_*` tests to extract data and pass without `pytest.skip`. (5) All in-function code comments in English only."

## Clarifications

### Session 2026-11-02

- Q: Why do the Alerts Analysis UI tests ERROR with `LoadTimeout`? → A: `AlertsPopulationPage.before_report_ready_check` opens Screen 2 through the page-rail control located only by the Hebrew accessible name `ניווט בין עמודים`, and `set_between_dates` fills the date fields only by the Hebrew aria-label prefixes `תאריך התחלה` / `תאריך סיום`. When Power BI renders those accessibility names in English (`Page navigation`, `Start date`, `End date`), the locator never resolves, page-switch/date entry never completes, and the report-ready wait raises `LoadTimeoutError`.
- Q: Why do `test_hierarchy_*` and `test_alerts_by_hour_*` skip? → A: `read_district_labels` and `read_hour_buckets` return empty dictionaries. The district/hour bar visuals render as a Power BI `listbox` of options rather than the grid rows (`role="row"`) or SVG `aria-label` marks those readers expect, so every read path (`_scrolled_district_rows`, `_labeled_mark_values`, `_aria_labels`, tooltip hover) yields nothing and the tests hit `pytest.skip(...)`.
- Q: Why does the district chart title break drill-down? → A: `DISTRICT_CHART = "התרעות לפי מחוז"` is a module constant used as the chart anchor by `before_report_ready_check`, `set_district_aggregation`, `_hierarchy_control`, `set_hierarchy_level`, `chart_total`, `read_district_labels`, and `_district_visible_total`. When a hierarchy level is selected, Power BI retitles the visual to `התרעות לפי נפה` / `התרעות לפי רשות` / `התרעות לפי יישוב`, so the hardcoded constant no longer matches and `_visual_container` cannot find the drilled-down chart.
- Q: How should the title become dynamic? → A: Replace the constant with an accessor that evaluates `"התרעות לפי " + level_name` from the active hierarchy level (`מחוז` at the base level, then `נפה` / `רשות` / `יישוב`). `set_hierarchy_level` records the active level; every reader that anchored on `DISTRICT_CHART` now asks the accessor for the current expected title. The three test references to the removed constant are updated in the same change to use the accessor's base-level title.
- Q: How should the listbox data be extracted? → A: Add a listbox-aware read path to `read_district_labels` and `read_hour_buckets`. Either (a) pair the category `listbox` options with the `התרעות` series `listbox` options in draw order, or (b) reuse the Right-click → "Show as a table" fallback already used by the dates chart (`read_date_counts` / `_dates_table_total` via `_click_show_as_table` / `_alert_column_table` / `_collect_scrolled_rows`). The show-as-table fallback is the primary strategy because it is already proven on Screen 2.
- Q: Should the golden YAML values change? → A: No. `data/alerts/db_sanity_am_kalavi.yaml` stays the source of truth (Constitution V/VII). The fix is in the page-object locators and readers, not the golden numbers. Skip guards remain as a safety net for a genuinely absent control.
- Q: Which modules are off-limits? → A: No fleet module (`pages/fleet_dashboard/`, `tests/**/fleet_dashboard/`), no status-picture module (`pages/status_picture/`, `tests/**/status_picture_dashboard/`), no `core/portal`, and no `core/components`. All edits stay on the alerts domain page object and the alerts test package.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Page navigation and date entry survive an English render (Priority: P1)

A validation author runs the Alerts Analysis suite while Power BI serves the report with English accessibility names. The page-rail switch to Screen 2 and the start/end date fields still resolve, so the report-ready wait completes instead of raising `LoadTimeoutError`.

**Why this priority**: These are the `ERROR` results. If the page cannot switch to Screen 2 or fill the dates, no population metric is reachable and every downstream test errors.

**Independent Test**: Run `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` with the report forced to English accessibility names. The suite opens Screen 2 and applies a date range with no `LoadTimeoutError`.

**Acceptance Scenarios**:

1. **Given** the page-rail control is exposed with the English name `Page navigation`, **When** `before_report_ready_check` runs, **Then** the bilingual `.or_()` locator matches it and Screen 2 opens.
2. **Given** the date fields carry the English aria-labels `Start date` / `End date`, **When** `set_between_dates` runs, **Then** the bilingual `.or_()` locator fills both and the total card settles.
3. **Given** the Hebrew names are rendered, **When** the same methods run, **Then** the Hebrew side of each `.or_()` still matches (behavior preserved).

---

### User Story 2 - District chart title follows drill-down (Priority: P1)

A validation author drills the district chart from מחוז down to נפה / רשות / יישוב. Each reader anchors on the live title (`התרעות לפי <level>`) rather than a hardcoded `התרעות לפי מחוז`, so `_visual_container` finds the retitled chart and reads its data.

**Why this priority**: The hierarchy tests select a level and then read the chart; after a drill-down the hardcoded title no longer exists, so the container lookup fails and the read returns empty.

**Independent Test**: Run `test_hierarchy_nafa_matches_db` / `test_hierarchy_rashut_matches_db` / `test_hierarchy_yeshuv_matches_db`. After each level selection the reader locates the retitled chart and returns the level's rows.

**Acceptance Scenarios**:

1. **Given** the base district chart, **When** the title accessor is asked at the base level, **Then** it returns `התרעות לפי מחוז`.
2. **Given** `set_hierarchy_level("nafa")` succeeded, **When** a district reader runs, **Then** it anchors on `התרעות לפי נפה` and finds the container.
3. **Given** the module constant `DISTRICT_CHART` is removed, **When** the smoke and unit tests reference the district title, **Then** they use the accessor's base-level title and still pass.

---

### User Story 3 - Listbox district and hour data is extracted (Priority: P1)

A validation author reads the district and hour charts. When the visual renders as a Power BI `listbox` rather than grid rows or SVG marks, `read_district_labels` and `read_hour_buckets` still return the name→count mapping instead of an empty dictionary.

**Why this priority**: These empty reads are the direct cause of the `SKIPPED` results. Without a listbox-aware path the hierarchy and hour tests can never reach their assertions.

**Independent Test**: Run `test_hierarchy_mahoz_sum_matches_db`, `test_hierarchy_mahoz_daily_avg_matches_db`, `test_alerts_by_hour_sum_matches_db`, and `test_alerts_by_hour_daily_avg_matches_db`. Each returns a non-empty mapping that matches the golden record.

**Acceptance Scenarios**:

1. **Given** the district visual renders as a `listbox`, **When** `read_district_labels` runs, **Then** it pairs the category options with the `התרעות` series options (or reads the Show-as-a-table fallback) and returns district→count.
2. **Given** the hour visual renders as a `listbox`, **When** `read_hour_buckets` runs, **Then** it returns hour→count by the same strategy.
3. **Given** a control is genuinely absent, **When** the readers return nothing, **Then** the existing `pytest.skip` guard still fires (behavior preserved).

---

### User Story 4 - Skipped hierarchy and hour tests become real assertions (Priority: P1)

The locator, title, and listbox fixes remove the empty-read `pytest.skip` paths for the `test_hierarchy_*` and `test_alerts_by_hour_*` tests; the skip guards remain only as a safety net for a genuinely absent control.

**Why this priority**: The request explicitly asks that the fixes turn skips into passing assertions, not that the skip guards be deleted.

**Independent Test**: Run `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. The `test_hierarchy_*` and `test_alerts_by_hour_*` tests report pass/fail (not skip) when data is present; guards still fire if a control is truly missing.

**Acceptance Scenarios**:

1. **Given** data is present, **When** the hierarchy and hour tests run, **Then** none skip with an empty-read message.
2. **Given** a control is genuinely absent, **When** a reader returns nothing, **Then** the existing skip guard still fires (behavior preserved).

---

### Edge Cases

- A date or page-rail control rendered only in English must still resolve through the `.or_()` Hebrew/English locator.
- A district chart drilled to a lower level must be found by its live title, not the removed `התרעות לפי מחוז` constant.
- A visual that renders as a `listbox` must expose both the category options and the `התרעות` series options, or the Show-as-a-table fallback must open.
- A genuinely empty or unrendered chart still skips with its descriptive guard message.
- The fleet and status-picture modules, `core/`, and the golden YAML values are not edited.
- Comments inside new or edited functions are English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `AlertsPopulationPage` page-rail navigation MUST locate the page-switch control by a bilingual `.or_()` condition over `ניווט בין עמודים` and `Page navigation`, so Screen 2 opens whether Power BI renders Hebrew or English accessibility names.
- **FR-002**: `set_between_dates` MUST fill the start and end date fields through a bilingual `.or_()` condition over `תאריך התחלה` / `Start date` and `תאריך סיום` / `End date`; the Hebrew side MUST keep working when Hebrew is rendered.
- **FR-003**: The module constant `DISTRICT_CHART = "התרעות לפי מחוז"` MUST be removed and replaced with an accessor that evaluates the expected district-chart title as `"התרעות לפי " + level_name` from the active hierarchy level (`מחוז` base level, then `נפה` / `רשות` / `יישוב`).
- **FR-004**: `set_hierarchy_level` MUST record the selected level, and every reader that anchored on `DISTRICT_CHART` (`before_report_ready_check`, `set_district_aggregation`, `_hierarchy_control`, `chart_total`, `read_district_labels`, `_district_visible_total`) MUST anchor on the dynamic title accessor instead.
- **FR-005**: `read_district_labels` MUST return the district→count mapping when the visual renders as a Power BI `listbox`, by pairing the category `listbox` options with the `התרעות` series `listbox` options, or by using the Right-click → "Show as a table" fallback already used by the dates chart.
- **FR-006**: `read_hour_buckets` MUST return the hour→count mapping when the hour visual renders as a `listbox`, by the same listbox-pairing or Show-as-a-table strategy.
- **FR-007**: After the fixes, every `test_hierarchy_*` and `test_alerts_by_hour_*` test in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` MUST report pass/fail rather than skip when data is present, while the existing `pytest.skip` guards remain as a safety net for a genuinely absent control.
- **FR-008**: This slice MUST NOT edit any fleet module (`pages/fleet_dashboard/`, `tests/**/fleet_dashboard/`), any status-picture module (`pages/status_picture/`, `tests/**/status_picture_dashboard/`), `core/portal`, or `core/components`.
- **FR-009**: The golden record `data/alerts/db_sanity_am_kalavi.yaml` metric values MUST NOT change.
- **FR-010**: The three test references to the removed `DISTRICT_CHART` constant (`tests/ui/alerts_analysis_dashboard/test_population_invariants.py`, `tests/ui/alerts_analysis_dashboard/population_snapshot.py`, `tests/unit/test_population_page.py`) MUST be updated in the same change to use the dynamic title accessor at the base level, and the alerts UI smoke suite MUST stay green.
- **FR-011**: Comments inside new or edited functions MUST be English.

### Key Entities

- **Bilingual locator**: A Playwright `.or_()` over the Hebrew and English accessible name / aria-label for one control (page-rail switch, start date, end date).
- **District title accessor**: A method that returns `"התרעות לפי " + level_name` for the active hierarchy level, replacing the removed `DISTRICT_CHART` constant.
- **Hierarchy level state**: The active district level (`mahoz` / `nafa` / `rashut` / `yeshuv`) recorded by `set_hierarchy_level` and read by the title accessor.
- **Listbox reading**: The category and `התרעות` series `listbox` option pairs, or the Show-as-a-table grid, that `read_district_labels` / `read_hour_buckets` parse into a name→count mapping.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` are NOT edited. All locator, title, and listbox logic stays on the alerts domain page, as the constitution requires for report tables, tooltips, and drilldowns.
- **AC-002**: `AlertsPopulationPage` keeps inheriting `AlertsAnalysisPage` → `ReportShell`. No portal step is added or removed.
- **AC-003**: Public reader names and return types on the alerts page (`read_card`, `chart_total`, `read_settlement_warned`, `read_date_counts`, `read_district_labels`, `read_hour_buckets`, `read_hour_daily_avg`, `set_hierarchy_level`, `set_district_aggregation`, `set_between_dates`, `set_date_range`) are unchanged; any new helper (title accessor, listbox reader) is private and additive. The one public surface change is the removal of the `DISTRICT_CHART` class constant, replaced by an accessor, with its three test references updated in the same change.
- **AC-004**: `core/` does not load `data/alerts/`. The alerts tests load the golden file.
- **AC-005**: No new report page and no new SQL client; `db/clients/alerts.py` is unchanged.
- **AC-006**: The alerts domain page object stays at `pages/alerts_analysis/population_page.py`; alerts sanity logic stays under `tests/sanity/alerts_analysis_dashboard/` and alerts UI logic under `tests/ui/alerts_analysis_dashboard/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the report served in English accessibility names, the alerts UI suite opens Screen 2 and applies a date range with no `LoadTimeoutError`; with Hebrew names it still works.
- **SC-002**: After a district drill-down, the district readers anchor on the live `התרעות לפי <level>` title and return a non-empty mapping.
- **SC-003**: `read_district_labels` and `read_hour_buckets` return non-empty mappings when the visual renders as a `listbox`.
- **SC-004**: With auth, every `test_hierarchy_*` and `test_alerts_by_hour_*` test reports pass/fail (not skip) and matches the golden record; a genuinely absent control still skips with its guard message.
- **SC-005**: The alerts UI smoke suite (`tests/ui/alerts_analysis_dashboard/`) passes after the page-object edits.
- **SC-006**: No fleet/status-picture module, `core/`, or golden YAML metric value is edited.

## Assumptions

- The page-rail switch and the date fields expose a stable Hebrew-or-English accessible name / aria-label; the `.or_()` locator covers both without a third variant.
- The district and hour visuals either expose a category `listbox` alongside the `התרעות` series `listbox` in draw order, or support the Right-click → "Show as a table" menu that the dates chart already uses.
- The active hierarchy level is known to the page object because `set_hierarchy_level` is the only control that changes it; the base level is `מחוז`.
- Portal auth is required to run the UI tests; this spec does not run the browser.
- `self.timeout` on the population page is `120_000`, inherited from `ReportShell`/`BasePage`, and is a sufficient overall render budget.
