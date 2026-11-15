# Implementation Plan: Population Hour Sum and Clear Baseline

**Branch**: `feature/reportportal-integration` (spec directory `023-population-hour-clear`) | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/023-population-hour-clear/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Feature 022's tight chart container stays.
This slice drops the hour-chart average from the total and makes the clear test baseline
the state after the first clear.

## Summary

The hour total returned `5895.54`, the average line on that chart, instead of the integer bars.
`chart_total` for the hour chart will skip a series whose name contains `ממוצע` and will skip a
fractional float. Integer bars stay.

The clear test stored the snapshot at arrival, while the report still had its default filters
(warned `10136795`). Clear removes those filters (warned `10142584`, equal to the total
population). The test will clear first, store that snapshot, apply its filters, clear again, and
compare with the cleared baseline.

`core/` is not edited. The snapshot helper still calls `chart_total`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: The series names already returned by `Chart._parse`. No new package.
No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Auth
state is required. Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object and one population UI test.

**Performance Goals**: N/A. One extra clear at the start of one test.

**Constraints**:

- **No `core/` edit** (FR-006, AC-005).
- **Hour chart only** for the average skip (FR-001, FR-002). Dates, district, and settlement totals stay.
- **Do not add 0 for a skipped average** (FR-003).
- **Snapshot helper stays a caller** (FR-007).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Hour total skips `ממוצע` and fractional floats |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | EDIT | Clear once before the baseline snapshot |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | Parser stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `ממוצע` stays on the population page.
- **Existing tests are the contract (III)**: PASS for this slice. The clear test's steps change because the arrival state is not the unfiltered state. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `clear_filters`, `set_between_dates`, `set_day_night`, `set_value_range`, and `take_snapshot`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The average skip is page-local because the generic reader must not change in this slice.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/023-population-hour-clear/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── hour-and-clear.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # hour chart: skip ממוצע and fractional floats

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_clear_restores_population_snapshot()   # clear, snapshot, filter, clear, compare

core/                                    # UNCHANGED
```

**Structure Decision**: Keep the average rule inside `chart_total` so the snapshot, the day/night
test, and the three-chart test share it. Change only the clear test's order of calls.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The clear test no longer treats arrival as the restored state | Arrival still has the report's default filters. Clear removes them, so the two states differ by design. | Asserting arrival against the cleared page fails on the live warned card (`10136795` versus `10142584`). |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The hour total skips `ממוצע` and fractional floats. Integer bars remain. A chart with no integer bar still fails.
- The clear test clears before the baseline.
- `population_snapshot.py` is unchanged.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.

## Phase 0 / Phase 1 Outputs

- [research.md](./research.md)
- [data-model.md](./data-model.md)
- [contracts/hour-and-clear.md](./contracts/hour-and-clear.md)
- [quickstart.md](./quickstart.md)
