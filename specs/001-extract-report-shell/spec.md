# Feature Specification: Extract Generic ReportShell

**Feature Branch**: `001-extract-report-shell`

**Created**: 2026-08-23

**Status**: Draft

**Audience**: Validation and BI leads own the user scenarios. The extraction
inventory and hook contract in Requirements / Architectural Constraints are
normative for this platform refactor (Constitution v1.0.0 and the feature
request). They are not optional design notes.

**Input**: User description: "Extract generic ReportShell (Layer 0) from MainDashboardPage into core/portal/page.py: move portal navigation, SSO, and iframe loading; hook-based report-ready; inherit or compose; fleet UI tests stay 100% green with unchanged navigate() signature."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same fleet open-and-ready path after extraction (Priority: P1)

A Validation engineer runs the existing fleet load and visibility checks. They still open the fleet report through the same public `navigate` entry point (including `force_reload`). The portal signs them in if needed, finds the report in the catalog when a direct URL is not enough, waits until the report frame and the fleet-ready visual are present, and leaves filters in the same baseline state as today. No test file is rewritten to learn a new open sequence.

**Why this priority**: If opening the fleet report changes for callers, the extraction has failed regardless of how clean the layering looks. This is the MVP.

**Independent Test**: Run the fleet smoke suite (`tests/ui/fleet_dashboard/`) against the refactored page object. All tests MUST pass. Callers still invoke `navigate(*, force_reload=False)`.

**Acceptance Scenarios**:

1. **Given** a valid saved portal session and the fleet report already open, **When** a test calls `navigate()` without `force_reload`, **Then** the open report is reused, filters are reset to baseline, and no full portal re-login is required.
2. **Given** a valid session and a cold start (or `force_reload=True`), **When** a test calls `navigate()`, **Then** the report frame appears and the fleet-ready visual becomes visible within the existing timeout budget.
3. **Given** the session has expired or the landing page shows login, **When** `navigate()` runs, **Then** a single SSO attempt (and manual completion when configured) authenticates, then the same catalog/frame/ready path completes.
4. **Given** the public `navigate` signature `navigate(self, *, force_reload: bool = False) -> None`, **When** the extraction is complete, **Then** that signature is unchanged and existing callers compile and run without edits.

---

### User Story 2 - Report-ready comes from the domain page, not the shell (Priority: P1)

The generic shell can tell that *a* report has loaded only because the fleet page tells it which visual means "ready". The shell does not know about fleet KPI titles, vehicle counts, or district slicers. A second report could later supply a different ready visual without changing portal login or catalog search.

**Why this priority**: Zero domain leakage is a non-negotiable constitution rule. Shipping a "generic" shell that still waits on the fleet total-vehicles KPI would block every future report.

**Independent Test**: Inspect Layer 0 for fleet-specific labels (vehicles, district, fleet KPI/chart titles). Confirm the fleet page supplies the ready visual via a hook. Confirm `reload_and_measure_ready_ms()` still measures until that same ready visual is visible.

**Acceptance Scenarios**:

1. **Given** `ReportShell` has no fleet-ready locator of its own, **When** `MainDashboardPage` overrides `_report_ready_locator`, **Then** `navigate` and reload-timing wait on that locator (today: the fleet total KPI card) and not on a hardcoded shell visual.
2. **Given** Layer 0 source, **When** a reviewer searches for vehicles, district, subunit, fleet KPI titles, or fleet chart titles, **Then** there are zero matches.
3. **Given** a future report page that overrides `_report_ready_locator` with a different visual, **When** it reuses `ReportShell` navigation, **Then** it does not inherit fleet KPI or slicer names.

---

### User Story 3 - Fleet page is a report on top of the shell (Priority: P2)

The fleet page stops owning login, catalog search, iframe wait, and visual-load timeout. It becomes a domain report: KPIs, filters, tabs, table, charts. Engineers adding a new Power BI report copy the fleet *pattern* (inherit the shell, override the ready hook) instead of copying hundreds of lines of portal code.

**Why this priority**: This is the maintainability outcome. It can be verified after P1 still passes.

**Independent Test**: Confirm `MainDashboardPage` inherits `ReportShell` and no longer defines the moved portal methods. Confirm fleet filter/KPI/chart methods remain on the fleet page. Confirm Allure/CSV navigation evidence still appears.

**Acceptance Scenarios**:

1. **Given** the type hierarchy `BasePage` → `ReportShell` → `MainDashboardPage`, **When** a test constructs `MainDashboardPage(page)`, **Then** `navigate`, `reload_and_measure_ready_ms`, and portal helpers resolve from the shell (or a thin fleet override that only supplies ready-state and post-navigate reset).
2. **Given** the extraction is done, **When** a tester applies district or vehicle filters, **Then** those behaviors still live only on the fleet page and still work as today.
3. **Given** a successful `navigate`, **When** the run report and Allure output are inspected, **Then** navigation/auth evidence is still recorded (step and CSV UI line).

---

### Edge Cases

- Session expired mid-run: one automatic SSO click, then the existing manual-login pause when configured; no click-loop on the landing page.
- Transient portal profile/user-fetch error: recover by reload and retry catalog open, as today.
- Catalog search box missing: fall back to the configured catalog control, then the catalog URL; fail with a debug summary if the search box never appears.
- Direct report URL already shows the frame: skip catalog search.
- Report frame visible but the domain ready visual not yet hydrated: keep polling until timeout, then fail with the existing load-timeout error.
- `force_reload=False` while the report is already ready: reuse the tab and run the domain post-navigate reset only.
- Headless / non-manual login still stuck on the login page after one click: fail with the existing assertion (do not invent a new auth product).
- `reload_and_measure_ready_ms` used by the load-SLA smoke test: must keep returning elapsed milliseconds until the domain ready visual is visible, using the same hook as `navigate`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST introduce a generic `ReportShell` in `core/portal/page.py` that owns portal login/SSO, catalog search, iframe waiting, and visual-loading timeouts.
- **FR-002**: `MainDashboardPage` MUST inherit `ReportShell` (which inherits `BasePage`). Composition is not used for this extraction so the existing `dashboard` fixture and `self.page` / `self.timeout` surface stay on one object.
- **FR-003**: The public signature `navigate(self, *, force_reload: bool = False) -> None` MUST remain unchanged. Tests MUST NOT be edited to adopt a new open API.
- **FR-004**: `reload_and_measure_ready_ms(self) -> int` MUST remain callable on the fleet page object with the same meaning (elapsed ms until the report is interactively ready).
- **FR-005**: After extraction, `pytest tests/ui/fleet_dashboard/` MUST pass at 100%. Existing `tests/e2e/` tests that use `MainDashboardPage` / the `dashboard` fixture MUST also remain green without test rewrites. There is no `tests/e2e/fleet/` path; the relevant UI smoke path is `tests/ui/fleet_dashboard/`.
- **FR-006**: `ReportShell` MUST wait for report-ready only through a domain hook. The fleet page MUST override `_report_ready_locator` to return the visual that means "this report is loaded" (fleet: the total KPI card). The shell MUST NOT reference that card by fleet title or attribute name.
- **FR-007**: `_dashboard_ready` (or its shell equivalent) MUST mean: iframe visible AND `_report_ready_locator` visible. Auth and reuse paths that today call `_dashboard_ready` MUST use this hook-based check.
- **FR-008**: After a successful navigate (including reuse of an already-open report), the fleet page MUST still reset filters to baseline. That reset MUST run from a domain hook (`after_navigate`) or a fleet override — not from generic shell knowledge of fleet slicers.
- **FR-009**: Layer 0 MUST NOT contain vehicles, district, subunit, fleet KPI titles, fleet chart titles, or fleet slicer display names. Settings keys for URL, catalog label, and search term are allowed.
- **FR-010**: The following methods MUST move to `ReportShell` as generic portal behavior (names preserved unless a hook split is required):
  - `_portal_search_box`
  - `_all_products_control`
  - `_dashboard_iframe`
  - `_click_even_if_hidden`
  - `_is_portal_home`
  - `_hitachbrut_button`
  - `_is_login_page`
  - `_page_debug_summary`
  - `_is_portal_profile_error`
  - `_recover_from_portal_glitch`
  - `_wait_for_dashboard_iframe`
  - `_auto_click_hitachbrut`
  - `_open_all_products_catalog`
  - `_open_dashboard_via_portal_search`
  - `_ensure_authenticated`
- **FR-011**: The following methods MUST be split, not moved verbatim:
  - `_dashboard_ready` — shell: iframe + hook; fleet: provides `_report_ready_locator`
  - `navigate` — shell: goto, auth, catalog, iframe, wait on hook; fleet: `after_navigate` (filter reset) and Allure wording that may stay fleet-specific on the subclass
  - `reload_and_measure_ready_ms` — shell: reload, iframe poll, timeout; fleet: same `_report_ready_locator`
- **FR-012**: Fleet-only behavior MUST stay on `MainDashboardPage`: KPI maps and reads, tabs, district/sub-unit/source/category slicers, vehicle table and search, charts, tooltips, drilldown, and warehouse-facing helpers.
- **FR-013**: Navigation and authentication MUST keep Allure step coverage and CSV UI log lines equivalent to today. Failures MUST still produce screenshot and trace attachments.
- **FR-014**: `ReportShell` MUST NOT embed warehouse SQL or fleet business invariants.

### Key Entities

- **ReportShell**: Generic portal host (Layer 0). Knows login, catalog, report frame, and timeouts. Does not know any one dashboard's visuals.
- **Domain report page**: Fleet `MainDashboardPage` today. Owns report-specific visuals and overrides the ready hook.
- **Ready-state hook**: `_report_ready_locator` supplied by the domain page so the shell can wait without hardcoding a KPI.
- **Post-navigate hook**: `after_navigate` supplied by the domain page for baseline filter reset and any report-specific cleanup.
- **Portal session**: Existing saved browser storage used to skip login when still valid.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. It MUST NOT contain vehicles, district, fleet KPI/chart titles, or other report-specific labels.
- **AC-002**: `MainDashboardPage` MUST inherit `ReportShell` rather than re-implement login, catalog search, iframe wait, or visual-load timeout.
- **AC-003**: Report-ready state MUST be supplied by `MainDashboardPage._report_ready_locator` (and optionally `_report_ready()` that uses it). `ReportShell` MUST NOT hardcode a fleet visual.
- **AC-004**: Public test-facing APIs `navigate(*, force_reload=False)` and `reload_and_measure_ready_ms()` MUST keep their contracts. Tests are not updated in this change.
- **AC-005**: Inheritance chain MUST be `BasePage` → `ReportShell` → `MainDashboardPage`. `ReportShell` lives in `core/portal/page.py`.
- **AC-006**: Extract shared portal steps only. Do not genericize fleet filters, KPIs, charts, tables, or drilldown.

### Hook strategy (normative)

```text
ReportShell
  _report_ready_locator()     # abstract/required override — domain visual
  _report_ready()             # iframe + locator visible (used by auth/reuse)
  after_navigate()            # default no-op; fleet resets filters
  navigate(...)               # unchanged public signature
  reload_and_measure_ready_ms()

MainDashboardPage(ReportShell)
  _report_ready_locator()  → fleet total KPI card locator
  after_navigate()         → reset_dashboard_filters()
```

`_auto_click_hitachbrut` and `_ensure_authenticated` MUST call the hook-based ready check, not a fleet KPI attribute.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of existing fleet load and visibility checks pass after the
  extraction. Those check files are not edited. Binding suite:
  `tests/ui/fleet_dashboard/` (see FR-005).
- **SC-002**: 100% of existing warehouse-backed fleet checks that open the
  report through the shared dashboard entry pass without editing those files.
- **SC-003**: Testers still open a report through the same `navigate` entry
  they use today, including the optional force-reload flag, with no new
  required inputs and the same empty return.
- **SC-004**: A reviewer finds zero fleet business terms in Layer 0
  (vehicles, district, subunit, fleet KPI or chart titles).
- **SC-005**: The existing load-budget check still measures time until the
  report is interactively ready and still compares that time to the
  configured budget.
- **SC-006**: A second report can reuse sign-in, catalog search, and frame
  wait by supplying only its own ready signal and post-open cleanup — without
  copying fleet filter or KPI behavior.

## Assumptions

- The current portal SSO, catalog, and iframe flow in `MainDashboardPage` is the correct behavior to preserve; this feature relocates it, it does not redesign auth.
- Inheritance is the required integration style so the `dashboard` fixture keeps returning a single page object.
- The fleet-ready visual remains the total KPI card; only the *ownership* of that locator moves to the hook on `MainDashboardPage`.
- `tests/e2e/fleet/` does not exist; the binding UI suite is `tests/ui/fleet_dashboard/`, with `tests/e2e/` as the regression suite that must also stay green.
- No second production report is in scope; only the reuse *shape* must be possible.
- Settings-driven URLs, catalog label, and search term stay configuration, not domain leakage.
- Implementation code is out of scope for this specification; `/speckit-plan` and `/speckit-tasks` follow.
