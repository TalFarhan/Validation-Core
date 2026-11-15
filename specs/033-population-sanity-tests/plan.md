# Implementation Plan: Population Screen Data Validation Tests

**Branch**: `feature/reportportal-integration` (spec directory `033-population-sanity-tests`) | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/033-population-sanity-tests/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The previous pin, `032-date-input-force-click`, stays as its own slice.

## Summary

Add a sanity package that checks the population screen against the golden record in
`data/alerts/db_sanity_am_kalavi.yaml`. Two tests reuse the existing `population_dashboard`
fixture. One clears every slicer and asserts the total and unprotected cards. The other sets
the golden date range and asserts the warned card. `tests/ui/` and `core/` are not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML` (`pyyaml>=6.0`, already in `requirements.txt`),
Playwright through the existing `population_dashboard` fixture. No new package.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml`. No warehouse query in this slice.

**Testing**: `pytest` on `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
Auth state is required to pass. Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: New pytest module under `tests/sanity/`. No page-object or `core/` change.

**Performance Goals**: Each test reads three population cards. It does not sum the hour, dates, district, or settlement charts.

**Constraints**:

- **No `tests/ui/` edit** (FR-008, AC-004).
- **No `core/` edit** (FR-008, AC-001).
- **No page-object edit** (AC-002). The test calls `clear_filters()`, `set_date_range()`, and `read_card()`.
- **Golden paths stay** (FR-005, FR-006). Assertions use the three `expected_value` keys named in the spec.
- **Page date format** (FR-009). ISO dates from the file become `DD/MM/YYYY` before `set_date_range`.
- **English comments** (FR-007) inside the new functions.
- **Signatures stay** (FR-004): both tests take only `population_dashboard`.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/sanity/__init__.py` | ADD | Package marker |
| `tests/sanity/alerts_analysis_dashboard/__init__.py` | ADD | Package marker |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | ADD | Two golden-record tests |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Golden expected values |
| `pages/alerts_analysis/population_page.py` | UNCHANGED | Existing `clear_filters`, `set_date_range`, `read_card` |
| `tests/ui/` | UNCHANGED | Fixture is imported, not edited |
| `core/` | UNCHANGED | No layer change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The sanity tests open the population page through the existing fixture.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The golden file and the card roles stay outside `core/`. `core/` does not load `data/alerts/`.
- **Existing tests are the contract (III)**: PASS. `tests/ui/` is not edited. Public page methods keep their names and arguments. Fleet smoke is not the gate: Layer 0, Layer 2, and the fleet page are not edited.
- **Page object discipline (IV)**: PASS. The new tests call `clear_filters`, `set_date_range`, and `read_card`. They do not add locators.
- **Warehouse as source of truth (V)**: PASS with a recorded deviation. These two tests compare the UI to the checked-in golden record, not to a live SQL query. The deviation is justified in Complexity Tracking. No SQL is added to `core/` or to the test.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay on the existing pytest run path.
- **Extract shared behavior only (VII)**: PASS. Card reading stays on the population page. The YAML load stays in the new test module. No new generic API.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/033-population-sanity-tests/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── sanity-tests.md
```

### Source Code (repository root)

```text
data/alerts/db_sanity_am_kalavi.yaml          # UNCHANGED golden record

tests/sanity/
├── __init__.py
└── alerts_analysis_dashboard/
    ├── __init__.py
    └── test_data_validation.py
          ├── load_sanity_data()
          ├── to_page_date()
          ├── read_population_cards()
          ├── test_global_metrics_match_db()
          └── test_filtered_population_matches_db()

tests/ui/alerts_analysis_dashboard/conftest.py   # UNCHANGED; fixture is imported
pages/alerts_analysis/population_page.py         # UNCHANGED
core/                                            # UNCHANGED
```

**Structure Decision**: Put the golden-record checks in a new `tests/sanity/` package.
Import `population_dashboard` from the alerts UI conftest so the sanity module can request
that fixture without editing `tests/ui/`. Leave the golden file, the page object, and `core/`
as they are.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: the two tests compare cards to a YAML golden record instead of a live warehouse query | The user placed the expected numbers in `data/alerts/db_sanity_am_kalavi.yaml` and named the assertion paths. This slice checks that file. | Calling `db/clients/alerts.py` would ignore the golden file and the three `expected_value` keys the user specified. The existing e2e suite remains the live SQL path. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The new module loads only `dashboard_sanity_checks.screen_2_alerts_analysis`.
- `clear_filters()` is the clear-all call. No `clear_all_filters` method is added.
- `set_date_range` receives `DD/MM/YYYY` converted from the file's `YYYY-MM-DD` values, still in file order.
- Cards are `read_card("total")`, `read_card("unprotected")`, and `read_card("warned")`.
- `tests/ui/` and `core/` are absent from the edit list.
- No SQL client, catalog row, or `core/` parser is added.
