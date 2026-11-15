# Implementation Plan: Top Settlement Tie Assertion

**Branch**: `feature/reportportal-integration` (spec directory `036-top-settlement-ties`) | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/036-top-settlement-ties/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The golden YAML file stays as it is.
This slice changes the assertion inside `test_screen_1_top_settlements` only.

## Summary

`test_screen_1_top_settlements` requires every golden name, including four settlements
that share the count 31. The live ranking chart keeps the six higher counts and fills
the last four rows from a larger tie. Those four names change between page loads.

The test will split `top_10_settlements.values`. Names at 32 or above must match the
UI exactly. The other UI rows must be exactly four, and each count must be the golden
tie value, which is 31 in the current file. Tie names are not compared.
`test_screen_1_filtered_metrics` stays on the two range cards.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: pytest and the existing `status_picture_dashboard` fixture.
No new package. No edit under `pages/` or `core/`.

**Storage**: The golden map stays in `data/alerts/db_sanity_am_kalavi.yaml`. This slice
reads it and does not write it.

**Testing**: `pytest` on `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`.
Portal auth is required for a live run. Fleet smoke is not a gate: Layer 0, Layer 2,
and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: One assertion change in an existing sanity test.

**Performance Goals**: The ranking test still performs one report open and one date-range
selection. No extra chart scroll is added in the test.

**Constraints**:

- **Ranking test only** (FR-001, FR-007). `test_screen_1_filtered_metrics` is not the tie check.
- **Stable partition** (FR-002, FR-003). Golden counts `>= 32` must match by name. Do not hard-code the six names.
- **Four tie slots** (FR-004, FR-005). UI rows outside that set number 4, and each count is the golden tie value (31).
- **Empty map still skips** (FR-006).
- **Golden file stays** (FR-008). Do not edit `db_sanity_am_kalavi.yaml`.
- **Page and core stay** (FR-008, AC-001, AC-002).
- Inline comments in the edited function MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` | EDIT | Split the top-settlements assertion |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Still the source of the stable counts and the tie value |
| `pages/status_picture/status_picture_page.py` | UNCHANGED | `read_top_10_settlements()` already returns the scrolled map |
| `core/` | UNCHANGED | No visual-reader change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Settlement names stay in the golden file and in the test that already loads that file.
- **Existing tests are the contract (III)**: PASS. The other three Screen 1 tests keep their assertions. Fleet smoke is not the gate: Layer 0, Layer 2, and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The test still calls `read_top_10_settlements()`. No new locator is added in the test.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as feature 035. This test compares the UI to the golden file, not to a live SQL query.
- **Observability (VI)**: PASS. The existing pytest HTML report path stays.
- **Extract shared behavior only (VII)**: PASS. The tie split stays in this test. `core/components` is not extended.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/036-top-settlement-ties/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── top-settlement-ties.md
```

### Source Code (repository root)

```text
tests/sanity/status_picture_dashboard/test_status_picture_validation.py
  └── test_screen_1_top_settlements()
        stable golden counts >= 32 must match by name
        the other UI rows: length 4, each count is the golden tie value

data/alerts/db_sanity_am_kalavi.yaml          # UNCHANGED
pages/status_picture/status_picture_page.py   # UNCHANGED
core/                                         # UNCHANGED
```

**Structure Decision**: Edit the ranking assertion in the existing Screen 1 module.
Leave the card tests, the category test, the page reader, and the golden file alone.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: the ranking test still compares the UI to the golden YAML instead of a live warehouse query | Feature 035 already uses `screen_1_status_picture` as the source, and this slice must not edit that file or add SQL. | A new SQL client would ignore the golden file the user named. The alerts parity suite remains the live SQL path. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The edit is confined to `test_screen_1_top_settlements`.
- Stable rows come from golden values `>= 32`. Tie slots are the other UI rows, length 4, count 31.
- `test_screen_1_filtered_metrics` still asserts only the two range cards.
- `read_top_10_settlements()` is still the only ranking reader the test calls.
- `data/alerts/db_sanity_am_kalavi.yaml`, `pages/status_picture/status_picture_page.py`, and `core/` are absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
