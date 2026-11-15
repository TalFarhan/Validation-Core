# Implementation Plan: Force the Date Field Click Past the Overlay

**Branch**: `feature/reportportal-integration` (spec directory `032-date-input-force-click`) | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/032-date-input-force-click/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The invariant test stays as it is.
This slice forces the field click inside `_commit_field`.

## Summary

`test_clear_restores_population_snapshot` calls `clear_filters()` and then `set_date_range`.
`clear_filters()` leaves a transparent `<div class="cdk-overlay-backdrop">` in the report
frame. `_dismiss_overlay` only clicks `.cdk-overlay-backdrop-showing`, so that backdrop
stays up. The next `field.click()` in `_commit_field` waits until the 60-second timeout.

`_commit_field` will call `field.click(force=True)`, then keep `field.fill(value)` and
`field.press("Enter")`. The invariant test is not edited. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright `Locator.click(force=True)` on the population page.
No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_clear_restores_population_snapshot`. Auth state is required.
Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: One method on the population page object.

**Performance Goals**: The date-field click returns without waiting out the 60-second
actionability timeout.

**Constraints**:

- **No `core/` edit** (FR-005, AC-005).
- **No test edit** (FR-004). `test_population_invariants.py` stays as it is.
- **Forced click** (FR-001). `_commit_field` uses `field.click(force=True)`.
- **Commit order stays** (FR-002): dismiss, expect visible, forced click, fill, Enter, dismiss.
- **Public date methods stay** (FR-003). `set_date_range` and `set_between_dates` keep their names and arguments.
- **No xfail** (FR-006).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | `field.click(force=True)` inside `_commit_field` |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | UNCHANGED | Clear-restore order and assertions stay |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls page methods |
| `core/` | UNCHANGED | Overlay handling stays off Layer 0 and Layer 2 |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The backdrop locator and the date labels stay on the population page.
- **Existing tests are the contract (III)**: PASS. `set_date_range` and `clear_filters` keep their contracts. The clear-restore test is not rewritten. Fleet smoke is not the gate: Layer 0, Layer 2, and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The forced click stays inside the page object. The test still calls `set_date_range`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The backdrop bypass stays on the population page because this slice must not change `core/`.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/032-date-input-force-click/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── field-click.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── _commit_field()
        _dismiss_overlay → expect visible → click(force=True) → fill → Enter → _dismiss_overlay

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_clear_restores_population_snapshot()   # UNCHANGED

core/                                              # UNCHANGED
```

**Structure Decision**: Change only the click inside `_commit_field`. Date inputs and the
value-range inputs share that method, so both get the forced click. Leave the clear-restore
test and `_dismiss_overlay` as they are.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| `field.click(force=True)` skips Playwright's actionability check | The leftover `cdk-overlay-backdrop` is transparent and intercepts the pointer. The 60-second wait is that check. | Clicking `.cdk-overlay-backdrop-showing` does not remove a backdrop that lacks the `-showing` class. Editing the test would not move the backdrop. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- `_commit_field` clicks with `force=True` and still fills and presses Enter.
- `_dismiss_overlay` still runs before and after the commit.
- `set_date_range` and `set_between_dates` keep their names and arguments.
- `test_population_invariants.py` is unchanged and has no new `pytest.mark.xfail`.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
