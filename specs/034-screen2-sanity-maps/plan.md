# Implementation Plan: Screen 2 Sanity Maps

**Branch**: `feature/reportportal-integration` (spec directory `034-screen2-sanity-maps`) | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/034-screen2-sanity-maps/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). `033-population-sanity-tests` stays the card-only slice.

## Summary

Extend `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` so Screen 2's
settlement, hierarchy, date, and hour golden maps are checked after the same date range
the card test already applies. Settlement uses the existing `Chart.read` call. מחוז uses
`set_district_aggregation` plus a new label reader. נפה, רשות, and יישוב skip because the
page has no level switch. Dates and hour sums get basic readers beside `chart_total`.
The hour daily average skips. The two existing card tests stay as they are.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `population_dashboard`,
and the existing `Chart` class. No new package. No edit under `core/`.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml`. This slice does not edit it and does not query the warehouse.

**Testing**: `pytest` on `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
Auth state is required to pass. Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: More tests in the sanity module, plus basic readers on the population page where a category map is missing.

**Performance Goals**: Each new test reads one chart after one date range. District and hour modes are separate tests so a skip does not hide a finished assertion.

**Constraints**:

- **Existing card tests stay** (FR-001). `test_global_metrics_match_db` and `test_filtered_population_matches_db` keep their steps.
- **No `tests/ui/` edit** (FR-011).
- **No `core/` edit** (FR-011, AC-001).
- **Date range first** (FR-002). New tests call `set_date_range` with `to_page_date` on the file's start and end.
- **Skip is per test** (FR-006, FR-008, FR-009). Message form: `Missing page object method for <metric>`.
- **No invented hierarchy drill** (FR-006).
- **`chart_total` stays a total** (FR-005, AC-002).
- **English comments** (FR-010).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | EDIT | New map tests. The two card tests stay |
| `pages/alerts_analysis/population_page.py` | EDIT | Basic district, date, and hour maps. Totals stay |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Golden maps |
| `tests/ui/` | UNCHANGED | Invariant tests keep `chart_total` |
| `core/` | UNCHANGED | `Chart.read` is called, not edited |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. New tests use the existing population fixture.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Chart titles, hierarchy level names, and the golden file stay on the population page and in the sanity test. `core/` does not gain them.
- **Existing tests are the contract (III)**: PASS. `chart_total`, `read_card`, `clear_filters`, `set_date_range`, and `set_district_aggregation` keep their contracts. `tests/ui/` is not edited. Fleet smoke is not the gate.
- **Page object discipline (IV)**: PASS. New tests call page methods or the existing `Chart.read` construction. They do not add locators.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the card slice. These tests compare the UI to the golden file, not to a live SQL query.
- **Observability (VI)**: PASS. The existing pytest report path stays.
- **Extract shared behavior only (VII)**: PASS. The new maps are report-specific and stay on the population page. `Chart.read` is reused and not extended.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/034-screen2-sanity-maps/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── sanity-maps.md
```

### Source Code (repository root)

```text
tests/sanity/alerts_analysis_dashboard/test_data_validation.py
  ├── test_global_metrics_match_db()                         # UNCHANGED
  ├── test_filtered_population_matches_db()                  # UNCHANGED
  ├── test_alerted_population_by_settlement_matches_db()
  ├── test_hierarchy_mahoz_sum_matches_db()
  ├── test_hierarchy_mahoz_daily_avg_matches_db()
  ├── test_hierarchy_nafa_matches_db()                       # skip
  ├── test_hierarchy_rashut_matches_db()                     # skip
  ├── test_hierarchy_yeshuv_matches_db()                     # skip
  ├── test_alerts_by_date_matches_db()
  ├── test_alerts_by_hour_sum_matches_db()
  └── test_alerts_by_hour_daily_avg_matches_db()             # skip

pages/alerts_analysis/population_page.py
  ├── chart_total()                                          # UNCHANGED
  ├── read_district_labels()                                 # ADD
  ├── read_date_counts()                                     # ADD
  └── read_hour_buckets()                                    # ADD
```

**Structure Decision**: Keep the card tests in place. Add one test per golden map so a skip
cannot erase another map's result. Add three readers on the population page. Leave `core/`
and `tests/ui/` alone.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: map tests compare the UI to the golden YAML instead of a live warehouse query | The user named `data/alerts/db_sanity_am_kalavi.yaml` as the source for these sections. | A new SQL client would ignore that file. The e2e suite remains the live SQL path. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- Settlement uses `Chart.read` and does not add a page method.
- מחוז uses `set_district_aggregation` and `read_district_labels`.
- נפה, רשות, and יישוב skip without a click.
- `read_date_counts` reuses the dates-table open and close path. `chart_total` still returns the sum.
- `read_hour_buckets` reads hour SVG labels. The hour daily-average test skips.
- The two card tests are not rewritten.
- `core/` and `tests/ui/` are absent from the edit list.
