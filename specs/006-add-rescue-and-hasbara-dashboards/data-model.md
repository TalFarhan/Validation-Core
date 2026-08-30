# Data Model: Rescue & Hasbara Dashboards — Layer 0 Freshness Smoke

**Feature**: `006-add-rescue-and-hasbara-dashboards` | **Date**: 2026-08-30

This feature does not introduce warehouse tables or filter catalogs. The
model is the per-report Layer 0 binding: search term, temporary ready
visual, and the smoke caller.

## Entities

### Report binding (Layer 0 page)

| Field | Rescue Capabilities | Public Inquiries |
|-------|---------------------|------------------|
| Class | `RescueCapabilitiesPage` | `PublicInquiriesPage` |
| Base | `ReportShell` | `ReportShell` |
| `DASHBOARD_SEARCH_TERM` | `כשירויות חילוץ במרחב האזרחי` | `ניתוח פניות הסברה` |
| Ready visual text | same as search term, exact (temporary) | same as search term, exact (temporary) |
| Popup | none | none |
| JSON / slicers | forbidden | forbidden |

**Validation**: Ready locator is iframe exact text via
`_report_frame().get_by_text(..., exact=True)`. Search term is a class
attribute read by Layer 0; `core/` MUST NOT contain the Hebrew product
names.

### Per-report smoke package

| Attribute | Rescue Capabilities | Public Inquiries |
|-----------|---------------------|------------------|
| Directory | `tests/ui/rescue_capabilities_dashboard/` | `tests/ui/public_inquiries_dashboard/` |
| Fixture | `dashboard` → that page | same |
| Test | `test_dashboard_updated_within_24_hours` | same |
| Call | `dashboard.verify_freshness()` | same |
| Marker | `sanity` | `sanity` |

### Catalog search term resolution

```text
page.DASHBOARD_SEARCH_TERM if set
  else settings.DASHBOARD_SEARCH_TERM  # fleet default (already in Layer 0)
```

Layer 0 stores no product list. Each page owns one term.

## State transitions

```text
[start]
  → iframe + ready <search term>?
       ├─ yes → after_navigate → done
       └─ no → portal catalog search (page term)
            → wait ready visual → after_navigate → done
```

Same for both reports. No popup dismiss step.

## Out of scope

- `data/filters.json` / `filter_matrix.json` for these reports
- KPI, tab, chart, table, drilldown, slicer methods
- Warehouse last-refresh SQL
- New `.env` keys
- Moving these pages to `pages/<report>/`
- Editing `core/portal/page.py`
- Confirmed (non-temporary) ready visuals — deferred to live-run feedback
