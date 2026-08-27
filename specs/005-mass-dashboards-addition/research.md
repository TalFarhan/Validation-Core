# Research: Mass Dashboards Addition — Layer 0 Freshness Smoke

**Feature**: `005-mass-dashboards-addition` | **Date**: 2026-08-27

All Technical Context items were known from the repo, Constitution v1.2.0,
feature 004 (per-page `DASHBOARD_SEARCH_TERM` + local fixtures), and the
requester's architecture rules. No `NEEDS CLARIFICATION` markers remain.

## Decision: Colocate thin page objects under `tests/ui/<report>/`

- **Decision**: Put `page.py`, `conftest.py`, and `test_dashboard_smoke.py`
  in four new directories under `tests/ui/`. Do not create anything under
  `pages/`.
- **Rationale**: Requester CRITICAL ARCHITECTURE RULES. Same structure as
  Power Outages / Credit Consumption. Constitution requires `ReportShell`
  inheritance, not a folder.
- **Alternatives considered**: Mirror fleet under `pages/<report>/` —
  rejected (user forbade `pages/`). Shared package for all four reports —
  rejected (each suite must independently shadow `dashboard`).

## Decision: No Layer 0 or `.env` changes

- **Decision**: Do not edit `core/portal/page.py` or `.env`. Reuse
  `_catalog_search_term()` from feature 004.
- **Rationale**: Spec FR-006 / FR-010. Per-page search already works.
  Adding `.env` keys would force process-global product switching.
- **Alternatives considered**: New settings keys per dashboard — rejected
  (cannot run four suites in one session without mutating env). Override
  `_open_dashboard_via_portal_search` on each page — rejected (copies
  Layer 0).

## Decision: Temporary ready locator equals the search term

- **Decision**: `_report_ready_locator()` returns
  `self._iframe_phrase_locator(self.DASHBOARD_SEARCH_TERM)` (or the same
  literal). Update later from live-run feedback.
- **Rationale**: Requester explicit instruction. Real landing titles are
  unknown until a live run. Using the catalog phrase is a deliberate
  placeholder, not a claim that the title exists in the iframe.
- **Alternatives considered**: Copy Power Outages ready titles — rejected
  (wrong reports). Skip ready wait — rejected (`ReportShell` requires a
  domain locator). Outer-page catalog text as ready — rejected (must be
  inside the report iframe).

## Decision: Local `dashboard` fixtures copy the Power Outages shape

- **Decision**: Each package defines `dashboard(auth_page,
  browser_context)` matching
  `tests/ui/power_outages_dashboard/conftest.py` (transient catalog /
  profile retry, `save_auth_state`). Do not edit root `conftest.py`.
- **Rationale**: Spec FR-008 / AC-006. Proven retry shape; pytest closest
  fixture keeps fleet on `MainDashboardPage`.
- **Alternatives considered**: Parametrize one root fixture — rejected
  (fleet contract). Shared helper fixture in `tests/ui/conftest.py` —
  rejected (out of scope; copy-paste of ~30 lines is the 004 pattern).

## Decision: No JSON, no Slicer, no popup handling, no constitution amendment

- **Decision**: Do not add filter JSON, `Slicer` composition, KPI
  methods, popup dismiss, or Constitution version bump. Reuse
  `verify_freshness` from 003 unchanged.
- **Rationale**: Spec FR-007. None of the four reports specified an
  overlay. Principle VII: do not genericize until needed.
- **Alternatives considered**: Pre-emptively copy Credit Consumption
  popup code — rejected (no evidence these reports show an info page).
