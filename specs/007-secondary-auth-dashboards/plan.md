# Implementation Plan: Secondary-Auth Dashboards — Layer 0 Freshness Smoke + Bypass Hook

**Branch**: `007-secondary-auth-dashboards` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-secondary-auth-dashboards/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by
`/speckit-tasks` (not this command).

## Summary

Add a single generic Layer 0 seam — `_bypass_secondary_auth()` — to
`ReportShell`, invoked inside `navigate()` after the catalog click and before
the ready-locator wait, defaulting to a no-op. Then add four Layer 0-only
report bindings — Mass Events, Life-Saving Guidelines, Maya System, and Public
Shelters — that inherit `ReportShell`, open via per-page catalog search terms,
override `_bypass_secondary_auth()` with a placeholder (real clicks later),
wait on a **temporary** ready locator equal to that search term (exact text),
and reuse `verify_freshness()`. No JSON catalogs, no slicer/KPI/chart logic, no
`pages/` packages, no `.env` edits. The only `core/` change is the generic hook
plus its invocation — no product names or ready strings enter `core/`.

Technical approach: **one small Layer 0 seam + four thin domain pages colocated
with smoke tests** under `tests/ui/<report>/`. Each suite shadows the
`dashboard` fixture locally. Root fleet fixture stays unchanged; the default
hook is a no-op so fleet behavior is byte-for-byte the same.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, allure-pytest.
Existing: `ReportShell`, `verify_freshness`, `_catalog_search_term`,
`_open_dashboard_via_portal_search`, root `conftest.py` session browser /
`auth_page`.

**Storage**: N/A. No warehouse schema, no `data/*.json` for these reports.

**Testing**: `pytest` + Playwright Chromium. Binding gates:
`pytest tests/ui/mass_events_dashboard/`,
`pytest tests/ui/life_saving_guidelines_dashboard/`,
`pytest tests/ui/maya_system_dashboard/`,
`pytest tests/ui/public_shelters_dashboard/`.
Fleet regression: `pytest tests/ui/fleet_dashboard/` MUST remain 100% green
because Layer 0 is touched (new no-op hook). Markers `sanity`.

**Target Platform**: Windows workstation + Chromium, organizational Agamim
portal + Microsoft SSO (same as today).

**Project Type**: Internal validation framework (pytest page objects).

**Performance Goals**: Freshness reuses existing `self.timeout`. Default bypass
hook adds no wait (no-op); overrides implemented later may add short waits.

**Constraints**: Constitution v1.2.0 — zero domain leakage in `core/`; ready
visuals stay on domain pages; frozen fleet `navigate` /
`reload_and_measure_ready_ms` signatures; no Layer 2 slicer on the new pages;
do not create `pages/` or edit `.env`. The single permitted Layer 0 change is
the generic `_bypass_secondary_auth()` seam.

**Scale/Scope**: One ~2-line Layer 0 hook + one call site, four page classes
(~20–30 lines each), four local conftest fixtures, four ~10-line smoke tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: PASS — new pages inherit `ReportShell`. Portal/SSO/
  iframe/timeout/freshness stay in Layer 0. The new `_bypass_secondary_auth()`
  seam is generic (default no-op); per-page catalog term is configuration owned
  by the domain page.
- **Zero domain leakage**: PASS — the four product names and temporary ready
  phrases MUST NOT enter `core/`. Only the generic hook name is added.
- **Test contract**: PASS — root `conftest.py` `dashboard` fixture and
  `tests/ui/fleet_dashboard/` stay unchanged. New suites shadow `dashboard` in
  their own conftest. Fleet smoke is the Layer 0 regression gate because Layer 0
  is touched.
- **Extract shared only**: PASS — the new seam is a genuine shared extension
  point (multiple reports need it), not a per-report branch in `core/`.
- **Warehouse truth**: PASS — `db/` untouched; Layer 0 smoke uses UI
  last-refresh only.
- **Observability**: PASS — existing Allure / screenshot / trace hooks apply via
  root `auth_page`. New tests use `suite_marks` + `sanity`.

**Post-design re-check**: All gates still PASS. Colocating page objects under
`tests/ui/<report>/` matches features 004/005/006. No Complexity Tracking rows.

## Project Structure

### Documentation (this feature)

```text
specs/007-secondary-auth-dashboards/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── layer0-report-binding.md
└── tasks.md             # Phase 2 — /speckit-tasks (not this command)
```

### Source Code (repository root)

```text
core/portal/page.py       # CHANGED — add _bypass_secondary_auth() no-op + call it in navigate()

tests/ui/mass_events_dashboard/
  page.py                 # MassEventsPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

tests/ui/life_saving_guidelines_dashboard/
  page.py                 # LifeSavingGuidelinesPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

tests/ui/maya_system_dashboard/
  page.py                 # MayaSystemPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

tests/ui/public_shelters_dashboard/
  page.py                 # PublicSheltersPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

conftest.py               # UNCHANGED
pages/                    # UNCHANGED — do not create new packages
.env                      # UNCHANGED
```

**Structure Decision**: Same Layer 0-only exception as 004/005/006: thin page
objects live next to their smoke tests under `tests/ui/<report>/` until a later
feature adds business logic and a `pages/<report>/` module.

## Complexity Tracking

> No constitution violations.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Implementation Approach: One generic seam + four thin bindings

Sequence:

1. Add `_bypass_secondary_auth(self)` no-op to `ReportShell` (next to the other
   domain hooks such as `after_navigate` / `before_report_ready_check`) and call
   `self._bypass_secondary_auth()` in `navigate()` after the catalog-open branch
   and before `ready = self._report_ready_locator()`.
2. Add Mass Events page + fixture + freshness smoke (with placeholder override).
3. Add Life-Saving Guidelines page + fixture + freshness smoke.
4. Add Maya System page + fixture + freshness smoke.
5. Add Public Shelters page + fixture + freshness smoke.
6. Leakage audit of `core/` (no new-report strings; only the generic hook).
7. Collect the four new suites (live ready locators may fail until updated).

Each `_report_ready_locator` returns
`_report_frame().get_by_text(<search term>, exact=True)` as a temporary
stand-in. Each `_bypass_secondary_auth` override is a placeholder (comment or
`print`) until real clicks are supplied from live-run feedback.

## Risk notes

- Temporary ready locators matching the catalog search term may not exist as
  iframe text on the live landing page. Suites may fail the ready wait until
  locators are updated from live-run feedback. That is expected.
- The `_bypass_secondary_auth()` overrides are placeholders. Until real clicks
  are implemented, a report that truly gates behind a secondary screen may not
  reach its ready visual. That is expected and does not justify moving report
  logic into `core/`.
- The Layer 0 change is a no-op for fleet and for the 005/006 reports (they do
  not override the hook), so fleet smoke MUST stay green.
- Shared session tab may still show another report; `_dashboard_ready` using the
  new ready locator forces catalog search for the right product.
