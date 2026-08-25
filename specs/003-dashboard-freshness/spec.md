# Feature Specification: Dashboard Freshness Verification

**Feature Branch**: `003-dashboard-freshness`

**Created**: 2026-08-25

**Status**: Draft

**Audience**: Validation and BI leads own the user scenarios. The Layer 0 /
Layer 3 split, generic last-refresh chrome, and smoke-test contract in
Requirements / Architectural Constraints are normative for this platform
capability (Constitution v1.1.0, to be amended for last-refresh verification).
They are not optional design notes.

**Input**: User description: "Add a generic dashboard freshness verification to
Layer 0 (ReportShell) and apply it to the fleet dashboard smoke tests.
`verify_freshness(max_hours: int = 24)` locates text containing
'הדשבורד עודכן לאחרונה ב:', extracts the date/time, parses it, and asserts
the difference from now is <= max_hours. Fleet smoke test
`test_dashboard_updated_within_24_hours` calls `dashboard.verify_freshness()`.
Do not hardcode dashboard-specific selectors in Layer 0; use a regex or
standard text locator inside the Power BI iframe."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generic last-refresh check on any report (Priority: P1)

A Validation engineer opens any Power BI report hosted in the shared portal
shell. They can ask the shell to confirm that the report's last-refresh
caption is present, readable, and not older than a chosen maximum age
(default: 24 hours). The check uses the standard last-refresh phrase that
Power BI reports display, not a title unique to the fleet dashboard. A
second report can reuse the same check without copying locators or date
parsing.

**Why this priority**: Stale data is a production-quality failure. The check
must live once on the shared shell so every future report inherits it. This
is the MVP.

**Independent Test**: With a report already open through the existing
navigate path, call `verify_freshness()` (default 24 hours) and a
`verify_freshness(max_hours=N)` variant. Confirm Layer 0 locates the
last-refresh caption by standard text (or regex) inside the report iframe,
parses the timestamp, and fails with a clear assertion when the caption is
missing, unparseable, or older than the limit. Confirm `core/` has no
fleet-specific selectors, KPI titles, vehicle/district labels, or CSS ids
unique to one dashboard.

**Acceptance Scenarios**:

1. **Given** a report is open and the last-refresh caption is visible in the
   iframe, **When** a tester calls freshness verification with the default
   limit, **Then** the check passes if the parsed timestamp is at most 24
   hours before now.
2. **Given** the same visible caption, **When** a tester calls freshness
   verification with a custom maximum age, **Then** the check uses that
   limit instead of 24 hours.
3. **Given** the last-refresh caption is missing from the iframe, **When**
   freshness is verified, **Then** the check fails with a message that the
   standard last-refresh phrase was not found.
4. **Given** the caption is present but the timestamp cannot be parsed,
   **When** freshness is verified, **Then** the check fails with a message
   that includes the captured text.
5. **Given** a parsed timestamp older than the allowed maximum age, **When**
   freshness is verified, **Then** the check fails and reports both the
   parsed time and the observed age.
6. **Given** Layer 0 source under `core/`, **When** a reviewer searches for
   fleet-specific selectors, vehicles, district, subunit, or fleet KPI/chart
   titles, **Then** there are zero matches. The last-refresh Hebrew phrase is
   treated as generic Power BI chrome, not as a fleet label.

---

### User Story 2 - Fleet smoke asserts freshness within 24 hours (Priority: P1)

A Validation engineer runs the fleet dashboard smoke suite. A dedicated
sanity test confirms the open fleet report was last refreshed within 24
hours. The test body stays thin: it uses the shared `dashboard` fixture
(already navigated) and calls the shell method. It does not locate iframe
text, parse dates, or hardcode CSS selectors.

**Why this priority**: The generic method only earns its place when the
binding fleet suite actually exercises it. This is the Layer 3 application
of User Story 1.

**Independent Test**: Add `test_dashboard_updated_within_24_hours(dashboard)`
to `tests/ui/fleet_dashboard/test_dashboard_smoke.py`. The test calls
`dashboard.verify_freshness()` (default 24 hours) and is marked sanity like
the other smoke checks. Existing smoke tests remain unchanged.

**Acceptance Scenarios**:

1. **Given** the fleet report is already open via the `dashboard` fixture,
   **When** `test_dashboard_updated_within_24_hours` runs, **Then** it calls
   `dashboard.verify_freshness()` and passes when the caption is within 24
   hours.
2. **Given** the last-refresh timestamp is older than 24 hours, **When** the
   new smoke test runs, **Then** it fails (the suite correctly flags stale
   data).
3. **Given** existing smoke tests, **When** this feature lands, **Then**
   those tests are not rewritten; only the new freshness test is added.
4. **Given** the new test file body, **When** a reviewer inspects it, **Then**
   it contains no iframe locators, date parsing, or fleet-specific CSS
   selectors — only the page-object call.

---

### Edge Cases

- Caption present but truncated or split across nodes so a naive exact-string
  match misses it — the locator MUST still find text *containing* the
  standard phrase.
- Timestamp in a future offset (clock skew) — treat a future timestamp as
  fresh (age is not greater than the limit).
- Multiple matches of the phrase — use the first visible match inside the
  report iframe.
- Report iframe not yet ready — wait using the existing iframe wait policy
  before asserting; do not invent a fleet ready visual.
- Whitespace, extra punctuation, or a date with or without seconds after the
  phrase — parsing MUST tolerate common variants.
- `max_hours` of 0 — only timestamps at or after now (including future)
  pass; any past timestamp fails.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Layer 0 `ReportShell` MUST expose
  `verify_freshness(max_hours: int = 24)`. The default maximum age is 24
  hours. Domain pages inherit the method; they MUST NOT re-implement last-
  refresh parsing.
- **FR-002**: The method MUST locate text containing
  `הדשבורד עודכן לאחרונה ב:` inside the Power BI report iframe using a
  regex or standard text locator. It MUST NOT hardcode dashboard-specific
  CSS selectors, visual ids, fleet KPI titles, or other report-unique
  locators.
- **FR-003**: The method MUST extract the date/time that follows the
  standard phrase, parse it with Python `datetime`, and assert that
  `datetime.now() - parsed <= max_hours`.
- **FR-004**: Failure messages MUST distinguish (a) caption not found,
  (b) timestamp unparseable, (c) timestamp older than `max_hours`. Each
  message MUST include enough captured text or computed age for a tester
  to diagnose without opening a debugger.
- **FR-005**: Layer 3 MUST add
  `test_dashboard_updated_within_24_hours(dashboard)` in
  `tests/ui/fleet_dashboard/test_dashboard_smoke.py`. The test MUST call
  `dashboard.verify_freshness()` and MUST be marked `sanity` like the other
  smoke tests.
- **FR-006**: Existing smoke tests and `conftest.py` MUST NOT be rewritten.
  Public APIs `navigate` and `reload_and_measure_ready_ms` stay unchanged.
- **FR-007**: After this feature, `pytest tests/ui/fleet_dashboard/` MUST
  pass at 100% when the live report's last-refresh caption is within 24
  hours. A genuinely stale report MUST fail the new test (that is a correct
  fail, not a framework bug).
- **FR-008**: `core/` MUST remain free of vehicles, district, subunit, fleet
  KPI/chart titles, and fleet slicer names. The last-refresh Hebrew phrase
  is generic Power BI chrome and MAY live in Layer 0.
- **FR-009**: KPI cards, tabs, tables, charts, tooltips, drilldown, and
  slicer interaction MUST stay where they are. This feature adds last-
  refresh verification only.
- **FR-010**: Allure SHOULD record a step for freshness verification.
  Failures MUST still produce screenshot and trace attachments via the
  existing pytest/Playwright hooks.
- **FR-011**: Constitution Principles I and VII MUST be updated in the same
  feature so Layer 0 is authorized to verify generic last-refresh chrome,
  while report-specific visuals remain outside `core/`.

### Key Entities

- **Last-refresh caption**: Standard Power BI chrome text containing
  `הדשבורד עודכן לאחרונה ב:` followed by a date/time. Shared across reports
  that use this caption; not a fleet KPI.
- **Freshness window**: Maximum allowed age in hours (default 24) between
  now and the parsed last-refresh timestamp.
- **ReportShell (Layer 0)**: Generic host that locates the caption inside
  the report iframe, parses the timestamp, and asserts the window.
- **Fleet smoke test (Layer 3)**: Thin caller that applies the default
  24-hour window to the fleet dashboard via the existing `dashboard`
  fixture.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal/page.py`) MUST remain report-agnostic.
  It MUST NOT contain vehicles, district, fleet KPI/chart titles, or other
  report-specific labels. Generic last-refresh chrome MAY live here.
- **AC-002**: Domain page objects MUST inherit or compose `ReportShell`
  rather than re-implement last-refresh location or parsing.
  `MainDashboardPage` MUST NOT add a competing freshness method.
- **AC-003**: Report-ready state remains a domain locator. Freshness
  verification MUST wait on the generic iframe (and the already-loaded
  report) — never on a fleet KPI card.
- **AC-004**: Public test-facing APIs `navigate` and
  `reload_and_measure_ready_ms` MUST keep their contracts. The new method
  `verify_freshness(max_hours: int = 24)` is an additive contract. Tests
  that call it are added in the same change (FR-005).
- **AC-005**: Layer 2 (`core/components/`) is unchanged. Do not put
  freshness logic in `Slicer`.
- **AC-006**: Locators in Layer 0 MUST be regex or `get_by_text` (or
  equivalent text locators) scoped to the Power BI iframe. CSS/XPath
  unique to the fleet report is forbidden.
- **AC-007**: Layer 3 application is the one new smoke test in
  `tests/ui/fleet_dashboard/test_dashboard_smoke.py`. Do not add a second
  copy of parsing in the test or on the fleet page.

### Integration shape (normative)

```text
ReportShell (Layer 0)                         # core/portal/page.py
  verify_freshness(max_hours=24)
    → iframe text locator / regex for
      "הדשבורד עודכן לאחרונה ב:"
    → parse datetime → assert age <= max_hours

MainDashboardPage(ReportShell)                # inherits; no override

tests/ui/fleet_dashboard/test_dashboard_smoke.py
  test_dashboard_updated_within_24_hours(dashboard)
    → dashboard.verify_freshness()
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tester can confirm last-refresh freshness on the open
  report with a single page-object call and no extra inputs (default window
  24 hours).
- **SC-002**: 100% of the existing fleet smoke checks still pass; the new
  freshness check is the only added smoke case.
- **SC-003**: When last-refresh is older than 24 hours, the new smoke check
  fails 100% of the time (stale data is never silently accepted).
- **SC-004**: A reviewer finds zero fleet business terms in `core/`
  (vehicles, district, subunit, fleet KPI or chart titles). The last-refresh
  phrase is the only Hebrew chrome added.
- **SC-005**: A second report can reuse freshness verification by inheriting
  the shell — without copying locators or parsing.
- **SC-006**: Missing or unparseable captions fail with an identifiable
  reason in the test output (not a generic timeout with no captured text).
- **SC-007**: Binding suite `tests/ui/fleet_dashboard/` remains the gate and
  MUST be 100% green when the live report is actually fresh.

## Assumptions

- The Hebrew phrase `הדשבורד עודכן לאחרונה ב:` is generic Power BI last-
  refresh chrome shared by reports in this portal, not a fleet-only KPI
  title. Treating it as generic chrome is consistent with Constitution
  Principle II (generic chrome MAY live in `core/`).
- `datetime.now()` is local machine time. The caption timestamp is
  interpreted in the same local timezone unless the captured text includes
  an explicit offset.
- Common caption formats after the phrase include `dd/MM/yyyy HH:mm` and
  `dd/MM/yyyy HH:mm:ss` (with optional seconds). Parsing tries those
  variants first; additional common variants (ISO-like, day/month swapped)
  MAY be attempted if the primary patterns fail.
- The report is already navigated and visually ready via the existing
  `dashboard` fixture / `navigate` path. Freshness does not replace ready-
  state.
- A future timestamp (clock skew) is treated as within the window.
- No warehouse SQL is consulted; the UI caption is the source of last-
  refresh truth for this check.
- Constitution Principles I and VII are amended in this feature to
  authorize last-refresh verification as shared Layer 0 behavior.
- Implementation sequencing lives in `plan.md` and `tasks.md`; this
  specification states the contract those documents must satisfy.
- No second production report is in scope; only the reuse *shape* must be
  possible.
