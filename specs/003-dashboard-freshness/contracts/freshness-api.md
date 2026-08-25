# Contract: Report freshness API (test-facing)

**Feature**: `003-dashboard-freshness` | **Date**: 2026-08-25

Consumers: `tests/ui/fleet_dashboard/test_dashboard_smoke.py` (new test),
any future report page that inherits `ReportShell`.
Existing consumers of `navigate` / `reload_and_measure_ready_ms` MUST NOT
need edits.

## Additive public method

### `ReportShell.verify_freshness(max_hours: int = 24) -> None`

Inherited as `MainDashboardPage.verify_freshness`.

| Rule | Value |
|------|--------|
| Required args | none beyond `self` |
| `max_hours` | `int`, default `24` |
| Return | `None` on success |
| Side effects | None (read-only; no reload, no filter change) |
| Locator | Regex or text locator for `הדשבורד עודכן לאחרונה ב:` inside the Power BI iframe |
| Parse | Python `datetime`; compare `datetime.now() - parsed` to `max_hours` |
| Errors | `AssertionError` — caption missing, unparseable, or older than `max_hours` |

Caller: `test_dashboard_updated_within_24_hours(dashboard)` →
`dashboard.verify_freshness()`.

## Frozen methods (unchanged)

### `navigate(*, force_reload: bool = False) -> None`

Unchanged signature and behavior.

### `reload_and_measure_ready_ms() -> int`

Unchanged signature and behavior.

## Fixture-visible helpers (unchanged)

`conftest.py` MUST NOT be edited. Names remain resolvable:

- `_dashboard_ready() -> bool`
- `_is_portal_profile_error() -> bool`
- `_recover_from_portal_glitch() -> None`

## Domain page

`MainDashboardPage` MUST NOT add a competing freshness method or
hardcoded last-refresh CSS. Inheritance is the contract.

## Layer 3 test contract

```python
@pytest.mark.sanity
def test_dashboard_updated_within_24_hours(dashboard):
    dashboard.verify_freshness()
```

The test MUST NOT contain iframe locators, date parsing, or CSS selectors.

## Leakage contract

`core/**` MUST match none of:

```text
vehicles|district|subunit|sub_unit|total_vehicles|רכבים|מחוז
```

Allowed in `core/`: the last-refresh phrase `הדשבורד עודכן לאחרונה ב:`
and generic words (dashboard, iframe, portal, datetime).

Dashboard-specific CSS selectors and visual GUIDs are forbidden in Layer 0.

## Observability contract

- `verify_freshness` records an Allure step.
- Failure screenshot + Playwright trace behavior in `conftest` is unchanged.
- No requirement to write a CSV UI log line (read-only check).
