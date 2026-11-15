# Phase 1 Data Model: Credit Consumption Dashboard UI Sanity

This slice adds no persistent schema. The entities below are the golden YAML document and the
in-memory structures the page object and sanity tests exchange.

## Golden record (`data/credit/db_sanity_purim2026.yaml`) — UNCHANGED values

Root key: `credit_consumption_dashboard`.

### `screen_1_summary`

| Field | Shape | Notes |
|-------|--------|--------|
| `dashboard_info.title` | string | `תמ״צ צריכת אשראי` |
| `dashboard_info.last_updated` | string | Informational; not asserted unless a dedicated test is added |
| `kpi_metrics` | nested object | See KPI entity |
| `daily_trends_by_toggle` | object of four lists | Keyed by `{metric}_{visualization}` |
| `daily_alerts` | list of `{date, day, alerts_count}` | Optional visual; skip if unread |
| `expenses_by_authority_millions` | list of `{authority, amount}` | Amount is a number (millions) |
| `active_filters` | flat string map | Apply values that are not `הכל` |

**Validation rule**: metric values are not changed by this slice.

### `screen_2_data_export`

| Field | Shape | Notes |
|-------|--------|--------|
| `title` | string | `צריכת אשראי - ייצוא נתונים` (Screen 2 ready / tab name) |
| `active_filters.top_bar` | string map | `period` is `פורים 2026`; others `הכל` |
| `active_filters.side_bar` | string map | All `הכל` in the current file |
| `export_table_data` | list of row objects | See Export row |

## KPI metrics (nested)

Returned by `read_kpi_metrics()` with the same nesting as YAML:

```text
kpi_metrics:
  num_population: int                         # 10006812
  average_purchase_expense_routine:
    physical_purchase: float                  # 125.19
  average_purchase_expense_selected_range:
    total: float                              # 389.33
    physical_purchase: float                  # 129.23
    online_purchase: float                    # 405.79
  average_change_percentage_vs_routine:
    physical_purchase: percent-string         # "3.23%"
    online_purchase: percent-string           # "4.23%"
```

**Rules**:

- Integers stay `int`; non-integral expenses stay `float`.
- Change-vs-routine values stay strings that include `%`. Do not parse them through `KPI.number`.
- Hebrew card titles are live-copied; they are not stored in this model.

## Toggle state (runtime)

- **Fields** on `CreditConsumptionPage`: `_active_metric` (`expense_amount` \| `transactions_count`),
  `_active_visualization` (`line` \| `bar`).
- **Writer**: `set_metric` / `set_visualization` record state only after the control is selected.
- **Reader key**: `f"{_active_metric}_{_active_visualization}"` must be one of the four YAML keys.
- **Invariant**: default after navigate is whatever the report lands on; the test sets both toggles
  before each `read_daily_trends()` call.

## Daily trend row

| YAML key | `value` field | Example |
|----------|---------------|---------|
| `expense_amount_line` | `value: number` | `{date: "02/03/2026", day: "שני", value: 974}` |
| `transactions_count_line` | `value: number` | `{date, day, value: 4.6}` |
| `expense_amount_bar` | `value: number` | `{date, day, value: 426}` |
| `transactions_count_bar` | `values: list[number]` | `{date, day, values: [3, 1]}` |

**Rules**:

- `date` is `DD/MM/YYYY`. `day` is the Hebrew weekday from the YAML.
- Do not coerce `values` to a scalar. Do not require extra UI dates beyond the golden list.
- Empty extraction returns `[]` so the test skip guard can fire.

## Authority row

`{authority: str, amount: number}` e.g. `{authority: "תל אביב - יפו", amount: 346}`.

Returned as a list (YAML order is not required). Tests match by authority name.

## Daily alert row (optional)

`{date: str, day: str, alerts_count: int}`. Empty list → skip.

## Export row

| Key | Type | Example |
|-----|------|---------|
| `transaction_date` | `DD/MM/YYYY` string | `"03/03/2026"` |
| `authority_name` | string | `"מגאר"` |
| `vitality_status` | string | `"חיוני"` / `"לא חיוני"` |
| `category` | string | `"מזון חיוני"` |
| `sub_category` | string | `"רשתות מזון סופרמרקטים ומרכולים"` |
| `quantity` | int | `8` |
| `amount` | thousands-separated string | `"1,944.97"` |
| `purchase_nature` | string | `"רכישה מקוונת"` |

**Rules**: every golden row must appear in the UI read. Extra UI rows are ignored. Amount stays a
string with comma thousands separators.

## Active filters

Screen 1 (flat):

`guidelines_area`, `district`, `sub_district`, `time_range`, `sector`, `purchase_nature`,
`vitality_status`, `category`, `index`.

Screen 2:

- `top_bar`: `period`, `date`, `day_of_week`
- `side_bar`: `guidelines_area`, `district`, `sub_district`, `authority`, `sector`,
  `purchase_nature`, `vitality_status`, `category`, `index`

**Apply rule**: skip `הכל`. Apply every other string via `Slicer.select` (dropdown) or bilingual
date fill. Current snapshot applies `time_range` / `period` = `פורים 2026` only.

**Slicer id**: YAML key. **role_name**: copied from the live report, stored as page constants.

## Bilingual locator (runtime)

| Control | Hebrew | English |
|---------|--------|---------|
| Page-rail | `ניווט בין עמודים` | `Page navigation` |
| Start date | `תאריך התחלה` | `Start date` |
| End date | `תאריך סיום` | `End date` |
| Show as a table | `הצג כטבלה` | `Show as a table` |

Invariant: the Hebrew side still matches when Hebrew is rendered.

## Relationships

```text
golden YAML
  └── credit_consumption_dashboard
        ├── screen_1_summary
        │     ├── active_filters ──► apply_filters (skip הכל)
        │     ├── kpi_metrics ──► read_kpi_metrics
        │     ├── daily_trends_by_toggle[key] ──► set toggles + read_daily_trends
        │     ├── expenses_by_authority_millions ──► read_expenses_by_authority
        │     └── daily_alerts ──► read_daily_alerts (optional)
        └── screen_2_data_export
              ├── active_filters ──► apply_filters after open_export_page
              └── export_table_data ──► read_export_table
```
