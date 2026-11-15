# Contract: Alerts YAML Coverage

**Feature**: 017-alerts-contract-coverage | **Date**: 2026-10-13

Extends the feature 016 YAML and the Alerts SQL constants. The engine contract is unchanged.
`validate_dashboard_generic` still takes `(yaml_path, page, db_client, start_date, end_date)`.

## 1. New YAML rows

File: `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml`

Comments in this file stay English. Hebrew appears only as data.

Threat cards. Repeat this shape for every pair in the table. `sql_query` is `THREAT_KPI_STUB_SQL`.

```yaml
  - name: "היום"
    scope: "ירי רקטות וטילים"
    visual: kpi
    category_id: "1"
    label: Rockets
    sql_query: "SELECT 0"
```

| `scope` | `category_id` | `label` | names |
|---------|---------------|---------|-------|
| `ירי רקטות וטילים` | `"1"` | `Rockets` | `היום`, `אתמול`, `סה"כ בטווח שנבחר` |
| `חדירת מחבלים` | `"2"` | `Terrorists` | same three |
| `חדירת כלי טיס עוין` | `"10"` | `UAV` | same three |

Quote `סה"כ בטווח שנבחר` so the double quote is data. In YAML, single quotes do that:
`'סה"כ בטווח שנבחר'`.

General cards. No `category_id`. No `label`. No `maximum_sql`.

```yaml
  - name: "היום"
    scope: "אוכלוסייה מותרעת"
    visual: kpi
    sql_query: "SELECT 0"

  - name: "אתמול"
    scope: "אוכלוסייה מותרעת"
    visual: kpi
    sql_query: "SELECT 0"

  - name: 'סה"כ בטווח שנבחר'
    scope: "אוכלוסייה מותרעת"
    visual: kpi
    sql_query: "SELECT 0"

  - name: "היום"
    scope: "אזורי התרעה תחת ירי"
    visual: kpi
    sql_query: "SELECT 0"

  - name: "אתמול"
    scope: "אזורי התרעה תחת ירי"
    visual: kpi
    sql_query: "SELECT 0"

  - name: 'סה"כ בטווח שנבחר'
    scope: "אזורי התרעה תחת ירי"
    visual: kpi
    sql_query: "SELECT 0"
```

Population rows use `POPULATION_KPI_STUB_SQL`. Warning-area rows use `AREA_KPI_STUB_SQL`. Both
constants are the text `SELECT 0`, kept separate so a later real query can replace one group.

Static chart. No `scope`. No `category_id`. Spell `ישובים` with one yod.

```yaml
  - name: "עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת"
    visual: chart
    sql_query: "SELECT CAST(NULL AS nvarchar(200)) AS category_label, CAST(NULL AS int) AS metric_value WHERE 1 = 0"
```

Do not remove or rewrite the existing metrics: six category KPIs, ranking chart
`עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`, map `מפת התרעות ביישובים`, policy
`סיכון לפי מדיניות התגוננות ברגע`.

## 2. SQL constants — `db/clients/alerts.py`

Add constants next to the existing stubs. English comments only. No Hebrew. No `'1'`, `'2'`,
or `'10'`. No `try`/`except` around `create_db_engine` or `connect`.

```python
# Placeholder SELECTs for the time-bucket cards. Executed as written.
# A missing database must surface as a connection error.
THREAT_KPI_STUB_SQL = "SELECT 0"
POPULATION_KPI_STUB_SQL = "SELECT 0"
AREA_KPI_STUB_SQL = "SELECT 0"

# Current-day versus previous-day settlements. This statement ignores the
# slicer window: it must not reference AlertDate, :start_date, or :end_date.
# WHERE 1 = 0 yields no rows, so rows() does not see a blank label.
PERIOD_COMPARISON_CHART_SQL = (
    "SELECT CAST(NULL AS nvarchar(200)) AS category_label, "
    "CAST(NULL AS int) AS metric_value WHERE 1 = 0"
)
```

`scalar`, `rows`, and `cell` stay. They already bind dates and an optional `category_id`.
Unused binds in a statement are ignored by SQLAlchemy 2.0.51 (research R5).

## 3. What the live test does with these rows

`tests/ui/alerts_analysis_dashboard/test_db_parity.py` is not edited.

- It still selects the 30-day slicer and passes the half-open window.
- It still loads every metric in the YAML, including the sixteen new ones.
- It still has no `pytest.skip`, `importorskip`, or `mark.skip`.
- A connection failure while executing `SELECT 0` or the empty chart statement fails the test.

The chart's empty result will not match a populated visual. That failure is the stub doing its
job. It is not a reason to skip.

## 4. Unchanged surfaces

- `tests/helpers/db_parity_engine.py`
- `core/components/kpi.py`, `core/components/chart.py`, `core/components/visual.py`
- `tests/ui/alerts_analysis_dashboard/page.py`
- `AlertsDBRunner` method signatures

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Nine threat cards, ids `1` / `2` / `10`, three names each | `tests/unit/test_db_parity_engine.py` keyed by `(name, scope)` |
| Six general cards, no `category_id` | Same test |
| Chart name is the full static title; SQL has no `:start_date` and no `AlertDate` | Same test, compared to `PERIOD_COMPARISON_CHART_SQL` |
| Ranking chart, map, and policy stubs still match their constants | Existing `test_remaining_visuals_use_stub_sql` |
| Existing six category measures still use `:category_id` | Existing `test_alerts_contract_names_and_category_ids` |
| No skip on the live test | Existing assertion in `test_remaining_visuals_use_stub_sql` |
| No new domain strings under `core/` | `git diff -- core/components core/portal` is empty |
| Fleet smoke | `pytest tests/ui/fleet_dashboard/` |
