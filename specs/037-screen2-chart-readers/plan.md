# Implementation Plan: Screen 2 Chart Readers

**Branch**: `feature/reportportal-integration` (spec directory `037-screen2-chart-readers`) | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/037-screen2-chart-readers/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The golden YAML file stays as it is.
This slice adds hierarchy-level selection and an hour daily-average reader, and wires
the four tests that currently skip before the page opens.

## Summary

`test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`,
`test_hierarchy_yeshuv_matches_db`, and `test_alerts_by_hour_daily_avg_matches_db`
call `pytest.skip` and never open the chart. מחוז sum, מחוז daily average, and hour
sum already call page methods and skip only when the returned map is empty.

`AlertsPopulationPage` will select נפה, רשות, or יישוב on the district chart when
that control is visible, then reuse Sum mode and `read_district_labels()`. The hour
chart gains `read_hour_daily_avg()` for the average series the sum reader drops.
A tooltip hover is the last fallback when rows and mark labels are both empty.
If a level control or the average series is not on the page, that test keeps its
current skip message.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Playwright locators on `AlertsPopulationPage`, the existing
`Chart` container lookup, and pytest. No new package. No edit under `core/`.

**Storage**: The golden maps stay in `data/alerts/db_sanity_am_kalavi.yaml`. This slice
reads them and does not write them.

**Testing**: `pytest` on `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
Portal auth is required for a live run. Fleet smoke is not a gate: Layer 0, Layer 2,
and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Page-object readers plus the four sanity tests that currently skip unconditionally.

**Performance Goals**: One report open per test. A tooltip hover runs only after the
cheaper row and mark reads return nothing.

**Constraints**:

- **Level click only when visible** (FR-001, FR-002). Do not click a substitute control.
- **Sum for the three levels** (FR-004). Do not add נפה, רשות, or יישוב daily-average tests.
- **Hour average is separate** (FR-005, FR-006). `read_hour_buckets()` still drops `ממוצע` and fractions.
- **Empty map still skips** with the messages already in the four tests.
- **Golden file stays** (FR-008).
- **No `core/` edit** (AC-001). Tooltips stay on the population page.
- Inline comments in edited Python MUST be English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Level selection, scroll, tooltip fallback, hour daily average |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | EDIT | Replace the four unconditional skips with reader calls |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Sum and daily-average maps stay the expected values |
| `core/` | UNCHANGED | No shared tooltip or drill API |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The population page still inherits `AlertsAnalysisPage`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. נפה, רשות, יישוב, and the hour title stay on the population page.
- **Existing tests are the contract (III)**: PASS. The two card tests stay. The four skip tests change because this slice adds the methods they were waiting for. Fleet smoke is not the gate: Layer 0, Layer 2, and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The tests call page methods. New locators stay on the population page.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the other sanity slices. These tests compare the UI to the golden file, not to a live SQL query.
- **Observability (VI)**: PASS. The existing pytest report path stays.
- **Extract shared behavior only (VII)**: PASS. The tooltip and the hierarchy click stay on the population page. `core/components` is not extended.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/037-screen2-chart-readers/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── chart-readers.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  ├── set_hierarchy_level("nafa" | "rashut" | "yeshuv") -> bool
  ├── read_district_labels()          # rows, then marks, then tooltip
  ├── read_hour_buckets()             # sum; tooltip only when empty
  └── read_hour_daily_avg() -> dict[str, int]

tests/sanity/alerts_analysis_dashboard/test_data_validation.py
  ├── test_hierarchy_nafa_matches_db()
  ├── test_hierarchy_rashut_matches_db()
  ├── test_hierarchy_yeshuv_matches_db()
  └── test_alerts_by_hour_daily_avg_matches_db()

data/alerts/db_sanity_am_kalavi.yaml    # UNCHANGED
core/                                   # UNCHANGED
```

**Structure Decision**: Keep one district chart and one hour chart. Level selection
and the average reader are methods on the population page. The four tests stop
skipping before those methods are called.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: the tests compare the UI to the golden YAML instead of a live warehouse query | The user named `db_sanity_am_kalavi.yaml` as the source and forbade editing it. | A new SQL client would ignore that file. The alerts parity suite remains the live SQL path. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- `set_hierarchy_level` returns false when נפה, רשות, or יישוב is not visible.
- The three level tests compare `sum` only. מחוז daily average stays on its existing test.
- `read_hour_daily_avg` is a separate method from `read_hour_buckets`.
- An empty map keeps the current skip message.
- `data/alerts/db_sanity_am_kalavi.yaml` and `core/` are absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.
