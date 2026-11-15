# Implementation Plan: Status Picture Sanity Tests

**Branch**: `feature/reportportal-integration` (spec directory `035-status-picture-sanity`) | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/035-status-picture-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Screen 2 stays in `034-screen2-sanity-maps`.

## Summary

Add a status-picture page object for the first page of `ניתוח התרעות` and a sanity
module that checks `screen_1_status_picture` in the golden file. All-time cards are
checked after `clear_filters`. Range cards, threat totals, and the top settlements
are checked after `13/06/2025` through `25/06/2025`. Category and top-10 readers
skip on their own tests when they cannot see labels. The Screen 2 sanity module
and the root `tests/conftest.py` stay as they are.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright, `ReportShell` through
`AlertsAnalysisPage`, and the existing `Slicer` and `KPI` readers. No new package.
No edit under `core/`.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml`. This slice does not edit it and does not query the warehouse.

**Testing**: `pytest` on `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`.
Auth state is required to pass. Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: One new domain page and one new sanity package.

**Performance Goals**: Each test reads the cards it asserts. Category and top-10 tests do not run inside the card tests.

**Constraints**:

- **Screen 2 file stays** (FR-012). `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` is not edited.
- **Root conftest stays** (FR-005, AC-004). The fixture is registered in the sanity package.
- **No page-2 switch** (FR-002). The new page does not click `ניווט בין עמודים`.
- **No `core/` edit** (FR-012).
- **Page date format** (FR-004). ISO dates become `DD/MM/YYYY`.
- **Skip is per chart test** (FR-009, FR-010).
- **English comments** (FR-011).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/status_picture/__init__.py` | ADD | Package marker |
| `pages/status_picture/status_picture_page.py` | ADD | Screen 1 page object |
| `tests/sanity/status_picture_dashboard/__init__.py` | ADD | Package marker |
| `tests/sanity/status_picture_dashboard/conftest.py` | ADD | `status_picture_dashboard` fixture |
| `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` | ADD | Golden checks |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | UNCHANGED | Screen 2 tests |
| `tests/conftest.py` | UNCHANGED | No report import |
| `core/` | UNCHANGED | No layer change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. The new page inherits `AlertsAnalysisPage` and therefore `ReportShell`. It does not copy login or catalog search.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Screen 1 titles stay on the new page. The root `conftest.py` does not import it. `core/` does not load the golden file.
- **Existing tests are the contract (III)**: PASS. Screen 2 tests, `tests/ui/`, and public population methods stay unchanged. Fleet smoke is not the gate.
- **Page object discipline (IV)**: PASS. The new tests call `clear_filters`, `set_date_range`, `read_cards`, `read_alerts_by_category`, and `read_top_10_settlements`.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the other sanity slices. These tests compare the UI to the golden file, not to a live SQL query.
- **Observability (VI)**: PASS. The existing pytest report path stays.
- **Extract shared behavior only (VII)**: PASS. Date commit and card titles stay on this page. `Slicer` and `KPI` are composed, not extended.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/035-status-picture-sanity/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── status-picture.md
```

### Source Code (repository root)

```text
pages/status_picture/status_picture_page.py
  ├── clear_filters()
  ├── set_date_range(start, end)
  ├── read_cards()
  ├── read_alerts_by_category()
  └── read_top_10_settlements()

tests/sanity/status_picture_dashboard/
  ├── conftest.py
  └── test_status_picture_validation.py
        ├── test_screen_1_global_metrics()
        ├── test_screen_1_filtered_metrics()
        ├── test_screen_1_alerts_by_category()
        └── test_screen_1_top_settlements()
```

**Structure Decision**: Keep Screen 1 in its own page package and its own sanity
package. Inherit the alerts report shell so the catalog search stays `ניתוח התרעות`.
Register the fixture beside the tests. Leave the root conftest and the Screen 2 module alone.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: the tests compare the UI to the golden YAML instead of a live warehouse query | The user named `screen_1_status_picture` in `data/alerts/db_sanity_am_kalavi.yaml` as the source. | A new SQL client would ignore that file. The alerts parity suite remains the live SQL path. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- `StatusPicturePage` inherits `AlertsAnalysisPage` and does not click the page-2 control.
- The fixture is `bind_dashboard(StatusPicturePage, "status_picture_dashboard")` in the sanity conftest.
- `tests/conftest.py` is absent from the edit list.
- Card tests and chart tests are separate functions.
- Category ids 1, 2, and 10 select the threat sections already named in `data/alerts/alerts_contract.yaml`.
- The Screen 2 sanity module is not edited.
