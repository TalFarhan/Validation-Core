# Implementation Plan: Bound the Global Invariant Tests by Date

**Branch**: `feature/reportportal-integration` (spec directory `031-invariant-date-bounds`) | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/031-invariant-date-bounds/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The population page and `core/` stay as they are.
This slice applies the existing date range inside two invariant tests.

## Summary

`test_day_plus_night_equals_untoggled_sum` and `test_clear_restores_population_snapshot`
read the dates chart with no date window. That chart is a virtualized table of more than
11,000 rows, and the run hits a 13-minute timeout. Both tests keep their business checks.
Each one calls the existing `set_date_range("01/09/2026", "15/10/2026")` before those reads.
The clear test calls it again immediately after `clear_filters()` and before the after
snapshot. Neither test gains `pytest.mark.xfail`. `core/` and `pages/` are not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `AlertsPopulationPage.set_date_range` and `clear_filters`, already
on the population page. No new package. No edit under `core/` or `pages/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_day_plus_night_equals_untoggled_sum` and
`test_clear_restores_population_snapshot`. Auth state is required. Fleet smoke is not a
gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Two existing population invariant tests.

**Performance Goals**: Each dates read stays inside the bounded window so the suite does not
scan the unfiltered table of more than 11,000 rows.

**Constraints**:

- **No `core/` edit and no `pages/` edit** (FR-007, AC-002, AC-005).
- **Call `set_date_range`**, not a new `filter_dates` (FR-001, FR-007).
- **Call `clear_filters`**, not a new `clear_all_filters` (FR-007).
- **Day/night range before the untoggled total** (FR-001). Assertion stays `day + night == untoggled` (FR-002).
- **Clear test range before the before snapshot, and again after `clear_filters()` before the after snapshot** (FR-003, FR-004).
- **Keep the clear test's mutations** `set_between_dates("01/09/2026", "01/10/2026")`, day, night, and `set_value_range(0, 349)` (FR-006).
- **No xfail** (FR-002, FR-005).
- **Leave the other four tests and `population_snapshot.py` unchanged** (FR-008, FR-009).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | EDIT | Apply `01/09/2026`–`15/10/2026` in the day/night test and both sides of the clear test |
| `pages/alerts_analysis/population_page.py` | UNCHANGED | `set_date_range` and `clear_filters` already exist |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | Readers stay as they are |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. No new label is added under `core/` or `pages/`.
- **Existing tests are the contract (III)**: PASS. The two invariant assertions stay strict and are updated in this same slice. Fleet smoke is not the gate: Layer 0, Layer 2, and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The tests call `set_date_range` and `clear_filters` on the page object.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. No shared reader is added.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/031-invariant-date-bounds/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── invariant-dates.md
```

### Source Code (repository root)

```text
tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  ├── test_day_plus_night_equals_untoggled_sum()
  │     clear_filters → set_date_range("01/09/2026", "15/10/2026") → dates totals
  └── test_clear_restores_population_snapshot()
        clear_filters → set_date_range(...) → before snapshot
        → mutations → during snapshot
        → clear_filters → set_date_range(...) → after snapshot

pages/alerts_analysis/population_page.py          # UNCHANGED
tests/ui/alerts_analysis_dashboard/population_snapshot.py   # UNCHANGED
core/                                              # UNCHANGED
```

**Structure Decision**: Edit only `test_population_invariants.py`. The bounded window is
the existing `set_date_range` call. The clear test repeats that call after `clear_filters()`
so `take_snapshot` never opens the unfiltered dates table.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Tests call `set_date_range` where the request says `filter_dates` | `pages/` is out of scope, and `filter_dates` is not on the page. `set_date_range` already fills the two date fields and waits for the total card. | Adding `filter_dates` would edit `pages/`. Calling a missing name would fail at collection. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The day/night test applies `01/09/2026`–`15/10/2026` before the untoggled dates total and keeps `day + night == untoggled`.
- The clear test applies that window before the before snapshot and again after `clear_filters()` before the after snapshot.
- The clear test still mutates with `01/09/2026`–`01/10/2026`, day, night, and the 0–349 range.
- Neither test gains `pytest.mark.xfail`.
- The other four tests and `population_snapshot.py` stay unchanged.
- `core/` and `pages/` are absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
