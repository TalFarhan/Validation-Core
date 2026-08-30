# Research: Secondary-Auth Dashboards — Layer 0 Freshness Smoke + Bypass Hook

**Feature**: `007-secondary-auth-dashboards` | **Date**: 2026-08-30

All Technical Context items were known from the repo, Constitution v1.2.0,
feature 004 (per-page `DASHBOARD_SEARCH_TERM` + local fixtures), features
005/006 (additional dashboards), and the requester's architecture rules. No
`NEEDS CLARIFICATION` markers remain.

## Decision: Add a generic `_bypass_secondary_auth()` seam to Layer 0

- **Decision**: Add `def _bypass_secondary_auth(self): pass` to `ReportShell`
  alongside the other domain hooks (`after_navigate`,
  `before_report_ready_check`) and invoke `self._bypass_secondary_auth()` in
  `navigate()` after the catalog-open branch and before
  `ready = self._report_ready_locator()`.
- **Rationale**: Multiple new reports gate behind a secondary auth/entry screen
  after the catalog click. A generic no-op seam keeps report-specific dismissal
  in the domain page (override) while Layer 0 stays report-agnostic. Placing the
  call after the catalog click and before the ready wait is exactly where a
  post-catalog interstitial must be handled.
- **Alternatives considered**: Put per-report interstitial handling in `core/` —
  rejected (domain leakage). Handle it inside each `_report_ready_locator` —
  rejected (locator getters must stay side-effect free). Reuse
  `before_report_ready_check` — rejected: it runs on every ready poll and also
  fires for fleet; the bypass must run once, right after the catalog click.

## Decision: Colocate thin page objects under `tests/ui/<report>/`

- **Decision**: Put `page.py`, `conftest.py`, and `test_dashboard_smoke.py` in
  four new directories under `tests/ui/`. Do not create anything under `pages/`.
- **Rationale**: Requester CRITICAL ARCHITECTURE RULES. Same structure as
  features 005/006 (Power Outages / Hosen Status pattern). Constitution requires
  `ReportShell` inheritance, not a folder.
- **Alternatives considered**: Mirror fleet under `pages/<report>/` — rejected
  (user forbade `pages/`). Shared package for the four reports — rejected (each
  suite must independently shadow `dashboard`).

## Decision: No `.env` changes; only the generic hook enters `core/`

- **Decision**: Do not edit `.env`. The only `core/portal/page.py` change is the
  generic `_bypass_secondary_auth()` hook and its `navigate()` call. Reuse
  `_catalog_search_term()` from feature 004.
- **Rationale**: Spec FR-006 / FR-009. Per-page search already works. Adding
  `.env` keys would force process-global product switching.
- **Alternatives considered**: New settings keys per dashboard — rejected
  (cannot run all four suites in one session without mutating env). Override
  `_open_dashboard_via_portal_search` on each page — rejected (copies Layer 0).

## Decision: Temporary ready locator equals the search term (exact text)

- **Decision**: `_report_ready_locator()` returns
  `self._report_frame().get_by_text(self.DASHBOARD_SEARCH_TERM, exact=True)`.
  Update later from live-run feedback.
- **Rationale**: Requester explicit instruction (`exact=True`). Real landing
  titles are unknown until a live run. Using the catalog phrase is a deliberate
  placeholder, matching the confirmed Hosen Status pattern from 005.
- **Alternatives considered**: Guess landing titles — rejected (wrong reports).
  `_iframe_phrase_locator` (substring) — rejected (requester asked for exact
  match). Skip ready wait — rejected (`ReportShell` requires a domain locator).

## Decision: `_bypass_secondary_auth` overrides are placeholders

- **Decision**: Each page overrides `_bypass_secondary_auth(self)` with a simple
  comment or `print` (e.g. `print("Waiting for discovery run to reveal auth
  screen")`). Real clicks come later from live-run feedback.
- **Rationale**: Requester explicit instruction. The real interstitial and its
  selectors are unknown until a discovery run. The placeholder makes the seam
  visible and testable without asserting a screen shape that has not been
  observed.
- **Alternatives considered**: Implement speculative clicks now — rejected (no
  observed screen). Leave the override off entirely — rejected (requester wants
  the seam present on each page for the later fill-in).

## Decision: Local `dashboard` fixtures copy the existing shape

- **Decision**: Each package defines `dashboard = bind_dashboard(<Page>)` from
  `tests/helpers/dashboard_fixture.py`, matching the existing suites
  (`tests/ui/hosen_status_dashboard/conftest.py`). Do not edit root
  `conftest.py`.
- **Rationale**: Spec FR-008 / AC-006. Proven retry shape; pytest closest
  fixture keeps fleet on `MainDashboardPage`.
- **Alternatives considered**: Parametrize one root fixture — rejected (fleet
  contract). Inline copy of the retry body — rejected (`bind_dashboard` already
  exists as the shared helper).

## Decision: No JSON, no Slicer, no constitution amendment

- **Decision**: Do not add filter JSON, `Slicer` composition, KPI methods, or a
  Constitution version bump. Reuse `verify_freshness` from 003 unchanged.
- **Rationale**: Spec FR-007. Principle VII: do not genericize beyond the single
  shared seam the four reports actually need.
- **Alternatives considered**: Pre-emptively copy Credit Consumption popup code
  — rejected (the secondary-auth screen shape is not yet observed).
