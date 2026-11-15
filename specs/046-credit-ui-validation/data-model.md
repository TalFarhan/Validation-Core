# Data Model: Credit Consumption UI Sanity Validation

Source file (unchanged): `data/credit/db_sanity_purim2026.yaml`.
Root key: `credit_consumption_dashboard`.

This slice does not add fields and does not change values. It defines how each existing
field is compared to the live UI.

## Screen 1 — `screen_1_summary`

| Path | Type | Match rule |
|------|------|------------|
| `dashboard_info.title` | string | Visible iframe phrase equals this string (`תמ״צ צריכת אשראי` in the current file). |
| `dashboard_info.last_updated` | string | `DD/MM/YYYY HH:MM`. The string occurs in `_last_refresh_caption_text()`. Current file: `01/11/2026 11:38`. |
| `kpi_metrics` | nested map | `_assert_nested`. Extra UI keys ignored. |
| `kpi_metrics.num_population` | int | Exact. Current file: `10006812`. |
| `kpi_metrics.average_purchase_expense_routine.physical_purchase` | number | Exact. |
| `kpi_metrics.average_purchase_expense_selected_range.total` | number | Exact. |
| `kpi_metrics.average_purchase_expense_selected_range.physical_purchase` | number | Exact. |
| `kpi_metrics.average_purchase_expense_selected_range.online_purchase` | number | Exact. |
| `kpi_metrics.average_change_percentage_vs_routine.physical_purchase` | string | Stays a percent string (`"3.23%"`). Not a float. |
| `kpi_metrics.average_change_percentage_vs_routine.online_purchase` | string | Stays a percent string (`"4.23%"`). |
| `daily_trends_by_toggle.<metric>_<visualization>` | list of rows | Key splits on the last `_`. Row key is `date`. |
| `daily_trends_by_toggle.*.day` | string | Exact string. Not a weekday index. |
| `daily_trends_by_toggle.*.value` | number | Used by `expense_amount_line`, `transactions_count_line`, `expense_amount_bar`. |
| `daily_trends_by_toggle.transactions_count_bar.values` | list of numbers | Exact list, including `[3, 1]` and `[3]`. Not unwrapped. |
| `daily_alerts[]` | list of rows | Row key is `date`. Fields `day` (string) and `alerts_count` (number). |
| `expenses_by_authority_millions[]` | list of rows | Row key is `authority`. Field `amount` (number, millions). |
| `active_filters` | map of string to string | Passed to `apply_filters` before Screen 1 reads. Value `הכל` is not applied. |

### Trend keys in the current file

| YAML key | `set_metric` | `set_visualization` | Value field |
|----------|--------------|---------------------|-------------|
| `expense_amount_line` | `expense_amount` | `line` | `value` |
| `transactions_count_line` | `transactions_count` | `line` | `value` |
| `expense_amount_bar` | `expense_amount` | `bar` | `value` |
| `transactions_count_bar` | `transactions_count` | `bar` | `values` (list) |

## Screen 2 — `screen_2_data_export`

| Path | Type | Match rule |
|------|------|------------|
| `title` | string | Visible iframe phrase equals this string after `open_export_page()`. Current file: `צריכת אשראי - ייצוא נתונים`. |
| `active_filters.top_bar` | map | Merged first into the filter dict. `הכל` is not applied. |
| `active_filters.side_bar` | map | Merged second (`dict.update`). `הכל` is not applied. |
| `export_table_data[]` | list of rows | Composite key `(transaction_date, authority_name, sub_category)`. |

### Export row fields

| Field | Type | Rule |
|-------|------|------|
| `transaction_date` | string | Part of the key. Example `03/03/2026`. |
| `authority_name` | string | Part of the key. |
| `sub_category` | string | Part of the key. |
| `vitality_status` | string | Exact. |
| `category` | string | Exact. |
| `quantity` | int | Exact int. Example `8`, not `"8"` and not `8.0` left as a float. |
| `amount` | string | Exact, commas kept. Example `"1,944.97"`. |
| `purchase_nature` | string | Exact. |

## Comparison state

```text
golden block non-empty
        │
        ▼
visual title or grid absent? ── yes ──► pytest.skip
        │ no
        ▼
reader returns empty? ── yes ──► FAIL (path, ui=[], golden=...)
        │ no
        ▼
each golden key/row equal? ── no ──► FAIL (path, ui, golden)
        │ yes
        ▼
pass (extra UI keys/rows ignored)
```

## Relationships

- One golden file → one `credit_consumption_dashboard` object → two screens.
- Screen 1 `active_filters` is flat. Screen 2 `active_filters` has `top_bar` and `side_bar`.
  Both are inputs to the same `apply_filters` method.
- A trend series is identified by the toggle key, then by `date` inside that list.
- An export row is identified only by the three-part key. Other fields are payload.
- `dashboard_info.last_updated` is not an input to `verify_freshness`. The smoke test still
  uses the Layer 0 24-hour window on the same caption.

## Validation rules

- Do not add or rename YAML keys in this slice.
- Do not coerce a percent string, a `day` string, or an `amount` string through `_parse_number`.
- Do not coerce `transactions_count_bar.values` to a scalar.
- A golden key missing from a rendered visual fails even if other UI keys exist.
- UI keys that are not in the golden object are ignored.
