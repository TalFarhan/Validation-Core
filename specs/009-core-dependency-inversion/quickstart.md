# Quickstart: Verify the Dependency Inversion Refactor

This quickstart is the manual verification path once the move is implemented (by `/speckit-implement`).
It does not perform the move; it proves the move is correct.

## 1. Prove the reverse dependency is gone

From the repo root, these must return **no matches** in live code:

```powershell
rg "from pages\.(base_page|errors)|import pages\.(base_page|errors)" core/ pages/ tests/
```

The only acceptable `ExpandHierarchyUnavailable` reference inside `pages/fleet_dashboard/` is its **class
definition** and local raises — not a `from pages.errors import ...` line.

## 2. Prove the new modules exist and import cleanly

```powershell
python -c "from core.base_page import BasePage; from core.errors import LoadTimeoutError; print('core ok')"
python -c "from pages.fleet_dashboard.main_dashboard_page import ExpandHierarchyUnavailable; print('fleet err ok')"
```

Both lines must print their `ok` message with no `ImportError`.

## 3. Prove the old modules are gone

```powershell
Test-Path pages/base_page.py   # must be False
Test-Path pages/errors.py      # must be False
```

## 4. Run the regression gate (Constitution III)

```powershell
pytest tests/ui/fleet_dashboard/
```

Expected: **100% pass**. This is the hard gate — the feature is not done unless this is green.

## 5. Confirm the drilldown e2e still collects

```powershell
pytest tests/e2e/test_chart_drilldown.py --collect-only
```

Expected: collection succeeds (the `ExpandHierarchyUnavailable` import resolves from the fleet page).

## Done-when checklist

- [ ] Step 1 grep returns no `pages.base_page` / `pages.errors` imports in live code.
- [ ] Step 2 both import probes print `ok`.
- [ ] Step 3 old files no longer exist.
- [ ] Step 4 fleet smoke suite is 100% green.
- [ ] Step 5 drilldown e2e collects without import error.
- [ ] No business logic / UI flow / chart logic changed; in-function comments are English only.
