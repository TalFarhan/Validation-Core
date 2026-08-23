# Contract: ReportShell and fleet page (test-facing)

**Feature**: `001-extract-report-shell` | **Date**: 2026-08-23

Consumers: `conftest.py` (`dashboard` fixture), `tests/ui/fleet_dashboard/*`,
`tests/e2e/*`, `tests/helpers/dashboard_validation.py`.
This change MUST NOT require consumer edits.

## Public methods (frozen)

### `MainDashboardPage.navigate(*, force_reload: bool = False) -> None`

| Rule | Value |
|------|--------|
| Required args | none beyond `self` |
| Keyword-only | `force_reload` default `False` |
| Return | `None` |
| Side effects | Open or reuse the report; reset domain filters via `after_navigate`; persist storage state when already doing so today |
| Errors | `AssertionError` (login/catalog); `LoadTimeoutError` (ready visual) |

Callers today: `conftest.dashboard` (`force_reload` on retry), any test
that calls `dashboard.navigate(...)`.

### `MainDashboardPage.reload_and_measure_ready_ms() -> int`

| Rule | Value |
|------|--------|
| Args | none beyond `self` |
| Return | Non-negative elapsed milliseconds until ready visual is visible |
| Ready signal | Same `_report_ready_locator` as `navigate` |
| Errors | `LoadTimeoutError` if budget exceeded |

Caller today: `tests/ui/fleet_dashboard/test_dashboard_smoke.py`
(`test_dashboard_loads_within_sla`).

### Fixture-visible helpers (keep names)

These are not a public product API but `conftest.py` calls them. Names MUST
remain resolvable on `MainDashboardPage` (via inheritance is enough):

- `_dashboard_ready() -> bool`
- `_is_portal_profile_error() -> bool`
- `_recover_from_portal_glitch() -> None`

## Domain hooks (new; not called from tests)

| Method | On | Contract |
|--------|----|----------|
| `_report_ready_locator()` | Domain page MUST override | Returns a Playwright locator. Shell MUST NOT construct the fleet KPI by title. |
| `after_navigate()` | Shell default no-op; fleet MUST override | Fleet calls `reset_dashboard_filters()`. |

## Methods that move to `ReportShell` (names preserved)

`_portal_search_box`, `_all_products_control`, `_dashboard_iframe`,
`_click_even_if_hidden`, `_is_portal_home`, `_hitachbrut_button`,
`_is_login_page`, `_page_debug_summary`, `_is_portal_profile_error`,
`_recover_from_portal_glitch`, `_wait_for_dashboard_iframe`,
`_auto_click_hitachbrut`, `_open_all_products_catalog`,
`_open_dashboard_via_portal_search`, `_ensure_authenticated`.

## Methods that stay on `MainDashboardPage`

KPI maps/reads, tabs, district/sub-unit/source/category slicers, vehicle
table and search, charts, tooltips, drilldown, `reset_dashboard_filters`,
`apply_filters`, and all other fleet helpers.

## Leakage contract

`core/**` MUST match none of:

```text
vehicles|district|subunit|sub_unit|total_vehicles|רכבים|מחוז
```

except inside comments that are generic English ("report", "portal") —
Hebrew fleet KPI titles and the identifier `total_vehicles_kpi` are
forbidden in `core/`.

## Observability contract

- A successful navigate still writes a CSV UI log line (reuse or via-path).
- Allure still records a navigate step (fleet wrapper allowed).
- Failure screenshot + Playwright trace behavior in `conftest` is unchanged.
