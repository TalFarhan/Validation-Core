# Implementation Plan: Population Date Range for the Three-Chart Total

**Branch**: `feature/reportportal-integration` (spec directory `028-population-date-range`) | **Date**: 2026-10-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/028-population-date-range/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The hour, dates, and district readers stay.
This slice sets an explicit date range before those readers run.

## Summary

On 2026-10-15 the dates menu table summed to `140493` and the hour chart summed to `141493`.
No summary row and no unparsed cell explained the `1000` gap. The default date slider can
leave one chart on a different window.

`test_hour_date_and_district_sums_match` will clear filters, call `set_date_range` with
`01/01/2020` and today's day/month/year value, wait until the total card settles, set
district Sum, then assert `hour_total == district_total == dates_total`. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright locators already used by `set_between_dates` and
`clear_filters` on the population page. No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object plus one existing population test.

**Performance Goals**: N/A. Two date fields and a settle wait before the three chart reads.

**Constraints**:

- **No `core/` edit** (FR-007, AC-005).
- **Date fields stay the existing pair** `תאריך התחלה` and `תאריך סיום` (FR-002).
- **Wait until the total card repeats** (FR-003).
- **Clear first, then the wide range, then Sum, then the three reads** (FR-004).
- **Strict equality. No expected-fail** (FR-005).
- **Readers stay** (FR-006). The dates total still comes from the menu table.
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Add `set_date_range` and the settle wait |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | EDIT | Apply the wide range, then assert the three totals |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | Slicer chrome stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `תאריך התחלה` and `תאריך סיום` stay on the population page.
- **Existing tests are the contract (III)**: PASS. The three-way equality stays strict and the test is updated in this same slice. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test calls `set_date_range` on the page object. The date locators stay on that page.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The date labels are page-local because this slice must not change the generic slicer.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/028-population-date-range/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── date-range.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── set_date_range()                 # start, end, then a settled total card

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # wide range, then strict equality

core/                                    # UNCHANGED
```

**Structure Decision**: Add `set_date_range` on `AlertsPopulationPage`. It fills the same
inputs as `set_between_dates`, then waits the way `clear_filters` waits. The three-chart
test calls it after `clear_filters` and before the totals.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The three-chart test changes its setup | The default date slider can leave the dates total `1000` below the hour total. | Marking the test expected-fail would hide that filter. Changing the dates parser would ignore a range the page can set. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- `set_date_range("01/01/2020", <today DD/MM/YYYY>)` commits both date fields and waits for a repeated total-card read.
- The test clears first, applies that range, sets district Sum, and asserts `hour_total == district_total == dates_total`.
- The hour SVG reader, the dates menu-table reader, and the district reader are unchanged.
- `population_snapshot.py` is unchanged.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
