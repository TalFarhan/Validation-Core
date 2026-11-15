# Phase 1 Data Model: Generic DB Parity Engine + Alerts Pilot

This feature introduces lightweight runtime entities (no persistence). "Fields" describe in-memory shapes and
the declarative YAML contract schema.

## Entity: MetricContract (one `metrics[]` item in the YAML)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | The UI KPI card title text (opaque to `core/`). Matched inside the Power BI iframe. May contain Hebrew + RTL marks. |
| `sql_query` | string | yes | Parameterized SQL returning a **single scalar**. MUST use named binds `:start_date` / `:end_date`. |

Validation rules:
- The contract root MUST contain a `metrics:` list with ≥ 1 item.
- Each item MUST have non-empty `name` and `sql_query`.
- `sql_query` MUST NOT contain Python format placeholders (`{`...`}` / `%s`); binds are `:start_date` /
  `:end_date` only. (Guard is advisory; binding is enforced by using `text()`.)

### Example (`tests/ui/alerts_dashboard/alerts_contract.yaml`)

```yaml
metrics:
  - name: "אזורי התרעה תחת יריי בשלושים יום האחרונים"
    sql_query: >
      SELECT COUNT(DISTINCT [WarningZoneName])
      FROM [FACT].[AlertsRedWeb]
      WHERE AlertDate >= :start_date AND AlertDate < :end_date
        AND CategoryID IN ('1', '2', '10')
  - name: "אוכלוסיה מותרעת בשלושים יום האחרונים"
    sql_query: >
      SELECT ISNULL(SUM(LesserWarningAreaPopulation), 0)
      FROM (
        SELECT LesserWarningAreaID,
               MAX(LesserWarningAreaPopulation) AS LesserWarningAreaPopulation
        FROM [FACT].[AlertsRedWeb]
        WHERE AlertDate >= :start_date AND AlertDate < :end_date
          AND CategoryID IN ('1', '2', '10')
        GROUP BY LesserWarningAreaID
      ) A
```

## Entity: KPI (Layer 2 component, `core/components/kpi.py`)

Composed by a caller with a Power BI iframe `FrameLocator`. Holds **no** report-specific strings.

| Member | Type | Notes |
|--------|------|-------|
| `__init__(page, frame, timeout_ms=None)` | ctor | Mirrors `Slicer.__init__`; `frame` is the report iframe `FrameLocator`. |
| `card(title: str) -> Locator` | method | Locate a KPI card by title: `frame.get_by_role("button", name=re.compile(re.escape(title)))` (same strategy as fleet `_kpi_card`). |
| `read_text(title: str) -> str` | method | Raw value text from the card value node (`card.locator("p").last`), awaited visible. |
| `value(title: str) -> str` | method | Normalized string form of the KPI (see normalization). |
| `number(title: str) -> int \| float` | method | Numeric form parsed from the normalized string. |

Normalization (pure helper `normalize_kpi_text(raw) -> str`):
- Remove RTL/LTR marks `\u200f`, `\u200e`.
- Remove thousands separators `,`.
- Collapse/strip whitespace including NBSP `\u00a0`.
- Return the cleaned string; `number(...)` casts to `int` when integral, else `float`.

## Entity: AlertsDBRunner (`db/clients/alerts.py`)

| Member | Type | Notes |
|--------|------|-------|
| `__init__(engine=None)` | ctor | Defaults to `create_db_engine(database=settings.DB_ALERTS_NAME)`. |
| `scalar(sql: str, *, start_date, end_date) -> int \| float` | method | `conn.execute(text(sql), {"start_date": start_date, "end_date": end_date}).scalar()`; logs via `log_db_query`; coerces numeric result. |

Rules:
- Read-only. No DDL/DML. Only `SELECT` via `text()` with bound params.
- Dates passed as Python `datetime`/`date`; never string-formatted into SQL.

## Entity: ParityResult (engine internal, `tests/helpers/db_parity_engine.py`)

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Metric name from contract. |
| `ui_value` | int \| float | Normalized UI KPI number. |
| `db_value` | int \| float | Scalar from the Alerts DB runner. |
| `passed` | bool | `ui_value == db_value`. |

`validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)`:
- Loads the YAML contract (`yaml.safe_load`).
- Builds a `KPI` from the page's report iframe `FrameLocator`.
- For each metric: `ui = kpi.number(name)`; `db = db_client.scalar(sql_query, start_date=..., end_date=...)`;
  records a `ParityResult`; logs `log_kpi_read` / `log_db_query` / `log_assertion`.
- Asserts every `ParityResult.passed`; on failure raises `AssertionError` listing each mismatching metric
  (name, ui, db).

## Relationships

```text
test_db_parity.py
  ├── selects date range via  Slicer (core/components/slicer.py)         [Layer 2, unchanged]
  ├── computes start_date/end_date (Python, 30-day half-open window)
  └── calls validate_dashboard_generic(yaml, page, alerts_db, start, end) [tests/helpers]
        ├── reads UI via  KPI (core/components/kpi.py)                     [Layer 2, NEW]
        ├── reads DB via  AlertsDBRunner (db/clients/alerts.py)           [NEW]
        │       └── create_db_engine(database=DB_ALERTS_NAME)             [db/connection.py, reused]
        └── loads  alerts_contract.yaml                                   [tests/ui/alerts_dashboard, NEW]
```
