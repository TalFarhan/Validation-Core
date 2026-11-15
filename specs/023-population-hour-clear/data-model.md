# Data Model: Population Hour Sum and Clear Baseline

**Feature**: 023-population-hour-clear | **Date**: 2026-10-15

No new stored records.

## Hour total

| Field | Type | Rule |
|-------|------|------|
| title | string | `גרף התרעות וגם ממוצע לפי שעה` only for this rule. |
| series | tuple of strings | From `Chart._parse`. A name containing `ממוצע` is omitted. |
| cell | `int \| float \| other` | Added when it is an `int`, or a `float` that is a whole number, and not a `bool`. |
| total | `int \| float` | Sum of included cells. A whole float is returned as `int`. |

Other chart titles do not use the `ממוצע` rule or the fractional-float rule.

## Cleared baseline

| Field | Type | Rule |
|-------|------|------|
| baseline | `PopulationSnapshot` | Taken after the first `clear_filters` in the clear test. |
| during | `PopulationSnapshot` | Taken after the date range, both hour toggles, and the range `0`–`349`. |
| restored | `PopulationSnapshot` | Taken after the second `clear_filters`. Must equal `baseline`. |

`PopulationSnapshot` is unchanged: three cards and the five chart totals.

## Validation rules

1. A series named with `ממוצע` contributes nothing, including `0`.
2. `5895.54` is not added. `0` and `5293` are added when they are bars on a kept series.
3. If the hour chart has no included cell, `chart_total` raises.
4. The clear test does not store a snapshot until the first clear has returned.

## State transitions

```text
hour categories and series
    → series name contains ממוצע → skip the series
    → else each cell
         → int, or whole float, and not bool → add
         → otherwise → skip
no cell added → fail
else → return the sum
```

```text
page open
    → clear_filters → baseline snapshot
    → apply filters → snapshot differs
    → clear_filters → snapshot equals baseline
```
