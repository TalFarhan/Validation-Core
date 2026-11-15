# Data Model: Alerts Contract Coverage

**Feature**: 017-alerts-contract-coverage | **Date**: 2026-10-13

The engine entities from feature 016 (`MetricContract` fields, `ParityResult`, date window) stay.
This feature adds rows. It does not add fields.

## ThreatCard

A KPI inside one threat section.

| Field | Required | Rule |
|-------|----------|------|
| `name` | yes | One of `היום`, `אתמול`, `סה"כ בטווח שנבחר` |
| `scope` | yes | One of the three threat sections below |
| `visual` | yes | `kpi` |
| `category_id` | yes | String paired with `scope` |
| `label` | no | English documentation. Engine ignores it |
| `sql_query` | yes | Equals `THREAT_KPI_STUB_SQL` (`SELECT 0`) |

| `scope` | `category_id` | `label` |
|---------|---------------|---------|
| `ירי רקטות וטילים` | `1` | `Rockets` |
| `חדירת מחבלים` | `2` | `Terrorists` |
| `חדירת כלי טיס עוין` | `10` | `UAV` |

Three names times three scopes is nine metrics. Identity is `(name, scope)`.

Validation:

- `category_id` is the quoted string, not an integer, so the file matches the existing contract.
- `scope` and `name` do not contain `שלושים יום`.
- No `maximum_sql`, no `compare: text`.

## GeneralCard

A KPI inside the population group or the warning-area group. Not filtered by category.

| Field | Required | Rule |
|-------|----------|------|
| `name` | yes | One of `היום`, `אתמול`, `סה"כ בטווח שנבחר` |
| `scope` | yes | `אוכלוסייה מותרעת` or `אזורי התרעה תחת ירי` |
| `visual` | yes | `kpi` |
| `category_id` | absent | These cards are general |
| `sql_query` | yes | `POPULATION_KPI_STUB_SQL` or `AREA_KPI_STUB_SQL`, both `SELECT 0` |

Six metrics. The scope is the stable base. A slicer suffix on the live accessible name is still
matched because lookup is unanchored. The scope value in the file does not include that suffix.

These rows are not the same metrics as the existing six category measures. Those keep
`name` equal to the base and `category_id` set. The new rows put the base in `scope` and the
time bucket in `name`.

## StaticComparisonChart

One chart that does not follow the time slicer.

| Field | Required | Rule |
|-------|----------|------|
| `name` | yes | `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת` |
| `visual` | yes | `chart` |
| `scope` | absent | The full title is unique |
| `category_id` | absent | |
| `series_index` | absent | Default 0 |
| `sql_query` | yes | Equals `PERIOD_COMPARISON_CHART_SQL` |

The name uses one yod in `ישובים`. The ranking chart's name uses two yods and stays a different
metric.

SQL rules:

- Two columns, aliases `category_label` and `metric_value`, so `rows()` can read the shape.
- `WHERE 1 = 0`, so the result is empty and no NULL label is returned.
- No `:start_date`, no `:end_date`, no `AlertDate`. The runner may still pass the date dict.

## StubStatement

A module-level string on `AlertsDBRunner`'s module. Not a query builder.

| Constant | Text | Used by |
|----------|------|---------|
| `THREAT_KPI_STUB_SQL` | `SELECT 0` | Nine threat cards |
| `POPULATION_KPI_STUB_SQL` | `SELECT 0` | Three population cards |
| `AREA_KPI_STUB_SQL` | `SELECT 0` | Three warning-area cards |
| `PERIOD_COMPARISON_CHART_SQL` | Empty two-column `SELECT` | The static chart |

The constant text contains no Hebrew and no category id. The YAML copies the text into
`sql_query`. The engine executes the YAML string.

Existing constants `SETTLEMENTS_CHART_SQL`, `MAP_PRESENCE_SQL`, and `POLICY_STATUS_SQL` stay.

## Unchanged rows

| Metric | Why it stays |
|--------|----------------|
| Six category KPIs named `אזורי התרעה תחת ירי` and `אוכלוסייה מותרעת` | Confirmed warehouse SQL, ids `1`, `2`, `10` |
| Ranking chart `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` | Different title and different stub |
| Map `מפת התרעות ביישובים` | Out of this slice |
| Policy `סיכון לפי מדיניות התגוננות ברגע` | Out of this slice |

## Relationships

- A `ThreatCard` scope maps to exactly one `category_id`. The runner binds that id only because
  the YAML sets the field. The stub text ignores the bind until a later SQL replacement uses it.
- A `GeneralCard` has no category relationship.
- `StaticComparisonChart` has no date-window relationship. The test may still select a slicer
  for the other metrics. This chart's result does not change with that window.

## State

No lifecycle. A row is either present in the contract or not. Load fails closed on the feature
016 rules (missing `sql_query`, illegal `visual`, gauge without `maximum_sql`). This feature
adds no new load error.
