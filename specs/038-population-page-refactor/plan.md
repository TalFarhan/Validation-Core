# Implementation Plan: Population Page Internal Refactor

**Branch**: `feature/reportportal-integration` (spec directory `038-population-page-refactor`) | **Date**: 2026-10-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/038-population-page-refactor/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). `specs/037-screen2-chart-readers/` is a different slice and is not edited.
This slice consolidates private helpers inside `AlertsPopulationPage` and adds one public wrapper on `Chart`.

## Summary

`pages/alerts_analysis/population_page.py` is about 1,450 lines. Two dates readers copy the same scroll loop. Two row helpers copy the same DOM script. District and hour tooltips copy the same hover loop. `set_district_aggregation` calls `Chart._container`. `read_chart_categories` calls `Chart._parse`. Helpers swallow `except Exception`. Fixed pauses are `page.wait_for_timeout` (there is no `time.sleep`).

The public methods stay. Tests under `tests/sanity/` and `tests/ui/` stay. The dates total and `read_date_counts()` call one visible-row scroll collector. Both entry helpers evaluate one row script. Both tooltip fallbacks call one hover method. The district Sum button uses the page's visual locator. Category parsing goes through a new public `Chart.parse_container` that returns the same pair `_parse` returns today. Playwright failures are caught as `playwright.sync_api.Error`. Appearance waits use `state="visible"`. Loops that wait for two equal numbers stay polls.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Playwright 1.61 (`locator.wait_for`, `expect(...).to_be_visible`, `Error` / `TimeoutError`). `Chart` and `KPI` as already composed by the page. No new package.

**Storage**: N/A. `data/alerts/db_sanity_am_kalavi.yaml` is not read or written by this slice.

**Testing**: Existing modules only. `tests/unit/test_population_page.py` needs no browser. Sanity and UI suites are not edited and are the live contract. Fleet smoke (`tests/ui/fleet_dashboard/`) is the gate because `core/components/chart.py` gains one method.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal refactor of one domain page object, plus a report-agnostic public wrapper on the Layer 2 chart reader.

**Performance Goals**: The dates scroll still stops at the bottom or at `self.timeout`. A tooltip hover still runs only after the cheaper read is empty. No extra full-table pass is added.

**Constraints**:

- **Public signatures stay** (FR-001). See `contracts/population-page.md`.
- **One visible-row scroll** (FR-002, FR-003). The unused hidden-row / scroll-to-end helper is deleted, not revived.
- **One row script** (FR-004, FR-005). Python key and skip rules stay per caller.
- **One hover loop** (FR-006). District and hour parsers stay different.
- **No private Chart calls** (FR-007). `Chart.read` is not a substitute for `_parse` on the page-scoped container.
- **`_plain_cell` stays** (FR-008). It is not the same function as `Chart._dedupe_doubled`.
- **Specific Playwright errors** (FR-009). No `ElementHandleError` in this Playwright.
- **No new blind sleep** (FR-010, FR-011). `expect.poll` is not in the installed Python API.
- **English comments** inside functions (FR-012).
- Tests under `tests/sanity/` and `tests/ui/` are not edited.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | One scroll collector, one row script, one hover loop, public Chart call, narrower exceptions, condition waits |
| `core/components/chart.py` | EDIT | Public `parse_container(container, title)` wrapping the existing `_parse` |
| `tests/sanity/`, `tests/ui/` | UNCHANGED | Contract |
| `data/alerts/` | UNCHANGED | Golden maps stay |
| `core/portal/` | UNCHANGED | Layer 0 stays |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The population page still inherits `AlertsAnalysisPage`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `parse_container` takes a locator and an opaque title. נפה, רשות, יישוב, chart titles, and `סה"כ` stay on the population page.
- **Existing tests are the contract (III)**: PASS. Public signatures stay, and `tests/sanity/` plus `tests/ui/` are not edited. Layer 2 changes, so fleet smoke is a gate and fleet page objects are not edited.
- **Page object discipline (IV)**: PASS. Locators and the row script stay on the population page. Tests are not given new locators.
- **Warehouse as source of truth (V)**: PASS. This slice does not change what a test compares. No SQL is added.
- **Observability (VI)**: PASS. Allure, CSV, screenshots, and traces are untouched.
- **Extract shared behavior only (VII)**: PASS. The new Chart method publishes the parse the page already uses. Tooltips, the dates table, and the scroll script stay on the domain page. `_dedupe_doubled` stays private because the page helper is not a duplicate.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/038-population-page-refactor/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── population-page.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  ├── public methods unchanged (contracts/population-page.md)
  ├── _collect_scrolled_rows(table, column, key=...)   # one visible-row loop
  ├── _ROW_CELLS_JS                                     # one evaluate script
  ├── _hover_mark_values(container, parse)              # one hover loop
  └── _visual_container                                 # replaces Chart._container

core/components/chart.py
  └── Chart.parse_container(container, title)           # public wrapper, no empty wipe
```

**Structure Decision**: Keep the refactor inside the population page. Add one public method on `Chart` so category parsing of a caller-supplied container does not go through `_parse`. Do not add a second scroll implementation and do not move tooltips into `core/`.

## Complexity Tracking

No constitution violations require justification.

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The scroll collector is visible-row only. The dead scroll-to-end path is not a mode of the new method.
- `parse_container` returns the raw `_parse` pair and does not apply the empty wipe inside `Chart.read`.
- `set_district_aggregation` uses `_visual_container` and keeps the count-equals-1 fallback.
- `_plain_cell` stays on the page. `Chart._dedupe_doubled` is not imported.
- Playwright `Error` replaces `except Exception`. `AssertionError` still becomes `{}` only on the two readers that already do that.
- Appearance waits use `state="visible"`. Numeric settle stays a poll with `wait_for_timeout` as the interval.
- No unresolved `NEEDS CLARIFICATION` markers remain.
