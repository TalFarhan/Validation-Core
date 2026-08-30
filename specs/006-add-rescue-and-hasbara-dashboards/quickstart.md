# Quickstart: Rescue & Hasbara Dashboards — Layer 0 Freshness Smoke

**Feature**: `006-add-rescue-and-hasbara-dashboards` | **Date**: 2026-08-30

Implementers follow the sequence in [plan.md](./plan.md).

## Prerequisites

- Python 3.11+ venv with `requirements.txt` and Playwright Chromium
- Valid `.env` and `auth_state.json` (same as today's fleet runs)
- Branch `006-add-rescue-and-hasbara-dashboards`
- Two catalog products exist: `כשירויות חילוץ במרחב האזרחי`,
  `ניתוח פניות הסברה`
- Feature 004 is already in the tree (`DASHBOARD_SEARCH_TERM` on
  `ReportShell`)

## Sequence

1. Confirm Layer 0 already reads `self.DASHBOARD_SEARCH_TERM`. Do not
   edit `core/` or `.env`.
2. Add Rescue Capabilities `page.py` / `conftest.py` / smoke test.
3. Add Public Inquiries `page.py` / `conftest.py` / smoke test.
4. Leakage scan of `core/`.
5. Run the two new suites. Ready locators are temporary; update after
   live-run feedback.

## Commands

```powershell
rg -n "כשירויות חילוץ במרחב האזרחי|ניתוח פניות הסברה" core
pytest tests/ui/rescue_capabilities_dashboard/ -m sanity
pytest tests/ui/public_inquiries_dashboard/ -m sanity
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
class RescueCapabilitiesPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "כשירויות חילוץ במרחב האזרחי"

class PublicInquiriesPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "ניתוח פניות הסברה"
```

## Done when

- [x] Two smoke packages exist under `tests/ui/` with page, fixture, and
      `test_dashboard_updated_within_24_hours`
- [x] Each page inherits `ReportShell` and sets the exact search term
- [x] Ready locators are temporary iframe exact-text phrases matching the
      search term
- [x] No JSON / slicer / KPI logic on the new pages
- [x] Nothing created under `pages/`; `.env` untouched; `core/` unchanged
- [x] `core/` has zero new-report product or ready-visual strings

Next command after this plan: `/speckit-tasks` to turn the sequence into
`tasks.md`.
