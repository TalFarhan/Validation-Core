# Implementation Plan: Population Chart Scope

**Branch**: `feature/reportportal-integration` (spec directory `022-population-chart-scope`) | **Date**: 2026-10-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/022-population-chart-scope/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Feature 021's numeric skip and single Sum click stay.
This slice narrows the dates and hour reads and lengthens the population page's ready wait.

## Summary

`Chart.read` for the dates chart, called with the page title as scope, returns a container that
also holds district names, city names, scale captions, and hour ticks. Night mode fills some of
those city cells, so day plus night no longer equals the untoggled sum.

The population page will choose the read root itself for the dates chart and the hour chart: the
nearest visual container that contains that chart's title, contains a number, and does not contain
another chart title from this page. It will pass that locator to the existing chart parser. It
will not change `core/`.

Setup will wait until the district chart is visible, with a 60 second budget on this page only.
`clear_filters` will wait until the total population card is visible before it clicks clear.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright locators on the report frame. The existing `Chart._parse`
method, called with a locator the page built. No new package. No edit under `core/`.

**Storage**: N/A.

**Testing**: `pytest` on `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`. Auth
state is required. Fleet smoke is not a gate: Layer 0 and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Domain page object under `pages/alerts_analysis/`.

**Performance Goals**: N/A. One tighter read per dates or hour total. Ready wait up to 60 seconds.

**Constraints**:

- **No `core/` edit** (FR-002, AC-005).
- **Dates and hour only** (FR-001). District and settlement totals keep `Chart.read`.
- **Do not add 0 for an empty cell** (FR-004). Feature 021's numeric skip stays.
- **Snapshot stays a caller** (FR-007).
- Inline comments in edited Python MUST be English.

**Scale/Scope**: `chart_total`, `before_report_ready_check`, `clear_filters`, and `__init__` in
`pages/alerts_analysis/population_page.py`.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Tight container for dates and hour; 60s ready budget; card visible before clear |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | UNCHANGED | Still calls `chart_total` |
| `core/` | UNCHANGED | Parser and canvas host stay as they are |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell.navigate` is not edited. The population page sets its own `timeout`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Chart titles stay on the population page. The container walk uses generic class fragments already known to Power BI (`visualContainer`, `visual-container`) and the page's own titles.
- **Existing tests are the contract (III)**: PASS for this slice. Layer 0 and the fleet page are not edited, so fleet smoke is not the gate. The population invariant file is the gate. The ready hook that changes is `AlertsPopulationPage.before_report_ready_check`, which fleet does not call.
- **Page object discipline (IV)**: PASS. Tests still call page methods.
- **Warehouse as source of truth (V)**: PASS. No SQL.
- **Observability (VI)**: PASS. Run reports and screenshots stay as they are.
- **Extract shared behavior only (VII)**: PASS. The tight container is page-local because the generic reader must not change in this slice.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/022-population-chart-scope/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── chart-container.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
  ├── __init__                         # timeout = 60_000 before KPI and Chart are built
  ├── before_report_ready_check()      # district chart, else page switcher once it is visible
  ├── clear_filters()                  # total card visible, then clear
  ├── _visual_container(title)         # nearest box for dates or hour
  └── chart_total()                    # dates and hour use that box; others use Chart.read

tests/ui/alerts_analysis_dashboard/population_snapshot.py   # UNCHANGED
tests/ui/alerts_analysis_dashboard/test_population_invariants.py   # UNCHANGED; the gate
core/                                                               # UNCHANGED
```

**Structure Decision**: Keep one `chart_total`. Inside it, the dates and hour titles take the tight
container and `Chart._parse`. Every other title keeps `Chart.read`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Page calls `Chart._parse` on a locator it built | The public `read` always starts from `scope_host`, which for this page title is the visible canvas, and then the outer `visualContainerHost`. That box holds several charts. | Editing `core/components/chart.py` to prefer the inner container would change every report and violates the request. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The contract changes only the population page.
- Dates and hour reads exclude a container that also holds another chart title from this page.
- Empty charts still fail. Neighboring cells are not added as 0.
- Ready budget is 60 seconds on this page. `clear_filters` waits for the total card.
- `core/` is absent from the edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.

## Phase 0 / Phase 1 Outputs

- [research.md](./research.md)
- [data-model.md](./data-model.md)
- [contracts/chart-container.md](./contracts/chart-container.md)
- [quickstart.md](./quickstart.md)
