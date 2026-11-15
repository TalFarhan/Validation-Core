# Implementation Plan: Population Chart SVG Aria Labels

**Branch**: `feature/reportportal-integration` (spec directory `024-population-svg-aria`) | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/024-population-svg-aria/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Feature 022's tight chart container stays.
This slice reads dates and hour totals from SVG `aria-label` values on the population page.

## Summary

`test_hour_date_and_district_sums_match` failed on 2026-10-15 with `141493 == 0`.
`141493` is the hour-chart average `5895.54` times 24. The hour reader summed option text
that carried that average. The dates reader summed text nodes and returned `0`. The bar
values sit on SVG mark `aria-label` attributes. `inner_text` cannot read those nodes.

`chart_total` for the dates chart and the hour chart will read `aria-label` from `svg rect`
and `svg path` inside the existing visual container. A label containing `ממוצע` or a float
is skipped. The remaining integers are summed. An image role is used only when the shapes
yield no integer, so one bar is not added twice.

District and settlement totals stay on their current readers. `core/` is not edited.
The snapshot helper still calls `chart_total`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright locators already used by the population page. No new package.
No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object. The population test file is not edited.

**Performance Goals**: N/A. One attribute read per SVG mark on two charts.

**Constraints**:

- **No `core/` edit** (FR-008, AC-005).
- **Dates and hour only** (FR-001, FR-007). District and settlement totals stay.
- **No `inner_text` on these marks** (FR-002).
- **Do not add 0 for a skipped average or float** (FR-003, FR-004, FR-006).
- **Snapshot helper stays a caller** (FR-009).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Dates and hour totals come from SVG `aria-label` values |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | UNCHANGED | The three-chart test stays the gate |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | `Chart` stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `ממוצע` and the chart titles stay on the population page.
- **Existing tests are the contract (III)**: PASS. `test_hour_date_and_district_sums_match` is unchanged and is the gate. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `chart_total`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The SVG label rule is page-local because this slice must not change the generic chart reader.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/024-population-svg-aria/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── svg-aria-total.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # dates and hour: sum SVG aria-label integers

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # UNCHANGED gate

core/                                    # UNCHANGED
```

**Structure Decision**: Keep the SVG reader on `AlertsPopulationPage` and call it from
`chart_total` for `DATES_CHART` and `HOUR_CHART`. The option-text hour reader is replaced
by that method. District and settlement totals keep the readers they have now.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| A page-local SVG label parser sits beside `Chart._parse` | `inner_text` misses the bar nodes, and the option-text fallback summed the average line (`141493`). This slice must not change `Chart`. | Teaching `Chart._parse` to prefer these `aria-label` values would edit `core/`. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- Dates and hour totals read `aria-label` on SVG marks. `inner_text` is not used for those marks.
- A label containing `ממוצע` or a float is omitted and is not stored as `0`.
- No included integer still fails the total.
- District and settlement totals are unchanged.
- `population_snapshot.py` and the three-chart test are unchanged.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
