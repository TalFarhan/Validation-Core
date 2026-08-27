# Contract: Layer 0 report binding (test-facing)

**Feature**: `004-horizontal-scaling` | **Date**: 2026-08-27

Consumers: `tests/ui/power_outages_dashboard/test_dashboard_smoke.py`,
`tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py`.
Fleet consumers of root `dashboard` / `navigate` /
`reload_and_measure_ready_ms` MUST NOT need edits.

## Domain pages

### `PowerOutagesPage(ReportShell)`

| Rule | Value |
|------|--------|
| File | `tests/ui/power_outages_dashboard/page.py` |
| `DASHBOARD_SEARCH_TERM` | `"תמונת מצב הפסקות חשמל"` |
| `_report_ready_locator()` | iframe text `"אוכלוסייה מותרעת"` |
| Freshness | inherited `verify_freshness` — no override |
| Forbidden | JSON, `Slicer`, KPI/chart/table methods |

### `CreditConsumptionPage(ReportShell)`

| Rule | Value |
|------|--------|
| File | `tests/ui/credit_consumption_dashboard/page.py` |
| `DASHBOARD_SEARCH_TERM` | `"צריכת אשראי"` |
| `_report_ready_locator()` | iframe text `"כמות אוכלוסיה ברשויות"` |
| Popup | dismiss info-page close/X before ready wait; no-op if absent |
| Freshness | inherited `verify_freshness` — no override |
| Forbidden | JSON, `Slicer`, KPI/chart/table methods |

## Layer 0 additive behavior

### Catalog search term

`ReportShell` MUST resolve:

```python
getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM
```

`core/` MUST NOT contain the Power Outages or Credit Consumption Hebrew
product names or ready-visual strings.

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

Each new package:

```python
@pytest.fixture
def dashboard(auth_page, browser_context):
    page_obj = <ReportPage>(auth_page)
    page_obj.navigate()
    return page_obj
```

Retry/transient profile-error handling MAY match the root fixture.
`auth_page` remains the shared session tab.

## Layer 3 test contract

```python
@pytest.mark.sanity
def test_dashboard_updated_within_24_hours(dashboard):
    dashboard.verify_freshness()
```

The test MUST NOT contain iframe locators, date parsing, CSS, or popup
clicks — those belong on the page object.

## Leakage contract

`core/**` MUST match none of:

```text
תמונת מצב הפסקות חשמל|אוכלוסייה מותרעת|צריכת אשראי|כמות אוכלוסיה ברשויות
```

and none of the existing fleet leakage tokens from 003
(`vehicles|district|subunit|רכבים|מחוז`).

## Observability contract

- Smoke modules use `suite_marks(feature=FEATURE_UI_SMOKE)` and
  `@pytest.mark.sanity`.
- Failure screenshot + Playwright trace behavior in root `conftest` is
  unchanged.
