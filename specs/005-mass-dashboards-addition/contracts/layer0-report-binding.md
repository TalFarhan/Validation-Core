# Contract: Layer 0 report binding (test-facing)

**Feature**: `005-mass-dashboards-addition` | **Date**: 2026-08-27

Consumers: the four new `tests/ui/<report>/test_dashboard_smoke.py` modules.
Fleet consumers of root `dashboard` / `navigate` /
`reload_and_measure_ready_ms` MUST NOT need edits.

## Domain pages

| Class | File | `DASHBOARD_SEARCH_TERM` | `_report_ready_locator()` |
|-------|------|-------------------------|---------------------------|
| `AlertsAnalysisPage` | `tests/ui/alerts_analysis_dashboard/page.py` | `"ניתוח התרעות"` | iframe phrase `"ניתוח התרעות"` (temporary) |
| `MarsalPage` | `tests/ui/marsal_dashboard/page.py` | `"מרס\"ל"` | iframe phrase `"מרס\"ל"` (temporary) |
| `AuthoritiesStatusPage` | `tests/ui/authorities_status_dashboard/page.py` | `"הערכת מצב רשויות"` | iframe phrase `"הערכת מצב רשויות"` (temporary) |
| `HosenStatusPage` | `tests/ui/hosen_status_dashboard/page.py` | `"תמ\"צ חוסן"` | exact iframe text `"תמ\"צ ארצי - דיווחי קה"א יקל"ר"` (no popup) |

Shared rules for all four:

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

This feature MUST NOT add the four Hebrew product names or ready strings
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

Each new package copies the Power Outages fixture shape:

```python
@pytest.fixture
def dashboard(auth_page, browser_context):
    page_obj = <ReportPage>(auth_page)
    page_obj.navigate()
    return page_obj
```

Retry/transient profile-error handling MUST match
`tests/ui/power_outages_dashboard/conftest.py`.
`auth_page` remains the shared session tab.

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
ניתוח התרעות|מרס"ל|הערכת מצב רשויות|תמ"צ חוסן|תמ"צ ארצי - דיווחי קה"א יקל"ר
```

`pages/` MUST gain no new files. `.env` MUST be unchanged.

## Observability contract

- Smoke modules use `suite_marks(feature=FEATURE_UI_SMOKE)` and
  `@pytest.mark.sanity`.
- Failure screenshot + Playwright trace behavior in root `conftest` is
  unchanged.
