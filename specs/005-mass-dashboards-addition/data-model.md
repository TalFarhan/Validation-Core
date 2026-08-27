# Data Model: Mass Dashboards Addition — Layer 0 Freshness Smoke

**Feature**: `005-mass-dashboards-addition` | **Date**: 2026-08-27

This feature does not introduce warehouse tables or filter catalogs. The
model is the per-report Layer 0 binding: search term, temporary ready
visual, and the smoke caller.

## Entities

### Report binding (Layer 0 page)

| Field | Alerts Analysis | Marsal | Authorities Status | Hosen Status |
|-------|-----------------|--------|--------------------|--------------|
| Class | `AlertsAnalysisPage` | `MarsalPage` | `AuthoritiesStatusPage` | `HosenStatusPage` |
| Base | `ReportShell` | `ReportShell` | `ReportShell` | `ReportShell` |
| `DASHBOARD_SEARCH_TERM` | `ניתוח התרעות` | `מרס"ל` | `הערכת מצב רשויות` | `תמ"צ חוסן` |
| Ready visual text | same as search term (temporary) | same | same | same |
| Popup | none | none | none | none |
| JSON / slicers | forbidden | forbidden | forbidden | forbidden |

**Validation**: Ready locator is iframe phrase via
`_iframe_phrase_locator(...)`. Search term is a class attribute read by
Layer 0; `core/` MUST NOT contain the Hebrew product names.

### Per-report smoke package

| Attribute | Alerts Analysis | Marsal | Authorities Status | Hosen Status |
|-----------|-----------------|--------|--------------------|--------------|
| Directory | `tests/ui/alerts_analysis_dashboard/` | `tests/ui/marsal_dashboard/` | `tests/ui/authorities_status_dashboard/` | `tests/ui/hosen_status_dashboard/` |
| Fixture | `dashboard` → that page | same | same | same |
| Test | `test_dashboard_updated_within_24_hours` | same | same | same |
| Call | `dashboard.verify_freshness()` | same | same | same |
| Marker | `sanity` | `sanity` | `sanity` | `sanity` |

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

Same for all four reports. No popup dismiss step.

## Out of scope

- `data/filters.json` / `filter_matrix.json` for these reports
- KPI, tab, chart, table, drilldown, slicer methods
- Warehouse last-refresh SQL
- New `.env` keys
- Moving these pages to `pages/<report>/`
- Editing `core/portal/page.py`
- Confirmed (non-temporary) ready visuals — deferred to live-run feedback
