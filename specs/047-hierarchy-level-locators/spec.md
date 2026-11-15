# Feature Specification: Fix Hierarchy Level Locators

**Feature Branch**: `feature/reportportal-integration` (spec directory `047-hierarchy-level-locators`; git checkout stays put)

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Fix Hierarchy Level Locators (Custom UI Tabs). The hierarchy controls (`נפה`, `רשות`, `יישוב`) are custom, large visual tabs located directly above the district chart, not the native Power BI visual header drill-down arrows. The current tests skip because the locator strategy expects native controls or a strict `button` role, which fails against Power BI's custom DOM elements. Update `set_hierarchy_level` (or the skip-check logic) in `pages/alerts_analysis/population_page.py` to target these tabs by text, using a broader locator such as `get_by_text` with `exact=True` or `text='נפה'` (and the same for `רשות` and `יישוב`). Remove the premature `pytest.skip` that checks for the control not visible on the district chart when that check depends on native visual headers. Let Playwright's built-in wait handle the click. Comments inside functions stay in English."

## Clarifications

### Session 2026-11-04

- Q: Which git checkout should this slice use? → A: Spec directory `047-hierarchy-level-locators`. Planning does not switch the git checkout (`feature/reportportal-integration`). `.specify/feature.json` is repointed here. Sibling `046-credit-ui-validation` stays untouched.
- Q: Where does the text locator run? → A: On the report iframe (`_report_frame()`), which is the frame that hosts the Power BI visual. The outer browser page does not contain these tab labels.
- Q: Which spelling is the settlement tab? → A: `יישוב`, the label already stored in `_HIERARCHY_LEVEL_NAMES["yeshuv"]`. The brief's later `ישוב` is the same tab.
- Q: What happens when the tab text is absent? → A: The click waits with Playwright's actionability timeout and the test fails. It does not `pytest.skip` with "control not visible on district chart".
- Q: Which skip stays? → A: The later skip that runs only after a level was selected and `read_district_labels()` returns no rows. That guard is about an empty chart, not about a missing native header control.
- Q: Does the click stay a force click? → A: No. Feature 045 force-clicked a role-matched header control because the visual header toolbar intercepted the pointer. These tabs are the large labels above the chart. A normal click lets Playwright wait until the text can receive the pointer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hierarchy tabs are selected by their labels (Priority: P1)

A validation author runs a nafa, rashut, or yeshuv sanity test. `set_hierarchy_level` clicks the custom tab whose visible text is exactly `נפה`, `רשות`, or `יישוב`. The click does not require a `button`, `tab`, or `option` role, and it does not require the label to sit inside the district visual's native header.

**Why this priority**: The six hierarchy tests skip today because the role lookup inside the visual container never sees these custom tabs.

**Independent Test**: Run `test_hierarchy_nafa_matches_db`. The page clicks the `נפה` label, the district title becomes `התרעות לפי נפה`, and the test reaches the golden comparison.

**Acceptance Scenarios**:

1. **Given** Screen 2 is showing the district chart, **When** `set_hierarchy_level("nafa")` runs, **Then** it clicks the exact text `נפה` in the report iframe.
2. **Given** the same screen, **When** `set_hierarchy_level("rashut")` or `set_hierarchy_level("yeshuv")` runs, **Then** it clicks the exact text `רשות` or `יישוב` the same way.
3. **Given** the tab is a custom element with no `button` role, **When** the level is selected, **Then** the click still happens.
4. **Given** the tab sits above the district chart and outside the native visual-header arrows, **When** the level is selected, **Then** the lookup still finds the label.
5. **Given** the click is issued, **When** Playwright has not yet painted the label, **Then** the click waits until the label is actionable. The method does not probe visibility and return before that wait.

---

### User Story 2 - A missing tab fails the test (Priority: P1)

A validation author runs the same hierarchy tests when the tab text cannot be clicked. The test fails. It does not skip with "Hierarchy level … control not visible on district chart".

**Why this priority**: That skip treats a locator miss as "chart not rendered" and hides the broken lookup.

**Independent Test**: With the skip removed, a hierarchy test whose tab click times out is reported as a failure.

**Acceptance Scenarios**:

1. **Given** `_assert_hierarchy_sum` or `_assert_hierarchy_daily_avg`, **When** the level is requested, **Then** the helper does not call `pytest.skip` for a control that is not visible on the district chart.
2. **Given** `set_hierarchy_level` returns false after the click (the drilled title never appears), **When** the helper continues, **Then** the test fails on that result.
3. **Given** the tab click exceeds the page timeout, **When** Playwright raises, **Then** that error fails the test.

---

### User Story 3 - An empty drilled chart still skips (Priority: P2)

A validation author selects a hierarchy level and the district reader returns no rows. The existing empty-chart skip still applies.

**Why this priority**: The brief removes the locator skip. It leaves the empty-read guard in place.

**Independent Test**: After a successful level selection, an empty `read_district_labels()` result still skips with the existing "returned no rows" reason.

**Acceptance Scenarios**:

1. **Given** `set_hierarchy_level` succeeded, **When** `read_district_labels()` is empty, **Then** the helper skips with the existing per-level empty-chart reason.
2. **Given** the reader returns rows, **When** they are compared, **Then** `_assert_golden_keys` still runs against the golden `alerts_by_hierarchy` block.

---

### Edge Cases

- An unknown level string (`set_hierarchy_level` only accepts `nafa`, `rashut`, and `yeshuv`) still returns false and the helper fails the test. No tab is clicked.
- Exact text match ignores a longer phrase such as the retitled chart `התרעות לפי נפה`.
- The settlement label is `יישוב`. A locator for `ישוב` is out of scope.
- Several nodes can carry the same exact label. The click uses the first match in the report iframe and still waits for that node.
- Custom tabs may omit `aria-pressed` and `aria-selected`. The existing "no selection attribute" path still counts as selected, and the district title wait remains the confirmation.
- `מחוז` is the base level. This slice does not add a tab click for it.
- `set_district_aggregation` stays a separate click.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `set_hierarchy_level` MUST locate `נפה`, `רשות`, and `יישוב` by exact text inside the report iframe.
- **FR-002**: That lookup MUST accept a custom element. It MUST NOT require role `button`, `tab`, or `option`.
- **FR-003**: That lookup MUST find the tabs that sit above the district chart. It MUST NOT require the label to be a native visual-header drill control or a descendant of the district visual container.
- **FR-004**: The click MUST be a normal Playwright click so the built-in actionability wait runs. The method MUST NOT return before the click because a role or container probe found nothing, and it MUST NOT force-click this tab.
- **FR-005**: `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg` MUST NOT `pytest.skip` with the "control not visible on district chart" reason.
- **FR-006**: A click timeout, or a false return after the click, MUST fail the calling test.
- **FR-007**: The empty-chart `pytest.skip` after `read_district_labels()` MUST stay, with its current reason text.
- **FR-008**: `set_hierarchy_level` MUST keep the return type `bool`. It records `_active_hierarchy_level` and waits for the retitled district chart (`התרעות לפי ` plus the level name) on success.
- **FR-009**: Comments inside the touched functions MUST be English.
- **FR-010**: `data/alerts/db_sanity_am_kalavi.yaml`, `core/`, `db/`, and page objects for other reports MUST stay unchanged.

### Key Entities

- **Hierarchy tab**: A custom label above the district chart. The visible text is exactly `נפה`, `רשות`, or `יישוב`. It maps to level keys `nafa`, `rashut`, and `yeshuv`.
- **Hierarchy level**: The active district grain. It starts at `mahoz` and becomes `nafa`, `rashut`, or `yeshuv` after a successful tab click. The district title is `התרעות לפי ` plus the Hebrew name.
- **Golden hierarchy block**: `metrics.alerts_by_hierarchy.<level>.sum` and `.daily_avg` in the alerts sanity YAML. This slice reads those blocks and does not edit them.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) stays report-agnostic. The Hebrew tab labels stay on `AlertsPopulationPage`.
- **AC-002**: `AlertsPopulationPage` keeps inheriting the alerts page and `ReportShell`. Login, catalog search, iframe wait, and last-refresh verification stay on the shell.
- **AC-003**: Report-ready state stays the domain locator already used by this page.
- **AC-004**: `set_hierarchy_level(level: str) -> bool` keeps that signature. The sanity helpers change in the same slice so a false return fails the test.
- **AC-005**: Layer 2 (`core/components/`) is not edited. The tab locator is report-specific and stays on the alerts page.
- **AC-006**: The only page edit is `pages/alerts_analysis/population_page.py`. The only test edit is `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, `test_hierarchy_yeshuv_matches_db`, and the three daily-average twins no longer skip with "control not visible on district chart" when the custom tabs are on screen.
- **SC-002**: A missing tab is a failed test (Playwright timeout or an assertion on the false return), not a skip.
- **SC-003**: An empty district read after a successful selection still skips with the existing "returned no rows" reason.
- **SC-004**: The clicked label, the stored level, and the district title stay aligned: `nafa`/`נפה`/`התרעות לפי נפה`, and the same pattern for `רשות` and `יישוב`.
- **SC-005**: Fleet smoke is unchanged because `core/` and the fleet page are unchanged. This slice does not add a fleet run as a gate.

## Assumptions

- The custom tabs render the three Hebrew words as their own text nodes inside the report iframe, above the district chart.
- The page timeout already set on `AlertsPopulationPage` (120 seconds) is the wait Playwright uses for the click.
- Golden YAML comparisons, quote folding, hour-chart teardown, and district aggregation stay as they are.
- Feature 045's force-click applied to a role-matched header control. This slice replaces that click target and that click mode for `set_hierarchy_level` only.
