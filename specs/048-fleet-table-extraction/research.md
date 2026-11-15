# Phase 0 Research: Centralize Show as a Table Extraction (Fleet MVP)

All Technical Context items are known from `MainDashboardPage`, the alerts and credit
Show as a table helpers, `core/components/chart.py`, and the constitution. No
**NEEDS CLARIFICATION** remains.

## R1 — Which feature directory this plan belongs to

- **Decision**: Plan this slice as `specs/048-fleet-table-extraction`. Repoint
  `.specify/feature.json` at that directory. Leave the git checkout on
  `feature/reportportal-integration`. Leave `specs/047-hierarchy-level-locators/`
  unchanged.
- **Rationale**: Setup initially resolved the pinned feature to the hierarchy-locator
  plan. The brief is fleet Show as a table extraction. Writing it into 047 would
  replace an unrelated plan. Recent slices in this repo keep the same git branch and
  use a new spec directory. The branch-name check in `setup-plan.ps1` passes once the
  directory exists, because `feature.json` pins it.
- **Alternatives considered**: Fill `specs/047-hierarchy-level-locators/plan.md` again.
  Rejected — that spec is the alerts hierarchy tabs. Create a new git branch. Rejected
  — this repo's current slices explicitly stay on `feature/reportportal-integration`.

## R2 — Layer 2, not ReportShell

- **Decision**: New module `core/components/visual_table.py`. `MainDashboardPage`
  constructs `VisualTable(page, frame, timeout_ms)` the same way it constructs
  `Slicer`. `core/portal/page.py` is not edited.
- **Rationale**: Constitution I limits Layer 0 to login/SSO, catalog search, iframe
  wait, visual-loading timeouts, and last-refresh verification. Constitution VII
  allows generic visual readers in Layer 2 (`core/components/`). Show as a table is
  a visual read, not portal chrome. The menu strings are generic Power BI chrome,
  the same class as the Layer 2 clear-all and search phrases. The brief says
  "a shared, reusable method in `core` (e.g., inside `ReportShell`)". The example
  is the part that fails the gate. "In `core`" is satisfied by Layer 2.
- **Alternatives considered**: Methods on `ReportShell`. Rejected — it widens Layer 0
  past portal steps and would need a Complexity Tracking exception. Methods on
  `Chart`. Rejected — `Chart.read` is the SVG/legend path, and its module docstring
  keeps tooltips and drill-down off Layer 2. A mode switch that leaves the canvas
  does not belong inside `read`. Copying the alerts helpers into the fleet page
  only. Rejected — the brief asks for a shared method, and the menu workflow is
  already duplicated on alerts and credit.

## R3 — Raw rows in core, integers on a pure helper

- **Decision**: `read_rows` returns `list[dict[str, str]]` in header order.
  `rows_to_label_values(rows, *, skip_labels=())` returns `dict[str, int]`.
  The fleet page passes `skip_labels=("סה\"כ",)`.
- **Rationale**: Alerts `_visual_table_map` returns `dict[str, int]` for one
  hardcoded measure column (`התרעות`) and swallows errors into `{}`. Credit
  `_show_as_table_rows` returns string rows and also swallows errors. The reusable
  piece is the string grid. Choosing a measure column, dropping a Hebrew total row,
  and parsing pie labels are caller policy. A pure function can be unit-tested
  without Playwright, matching `tests/unit/test_chart_shape.py`. First-seen label
  wins. `0` is a value. A cell that is only a percent is not the count. A cell
  shaped like `name N` or `name N (P%)` contributes the name as the label and `N`
  as the count when no pure integer cell is present. That is the pie pattern
  feature 042 already keeps for credit reasons.
- **Alternatives considered**: Return `dict[str, int]` from `read_rows` directly.
  Rejected — it forces a column choice into core. Swallow failures and return `[]`,
  as credit does. Rejected — a missing menu would look like an empty chart and the
  golden test would skip. This slice raises `AssertionError` instead, and still
  leaves the table when it was opened.

## R4 — Scroll the grid

- **Decision**: After the grid is visible, scroll its scrollable ancestor from the
  top in page steps. Dedupe rows by the tuple of cell texts. Stop when two passes
  add nothing and the scroll position does not move, or when the timeout is hit.
  There is no separate scroll-to-end pass.
- **Rationale**: Alerts dates work (specs 029, 030, 038) showed that a Power BI
  visual table virtualizes. Credit reads only the current viewport, which is enough
  for its smaller charts and wrong for the fleet unit breakdown. The stop rule is
  the alerts rule, applied to full rows instead of one integer column. Header rows
  and rows whose cells equal the header texts are not data.
- **Alternatives considered**: Visible rows only. Rejected for the unit chart.
  Reuse `Chart._texts` on the canvas. Rejected — that is the fragile path this
  slice replaces for extraction.

## R5 — Menu search and teardown

- **Decision**: Search `frame` then `page` for an exact visible `menuitem`, Hebrew
  then English, with a short wait per candidate so the second label still gets the
  remaining timeout. Same search for the back `button`. Right-click the locator the
  caller passed. Do not look up a title inside core. After the back click, wait
  until that back button is hidden. The fleet page calls `dismiss_tooltip()` before
  `read_rows` so an open tooltip does not cover the visual.
- **Rationale**: Both alerts `_click_show_as_table` and credit `_show_as_table_rows`
  search the report frame and the outer page, because Power BI sometimes mounts the
  menu outside the iframe. Feature 045 showed that leaving Show as a table open
  makes the next test time out. The back click belongs in `finally` on `read_rows`.
  Waiting for a chart title inside core would leak a domain string. The back button
  disappearing is report-agnostic.
- **Alternatives considered**: Click only inside the frame. Rejected — the existing
  helpers already needed the outer page. Wait for `chart_section` to be visible
  again inside `VisualTable`. Rejected — the caller can do that; core does not
  receive the chart key.

## R6 — Do not retarget `get_chart_segment_labels`

- **Decision**: Add `read_chart_segments`. Leave `get_chart_segment_labels`,
  `hover_chart_segment`, and `expand_chart_hierarchy` as they are.
  `wait_for_chart_labels_change`, `drill_up_chart`, `reset_chart_hierarchy`, and
  `expand_via_tooltip_drilldown` keep calling the canvas method.
- **Rationale**: `expand_chart_hierarchy` snapshots labels and then polls every
  200ms until they change. `get_chart_segment_labels` is also what
  `tests/e2e/test_chart_drilldown.py` uses as a before/after canvas snapshot.
  Opening Show as a table on that path would switch the visual out of chart mode
  and fight the hover that expand still performs. The brief says those interaction
  methods stay. Constitution III keeps their signatures. Extraction callers are a
  different set: `assert_chart_matches`, `assert_chart_labels_match_db_sample`, and
  `assert_unit_drilldown_matches_db`.
- **Alternatives considered**: Implement `get_chart_segment_labels` with the table
  and point the poll at a new private canvas method. Rejected — it edits
  `expand_chart_hierarchy` and every drill caller for no extraction benefit.
  Fallback from the table to SVG when the menu is missing. Rejected — that hides
  the failure this slice is meant to surface.

## R7 — Which tests change source

- **Decision**: `assert_chart_matches` takes both the label set and the integer from
  `read_chart_segments`. It no longer calls `hover_chart_segment` or
  `parse_tooltip_entries`. A golden name that is absent still fails once any golden
  name was present, and still skips when none of the golden names were present.
  A present name with a different integer fails. The "no tooltip appeared" skip is
  removed from this helper only. `assert_chart_labels_match_db_sample` and
  `assert_unit_drilldown_matches_db` use the mapping keys. Tooltip helpers
  `assert_chart_tooltip_segment_matches_db` and
  `assert_chart_tooltips_match_db_sample` keep hovering and keep their SVG presence
  check.
- **Rationale**: The four golden tests are the fragile SVG-plus-hover path
  (`test_ui_unit_breakdown_matches_golden`, `test_ui_pull_source_matches_golden`,
  `test_ui_credit_reasons_match_golden`, `test_ui_category_actuals_match_golden`).
  Label coverage after a drill is a one-shot read, so the table is safe there.
  Tooltip tests exist to prove hover. The brief keeps hover for those checks.
- **Alternatives considered**: Leave `assert_chart_matches` on hover and only add
  the page method. Rejected — the golden counts would still depend on the tooltip.
  Switch the tooltip e2e tests to the table. Rejected — those tests are the hover
  contract.

## R8 — What stays unedited

- **Decision**: Do not edit `pages/alerts_analysis/population_page.py`,
  `pages/credit_consumption/credit_consumption_page.py`, `core/portal/page.py`,
  `core/components/chart.py`, `data/fleet/db_sanity_all.yaml`, or `db/`.
- **Rationale**: Phase 1 verifies the shared reader on fleet before other suites
  move. Alerts and credit keep the behavior their specs already locked.
  `Chart` remains the SVG reader for callers that still want it. The golden file
  is the recorded source, not a file this slice corrects.
- **Alternatives considered**: Migrate alerts `_visual_table_map` in the same
  change. Rejected — the brief says not to modify other page objects yet, and that
  helper's scroll, column, and empty-dict behavior is specified by earlier alerts
  features.
