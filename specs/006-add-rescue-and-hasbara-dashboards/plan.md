# Implementation Plan: Rescue & Hasbara Dashboards — Layer 0 Freshness Smoke

**Branch**: `006-add-rescue-and-hasbara-dashboards` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-add-rescue-and-hasbara-dashboards/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by
`/speckit-tasks` (not this command).

## Summary

Add two Layer 0-only report bindings — Rescue Capabilities and Public
Inquiries — that inherit `ReportShell`, open via per-page catalog search
terms, wait on a **temporary** ready locator equal to that search term
(exact text, to be replaced after live-run feedback), and reuse
`verify_freshness()`. No JSON catalogs, no slicer/KPI/chart logic, no
`pages/` packages, no `.env` edits, and no Layer 0 code changes
(feature 004 already resolves `DASHBOARD_SEARCH_TERM`).

Technical approach: **thin domain pages colocated with smoke tests** under
`tests/ui/<report>/`. Each suite shadows the `dashboard` fixture locally.
Root fleet fixture stays unchanged.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, allure-pytest.
Existing: `ReportShell`, `verify_freshness`, `_catalog_search_term`,
root `conftest.py` session browser / `auth_page`.

**Storage**: N/A. No warehouse schema, no `data/*.json` for these reports.

**Testing**: `pytest` + Playwright Chromium. Binding gates:
`pytest tests/ui/rescue_capabilities_dashboard/`,
`pytest tests/ui/public_inquiries_dashboard/`.
Fleet regression: `pytest tests/ui/fleet_dashboard/` MUST remain 100%
green if Layer 0 is touched (this feature does not intend to touch it).
Markers `sanity`.

**Target Platform**: Windows workstation + Chromium, organizational Agamim
portal + Microsoft SSO (same as today).

**Project Type**: Internal validation framework (pytest page objects).

**Performance Goals**: Freshness reuses existing `self.timeout`. No extra
popup waits (neither report specifies an overlay).

**Constraints**: Constitution v1.2.0 — zero domain leakage in `core/`;
ready visuals stay on domain pages; frozen fleet `navigate` /
`reload_and_measure_ready_ms` signatures; no Layer 2 slicer on the new
pages; do not create `pages/` or edit `.env`.

**Scale/Scope**: Two page classes (~15–25 lines each), two local conftest
fixtures, two ~10-line smoke tests. Zero Layer 0 edits unless a regression
is found.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: PASS — new pages inherit `ReportShell`. Portal/SSO/
  iframe/timeout/freshness stay in Layer 0. Per-page catalog term is
  configuration owned by the domain page (already read by Layer 0).
- **Zero domain leakage**: PASS — the two product names and temporary
  ready phrases MUST NOT enter `core/`.
- **Test contract**: PASS — root `conftest.py` `dashboard` fixture and
  `tests/ui/fleet_dashboard/` stay unchanged. New suites shadow
  `dashboard` in their own conftest. Fleet smoke remains the Layer 0
  regression gate if Layer 0 is touched.
- **Extract shared only**: PASS — no new Layer 0 APIs. Feature 004 already
  added per-page search term + `before_report_ready_check`.
- **Warehouse truth**: PASS — `db/` untouched; Layer 0 smoke uses UI
  last-refresh only.
- **Observability**: PASS — existing Allure / screenshot / trace hooks
  apply via root `auth_page`. New tests use `suite_marks` + `sanity`.

**Post-design re-check**: All gates still PASS. Colocating page objects
under `tests/ui/<report>/` matches feature 004/005. No Complexity Tracking
rows.

## Project Structure

### Documentation (this feature)

```text
specs/006-add-rescue-and-hasbara-dashboards/
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
tests/ui/rescue_capabilities_dashboard/
  page.py                 # RescueCapabilitiesPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

tests/ui/public_inquiries_dashboard/
  page.py                 # PublicInquiriesPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

core/portal/page.py       # UNCHANGED
conftest.py               # UNCHANGED
pages/                    # UNCHANGED — do not create new packages
.env                      # UNCHANGED
```

**Structure Decision**: Same Layer 0-only exception as 004/005: thin page
objects live next to their smoke tests under `tests/ui/<report>/` until a
later feature adds business logic and a `pages/<report>/` module.

## Complexity Tracking

> No constitution violations.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Implementation Approach: Two thin bindings, no Layer 0 change

Sequence:

1. Confirm `ReportShell._catalog_search_term` already reads
   `self.DASHBOARD_SEARCH_TERM`. Do not edit `core/`.
2. Add Rescue Capabilities page + fixture + freshness smoke.
3. Add Public Inquiries page + fixture + freshness smoke.
4. Leakage audit of `core/` (no new-report strings).
5. Run the two new suites (live ready locators may fail until updated).

Each `_report_ready_locator` returns
`_report_frame().get_by_text(<search term>, exact=True)` as a temporary
stand-in.

## Risk notes

- Temporary ready locators matching the catalog search term may not
  exist as iframe text on the live landing page. Suites may fail the
  ready wait until locators are updated from live-run feedback. That is
  expected, not a reason to put strings in `core/`.
- Root `dashboard` fixture would steal fleet page objects if new tests
  lived under `tests/ui/fleet_dashboard/`. Separate packages + local
  fixtures avoid that.
- Shared session tab may still show another report; `_dashboard_ready`
  using the new ready locator forces catalog search for the right product.
