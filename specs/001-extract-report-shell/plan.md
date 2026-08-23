# Implementation Plan: Extract Generic ReportShell

**Branch**: `001-extract-report-shell` | **Date**: 2026-08-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-extract-report-shell/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by
`/speckit-tasks` (not this command). The Strangler Fig sequence below is the
implementation order that tasks MUST follow.

## Summary

Extract portal login/SSO, catalog search, iframe wait, and visual-load timeout
from `MainDashboardPage` into Layer 0 `ReportShell` (`core/portal/page.py`).
The fleet page inherits the shell and supplies `_report_ready_locator` plus
`after_navigate`. Public `navigate(*, force_reload=False)` stays unchanged.
Tests are not rewritten.

Technical approach: **Strangler Fig**. Introduce an empty inheriting shell,
rewire ready-state to hooks *in place*, then move leaf methods before
orchestrators. After every major step the suite stays importable and
`pytest tests/ui/fleet_dashboard/` remains the gate. Do not big-bang move
`navigate` on day one.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, allure-pytest,
python-dotenv. Existing helpers: `browser_session`, `config.settings`,
`pages.errors.LoadTimeoutError`, `reports.test_run_report`.

**Storage**: N/A for this feature. Existing `auth_state.json` session file
is unchanged. No warehouse schema changes.

**Testing**: `pytest` + Playwright Chromium. Binding gate:
`pytest tests/ui/fleet_dashboard/` (markers `sanity`). Regression callers in
`tests/e2e/` must stay green. No new test files required; do not edit
existing test modules or `conftest.py` (it already calls `_dashboard_ready`,
`navigate`, `_recover_from_portal_glitch`).

**Target Platform**: Windows workstation + Chromium, organizational Agamim
portal + Microsoft SSO (same as today).

**Project Type**: Internal validation framework (pytest page objects), not
a shipped web service.

**Performance Goals**: Preserve existing load SLA
(`settings.DASHBOARD_LOAD_SLA_MS`, default 5s) measured by
`reload_and_measure_ready_ms()`.

**Constraints**: Constitution v1.0.0 — zero domain leakage in `core/`;
unchanged `navigate` / `reload_and_measure_ready_ms` contracts; extract
shared portal steps only; keep Allure steps and CSV UI logs.

**Scale/Scope**: One domain page (`pages/fleet_dashboard/main_dashboard_page.py`,
~2400 lines). Move ~15 portal methods + split 3 orchestrators. Fleet KPI,
filter, table, and chart code stays put.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: PASS — `ReportShell` in `core/portal/page.py`;
  `MainDashboardPage` inherits it (`BasePage` → `ReportShell` → fleet page).
- **Zero domain leakage**: PASS — ready visual is `_report_ready_locator` on
  the fleet page; `core/` forbids vehicles, district, KPI/chart titles.
- **Test contract**: PASS — `pytest tests/ui/fleet_dashboard/` at 100% after
  each major Strangler step and at completion; no test-file edits.
- **Extract shared only**: PASS — filters, KPIs, charts, tables, drilldown
  stay on the fleet page.
- **Warehouse truth**: PASS — `db/` untouched; no SQL in Layer 0.
- **Observability**: PASS — fleet may wrap `navigate` with the existing
  Allure title; CSV `log_ui` lines stay; traces/screenshots unchanged.

**Post-design re-check**: All gates still PASS. No Complexity Tracking rows.

## Project Structure

### Documentation (this feature)

```text
specs/001-extract-report-shell/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   └── report-shell-api.md
└── tasks.md             # Phase 2 — /speckit-tasks (not this command)
```

### Source Code (repository root)

```text
core/
└── portal/
    ├── __init__.py
    └── page.py                 # ReportShell (Layer 0)
pages/
├── base_page.py                # unchanged timeout/retry foundation
├── errors.py                   # LoadTimeoutError reused
└── fleet_dashboard/
    └── main_dashboard_page.py  # inherits ReportShell; domain visuals
browser_session.py              # unchanged SSO popup helpers
config/settings.py              # URLs, search term, timeouts (config, not domain)
conftest.py                     # unchanged dashboard fixture
tests/ui/fleet_dashboard/       # smoke gate — do not edit
tests/e2e/                      # regression callers — do not edit
db/                             # out of scope
```

**Structure Decision**: Validation Core layout. Add only `core/portal/`.
Do not invent `src/`, backend/frontend, or a second page-object tree.

## Complexity Tracking

> No constitution violations. Table left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Implementation Approach: Strangler Fig

Each step MUST leave the project importable. After every **major** step
(marked GATE), run `pytest tests/ui/fleet_dashboard/` (or a cheaper smoke
subset if a full portal run is blocked) and fix before continuing. Do not
skip ahead to moving `navigate` while `_dashboard_ready` still hardcodes
`total_vehicles_kpi` inside code that will live in `core/`.

### Step 0 — Baseline (GATE)

- Record current smoke result. Do not change behavior.
- Confirm callers: `conftest.dashboard` → `MainDashboardPage.navigate`,
  `_dashboard_ready`, `_recover_from_portal_glitch`,
  `_is_portal_profile_error`.

### Step 1 — Empty shell + inherit (GATE)

- Add `core/portal/__init__.py` and `core/portal/page.py`.
- `class ReportShell(BasePage)` with:
  - `_report_ready_locator(self)` raising `NotImplementedError`
  - `after_navigate(self)` no-op
  - optional `_report_ready(self)` not yet used
- Change `MainDashboardPage(BasePage)` → `MainDashboardPage(ReportShell)`.
- Override `_report_ready_locator` to return `self.total_vehicles_kpi`
  (locator only; no logic move yet).
- **Do not move methods.** Tests pass because all behavior still sits on
  the subclass.

### Step 2 — Hook the monolith in place (GATE)

Still on `MainDashboardPage`:

- `_dashboard_ready` uses iframe + `self._report_ready_locator()` instead of
  `self.total_vehicles_kpi` by name.
- `navigate` ready-wait and `reload_and_measure_ready_ms` use the same hook.
- Replace `self.reset_dashboard_filters()` call sites inside `navigate`
  with `self.after_navigate()`.
- Implement `after_navigate` on the fleet page as
  `self.reset_dashboard_filters()`.
- **Do not move files yet.** Behavior is identical; coupling is now
  hook-shaped. Tests pass.

### Step 3 — Move leaf locators and predicates (GATE)

Move these verbatim to `ReportShell` (no fleet names). Delete the fleet
copies so one implementation remains:

- `_portal_search_box`
- `_all_products_control`
- `_dashboard_iframe`
- `_click_even_if_hidden`
- `_is_portal_home`
- `_hitachbrut_button`
- `_is_login_page`
- `_page_debug_summary`
- `_is_portal_profile_error`

Fleet keeps inheriting them. `conftest` still works. Tests pass.

### Step 4 — Move recovery and iframe wait (GATE)

Move `_recover_from_portal_glitch` and `_wait_for_dashboard_iframe`.
If recovery calls `_ensure_authenticated`, either keep a temporary
forward on the fleet page or move auth in the same step as Step 6 —
prefer leaving a `_ensure_authenticated` call that still resolves on
the subclass until Step 6. Tests pass.

### Step 5 — Move catalog open/search (GATE)

Move `_open_all_products_catalog` and `_open_dashboard_via_portal_search`.
Rewrite comments that mention the fleet product name; use
`settings.DASHBOARD_SEARCH_TERM` only. Tests pass.

### Step 6 — Move auth (GATE)

Move `_auto_click_hitachbrut` and `_ensure_authenticated`.
They MUST call hook-based `_dashboard_ready` / `_report_ready`, never
`total_vehicles_kpi`. Tests pass.

### Step 7 — Move orchestrators (GATE)

- Implement `_dashboard_ready` / `_report_ready` on `ReportShell` as
  iframe + `_report_ready_locator()`.
- Move `navigate` and `reload_and_measure_ready_ms` to `ReportShell`.
- `navigate` calls `after_navigate()` after reuse and after cold load.
- Allure: keep fleet title via a thin `MainDashboardPage.navigate` wrapper
  that only adds `@allure.step("Navigate to Fleet Dashboard")` and calls
  `super().navigate(...)`. Same optional wrapper for reload timing if the
  current step text stays fleet-specific.
- Delete remaining portal method bodies from the fleet page.
- Signature stays `navigate(self, *, force_reload: bool = False) -> None`.

### Step 8 — Leakage audit

Search `core/` for: vehicles, district, subunit, fleet KPI titles, chart
titles, `total_vehicles`, `reset_dashboard_filters`. Must be zero.
Generic words (dashboard, iframe, portal, catalog) are allowed.
Settings keys are allowed.

### Step 9 — Final gate

- `pytest tests/ui/fleet_dashboard/` MUST be 100% green.
- Do not edit test files. If e2e is run, `tests/e2e/` stays green.
- `conftest.py` unchanged.

## Risk notes

- `conftest.py` depends on `_dashboard_ready` by name — keep that name on
  the shell (or an alias) so fixtures need no edits.
- Moving `_recover_from_portal_glitch` before auth can create a temporary
  cross-layer call; resolve by Step 6, never by importing the fleet page
  from `core/`.
- Do not genericize slicers, KPIs, or charts in this feature.
