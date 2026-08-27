# Quickstart: Horizontal Scaling — Layer 0 Smoke for New Dashboards

**Feature**: `004-horizontal-scaling` | **Date**: 2026-08-27

Implementers follow the sequence in [plan.md](./plan.md).

## Prerequisites

- Python 3.11+ venv with `requirements.txt` and Playwright Chromium
- Valid `.env` and `auth_state.json` (same as today's fleet runs)
- Branch `004-horizontal-scaling`
- Both catalog products exist: `תמונת מצב הפסקות חשמל`, `צריכת אשראי`

## Sequence

1. Point `ReportShell` catalog search at `self.DASHBOARD_SEARCH_TERM`
   when set, else `settings.DASHBOARD_SEARCH_TERM`.
2. Add Power Outages `page.py` / `conftest.py` / smoke test.
3. Add Credit Consumption `page.py` (popup dismiss before ready) /
   `conftest.py` / smoke test.
4. Leakage scan of `core/`.
5. Run the two new suites; confirm fleet smoke still passes.

## Commands

```powershell
rg -n "תמונת מצב הפסקות חשמל|לקוחות חיוניים מופסקים|צריכת אשראי|ממוצע הוצאות לקנייה בשגרה" core
rg -n -i "vehicles|district|subunit|total_vehicles|רכבים|מחוז" core
pytest tests/ui/power_outages_dashboard/ -m sanity
pytest tests/ui/credit_consumption_dashboard/ -m sanity
pytest tests/ui/fleet_dashboard/ -m sanity
```

Expected leakage scan: no matches in `core/` for the new-report strings.
Fleet tokens remain absent except generic last-refresh chrome.

Expected pytest: 100% green when each live report caption is within 24
hours. A stale caption MUST fail that suite's
`test_dashboard_updated_within_24_hours`.

## Frozen signatures (must remain)

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
def verify_freshness(self, max_hours: int = 24) -> None: ...
```

## Page attributes (normative)

```python
class PowerOutagesPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "תמונת מצב הפסקות חשמל"

class CreditConsumptionPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "צריכת אשראי"
```

## Done when

- [x] Catalog search uses per-page `DASHBOARD_SEARCH_TERM` with settings fallback
- [x] Power Outages smoke opens that report and calls `verify_freshness()`
- [x] Credit Consumption dismisses info popup before ready wait, then freshness
- [x] No JSON / slicer / KPI logic on the new pages
- [ ] Root `conftest.py` unchanged; fleet smoke still 100% green
- [x] `core/` has zero new-report product or ready-visual strings

Ready locators (field-confirmed landing titles):
`לקוחות חיוניים מופסקים` and `ממוצע הוצאות לקנייה בשגרה`.

Live run 2026-08-27: Power Outages freshness PASSED. Credit Consumption
navigation/ready PASSED; freshness correctly failed (caption 19/07/2026).

Next command after this plan: `/speckit-tasks` to turn the sequence into
`tasks.md`.
