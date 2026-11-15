# Implementation Plan: Visible Dates Table Rows

**Branch**: `feature/reportportal-integration` (spec directory `029-dates-visible-rows`) | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/029-dates-visible-rows/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The hour and district readers stay.
This slice sums only the visible dates-table rows after they settle.

## Summary

Manual reading of the filtered dashboard shows 13 for the hour chart, the district chart,
and the dates table. `chart_total` for the dates chart returns 5847.

`_dates_table_total` currently calls `_sum_scrolled_alert_column`, which reads every row
`evaluate_all` can see and scrolls for more. Hidden rows that Power BI has filtered out
stay in the DOM. The dates total will wait until the visible `התרעות` integers repeat,
then add only rows that pass `is_visible()`. It will not scroll. The three-chart test
stays a strict equality and carries no `pytest.mark.xfail`. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright `Locator.is_visible()` and `get_by_role`, already used
on the population page. No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object. The three-chart test loses any expected-fail mark and keeps its date strings.

**Performance Goals**: N/A. One settle poll of the visible column, then one sum.

**Constraints**:

- **No `core/` edit** (FR-008, AC-005).
- **Dates chart only** (FR-006). Hour and district readers stay.
- **Visible rows only** (FR-003). `is_visible()` is the check.
- **No scroll** (FR-004). `_sum_scrolled_alert_column` is not the dates total.
- **Settle before summing** (FR-002).
- **No xfail** (FR-007). The date strings in the test stay `01/09/2026` and `15/10/2026`.
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Dates total waits, then sums visible rows only |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | EDIT | Remove `pytest.mark.xfail` if it is present. Keep the strict equality and the current date strings |
| `core/` | UNCHANGED | `Chart` stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `הצג כטבלה`, `התרעות`, `סה"כ`, and `חזרה לדוח` stay on the population page.
- **Existing tests are the contract (III)**: PASS. The three-way equality stays strict. An expected-fail mark is removed when present. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `chart_total`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The visibility check is page-local because this slice must not change the generic chart reader.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/029-dates-visible-rows/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── visible-rows.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # dates: visible settled rows; hour and district stay

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # strict equality, no xfail

core/                                    # UNCHANGED
```

**Structure Decision**: Replace the scrolled dates sum inside `_dates_table_total` on
`AlertsPopulationPage`. Leave `_svg_mark_total` for `HOUR_CHART` and `_rows_for_total` for
`DISTRICT_CHART`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The dates total ignores hidden DOM rows | Power BI keeps filtered rows in the HTML. Scrolling and `evaluate_all` add those rows and return 5847. | Summing every DOM row keeps the stale total. Teaching `Chart` about this table would edit `core/`. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The dates total waits until the visible `התרעות` integers repeat, then adds only rows that pass `is_visible()`.
- A header and a `סה"כ` row are omitted. The table is not scrolled.
- `חזרה לדוח` still runs before the method returns.
- The hour SVG reader and the district reader are unchanged.
- The three-chart test keeps `01/09/2026` and `15/10/2026`, keeps `hour_total == district_total == dates_total`, and has no `pytest.mark.xfail`.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
