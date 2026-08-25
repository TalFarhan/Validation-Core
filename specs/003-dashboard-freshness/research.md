# Research: Dashboard Freshness Verification

**Feature**: `003-dashboard-freshness` | **Date**: 2026-08-25

All Technical Context items were known from the repo, Constitution v1.1.0,
and the requester's Layer 0 / Layer 3 rules. No `NEEDS CLARIFICATION`
markers remain.

## Decision: Last-refresh lives on ReportShell, not Slicer or the fleet page

- **Decision**: Implement `verify_freshness(max_hours: int = 24)` on
  `ReportShell` in `core/portal/page.py`. `MainDashboardPage` inherits it
  and MUST NOT override. Do not add a Layer 2 component.
- **Rationale**: Spec FR-001 / AC-002 / AC-005. Last-refresh is portal /
  report-chrome, same class of concern as iframe wait. A fleet-page method
  would be copied by the next report. Slicer is filter interaction only.
- **Alternatives considered**: Fleet-only helper on `MainDashboardPage` —
  rejected (domain leakage of a generic check). Layer 2 module —
  rejected (over-structure for one method). Test-body locators — rejected
  (Constitution IV).

## Decision: Text / regex inside the iframe, never fleet CSS

- **Decision**: Locate the caption with a regex or `get_by_text` pattern
  matching `הדשבורד עודכן לאחרונה ב:` scoped to the Power BI iframe.
  Forbidden: visual GUIDs, fleet KPI titles, CSS unique to this report.
- **Rationale**: Spec FR-002 / AC-006 and Constitution II. The phrase is
  generic last-refresh chrome (Principle II already allows generic chrome
  phrases in `core/`).
- **Alternatives considered**: `page.get_by_text` on the outer page —
  rejected (caption lives in the iframe). `aria-label` / visual title
  unique to fleet — rejected (dashboard-specific).

## Decision: FrameLocator via existing iframe selector

- **Decision**: Reuse the shell's iframe identity (`main iframe` with
  fallback `iframe`). Read inner text through Playwright `FrameLocator`
  (`page.frame_locator(...)` or `Locator.content_frame`), not through the
  outer page. Wait with `_wait_for_dashboard_iframe` before asserting.
- **Rationale**: `_dashboard_iframe()` today returns a `Locator`. Text
  inside a cross-origin Power BI frame is not on `page`. Fleet already
  uses `page.frame_locator("main iframe")` for domain visuals; Layer 0
  must use the same iframe *selector*, not fleet visual locators.
- **Alternatives considered**: `page.locator("iframe").inner_text()` —
  often empty for nested frames. Inject JS into the parent — fragile.

## Decision: Parse with datetime, compare to datetime.now()

- **Decision**: Extract the substring after the standard phrase. Try
  `datetime.strptime` formats in order: `%d/%m/%Y %H:%M:%S`,
  `%d/%m/%Y %H:%M`, `%m/%d/%Y %H:%M:%S`, `%m/%d/%Y %I:%M:%S %p`,
  `%d.%m.%Y %H:%M:%S`, `%Y-%m-%d %H:%M:%S`. Assert
  `(datetime.now() - parsed) <= timedelta(hours=max_hours)`. Naive datetimes
  in local time. Future timestamps (negative age) pass.
- **Rationale**: Spec FR-003 and Assumptions. Power BI locale may emit
  day-first or month-first strings; a short ordered list is enough
  without a heavy parser.
- **Alternatives considered**: `dateutil.parser` — extra dependency, not
  in `requirements.txt`. Warehouse last-refresh SQL — spec says UI caption
  is the source of truth. UTC conversion — caption has no timezone.

## Decision: One new sanity test; do not rewrite existing smoke

- **Decision**: Add `test_dashboard_updated_within_24_hours(dashboard)` in
  `tests/ui/fleet_dashboard/test_dashboard_smoke.py`. Body is
  `dashboard.verify_freshness()`. Keep `@pytest.mark.sanity`. Do not edit
  other tests or `conftest.py`.
- **Rationale**: Spec FR-005 / FR-006 / Constitution III (tests updated in
  the same change when the public API grows).
- **Alternatives considered**: Separate test module — unnecessary. Unit
  test of the parser with a fake page — useful later, not required to
  close this feature.

## Decision: Amend Constitution I and VII (MINOR 1.1.0 → 1.2.0)

- **Decision**: Expand Layer 0 authorized behavior to include generic
  last-refresh verification. Keep KPI/chart/table/slicer extraction
  forbidden. Update `.specify/templates/` plan/spec/tasks constitution
  wording in the same change.
- **Rationale**: Spec FR-011. Principle VII currently lists only login,
  catalog, iframe wait, and visual-load timeout. Shipping the method
  without the amendment would fail the Extract-shared-only gate.
- **Alternatives considered**: Justify as Complexity Tracking without
  amending — rejected (this is intended shared Layer 0 behavior, not a
  one-off exception).

## Decision: Binding test path

- **Decision**: Gate is `pytest tests/ui/fleet_dashboard/`. A stale live
  report is a correct fail of the new test. Existing e2e is not edited
  and is not required to call freshness.
- **Rationale**: Spec FR-007 / SC-007.
