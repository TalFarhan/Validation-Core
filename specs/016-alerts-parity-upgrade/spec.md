# Feature Specification: Alerts DB Parity Upgrade

**Feature Branch**: `016-alerts-parity-upgrade`

**Created**: 2026-10-13

**Status**: Draft

**Input**: User description: "Upgrade DB Parity Engine for Alerts using new core components (scoped KPI lookups, KPI.scale, generic Chart parsing). Pass scope into KPI lookups, verify gauge value and maximum against the database, filter Alerts SQL by dynamic category_id (UAV, Rockets, Terrorists), and keep date phrases out of contract metric names. Business SQL, category ids, and Hebrew strings stay in the Alerts test/domain layer. Inline comments in English only. Expand the Alerts contract to the remaining dashboard visuals: the Top 10 Settlements chart, the Alerts map (presence via classify_presence, true zero versus empty), and the policy-classification status as text. Stub those three queries in the Alerts SQL client. Do not skip the parity test, and do not hide database connection errors."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scoped visual lookup (Priority: P1)

A validation author points a contract metric at a KPI, gauge, or chart that is not unique in the report iframe. The engine searches only inside the section named by that metric's scope.

**Why this priority**: Duplicate titles across Alert categories make a global title search ambiguous. Scope is what makes the later category split trustworthy.

**Independent Test**: A contract metric with a non-empty `scope` is read through `KPI.number`, `KPI.scale`, or `Chart.read` with that same scope. A metric with no scope, or a blank scope, is read with scope omitted (`None`).

**Acceptance Scenarios**:

1. **Given** a metric whose `scope` is a non-empty string, **When** the engine reads the visual, **Then** the Layer 2 call receives that string and does not search the whole iframe.
2. **Given** a metric with `scope` missing, empty, or whitespace, **When** the engine reads the visual, **Then** the call uses no scope.
3. **Given** the scope text is Hebrew or otherwise report-specific, **When** the engine runs, **Then** that text exists only in the Alerts contract, not under `core/`.

---

### User Story 2 - Gauge value and denominator (Priority: P1)

A validation author declares a metric as a gauge. The engine reads `KPI.scale` and checks both the current value and the maximum (denominator) against separate warehouse queries.

**Why this priority**: `KPI.number` returns only the current figure. A gauge that matches on the numerator and is wrong on the scale would pass today's engine.

**Independent Test**: A gauge metric fails when either the value or the maximum differs from its query, including when the value is 0. A missing maximum on the visual fails the maximum check.

**Acceptance Scenarios**:

1. **Given** a gauge metric with `sql_query` and `maximum_sql`, **When** parity runs, **Then** `scale["value"]` equals the first scalar and `scale["maximum"]` equals the second.
2. **Given** the visual shows 0 and the value query returns 0, **When** parity runs, **Then** the value check passes.
3. **Given** `scale["maximum"]` is missing, or `scale["state"]` is `empty`, **When** parity runs, **Then** the metric fails.
4. **Given** a metric whose visual is `kpi` (or omitted), **When** parity runs, **Then** the engine still uses `KPI.number` and does not require `maximum_sql`.

---

### User Story 3 - One category at a time (Priority: P1)

A validation author splits the Alerts pilot so UAV, Rockets, and Terrorists are checked separately. Each metric names one category id. The Alerts SQL client binds that id. The old grouped `CategoryID IN ('1', '2', '10')` query is not the parity path.

**Why this priority**: A single grouped total can match while one category is wrong.

**Independent Test**: Each of the three category ids is bound as `:category_id` on its own query. The id values and their labels live in the Alerts contract or Alerts test module. `core/` and the parity engine do not contain those ids or the words UAV, Rockets, or Terrorists.

**Acceptance Scenarios**:

1. **Given** a metric with `category_id`, **When** the Alerts runner executes `sql_query` or `maximum_sql` or a chart query, **Then** `:category_id` is a bound parameter and the id is not interpolated into the SQL text.
2. **Given** the three ids previously grouped together (`1`, `2`, `10`), **When** the Alerts contract is updated, **Then** each id is validated on its own metrics rather than in one `IN` list.
3. **Given** a metric with no `category_id`, **When** a query does not reference `:category_id`, **Then** the runner still binds only the date window.

---

### User Story 4 - Chart rows against the warehouse (Priority: P1)

A validation author declares a bar or column visual. The engine reads it with `Chart.read` and compares category labels and numeric cells to a row query on the Alerts database.

**Why this priority**: Feature 015 added chart parsing specifically so parity can check more than scalar KPI cards. The Alerts upgrade is the first consumer.

**Independent Test**: A chart metric's categories match the query's label/value rows for the bound dates and category id. A missing bar (`None`) matches a SQL NULL. An extra label on either side fails.

**Acceptance Scenarios**:

1. **Given** a chart metric, **When** parity runs, **Then** the engine calls `Chart.read(name, scope=...)` and does not parse the chart inside the engine.
2. **Given** the query returns one label column and one numeric column, **When** labels and values match series index 0 (or the metric's `series_index`), **Then** the metric passes.
3. **Given** the visual state is `empty` and the query returns no rows, **When** parity runs, **Then** the metric passes. Any other empty-versus-rows combination fails.

---

### User Story 5 - Metric names survive a slicer change (Priority: P1)

A validation author changes the date-range slicer. Contract metric names stay the same. The test supplies the slicer option and the matching date window. The engine never appends a date phrase to a title.

**Why this priority**: Today's titles embed "בשלושים יום האחרונים", so another slicer state requires renaming metrics and rewriting the catalog.

**Independent Test**: The Alerts contract names do not contain the slicer option text. The test still selects the 30-day option and passes a half-open window. A second option can be added in the test without editing metric names.

**Acceptance Scenarios**:

1. **Given** the 30-day slicer option, **When** the contract is loaded, **Then** no metric `name` equals or contains that option text.
2. **Given** the test computes `start_date` and `end_date`, **When** SQL runs, **Then** those values are bound as `:start_date` and `:end_date` and are not formatted into the query string.
3. **Given** a different slicer option with its own window, **When** the same contract is used, **Then** metric names and SQL text stay unchanged.

---

### User Story 6 - Remaining report visuals (Priority: P1)

A validation author covers the rest of the Alerts report: the top-10 settlements chart, the alerts map, and the policy-classification status. Warehouse SQL for these three is not confirmed. Each metric still executes a stub query from the Alerts SQL client. A missing database fails the test. Nothing skips that failure.

**Why this priority**: The scoped KPI contract only checks two cards per category. The map, the settlements chart, and the policy bar are on the same report and are unchecked.

**Independent Test**: The contract loads one `chart` metric, one `map` metric, and one `kpi` metric with `compare: text`. Unit tests show chart rows, map presence (`value` for a true zero, `empty` only when nothing is drawn), and string equality. The live parity test has no skip mark. A connection error from the Alerts database fails the test.

**Acceptance Scenarios**:

1. **Given** the top-10 settlements chart, **When** the contract is loaded, **Then** its `visual` is `chart` and its `name` is that chart's title anchor without the date-range slicer phrase.
2. **Given** the alerts map, **When** parity runs, **Then** the engine classifies the visual with `classify_presence`. A rendered 0 is `value`. No number and no data marks is `empty`.
3. **Given** the policy-classification visual, **When** parity runs, **Then** the metric stays `visual: kpi` with text comparison, and the engine reads the active status text (a phrase such as `הכרחית / מצומצמת`) instead of parsing a number.
4. **Given** the Alerts database is missing or refuses the connection, **When** the parity test runs, **Then** that error propagates. The test is not skipped and the error is not caught to force a pass.

---

### Edge Cases

- `visual` outside `kpi`, `gauge`, `chart`, and `map` fails at contract load with the metric name. `map` is a supported kind. A unit test that needs an illegal kind uses a different token (for example `sankey`).
- A gauge metric without `maximum_sql`, or a chart, map, or kpi metric without `sql_query`, fails at contract load. `compare` other than `number` or `text`, or `compare: text` on a gauge, chart, or map, fails at contract load.
- `category_id` is forwarded only when the metric sets it. A query that references `:category_id` without that field fails at execution rather than silently running unfiltered.
- Gauge maximum of 0 is a real bound and passes when the maximum query returns 0.
- Chart comparison is by label, not by visual order. Duplicate labels in the query or on the visual fail that metric.
- `series_index` past the row's values fails that category.
- Existing callers of `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` keep that signature.
- Inline comments added or edited by this feature are English only. Hebrew remains legal as data in the Alerts contract and page object.
- A `kpi` metric with `compare: text` does not call `KPI.number`. A non-numeric status is a string check, not a parse error and not a skip.
- Map presence uses `classify_presence`. Numeric 0 is `value` (true zero). `empty` is only the case with no number and no data marks. The engine does not store empty as 0.
- Stub SQL is executed. `pytest.skip`, `pytest.importorskip`, and `pytest.mark.skip` are not added to the Alerts parity test to hide a missing database.
- The settlements-chart anchor must match one visual. A shared prefix with the neighboring period-comparison chart is disambiguated in the contract without putting the slicer phrase into `name`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The parity engine MUST accept an optional per-metric `scope` and pass it to `KPI.number`, `KPI.read_text`, `KPI.scale`, `Chart.read`, and the map lookup. Blank scope MUST be treated as no scope.
- **FR-002**: Metrics MUST declare `visual` as `kpi` (default), `gauge`, `chart`, or `map`.
- **FR-002a**: A `kpi` metric MAY set `compare` to `number` (default) or `text`. `compare: text` MUST read the card text and compare strings. It MUST NOT call `KPI.number`.
- **FR-002b**: A `map` metric MUST classify the located visual with `classify_presence`. The check value is `value` or `empty`. A present 0 MUST be `value`. `empty` MUST be used only when every number is absent and the data-mark count is 0.
- **FR-003**: A `kpi` metric with `compare: number` (the default) MUST compare `KPI.number` to one scalar query. A `kpi` metric with `compare: text` MUST compare card text to one raw SQL cell and MUST NOT call `KPI.number`.
- **FR-004**: A `gauge` metric MUST compare `KPI.scale` `value` to `sql_query` and `maximum` to `maximum_sql`. Both checks MUST run and MUST be reported. `KPI.number` MUST NOT be used for gauges.
- **FR-005**: A `chart` metric MUST compare `Chart.read` categories to rows from the Alerts runner (label, number), using `series_index` (default 0).
- **FR-006**: `AlertsDBRunner` MUST accept `category_id` and bind it as `:category_id` via SQLAlchemy `text()`. Dates and the category id MUST NOT be interpolated into SQL.
- **FR-007**: The Alerts contract MUST replace the grouped `CategoryID IN ('1', '2', '10')` predicates with one bound `:category_id` per metric, covering ids `1`, `2`, and `10` separately for each measure that was previously grouped.
- **FR-008**: Category labels (UAV, Rockets, Terrorists), category ids, Hebrew titles, scopes, and SQL MUST live in the Alerts test package or `db/clients/alerts.py` parameter surface. They MUST NOT be added under `core/`.
- **FR-009**: Contract metric `name` values MUST be stable title anchors and MUST NOT include the date-range slicer phrase. The test owns the slicer selection and the date window.
- **FR-010**: A mismatch MUST raise one `AssertionError` listing every failed check (metric name, check, UI value, DB value) after all metrics have been compared.
- **FR-011**: Each UI read, query, and assertion MUST keep using the current run-report hooks (`log_kpi_read` or the equivalent visual log, `log_db_query`, `log_assertion`).
- **FR-012**: `docs/COVERAGE_CATALOG.md` MUST be updated so each Alerts measure maps to its visual kind, category id, and test.
- **FR-013**: New or edited inline comments MUST be English only.
- **FR-014**: `core/components/` MUST NOT be modified by this feature. Layer 2 readers from features 012–015 are consumed, not extended. Map presence MUST call the existing `classify_presence` helper. No `Map` class is added.
- **FR-015**: The Alerts contract MUST add the top-10 settlements chart (`visual: chart`), the alerts map (`visual: map`), and the policy-classification status (`visual: kpi`, `compare: text`). Titles are the report anchors with the date-range slicer phrase removed from `name`.
- **FR-016**: `db/clients/alerts.py` MUST define the stub SQL for those three metrics (a placeholder `SELECT`, two columns for the chart). The contract `sql_query` MUST be that stub. The statements are executed. They MUST NOT be replaced with a skip, a mocked success, or a swallowed exception.
- **FR-017**: `tests/ui/alerts_analysis_dashboard/test_db_parity.py` MUST NOT gain a skip for a missing or failing Alerts database. Connection and query errors propagate.

### Key Entities

- **Metric contract**: One YAML item. Identity is `name` plus optional `scope` and `category_id`. Kind is `visual`. `compare` selects number or text for a KPI. Queries are `sql_query` and, for gauges, `maximum_sql`.
- **Map presence**: `value` or `empty` from `classify_presence` on the map container. Not a count stored as 0 when the map is blank.
- **Status text**: The policy metric's UI value is the active status phrase, compared as text to one SQL cell.
- **Category binding**: Opaque string id supplied by the Alerts contract and bound by `AlertsDBRunner`. Labels are documentation in the Alerts package.
- **Parity check**: One comparison inside a metric (KPI number, KPI text, gauge value, gauge maximum, one chart category, or map presence).
- **Date window**: `start_date` / `end_date` computed by the test from the selected slicer option. Not part of the metric name.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/` stays report-agnostic. This feature does not add titles, scopes, category ids, Hebrew strings, or SQL there.
- **AC-002**: The Alerts page continues to compose `ReportShell` and `Slicer`. The date-range option remains a page/test string.
- **AC-003**: The engine stays in `tests/helpers/`. It may branch on generic visual kinds (`kpi`, `gauge`, `chart`, `map`, and text versus number). It must not interpret category labels or Hebrew status words.
- **AC-004**: `validate_dashboard_generic`'s positional signature stays. `KPI.number(title)` without a scope remains valid for metrics that omit `scope`.
- **AC-005**: `db/clients/alerts.py` may learn a `category_id` parameter and the three stub SQL constants. It must not hardcode ids `1`, `2`, or `10`, and it must not embed Hebrew.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Alerts `db_parity` test checks ids `1`, `2`, and `10` as separate bound filters, and no parity query still uses `CategoryID IN ('1', '2', '10')`.
- **SC-002**: Every gauge metric in the Alerts contract produces two checks (value and maximum). A unit test shows a maximum mismatch fails even when the value matches.
- **SC-003**: A unit test shows `scope` is forwarded, a blank scope is not, and a chart's labels are compared to runner rows.
- **SC-004**: Searching `core/` for `CategoryID`, the Alerts metric titles, and the slicer phrase finds no new matches from this feature.
- **SC-005**: Fleet smoke (`pytest tests/ui/fleet_dashboard/`) stays 100% green. This feature does not change Layer 0, Layer 2, or the fleet page.
- **SC-006**: Metric names in `alerts_contract.yaml` do not contain the 30-day slicer phrase, and the test still selects that phrase and binds a half-open 30-day window.
- **SC-007**: The Alerts contract contains the settlements chart, the map, and the policy status. A unit test shows map `0` is `value`, map-with-nothing is `empty`, and a text KPI compares strings. The live test file contains no `pytest.skip` / `importorskip` / `mark.skip`. A missing Alerts database still fails that test.

## Assumptions

- The category id set to split is the set already grouped in the pilot: `'1'`, `'2'`, and `'10'`. Which id is UAV, Rockets, or Terrorists is recorded only in the Alerts contract as a label. The engine never reads the label. The pairing is confirmed against the report or warehouse during implementation and is not invented inside `core/` or the engine.
- Title lookup stays substring-style (`re.escape` with no anchors), which features 014 and 015 already implement. Dropping the period phrase from `name` is enough for the same card to match after the slicer rewrites the suffix. No Layer 2 change is required for that.
- Chart queries return two columns: category label, then one numeric value. Multi-series charts set `series_index`. Legend names are not SQL keys.
- Gauge denominator is a second scalar query (`maximum_sql`) using the same date and category binds. It is not a literal in `core/`.
- The 30-day slicer option remains the first exercised state. The contract does not need a second state to satisfy FR-009; the test structure must allow one to be added without renaming metrics.
- Alerts visuals for each category are distinguishable by `scope` and title anchor while the date slicer is applied. A new category slicer is added on the Alerts page only if a visual is not in the iframe until that control is set. That control stays on the Alerts page.
- `core/components/kpi.py` and `core/components/chart.py` already provide `scope`, `KPI.scale`, and `Chart.read`. `core/components/visual.py` already provides `classify_presence`. This feature does not change those modules.
- The three added titles are taken from the Alerts report captured on 2026-10-13: map anchor `מפת התרעות ביישובים`, settlements-chart anchor `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`, policy-bar anchor `סיכון לפי מדיניות התגוננות ברגע`. The date suffix on the map and the ranking chart is not part of `name`. A second settlements chart (current period versus previous period) shares that ranking prefix; this slice contracts the ranking chart only, and the name must match one visual.
- The policy example `הכרחית / מצומצמת` is the shape of a status phrase, not the metric name. The screenshot shows the highlighted segment `פעילות הכרחית` among `פעילות מצומצמת`, `פעילות חלקית`, and `פעילות מלאה`. The contract does not hardcode the expected phrase; the query returns it. The stub returns the placeholder literal.
- Gauges visible on the same report stay on the existing gauge path. This slice does not invent `maximum_sql` for them.
