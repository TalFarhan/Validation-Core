# Feature Specification: Secondary-Auth Dashboards — Layer 0 Freshness Smoke + Bypass Hook

**Feature Branch**: `007-secondary-auth-dashboards`

**Created**: 2026-08-30

**Status**: Draft

**Audience**: Validation engineers own the user scenarios. The Layer 0 reuse
shape, the new `_bypass_secondary_auth()` post-catalog hook, per-report
catalog search terms, temporary ready locators, and the smoke-test contract
in Requirements / Architectural Constraints are normative for this platform
capability (Constitution v1.2.0). They are not optional design notes.

**Input**: User description: "Add 4 new dashboards that require a secondary
authentication/entry step, and introduce a bypass hook in `ReportShell`.
Add `def _bypass_secondary_auth(self): pass` to `ReportShell`, and inside the
`navigate()` flow call `self._bypass_secondary_auth()` exactly AFTER clicking
the dashboard in the catalog, but BEFORE waiting for
`self._report_ready_locator()`. Create four new directories under `tests/ui/`
for the new dashboards. DO NOT create anything in `pages/` and DO NOT touch
`.env`. For EACH dashboard create `page.py`, `conftest.py`, and
`test_dashboard_smoke.py` (same structure as 005/006), define
`DASHBOARD_SEARCH_TERM`, use the search term as a temporary exact-text ready
locator, and override `_bypass_secondary_auth(self)` with a placeholder
(comment or print) — real clicks implemented later. Dashboards: Mass Events
(`תמ\"צ אירועים המוניים`), Life-Saving Guidelines
(`תמ\"צ שליטה - סטטוס הנחיות מצילות חיים`), Maya System (`מערכת המא\"יה`),
Public Shelters (`תמ\"צ מחסים ציבוריים`)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mass Events Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Mass Events smoke suite. The suite
opens that report through the shared portal shell (catalog search for
`תמ"צ אירועים המוניים`), runs the domain `_bypass_secondary_auth()` hook after
the catalog click, waits until a temporary ready visual matching that search
term is visible, and confirms the report's last-refresh caption is within 24
hours. The test body stays thin: it uses a local `dashboard` fixture and calls
the inherited freshness check.

**Why this priority**: Each new report is an independent Layer 0 binding.
Mass Events is the first of four identical slices and the MVP.

**Independent Test**: Run the Mass Events smoke suite alone. The suite opens
that report (not fleet or another new report), runs the bypass hook, waits for
the temporary ready locator, and passes `verify_freshness()` when last-refresh
is within 24 hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Mass Events smoke
   suite starts, **Then** the local dashboard fixture opens the report via
   catalog search for `תמ"צ אירועים המוניים`, calls `_bypass_secondary_auth()`
   after the catalog click, and waits until a temporary ready locator matching
   that search term (exact text) is visible.
2. **Given** the Mass Events report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24 hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test runs,
   **Then** it fails (stale data is correctly flagged).
4. **Given** the Mass Events page object, **When** a reviewer inspects it,
   **Then** it inherits `ReportShell`, supplies a search term, a ready locator,
   and a `_bypass_secondary_auth()` override, and contains no slicer, KPI,
   chart, or JSON catalog logic.
5. **Given** the smoke test body, **When** a reviewer inspects it, **Then** it
   contains no iframe locators, date parsing, or CSS — only the page-object
   freshness call.

---

### User Story 2 - Life-Saving Guidelines Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Life-Saving Guidelines smoke suite. The
suite opens that report through catalog search for
`תמ"צ שליטה - סטטוס הנחיות מצילות חיים`, runs the bypass hook after the catalog
click, waits on a temporary ready locator matching that search term, and
confirms last-refresh is within 24 hours.

**Why this priority**: Same Layer 0 contract as Mass Events on a second catalog
product; independently shippable.

**Independent Test**: Run the Life-Saving Guidelines smoke suite alone. The
suite opens that report and passes `verify_freshness()` when the caption is
within 24 hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Life-Saving
   Guidelines smoke suite starts, **Then** the local dashboard fixture opens the
   report via catalog search for `תמ"צ שליטה - סטטוס הנחיות מצילות חיים`, calls
   `_bypass_secondary_auth()`, and waits until a temporary ready locator
   matching that search term (exact text) is visible.
2. **Given** the report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24 hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test runs,
   **Then** it fails.

---

### User Story 3 - Maya System Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Maya System smoke suite. The suite opens
that report through catalog search for `מערכת המא"יה`, runs the bypass hook
after the catalog click, waits on a temporary ready locator matching that
search term, and confirms last-refresh is within 24 hours.

**Why this priority**: Same Layer 0 contract on a third catalog product;
independently shippable.

**Independent Test**: Run the Maya System smoke suite alone. It opens the Maya
System report and passes `verify_freshness()` when the caption is within 24
hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Maya System smoke
   suite starts, **Then** the local dashboard fixture opens the report via
   catalog search for `מערכת המא"יה`, calls `_bypass_secondary_auth()`, and
   waits until a temporary ready locator matching that search term (exact text)
   is visible.
2. **Given** the report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24 hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test runs,
   **Then** it fails.

---

### User Story 4 - Public Shelters Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Public Shelters smoke suite. The suite
opens that report through catalog search for `תמ"צ מחסים ציבוריים`, runs the
bypass hook after the catalog click, waits on a temporary ready locator
matching that search term, and confirms last-refresh is within 24 hours.

**Why this priority**: Same Layer 0 contract on a fourth catalog product;
independently shippable.

**Independent Test**: Run the Public Shelters smoke suite alone. It opens the
Public Shelters report and passes `verify_freshness()` when the caption is
within 24 hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Public Shelters
   smoke suite starts, **Then** the local dashboard fixture opens the report via
   catalog search for `תמ"צ מחסים ציבוריים`, calls `_bypass_secondary_auth()`,
   and waits until a temporary ready locator matching that search term (exact
   text) is visible.
2. **Given** the report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24 hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test runs,
   **Then** it fails.

---

### Edge Cases

- Fleet or another report already open on the shared browser tab — the new
  suite MUST still switch to its own report via catalog search (a different
  report's ready visual MUST NOT be treated as success).
- Catalog search returns several products — open the result matching the
  report's search term.
- A report exposes a secondary authentication / entry screen after the catalog
  click — the domain `_bypass_secondary_auth()` hook is the single place where
  that screen is dismissed. The default Layer 0 hook is a no-op, so fleet and
  the 005/006 reports are unaffected.
- Temporary ready locator (search-term text) is not yet present as a landing
  title on the live report — the ready wait fails until a later change updates
  the locator from live-run feedback. That fail is expected.
- Live report last-refresh older than 24 hours — correct fail of the freshness
  test, not a framework bug.
- Shared session auth already valid — reuse it; do not force a new login.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `ReportShell` MUST gain a `_bypass_secondary_auth(self)` hook
  whose Layer 0 default is a no-op (`pass`). It exists so reports gated behind a
  secondary auth/entry screen can dismiss it without any report-specific logic
  entering `core/`.
- **FR-002**: `ReportShell.navigate()` MUST call `self._bypass_secondary_auth()`
  exactly AFTER the dashboard is clicked in the catalog and BEFORE the flow
  begins waiting on `self._report_ready_locator()`. The call MUST run on every
  navigation path so the hook fires regardless of how the report was reached.
- **FR-003**: The framework MUST add four Layer 0 pages that inherit
  `ReportShell`, each setting its own catalog search term, a temporary ready
  locator (exact text) matching that search term, and a `_bypass_secondary_auth`
  override that is currently a placeholder (comment/print) pending real clicks.
- **FR-004**: The four search terms MUST be: Mass Events
  `תמ"צ אירועים המוניים`; Life-Saving Guidelines
  `תמ"צ שליטה - סטטוס הנחיות מצילות חיים`; Maya System `מערכת המא"יה`; Public
  Shelters `תמ"צ מחסים ציבוריים`.
- **FR-005**: Each new report MUST have its own smoke package under `tests/ui/`
  with a `dashboard` fixture that returns that report's page object and a sanity
  test `test_dashboard_updated_within_24_hours(dashboard)` that calls
  `dashboard.verify_freshness()`.
- **FR-006**: Catalog search MUST use the page's own search term, not the fleet
  default, so these reports can share Layer 0 without editing `.env` between
  suites. This feature MUST NOT modify `.env`.
- **FR-007**: None of the new pages MAY add JSON filter catalogs, generic slicer
  wiring, KPI/chart/table methods, or other business logic. Scope is Layer 0
  readiness, the secondary-auth bypass placeholder, and inherited freshness only.
- **FR-008**: Root fleet `dashboard` fixture and existing
  `tests/ui/fleet_dashboard/` tests MUST keep their contracts. New suites MUST
  override `dashboard` locally. This feature MUST NOT create anything under
  `pages/`.
- **FR-009**: `core/` MUST remain free of the four new product names and their
  ready-locator strings. Those strings belong on the domain page objects. The
  only permitted `core/` change is the generic `_bypass_secondary_auth()` hook
  and its invocation in `navigate()`.
- **FR-010**: New pages MUST reuse `ReportShell` login, catalog, iframe wait,
  visual-load timeout, and `verify_freshness`. They MUST NOT copy those
  implementations.
- **FR-011**: Allure MUST keep existing screenshot/trace failure hooks. Smoke
  tests MUST be marked sanity like other Layer 0 smoke checks.
- **FR-012**: Each of the four new suites MUST be independently runnable. A
  stale live caption is a correct fail of freshness.

### Key Entities

- **`_bypass_secondary_auth()` hook**: Generic Layer 0 post-catalog seam.
  Default no-op; domain pages override it to dismiss a secondary auth/entry
  screen. No report-specific text lives in `core/`.
- **Mass Events report**: Portal catalog product searched as
  `תמ"צ אירועים המוניים`. Temporary ready visual is that same search term.
- **Life-Saving Guidelines report**: Portal catalog product searched as
  `תמ"צ שליטה - סטטוס הנחיות מצילות חיים`. Temporary ready visual is that same
  search term.
- **Maya System report**: Portal catalog product searched as `מערכת המא"יה`.
  Temporary ready visual is that same search term.
- **Public Shelters report**: Portal catalog product searched as
  `תמ"צ מחסים ציבוריים`. Temporary ready visual is that same search term.
- **Temporary ready locator**: Iframe exact text matching the catalog search
  term, used until live-run feedback supplies the real landing-page title.
- **Layer 0 smoke package**: Directory with page object, local `dashboard`
  fixture, and one freshness smoke test. No filter JSON.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. It MAY read
  a page-owned catalog search term with fallback to the settings default
  (feature 004), and it MAY expose the generic `_bypass_secondary_auth()` seam.
  It MUST NOT hardcode the four new product names or ready strings.
- **AC-002**: Domain page objects MUST inherit `ReportShell`. The four pages
  live under `tests/ui/mass_events_dashboard/`,
  `tests/ui/life_saving_guidelines_dashboard/`,
  `tests/ui/maya_system_dashboard/`, and `tests/ui/public_shelters_dashboard/`
  for this Layer 0-only slice (no `pages/<report>/` domain module).
- **AC-003**: Report-ready state MUST be supplied by each domain page locator.
  Ready text MUST NOT be hardcoded in `ReportShell`. For this feature the ready
  locator is temporarily the same phrase as `DASHBOARD_SEARCH_TERM` (matched
  with `exact=True`).
- **AC-004**: Public fleet APIs (`navigate`, `reload_and_measure_ready_ms`,
  root `dashboard` fixture, fleet smoke) MUST keep their contracts. Adding the
  `_bypass_secondary_auth()` call inside `navigate()` MUST NOT change its
  signature and MUST be a no-op for fleet (default hook does nothing). Do not
  edit `.env`.
- **AC-005**: Layer 2 (`core/components/`) MUST NOT be used by these new pages.
  No `data/*.json` catalogs for the new reports.
- **AC-006**: Each suite's `dashboard` fixture MUST be defined next to that
  suite so pytest fixture shadowing keeps fleet tests on `MainDashboardPage`.

### Integration shape (normative)

```text
ReportShell (Layer 0)
  catalog search term = page.DASHBOARD_SEARCH_TERM or settings default
  _bypass_secondary_auth() default no-op (pass)
  navigate(): ... open report (catalog click) → _bypass_secondary_auth()
              → wait _report_ready_locator() → ...
  verify_freshness() inherited

MassEventsPage(ReportShell)
  DASHBOARD_SEARCH_TERM = 'תמ"צ אירועים המוניים'
  ready = same phrase, exact=True (temporary)
  _bypass_secondary_auth() → placeholder (real clicks later)

LifeSavingGuidelinesPage(ReportShell)
  DASHBOARD_SEARCH_TERM = 'תמ"צ שליטה - סטטוס הנחיות מצילות חיים'
  ready = same phrase, exact=True (temporary)
  _bypass_secondary_auth() → placeholder

MayaSystemPage(ReportShell)
  DASHBOARD_SEARCH_TERM = 'מערכת המא"יה'
  ready = same phrase, exact=True (temporary)
  _bypass_secondary_auth() → placeholder

PublicSheltersPage(ReportShell)
  DASHBOARD_SEARCH_TERM = 'תמ"צ מחסים ציבוריים'
  ready = same phrase, exact=True (temporary)
  _bypass_secondary_auth() → placeholder

tests/ui/<report>/conftest.py
  dashboard fixture → that page, navigate()

tests/ui/<report>/test_dashboard_smoke.py
  test_dashboard_updated_within_24_hours(dashboard)
    → dashboard.verify_freshness()
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tester can confirm each of the four reports' last-refresh
  freshness with a single page-object call after the suite opens that report.
- **SC-002**: `ReportShell.navigate()` invokes `_bypass_secondary_auth()` after
  the catalog click and before the ready-locator wait, on every navigation path.
- **SC-003**: 100% of existing fleet smoke checks still pass; fleet tests still
  receive the fleet dashboard fixture, and the default bypass hook is a no-op.
- **SC-004**: Each new suite is independently runnable and contains exactly one
  Layer 0 freshness smoke test (no slicer/KPI/chart cases).
- **SC-005**: A reviewer finds zero of the four new product names or temporary
  ready strings under `core/`, nothing new under `pages/`, and no `.env` edits.
- **SC-006**: When last-refresh is older than 24 hours, the new smoke checks
  fail 100% of the time (stale data is never silently accepted).

## Assumptions

- All four products exist in the same Agamim portal catalog used by fleet.
- Search terms uniquely identify the intended catalog items for this environment.
- Temporary ready locators equal the catalog search terms until live-run
  feedback supplies the real landing-page titles.
- Each report's real secondary-auth screen and its clicks are unknown until a
  live run; the override placeholder is intentional and will be filled later.
- Shared Playwright session and auth file from the root fixture remain the login
  path; new suites do not add a second browser.
- `verify_freshness` already exists on `ReportShell` (feature 003) and is reused
  unchanged. Per-page `DASHBOARD_SEARCH_TERM` resolution already exists (feature
  004).
- No warehouse SQL, coverage-catalog rows, or filter JSON are required for
  Layer 0 smoke.
- Colocating thin page objects under `tests/ui/<report>/` is intentional until a
  later feature adds business logic and a `pages/<report>/` module.
- Implementation sequencing lives in `plan.md` and `tasks.md`; this
  specification states the contract those documents must satisfy.
