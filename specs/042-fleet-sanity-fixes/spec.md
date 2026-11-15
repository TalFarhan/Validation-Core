# Feature Specification: Fix Skipped Tests and Tooltips for Fleet DB Sanity

**Feature Branch**: `feature/reportportal-integration` (spec directory `042-fleet-sanity-fixes`; git checkout stays put)

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Resolve the skipped UI chart tests in the Fleet dashboard. Do NOT touch the alerts modules. (1) Tooltips Validation: the unit chart and category chart tests failed because tooltips never opened — update the Playwright hover/click locators so tooltips trigger before asserting counts. (2) Fix Golden Labels: ensure the credit-reason chart assertions map correctly to the expected labels in the YAML data. (3) Resolve skipped tests so `test_ui_credit_reasons_match_golden` and `test_ui_category_actuals_match_golden` pass. (4) Increase locator wait times dynamically for report rendering. (5) All in-function code comments in English only."

## Clarifications

### Session 2026-11-02

- Q: Why do `test_ui_credit_reasons_match_golden` and `test_ui_category_actuals_match_golden` skip today? → A: Both route through `assert_chart_matches` in `tests/sanity/fleet_dashboard/contract.py`. Two skip paths fire: (a) `pytest.skip("chart {key} exposed no golden labels")` when no golden name maps to a rendered label, and (b) `pytest.skip("chart {key} exposed golden labels but no tooltip appeared")` when `hover_chart_segment` raises `LoadTimeoutError` because the Power BI tooltip never opened. The category/unit charts hit (b); the credit-reason chart hits (a).
- Q: Why does the credit-reason chart hit the "no golden labels" path? → A: `withdrawal` (`פילוח סיבות לזיכוי רכב`) is a pie visual. `get_chart_segment_labels` strips pure numeric and `"3 (50.0%)"` data-label chrome, so the reason names must come through the legend/axis `<title>`/text nodes. When the rendered label does not fold to the golden key (`אחר`, `פקודת רידוד פיקודית`) under `normalize_label`, no match is found and the test skips. The golden YAML keys are authoritative; the mapping (reader + normalization) is what must align.
- Q: Should the golden YAML values change? → A: No. `data/fleet/db_sanity_all.yaml` stays the source of truth (Constitution V/VII). The fix is in the reader/normalization and hover logic, not the golden numbers. The YAML may only gain a label alias if a rendered label genuinely cannot fold to a golden key by normalization alone.
- Q: How should tooltips be made to open? → A: Keep `hover_chart_segment`'s hover-first strategy but make it more robust: dynamic per-attempt budgets scaled off `self.timeout`, broader shape/legend targeting, and a click-to-pin fallback (click the segment glyph to open a persistent tooltip) before giving up. Return type stays `str`; a genuinely absent tooltip still raises `LoadTimeoutError`.
- Q: Are timeouts increased? → A: The hard-coded 20s `overall_deadline` and the small per-hover budgets become a function of `self.timeout` (already `120_000` on the fleet page) so slow report renders get more time, while a never-rendering tooltip still raises `LoadTimeoutError` once the budget is exhausted.
- Q: Which modules are off-limits? → A: No alerts or status-picture module, no `core/portal`, no `core/components` (including `core/components/chart.py`), and no root `conftest.py`. Fleet tooltip/chart logic lives on the fleet domain page by constitution, so edits are confined to the fleet page object and the fleet sanity test package (plus an optional additive YAML alias).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unit and category chart tooltips open before counts are asserted (Priority: P1)

A validation author runs the fleet DB-sanity suite. For the unit chart (`פילוח רכבים בשימוש ביחידות`) and the category chart (`פילוח קטגוריות רכב`), hovering a segment reliably opens a Power BI tooltip, the test reads the measure value, and it asserts against the golden count instead of skipping because no tooltip appeared.

**Why this priority**: The unit and category tests are the ones the request names as failing on missing tooltips. If the tooltip never opens, the count can never be read and the test skips.

**Independent Test**: Run `tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_category_actuals_match_golden` and `::test_ui_unit_breakdown_matches_golden` with portal auth. They pass when each golden segment yields a tooltip whose value matches the golden count, with no "no tooltip appeared" skip.

**Acceptance Scenarios**:

1. **Given** the category chart is visible with its golden labels rendered, **When** a segment is hovered, **Then** a chart tooltip opens within the dynamic budget and `hover_chart_segment` returns its text.
2. **Given** a hover does not open a tooltip, **When** the click-to-pin fallback runs, **Then** a persistent tooltip opens and the value is read.
3. **Given** a segment genuinely never shows a tooltip, **When** the budget is exhausted, **Then** `hover_chart_segment` still raises `LoadTimeoutError` (behavior preserved).

---

### User Story 2 - Credit-reason chart labels map to the golden YAML keys (Priority: P1)

A validation author runs the credit-reason test. The pie visual (`פילוח סיבות לזיכוי רכב`) exposes its reason names (`אחר`, `פקודת רידוד פיקודית`) in a form that folds to the golden keys, so the test matches every golden reason and asserts its count instead of skipping with "exposed no golden labels".

**Why this priority**: Without a correct label mapping the credit-reason test can never reach its assertions; it skips before any hover.

**Independent Test**: Run `tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_credit_reasons_match_golden` with auth. It passes when both golden reasons map to rendered labels and their counts match.

**Acceptance Scenarios**:

1. **Given** the credit-reason pie chart, **When** `get_chart_segment_labels("withdrawal")` runs, **Then** both golden reason names appear after normalization (pie `"n (x%)"` data chrome is excluded without dropping the reason text).
2. **Given** the mapped labels, **When** the test hovers each reason, **Then** the tooltip value matches the golden `credit_reasons_summary` count.
3. **Given** a golden reason is genuinely not rendered, **When** mapping runs, **Then** the existing skip guard still fires with its descriptive message (behavior preserved).

---

### User Story 3 - Locator wait times scale with the render budget (Priority: P2)

Hover and tooltip waits are derived from the page's `self.timeout` instead of fixed small constants, so a slow report render gets proportionally more time to settle while a true failure still times out.

**Why this priority**: Flaky skips on slow renders are a secondary but real cause of non-determinism; dynamic budgets remove the magic numbers without masking genuine failures.

**Independent Test**: Inspect `hover_chart_segment` and its helpers. The `overall_deadline` and per-attempt waits are computed from `self.timeout`, not literal seconds; a never-rendering tooltip still raises `LoadTimeoutError`.

**Acceptance Scenarios**:

1. **Given** the fleet page with `self.timeout = 120_000`, **When** a hover runs, **Then** its overall budget is a function of `self.timeout`, not a hard-coded 20 seconds.
2. **Given** an unbounded wait would hide a real failure, **When** the dynamic budget elapses, **Then** `LoadTimeoutError` is raised as before.

---

### User Story 4 - Skipped tests become real assertions, guards stay (Priority: P1)

The tooltip and mapping fixes remove the `pytest.skip` paths that fired on empty/missing tooltips for the named tests; the skip guards remain only as a safety net for a genuinely absent control.

**Why this priority**: The request explicitly asks that the fixes turn skips into passing assertions, not that the skip guards be deleted.

**Independent Test**: Run the full fleet sanity module. `test_ui_credit_reasons_match_golden` and `test_ui_category_actuals_match_golden` report pass/fail (not skip) when data is present; the guards still fire if a control is truly missing.

**Acceptance Scenarios**:

1. **Given** data is present, **When** the two named tests run, **Then** neither skips with an empty-label or no-tooltip message.
2. **Given** a control is genuinely absent, **When** the reader returns nothing, **Then** the existing skip guard still fires (behavior preserved).

---

### Edge Cases

- A pie slice that renders only a `"n (x%)"` data label must still expose its reason name for matching, or a golden label alias covers it.
- A hover that does not open a tooltip must fall back to a click-to-pin, then raise `LoadTimeoutError` only after the dynamic budget is exhausted.
- A never-rendering tooltip still raises `LoadTimeoutError` so a real failure is not hidden.
- The alerts and status-picture modules, `core/`, and the root `conftest.py` are not edited.
- Comments inside new or edited functions are English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MainDashboardPage.hover_chart_segment()` MUST reliably open a Power BI tooltip for a segment of the unit and category charts before the caller asserts a count, using a more robust hover sequence plus a click-to-pin fallback. Its signature and `str` return type are unchanged.
- **FR-002**: A segment hover that cannot open a tooltip MUST fall back to clicking the segment glyph to pin a persistent tooltip; only after that fallback also fails within the dynamic budget may `LoadTimeoutError` be raised.
- **FR-003**: The credit-reason chart (`withdrawal`) golden reasons (`אחר`, `פקודת רידוד פיקודית`) MUST map to rendered labels so `assert_chart_matches` reaches its assertions. The fix is in the reader/normalization; the golden YAML values are not changed. A label alias MAY be added to the golden YAML only if normalization alone cannot fold a rendered label to a golden key.
- **FR-004**: After the fixes, `test_ui_credit_reasons_match_golden` and `test_ui_category_actuals_match_golden` MUST report pass/fail rather than skip when data is present, while the existing skip guards remain as a safety net for a genuinely absent control.
- **FR-005**: Hover/tooltip wait budgets in `hover_chart_segment` and its helpers MUST be derived from `self.timeout` instead of fixed literals (e.g. the 20s `overall_deadline`), so report rendering gets proportionally more time; a never-rendering tooltip MUST still raise `LoadTimeoutError`.
- **FR-006**: This slice MUST NOT edit any alerts or status-picture module, `core/portal`, `core/components` (including `core/components/chart.py`), or the root `conftest.py`.
- **FR-007**: Comments inside new or edited functions MUST be English.
- **FR-008**: Public test-facing fleet page-object APIs (`get_chart_segment_labels`, `hover_chart_segment`, `parse_tooltip_entries`, `dismiss_tooltip`, `get_kpi_value`, `reset_dashboard_filters`) MUST keep their names and return types; the fleet smoke suite MUST stay green.

### Key Entities

- **Chart segment tooltip**: The transient Power BI overlay opened by hovering (or, as a fallback, clicking) a bar/slice; carries the measure value the test asserts.
- **Golden label mapping**: The fold from a rendered chart label to a golden YAML key via `normalize_label`, used by `assert_chart_matches`.
- **Dynamic wait budget**: Hover/tooltip deadlines computed from `self.timeout` rather than fixed constants.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` (including the generic `core/components/chart.py`) are NOT edited. All tooltip/hover/label logic stays on the fleet domain page, as the constitution requires for report tooltips and drilldowns.
- **AC-002**: `MainDashboardPage` keeps inheriting `ReportShell`. No portal step is added or removed.
- **AC-003**: Public reader names and return types on the fleet page are unchanged; any new helper (e.g. a click-to-pin step) is private and additive.
- **AC-004**: `core/` does not load `data/fleet/`. The fleet sanity tests load the golden file.
- **AC-005**: No new report page and no new SQL client; `db/clients/fleet.py` is unchanged.
- **AC-006**: The fleet domain page object stays at `pages/fleet_dashboard/main_dashboard_page.py`; fleet sanity logic stays under `tests/sanity/fleet_dashboard/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With auth, `test_ui_category_actuals_match_golden` and `test_ui_unit_breakdown_matches_golden` reach their assertions with tooltips opened and do not skip with a "no tooltip appeared" message.
- **SC-002**: With auth, `test_ui_credit_reasons_match_golden` maps both golden reasons and asserts their counts; it does not skip with "exposed no golden labels".
- **SC-003**: Hover/tooltip budgets in the fleet page are computed from `self.timeout`; a deliberately broken (never-rendering) tooltip still raises `LoadTimeoutError`.
- **SC-004**: The fleet smoke suite (`tests/ui/fleet_dashboard/`) passes at 100% under `pytest` after the page-object edits.
- **SC-005**: No alerts/status module, `core/`, or root `conftest.py` is edited; the golden YAML metric values are unchanged (an additive label alias is the only permitted YAML edit, and only if required).

## Assumptions

- The unit and category charts render per-segment glyphs that accept a hover or click at their geometric center (the existing shape iteration already targets them).
- The credit-reason pie exposes its reason names via legend/axis text or `<title>` in a form that folds to the golden keys, possibly after a normalization tweak; if not, a single additive YAML alias covers the gap.
- Portal auth is required to run the UI tests; this plan does not run the browser.
- `self.timeout` on the fleet page is `120_000`, inherited from `ReportShell`/`BasePage`, and is a sufficient overall render budget.
