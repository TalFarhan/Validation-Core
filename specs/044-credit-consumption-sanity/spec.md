# Feature Specification: Credit Consumption Dashboard UI Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `044-credit-consumption-sanity`; git checkout stays put)

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Create a new feature branch (e.g., 044-credit-consumption-sanity) to build the Page Objects and UI Sanity tests for the new Credit Consumption Dashboard (`credit_consumption_dashboard`). Leverage the robust UI extraction strategies (Show as a table, bilingual locators) established in recent fixes. Do NOT touch existing alerts, status picture, or fleet modules. (1) Create Page Objects: implement `credit_consumption_page.py` handling both Screen 1 (Summary) and Screen 2 (Data Export). Use Playwright `.or_()` for bilingual accessibility names (page navigation and date filters) to prevent `LoadTimeoutError`. (2) Handle Dynamic Toggles (Screen 1): switch between metrics (Expense Amount vs. Transactions Count) and visualization types (Line vs. Bar). Extract chart data using Right-click → Show as a table. Map results to `daily_trends_by_toggle`. (3) Extract KPIs and tables: KPI cards (`kpi_metrics`), Authority chart (`expenses_by_authority_millions`), and Screen 2 raw data matrix (`export_table_data`). (4) Create Test Suite: `tests/sanity/credit_consumption_dashboard/test_data_validation.py`. The setup/fixture must read `active_filters` from the golden YAML (e.g. `time_range: \"פורים 2026\"`) and apply them in the UI before asserting all metrics, trends, and table exports against the Golden Record. (5) Code comments inside functions are English only."

## Clarifications

### Session 2026-11-02

- Q: Which git checkout should this slice use? → A: Spec directory `044-credit-consumption-sanity`. Planning does not switch the git checkout (`feature/reportportal-integration`), matching 019/035/039/043. `.specify/feature.json` is repointed to this directory.
- Q: Where does the page object live? → A: Implementation is `pages/credit_consumption/credit_consumption_page.py` (class `CreditConsumptionPage`). The existing Layer 0 binding at `pages/credit_consumption/page.py` becomes a re-export so `tests/ui/credit_consumption_dashboard/conftest.py` keeps `from pages.credit_consumption.page import CreditConsumptionPage`. Popup dismiss, catalog search `צריכת אשראי`, and ready visual `ממוצע הוצאות לקנייה בשגרה` stay on the class.
- Q: What is the source of truth? → A: Golden record `data/credit/db_sanity_purim2026.yaml` under `credit_consumption_dashboard`. Metric values are not changed. No warehouse client and no `db/clients/credit.py` in this slice.
- Q: How are Screen 1 daily trends extracted? → A: Primary strategy is Right-click → bilingual "Show as a table" (`הצג כטבלה` / `Show as a table`), the same Power BI fallback proven on Alerts Analysis. SVG/tooltip reads are not the assertion path. Results map to the four `daily_trends_by_toggle` keys.
- Q: How do bilingual locators work? → A: Playwright `.or_()` over Hebrew and English accessible names for the page-rail (`ניווט בין עמודים` / `Page navigation`) and date fields (`תאריך התחלה` / `Start date`, `תאריך סיום` / `End date`). Prevents `LoadTimeoutError` when Power BI renders English chrome.
- Q: Which modules are off-limits? → A: No alerts (`pages/alerts_analysis/`, `tests/**/alerts_analysis_dashboard/`), no status-picture (`pages/status_picture/`, `tests/**/status_picture_dashboard/`), no fleet (`pages/fleet_dashboard/`, `tests/**/fleet_dashboard/`), no `core/portal`, no `core/components`. Root `conftest.py` is not edited.
- Q: What does the fixture apply? → A: Load `active_filters` from the golden YAML and apply non-`הכל` values in the UI (Screen 1: `time_range: "פורים 2026"`; Screen 2: `top_bar.period: "פורים 2026"`) before any metric assertion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open both screens under Hebrew or English chrome (Priority: P1)

A validation author opens the Credit Consumption report. The info overlay is dismissed, Screen 1 becomes ready, and the page-rail switch to Screen 2 still resolves when Power BI serves English accessibility names, so navigation does not raise `LoadTimeoutError`.

**Why this priority**: Without a bilingual page-rail and a stable ready visual, no KPI, trend, or export assertion can run.

**Independent Test**: Credit smoke (`test_dashboard_updated_within_24_hours`) stays green. A sanity fixture opens Screen 1; a Screen 2 test switches via the bilingual page-rail and lands on the export title.

**Acceptance Scenarios**:

1. **Given** the catalog product `צריכת אשראי`, **When** `CreditConsumptionPage.navigate` runs, **Then** the info overlay is dismissed if present and the ready visual `ממוצע הוצאות לקנייה בשגרה` is visible.
2. **Given** the page-rail control is named `Page navigation`, **When** the suite opens Screen 2, **Then** the bilingual `.or_()` locator matches it and the export page title is visible.
3. **Given** the Hebrew name `ניווט בין עמודים` is rendered, **When** the same switch runs, **Then** the Hebrew side of the `.or_()` still matches.

---

### User Story 2 - Golden filters are applied before every assertion (Priority: P1)

A validation author runs the sanity suite. The fixture (or a shared setup helper) reads `active_filters` from `data/credit/db_sanity_purim2026.yaml` and applies the non-default values in the UI, including `time_range: "פורים 2026"` on Screen 1 and `top_bar.period: "פורים 2026"` on Screen 2.

**Why this priority**: The golden numbers are a snapshot of that period. Asserting against the unfiltered landing page would be a false failure.

**Independent Test**: Every Screen 1 test applies Screen 1 `active_filters` before reading; every Screen 2 test applies Screen 2 `active_filters` after the page switch.

**Acceptance Scenarios**:

1. **Given** Screen 1 `active_filters.time_range` is `פורים 2026`, **When** setup runs, **Then** that period is selected in the UI and values of `הכל` are left as the default (not re-clicked).
2. **Given** Screen 2 `active_filters.top_bar.period` is `פורים 2026`, **When** the export tests run, **Then** that period is selected on Screen 2 before the matrix is read.
3. **Given** a date field is present, **When** it is filled, **Then** the locator is a bilingual `.or_()` over `תאריך התחלה` / `Start date` and `תאריך סיום` / `End date`.

---

### User Story 3 - KPI cards match the golden record (Priority: P1)

A validation author, after the golden filters, reads the Screen 1 KPI cards and compares them to `kpi_metrics`.

**Why this priority**: The cards are the summary contract for the Purim 2026 window.

**Independent Test**: `test_kpi_metrics_match_golden` calls `read_kpi_metrics()` and asserts every golden key.

**Acceptance Scenarios**:

1. **Given** Screen 1 filters are applied, **When** the KPI cards are read, **Then** `num_population` equals `10006812`.
2. **Given** the same state, **When** routine and selected-range expense cards are read, **Then** they match `average_purchase_expense_routine` and `average_purchase_expense_selected_range` (including nested physical / online / total).
3. **Given** the same state, **When** the change-vs-routine cards are read, **Then** the percent strings match `average_change_percentage_vs_routine` (`"3.23%"`, `"4.23%"`).

---

### User Story 4 - Daily trends follow the four toggle combinations (Priority: P1)

A validation author switches metric (Expense Amount vs. Transactions Count) and visualization (Line vs. Bar), then extracts each chart through Right-click → Show as a table. The four result lists match `daily_trends_by_toggle`.

**Why this priority**: Toggle state is the only way to reach all four golden series. SVG/tooltip reads are known-flaky on this portal.

**Independent Test**: `test_daily_trends_match_golden` iterates the four YAML keys, sets the matching toggles, reads via show-as-table, and compares rows (date, day, value / values).

**Acceptance Scenarios**:

1. **Given** Expense Amount + Line, **When** the chart is opened as a table, **Then** the rows match `expense_amount_line` (scalar `value` per date).
2. **Given** Transactions Count + Line, **When** the chart is opened as a table, **Then** the rows match `transactions_count_line`.
3. **Given** Expense Amount + Bar, **When** the chart is opened as a table, **Then** the rows match `expense_amount_bar`.
4. **Given** Transactions Count + Bar, **When** the chart is opened as a table, **Then** the rows match `transactions_count_bar`, including the list-shaped `values` field (`[3, 1]` / `[3]`).
5. **Given** a genuinely unrendered chart, **When** the reader returns nothing, **Then** that test skips with a descriptive guard (safety net only).

---

### User Story 5 - Authority chart and Screen 2 export matrix match (Priority: P2)

A validation author reads `expenses_by_authority_millions` on Screen 1 (show-as-table) and the export matrix on Screen 2, and compares both to the golden record.

**Why this priority**: These are the remaining golden blocks after KPIs and daily trends. Screen 2 is a different page.

**Independent Test**: `test_expenses_by_authority_match_golden` on Screen 1; `test_export_table_match_golden` after switching to Screen 2 and applying Screen 2 filters.

**Acceptance Scenarios**:

1. **Given** Screen 1 filters, **When** the authority visual is opened as a table, **Then** every golden authority (`תל אביב - יפו`, `ירושלים`, `רמת גן`, `ראשון לציון`) matches its amount. Extra UI rows are ignored.
2. **Given** Screen 2 is open with golden filters, **When** `read_export_table()` runs, **Then** every golden `export_table_data` row is present (transaction date, authority, vitality, category, sub-category, quantity, amount, purchase nature). Extra UI rows are ignored.
3. **Given** `daily_alerts` in the golden file, **When** that visual is readable, **Then** a dedicated test compares it; if the visual is absent the test skips.

---

### Edge Cases

- Power BI serving English accessibility names for the page-rail or date fields must still resolve through `.or_()`.
- Filter values of `הכל` are the default and must not be re-selected as if they were a named period.
- Transactions-count bar rows use a `values` list, not a scalar `value`; the reader must not coerce a list into a single number.
- A genuinely empty visual still skips with a descriptive message; skip is not used when data is present.
- The info overlay (`דף מידע`) is dismissed before the ready wait; a session without the overlay is a no-op.
- Alerts, status-picture, fleet, `core/`, and the golden metric values are not edited.
- Comments inside new or edited functions are English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `CreditConsumptionPage` MUST live at `pages/credit_consumption/credit_consumption_page.py`, inherit `ReportShell`, keep `DASHBOARD_SEARCH_TERM = "צריכת אשראי"`, dismiss the info overlay in `before_report_ready_check` / `after_navigate`, and use `_report_ready_locator` on `ממוצע הוצאות לקנייה בשגרה`.
- **FR-002**: `pages/credit_consumption/page.py` MUST re-export `CreditConsumptionPage` so the existing smoke conftest import stays valid (AC-004).
- **FR-003**: Page-rail navigation to Screen 2 MUST locate the switch by a bilingual `.or_()` over `ניווט בין עמודים` and `Page navigation`.
- **FR-004**: Date fields, when present, MUST fill through a bilingual `.or_()` over `תאריך התחלה` / `Start date` and `תאריך סיום` / `End date`.
- **FR-005**: The sanity fixture or shared setup MUST load `data/credit/db_sanity_purim2026.yaml`, apply Screen 1 `active_filters` (non-`הכל` values, including `time_range: "פורים 2026"`) before Screen 1 assertions, and apply Screen 2 `active_filters` (including `top_bar.period: "פורים 2026"`) before Screen 2 assertions.
- **FR-006**: `read_kpi_metrics()` MUST return the nested shape of golden `kpi_metrics` (population, routine expense, selected-range expense, change-vs-routine percents) using Layer 2 `KPI` with titles copied from the live report.
- **FR-007**: The page MUST expose toggle methods for metric (Expense Amount vs. Transactions Count) and visualization (Line vs. Bar). Toggle accessible names are copied from the live report; they MUST NOT be added as a `SlicerKind`.
- **FR-008**: `read_daily_trends()` MUST extract the active chart via Right-click → bilingual Show as a table (`הצג כטבלה` / `Show as a table`) and return rows matching the active `daily_trends_by_toggle` key (`expense_amount_line`, `transactions_count_line`, `expense_amount_bar`, `transactions_count_bar`). Scalar `value` vs list `values` MUST follow the YAML shape for that key.
- **FR-009**: `read_expenses_by_authority()` MUST return `{authority: amount}` (or a list of `{authority, amount}`) from the authority visual via the same Show-as-a-table strategy, mapped to `expenses_by_authority_millions`.
- **FR-010**: `read_export_table()` MUST return the Screen 2 matrix rows mapped to `export_table_data` keys (`transaction_date`, `authority_name`, `vitality_status`, `category`, `sub_category`, `quantity`, `amount`, `purchase_nature`).
- **FR-011**: `tests/sanity/credit_consumption_dashboard/test_data_validation.py` MUST assert KPIs, all four daily-trend combinations, the authority chart, and the export table against the golden record. Extra UI keys/rows are ignored; every golden key/row MUST be present. Empty-read `pytest.skip` guards remain as a safety net.
- **FR-012**: This slice MUST NOT edit any alerts, status-picture, or fleet module, `core/portal`, `core/components`, or the root `conftest.py`.
- **FR-013**: Golden metric values in `data/credit/db_sanity_purim2026.yaml` MUST NOT change.
- **FR-014**: Comments inside new or edited functions MUST be English.
- **FR-015**: Existing credit smoke (`tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py`) MUST stay green. Additive page methods MUST NOT break `verify_freshness` or popup dismiss.
- **FR-016**: Hebrew titles, slicer role names, and toggle labels that are not already in the golden YAML or in the existing Layer 0 page MUST be copied from the live report during implementation, not invented in this spec.

### Key Entities

- **Golden record**: `data/credit/db_sanity_purim2026.yaml` → `credit_consumption_dashboard` with `screen_1_summary` and `screen_2_data_export`.
- **Bilingual locator**: Playwright `.or_()` over Hebrew and English accessible names for page-rail, date fields, and the Show-as-a-table menu.
- **Toggle state**: Active metric (`expense_amount` / `transactions_count`) and visualization (`line` / `bar`) that compose a `daily_trends_by_toggle` key.
- **KPI metrics**: Nested card values under `kpi_metrics`.
- **Authority row**: `{authority, amount}` in millions.
- **Export row**: one Screen 2 matrix record matching `export_table_data` fields.
- **Active filters**: Screen 1 flat map and Screen 2 `top_bar` / `side_bar` maps; `הכל` means default.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. It MUST NOT
  contain vehicles, district, fleet KPI/chart titles, or other report-specific labels.
  Generic last-refresh chrome (`הדשבורד עודכן לאחרונה ב:`) MAY live in Layer 0
  and MUST be located by regex or text inside the report iframe, never by
  dashboard-specific CSS or visual ids.
- **AC-002**: Domain page objects MUST inherit or compose `ReportShell` rather
  than re-implement login, catalog search, iframe wait, visual-load timeout,
  or last-refresh verification.
- **AC-003**: Report-ready state MUST be supplied by the domain page (locator,
  predicate, or override), never hardcoded in `ReportShell`.
- **AC-004**: Public test-facing page-object APIs MUST keep their contracts
  unless tests are updated in the same change.
- **AC-005**: Layer 2 (`core/components/`) MUST remain report-agnostic when
  present. Domain pages compose `Slicer` and supply definitions plus settle;
  `core/` MUST NOT load `data/<report>/` or hardcode fleet filter names.
- **AC-006**: Report pages MUST live in `pages/<report>/`. Report SQL MUST
  live in `db/clients/<report>.py`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With portal auth, `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity` applies `פורים 2026` and asserts KPIs, four daily-trend combinations, the authority chart, and the export table against the golden record (pass/fail, not skip, when data is present).
- **SC-002**: Opening Screen 2 and filling date fields (when present) does not raise `LoadTimeoutError` under Hebrew or English accessibility names.
- **SC-003**: Credit smoke `pytest tests/ui/credit_consumption_dashboard/` stays green (`verify_freshness` still works after popup dismiss).
- **SC-004**: No alerts, status-picture, fleet, `core/`, or root-conftest file is modified. Golden metric values are unchanged.
- **SC-005**: Fleet smoke is not a required gate (Layer 0, Layer 2, and the fleet page are not edited). If a later change edits `core/`, fleet smoke MUST pass at 100%.

## Assumptions

- Portal SSO and the shared `auth_page` / `bind_dashboard` fixture already open this catalog product (feature 004 / 018).
- The golden YAML is a Purim 2026 snapshot; this slice does not query SQL Server.
- Slicer kind for `time_range` is a dropdown (Layer 2 `Slicer.select`); confirmation happens against the live report.
- Toggle controls are visual buttons on Screen 1, not catalog slicers.
- `daily_alerts` is asserted when the visual is present and skipped when it is not.
- Show-as-a-table helpers are implemented on the credit domain page (alerts copy is off-limits; no new Layer 2 API in this slice).
- Hebrew KPI / toggle / slicer labels not already recorded are copied from the live report during implementation.
