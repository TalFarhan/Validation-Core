# Implementation Plan: Dates Table from the Right-Click Menu

**Branch**: `feature/reportportal-integration` (spec directory `027-dates-table-menu`) | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/027-dates-table-menu/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The hour SVG reader and the district reader stay.
This slice opens the dates data table from the right-click menu.

## Summary

`Alt+Shift+F11` did not open a data table with integer alert cells. The hour total and the
district total are both `141493`.

`chart_total` for the dates chart will right-click that chart's visual container, click
`הצג כטבלה` (or `Show as a table`), wait for rows, sum the `gridcell` values under the
`התרעות` column header, skip a `סה"כ` row, then click `חזרה לדוח` and wait until the dates
chart is visible again. The hour and district branches stay. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright `click(button="right")` and `get_by_role` already used
by the population page. No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object. The population test file is not edited.

**Performance Goals**: N/A. One right-click, one menu click, one table read, and one back click.

**Constraints**:

- **No `core/` edit** (FR-008, AC-005).
- **Dates chart only** (FR-001, FR-006). Hour and district readers stay.
- **No `Alt+Shift+F11`** (FR-007).
- **Do not dismiss the context menu before the menu item is clicked**.
- **Close the table before returning** (FR-005).
- **Snapshot helper stays a caller** (FR-009).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Dates total opens the table from the right-click menu |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | UNCHANGED | The three-chart test stays the gate |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | `Chart` stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `הצג כטבלה`, `התרעות`, `סה"כ`, and `חזרה לדוח` stay on the population page.
- **Existing tests are the contract (III)**: PASS. `test_hour_date_and_district_sums_match` is unchanged and is the gate. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `chart_total`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The menu and the table read are page-local because this slice must not change the generic chart reader.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/027-dates-table-menu/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── dates-menu-table.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # dates: right-click menu table; hour and district stay

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # UNCHANGED gate

core/                                    # UNCHANGED
```

**Structure Decision**: Replace the keyboard shortcut inside the dates-only reader on
`AlertsPopulationPage`. Leave `_svg_mark_total` for `HOUR_CHART` and `_rows_for_total` for
`DISTRICT_CHART`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The dates total uses the visual's context menu | `Alt+Shift+F11` did not open a table with integer cells. The menu item is the same Power BI command. | Sending the shortcut again leaves the dates total unread. Teaching `Chart` the menu label would edit `core/`. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The dates total right-clicks the chart, clicks `הצג כטבלה`, sums the `התרעות` grid cells, and clicks `חזרה לדוח`.
- A `סה"כ` row is omitted.
- The hour SVG reader and the district reader are unchanged.
- The table is closed before `chart_total` returns.
- `population_snapshot.py` and the three-chart test are unchanged.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
