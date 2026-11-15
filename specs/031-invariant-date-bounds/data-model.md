# Data Model: Bound the Global Invariant Tests by Date

**Feature**: 031-invariant-date-bounds | **Date**: 2026-10-18

No new stored records. No page-object fields.

## Bounded window

Used by `test_day_plus_night_equals_untoggled_sum` and `test_clear_restores_population_snapshot`.

| Field | Type | Rule |
|-------|------|------|
| start | string | `01/09/2026`. Day, month, year. |
| end | string | `15/10/2026`. Day, month, year. |
| call | method | `set_date_range(start, end)` on the population page. |

## Day/night totals

Used by `test_day_plus_night_equals_untoggled_sum` after the bounded window is applied.

| Field | Type | Rule |
|-------|------|------|
| untoggled | int | Dates total with both hour toggles off, inside the bounded window. |
| day | int | Dates total after `set_day_night("day")`. |
| night | int | Dates total after toggles are turned off and `set_day_night("night")` runs. |
| identity | check | `day + night == untoggled`. |

## Clear-restore snapshots

Used by `test_clear_restores_population_snapshot`. Each snapshot is a `PopulationSnapshot` from the unchanged helper.

| Field | Type | Rule |
|-------|------|------|
| before | snapshot | Taken after the opening `clear_filters()` and the bounded window. |
| during | snapshot | Taken after `set_between_dates("01/09/2026", "01/10/2026")`, day, night, and `set_value_range(0, 349)`. Must differ from `before`. |
| after | snapshot | Taken only after the later `clear_filters()` and a second bounded window. Must equal `before`. |

## Validation rules

1. The untoggled dates total is read only after `set_date_range("01/09/2026", "15/10/2026")`.
2. The before snapshot is taken only after that same call.
3. The after snapshot is taken only after `clear_filters()` and a second `set_date_range("01/09/2026", "15/10/2026")`.
4. Neither test is marked expected-fail.
5. `population_snapshot.py`, `pages/`, and `core/` stay unchanged.

## State transitions

```text
day/night test
    → clear_filters
    → set_date_range("01/09/2026", "15/10/2026")
    → untoggled dates total
    → day total → night total
    → day + night == untoggled

clear test
    → clear_filters
    → set_date_range("01/09/2026", "15/10/2026")
    → before snapshot
    → narrower dates, day, night, 0–349
    → during snapshot differs
    → clear_filters
    → set_date_range("01/09/2026", "15/10/2026")
    → after snapshot equals before
```
