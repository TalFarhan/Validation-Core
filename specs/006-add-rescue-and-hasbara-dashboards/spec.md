# Feature Specification: Rescue & Hasbara Dashboards — Layer 0 Freshness Smoke

**Feature Branch**: `006-add-rescue-and-hasbara-dashboards`

**Created**: 2026-08-30

**Status**: Draft

**Audience**: Validation engineers own the user scenarios. The Layer 0 reuse
shape, per-report catalog search terms, temporary ready locators, and
smoke-test contract in Requirements / Architectural Constraints are
normative for this platform capability (Constitution v1.2.0). They are not
optional design notes.

**Input**: User description: "Add Layer 0 freshness smoke tests for two new
dashboards. Create two new directories under `tests/ui/` for the new
dashboards. DO NOT create anything in `pages/` and DO NOT touch `.env`.
For each dashboard: `page.py` inheriting `ReportShell` with
`DASHBOARD_SEARCH_TERM` as listed; `_report_ready_locator` as a temporary
text locator matching the search term (`exact=True`, updated later from
live run feedback); `conftest.py` dashboard fixture like the existing ones;
`test_dashboard_smoke.py` with `test_dashboard_updated_within_24_hours`
calling `dashboard.verify_freshness()`. Dashboards: Rescue Capabilities
(`כשירויות חילוץ במרחב האזרחי`), Public Inquiries
(`ניתוח פניות הסברה`)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rescue Capabilities Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Rescue Capabilities smoke suite. The
suite opens that report through the shared portal shell (catalog search
for `כשירויות חילוץ במרחב האזרחי`), waits until a temporary ready visual
matching that search term is visible, and confirms the report's
last-refresh caption is within 24 hours. The test body stays thin: it uses
a local `dashboard` fixture and calls the inherited freshness check.

**Why this priority**: Each new report is an independent Layer 0 binding.
Rescue Capabilities is the first of two identical slices and the MVP.

**Independent Test**: Run the Rescue Capabilities smoke suite alone. The
suite opens that report (not fleet or another new report), waits for the
temporary ready locator, and passes `verify_freshness()` when last-refresh
is within 24 hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Rescue
   Capabilities smoke suite starts, **Then** the local dashboard fixture
   opens the report via catalog search for `כשירויות חילוץ במרחב האזרחי`
   and waits until a temporary ready locator matching that search term
   (exact text) is visible.
2. **Given** the Rescue Capabilities report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24
   hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test
   runs, **Then** it fails (stale data is correctly flagged).
4. **Given** the Rescue Capabilities page object, **When** a reviewer
   inspects it, **Then** it inherits `ReportShell`, supplies only a search
   term and a ready locator, and contains no slicer, KPI, chart, or JSON
   catalog logic.
5. **Given** the smoke test body, **When** a reviewer inspects it, **Then**
   it contains no iframe locators, date parsing, or CSS — only the
   page-object freshness call.

---

### User Story 2 - Public Inquiries Layer 0 freshness smoke (Priority: P1)

A Validation engineer runs a dedicated Public Inquiries smoke suite. The
suite opens that report through catalog search for `ניתוח פניות הסברה`,
waits on a temporary ready locator matching that search term, and confirms
last-refresh is within 24 hours.

**Why this priority**: Same Layer 0 contract as Rescue Capabilities on a
second catalog product; independently shippable.

**Independent Test**: Run the Public Inquiries smoke suite alone. The suite
opens the Public Inquiries report and passes `verify_freshness()` when the
caption is within 24 hours.

**Acceptance Scenarios**:

1. **Given** an authenticated portal session, **When** the Public Inquiries
   smoke suite starts, **Then** the local dashboard fixture opens the
   report via catalog search for `ניתוח פניות הסברה` and waits until a
   temporary ready locator matching that search term (exact text) is
   visible.
2. **Given** the Public Inquiries report is open and ready, **When**
   `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes if last-refresh is within 24
   hours.
3. **Given** last-refresh is older than 24 hours, **When** the smoke test
   runs, **Then** it fails (stale data is correctly flagged).
4. **Given** the Public Inquiries page object, **When** a reviewer inspects
   it, **Then** it inherits `ReportShell` and contains no slicer, KPI,
   chart, or JSON catalog logic.

---

### Edge Cases

- Fleet or another report already open on the shared browser tab — the
  new suite MUST still switch to its own report via catalog search (a
  different report's ready visual MUST NOT be treated as success).
- Catalog search returns several products — open the result matching the
  report's search term.
- Temporary ready locator (search-term text) is not yet present as a
  landing title on the live report — the ready wait fails until a later
  change updates the locator from live-run feedback. That fail is
  expected until the locator is confirmed.
- Live report last-refresh older than 24 hours — correct fail of the
  freshness test, not a framework bug.
- Shared session auth already valid — reuse it; do not force a new login.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The framework MUST add a Rescue Capabilities Layer 0 page
  that inherits `ReportShell`, sets catalog search term
  `כשירויות חילוץ במרחב האזרחי`, and uses a temporary ready locator
  (exact text) matching that search term.
- **FR-002**: The framework MUST add a Public Inquiries Layer 0 page that
  inherits `ReportShell`, sets catalog search term `ניתוח פניות הסברה`,
  and uses a temporary ready locator (exact text) matching that search
  term.
- **FR-003**: Each new report MUST have its own smoke package under
  `tests/ui/` with a `dashboard` fixture that returns that report's page
  object and a sanity test `test_dashboard_updated_within_24_hours(dashboard)`
  that calls `dashboard.verify_freshness()`.
- **FR-004**: Catalog search MUST use the page's own search term, not the
  fleet default, so these reports can share Layer 0 without editing
  `.env` between suites. This feature MUST NOT modify `.env`.
- **FR-005**: None of the new pages MAY add JSON filter catalogs, generic
  slicer wiring, KPI/chart/table methods, or other business logic. Scope
  is Layer 0 readiness plus inherited freshness only.
- **FR-006**: Root fleet `dashboard` fixture and existing
  `tests/ui/fleet_dashboard/` tests MUST keep their contracts. New suites
  MUST override `dashboard` locally. This feature MUST NOT create anything
  under `pages/`.
- **FR-007**: `core/` MUST remain free of the two new product names and
  their ready-locator strings. Those strings belong on the domain page
  objects.
- **FR-008**: New pages MUST reuse `ReportShell` login, catalog, iframe
  wait, visual-load timeout, and `verify_freshness`. They MUST NOT copy
  those implementations. Layer 0 already resolves per-page
  `DASHBOARD_SEARCH_TERM` (feature 004); this feature MUST NOT change
  `core/` unless a regression is found.
- **FR-009**: Allure MUST keep existing screenshot/trace failure hooks.
  Smoke tests MUST be marked sanity like other Layer 0 smoke checks.
- **FR-010**: Each of `pytest tests/ui/rescue_capabilities_dashboard/` and
  `pytest tests/ui/public_inquiries_dashboard/` MUST be independently
  runnable. A stale live caption is a correct fail of freshness.

### Key Entities

- **Rescue Capabilities report**: Portal catalog product searched as
  `כשירויות חילוץ במרחב האזרחי`. Temporary ready visual is that same
  search term (exact text).
- **Public Inquiries report**: Portal catalog product searched as
  `ניתוח פניות הסברה`. Temporary ready visual is that same search term
  (exact text).
- **Temporary ready locator**: Iframe exact text matching the catalog
  search term, used until live-run feedback supplies the real
  landing-page title.
- **Layer 0 smoke package**: Directory with page object, local
  `dashboard` fixture, and one freshness smoke test. No filter JSON.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. It MAY
  already read a page-owned catalog search term (class/instance attribute)
  with fallback to the existing settings default (feature 004). This
  feature MUST NOT hardcode the two new product names or ready strings
  into `core/`.
- **AC-002**: Domain page objects MUST inherit `ReportShell`. The two
  pages live under `tests/ui/rescue_capabilities_dashboard/` and
  `tests/ui/public_inquiries_dashboard/` for this Layer 0-only slice
  (no `pages/<report>/` domain module).
- **AC-003**: Report-ready state MUST be supplied by each domain page
  locator. Ready text MUST NOT be hardcoded in `ReportShell`. For this
  feature the ready locator is temporarily the same phrase as
  `DASHBOARD_SEARCH_TERM` (matched with `exact=True`).
- **AC-004**: Public fleet APIs (`navigate`,
  `reload_and_measure_ready_ms`, root `dashboard` fixture, fleet smoke)
  MUST keep their contracts. Do not edit `.env`.
- **AC-005**: Layer 2 (`core/components/`) MUST NOT be used by these new
  pages. No `data/*.json` catalogs for the new reports.
- **AC-006**: Each suite's `dashboard` fixture MUST be defined next to
  that suite so pytest fixture shadowing keeps fleet tests on
  `MainDashboardPage`.

### Integration shape (normative)

```text
ReportShell (Layer 0) — unchanged from 004
  catalog search term = page.DASHBOARD_SEARCH_TERM or settings default
  verify_freshness() inherited

RescueCapabilitiesPage(ReportShell)
  DASHBOARD_SEARCH_TERM = "כשירויות חילוץ במרחב האזרחי"
  ready = same phrase, exact=True (temporary)

PublicInquiriesPage(ReportShell)
  DASHBOARD_SEARCH_TERM = "ניתוח פניות הסברה"
  ready = same phrase, exact=True (temporary)

tests/ui/<report>/conftest.py
  dashboard fixture → that page, navigate()

tests/ui/<report>/test_dashboard_smoke.py
  test_dashboard_updated_within_24_hours(dashboard)
    → dashboard.verify_freshness()
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tester can confirm Rescue Capabilities last-refresh
  freshness with a single page-object call after the suite opens that
  report.
- **SC-002**: A tester can confirm Public Inquiries last-refresh freshness
  with a single page-object call after the suite opens that report.
- **SC-003**: 100% of existing fleet smoke checks still pass; fleet tests
  still receive the fleet dashboard fixture.
- **SC-004**: Each new suite is independently runnable and contains
  exactly one Layer 0 freshness smoke test (no slicer/KPI/chart cases).
- **SC-005**: A reviewer finds zero of the two new product names or
  temporary ready strings under `core/`, nothing new under `pages/`, and
  no `.env` edits.
- **SC-006**: When last-refresh is older than 24 hours, the new smoke
  checks fail 100% of the time (stale data is never silently accepted).

## Assumptions

- Both products exist in the same Agamim portal catalog used by fleet.
- Search terms uniquely identify the intended catalog items for this
  environment.
- Temporary ready locators equal the catalog search terms until live-run
  feedback supplies the real landing-page titles.
- Shared Playwright session and auth file from the root fixture remain
  the login path; new suites do not add a second browser.
- `verify_freshness` already exists on `ReportShell` (feature 003) and is
  reused unchanged.
- Per-page `DASHBOARD_SEARCH_TERM` resolution already exists (feature
  004); this feature does not need to change Layer 0.
- No warehouse SQL, coverage-catalog rows, or filter JSON are required
  for Layer 0 smoke.
- Colocating thin page objects under `tests/ui/<report>/` is intentional
  until a later feature adds business logic and a `pages/<report>/`
  module.
- Implementation sequencing lives in `plan.md` and `tasks.md`; this
  specification states the contract those documents must satisfy.
