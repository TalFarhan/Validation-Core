# Quickstart: Dashboard Freshness Verification

**Feature**: `003-dashboard-freshness` | **Date**: 2026-08-25

Implementers follow the additive sequence in [plan.md](./plan.md).

## Prerequisites

- Python 3.11+ venv with `requirements.txt` and Playwright Chromium
- Valid `.env` and `auth_state.json` (same as today's fleet runs)
- Branch `003-dashboard-freshness`

## Sequence

1. Amend Constitution Principles I and VII to v1.2.0 and sync
   `.specify/templates/` (plan, spec, tasks).
2. Add `verify_freshness(max_hours: int = 24)` on `ReportShell` in
   `core/portal/page.py`.
3. Add `test_dashboard_updated_within_24_hours` in
   `tests/ui/fleet_dashboard/test_dashboard_smoke.py`.
4. Leakage scan.
5. Run the fleet smoke suite.

## Commands

```powershell
rg -n -i "vehicles|district|subunit|total_vehicles|רכבים|מחוז" core
pytest tests/ui/fleet_dashboard/ -m sanity
```

Expected leakage scan: no matches except the allowed last-refresh phrase
(that phrase does not contain those tokens).

Expected pytest: 100% green when the live report caption is within 24
hours. A stale caption MUST fail `test_dashboard_updated_within_24_hours`.

## Frozen signatures (must remain)

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
```

## Additive signature

```python
def verify_freshness(self, max_hours: int = 24) -> None: ...
```

## Done when

- [x] Constitution v1.2.0 authorizes last-refresh verification on Layer 0
- [x] `ReportShell.verify_freshness` locates the caption inside the iframe
      by text/regex and asserts age ≤ `max_hours`
- [x] `MainDashboardPage` has no freshness override
- [x] `test_dashboard_updated_within_24_hours` calls `dashboard.verify_freshness()`
- [x] `core/` has zero fleet domain terms
- [x] `pytest tests/ui/fleet_dashboard/` is 100% green when the report is fresh
- [x] `conftest.py` and existing smoke tests are unmodified

Next command after this plan: `/speckit-tasks` to turn the sequence into
`tasks.md`.
