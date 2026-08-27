# Feature Specification: Horizontal Scaling — Layer 0 Smoke for New Dashboards

**Feature Branch**: `004-horizontal-scaling`

**Created**: 2026-08-27

**Status**: Draft

**Audience**: Validation engineers own the user scenarios. The Layer 0 reuse
shape, per-report ready visuals, catalog search terms, popup handling, and
smoke-test contract in Requirements / Architectural Constraints are
normative for this platform capability (Constitution v1.2.0). They are not
optional design notes.

**Input**: User description: "Add basic Layer 0 smoke tests (freshness check)
for two new dashboards: 'Power Outages' and 'Credit Consumption'. Handle
dashboard-specific popups gracefully. Create `tests/ui/power_outages_dashboard/`
and `tests/ui/credit_consumption_dashboard/` with page objects inheriting
`ReportShell`, report-ready locators, local `dashboard` fixtures, and
`test_dashboard_updated_within_24_hours` calling `verify_freshness()`. Credit
Consumption shows an info-page popup that must be closed before the main
report can settle. No JSON catalogs and no slicer/business logic yet."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Power Outages Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Power Outages smoke suite. The suite
opens that report through the shared portal shell (catalog search for the
Power Outages product), waits until a Power Outages–specific ready visual is
visible, and confirms the report's last-refresh caption is within 24 hours.
The test body stays thin: it uses a local `dashboard` fixture and calls the
inherited freshness check. It does not locate iframe text, parse dates, or
apply filters.

**Why this priority**: This is the first second-report binding of Layer 0.
It proves a new dashboard can reuse login, catalog search, iframe wait, and
freshness without copying portal logic. This is the MVP.

**Independent Test**: Run the Power Outages smoke suite alone. The suite
opens the Power Outages report (not the fleet report), waits for the
alerted-population ready visual, and passes `verify_freshness()` when that
report's last-refresh caption is within 24 hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Power Outages
   smoke suite starts, **Then** the local dashboard fixture opens the Power
   Outages report via catalog search for `תמונת מצב הפסקות חשמל` and waits
   until the ready visual `אוכלוסייה מותרעת` is visible.
2. **Given** the Power Outages report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24
   hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test
   runs, **Then** it fails (stale data is correctly flagged).
4. **Given** the Power Outages page object, **When** a reviewer inspects it,
   **Then** it inherits `ReportShell`, supplies only a search term and a
   ready locator, and contains no slicer, KPI, chart, or JSON catalog logic.
5. **Given** the smoke test body, **When** a reviewer inspects it, **Then**
   it contains no iframe locators, date parsing, or CSS — only the
   page-object freshness call.

---

### User Story 2 - Credit Consumption Layer 0 freshness smoke with popup dismiss (Priority: P1)

A Validation engineer runs a dedicated Credit Consumption smoke suite. That
report shows an info-page popup that covers the main view after open. The
page object dismisses the popup (close / X) before waiting for the main
dashboard to settle, then confirms last-refresh is within 24 hours. The
test body stays as thin as Power Outages.

**Why this priority**: Without popup handling, Layer 0 ready-wait never sees
the main report and freshness cannot run. This is the second independent
report binding and the popup-gracefulness requirement.

**Independent Test**: Run the Credit Consumption smoke suite alone. The
suite opens the Credit Consumption report, closes the info popup if it
appears, waits for the authorities-population ready visual, and passes
`verify_freshness()` when that report is fresh.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Credit
   Consumption smoke suite starts, **Then** the local dashboard fixture
   opens the Credit Consumption report via catalog search for `צריכת אשראי`.
2. **Given** the report has opened and an info-page popup is visible,
   **When** navigation continues, **Then** the page object clicks the popup
   close (X) control so the main report is no longer blocked.
3. **Given** the popup is absent (already dismissed or not shown), **When**
   navigation continues, **Then** the suite does not fail on a missing
   close button; it proceeds to the ready visual.
4. **Given** the popup is dismissed, **When** the page waits for ready,
   **Then** the ready visual `כמות אוכלוסיה ברשויות` becomes visible.
5. **Given** the Credit Consumption report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24
   hours.
6. **Given** the Credit Consumption page object, **When** a reviewer
   inspects it, **Then** it inherits `ReportShell`, supplies search term,
   ready locator, and popup dismiss only — no slicer, KPI, chart, or JSON
   catalog logic.

---

### Edge Cases

- Fleet report already open on the shared browser tab — the new suite MUST
  still switch to its own report via catalog search (ready visual of the
  other report MUST NOT be treated as success).
- Info popup appears after the iframe is visible but before the ready
  visual — dismiss MUST run before the ready wait, not only after navigate
  completes.
- Info popup close control is slow to attach — wait briefly, then click;
  do not burn the full default timeout if the popup never appears.
- Multiple close-like controls — click a visible popup close (X / Close /
  סגור) that dismisses the blocking overlay; do not click unrelated report
  chrome.
- Popup reappears after a first dismiss — a second dismiss attempt during
  ready-wait is allowed; do not loop indefinitely.
- Catalog search returns several products — open the result matching the
  report's search term.
- Live report last-refresh older than 24 hours — correct fail of the
  freshness test, not a framework bug.
- Shared session auth already valid — reuse it; do not force a new login.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The framework MUST add a Power Outages Layer 0 page that
  inherits `ReportShell`, sets catalog search term
  `תמונת מצב הפסקות חשמל`, and treats `אוכלוסייה מותרעת` as the
  report-ready visual.
- **FR-002**: The framework MUST add a Credit Consumption Layer 0 page that
  inherits `ReportShell`, sets catalog search term `צריכת אשראי`, and
  treats `כמות אוכלוסיה ברשויות` as the report-ready visual.
- **FR-003**: Each new report MUST have its own smoke package with a
  `dashboard` fixture that returns that report's page object and a sanity
  test `test_dashboard_updated_within_24_hours(dashboard)` that calls
  `dashboard.verify_freshness()`.
- **FR-004**: Catalog search MUST use the page's own search term, not the
  fleet default `שליטה בניוד`, so two reports can share Layer 0 without
  editing `.env` between suites.
- **FR-005**: Credit Consumption MUST dismiss the blocking info-page popup
  (click its close / X control) before waiting for the main ready visual.
  Dismiss MUST be safe when the popup is absent.
- **FR-006**: Neither new page MAY add JSON filter catalogs, generic slicer
  wiring, KPI/chart/table methods, or other business logic. Scope is Layer
  0 readiness plus inherited freshness only.
- **FR-007**: Root fleet `dashboard` fixture and existing
  `tests/ui/fleet_dashboard/` tests MUST keep their contracts. New suites
  MUST override `dashboard` locally so fleet tests still receive the fleet
  page.
- **FR-008**: `core/` MUST remain free of Power Outages and Credit
  Consumption labels, ready-visual text, popup copy, and catalog product
  names. Those strings belong on the domain page objects.
- **FR-009**: New pages MUST reuse `ReportShell` login, catalog, iframe
  wait, visual-load timeout, and `verify_freshness`. They MUST NOT copy
  those implementations.
- **FR-010**: Allure MUST keep existing screenshot/trace failure hooks.
  Smoke tests MUST be marked sanity like other Layer 0 smoke checks.
- **FR-011**: `pytest tests/ui/power_outages_dashboard/` and
  `pytest tests/ui/credit_consumption_dashboard/` MUST be independently
  runnable. A stale live caption is a correct fail of freshness.

### Key Entities

- **Power Outages report**: Portal catalog product searched as
  `תמונת מצב הפסקות חשמל`. Ready when `אוכלוסייה מותרעת` is visible.
- **Credit Consumption report**: Portal catalog product searched as
  `צריכת אשראי`. Ready when `כמות אוכלוסיה ברשויות` is visible after any
  info-page popup is dismissed.
- **Info-page popup**: Credit Consumption overlay that blocks the main
  report until the tester (or page object) closes it via X / close.
- **Per-report search term**: Catalog query owned by the domain page so
  Layer 0 can open the correct product without a global setting change.
- **Layer 0 smoke package**: Directory with page object, local
  `dashboard` fixture, and one freshness smoke test. No filter JSON.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. It MAY
  read a page-owned catalog search term (class/instance attribute) with
  fallback to the existing settings default. It MUST NOT hardcode Power
  Outages or Credit Consumption names, ready visuals, or popup copy.
- **AC-002**: Domain page objects MUST inherit `ReportShell`. Power
  Outages and Credit Consumption pages live under
  `tests/ui/power_outages_dashboard/` and
  `tests/ui/credit_consumption_dashboard/` for this Layer 0-only slice
  (no `pages/<report>/` domain module until business logic exists).
- **AC-003**: Report-ready state MUST be supplied by each domain page
  locator. Ready text MUST NOT be hardcoded in `ReportShell`.
- **AC-004**: Public fleet APIs (`navigate`,
  `reload_and_measure_ready_ms`, root `dashboard` fixture, fleet smoke)
  MUST keep their contracts. Additive Layer 0 change is limited to using
  a per-page search term when present.
- **AC-005**: Layer 2 (`core/components/`) MUST NOT be used by these new
  pages. No `data/*.json` catalogs for the new reports.
- **AC-006**: Popup handling is domain behavior on
  `CreditConsumptionPage` (override `navigate` / `after_navigate` and/or
  dismiss before ready-wait). Do not put Credit Consumption popup
  locators in `core/`.
- **AC-007**: Each suite's `dashboard` fixture MUST be defined next to
  that suite so pytest fixture shadowing keeps fleet tests on
  `MainDashboardPage`.

### Integration shape (normative)

```text
ReportShell (Layer 0)
  catalog search term = page.DASHBOARD_SEARCH_TERM or settings default
  verify_freshness() inherited

PowerOutagesPage(ReportShell)
  DASHBOARD_SEARCH_TERM = "תמונת מצב הפסקות חשמל"
  ready = "אוכלוסייה מותרעת"

CreditConsumptionPage(ReportShell)
  DASHBOARD_SEARCH_TERM = "צריכת אשראי"
  dismiss info-page popup (X) before ready wait
  ready = "כמות אוכלוסיה ברשויות"

tests/ui/<report>/conftest.py
  dashboard fixture → that page, navigate()

tests/ui/<report>/test_dashboard_smoke.py
  test_dashboard_updated_within_24_hours(dashboard)
    → dashboard.verify_freshness()
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tester can confirm Power Outages last-refresh freshness
  with a single page-object call after the suite opens that report.
- **SC-002**: A tester can confirm Credit Consumption last-refresh
  freshness with a single page-object call after the suite opens that
  report and dismisses a blocking info popup when present.
- **SC-003**: 100% of existing fleet smoke checks still pass; fleet tests
  still receive the fleet dashboard fixture.
- **SC-004**: Each new suite is independently runnable and contains
  exactly one Layer 0 freshness smoke test (no slicer/KPI/chart cases).
- **SC-005**: A reviewer finds zero Power Outages or Credit Consumption
  product names, ready-visual strings, or popup copy under `core/`.
- **SC-006**: When the info popup is missing, Credit Consumption
  navigation still reaches the ready visual (no hard fail on absent X).
- **SC-007**: When last-refresh is older than 24 hours, the new smoke
  checks fail 100% of the time (stale data is never silently accepted).

## Assumptions

- Both products exist in the same Agamim portal catalog used by fleet.
- Search terms `תמונת מצב הפסקות חשמל` and `צריכת אשראי` uniquely identify
  the intended catalog items for this environment.
- Ready visuals `אוכלוסייה מותרעת` and `כמות אוכלוסיה ברשויות` are stable
  Hebrew labels on those reports (spelling as provided, including
  `אוכלוסיה` without י on Credit Consumption).
- The Credit Consumption info page is a dismissible overlay with a close
  control (X / Close / סגור), not a separate portal route.
- Shared Playwright session and auth file from the root fixture remain
  the login path; new suites do not add a second browser.
- `verify_freshness` already exists on `ReportShell` (feature 003) and is
  reused unchanged.
- No warehouse SQL, coverage-catalog rows, or filter JSON are required
  for Layer 0 smoke.
- Colocating thin page objects under `tests/ui/<report>/` is intentional
  until a later feature adds business logic and a `pages/<report>/`
  module.
- Implementation sequencing lives in `plan.md` and `tasks.md`; this
  specification states the contract those documents must satisfy.
