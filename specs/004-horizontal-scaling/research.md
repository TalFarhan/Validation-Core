# Research: Horizontal Scaling — Layer 0 Smoke for New Dashboards

**Feature**: `004-horizontal-scaling` | **Date**: 2026-08-27

All Technical Context items were known from the repo, Constitution v1.2.0,
feature 003 (`verify_freshness`), and the requester's architecture rules.
No `NEEDS CLARIFICATION` markers remain.

## Decision: Colocate thin page objects under `tests/ui/<report>/`

- **Decision**: Put `page.py`, `conftest.py`, and `test_dashboard_smoke.py`
  in `tests/ui/power_outages_dashboard/` and
  `tests/ui/credit_consumption_dashboard/`. Do not create
  `pages/power_outages_dashboard/` or `pages/credit_consumption_dashboard/`
  in this feature.
- **Rationale**: Requester CRITICAL ARCHITECTURE RULES. These pages have
  no KPI/slicer/chart surface yet; a `pages/` module would be an empty
  shell. Constitution requires `ReportShell` inheritance, not a folder.
- **Alternatives considered**: Mirror fleet under `pages/<report>/` —
  rejected (premature; user forbade business modules). Put both pages in
  `pages/` and tests only under `tests/ui/` — rejected (explicit layout).

## Decision: Per-page `DASHBOARD_SEARCH_TERM` with settings fallback

- **Decision**: Domain pages set class attribute `DASHBOARD_SEARCH_TERM`.
  `ReportShell` catalog search and the navigate log use
  `getattr(self, "DASHBOARD_SEARCH_TERM", None) or
  settings.DASHBOARD_SEARCH_TERM`. Do not add new `.env` keys.
- **Rationale**: Spec FR-004 / AC-001. Global `DASHBOARD_SEARCH_TERM` is
  the fleet product (`שליטה בניוד`). A second report cannot share Layer 0
  if search is process-global. Class attribute is configuration, not
  domain leakage in `core/` (core never names the new products).
- **Alternatives considered**: Change `.env` between pytest invocations —
  rejected (cannot run suites in one session). Override
  `_open_dashboard_via_portal_search` on each page — rejected (copies
  Layer 0). `os.environ` mutation in fixtures — rejected (racy with
  fleet).

## Decision: Local `dashboard` fixtures shadow the root fixture

- **Decision**: Each new package defines `dashboard(auth_page,
  browser_context)` that constructs that report's page, retries transient
  catalog/profile errors like the root fixture, and calls `navigate()`.
  Do not edit root `conftest.py`.
- **Rationale**: Spec FR-007 / AC-007. Pytest uses the closest fixture.
  Fleet tests keep `MainDashboardPage`. Copy the retry/auth-save shape
  from root so SSO glitches behave the same.
- **Alternatives considered**: Parametrize one root fixture — rejected
  (would change fleet contract). Pytest `dashboard` name different per
  suite — rejected (smoke test signature must stay
  `test_dashboard_updated_within_24_hours(dashboard)`).

## Decision: Credit popup dismiss before ready wait

- **Decision**: Add empty Layer 0 hook `before_report_ready_check()` on
  `ReportShell`, called immediately before each ready-locator visibility
  check (`_dashboard_ready`, navigate wait loop, reload wait loop).
  `CreditConsumptionPage` implements it by clicking a visible close
  control (X / Close / סגור / aria-label) inside the report iframe, and
  also dismisses in `after_navigate`. Missing popup is a no-op with a
  short timeout (~250ms), not `self.timeout`. The hook is a no-op on
  fleet and Power Outages.
- **Rationale**: Spec FR-005 / AC-006 and plan risk note:
  `after_navigate` in `ReportShell.navigate` runs *after*
  `expect(ready).to_be_visible`. If the overlay blocks the ready visual,
  after_navigate is too late. A hook is the seam a second report needs
  without copying `navigate`. Popup locators stay on the domain page.
- **Alternatives considered**: Only override `after_navigate` — rejected
  (too late). Copy `navigate` onto `CreditConsumptionPage` — rejected
  (duplicates Layer 0). Side-effect inside `_report_ready_locator` —
  rejected (locator is captured once before the wait loop).

## Decision: Ready locators are iframe text, not CSS/visual ids

- **Decision**: `_report_ready_locator()` returns
  `self._report_frame().get_by_text("<phrase>").first` for
  `אוכלוסייה מותרעת` and `כמות אוכלוסיה ברשויות` respectively.
- **Rationale**: Spec FR-001 / FR-002 / AC-003. Matches fleet's
  text-based ready KPI, using Layer 0 `_report_frame()` instead of a
  page-owned `frame_locator` duplicate.
- **Alternatives considered**: Visual GUID CSS — rejected (fragile,
  dashboard-specific chrome). Outer page `get_by_text` — rejected
  (labels live in the Power BI iframe).

## Decision: No JSON, no Slicer, no constitution amendment

- **Decision**: Do not add filter JSON, `Slicer` composition, KPI
  methods, or Constitution version bump. Reuse `verify_freshness` from
  003 unchanged.
- **Rationale**: Spec FR-006. Principle VII: do not genericize until
  needed. Popup locators are report-specific, so they stay on the page.
- **Alternatives considered**: Amend Constitution for test-colocated
  pages — rejected (PATCH not required; folder is a structure decision).
  Shared popup helper in `core/` — rejected (domain leakage).
