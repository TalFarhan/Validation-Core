# Implementation Plan: Horizontal Scaling — Layer 0 Smoke for New Dashboards

**Branch**: `004-horizontal-scaling` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-horizontal-scaling/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by
`/speckit-tasks` (not this command).

## Summary

Add two Layer 0-only report bindings — Power Outages and Credit Consumption —
that inherit `ReportShell`, open via per-page catalog search terms, wait on
domain ready visuals, and reuse `verify_freshness()`. Credit Consumption
dismisses a blocking info-page popup before the ready wait. No JSON catalogs
and no slicer/KPI/chart logic.

Technical approach: **thin domain pages colocated with smoke tests**. Small
additive Layer 0 change so catalog search reads `self.DASHBOARD_SEARCH_TERM`
with fallback to `settings.DASHBOARD_SEARCH_TERM`, plus empty hook
`before_report_ready_check()` so Credit Consumption can dismiss a blocking
popup before the ready wait. Root fleet `dashboard` fixture stays
unchanged; each new suite shadows it locally.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, allure-pytest.
Existing: `ReportShell`, `verify_freshness`, root `conftest.py` session
browser / `auth_page`.

**Storage**: N/A. No warehouse schema, no `data/*.json` for these reports.

**Testing**: `pytest` + Playwright Chromium. Binding gates:
`pytest tests/ui/power_outages_dashboard/` and
`pytest tests/ui/credit_consumption_dashboard/`. Fleet regression:
`pytest tests/ui/fleet_dashboard/` MUST remain 100% green. Markers
`sanity`.

**Target Platform**: Windows workstation + Chromium, organizational Agamim
portal + Microsoft SSO (same as today).

**Project Type**: Internal validation framework (pytest page objects).

**Performance Goals**: Popup dismiss uses a short visibility budget (1–3s),
not a second full-page reload. Freshness reuses existing `self.timeout`.

**Constraints**: Constitution v1.2.0 — zero domain leakage in `core/`;
per-page search term MAY be read by Layer 0 as configuration; ready
visuals and popup locators stay on domain pages; frozen fleet
`navigate` / `reload_and_measure_ready_ms` signatures; no Layer 2 slicer
on the new pages.

**Scale/Scope**: Two page classes (~40–80 lines each), two local
conftest fixtures, two ~8-line smoke tests, plus a small search-term
read on `ReportShell` (~5–15 lines).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: PASS — new pages inherit `ReportShell`. Portal/SSO/
  iframe/timeout/freshness stay in Layer 0. Per-page catalog term is
  configuration owned by the domain page.
- **Zero domain leakage**: PASS — Power Outages / Credit Consumption
  names, ready text (`לקוחות חיוניים מופסקים`, `ממוצע הוצאות לקנייה בשגרה`), and
  popup close locators MUST NOT enter `core/`. Layer 0 only reads
  `DASHBOARD_SEARCH_TERM` from the instance/class when set.
- **Test contract**: PASS — root `conftest.py` `dashboard` fixture and
  `tests/ui/fleet_dashboard/` stay unchanged. New suites shadow
  `dashboard` in their own conftest. Fleet smoke remains the Layer 0
  regression gate.
- **Extract shared only**: PASS — Layer 0 additions are (1) resolving
  catalog search from the page when present and (2) empty
  `before_report_ready_check` seam for overlays. Popup locators stay on
  `CreditConsumptionPage`. No new slicer/KPI APIs.
- **Warehouse truth**: PASS — `db/` untouched; Layer 0 smoke uses UI
  last-refresh only.
- **Observability**: PASS — existing Allure / screenshot / trace hooks
  apply via root `auth_page`. New tests use `suite_marks` + `sanity`.

**Post-design re-check**: All gates still PASS. Colocating page objects
under `tests/ui/<report>/` (instead of `pages/<report>/`) is a structure
choice for a Layer 0-only slice, not a principle violation: Constitution
requires inheritance of `ReportShell`, not a specific folder for pages
that have no business module yet. No Complexity Tracking rows.

## Project Structure

### Documentation (this feature)

```text
specs/004-horizontal-scaling/
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
core/portal/page.py
  # catalog search uses self.DASHBOARD_SEARCH_TERM or settings default

tests/ui/power_outages_dashboard/
  page.py                 # PowerOutagesPage(ReportShell)
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

tests/ui/credit_consumption_dashboard/
  page.py                 # CreditConsumptionPage(ReportShell) + popup dismiss
  conftest.py             # dashboard fixture
  test_dashboard_smoke.py # test_dashboard_updated_within_24_hours

conftest.py               # UNCHANGED (fleet dashboard fixture)
pages/fleet_dashboard/    # UNCHANGED
core/components/slicer.py # UNCHANGED
data/                     # UNCHANGED — no new JSON
db/                       # UNCHANGED
```

**Structure Decision**: Validation Core layout with an intentional
Layer 0-only exception: thin page objects live next to their smoke tests
under `tests/ui/<report>/` until a later feature adds business logic and
a `pages/<report>/` module. Do not create empty `pages/` packages or
filter JSON now.

## Complexity Tracking

> No constitution violations.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Implementation Approach: Thin bindings + per-page search term

Sequence:

1. Teach `ReportShell._open_dashboard_via_portal_search` (and navigate
   log line) to use `getattr(self, "DASHBOARD_SEARCH_TERM", None) or
   settings.DASHBOARD_SEARCH_TERM`.
2. Add `PowerOutagesPage` + local fixture + freshness smoke.
3. Add `CreditConsumptionPage` with popup dismiss before ready wait +
   local fixture + freshness smoke.
4. Leakage audit of `core/` (no new-report strings).
5. Run the two new suites and fleet smoke.

## Risk notes

- If Layer 0 keeps using only `settings.DASHBOARD_SEARCH_TERM`, both new
  suites would open the fleet product. Per-page term is mandatory.
- `after_navigate()` runs *after* the ready wait in `ReportShell.navigate`.
  Credit Consumption MUST dismiss the popup before that wait (e.g. from
  `_report_ready_locator` / an override around ready detection), not only
  in `after_navigate`.
- Root `dashboard` fixture would steal fleet page objects if new tests
  lived under `tests/ui/fleet_dashboard/`. Separate packages + local
  fixtures avoid that.
- Shared session tab may still show the fleet report; `_dashboard_ready`
  using the new ready locator forces catalog search for the right product.
