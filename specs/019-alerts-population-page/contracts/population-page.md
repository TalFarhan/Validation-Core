# Contract: Alerts Population Page

**Feature**: 019-alerts-population-page | **Date**: 2026-10-14

UI identities and contract rows for the second page of the Alerts Analysis report.
`validate_dashboard_generic` still accepts `(yaml_path, page, db_client, start_date, end_date)`
positionally. An optional keyword `exclude_scopes` skips metrics by scope. This feature does not
compare page-2 visuals to SQL.

## 1. Page object

File: `pages/alerts_analysis/population_page.py`

Class: `AlertsPopulationPage(AlertsAnalysisPage)`

| Member | Contract |
|--------|----------|
| `PAGE_TITLE` | Exact page-tab accessible name. Every new YAML `scope` equals this. |
| `DISTRICT_CHART` | `התרעות לפי מחוז` |
| `SETTLEMENT_CHART` | `אוכלוסייה לפי יישוב` |
| `WARNED_SERIES` | `מותרעות` |
| `UNWARNED_SERIES` | `לא מותרעות` |
| Hour, dates, and three card title constants | Stable prefixes copied from the live page. No `בין` suffix. |
| `before_report_ready_check` | Selects the `PAGE_TITLE` tab if the district anchor is not showing. Safe to call twice. |
| `_report_ready_locator` | District anchor inside the report iframe. Not the catalog product name. |
| `clear_filters` | `Slicer.clear_all`. |
| `set_between_dates(start, end)` | Between-dates control on this page. |
| `set_day_night(mode)` | `mode` is `off`, `day`, or `night`. |
| `set_value_range(low, high)` | Numeric range. The clear test calls `set_value_range(0, 349)`. |
| `set_district_aggregation(mode)` | `mode` is `sum` or `average`. |
| `read_card(role)` | `role` is `total`, `warned`, or `unprotected`. Returns a number via `KPI.number(title, scope=PAGE_TITLE)`. |
| `chart_total(title, series_index=0)` | Sum of numeric cells from `Chart.read(title, scope=PAGE_TITLE)`. Fails on `state="empty"` or a `None` cell at `series_index`. |

Locators for the tab and the non-dropdown slicers stay in this module. Do not add them under `core/`.

`pages/alerts_analysis/page.py` is unchanged.

## 2. Suite fixture

File: `tests/ui/alerts_analysis_dashboard/conftest.py`

```python
population_dashboard = bind_dashboard(AlertsPopulationPage)
```

`dashboard` remains `bind_dashboard(AlertsAnalysisPage)`.

## 3. YAML rows

File: `data/alerts/alerts_contract.yaml`

Comments stay English. Hebrew appears only as data. Append. Do not rewrite page-1 metrics.

Scope on every row below is `AlertsPopulationPage.PAGE_TITLE` (the same string, not a second spelling).

Known names:

```yaml
  - name: "התרעות לפי מחוז"
    scope: "<PAGE_TITLE>"
    visual: chart
    sql_query: "<POPULATION_PAGE_CHART_STUB_SQL>"

  - name: "אוכלוסייה לפי יישוב"
    scope: "<PAGE_TITLE>"
    visual: chart
    series_index: 0
    label: "מותרעות"
    sql_query: "<POPULATION_PAGE_CHART_STUB_SQL>"

  - name: "אוכלוסייה לפי יישוב"
    scope: "<PAGE_TITLE>"
    visual: chart
    series_index: 1
    label: "לא מותרעות"
    sql_query: "<POPULATION_PAGE_CHART_STUB_SQL>"
```

Plus five copied rows: three `visual: kpi` cards (`SELECT 0`) and two `visual: chart` rows
(24-hour, dates) using the chart stub. Their `name` values follow the `בין` cut in
[data-model.md](../data-model.md). No `category_id`. No `maximum_sql`.

`sql_query` in the file is the constant's text, not a Python name. The unit test imports the
constant and compares.

## 4. Placeholder SQL

File: `db/clients/alerts.py`

```python
# Population page placeholders. Not executed by the population UI tests.
# The page-1 parity test excludes this page's scope.
#
# Future rules when these constants are replaced:
# - Half-open dates: AlertDate >= :start_date AND AlertDate < :end_date.
# - One grouping grain at a time, from district down to settlement.
#   Do not add a parent total to its children.
# - Sum mode is SUM of the grouped measure.
#   Average mode is that SUM divided by the group count
#   (SUM / NULLIF(COUNT, 0)), not a second measure.
POPULATION_PAGE_KPI_STUB_SQL = "SELECT 0"
POPULATION_PAGE_CHART_STUB_SQL = (
    "SELECT CAST(NULL AS nvarchar(200)) AS category_label, "
    "CAST(NULL AS int) AS metric_value WHERE 1 = 0"
)
```

The chart text MUST NOT contain `:start_date`, `:end_date`, or `AlertDate`.

Do not add a runner method. Do not wrap `connect` in `try/except`.

## 5. Engine keyword

File: `tests/helpers/db_parity_engine.py`

```text
validate_dashboard_generic(
    yaml_path, page, db_client, start_date, end_date, *, exclude_scopes=None
)
```

- `exclude_scopes is None` or empty: existing behavior, every metric runs.
- Otherwise skip a metric when `_normalize_scope(metric)` is in the set.
- Skipped metrics produce no `ParityResult`, no UI read, and no SQL call.

File: `tests/ui/alerts_analysis_dashboard/test_db_parity.py`

Pass `exclude_scopes={AlertsPopulationPage.PAGE_TITLE}`. Do not add a skip marker. Do not catch
connection errors.

## 6. Snapshot and UI tests

File: `tests/ui/alerts_analysis_dashboard/population_snapshot.py`

`take_snapshot(page) -> PopulationSnapshot` reads the three cards and the five totals in
[data-model.md](../data-model.md) section 3.

`same_snapshot(left, right) -> bool` is exact equality on every field.

File: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`

| Test | Asserts |
|------|---------|
| `test_clear_restores_population_snapshot` | Snapshot, then between-dates, day, night, and `set_value_range(0, 349)`. At least one field changes. `clear_filters` restores every field. |
| `test_day_plus_night_equals_untoggled_sum` | Dates-chart total: `day + night == off`. |
| `test_hour_date_and_district_sums_match` | After `set_district_aggregation("sum")` and a clear slicer state: 24-hour total, dates total, and district total are equal. |
| `test_population_cards_within_total` | Warned ≤ total and unprotected ≤ total. |

No test in this file imports `AlertsDBRunner` or calls `validate_dashboard_generic`.

A series check, in this file or the unit file's live-free cousin:

`Chart.read(SETTLEMENT_CHART, scope=PAGE_TITLE).series[0] == "מותרעות"` and index 1 is
`לא מותרעות`. That check needs the browser, so it lives in the UI module. The unit test only
checks that the YAML indexes differ and that the labels are those two strings.

## 7. Unit checks (no browser)

File: `tests/unit/test_db_parity_engine.py`

Load `data/alerts/alerts_contract.yaml` and assert:

- Every metric whose `label` is `מותרעות` or `לא מותרעות`, and every metric whose `name` is
  `התרעות לפי מחוז` with `scope == PAGE_TITLE`, uses that scope.
- The two settlement rows exist, their `series_index` values are `{0, 1}` unless a live legend
  fix has swapped them, and their labels are the two series names. After a swap the test expects
  the indexes actually written; it still expects both indexes and both labels.
- No page-2 `name` contains `בין`.
- Page-2 card SQL equals `POPULATION_PAGE_KPI_STUB_SQL`.
- Page-2 chart SQL equals `POPULATION_PAGE_CHART_STUB_SQL` and does not contain `AlertDate` or
  `:start_date`.
- `PAGE_TITLE` is not a substring of a page-1 scope and no page-1 scope is a substring of it.
- Page-1 metrics are still present (the six category KPIs, the ranking chart, the map, the
  policy status, the time buckets, the static comparison chart).
- A temporary contract plus `exclude_scopes` runs only the metrics outside that set.
- `test_db_parity.py` source contains `exclude_scopes` and contains no `pytest.skip`,
  `importorskip`, or `mark.skip`.

## 8. Catalog

File: `docs/COVERAGE_CATALOG.md`

Add a subsection under section 8. State that page-2 metrics are UI identities plus unconfirmed
placeholders, and that `test_db_parity.py` excludes their scope. Point at
`pages/alerts_analysis/population_page.py` and
`tests/ui/alerts_analysis_dashboard/test_population_invariants.py`.

The older bullet that still says the alerts page object lives under
`tests/ui/alerts_analysis_dashboard/page.py` is updated to `pages/alerts_analysis/page.py` in
the same edit, because that path is the page this feature extends.

## 9. Out of scope

- Replacing either placeholder with warehouse SQL.
- Calling `rows` or `scalar` from the new UI tests.
- Drilldown from district to settlement.
- Tooltip checks.
- A new `SlicerKind`.
- Edits under `core/`.
- Fleet page or fleet tests.
