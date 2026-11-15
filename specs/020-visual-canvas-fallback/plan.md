# Implementation Plan: Visual Canvas Fallback

**Branch**: `feature/reportportal-integration` (spec directory `020-visual-canvas-fallback`) | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/020-visual-canvas-fallback/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration`). Feature 019 stays on disk and stays paused: its page,
contract, and tests are not edited here.

## Summary

`scope_host` in `core/components/visual.py` treats every non-blank scope as a `role="group"`.
When the scope is a page title that is only a text node, both group queries miss, and the function
still returns `group.first`. The next read waits the action timeout (about 30 seconds) on a locator
that will never match.

This slice keeps the feature 014 group lookup as tier 1, and adds a tier 2 only when that lookup
matches nothing:

1. Blank scope returns the report frame (unchanged).
2. Tier 1: a `role="group"` with that accessible name, else a `role="group"` that contains the text,
   but only when `count() > 0`. `count()` does not wait.
3. Tier 2: the generic Power BI visual containers filtered with `visible=True`. Hidden pages drop
   out. No report name is consulted.

`KPI`, `Chart`, and the parity engine already call `scope_host`. Their signatures stay. Presence,
mark counting, and displayed title stay. Fleet section scopes and Alerts page 1 scopes still hit
tier 1.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright 1.61 sync API (`FrameLocator`, `Locator.filter(visible=...)`,
`Locator.count`). No new package. `Locator.filter` accepts `visible`, not `has_state`.

**Storage**: N/A. The host is a live locator. No contract or catalog edit.

**Testing**: `pytest`. Gates: (1) `tests/unit/` including `tests/unit/test_db_parity_engine.py` and a
new `tests/unit/test_scope_host.py`; (2) Constitution III — `pytest tests/ui/fleet_dashboard/` at
100%; (3) Alerts page 1 — `tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py` and
`test_db_parity.py`. Population-page tests are not this gate.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal for
the live gates. The host decision itself is unit-tested with a fake frame.

**Project Type**: Internal validation framework (Layer 2 `core/components`, domain pages unchanged).

**Performance Goals**: Host resolution is two `count()` probes, then either an existing group or one
visible-container locator. It must not spend the action timeout deciding the tier.

**Constraints**:

- **No domain leakage** (Constitution II, FR-006): no report name, page title, or metric title under
  `core/`. The canvas selector is generic visual-container chrome.
- **Backward compatibility** (Constitution III, FR-001–FR-003, FR-007): a scope that already matches
  a group returns that group. Blank scope returns the frame. Public `KPI` / `Chart` signatures stay.
- **No `*` text filter** (FR-009): tier 2 is visual containers, not `locator("*").filter(has_text=...)`.
- **Feature 019 paused** (FR-010): do not edit the population page, its contract rows, or its tests
  in this slice.
- All inline code comments MUST be English only.

**Scale/Scope**: One function in `core/components/visual.py`, a docstring correction on
`KPI._scope_host`, and one unit module. No portal, SQL, or page-object behavior change.

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/visual.py` | EDIT | Two-tier `scope_host`; visible canvas constant |
| `core/components/kpi.py` | EDIT | Docstring only: host is not always a group |
| `tests/unit/test_scope_host.py` | NEW | Tier 1, tier 2, blank scope, no Hebrew in `visual.py` |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `core/portal` and `ReportShell` are untouched. Domain pages still
  compose the shell.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The new branch keys off Playwright visibility
  and generic visual-container classes. The page title that motivated the slice stays on the alerts
  page. `core/` does not load a catalog.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Tier 1 is the feature 014 rule,
  including the `has_text` group, and it runs whenever a group `count()` is positive. Fleet smoke
  and Alerts page 1 are explicit gates. Signatures of `navigate`, `KPI.number`, and `Chart.read`
  stay.
- **Page object discipline (IV)**: PASS. Tests still enter through page objects and Layer 2. No new
  locator is added in a test body. The fake frame exists only in the unit test for `scope_host`.
- **Warehouse as source of truth (V)**: PASS. No SQL. The parity engine still compares UI to the
  warehouse; only the host of an unresolved scope changes.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces are untouched.
- **Extract shared behavior only (VII)**: PASS. This does not add a component. It finishes the
  existing `scope_host` so a page-level label, which feature 019 already needs, has a host. Chart
  container walks and fleet chart locators stay where they are.

**Result**: No unjustified violations. Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/020-visual-canvas-fallback/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # User stories and requirements
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    └── scope-host.md    # Host resolution contract
```

### Source Code (repository root)

```text
core/components/visual.py                 # EDIT — scope_host tiers
  ├── scope_host(frame, scope)            # blank → frame; group → group; else visible canvas
  ├── _VISUAL_CONTAINERS                  # generic Power BI visual-container selector
  └── classify_presence / count_data_marks / displayed_title_text   # UNCHANGED

core/components/kpi.py                    # EDIT docstring of KPI._scope_host only
core/components/chart.py                  # UNCHANGED — still calls scope_host
tests/helpers/db_parity_engine.py         # UNCHANGED — still calls scope_host
pages/alerts_analysis/population_page.py  # UNCHANGED — feature 019 paused
tests/ui/fleet_dashboard/                 # UNCHANGED — regression gate
tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py  # UNCHANGED — page 1 gate
tests/ui/alerts_analysis_dashboard/test_db_parity.py        # UNCHANGED — page 1 gate
```

**Structure Decision**: Keep a single `scope_host`. Tier 2 returns a locator that matches every
visible visual container, so existing `host.get_by_role(...)` calls search those containers and
skip hidden ones. Do not add a canvas class, and do not thread a locator through `KPI` or `Chart`.

## Complexity Tracking

> No constitution violations require justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- The contract returns the frame, a group, or the visible visual-container locator. It never returns
  `locator("*")` filtered by scope text.
- Tier 1 is specified to win whenever a group count is positive, so fleet and Alerts page 1 scopes
  do not widen.
- Tier 2 uses `filter(visible=True)` on generic container classes. No dashboard string is part of
  the design.
- `classify_presence`, mark counting, and displayed title are specified as unchanged.
- `KPI` / `Chart` / parity signatures are specified as unchanged. Feature 019 files are out of the
  edit list.
- No unresolved `NEEDS CLARIFICATION` markers remain.

## Phase 0 / Phase 1 Outputs

- [research.md](./research.md) — group probe, `visible=True`, selector ownership, regression boundary.
- [data-model.md](./data-model.md) — scope, group host, visible canvas, lookup pipeline.
- [contracts/scope-host.md](./contracts/scope-host.md) — normative host rules.
- [quickstart.md](./quickstart.md) — unit gate, source scan, fleet smoke, Alerts page 1.
