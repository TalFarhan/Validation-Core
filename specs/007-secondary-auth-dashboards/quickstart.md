# Quickstart: Secondary-Auth Dashboards — Layer 0 Freshness Smoke + Bypass Hook

**Feature**: `007-secondary-auth-dashboards` | **Date**: 2026-08-30

Implementers follow the sequence in [plan.md](./plan.md).

## Prerequisites

- Python 3.11+ venv with `requirements.txt` and Playwright Chromium
- Valid `.env` and `auth_state.json` (same as today's fleet runs)
- Branch `007-secondary-auth-dashboards`
- Four catalog products exist: `תמ"צ אירועים המוניים`,
  `תמ"צ שליטה - סטטוס הנחיות מצילות חיים`, `מערכת המא"יה`,
  `תמ"צ מחסים ציבוריים`
- Feature 004 is already in the tree (`DASHBOARD_SEARCH_TERM` on `ReportShell`)

## Sequence

1. Add the generic `_bypass_secondary_auth()` no-op to `ReportShell` and call it
   in `navigate()` after the catalog click, before the ready-locator wait.
2. Add Mass Events `page.py` / `conftest.py` / smoke test (placeholder override).
3. Add Life-Saving Guidelines `page.py` / `conftest.py` / smoke test.
4. Add Maya System `page.py` / `conftest.py` / smoke test.
5. Add Public Shelters `page.py` / `conftest.py` / smoke test.
6. Leakage scan of `core/` (no new-report product/ready strings).
7. Run/collect the four new suites. Ready locators and bypass overrides are
   temporary; update after live-run feedback.

## Commands

```powershell
rg -n 'תמ"צ אירועים המוניים|תמ"צ שליטה - סטטוס הנחיות מצילות חיים|מערכת המא"יה|תמ"צ מחסים ציבוריים' core
pytest tests/ui/mass_events_dashboard/ tests/ui/life_saving_guidelines_dashboard/ tests/ui/maya_system_dashboard/ tests/ui/public_shelters_dashboard/ -m sanity --collect-only
```

Expected leakage scan: no matches in `core/` for the new-report strings.

Expected pytest: 100% green when each live report caption is within 24 hours
**and** the temporary ready phrase is visible in the iframe. A stale caption
MUST fail that suite's `test_dashboard_updated_within_24_hours`. A missing
temporary phrase (or an un-dismissed secondary-auth screen) is an expected
locator fail until updated from live feedback.

## Frozen signatures (must remain)

```python
def navigate(self, *, force_reload: bool = False) -> None: ...
def reload_and_measure_ready_ms(self) -> int: ...
def verify_freshness(self, max_hours: int = 24) -> None: ...
```

## Page attributes (normative)

```python
class MassEventsPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ אירועים המוניים'

class LifeSavingGuidelinesPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ שליטה - סטטוס הנחיות מצילות חיים'

class MayaSystemPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'מערכת המא"יה'

class PublicSheltersPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ מחסים ציבוריים'
```

Each also overrides `_bypass_secondary_auth(self)` with a placeholder.

## Done when

- [x] `ReportShell` exposes a no-op `_bypass_secondary_auth()` called in
      `navigate()` after the catalog click and before the ready-locator wait
- [x] Four smoke packages exist under `tests/ui/` with page, fixture, and
      `test_dashboard_updated_within_24_hours`
- [x] Each page inherits `ReportShell`, sets the exact search term, and
      overrides `_bypass_secondary_auth` with a placeholder
- [x] Ready locators are temporary iframe exact-text phrases matching the
      search term
- [x] No JSON / slicer / KPI logic on the new pages
- [x] Nothing created under `pages/`; `.env` untouched
- [x] `core/` has zero new-report product or ready-visual strings (only the
      generic `_bypass_secondary_auth` hook)

Next command after this plan: `/speckit-tasks` to turn the sequence into
`tasks.md`.
