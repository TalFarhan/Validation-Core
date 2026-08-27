# Quickstart: Mass Dashboards Addition — Layer 0 Freshness Smoke

**Feature**: `005-mass-dashboards-addition` | **Date**: 2026-08-27

Implementers follow the sequence in [plan.md](./plan.md).

## Prerequisites

- Python 3.11+ venv with `requirements.txt` and Playwright Chromium
- Valid `.env` and `auth_state.json` (same as today's fleet runs)
- Branch `005-mass-dashboards-addition`
- Four catalog products exist: `ניתוח התרעות`, `מרס"ל`,
  `הערכת מצב רשויות`, `תמ"צ חוסן`
- Feature 004 is already in the tree (`DASHBOARD_SEARCH_TERM` on
  `ReportShell`)

## Sequence

1. Confirm Layer 0 already reads `self.DASHBOARD_SEARCH_TERM`. Do not
   edit `core/` or `.env`.
2. Add Alerts Analysis `page.py` / `conftest.py` / smoke test.
3. Add Marsal `page.py` / `conftest.py` / smoke test.
4. Add Authorities Status `page.py` / `conftest.py` / smoke test.
5. Add Hosen Status `page.py` / `conftest.py` / smoke test.
6. Leakage scan of `core/`.
7. Run the four new suites. Ready locators are temporary; update after
   live-run feedback.

## Commands

```powershell
rg -n "ניתוח התרעות|מרס`"ל|הערכת מצב רשויות|תמ`"צ חוסן" core
pytest tests/ui/alerts_analysis_dashboard/ -m sanity
pytest tests/ui/marsal_dashboard/ -m sanity
pytest tests/ui/authorities_status_dashboard/ -m sanity
pytest tests/ui/hosen_status_dashboard/ -m sanity
```

Expected leakage scan: no matches in `core/` for the new-report strings.

Expected pytest: 100% green when each live report caption is within 24
hours **and** the temporary ready phrase is visible in the iframe. A
stale caption MUST fail that suite's
`test_dashboard_updated_within_24_hours`. A missing temporary phrase is
an expected locator fail until updated from live feedback.

## Frozen signatures (must remain)

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
def verify_freshness(self, max_hours: int = 24) -> None: ...
```

## Page attributes (normative)

```python
class AlertsAnalysisPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "ניתוח התרעות"

class MarsalPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'מרס"ל'

class AuthoritiesStatusPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "הערכת מצב רשויות"

class HosenStatusPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ חוסן'
```

## Done when

- [x] Four smoke packages exist under `tests/ui/` with page, fixture, and
      `test_dashboard_updated_within_24_hours`
- [x] Each page inherits `ReportShell` and sets the exact search term
- [x] Ready locators are temporary iframe phrases matching the search term
- [x] No JSON / slicer / KPI logic on the new pages
- [x] Nothing created under `pages/`; `.env` untouched; `core/` unchanged
- [x] `core/` has zero new-report product or ready-visual strings

Next command after this plan: `/speckit-tasks` to turn the sequence into
`tasks.md`.
