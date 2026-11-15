# Feature Specification: Credit Consumption UI Sanity Validation

**Feature Branch**: `feature/reportportal-integration` (spec directory `046-credit-ui-validation`; git checkout stays put)

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Implement UI data validation tests for the Credit Consumption dashboard against the golden YAML file (e.g., `data/credit/db_sanity_purim2026.yaml`). Do NOT use SQL queries or `db/clients/credit.py`. Rely entirely on the live dashboard UI and compare it to the YAML. Expand existing page objects and tests (`pages/credit_consumption/credit_consumption_page.py` and `tests/sanity/credit_consumption_dashboard/test_data_validation.py`). Do not rebuild from scratch."

## Clarifications

### Session 2026-11-04

- Q: Which git checkout should this slice use? → A: Spec directory `046-credit-ui-validation`. Planning does not switch the git checkout (`feature/reportportal-integration`), matching 044/045. `.specify/feature.json` is repointed to this directory. Sibling `045-hour-chart-table-teardown` stays untouched.
- Q: What already exists? → A: Feature 044 already landed `CreditConsumptionPage`, the sanity fixture, and `test_data_validation.py`. This slice expands those files. It does not recreate the page, the fixture, or the suite.
- Q: What is the source of truth? → A: `data/credit/db_sanity_purim2026.yaml` under `credit_consumption_dashboard`. The period string is read from `active_filters`. It is not hardcoded. `הכל` stays the default and is not re-selected. The YAML file is not edited.
- Q: When is an empty UI a failure? → A: If the golden block has keys or rows and the reader returns empty, the test fails. `pytest.skip` is allowed only when that visual is genuinely not rendered on the page.
- Q: How is last-updated compared? → A: The test calls the inherited `_last_refresh_caption_text` reader. The golden value is `DD/MM/YYYY HH:MM`. This slice does not add a second date parser and does not change `verify_freshness`.
- Q: How are tables read? → A: The existing Show as a table path on the credit page (`הצג כטבלה` / `Show as a table`). No SVG or tooltip parsing. No copy from `pages/alerts_analysis/`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Screen 1 matches the golden summary (Priority: P1)

A validation author opens the Credit Consumption report, applies `screen_1_summary.active_filters` through the existing `apply_filters`, and compares the live summary to the golden YAML. The screen title, last-updated caption, KPI cards, daily-trend toggle series, daily alerts, and authority amounts are all checked. Extra UI keys and rows are ignored. Every golden key and row must be present and equal.

**Why this priority**: Screen 1 is the summary contract. A skip on an empty read hides a broken reader while the golden file still has data.

**Independent Test**: `test_data_validation.py` Screen 1 tests call `apply_filters` with the YAML `active_filters`, then `read_kpi_metrics`, `read_daily_trends`, `read_daily_alerts`, and `read_expenses_by_authority`.

**Acceptance Scenarios**:

1. **Given** `screen_1_summary.active_filters`, **When** setup runs, **Then** `apply_filters` is called with that map before any Screen 1 read, values equal to `הכל` are left as the default, and the period string is taken from the YAML (not a literal in the test).
2. **Given** filters are applied, **When** the screen title is read from the existing page title element, **Then** it equals `dashboard_info.title`.
3. **Given** filters are applied, **When** `_last_refresh_caption_text()` is read, **Then** it matches `dashboard_info.last_updated` in `DD/MM/YYYY HH:MM` without a new date parser.
4. **Given** filters are applied, **When** `read_kpi_metrics()` is compared with `_assert_nested`, **Then** every golden KPI key matches, percent values stay strings such as `"3.23%"`, and extra UI keys are ignored.
5. **Given** each key in `daily_trends_by_toggle`, **When** the key is split with `rsplit("_", 1)` into metric and visualization, **Then** `set_metric` and `set_visualization` run and `read_daily_trends()` matches that series. `date` is the row key. `day` is compared as a string. `transactions_count_bar` values stay a list such as `[3, 1]`.
6. **Given** `daily_alerts`, **When** `read_daily_alerts()` runs, **Then** rows match on `date`.
7. **Given** `expenses_by_authority_millions`, **When** `read_expenses_by_authority()` runs, **Then** rows match on `authority`.
8. **Given** the golden block has rows and the visual is rendered, **When** the reader returns empty, **Then** the test fails. **Given** the visual is not rendered, **When** the test reaches it, **Then** it `pytest.skip`s.

---

### User Story 2 - Screen 2 export rows match the golden matrix (Priority: P1)

A validation author opens Screen 2 through the existing page-navigation rail, merges `active_filters.top_bar` and `active_filters.side_bar`, and compares the export grid to `export_table_data`.

**Why this priority**: The export matrix is the second golden screen and uses a different filter shape.

**Independent Test**: The Screen 2 test calls `open_export_page()`, then `apply_filters` on the merged maps, asserts the visible title, then `read_export_table()`.

**Acceptance Scenarios**:

1. **Given** Screen 1 is open, **When** `open_export_page()` runs, **Then** navigation uses the existing page-rail method and the export page is shown.
2. **Given** Screen 2 `active_filters`, **When** setup runs, **Then** `top_bar` and `side_bar` are merged and passed to `apply_filters`. `הכל` stays the default. The period is not hardcoded.
3. **Given** filters are applied, **When** the visible screen title is read, **Then** it equals `screen_2_data_export.title`.
4. **Given** the export grid is readable, **When** `read_export_table()` is compared, **Then** every golden row matches on `(transaction_date, authority_name, sub_category)`. `quantity` is an int. `amount` stays a comma-formatted string such as `"1,944.97"`. Extra UI rows are ignored.
5. **Given** golden export rows exist and the grid is rendered, **When** the reader returns empty, **Then** the test fails.

---

### User Story 3 - Existing credit smoke stays green (Priority: P2)

A validation author runs the existing credit smoke test. `verify_freshness` still passes. This slice does not replace that check with the golden timestamp assertion.

**Why this priority**: The golden last-updated check is a separate exact match. The smoke test remains the 24-hour freshness gate.

**Independent Test**: `pytest tests/ui/credit_consumption_dashboard/` still calls `verify_freshness()` and is not edited.

**Acceptance Scenarios**:

1. **Given** the credit smoke module, **When** this slice is implemented, **Then** `test_dashboard_updated_within_24_hours` still calls `dashboard.verify_freshness()` and the module is not rewritten.
2. **Given** Layer 0 last-refresh parsing, **When** the sanity test reads the caption, **Then** it reuses `_last_refresh_caption_text` and does not add a parser in the credit page or the test.

---

### Edge Cases

- `הכל` in either screen's `active_filters` is the landing default and must not be applied as a named choice.
- The period value lives only in the YAML. Tests and new code must not embed that period as a literal.
- A golden dict or list that is non-empty with an empty UI read is a failure, including a KPI map that comes back `{}`.
- `pytest.skip` is reserved for a visual whose title or container is absent from the page. A rendered visual with zero parsed rows is a failure.
- Extra UI keys, extra trend rows, extra authorities, and extra export rows do not fail the test.
- `transactions_count_bar` uses `values` (a list). Other trend keys use scalar `value`. The list must not be unwrapped to its first element.
- `day` is a string (`"שני"`). It is not parsed into a weekday number.
- Percent KPI values stay strings. They are not converted to floats.
- `amount` keeps thousands separators. `quantity` is an `int`.
- Assertion failures name the JSON path, the UI value, and the golden value.
- A Hebrew label that is missing from the page is copied from the live report during implementation. Comments inside functions stay English.
- Show-as-a-table stays the chart extraction path. SVG paths and tooltips are not read.
- Alerts, status-picture, fleet, `core/portal`, `core/components`, `db/`, the root `conftest.py`, and the YAML files are not edited.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sanity tests MUST load `credit_consumption_dashboard` from `data/credit/db_sanity_purim2026.yaml`. They MUST NOT hardcode the period name. `apply_filters` MUST treat `הכל` as the default and skip it.
- **FR-002**: Screen 1 tests MUST call `apply_filters` with `screen_1_summary.active_filters` before reading the title, last-updated caption, KPIs, trends, alerts, or authority chart.
- **FR-003**: The visible Screen 1 title MUST equal `dashboard_info.title`, using the existing page title element (`SCREEN_1_TITLE` / iframe phrase). The visible Screen 2 title MUST equal `screen_2_data_export.title` after `open_export_page()`.
- **FR-004**: `dashboard_info.last_updated` MUST be compared to the text returned by the inherited `_last_refresh_caption_text()` in `DD/MM/YYYY HH:MM`. This slice MUST NOT add a date parser.
- **FR-005**: KPI comparison MUST use `read_kpi_metrics()` and `_assert_nested`. Nested golden keys MUST match. Percent strings MUST stay strings. Extra UI keys MUST be ignored.
- **FR-006**: For each `daily_trends_by_toggle` key, the test MUST split with `key.rsplit("_", 1)` into metric and visualization, call `set_metric` and `set_visualization`, then `read_daily_trends()`. Row identity is `date`. `day` is a string. `transactions_count_bar` values MUST remain a list.
- **FR-007**: `read_daily_alerts()` MUST be compared with row key `date`. `read_expenses_by_authority()` MUST be compared with row key `authority`.
- **FR-008**: Screen 2 tests MUST call `open_export_page()` on the existing navigation rail, then `apply_filters` with `active_filters.top_bar` merged with `active_filters.side_bar`.
- **FR-009**: `read_export_table()` MUST match every golden `export_table_data` row. The composite key is `(transaction_date, authority_name, sub_category)`. `quantity` MUST be an `int`. `amount` MUST remain a string that keeps commas (for example `"1,944.97"`).
- **FR-010**: Comparison is a subset match. Every golden key and row MUST exist in the UI result and be equal. Extra UI keys and rows MUST NOT fail the test.
- **FR-011**: If golden data is present and the UI reader returns empty, the assertion MUST fail. `pytest.skip` is allowed only when the visual is not rendered on the page.
- **FR-012**: Assertion messages MUST include the JSON path, the UI actual value, and the golden expected value.
- **FR-013**: Chart values MUST be read through the credit page's existing Show as a table flow. This slice MUST NOT parse SVGs or tooltips and MUST NOT copy implementations from `pages/alerts_analysis/`.
- **FR-014**: This slice MUST expand `pages/credit_consumption/credit_consumption_page.py` and `tests/sanity/credit_consumption_dashboard/test_data_validation.py`. It MUST NOT rebuild them. Comments inside new or edited functions MUST be English. Hebrew labels that are missing MUST be copied from the live report.
- **FR-015**: This slice MUST NOT edit `core/portal/`, `core/components/`, `pages/alerts_analysis/`, `pages/status_picture/`, `pages/fleet_dashboard/`, their test suites, `db/`, the root `conftest.py`, or any YAML file.
- **FR-016**: `tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py` MUST stay as a `verify_freshness()` check and MUST remain green. `verify_freshness` itself is not replaced or overridden.

### Key Entities

- **Golden record**: `data/credit/db_sanity_purim2026.yaml` → `credit_consumption_dashboard` with `screen_1_summary` and `screen_2_data_export`. Unchanged by this slice.
- **Screen 1 summary**: `dashboard_info` (`title`, `last_updated`), `kpi_metrics`, `daily_trends_by_toggle`, `daily_alerts`, `expenses_by_authority_millions`, `active_filters`.
- **Screen 2 export**: `title`, `active_filters.top_bar`, `active_filters.side_bar`, `export_table_data`.
- **Trend toggle key**: `{metric}_{visualization}` split on the last underscore (`expense_amount` / `transactions_count` × `line` / `bar`).
- **Export row key**: `(transaction_date, authority_name, sub_category)`.
- **Subset match**: golden keys and rows are required; UI-only keys and rows are ignored.
- **Not-rendered visual**: a chart or card whose existing title/container is absent. That is the only skip. An empty parse of a rendered visual is a failure.

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

- **SC-001**: With portal auth, `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity` applies filters from the YAML and asserts Screen 1 title, last-updated, KPIs, four trend combinations, daily alerts, authority amounts, Screen 2 title, and export rows. A rendered visual with golden data and an empty read fails. A missing visual skips.
- **SC-002**: Failure text for a mismatch contains the JSON path, the UI value, and the golden value.
- **SC-003**: `pytest tests/ui/credit_consumption_dashboard/` stays green (`verify_freshness` unchanged).
- **SC-004**: No file under `core/portal/`, `core/components/`, `pages/alerts_analysis/`, `pages/status_picture/`, `pages/fleet_dashboard/`, their tests, `db/`, the root `conftest.py`, or `data/credit/` is modified.
- **SC-005**: In-function comments added or edited in this slice are English. Chart reads still go through the credit page Show as a table helpers.

## Assumptions

- Feature 044 page methods (`apply_filters`, `open_export_page`, `read_kpi_metrics`, `set_metric`, `set_visualization`, `read_daily_trends`, `read_daily_alerts`, `read_expenses_by_authority`, `read_export_table`) stay the API. This slice fixes comparison and any reader gap that drops `quantity`/`amount` shape or list-shaped trend values. It does not replace the class.
- `_last_refresh_caption_text` already returns caption text that includes a `DD/MM/YYYY HH:MM` timestamp. The sanity test looks for the golden string in that text. `verify_freshness` keeps its own 24-hour age check in Layer 0.
- The golden last-updated value can disagree with a report that refreshed after the snapshot. This slice still asserts the YAML string and still leaves `verify_freshness` unchanged. The YAML is not edited to make them agree.
- Show-as-a-table helpers already on `CreditConsumptionPage` are the extraction path. Alerts Analysis helpers are not imported.
- Hebrew titles already stored on the page (`SCREEN_1_TITLE`, `SCREEN_2_TITLE`, chart titles, KPI titles) are reused. A label that is wrong against the live report is replaced by copying the live string, not by inventing one in the spec.
- Fleet smoke is not a gate. Layer 0, Layer 2, and the fleet page are not edited.
