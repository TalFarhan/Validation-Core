# Implementation Plan: Dates Chart Accessible Table

**Branch**: `feature/reportportal-integration` (spec directory `026-dates-accessible-table`) | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/026-dates-accessible-table/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The hour SVG reader and the district reader stay.
This slice totals the dates chart from the accessible table opened by `Alt+Shift+F11`.

## Summary

The hour total and the district total are both `141493`. The dates total is `0` because the
visible circles are the zoomed days, and those days have no alerts. Scrolling the zoom slider
is not the approach.

`chart_total` for the dates chart will click that chart's visual container, press
`Alt+Shift+F11`, wait for the grid or table that has an `התרעות` column, sum those integer
cells, skip the header and any `סה"כ` row, then press the back control and wait until the
dates chart is visible again. The hour and district branches of `chart_total` stay as they
are. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright `click`, `keyboard.press`, and `expect` already used by
the population page. No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object. The population test file is not edited.

**Performance Goals**: N/A. One shortcut, one table read, and one back click for the dates total.

**Constraints**:

- **No `core/` edit** (FR-008, AC-005).
- **Dates chart only** for the table (FR-001, FR-006). Hour and district readers stay.
- **Do not sum the zoomed circles for this chart** (FR-007).
- **Close the table before returning** (FR-005).
- **Snapshot helper stays a caller** (FR-009).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Dates total comes from the accessible table |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | UNCHANGED | The three-chart test stays the gate |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | `Chart` stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `התרעות`, `סה"כ`, and `חזרה` stay on the population page.
- **Existing tests are the contract (III)**: PASS. `test_hour_date_and_district_sums_match` is unchanged and is the gate. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `chart_total`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The shortcut and the table read are page-local because this slice must not change the generic chart reader.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/026-dates-accessible-table/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── dates-table.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # dates: accessible table; hour and district stay

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # UNCHANGED gate

core/                                    # UNCHANGED
```

**Structure Decision**: Add a dates-only table reader on `AlertsPopulationPage` and call it
from `chart_total` when the title is `DATES_CHART`. Leave the hour call to `_svg_mark_total`
and the district call to `_rows_for_total`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The dates total opens a Power BI table instead of reading marks | The visible circles are the zoomed window, and those days are `0`. The full series is in the accessible table. | Dragging the zoom slider is a brittle coordinate gesture. Teaching `Chart` the shortcut would edit `core/`. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The dates total focuses the chart, opens the accessible table, sums the `התרעות` column, and goes back.
- The header and a `סה"כ` row are omitted.
- The hour SVG reader and the district reader are unchanged.
- The table is closed before `chart_total` returns.
- `population_snapshot.py` and the three-chart test are unchanged.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
