# Implementation Plan: Population Invariant Fix

**Branch**: `feature/reportportal-integration` (spec directory `021-population-invariant-fix`) | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/021-population-invariant-fix/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration`). Feature 019 stays the population page. Feature 020's
canvas host stays as it is. This slice only changes how that page sums a chart and how it clicks Sum.

## Summary

Two population tests still fail after the canvas host:

- `chart_total` raises when the dates chart or the hour chart includes a settlement name whose
  selected cell is `None`.
- `set_district_aggregation("sum")` can see two buttons labeled `סכום` and then either hits strict
  mode or waits on a group that does not contain the button.

The fix stays on `AlertsPopulationPage`:

- Sum only cells that are `int` or `float`. Skip every other cell. Do not add 0 for a skip. Fail
  when the series has no numeric cell or the chart is empty.
- Click Sum with a one-element locator: the button inside the district chart container when it
  exists, otherwise the exact-name button's `.first`.

`population_snapshot.py` keeps calling `chart_total`. No file under `core/` is edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: The existing `Chart.read` result (`ChartCategory.values`) and Playwright
`Locator.first`. No new package.

**Storage**: N/A.

**Testing**: `pytest` on `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Auth
state is required. No fleet run in this slice, because `core/` is not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object under `pages/alerts_analysis/`.

**Performance Goals**: N/A. One chart read and one button click.

**Constraints**:

- **No `core/` edit** (FR-005, AC-005). Not `chart.py`, not `visual.py`, not the parity engine.
- **Do not add 0 for an empty cell** (FR-002). Skipping is not the same as substituting 0.
- **One click target** (FR-004). A locator that matches two buttons is not clicked as a set.
- **Snapshot stays a caller** (FR-006).
- Inline comments in edited Python MUST be English.

**Scale/Scope**: `chart_total` and `set_district_aggregation` in
`pages/alerts_analysis/population_page.py`.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Numeric-only total; one Sum click |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | Host and chart reader stay as feature 020 left them |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Sum and the chart titles stay on the
  population page. `core/` gains no label.
- **Existing tests are the contract (III)**: PASS for this slice. Layer 0 and Layer 2 are not
  edited, so fleet smoke is not a gate here. The population invariant file is the gate.
- **Page object discipline (IV)**: PASS. The test body still calls page methods. The snapshot
  helper still calls page methods.
- **Warehouse as source of truth (V)**: PASS. No SQL. These tests do not open the database.
- **Observability (VI)**: PASS. Run reports, screenshots, and traces stay as they are.
- **Extract shared behavior only (VII)**: PASS. The numeric filter is page-local because the
  generic chart reader must not change in this slice.

**Result**: No unjustified violations. The page-local sum rule is recorded below because feature
019 originally failed the total when any cell was missing.

## Project Structure

### Documentation (this feature)

```text
specs/021-population-invariant-fix/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── population-total.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  ├── chart_total(title, series_index=0)     # numeric cells only
  └── set_district_aggregation(mode)         # one Sum or average button

tests/ui/alerts_analysis_dashboard/population_snapshot.py   # UNCHANGED
tests/ui/alerts_analysis_dashboard/test_population_invariants.py   # UNCHANGED; the gate
core/                                                               # UNCHANGED
```

**Structure Decision**: Keep the sum on `chart_total` so the snapshot, the day/night test, and the
three-chart test share one rule. Do not parse categories again in the snapshot helper.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Page total skips an empty cell, which is looser than feature 019's "any missing cell fails the sum" | The dates and hour charts currently include a settlement name with no number. The user forbids changing the generic reader. | Editing `core/components/chart.py` to drop that label would fix every report and violates the request. Substituting 0 would change the identity the tests check. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The contract changes only `chart_total` and `set_district_aggregation`.
- Empty cells are omitted. They are not stored as 0. A series with no number still fails.
- The Sum click is `.first` when the chart container has no single button.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.

## Phase 0 / Phase 1 Outputs

- [research.md](./research.md)
- [data-model.md](./data-model.md)
- [contracts/population-total.md](./contracts/population-total.md)
- [quickstart.md](./quickstart.md)
