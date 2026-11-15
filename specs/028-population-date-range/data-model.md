# Data Model: Population Date Range for the Three-Chart Total

**Feature**: 028-population-date-range | **Date**: 2026-10-17

No new stored records.

## Date range

Used by `set_date_range` and by `test_hour_date_and_district_sums_match`.

| Field | Type | Rule |
|-------|------|------|
| start_date | string | Day/month/year. The three-chart test passes `01/01/2020`. |
| end_date | string | Day/month/year. The three-chart test passes the current day, `17/10/2026` on 17 October 2026. |
| start field | locator | Input whose accessible name begins with `תאריך התחלה`. |
| end field | locator | Input whose accessible name begins with `תאריך סיום`. |
| settled total | int or float | Two consecutive `read_card("total")` results that are equal. |

## Three-chart comparison

Read only after the range has settled and district aggregation is Sum.

| Name | Source | Role in the assertion |
|------|--------|------------------------|
| hour_total | `chart_total(HOUR_CHART)` | Left side of the equality |
| dates_total | `chart_total(DATES_CHART)` | Middle of the equality. Still the menu-table sum. |
| district_total | `chart_total(DISTRICT_CHART)` | Right side of the equality |

## Validation rules

1. `clear_filters` runs before `set_date_range`.
2. Both date fields are committed before the settle poll starts.
3. `set_date_range` returns only after the total card repeats, or the timeout elapses while polling.
4. Each of the three charts is read once.
5. The assertion is `hour_total == district_total == dates_total`.
6. A remaining difference fails the test.

## State transitions

```text
population page
    → clear_filters
    → set_date_range("01/01/2020", today)
         → fill תאריך התחלה
         → fill תאריך סיום
         → total card visible
         → two identical total-card reads
    → set_district_aggregation("sum")
    → read hour, dates, district
    → hour_total == district_total == dates_total
```
