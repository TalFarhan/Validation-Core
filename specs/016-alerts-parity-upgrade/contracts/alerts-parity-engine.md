# Contract: Alerts DB Parity Engine Upgrade

**Feature**: 016-alerts-parity-upgrade | **Date**: 2026-10-13

Extends the feature 010 engine contract. `KPI` and `Chart` keep the feature 014 and 015 surfaces.
This document is the caller contract for the engine, the Alerts runner, and the Alerts YAML.

## 1. Engine — `tests/helpers/db_parity_engine.py`

```python
def validate_dashboard_generic(
    yaml_path: str | Path,
    page,            # ReportShell page; exposes _report_frame()
    db_client,       # AlertsDBRunner or a fake with scalar(), rows(), and cell()
    start_date,      # datetime | date
    end_date,        # datetime | date
) -> list[ParityResult]:
    """Load metrics, compare each visual to the warehouse, assert every check."""
```

```python
@dataclass(frozen=True)
class ParityResult:
    name: str
    check: str                 # "value" | "maximum" | "presence" | <chart category label>
    ui_value: int | float | str | None
    db_value: int | float | str | None
    passed: bool
```

Rules:

- Signature stays these five positional parameters. No new required argument.
- Build one `KPI` and one `Chart` from `page.page` and `page._report_frame()`.
- Normalize scope: missing, `""`, or whitespace-only → `None`. Otherwise pass the string through.
- Normalize `category_id`: missing or blank → do not pass the kwarg. Otherwise `str(category_id)`.
- Do not read metric `label`. Do not modify `name`.
- `visual` default is `kpi`. Allowed values are `kpi`, `gauge`, `chart`, and `map`. Any other value raises `ValueError` naming the metric before any query.
- `compare` defaults to `number`. Allowed values are `number` and `text`. `text` is legal only on `kpi`.
- On numeric KPI: `ui = kpi.number(name, scope=scope)`; `db = db_client.scalar(...)` when the id is set. One `ParityResult` with `check="value"`. Log `log_kpi_read` when a run report is active.
- On text KPI: `ui = kpi.read_text(name, scope=scope)` with bidi marks removed and whitespace collapsed. `db = db_client.cell(...)`. Compare strings. Do not call `KPI.number`. One `ParityResult` with `check="value"`.
- On gauge: `scale = kpi.scale(name, scope=scope)`. Do not call `KPI.number`. Compare `scale["value"]` to `sql_query` and `scale["maximum"]` to `maximum_sql`. A `None` value, a `None` maximum, or `state == "empty"` fails that side. Log both reads.
- On chart: `reading = chart.read(name, scope=scope)`; `db_rows = db_client.rows(...)`. Match by label using `series_index` (default 0) as in [data-model.md](../data-model.md). Log each check with `log_assertion`.
- On map: locate the titled container (see [data-model.md](../data-model.md)), then `classify_presence`. Compare the UI state to the state mapped from `db_client.cell`. Check name is `presence`. A raw non-numeric cell fails and is reported as `db_value`. Do not coerce that failure into `empty` or `0`.
- `log_db_query` remains inside the runner. `log_assertion` filters include `start_date`, `end_date`, and `category_id` when set, plus `scope` when set.
- After every metric, raise one `AssertionError` if any check failed. The message includes `name`, `check`, `ui_value`, and `db_value` for each failure.
- The engine MUST NOT contain Hebrew, Alerts titles, category id literals, or SQL.

Loader errors (before UI or SQL):

- Missing or empty `metrics`.
- Metric without `name` or `sql_query`.
- `visual` not in `kpi`, `gauge`, `chart`, `map`.
- `compare` not in `number`, `text`, or `compare: text` on a non-KPI metric.
- `gauge` without `maximum_sql`.
- `maximum_sql` present on `kpi`, `chart`, or `map`.
- `series_index` present and not an int `>= 0`.

## 2. Alerts runner — `db/clients/alerts.py`

```python
class AlertsDBRunner:
    def scalar(
        self,
        sql: str,
        *,
        start_date,                  # datetime | date
        end_date,                    # datetime | date
        category_id: str | None = None,
    ) -> int | float: ...

    def rows(
        self,
        sql: str,
        *,
        start_date,
        end_date,
        category_id: str | None = None,
    ) -> list[tuple[str, int | float | None]]: ...

    def cell(
        self,
        sql: str,
        *,
        start_date,
        end_date,
        category_id: str | None = None,
    ) -> int | float | str | None: ...
```

Rules:

- Execute with `sqlalchemy.text(sql)` and a params dict. Never format dates or `category_id` into the SQL string.
- Params always include `start_date` and `end_date`. Include `category_id` only when the argument is not `None`.
- `scalar`: NULL → `0`; integral floats → `int`; otherwise `float`. Same as today.
- `rows`: each row is `(str(label).strip(), number)`. A NULL value becomes `None`, not `0`. A NULL or blank label raises `ValueError`.
- `cell`: first column only. SQL NULL stays `None` (not `0`). A string is returned stripped. A number uses the same numeric coercion as `scalar`. Log method name `alerts.cell`.
- All three methods log `log_db_query` with the params that were bound.
- Module-level stub constants, with no Hebrew and no category ids:

  ```text
  SETTLEMENTS_CHART_SQL = "SELECT 'placeholder' AS category_label, CAST(NULL AS int) AS metric_value"
  MAP_PRESENCE_SQL = "SELECT 'placeholder'"
  POLICY_STATUS_SQL = "SELECT 'placeholder'"
  ```

  The chart constant has two columns so `rows()` can read it. Map and policy constants are one cell for `cell()`.
- The runner MUST NOT hardcode `'1'`, `'2'`, `'10'`, Hebrew, or a category label. It MUST NOT import from `core.components` or from the Alerts test package.

## 3. YAML — `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`

Schema is section 1 of the data model. Additional Alerts-file rules:

- Comments in this file are English.
- Metric `name` values MUST NOT contain `שלושים יום אחרונים`.
- The two current measures are repeated once per category id `1`, `2`, and `10`, with `CategoryID = :category_id` instead of `CategoryID IN ('1', '2', '10')`.
- `label` may record UAV, Rockets, or Terrorists only after the author confirms the id. The engine ignores `label`.
- Gauge entries use titles taken from the report. Do not invent a gauge title or a `maximum_sql`.
- The file also contains the three remaining visuals. `sql_query` for each equals the matching constant in `db/clients/alerts.py`:

  | `name` | `visual` | other fields | SQL constant |
  |--------|----------|--------------|--------------|
  | `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` | `chart` | no `category_id` | `SETTLEMENTS_CHART_SQL` |
  | `מפת התרעות ביישובים` | `map` | no `category_id` | `MAP_PRESENCE_SQL` |
  | `סיכון לפי מדיניות התגוננות ברגע` | `kpi` | `compare: text` | `POLICY_STATUS_SQL` |

  If the settlements anchor matches two charts, extend that `name` with stable words that are not the slicer phrase (research R13). Do not add the period-comparison chart here.
- `scope`, when set, is the section accessible name, not a CSS id.

## 4. Test — `tests/ui/alerts_analysis_dashboard/test_db_parity.py`

- Stays `@pytest.mark.db_parity`.
- Still selects `שלושים יום אחרונים` through `dashboard.select_date_range`.
- Still computes the half-open 30-day window in the test and passes `datetime` objects into the engine.
- Does not pass category ids as engine arguments; they travel inside the YAML.
- If a visual is not in the iframe until a category control is selected, the selection is a new method on `AlertsAnalysisPage` that uses the existing `Slicer`. The test loops those selections. The engine signature does not grow a slicer parameter.
- The test MUST NOT call `pytest.skip`, `pytest.importorskip`, or `pytest.mark.skip` when the Alerts database is missing, refuses the connection, or rejects a stub query. Those errors propagate. The stub is not a reason to skip.

## 5. Unchanged surfaces

- `core/components/kpi.py`, `core/components/chart.py`, and `core/components/visual.py` (FR-014).
- `KPI.number` / `extract_kpi_value_text` / `normalize_kpi_text` results.
- `config/settings.py` `DB_ALERTS_NAME` and the `db_parity` marker.
- Fleet page objects and fleet chart tooltip / drilldown / hover.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Scope forwarded; blank scope is `None` | `tests/unit/test_db_parity_engine.py` |
| Gauge maximum mismatch fails when value matches; `0` matches | `tests/unit/test_db_parity_engine.py` |
| Chart labels, NULL cell, empty visual | `tests/unit/test_db_parity_engine.py` |
| Map `0` is `value`; no number and no marks is `empty`; `'placeholder'` fails the presence check | `tests/unit/test_db_parity_engine.py` |
| Text KPI compares strings and does not call `KPI.number` | `tests/unit/test_db_parity_engine.py` |
| Alerts parity test has no skip for a database error | Review of `test_db_parity.py` |
| `category_id` forwarded as a string and omitted when absent | `tests/unit/test_db_parity_engine.py` |
| Live Alerts UI equals warehouse per id | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| No new domain strings under `core/` | Review: `core/` diff is empty for this feature |
| Fleet smoke | `pytest tests/ui/fleet_dashboard/` |
