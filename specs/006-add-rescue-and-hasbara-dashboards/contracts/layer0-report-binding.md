# Contract: Layer 0 report binding (test-facing)

**Feature**: `006-add-rescue-and-hasbara-dashboards` | **Date**: 2026-08-30

Consumers: the two new `tests/ui/<report>/test_dashboard_smoke.py` modules.
Fleet consumers of root `dashboard` / `navigate` /
`reload_and_measure_ready_ms` MUST NOT need edits.

## Domain pages

| Class | File | `DASHBOARD_SEARCH_TERM` | `_report_ready_locator()` |
|-------|------|-------------------------|---------------------------|
| `RescueCapabilitiesPage` | `tests/ui/rescue_capabilities_dashboard/page.py` | `"כשירויות חילוץ במרחב האזרחי"` | iframe exact text `"כשירויות חילוץ במרחב האזרחי"` (temporary) |
| `PublicInquiriesPage` | `tests/ui/public_inquiries_dashboard/page.py` | `"ניתוח פניות הסברה"` | iframe exact text `"ניתוח פניות הסברה"` (temporary) |

Shared rules for both:

| Rule | Value |
|------|--------|
| Base | `ReportShell` |
| Freshness | inherited `verify_freshness` — no override |
| Forbidden | JSON, `Slicer`, KPI/chart/table methods, popup locators |
| `self.url` | `settings.LOGIN_URL or settings.DASHBOARD_URL` |

## Layer 0 behavior

`ReportShell` already resolves:

```python
getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM
```

This feature MUST NOT add the two Hebrew product names or ready strings
to `core/`. This feature MUST NOT edit `.env`.

### Frozen methods (unchanged signatures)

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
def verify_freshness(self, max_hours: int = 24) -> None: ...
```

## Fixtures

### Root `conftest.py`

MUST NOT be edited. Fleet `dashboard` still returns `MainDashboardPage`.

### Local fixtures

Each new package binds the shared helper:

```python
from tests.helpers.dashboard_fixture import bind_dashboard
from tests.ui.<report>_dashboard.page import <ReportPage>

dashboard = bind_dashboard(<ReportPage>)
```

`auth_page` remains the shared session tab. Retry/transient profile-error
handling is provided by `bind_dashboard`/`open_report`.

## Layer 3 test contract

```python
@pytest.mark.sanity
def test_dashboard_updated_within_24_hours(dashboard):
    dashboard.verify_freshness()
```

The test MUST NOT contain iframe locators, date parsing, or CSS — those
belong on the page object.

## Leakage contract

`core/**` MUST match none of:

```text
כשירויות חילוץ במרחב האזרחי|ניתוח פניות הסברה
```

`pages/` MUST gain no new files. `.env` MUST be unchanged.

## Observability contract

- Smoke modules use `suite_marks(feature=FEATURE_UI_SMOKE)` and
  `@pytest.mark.sanity`.
- Failure screenshot + Playwright trace behavior in root `conftest` is
  unchanged.
