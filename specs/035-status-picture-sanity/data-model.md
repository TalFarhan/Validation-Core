# Data Model: Status Picture Sanity Tests

**Feature**: 035-status-picture-sanity | **Date**: 2026-10-19

No new stored records. The golden file is not edited.

## Screen range

`dashboard_sanity_checks.screen_1_status_picture.date_range`

| Field | File value | Page argument |
|-------|------------|---------------|
| start | `2025-06-13` | `13/06/2025` |
| end | `2025-06-25` | `25/06/2025` |

The filtered card test and both chart tests set this pair. The global test does not.

## Cards

`read_cards()` keys:

| Key | Golden field | Expected | When |
|-----|--------------|----------|------|
| `total_warning_zones` | `total_warning_zones_all_time` | 1337 | After `clear_filters` |
| `total_alerted_population` | `total_alerted_population_all_time` | 10142584 | After `clear_filters` |
| `warning_zones_under_fire` | `warning_zones_under_fire` | 1271 | After the range |
| `alerted_population` | `alerted_population_selected_range` | 10091037 | After the range |

A key the page cannot see is absent. The test that needs it skips.

## Category map

`metrics.alerts_by_category.values`

| Golden key | Threat scope | Card | Expected |
|------------|--------------|------|----------|
| `category_1_rockets` | `ירי רקטות וטילים` | `סה"כ בטווח שנבחר` | 16817 |
| `category_2_aircraft` | `חדירת מחבלים` | `סה"כ בטווח שנבחר` | 519 |
| `category_10_terrorists` | `חדירת כלי טיס עוין` | `סה"כ בטווח שנבחר` | 0 |

The scope follows the numeric id in the key. An empty map skips `alerts_by_category`.

## Settlement ranking

`metrics.top_10_settlements.values`

| Name | Count |
|------|-------|
| ראשון לציון | 39 |
| תל אביב-יפו | 36 |
| רמת השרון | 35 |
| נתניה | 34 |
| ראש העין | 32 |
| רמלה | 32 |
| יגל | 31 |
| גינתון | 31 |
| צפרייה | 31 |
| חיפה | 31 |

The visual title is `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`. Every golden name must match. Extra UI rows are allowed. An empty map skips `top_10_settlements`.

## Validation rules

1. Global asserts use the cleared page and the two all-time integers.
2. Filtered card asserts use the translated range and the two range integers.
3. Chart asserts use the same range and compare golden keys only.
4. An empty chart map skips that chart test.
5. Screen 2 tests and the golden file stay unchanged.

## State transitions

```text
test_screen_1_global_metrics
    → clear_filters()
    → read_cards()
    → total_warning_zones == 1337
    → total_alerted_population == 10142584

test_screen_1_filtered_metrics
    → set_date_range(13/06/2025, 25/06/2025)
    → read_cards()
    → warning_zones_under_fire == 1271
    → alerted_population == 10091037

test_screen_1_alerts_by_category
    → same range
    → read_alerts_by_category() or skip

test_screen_1_top_settlements
    → same range
    → read_top_10_settlements() or skip
```
