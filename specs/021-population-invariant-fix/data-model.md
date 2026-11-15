# Data Model: Population Invariant Fix

**Feature**: 021-population-invariant-fix | **Date**: 2026-10-14

No new stored records. `chart_total` changes which cells become the total.

## Chart total

| Field | Type | Rule |
|-------|------|------|
| title | string | Opaque chart title already on `AlertsPopulationPage`. |
| series_index | int | Default 0. Selects `category.values[series_index]`. |
| cell | `int \| float \| other` | Included only for `int` and `float`, and not for `bool`. |
| total | `int \| float` | Sum of included cells. A whole float is returned as `int`. |

Relationships: `PopulationSnapshot.totals` still stores the return value of `chart_total`. It does
not see skipped cells.

## Sum control

| Field | Type | Rule |
|-------|------|------|
| label | string | `סכום` or `ממוצע ליום`, already constants on the page. |
| target | one locator | Container button when count is 1. Otherwise the frame's exact-name `.first`. |

## Validation rules

1. An empty reading (`state == "empty"` or no categories) fails before the loop.
2. A series index past `category.values` fails for that category only when the cell would have been
   read. A category with no slot at `series_index` is skipped, same as a non-number, unless every
   category is skipped.
3. After the loop, zero included cells fails. The failure is not the number 0.
4. `bool` is not numeric here, even though it is a subclass of `int` in Python.
5. No field on this model is written under `core/`.

## State transitions

```text
reading empty or no categories → fail
else each selected cell
    → int or float (not bool) → add
    → otherwise → skip
no cell added → fail
else → return the sum
```
