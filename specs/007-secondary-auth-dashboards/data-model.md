# Data Model: Secondary-Auth Dashboards — Layer 0 Freshness Smoke + Bypass Hook

**Feature**: `007-secondary-auth-dashboards` | **Date**: 2026-08-30

This feature does not introduce warehouse tables or filter catalogs. The model
is the generic Layer 0 seam plus the per-report Layer 0 binding: search term,
temporary ready visual, secondary-auth bypass override, and the smoke caller.

## Entities

### Layer 0 seam

| Field | Value |
|-------|-------|
| Method | `ReportShell._bypass_secondary_auth(self)` |
| Default | no-op (`pass`) |
| Call site | `navigate()`, after the catalog-open branch, before `ready = self._report_ready_locator()` |
| Contract | Report-agnostic; contains no product names |

### Report binding (Layer 0 pages)

| Field | Mass Events | Life-Saving Guidelines | Maya System | Public Shelters |
|-------|-------------|------------------------|-------------|-----------------|
| Class | `MassEventsPage` | `LifeSavingGuidelinesPage` | `MayaSystemPage` | `PublicSheltersPage` |
| Base | `ReportShell` | `ReportShell` | `ReportShell` | `ReportShell` |
| `DASHBOARD_SEARCH_TERM` | `תמ"צ אירועים המוניים` | `תמ"צ שליטה - סטטוס הנחיות מצילות חיים` | `מערכת המא"יה` | `תמ"צ מחסים ציבוריים` |
| Ready visual text | same as search term, exact (temporary) | same as search term, exact (temporary) | same as search term, exact (temporary) | same as search term, exact (temporary) |
| `_bypass_secondary_auth` | placeholder override | placeholder override | placeholder override | placeholder override |
| JSON / slicers | forbidden | forbidden | forbidden | forbidden |

**Validation**: Ready locator is iframe exact text via
`_report_frame().get_by_text(..., exact=True)`. Search term is a class attribute
read by Layer 0; `core/` MUST NOT contain the Hebrew product names.

### Per-report smoke package

| Attribute | Value (all four reports) |
|-----------|--------------------------|
| Directory | `tests/ui/mass_events_dashboard/`, `tests/ui/life_saving_guidelines_dashboard/`, `tests/ui/maya_system_dashboard/`, `tests/ui/public_shelters_dashboard/` |
| Fixture | `dashboard` → that page (`bind_dashboard(<Page>)`) |
| Test | `test_dashboard_updated_within_24_hours` |
| Call | `dashboard.verify_freshness()` |
| Marker | `sanity` |

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
     └─ no → portal catalog search (page term) → catalog click
          → _bypass_secondary_auth()   # domain hook (placeholder for now)
          → wait ready visual → after_navigate → done
```

Same for all four reports. The bypass step is a no-op for fleet / 005 / 006.

## Out of scope

- `data/filters.json` / `filter_matrix.json` for these reports
- KPI, tab, chart, table, drilldown, slicer methods
- Warehouse last-refresh SQL
- New `.env` keys
- Moving these pages to `pages/<report>/`
- Report-specific text in `core/portal/page.py` (only the generic hook)
- Real secondary-auth clicks (placeholder overrides now; filled from live feedback)
- Confirmed (non-temporary) ready visuals — deferred to live-run feedback
