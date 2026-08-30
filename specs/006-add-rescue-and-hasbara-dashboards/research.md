# Research: Rescue & Hasbara Dashboards — Layer 0 Freshness Smoke

**Feature**: `006-add-rescue-and-hasbara-dashboards` | **Date**: 2026-08-30

All Technical Context items were known from the repo, Constitution v1.2.0,
feature 004 (per-page `DASHBOARD_SEARCH_TERM` + local fixtures), feature
005 (mass dashboards addition), and the requester's architecture rules. No
`NEEDS CLARIFICATION` markers remain.

## Decision: Colocate thin page objects under `tests/ui/<report>/`

- **Decision**: Put `page.py`, `conftest.py`, and `test_dashboard_smoke.py`
  in two new directories under `tests/ui/`. Do not create anything under
  `pages/`.
- **Rationale**: Requester CRITICAL ARCHITECTURE RULES. Same structure as
  Power Outages / Hosen Status. Constitution requires `ReportShell`
  inheritance, not a folder.
- **Alternatives considered**: Mirror fleet under `pages/<report>/` —
  rejected (user forbade `pages/`). Shared package for both reports —
  rejected (each suite must independently shadow `dashboard`).

## Decision: No Layer 0 or `.env` changes

- **Decision**: Do not edit `core/portal/page.py` or `.env`. Reuse
  `_catalog_search_term()` from feature 004.
- **Rationale**: Spec FR-004 / FR-008. Per-page search already works.
  Adding `.env` keys would force process-global product switching.
- **Alternatives considered**: New settings keys per dashboard — rejected
  (cannot run both suites in one session without mutating env). Override
  `_open_dashboard_via_portal_search` on each page — rejected (copies
  Layer 0).

## Decision: Temporary ready locator equals the search term (exact text)

- **Decision**: `_report_ready_locator()` returns
  `self._report_frame().get_by_text(self.DASHBOARD_SEARCH_TERM, exact=True)`.
  Update later from live-run feedback.
- **Rationale**: Requester explicit instruction (`exact=True`). Real
  landing titles are unknown until a live run. Using the catalog phrase is
  a deliberate placeholder, not a claim that the title exists in the
  iframe. `exact=True` matches the confirmed Hosen Status pattern from 005.
- **Alternatives considered**: Copy Power Outages ready titles — rejected
  (wrong reports). `_iframe_phrase_locator` (substring) — rejected
  (requester asked for exact match). Skip ready wait — rejected
  (`ReportShell` requires a domain locator).

## Decision: Local `dashboard` fixtures copy the existing shape

- **Decision**: Each package defines `dashboard = bind_dashboard(<Page>)`
  from `tests/helpers/dashboard_fixture.py`, matching the existing suites
  (`tests/ui/hosen_status_dashboard/conftest.py`). Do not edit root
  `conftest.py`.
- **Rationale**: Spec FR-006 / AC-006. Proven retry shape; pytest closest
  fixture keeps fleet on `MainDashboardPage`.
- **Alternatives considered**: Parametrize one root fixture — rejected
  (fleet contract). Inline copy of the ~30-line retry body — rejected
  (`bind_dashboard` already exists as the shared helper).

## Decision: No JSON, no Slicer, no popup handling, no constitution amendment

- **Decision**: Do not add filter JSON, `Slicer` composition, KPI
  methods, popup dismiss, or Constitution version bump. Reuse
  `verify_freshness` from 003 unchanged.
- **Rationale**: Spec FR-005. Neither report specified an overlay.
  Principle VII: do not genericize until needed.
- **Alternatives considered**: Pre-emptively copy Credit Consumption
  popup code — rejected (no evidence these reports show an info page).
