# Data Model: Force the Date Field Click Past the Overlay

**Feature**: 032-date-input-force-click | **Date**: 2026-10-18

No new stored records.

## Field commit

Used by `_commit_field` for every input `_fill_input` and `_fill_exact` pass in.

| Field | Type | Rule |
|-------|------|------|
| field | locator | The visible input. Date inputs use an `aria-label` prefix of `תאריך התחלה` or `תאריך סיום`. |
| value | string | The text written after the click. Dates stay day/month/year. |
| click | call | `field.click(force=True)`. |
| commit | keys | `field.fill(value)` then `field.press("Enter")`. |

## Lingering backdrop

Present after `clear_filters()` and still present when `set_date_range` runs.

| Field | Type | Rule |
|-------|------|------|
| node | element | `div.cdk-overlay-backdrop` in the report frame. |
| dismiss | method | `_dismiss_overlay` clicks `.cdk-overlay-backdrop-showing` only. A backdrop without that class stays. |

## Validation rules

1. The click in `_commit_field` passes `force=True`.
2. Fill and Enter still run after that click.
3. `_dismiss_overlay` still runs before the click and after Enter.
4. `test_population_invariants.py` and `core/` stay unchanged.

## State transitions

```text
clear_filters
    → cdk-overlay-backdrop may remain
    → set_date_range
         → _commit_field
              → _dismiss_overlay (no -showing node)
              → click(force=True)
              → fill
              → Enter
              → _dismiss_overlay
```
