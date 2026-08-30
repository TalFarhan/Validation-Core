# Contract: Layer 0 report binding + secondary-auth bypass (test-facing)

**Feature**: `007-secondary-auth-dashboards` | **Date**: 2026-08-30

Consumers: the four new `tests/ui/<report>/test_dashboard_smoke.py` modules.
Fleet consumers of root `dashboard` / `navigate` / `reload_and_measure_ready_ms`
MUST NOT need edits.

## Layer 0 seam

`ReportShell` gains a generic hook:

```python
def _bypass_secondary_auth(self) -> None:
    """Domain hook: dismiss a secondary auth/entry screen shown after the
    catalog click, before the report ready visual. Default no-op."""
    return
```

Invoked inside `navigate()` **after** the report is opened from the catalog and
**before** the ready-locator wait begins:

```python
...
    self._open_dashboard_via_portal_search()   # or a reuse/direct path

ensure_single_tab(self.page.context, self.page)
self._bypass_secondary_auth()                  # <-- new call site
ready = self._report_ready_locator()
... wait on ready ...
```

The hook MUST be report-agnostic (no product names in `core/`). Default no-op
keeps fleet and the 005/006 reports unchanged.

## Domain pages

| Class | File | `DASHBOARD_SEARCH_TERM` | `_report_ready_locator()` |
|-------|------|-------------------------|---------------------------|
| `MassEventsPage` | `tests/ui/mass_events_dashboard/page.py` | `'תמ"צ אירועים המוניים'` | iframe exact text `'תמ"צ אירועים המוניים'` (temporary) |
| `LifeSavingGuidelinesPage` | `tests/ui/life_saving_guidelines_dashboard/page.py` | `'תמ"צ שליטה - סטטוס הנחיות מצילות חיים'` | iframe exact text of the same phrase (temporary) |
| `MayaSystemPage` | `tests/ui/maya_system_dashboard/page.py` | `'מערכת המא"יה'` | iframe exact text `'מערכת המא"יה'` (temporary) |
| `PublicSheltersPage` | `tests/ui/public_shelters_dashboard/page.py` | `'תמ"צ מחסים ציבוריים'` | iframe exact text `'תמ"צ מחסים ציבוריים'` (temporary) |

Shared rules for all four:

| Rule | Value |
|------|--------|
| Base | `ReportShell` |
| Freshness | inherited `verify_freshness` — no override |
| `_bypass_secondary_auth` | overridden with a placeholder (comment/`print`) — real clicks later |
| Forbidden | JSON, `Slicer`, KPI/chart/table methods |
| `self.url` | `settings.LOGIN_URL or settings.DASHBOARD_URL` |

## Layer 0 behavior

`ReportShell` already resolves:

```python
getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM
```

This feature MUST NOT add the four Hebrew product names or ready strings to
`core/`. This feature MUST NOT edit `.env`.

### Frozen methods (unchanged signatures)

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
def verify_freshness(self, max_hours: int = 24) -> None: ...
```

`navigate()` keeps its signature; only a `self._bypass_secondary_auth()` call is
inserted at the documented seam.

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

The test MUST NOT contain iframe locators, date parsing, or CSS — those belong
on the page object.

## Leakage contract

`core/**` MUST match none of:

```text
תמ"צ אירועים המוניים|תמ"צ שליטה - סטטוס הנחיות מצילות חיים|מערכת המא"יה|תמ"צ מחסים ציבוריים
```

`core/**` MAY contain the generic string `_bypass_secondary_auth`. `pages/` MUST
gain no new files. `.env` MUST be unchanged.

## Observability contract

- Smoke modules use `suite_marks(feature=FEATURE_UI_SMOKE)` and
  `@pytest.mark.sanity`.
- Failure screenshot + Playwright trace behavior in root `conftest` is unchanged.
