# Implementation Plan: Scroll the Dates Table and Filter District Rows

**Branch**: `feature/reportportal-integration` (spec directory `030-scroll-visible-totals`) | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/030-scroll-visible-totals/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The hour reader stays.
This slice scrolls the dates table and applies `is_visible()` to the district total.

## Summary

On 2026-10-18 the filtered dashboard shows 13 for the hour chart, the dates table, and the
district chart. The automation returned hour `13`, dates `11`, and district `5847`.

The dates total reads only the first viewport. Power BI virtualizes the remaining rows, so
the page will scroll that table and add each `is_visible()` row once. The district total
currently sums `_rows_for_total` with no visibility check, which is how hidden DOM content
becomes `5847`. The district branch will wait until the visible rows repeat and will ignore
rows that fail `is_visible()`. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright `Locator.is_visible()` and the population page's
existing table scroll. No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object. The three-chart test stays strict.

**Performance Goals**: N/A. The dates scroll stops at the end of the table or at `self.timeout`.

**Constraints**:

- **No `core/` edit** (FR-008, AC-005).
- **Dates scroll plus visibility** (FR-002, FR-003). Hidden rows stay out. One row is stored once.
- **District visibility and settle** (FR-004). The unfiltered `_rows_for_total` sum is not the district total.
- **Hour stays** on `_svg_mark_total` (FR-006).
- **No xfail** (FR-007). Date strings stay `01/09/2026` and `15/10/2026`.
- **Close the dates table** with `חזרה לדוח` (FR-009).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Scroll the dates table; filter the district total by `is_visible()` |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | UNCHANGED | Strict equality and the current date strings stay |
| `core/` | UNCHANGED | `Chart.read` stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The chart titles and `התרעות` stay on the population page.
- **Existing tests are the contract (III)**: PASS. The three-way equality stays strict. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `chart_total`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. Visibility and scrolling stay on the population page because this slice must not change `Chart`.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-scroll-visible-totals/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── scroll-visible.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # dates: scroll visible rows; district: visible settled rows

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # UNCHANGED assertion and dates

core/                                    # UNCHANGED
```

**Structure Decision**: Change the dates and district branches of `chart_total` on
`AlertsPopulationPage`. Leave `_svg_mark_total` for `HOUR_CHART` and `_rows_for_total`
for `SETTLEMENT_CHART`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The district total no longer uses `_rows_for_total` | That sum has no `is_visible()` check and returned `5847` while the visual shows `13`. | Editing `Chart.read` would change `core/`. Leaving the district branch unchanged keeps the hidden rows. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The dates total scrolls, stores each visible row once, and skips hidden rows.
- The district total waits for a repeated visible sum and skips hidden rows.
- The hour SVG reader and the settlement reader are unchanged.
- The three-chart test keeps its date strings, its equality, and has no `pytest.mark.xfail`.
- `חזרה לדוח` still runs before the dates total returns.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
