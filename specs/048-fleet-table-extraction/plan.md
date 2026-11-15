# Implementation Plan: Centralize Show as a Table Extraction (Fleet MVP)

**Branch**: `feature/reportportal-integration` (spec directory `048-fleet-table-extraction`) | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/048-fleet-table-extraction/spec.md`

**Note**: This plan is filled by `/speckit-plan`. `tasks.md` is not created here.
`.specify/feature.json` points at this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). `specs/047-hierarchy-level-locators/` stays as it is.

## Summary

Fleet golden chart checks read segment names from SVG `<title>` and legend text
(`get_chart_segment_labels`) and then hover each segment for a tooltip count. Both
steps are fragile: names are dropped or doubled, and the tooltip often never opens,
so the test skips. Alerts and credit already use a more reliable path — right-click
the visual, choose `הצג כטבלה` / `Show as a table`, read the grid, click
`חזרה לדוח` / `Back to report` — but each page owns a private copy.

1. **Shared reader in Layer 2** — Add `VisualTable` in `core/components/visual_table.py`.
   `read_rows(container)` right-clicks the caller's locator, clicks the bilingual menu
   item, scrolls the `grid` or `table`, and returns `list[dict[str, str]]`. A `finally`
   clicks the bilingual back button whenever the table was opened. A pure
   `rows_to_label_values` maps rows to `dict[str, int]`. No fleet title or measure
   header is stored in this module. `ReportShell` is not edited: Layer 0 is portal
   chrome only, and this is a visual reader.
2. **Fleet extraction only** — `MainDashboardPage.read_chart_segments(chart_key)`
   dismisses a tooltip, calls `VisualTable` on `chart_section(chart_key)`, and maps
   rows with the total-row token `סה"כ`. The golden helper
   `assert_chart_matches` uses that mapping for names and counts and stops hovering
   for the count. Label-coverage helpers use the mapping's keys.
3. **Leave interaction on the canvas** — `get_chart_segment_labels`,
   `hover_chart_segment`, and `expand_chart_hierarchy` stay. Hierarchy code polls
   canvas labels every 200ms; opening the table there would leave the visual.
   Tooltip e2e checks still hover. Alerts and credit page objects are not edited.

Comments added inside these functions are English.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, Playwright (`Locator.click(button="right")`,
`get_by_role("menuitem")`, `get_by_role("grid"|"table")`, `get_by_role("button")`).
No new package.

**Storage**: Golden record `data/fleet/db_sanity_all.yaml` is read by the chart tests
and is not edited.

**Testing**: `pytest tests/unit/test_visual_table_rows.py` for the pure mapper (no
browser). `pytest tests/ui/fleet_dashboard/` is the smoke gate because Layer 2 and the
fleet page change. The golden chart tests
`pytest tests/sanity/fleet_dashboard/test_db_sanity.py -m sanity -k "unit_breakdown or pull_source or credit_reasons or category_actuals"`
are the data-extraction gate and need portal auth.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI
portal. The visual and its context menu are inside the report iframe, with a fallback
search on the outer page.

**Project Type**: Layer 2 visual reader plus a fleet page method. No new report, no
SQL, no golden-YAML edit.

**Performance Goals**: One table open per `read_chart_segments` call. Scroll stops
after two passes that add no row and do not move, bounded by the page timeout.
Hierarchy polling does not call this method.

**Constraints**:

- Reader lives in `core/components/visual_table.py`, not `ReportShell` (FR-001, AC-001).
- Menu and back labels are the bilingual exact strings in FR-002. No fleet literals in that module (FR-005).
- Rows are header → cell text. Integer mapping is the pure helper (FR-003, FR-006).
- Back click runs after a successful open, including on read failure (FR-004).
- Fleet method is `read_chart_segments(chart_key) -> dict[str, int]` on `chart_section` (FR-007).
- Canvas label harvest, hover, and expand stay (FR-008).
- Golden counts come from the table. Tooltip helpers still hover (FR-009).
- Alerts, credit, `core/portal/page.py`, YAML, and `db/` stay unchanged (FR-010).
- In-function comments are English (FR-011).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/visual_table.py` | NEW | `VisualTable.read_rows` and `rows_to_label_values` |
| `core/components/__init__.py` | EDIT | Export `VisualTable` |
| `pages/fleet_dashboard/main_dashboard_page.py` | EDIT | Add `read_chart_segments` only |
| `tests/unit/test_visual_table_rows.py` | NEW | Pure mapper, no browser |
| `tests/sanity/fleet_dashboard/test_db_sanity.py` | EDIT | Golden chart helper reads the table |
| `tests/ui/fleet_dashboard/dashboard_validation.py` | EDIT | Label-coverage helpers use the table keys |
| `core/portal/page.py` | UNCHANGED | |
| `get_chart_segment_labels`, `hover_chart_segment`, `expand_chart_hierarchy` | UNCHANGED | |
| alerts / credit / status-picture pages | UNCHANGED | |
| `data/fleet/db_sanity_all.yaml` | UNCHANGED | |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The new reader is Layer 2,
  composed by `MainDashboardPage` the same way `Slicer` is. The brief's
  `core.portal.page.ReportShell` example is rejected in research R2.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Fleet chart titles, the
  `סה"כ` skip token, and chart keys stay on the fleet page. Core stores only the
  generic menu and back phrases, the same class of chrome as Layer 2 "Clear all
  slicers" / "Search".
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Public methods
  `get_chart_segment_labels`, `hover_chart_segment`, `expand_chart_hierarchy`,
  `navigate`, and `get_kpi_value` keep their names and return types.
  `read_chart_segments` is additive. Fleet smoke
  (`tests/ui/fleet_dashboard/`) is a gate because Layer 2 and the fleet page change.
  The golden helper's count source changes in the same slice, so a tooltip miss is
  no longer a skip on those four tests.
- **Page object discipline (IV)**: PASS. Tests call `read_chart_segments` on the
  page. They do not open the context menu themselves.
- **Warehouse as source of truth (V)**: PASS. This slice does not open SQL and does
  not edit the golden YAML. Chart tests still compare UI values to
  `data/fleet/db_sanity_all.yaml`.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay. A missing
  menu or back button raises, so the failure is reported. The table is closed first.
- **Extract shared behavior only (VII)**: PASS. Show as a table is generic visual
  chrome, so it belongs in `core/components/` with the other visual readers. Hover,
  tooltips, and drill-down stay on the fleet page. Alerts and credit are not
  migrated in this slice; the new API is used by fleet in the same change.

**Result**: No unjustified violations. Phase 0 may proceed.

## Project Structure

### Documentation (this feature)

```text
specs/048-fleet-table-extraction/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── visual-table.md
│   └── fleet-chart-table.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
core/components/visual_table.py
      ├── VisualTable(page, frame, timeout_ms)
      ├── read_rows(container, *, name="visual") -> list[dict[str, str]]
      └── rows_to_label_values(rows, *, skip_labels=()) -> dict[str, int]

core/components/__init__.py
      └── export VisualTable

pages/fleet_dashboard/main_dashboard_page.py
      ├── read_chart_segments(chart_key) -> dict[str, int]    # NEW
      ├── get_chart_segment_labels(chart_key)                 # UNCHANGED canvas harvest
      ├── hover_chart_segment(...)                            # UNCHANGED
      └── expand_chart_hierarchy(...)                         # UNCHANGED

tests/unit/test_visual_table_rows.py                         # pure mapper
tests/sanity/fleet_dashboard/test_db_sanity.py               # assert_chart_matches
tests/ui/fleet_dashboard/dashboard_validation.py             # label-coverage helpers only
```

**Structure Decision**: The menu workflow is generic Power BI chrome, so it lives in
Layer 2 beside `Chart` and `Slicer`. `Chart` keeps the SVG/legend reader used by
other reports and is not the place for a mode switch that leaves the canvas. The
fleet page owns chart keys, the right-click host, and the total-row token. Hierarchy
and hover stay in the existing fleet methods so a label poll never opens the table.

## Complexity Tracking

> No constitution violations require justification. The table is empty on purpose.
> Placing the reader on `ReportShell` would violate Principles I and VII; that
> placement is not used.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- `VisualTable` is constructed with the Playwright page and the fleet report iframe
  (`self.dashboard`). It does not subclass `ReportShell`. `core/portal/page.py` is
  not edited.
- Chrome literals inside the new module are only `הצג כטבלה`, `Show as a table`,
  `חזרה לדוח`, and `Back to report`. Fleet titles stay in `_CHART_TITLES`. The
  total-row token is an argument from `read_chart_segments`.
- `read_rows` returns string cells. `rows_to_label_values` is the only integer parse.
  `read_chart_segments` returns `dict[str, int]` in first-seen order.
- `get_chart_segment_labels`, `hover_chart_segment`, and `expand_chart_hierarchy`
  are not rewritten. `wait_for_chart_labels_change` still polls the canvas method.
- `assert_chart_matches` reads the new mapping and does not call
  `hover_chart_segment`. `assert_chart_tooltip_segment_matches_db` and
  `assert_chart_tooltips_match_db_sample` still hover.
- Alerts and credit modules are not on the edit list. Fleet smoke remains the gate
  for the Layer 2 and fleet-page edit.
- In-function comments stay English.

**Result**: No unjustified violations.
