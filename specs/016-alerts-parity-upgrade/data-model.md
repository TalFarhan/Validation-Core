# Phase 1 Data Model: Alerts DB Parity Upgrade

Runtime and YAML shapes. No new tables. Confirmed KPI SQL still reads `[FACT].[AlertsRedWeb]`.
The three new visuals execute the stub constants in `db/clients/alerts.py` until real SQL is confirmed.

## Entity: MetricContract (one `metrics[]` item)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | yes | Stable UI title anchor. Opaque. Must not contain the date-range slicer phrase. |
| `visual` | `kpi` \| `gauge` \| `chart` \| `map` | no | Default `kpi`. |
| `compare` | `number` \| `text` | no | KPI only. Default `number`. `text` reads `KPI.read_text` and compares strings. |
| `scope` | string | no | Passed to the Layer 2 reader. Missing, `""`, or whitespace becomes `None`. |
| `category_id` | string | no | Alerts domain. Stringified before bind (`1` and `"1"` both bind as `"1"`). Omitted means the key is not sent. |
| `label` | string | no | Documentation only (for example UAV). The engine MUST ignore it. |
| `sql_query` | string | yes | Numeric `kpi` and `gauge`: one scalar. Text `kpi` and `map`: one cell via `cell()`. `chart`: label column then value column. Binds `:start_date`, `:end_date`, and `:category_id` when the statement names them and the metric sets `category_id`. |
| `maximum_sql` | string | gauge only | Scalar for `KPI.scale` `maximum`. Same binds as `sql_query`. Forbidden on `kpi`, `chart`, and `map` (loader error). |
| `series_index` | int | no | Chart only. Default `0`. Which cell in `category.values` to compare. |

Validation rules:

- Root MUST be a mapping with a non-empty `metrics` list.
- `name` and `sql_query` MUST be non-empty strings.
- `visual` MUST be one of `kpi`, `gauge`, `chart`, `map`.
- `compare` MUST be omitted, `number`, or `text`. `text` is legal only on `kpi`.
- `gauge` MUST include non-empty `maximum_sql`. `map` MUST NOT set `maximum_sql`.
- `series_index` MUST be an int `>= 0` when present.
- `sql_query` / `maximum_sql` MUST NOT be built with Python format placeholders. Dates and category ids are named binds.
- The Alerts file MUST NOT contain `CategoryID IN ('1', '2', '10')` after this feature. Each of those ids appears as its own metric's `category_id`.

### Example shape (domain file only)

Titles below are the current contract anchors with the date suffix removed. `label` is not a
guess at implementation time until the author confirms it; the sample uses the field so the
engine's "ignore label" rule is visible. Ids are the existing set, not a claimed name mapping.

```yaml
metrics:
  - name: "אזורי התרעה תחת ירי"
    visual: kpi
    scope: "<section accessible name, or omit>"
    category_id: "1"
    label: "<UAV | Rockets | Terrorists after confirmation>"
    sql_query: >
      SELECT COUNT(DISTINCT [WarningZoneName])
      FROM [FACT].[AlertsRedWeb]
      WHERE AlertDate >= :start_date AND AlertDate < :end_date
        AND CategoryID = :category_id

  - name: "<gauge title anchor>"
    visual: gauge
    scope: "<section accessible name, or omit>"
    category_id: "1"
    sql_query: >
      SELECT <numerator>
      FROM [FACT].[AlertsRedWeb]
      WHERE AlertDate >= :start_date AND AlertDate < :end_date
        AND CategoryID = :category_id
    maximum_sql: >
      SELECT <denominator>
      FROM [FACT].[AlertsRedWeb]
      WHERE AlertDate >= :start_date AND AlertDate < :end_date
        AND CategoryID = :category_id

  - name: "<chart title anchor>"
    visual: chart
    category_id: "1"
    series_index: 0
    sql_query: >
      SELECT <label_column>, <value_column>
      FROM [FACT].[AlertsRedWeb]
      WHERE AlertDate >= :start_date AND AlertDate < :end_date
        AND CategoryID = :category_id
      GROUP BY <label_column>
```

The population KPI keeps its current shape (`ISNULL` of the per-area max) with the same date and
category binds, and the same stable-name rule.

The three remaining visuals do not set `category_id`. Their `sql_query` is the matching constant
from `db/clients/alerts.py` (research R16). Comments in the YAML stay English.

```yaml
metrics:
  - name: "עשרת היישובים עם כמות ההתרעות הגבוהה ביותר"
    visual: chart
    sql_query: >
      SELECT 'placeholder' AS category_label, CAST(NULL AS int) AS metric_value

  - name: "מפת התרעות ביישובים"
    visual: map
    sql_query: "SELECT 'placeholder'"

  - name: "סיכון לפי מדיניות התגוננות ברגע"
    visual: kpi
    compare: text
    sql_query: "SELECT 'placeholder'"
```

The chart `name` is extended only if that anchor matches more than one visual (research R13).
The policy `name` is the bar caption. The status phrase is the runtime UI value, not a YAML field.

## Entity: ParityCheck (engine result, replaces the single-number assumption)

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Metric `name`. |
| `check` | string | `value`, `maximum`, `presence`, or the chart category label. |
| `ui_value` | int \| float \| str \| None | Number for numeric KPI and gauge. String for text KPI and for map `value` / `empty`. |
| `db_value` | int \| float \| str \| None | Scalar, gauge bound, chart cell, status text, or map state. A non-numeric map cell is reported raw. |
| `passed` | bool | `ui_value == db_value` after the map cell is mapped to a state, or exact string equality for text. |

`validate_dashboard_generic` still returns `list[ParityCheck]` (the dataclass may keep the name
`ParityResult` with these fields). One gauge metric appends two checks. One chart metric appends
one check per union of UI labels and DB labels. After the loop, one `AssertionError` lists every
failed check.

Numeric equality is exact (`==`), same as today. No tolerance.

## Entity: Gauge reading (consumed, not redefined)

From `KPI.scale` (feature 015). The engine uses `state`, `value`, and `maximum`. `minimum` is not
a check.

| Condition | Result |
|-----------|--------|
| `state == "empty"` or `value is None` | Value check fails. |
| `maximum is None` | Maximum check fails. |
| Both numbers present, including 0 | Compare to the two scalars. |

## Entity: Chart reading (consumed, not redefined)

From `Chart.read` (feature 015).

| UI | DB `rows()` | Result |
|----|-------------|--------|
| `state == "empty"`, no categories | `[]` | Pass. |
| `state == "empty"` | one or more rows | Fail. |
| categories present | `[]` | Fail. |
| label on both sides, cell equals value | match | Pass for that label. |
| label on one side only | — | Fail. |
| duplicate label | — | Fail. |
| `series_index` out of range | — | Fail that label. |
| cell `None` and SQL NULL | both `None` | Pass. |

## Entity: Map presence (engine, using feature 015)

`classify_presence` is not redefined. The engine supplies `numbers` and `count_data_marks`.

| Container | `numbers` | `mark_count` | UI state |
|-----------|-----------|--------------|----------|
| Visible 0, no pins required | `[0]` | any | `value` (true zero) |
| Any other parsed number | `[n]` | any | `value` |
| No number, one or more data marks | `[None]` | `> 0` | `value` |
| No number, no data marks | `[None]` | `0` | `empty` |

| `cell()` result | Expected state |
|-----------------|----------------|
| `None` | `empty` |
| numeric `0` | `value` |
| any other number | `value` |
| anything else, including `'placeholder'` | fail; `db_value` is that raw cell |

## Entity: Text KPI

| UI | DB `cell()` | Result |
|----|-------------|--------|
| `KPI.read_text`, bidi marks removed, whitespace collapsed | stripped string | Pass when equal |
| status phrase | `'placeholder'` | Fail, both strings in the assertion |
| call | `KPI.number` | Not used |

## Entity: AlertsDBRunner binds

| Method | Params | Result |
|--------|--------|--------|
| `scalar(sql, *, start_date, end_date, category_id=None)` | Always dates. `category_id` only when not `None`. | One int or float. SQL NULL → `0`. |
| `rows(sql, *, start_date, end_date, category_id=None)` | Same binds. | List of `(label: str, value: int \| float \| None)`. SQL NULL value stays `None`. NULL label is a runner error. |
| `cell(sql, *, start_date, end_date, category_id=None)` | Same binds. | First column. SQL NULL stays `None`. A string is stripped. A number uses scalar's numeric coercion. |

Both methods execute `sqlalchemy.text(sql)` and log `log_db_query`. Read-only `SELECT` only.

## Entity: Date window (test-owned, not a contract field)

| Piece | Owner | Notes |
|-------|-------|-------|
| Slicer option `שלושים יום אחרונים` | `test_db_parity.py` via `select_date_range` | Not part of `name`. |
| `end_date = now`, `start_date = end_date - 30 days` | Test | Half-open `[start, end)`. Passed as `datetime` objects. |
| Another slicer state | Test, later | Same YAML names. New window next to the new option. |

## Relationships

```text
test_db_parity.py                          # domain: slicer option + window
  └── validate_dashboard_generic(...)      # tests/helpers
        ├── YAML metric.scope ──────────► KPI.number / KPI.read_text / KPI.scale / Chart.read
        │                                  # map uses scope_host + classify_presence
        │                                  # core/components, unchanged
        ├── YAML metric.category_id ────► AlertsDBRunner.scalar / rows / cell
        │     └── text() binds :start_date, :end_date, :category_id
        └── YAML label                     # ignored by the engine
```

`core/` has no edge to category ids, Hebrew titles, or SQL.
