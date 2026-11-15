# Phase 0 Research: Fix Hierarchy Level Locators

All Technical Context items are known from `AlertsPopulationPage`, the hierarchy sanity
helpers, and the report iframe on `ReportShell`. No **NEEDS CLARIFICATION** remains.

## R1 — Which feature directory this plan belongs to

- **Decision**: Plan this slice as `specs/047-hierarchy-level-locators`. Repoint
  `.specify/feature.json` at that directory. Leave the git checkout on
  `feature/reportportal-integration`. Leave `specs/046-credit-ui-validation/` unchanged.
- **Rationale**: Setup initially resolved the pinned feature to the credit UI plan.
  The brief is the alerts hierarchy tabs. Writing it into 046 would replace an unrelated
  plan. Recent slices in this repo keep the same git branch and use a new spec directory.
- **Alternatives considered**: Fill `specs/046-credit-ui-validation/plan.md` again.
  Rejected — that spec is Credit Consumption YAML sanity. Amend 045 in place. Rejected —
  045 already shipped the force-click on a role-matched header control; this brief
  replaces that target.

## R2 — Text locator inside the report iframe

- **Decision**: `_hierarchy_control` returns
  `self._report_frame().get_by_text(label, exact=True)`. `label` is
  `_HIERARCHY_LEVEL_NAMES[level]` (`נפה`, `רשות`, `יישוב`). `set_hierarchy_level` clicks
  `control.first` and does not call `count()` first.
- **Rationale**: `_report_frame()` is the Power BI iframe (`core/portal/page.py`).
  `page.get_by_text` on the outer browser page does not see nodes inside that iframe.
  The page object already looks up other visual text with `_report_frame().get_by_text`.
  `exact=True` matches the tab word and leaves a longer string such as
  `התרעות לפי נפה` unmatched. `.first` keeps the click legal when Power BI duplicates
  the same string. `click()` on that locator waits until the node is visible, stable,
  and able to receive events, using the 120-second timeout already set on the page.
- **Alternatives considered**: The brief's `page.get_by_text("נפה", exact=True)` on the
  outer page. Rejected — the visual is in the iframe. `page.locator("text='נפה'")` has
  the same frame limit and is a looser engine than `get_by_text` with `exact=True`.
  Scoping the text to `_visual_container(district title)`. Rejected — that container
  walk is what misses tabs that sit above the chart, outside the visual-container
  ancestor. Requiring role `button`, `tab`, or `option`. Rejected — the brief says the
  tabs are custom DOM and that role filter is why the tests skip.

## R3 — Normal click replaces the 045 force click

- **Decision**: Call `click()` with no `force=True`. Keep `_dismiss_overlay()` immediately
  before the click. Keep `_wait_for_level_selection` and the wait for
  `district_chart_title_for(level)`.
- **Rationale**: Feature 045 force-clicked a header control because the visual header
  toolbar sat on top of the pointer target. These tabs are large labels above the chart,
  not those header arrows. A force click skips the actionability wait the brief asks
  Playwright to perform. `_wait_for_level_selection` already treats a node with neither
  `aria-pressed` nor `aria-selected` as selected, which matches a custom text tab. The
  retitled chart (`התרעות לפי נפה` and the same pattern for the other two levels) remains
  the confirmation that the grain changed.
- **Alternatives considered**: Keep `click(force=True)` on the new text locator.
  Rejected — it bypasses the wait this slice is restoring. Drop the title wait.
  Rejected — a click on a duplicate text node could return before the chart grain
  changes, and the readers would compare the previous level.

## R4 — Remove the locator skip and keep the empty-chart skip

- **Decision**: Delete the `pytest.skip(... control not visible on district chart ...)`
  branch in `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg`. Assert that
  `set_hierarchy_level` returned true. Leave the following skip in both helpers:
  `District chart returned no rows for level {level!r} (chart empty or not rendered)`.
  Do not catch the click's timeout inside the page object.
- **Rationale**: Today `_hierarchy_control` returns `None`, `set_hierarchy_level` returns
  false, and both helpers skip with a message that claims the chart was not rendered.
  That path fires for a locator miss. The brief says to remove it and let the click wait.
  A false return still happens for an unknown level and for a title that never appears;
  asserting it makes those cases failures. The empty-row skip runs only after selection
  and is a different guard the brief left alone.
- **Alternatives considered**: Leave the skip and rely on the new locator always
  returning a control. Rejected — a future miss would skip again. Turn the empty-row
  skip into a failure. Rejected — the brief names the control-not-visible skip only.

## R5 — Settlement spelling and untouched surface

- **Decision**: Use `יישוב` from `_HIERARCHY_LEVEL_NAMES`. Do not add a locator for
  `ישוב`. Do not edit the YAML, `core/`, `db/`, `set_district_aggregation`, or the
  `מחוז` base level.
- **Rationale**: The page, the district title helper, and the earlier alerts specs all
  use `יישוב`. The brief lists that spelling first and uses `ישוב` only as shorthand
  in the locator example. `set_hierarchy_level` is the only caller of `_hierarchy_control`,
  and the only callers of `set_hierarchy_level` are the two sanity helpers.
- **Alternatives considered**: Accept either spelling with a regex. Rejected — `exact=True`
  on the real label is the brief's locator, and a regex would also match nearby words.
