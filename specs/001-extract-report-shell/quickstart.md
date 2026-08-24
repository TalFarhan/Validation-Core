# Quickstart: Extract Generic ReportShell

**Feature**: `001-extract-report-shell` | **Date**: 2026-08-23

Implementers follow the Strangler Fig steps in [plan.md](./plan.md).
Do not implement everything in one edit.

## Prerequisites

- Python 3.11+ venv with `requirements.txt` and Playwright Chromium
- Valid `.env` and `auth_state.json` (same as today's fleet runs)
- Branch `001-extract-report-shell`

## After each major step

```powershell
pytest tests/ui/fleet_dashboard/ -m sanity
```

That suite MUST stay 100% green. Do not edit files under
`tests/ui/fleet_dashboard/` or `tests/e2e/` or `conftest.py`.

If a full portal run is impossible (no session), at minimum:

```powershell
python -c "from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage; from core.portal.page import ReportShell; assert issubclass(MainDashboardPage, ReportShell)"
```

…and a leakage scan before merge:

```powershell
rg -n -i "vehicles|district|subunit|total_vehicles|רכבים|מחוז" core
```

Expected: no matches.

## Step order (do not skip)

0. Baseline smoke
1. Empty `ReportShell` + inherit
2. Hook `_report_ready_locator` / `after_navigate` **in place** on the fleet page
3. Move leaf portal helpers
4. Move recovery + iframe wait
5. Move catalog methods
6. Move auth methods (must use the hook, not the fleet KPI attribute)
7. Move `navigate` and `reload_and_measure_ready_ms`
8. Leakage audit
9. Final `pytest tests/ui/fleet_dashboard/`

## Inheritance target

```text
from pages.base_page import BasePage          # unchanged
from core.portal.page import ReportShell      # new

class ReportShell(BasePage): ...
class MainDashboardPage(ReportShell): ...
```

## Frozen signatures

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
```

## Done when

- [x] `MainDashboardPage` inherits `ReportShell`
- [x] Listed portal methods live only in `core/portal/page.py`
- [x] Fleet page overrides `_report_ready_locator` and `after_navigate`
- [x] `core/` has zero fleet domain terms
- [x] `pytest tests/ui/fleet_dashboard/` is 100% green
- [x] Test files and `conftest.py` are unmodified

Next command after this plan: `/speckit-tasks` to turn the sequence into
`tasks.md`.
