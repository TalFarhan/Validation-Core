# Implementation Plan: Dashboard Freshness Verification

**Branch**: `003-dashboard-freshness` | **Date**: 2026-08-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-dashboard-freshness/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by
`/speckit-tasks` (not this command).

## Summary

Add generic last-refresh verification to Layer 0 `ReportShell` as
`verify_freshness(max_hours: int = 24)`. The method locates the standard
Power BI caption containing `הדשבורד עודכן לאחרונה ב:` inside the report
iframe (regex / text locator, no fleet CSS), parses the timestamp with
`datetime`, and asserts `datetime.now() - parsed <= max_hours`. Apply it
with one new fleet smoke test
`test_dashboard_updated_within_24_hours(dashboard)`. Amend Constitution
Principles I and VII in the same change so last-refresh chrome is
authorized Layer 0 behavior.

Technical approach: **additive Layer 0 method**. No Strangler Fig. Do not
override on `MainDashboardPage`. Existing navigate / reload contracts stay
frozen.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, allure-pytest.
Existing helpers: `ReportShell._dashboard_iframe` /
`_wait_for_dashboard_iframe`, `datetime`, `re`.

**Storage**: N/A. No warehouse schema changes. UI caption is the source of
last-refresh truth.

**Testing**: `pytest` + Playwright Chromium. Binding gate:
`pytest tests/ui/fleet_dashboard/` (markers `sanity`). Add one test in
`tests/ui/fleet_dashboard/test_dashboard_smoke.py`. Do not edit
`conftest.py` or existing smoke tests.

**Target Platform**: Windows workstation + Chromium, organizational Agamim
portal + Microsoft SSO (same as today).

**Project Type**: Internal validation framework (pytest page objects).

**Performance Goals**: Freshness check uses existing `self.timeout` for
caption visibility. It MUST NOT add a second full-page reload.

**Constraints**: Constitution v1.1.0 amended to v1.2.0 in this feature —
zero domain leakage in `core/`; last-refresh Hebrew phrase is generic
chrome; frozen `navigate` / `reload_and_measure_ready_ms`; keep Allure
steps and failure screenshots.

**Scale/Scope**: One new method on `ReportShell` (~40–80 lines) plus one
smoke test (~8 lines). Fleet page unchanged. Slicer/KPI/chart code
untouched.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: PASS after Principle I amendment — last-refresh
  verification lives on `ReportShell` in `core/portal/page.py`. Domain
  pages inherit it; `MainDashboardPage` MUST NOT re-implement it.
- **Zero domain leakage**: PASS — locate generic last-refresh chrome by
  text/regex inside the iframe. `core/` forbids vehicles, district,
  subunit, fleet KPI/chart titles, and dashboard-specific CSS/visual ids.
- **Test contract**: PASS — existing smoke tests unchanged; new test added
  in the same change. `pytest tests/ui/fleet_dashboard/` MUST be 100% green
  when the live report is actually fresh. `navigate` /
  `reload_and_measure_ready_ms` stay frozen.
- **Extract shared only**: PASS after Principle VII amendment — last-
  refresh caption is shared Power BI chrome, analogous to iframe wait.
  KPI, tabs, charts, tables, drilldown, slicers stay on the domain page.
- **Warehouse truth**: PASS — `db/` untouched; no SQL in Layer 0. The UI
  caption is the freshness source of truth for this check.
- **Observability**: PASS — Allure step on `verify_freshness`; existing
  screenshot/trace hooks unchanged.

**Post-design re-check**: All gates still PASS once constitution templates
and Principle I / VII text are updated in the same feature. No Complexity
Tracking rows.

## Project Structure

### Documentation (this feature)

```text
specs/003-dashboard-freshness/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── freshness-api.md
└── tasks.md             # Phase 2 — /speckit-tasks (not this command)
```

### Source Code (repository root)

```text
core/portal/page.py                         # add verify_freshness
pages/fleet_dashboard/main_dashboard_page.py  # inherit only; no override
tests/ui/fleet_dashboard/test_dashboard_smoke.py  # add one sanity test
.specify/memory/constitution.md             # Principles I + VII, v1.2.0
.specify/templates/plan-template.md         # Layer 0 last-refresh in gates
.specify/templates/spec-template.md         # AC last-refresh chrome
.specify/templates/tasks-template.md        # Layer 0 scope includes freshness
conftest.py                                 # unchanged
db/                                         # out of scope
core/components/slicer.py                   # unchanged
```

**Structure Decision**: Validation Core layout. Add the method on the
existing `ReportShell`. Do not invent a Layer 2 freshness component or a
fleet-page wrapper.

## Complexity Tracking

> No constitution violations after the v1.2.0 amendment in this feature.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Implementation Approach: Additive method

This is not a Strangler Fig extraction. Sequence:

1. Amend Constitution Principles I and VII (and matching templates) so
   Layer 0 may verify generic last-refresh chrome.
2. Implement `verify_freshness` on `ReportShell`.
3. Add the fleet smoke test that calls it.
4. Leakage audit of `core/`.
5. Run `pytest tests/ui/fleet_dashboard/` (100% green when the report is
   actually fresh).

## Risk notes

- Caption date format may vary by Power BI locale. Parse a short list of
  common patterns; fail with the captured text if none match.
- `_dashboard_iframe()` returns a Playwright `Locator`, not a
  `FrameLocator`. Use `content_frame` or `page.frame_locator("main iframe")`
  to read iframe text (see research.md).
- A genuinely stale report is a correct fail of the new test, not a
  framework bug.
