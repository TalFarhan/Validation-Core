# Feature Specification: Alerts Contract Coverage

**Feature Branch**: `017-alerts-contract-coverage`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Expand the Alerts YAML contract to cover 100% of dashboard KPIs and the missing static comparison chart. Threat types are scopes with category ids. Each scope has the stable cards היום, אתמול, and סה\"כ בטווח שנבחר. Population and warning-area groups use those same stable card titles under the group base name, without a dynamic time suffix. The comparison chart title is static and its query ignores the time slicer. Stub the new SQL. English comments only. Do not hide a database connection error."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Threat cards inside their section (Priority: P1)

A validation author checks the three threat sections one at a time. Each section has the same three card titles. The contract names the section as `scope` and the card as `name`, and binds that section's category id.

**Why this priority**: Those titles repeat on the report. Without a scope, the engine cannot tell which section's "היום" it read. Feature 016 left this pairing unconfirmed.

**Independent Test**: The contract loads nine KPI metrics: three scopes times three card titles. Each scope carries one category id. A unit test reads the file and does not start a browser.

**Acceptance Scenarios**:

1. **Given** scope `ירי רקטות וטילים`, **When** the contract is loaded, **Then** that scope has `category_id` `1` and KPI names `היום`, `אתמול`, and `סה"כ בטווח שנבחר`.
2. **Given** scope `חדירת מחבלים`, **When** the contract is loaded, **Then** that scope has `category_id` `2` and the same three KPI names.
3. **Given** scope `חדירת כלי טיס עוין`, **When** the contract is loaded, **Then** that scope has `category_id` `10` and the same three KPI names.
4. **Given** any of those nine metrics, **When** parity runs, **Then** the engine passes that scope and that category id through the existing readers and runner. This feature does not add a new reader.

---

### User Story 2 - Population and warning-area cards (Priority: P1)

A validation author checks the general population group and the warning-area group. Each group is named by its stable base, not by a suffix the time slicer rewrites. Inside each group the three card titles are the same stable strings as in the threat sections.

**Why this priority**: Those group titles change when the slicer changes. Putting the slicer phrase into `name` or `scope` makes the contract true for only one slicer state.

**Independent Test**: The contract loads six KPI metrics: two scopes times three card titles. Neither scope includes a date-range slicer phrase. None of these six metrics sets `category_id`.

**Acceptance Scenarios**:

1. **Given** scope `אוכלוסייה מותרעת`, **When** the contract is loaded, **Then** it has KPI entries `היום`, `אתמול`, and `סה"כ בטווח שנבחר`, and no `category_id`.
2. **Given** scope `אזורי התרעה תחת ירי`, **When** the contract is loaded, **Then** it has the same three KPI entries and no `category_id`.
3. **Given** either scope, **When** the contract is loaded, **Then** the scope string is the base name and does not contain the slicer phrase `שלושים יום אחרונים`.

---

### User Story 3 - Static settlement comparison chart (Priority: P1)

A validation author checks the chart whose title always says the current day and the previous day. That title does not follow the time slicer. The warehouse query for it must not filter by the slicer window.

**Why this priority**: Feature 016 contracted the ranking chart and explicitly left this neighboring chart out. It is still unchecked.

**Independent Test**: The contract loads one `chart` metric whose `name` is the full static title. Its SQL returns no rows and does not mention the date binds. The ranking chart, the map, and the policy status stay as they are.

**Acceptance Scenarios**:

1. **Given** the comparison chart, **When** the contract is loaded, **Then** `visual` is `chart` and `name` is `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת`.
2. **Given** that metric, **When** its SQL is read, **Then** the statement does not reference `:start_date`, `:end_date`, or `AlertDate`.
3. **Given** the test still passes a date window into the runner, **When** this statement executes, **Then** those extra binds do not change the row set and do not raise a bind error.

---

### User Story 4 - Stubs run, connection errors surface (Priority: P1)

A validation author has not confirmed the warehouse SQL for the new cards or the comparison chart. Each new metric still executes a stub from the Alerts SQL client. A missing database fails the parity test.

**Why this priority**: A contract row that never runs looks covered. Swallowing the connection error would hide that the check did not happen.

**Independent Test**: `db/clients/alerts.py` defines a stub constant for each new group. The YAML `sql_query` text matches that constant. `test_db_parity.py` still has no skip. The runner does not catch connection failures.

**Acceptance Scenarios**:

1. **Given** a new KPI metric, **When** its query runs, **Then** the statement is `SELECT 0` from the Alerts client, not a skipped test.
2. **Given** the comparison chart, **When** its query runs, **Then** the statement returns an empty two-column row set.
3. **Given** the Alerts database is missing or refuses the connection, **When** the parity test runs, **Then** that error propagates. The test is not skipped and the error is not caught to force a pass.

---

### Edge Cases

- The card title `סה"כ בטווח שנבחר` contains a double quote. The YAML stores that character. It is not a slicer phrase and it is not stripped.
- `היום` is not unique. Identity for the new cards is `name` plus `scope`. A test that indexes the contract by `name` alone is not valid for these rows.
- The comparison-chart spelling uses `ישובים` (one yod). The existing ranking chart uses `יישובים` (two yods). The two `name` values must not be edited to match each other.
- The phrase `ביממה הנוכחית והקודמת` stays in the comparison-chart `name`. It is the chart's permanent title. It is not the slicer option `שלושים יום אחרונים`.
- A new KPI is `visual: kpi`. It does not set `maximum_sql`. A gauge entry is out of this slice until a denominator query is confirmed.
- The six existing category measures (`אוכלוסייה מותרעת` and `אזורי התרעה תחת ירי` with ids `1`, `2`, and `10`), the ranking chart, the map, and the policy status stay in the file.
- Stub SQL is executed. `pytest.skip`, `pytest.importorskip`, and `pytest.mark.skip` are not added to the Alerts parity test.
- Inline comments added or edited by this feature are English only. Hebrew remains legal as `name`, `scope`, and other contract data.
- `category_id` on a threat metric is the string `1`, `2`, or `10`. The runner already stringifies the value. The Python client does not hardcode those ids.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `alerts_contract.yaml` MUST add nine KPI metrics: scopes `ירי רקטות וטילים` (`category_id` `1`), `חדירת מחבלים` (`category_id` `2`), and `חדירת כלי טיס עוין` (`category_id` `10`). Each scope MUST include `היום`, `אתמול`, and `סה"כ בטווח שנבחר` with `visual: kpi`.
- **FR-002**: The contract MUST add six general KPI metrics. Scope `אוכלוסייה מותרעת` and scope `אזורי התרעה תחת ירי` each include `היום`, `אתמול`, and `סה"כ בטווח שנבחר`. These six MUST NOT set `category_id`. Their `visual` MUST be `kpi`.
- **FR-003**: Scope and name strings for FR-001 and FR-002 MUST be the stable bases above. They MUST NOT include the slicer phrase `שלושים יום אחרונים` or any other slicer-dependent suffix.
- **FR-004**: The contract MUST add one chart metric whose `name` is exactly `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת` and whose `visual` is `chart`. It MUST NOT set `category_id` or `scope`.
- **FR-005**: `db/clients/alerts.py` MUST define stub SQL for every new metric. KPI stubs are `SELECT 0`. The chart stub is an empty two-column row set. The chart statement MUST NOT reference `:start_date`, `:end_date`, or `AlertDate`. Each YAML `sql_query` MUST equal its constant.
- **FR-006**: Existing feature-016 metrics MUST remain: the six category KPIs, the ranking chart, the map, and the policy text KPI, including their current SQL.
- **FR-007**: Category ids, Hebrew titles, scopes, and SQL MUST stay in the Alerts contract or in `db/clients/alerts.py`. They MUST NOT be added under `core/`. The parity engine MUST NOT be modified.
- **FR-008**: New or edited inline comments MUST be English only.
- **FR-009**: The Alerts parity test MUST NOT gain a skip, and the Alerts runner MUST NOT catch a connection or query error from these stubs. Errors propagate.
- **FR-010**: `docs/COVERAGE_CATALOG.md` MUST list the new threat cards, the six general cards, and the static comparison chart, and MUST mark their SQL as stubs.

### Key Entities

- **Threat card**: A KPI identified by `scope` (threat section) plus `name` (time bucket) plus `category_id`.
- **General card**: A KPI identified by `scope` (population or warning-area base) plus `name` (time bucket). No category id.
- **Static comparison chart**: One chart identified by its full permanent title. Its query does not depend on the slicer window.
- **Stub statement**: A placeholder `SELECT` stored on the Alerts client and copied into `sql_query`. It is executed.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/` stays report-agnostic. This feature does not add titles, scopes, category ids, Hebrew strings, or SQL there.
- **AC-002**: The Alerts page is unchanged. The date-range option remains a test string. No new slicer is required for these titles.
- **AC-003**: The engine stays as feature 016 left it. Scope and `category_id` are already forwarded. This feature only adds contract rows and SQL constants.
- **AC-004**: `validate_dashboard_generic`'s signature stays. `AlertsDBRunner.scalar` and `rows` stay. They may receive date binds the chart SQL does not use.
- **AC-005**: `db/clients/alerts.py` may add stub constants. It must not hardcode ids `1`, `2`, or `10`, and it must not embed Hebrew.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The contract contains exactly nine new threat KPIs, with the three scopes and category ids in FR-001, and exactly six new general KPIs with no `category_id`.
- **SC-002**: One chart metric uses the full static title in FR-004. Its SQL text contains neither `:start_date` nor `AlertDate`. The ranking-chart metric is still present with its existing name.
- **SC-003**: No new metric `name` or `scope` contains `שלושים יום`. The comparison-chart name still contains `ביממה הנוכחית והקודמת`.
- **SC-004**: Searching `core/` for the new Hebrew titles finds no matches from this feature. `tests/helpers/db_parity_engine.py` has no diff from this feature.
- **SC-005**: Fleet smoke (`pytest tests/ui/fleet_dashboard/`) stays 100% green. This feature does not change Layer 0, Layer 2, or the fleet page.
- **SC-006**: `test_db_parity.py` contains no `pytest.skip`, `importorskip`, or `mark.skip`. A missing Alerts database still fails that test.

## Assumptions

- Feature 016 is already implemented. This slice does not reopen engine, gauge, map, or text-KPI work.
- The repeated card titles are `היום`, `אתמול`, and `סה"כ בטווח שנבחר`. The section that disambiguates them is `scope`, which feature 014 already supports. Title and scope matching stay unanchored, so a stable base still matches when a slicer suffix is appended to the accessible name.
- Population and warning-area time buckets are general cards, not a second copy of category ids `1`, `2`, and `10`. The six existing category measures stay.
- Those time buckets are KPI cards, not gauges. `KPI.number` reads the current figure. A gauge `maximum_sql` is not invented here. The user allowed either visual; `kpi` is the one that does not require an unconfirmed denominator.
- The comparison chart ignores the slicer in the business sense: its SQL has no date predicate. The runner may still pass `:start_date` and `:end_date`. SQLAlchemy 2.0.51 does not raise when the statement omits those binds.
- `category_id` is written as the YAML strings `"1"`, `"2"`, and `"10"`, matching the existing contract. The engine already coerces them with `str`.
- `label` on a threat metric may record `Rockets`, `Terrorists`, or `UAV` as documentation. The engine ignores `label`.
- Real warehouse SQL for these metrics is a later replacement of the stubs. This slice does not guess DAX or column names.
- Planning does not switch the git checkout. The spec directory is `specs/017-alerts-contract-coverage`.
