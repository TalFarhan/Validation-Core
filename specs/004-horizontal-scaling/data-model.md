# Data Model: Horizontal Scaling — Layer 0 Smoke for New Dashboards

**Feature**: `004-horizontal-scaling` | **Date**: 2026-08-27

This feature does not introduce warehouse tables or filter catalogs. The
model is the per-report Layer 0 binding: search term, ready visual,
optional popup, and the smoke caller.

## Entities

### Report binding (Layer 0 page)

| Field | Power Outages | Credit Consumption |
|-------|---------------|-------------------|
| Class | `PowerOutagesPage` | `CreditConsumptionPage` |
| Base | `ReportShell` | `ReportShell` |
| `DASHBOARD_SEARCH_TERM` | `תמונת מצב הפסקות חשמל` | `צריכת אשראי` |
| Ready visual text | `אוכלוסייה מותרעת` | `כמות אוכלוסיה ברשויות` |
| Popup | none | info-page overlay with close / X |
| JSON / slicers | forbidden | forbidden |

**Validation**: Ready locator is iframe text containment via
`_report_frame().get_by_text(...)`. Search term is a class attribute
read by Layer 0; `core/` MUST NOT contain the Hebrew product names.

### Info-page popup (Credit Consumption only)

| Field | Meaning | Rules |
|-------|---------|-------|
| Presence | Optional overlay after open | Dismiss if visible; ignore if absent |
| Close control | X / Close / סגור | Click visible control in report iframe |
| Timing | Before ready wait | Also safe to retry in `after_navigate` |
| Timeout | Short (~2s) | MUST NOT use full `self.timeout` when absent |
| Failure | Overlay still blocking ready | Ready wait fails as today (timeout) |

### Per-report smoke package

| Attribute | Power Outages | Credit Consumption |
|-----------|---------------|-------------------|
| Directory | `tests/ui/power_outages_dashboard/` | `tests/ui/credit_consumption_dashboard/` |
| Fixture | `dashboard` → that page | `dashboard` → that page |
| Test | `test_dashboard_updated_within_24_hours` | same name |
| Call | `dashboard.verify_freshness()` | same |
| Marker | `sanity` | `sanity` |

### Catalog search term resolution

```text
page.DASHBOARD_SEARCH_TERM if set
  else settings.DASHBOARD_SEARCH_TERM  # fleet default
```

Layer 0 stores no product list. Each page owns one term.

## State transitions

### Power Outages navigate

```text
[start]
  → iframe + ready "אוכלוסייה מותרעת"?
       ├─ yes → after_navigate → done
       └─ no → portal catalog search (page term)
            → wait ready visual → after_navigate → done
```

### Credit Consumption navigate

```text
[start]
  → iframe visible?
       └─ if info popup visible → click X (no-op if absent)
  → ready "כמות אוכלוסיה ברשויות"?
       ├─ yes → after_navigate (dismiss again if needed) → done
       └─ no → portal catalog search (page term)
            → dismiss popup if present
            → wait ready visual → after_navigate → done
```

## Out of scope

- `data/filters.json` / `filter_matrix.json` for these reports
- KPI, tab, chart, table, drilldown, slicer methods
- Warehouse last-refresh SQL
- New `.env` keys
- Moving these pages to `pages/<report>/`
