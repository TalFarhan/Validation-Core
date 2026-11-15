# Implementation Plan: Population SVG Circle and Value Regex

**Branch**: `feature/reportportal-integration` (spec directory `025-population-svg-refine`) | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/025-population-svg-refine/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The page-local SVG reader from feature 024 stays.
This slice adds circle marks, reads the integer after `התרעות`, and waits for a mark to be visible.

## Summary

`test_hour_date_and_district_sums_match` failed with `141493 == 0`.
The hour side is the sum of bar labels such as `5293` and `5587`. That sum is `5895.54` times 24.
The dates side kept one circle label, `תאריך 2026-10-15. התרעות 0.`, and returned `0`.

`chart_total` for the dates and hour charts will query `svg rect`, `svg path`, and `svg circle`,
wait until the first mark is visible, then read `aria-label`. A label that contains `התרעות`
contributes the integer after that word. A label that is only an integer stays a bar. `ממוצע`
and floats stay out. District and settlement totals stay on their current readers. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright locators and `expect` already used by the population page.
No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `test_hour_date_and_district_sums_match`. Auth state is required.
Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object. The population test file is not edited.

**Performance Goals**: N/A. One visibility wait, then one attribute read per mark on two charts.

**Constraints**:

- **No `core/` edit** (FR-009, AC-005).
- **Dates and hour only** (FR-001, FR-008). District and settlement totals stay.
- **No `inner_text` on these marks** (FR-002).
- **Value after `התרעות` wins over a date token** (FR-004).
- **A bare integer label stays a bar** (FR-005).
- **Do not add 0 for a skipped average or float** (FR-006, FR-007).
- **Snapshot helper stays a caller** (FR-010).
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Circle marks, value regex, visibility wait |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | UNCHANGED | The three-chart test stays the gate |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | `Chart` stays as it is |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `התרעות` and `ממוצע` stay on the population page.
- **Existing tests are the contract (III)**: PASS. `test_hour_date_and_district_sums_match` is unchanged and is the gate. Fleet smoke is not the gate: Layer 0 and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `chart_total`.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The regex and the wait are page-local because this slice must not change the generic chart reader.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/025-population-svg-refine/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── svg-value.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  └── chart_total()                    # dates and hour: circle marks, התרעות regex, wait

tests/ui/alerts_analysis_dashboard/test_population_invariants.py
  └── test_hour_date_and_district_sums_match()   # UNCHANGED gate

core/                                    # UNCHANGED
```

**Structure Decision**: Edit `_integer_from_mark_label` and `_svg_mark_total` in
`pages/alerts_analysis/population_page.py`. The mark locator includes `svg circle`.
The method waits for the first mark, then reads `aria-label`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| The value rule lives on the population page | The alert count follows the word `התרעות`. The generic reader must not learn that word. | Putting the regex in `Chart._parse` would edit `core/`. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- Dates and hour totals read `svg rect`, `svg path`, and `svg circle` after a visibility wait.
- A label with `התרעות` contributes the integer after that word. A bare integer label stays a bar.
- `ממוצע` and floats are omitted and are not stored as `0`.
- District and settlement totals are unchanged.
- `population_snapshot.py` and the three-chart test are unchanged.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
