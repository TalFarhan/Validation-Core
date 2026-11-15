# Data Model: Population Screen Data Validation Tests

**Feature**: 033-population-sanity-tests | **Date**: 2026-10-19

No new stored records. The golden file already exists and is not edited.

## Golden screen

`dashboard_sanity_checks.screen_2_alerts_analysis` in `data/alerts/db_sanity_am_kalavi.yaml`.

| Field | Type | Rule |
|-------|------|------|
| description | string | Ignored by this slice. |
| date_range.start | string `YYYY-MM-DD` | File value `2026-09-01`. Converted to `01/09/2026` for the page. |
| date_range.end | string `YYYY-MM-DD` | File value `2025-10-18`. Converted to `18/10/2025` for the page. Passed after start. Not swapped. |
| metrics.total_population_all_time.expected_value | int | `10142584`. Compared to `cards['total']` after a clear. |
| metrics.unprotected_population.expected_value | int | `3389879`. Compared to `cards['unprotected']` after a clear. |
| metrics.alerted_population_selected_range.expected_value | int | `9474`. Compared to `cards['warned']` after the date range. |

Other keys under this screen (`alerted_population_by_settlement`, `alerts_by_hierarchy`, `alerts_by_date`, `alerts_by_hour`) and the whole `screen_1_status_picture` block are out of this slice.

## Population cards

Read on the open population page. The map keys are the page's `CardRole` values.

| Key | Page role | Card title | When it is read |
|-----|-----------|------------|-----------------|
| total | `total` | `סה"כ אוכלוסייה` | After `clear_filters()` |
| unprotected | `unprotected` | `אוכלוסייה לא ממוגנת` | After `clear_filters()` |
| warned | `warned` | `אוכלוסייה מותרעת` | After `set_date_range` |

`read_card` returns `int | float`. The golden values are ints. Equality is exact.

## Date translation

| Golden | Page argument |
|--------|----------------|
| `2026-09-01` | `01/09/2026` |
| `2025-10-18` | `18/10/2025` |

The translator accepts only `YYYY-MM-DD`. It does not reorder the pair.

## Validation rules

1. The YAML load uses `yaml.safe_load` and UTF-8.
2. The global test clears filters before reading `total` and `unprotected`.
3. The filtered test does not clear filters. It sets the translated range, then reads `warned`.
4. Assertions use the `expected_value` integers above. They do not hard-code those integers in the test body.
5. `tests/ui/` and `core/` stay unchanged.

## State transitions

```text
test_global_metrics_match_db
    → load golden screen
    → clear_filters()
    → cards = read_card(total, warned, unprotected)
    → cards['total'] == 10142584
    → cards['unprotected'] == 3389879

test_filtered_population_matches_db
    → load golden screen
    → start, end = date_range translated to DD/MM/YYYY
    → set_date_range(start, end)
    → cards = read_card(total, warned, unprotected)
    → cards['warned'] == 9474
```
