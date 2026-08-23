# Data Model: Extract Generic ReportShell

**Feature**: `001-extract-report-shell` | **Date**: 2026-08-23

This feature does not introduce warehouse tables or persisted business
entities. The model is the page-object graph and hook contract.

## Entities

### ReportShell (Layer 0)

| Field / member | Meaning | Rules |
|----------------|---------|-------|
| `page` | Playwright `Page` | Inherited from `BasePage` |
| `timeout` | Default wait budget | Inherited from `BasePage` / settings |
| `url` | Report application URL | From settings (`DASHBOARD_URL`); not a fleet label |
| `_report_ready_locator()` | Domain visual that means "loaded" | Abstract; MUST be overridden; MUST NOT be implemented with fleet titles in `core/` |
| `_dashboard_ready()` | Iframe visible AND ready locator visible | Used by auth, reuse, and `conftest` |
| `after_navigate()` | Post-open cleanup | Default no-op on the shell |
| `navigate(*, force_reload=False)` | Public open path | Signature frozen |
| `reload_and_measure_ready_ms()` | Elapsed ms to ready | Same ready hook as `navigate` |

**Validation**: `core/` contains none of: vehicles, district, subunit,
fleet KPI titles, fleet chart titles, `total_vehicles_kpi`,
`reset_dashboard_filters`.

### Domain report page (`MainDashboardPage`)

| Field / member | Meaning | Rules |
|----------------|---------|-------|
| Fleet KPI / tab / slicer / table / chart locators | Domain visuals | MUST stay here |
| `_report_ready_locator()` | Returns the total KPI card locator | Ownership of "what ready means" |
| `after_navigate()` | Calls `reset_dashboard_filters()` | MUST NOT move to `core/` |
| Optional `navigate` wrapper | Allure title only | MUST call `super().navigate(...)` with the same kwargs |

**Relationships**: inherits `ReportShell`. One instance per test via
`dashboard` fixture.

### Ready-state hook

| Attribute | Value |
|-----------|--------|
| Name | `_report_ready_locator` |
| Supplier | Domain page |
| Consumer | `ReportShell._dashboard_ready`, `navigate` wait loop, `reload_and_measure_ready_ms` |
| Fleet binding | Existing total KPI card (`self.total_vehicles_kpi`) |
| Failure | Missing override → `NotImplementedError`; visible timeout → `LoadTimeoutError` |

### Post-navigate hook

| Attribute | Value |
|-----------|--------|
| Name | `after_navigate` |
| Supplier | Domain page |
| Consumer | `ReportShell.navigate` (reuse path and cold-load path) |
| Fleet binding | `reset_dashboard_filters()` |
| Default | no-op on `ReportShell` |

### Portal session

| Attribute | Value |
|-----------|--------|
| Store | `settings.AUTH_FILE` (`auth_state.json`) |
| Writer | Existing `storage_state` calls inside auth / navigate |
| Reader | Existing Playwright context setup in `conftest` |
| Change in this feature | None |

## State transitions (navigate)

```text
[start]
   ├─ force_reload=False AND _dashboard_ready → reuse → after_navigate → done
   └─ else goto(url)
         ├─ _dashboard_ready → wait ready locator → after_navigate → done
         └─ else
               ├─ login page → _ensure_authenticated (one SSO click)
               ├─ _dashboard_ready → after_navigate → done
               ├─ still login → fail
               └─ else catalog search → iframe → wait ready locator → after_navigate → done
```

Auth sub-state is unchanged: one automatic `התחברות` click; optional
manual pause; no click loop.

## Out of scope

- DIM/FACT warehouse entities
- New KPI or filter models
- A second production report entity
