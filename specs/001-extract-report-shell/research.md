# Research: Extract Generic ReportShell

**Feature**: `001-extract-report-shell` | **Date**: 2026-08-23

All Technical Context items were known from the repo and Constitution v1.0.0.
No `NEEDS CLARIFICATION` markers remain.

## Decision: Inheritance, not composition

- **Decision**: `BasePage` → `ReportShell` → `MainDashboardPage`.
- **Rationale**: Spec FR-002 / AC-005. The `dashboard` fixture and
  `conftest.py` treat one object as the page (`navigate`, `_dashboard_ready`,
  `_recover_from_portal_glitch`). Composition would force a facade or fixture
  rewrite, which the spec forbids.
- **Alternatives considered**: `MainDashboardPage` holds a `ReportShell`
  instance — rejected (two objects, fixture churn). Mixin-only portal module
  — rejected (weaker Layer 0 boundary, easier leakage).

## Decision: Strangler Fig, not a single move

- **Decision**: Empty inherit → in-place hooks → leaf methods → catalog →
  auth → `navigate` / reload. Gate with smoke after each major step.
- **Rationale**: User request and Constitution III. A one-shot cut of
  `navigate` plus 15 helpers is hard to bisect when SSO or iframe timing
  breaks. Fowler's Strangler Fig keeps the old page runnable while the new
  shell grows around it.
- **Alternatives considered**: Copy-paste entire `navigate` into `core/`
  first — rejected (would drag `total_vehicles_kpi` into Layer 0).
  Duplicate methods then switch calls — rejected (two sources of truth).

## Decision: Keep `_dashboard_ready` as the ready-check name

- **Decision**: Shell implements `_dashboard_ready` as iframe +
  `_report_ready_locator()`. `_report_ready` may alias it.
- **Rationale**: `conftest.py` calls `_dashboard_ready()` and must not be
  edited. Spec FR-007 allows "or its shell equivalent"; keeping the name
  satisfies the test-contract without fixture edits.
- **Alternatives considered**: Rename to `_report_ready` only — rejected
  unless `conftest` is updated (out of scope).

## Decision: Thin Allure wrappers on the fleet page

- **Decision**: Shell `navigate` / reload use generic step text or no
  fleet-specific Allure title. Fleet may override only to apply
  `@allure.step("Navigate to Fleet Dashboard")` and call `super()`.
- **Rationale**: Spec FR-013 and US3. Layer 0 must not say "Fleet".
  Existing Allure catalog (`FEATURE_UI_SMOKE`) still sees the fleet title
  if the wrapper exists.
- **Alternatives considered**: Generic "Navigate to report" only —
  acceptable if Allure grouping still works; prefer wrapper to minimize
  report-title drift.

## Decision: Settings are configuration, not domain leakage

- **Decision**: `DASHBOARD_URL`, `DASHBOARD_SEARCH_TERM`,
  `PORTAL_CATALOG_URL`, `PORTAL_ALL_PRODUCTS_LABEL`, `LOGIN_URL`,
  `AUTH_FILE`, timeouts stay in `config.settings` and may be read from
  `ReportShell`.
- **Rationale**: Constitution II. A second report would change env values,
  not Layer 0 code.
- **Alternatives considered**: Constructor-injected URL/term only —
  unnecessary for v1; settings already exist.

## Decision: No new automated tests in this feature

- **Decision**: Existing smoke + e2e are the contract. Optional static
  leakage grep in Step 8. Do not add a second report page "for tests".
- **Rationale**: Spec FR-005 / SC-001. A fake second report would invent
  product surface the constitution says not to genericize yet.
- **Alternatives considered**: Unit-test `ReportShell` with a fake page —
  useful later, not required to close this feature.

## Decision: Package layout `core.portal`

- **Decision**: `core/portal/page.py` + `core/portal/__init__.py`.
  Import: `from core.portal.page import ReportShell`.
- **Rationale**: Constitution architecture path. Matches Validation Core
  tree already documented in README.
- **Alternatives considered**: `pages/portal/report_shell.py` — rejected
  (would keep Layer 0 inside the domain `pages/` tree). `core/page.py` —
  rejected (no portal namespace for later helpers).

## Decision: Recovery may call auth across steps 4–6

- **Decision**: `_recover_from_portal_glitch` may call
  `_ensure_authenticated`. During Strangler Steps 4–5 that call may still
  resolve on the fleet subclass. By Step 6 both live on the shell.
  Never import `MainDashboardPage` from `core/`.
- **Rationale**: Current code already has this call cycle on one class.
  Inheritance preserves it without a circular package import.
- **Alternatives considered**: Inline recovery without re-auth — would
  change behavior (forbidden).

## Decision: Binding test path

- **Decision**: Gate is `tests/ui/fleet_dashboard/`. `tests/e2e/fleet/`
  does not exist. `tests/e2e/` is the regression suite that must remain
  green if executed; it is not edited.
- **Rationale**: Spec FR-005, repo layout, `pytest.ini` `testpaths = tests`.
