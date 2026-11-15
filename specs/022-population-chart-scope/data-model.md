# Data Model: Population Chart Scope

**Feature**: 022-population-chart-scope | **Date**: 2026-10-15

No new stored records. The dates and hour totals change which DOM node is parsed.

## Chart container

| Field | Type | Rule |
|-------|------|------|
| title | string | `התרעות לפי תאריך` or `גרף התרעות וגם ממוצע לפי שעה`. |
| title node | locator | First text node in the report frame that contains `title`. |
| container | locator | Nearest ancestor whose class contains `visualContainer` or `visual-container`, that has a numeric token, and whose text does not contain another chart title from this page. |
| categories | rows | Whatever `Chart._parse` returns for that container. |

Relationships: `chart_total` stores only the sum. It does not store spilled rows.

Other titles (`התרעות לפי מחוז`, `אוכלוסייה מותרעת לפי יישוב`) do not use this entity. They stay on `Chart.read`.

## Ready visual

| Field | Type | Rule |
|-------|------|------|
| anchor | locator | The district chart phrase in the report iframe. |
| budget | int | `60000` milliseconds, assigned on the population page. |
| card | locator | `סה"כ אוכלוסייה`, visible before clear. |

## Validation rules

1. A container that includes a second chart title from this page is rejected.
2. A container with no numeric token is rejected. The walk continues outward.
3. If no ancestor qualifies, `chart_total` fails. It does not fall back to the page-wide canvas.
4. After parse, only `int` and `float` cells are added. `bool` and `None` are skipped. Zero included cells fails.
5. A whole float sum is returned as `int`.

## State transitions

```text
title node missing → fail
else walk ancestors outward
    → has a number and no other chart title → parse that box
    → otherwise → next ancestor
no ancestor qualifies → fail
parse has no numeric cell → fail
else → return the sum
```

```text
open page
    → district chart visible → ready
    → page switcher visible and district chart not visible → click switcher, then wait
    → 60 seconds with no district chart → setup fails
clear
    → total card visible → click clear
```
