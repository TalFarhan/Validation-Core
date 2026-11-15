# Implementation Plan: Support Power BI Gauge Visual Parsing in KPI Component

**Branch**: `013-kpi-gauge-visuals` | **Date**: 2026-10-12 | **Spec**: inline feature request (no `spec.md`; `/speckit-plan` invoked directly)

**Input**: Feature request — the generic Layer 2 `KPI` component (`core/components/kpi.py`) fails on Power BI
Gauge visuals because the current value, minimum, and maximum are rendered in the same label. The current
`_NUMBER_TOKEN` regex allows ASCII spaces inside a number, so those three scale values concatenate into one
unparseable string (e.g. `"1337133733"`). Teach `extract_kpi_value_text` to isolate the Gauge's current
value and leave standard KPI-card extraction unchanged.

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command).

## Summary

Feature 012 taught `KPI` to read `role="group"` visuals by taking the **longest** numeric run from a mixed
`aria-label`. That heuristic is correct for a card that carries a single figure. A Power BI Gauge is also a
titled scalar, but its accessible text embeds **three** figures — current, min, and max — in one of two
observed shapes:

1. **Labeled**: `"distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337."`
2. **Compact**: `"0 1,337 3"` (min, max, current)

Because `_NUMBER_TOKEN` treats ASCII space as an interior thousands separator, both shapes collapse into one
token and `normalize_kpi_text` yields garbage. The parity engine then compares a concatenated integer to the
warehouse.

This feature extends **only** `extract_kpi_value_text` (plus unit coverage). A Gauge pre-pass detects the
labeled or compact pattern, returns the current value only, and otherwise falls through to the existing
longest-token logic so standard KPI cards (`"אזורי התרעה 1,234"`, `"1 234.5"`) keep their current behavior.
No new component, no locator change, no public-API change: callers still use `KPI.number(title)`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: stdlib `re` for extraction; pytest for the unit suite. Playwright is unchanged
(Gauge visuals already resolve through the feature-012 group path). No new package is added.

**Storage**: N/A — this is a pure text-extraction fix. The DB-parity engine still compares the returned
number to the read-only warehouse.

**Testing**: `pytest`. Primary gates: (1) `tests/unit/test_kpi_normalize.py` covers labeled Hebrew Gauge
strings, compact three-number Gauge strings, and existing single-value / space-thousands cases (regression);
(2) Constitution III — `pytest tests/ui/fleet_dashboard/` stays 100% green (button path and
`normalize_kpi_text` are untouched).

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework (layered portal architecture — Layer 0 `core/portal`,
Layer 2 `core/components`, domain `pages/<report>/` + `tests/ui/<report>/`).

**Performance Goals**: N/A — one extra regex scan on a short accessibility string; no extra DOM queries.

**Constraints**:
- **No domain leakage** (Constitution II): Gauge bound labels (`ערך מינימלי` / `ערך מקסימלי`, and the
  English Power BI chrome `Minimum value` / `Maximum value`) are generic visual chrome, not a report's
  metric titles. No Alerts KPI names, SQL, or CSS enter `core/`.
- **Fall back safely**: any string that is not a labeled or compact Gauge MUST keep today's
  longest-token behavior, including space-as-thousands (`"1 234"`).
- **Button-path stability** (Constitution III): `read_text`'s `role="button"` branch is not edited.
- All inline code comments MUST be English only (project rule).

**Scale/Scope**: 1 production file edited + 1 unit test file extended:

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/kpi.py` | EDIT | Gauge pre-pass in `extract_kpi_value_text`; compact number token that does not treat ASCII space as interior |
| `tests/unit/test_kpi_normalize.py` | EDIT | Labeled + compact Gauge cases; extract→normalize; existing cases still pass |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. The change stays inside the existing Layer 2 `KPI` module. No portal/SSO/
  iframe logic is touched.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Bound-scale phrases are generic Power BI Gauge chrome
  (the same class of exception as Layer 2 slicer chrome and Layer 0 last-refresh caption). They are not
  report metric titles. English equivalents are matched so the detector is locale-complete, not
  Alerts-specific. Callers still supply the opaque title.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. The button path and `normalize_kpi_text`
  are unchanged. Existing `extract_kpi_value_text` cases (single figure, space thousands, no-digit fallback)
  remain valid because they are not Gauge-shaped. A regression task re-runs `tests/ui/fleet_dashboard/`.
- **Page object discipline (IV)**: PASS. Tests still drive through `KPI.number` / the pure extract helper;
  no ad-hoc locators are added to test bodies.
- **Warehouse as source of truth (V)**: PASS. The parity engine still compares UI to the read-only DB; this
  feature only makes the Gauge's current value *parseable*.
- **Observability (VI)**: PASS. Run-report hooks, HTML/CSV artifacts, screenshots, and traces are untouched.
- **Extract shared behavior only (VII)**: PASS. The generic `KPI` component already exists (features 010 and
  012). A Gauge is a third rendering of the same titled-scalar concept, not a new abstraction. This extends
  the existing extract helper; it does not invent `GaugeKPI`.

**Result**: No violations. Complexity Tracking table left empty.

## Project Structure

### Documentation (this feature)

```text
specs/013-kpi-gauge-visuals/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (Gauge pattern + extraction decisions)
├── data-model.md        # Phase 1 output (value-resolution model update)
├── quickstart.md        # Phase 1 output (unit + regression verification)
└── contracts/
    └── kpi-component.md  # Phase 1 output (updated extract contract)
```

### Source Code (repository root)

```text
core/components/kpi.py                 # EDIT — Layer 2 generic KPI reader
  ├── _NUMBER_TOKEN                    # UNCHANGED (space-as-thousands still used on the fallback path)
  ├── _NUMBER_TOKEN_COMPACT            # NEW — digits / comma / nbsp / narrow-nbsp / decimal; no ASCII space
  ├── _GAUGE_BOUND_PAIR                # NEW — generic min/max chrome + the number that follows it
  ├── extract_kpi_value_text(raw)      # CHANGED — Gauge pre-pass, then existing longest-token fallback
  └── class KPI                        # UNCHANGED public surface and locators

tests/unit/test_kpi_normalize.py       # EDIT — add Gauge extraction cases
```

**Structure Decision**: Keep the single generic `KPI` component in Layer 2. Detection and extraction live
entirely in `extract_kpi_value_text` so `_read_group_value` and the parity engine need zero changes. Do not
add a `kind == "gauge"` locator branch — Gauges already resolve as `role="group"` after feature 012.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1 artifacts. Still PASS on I–VII:

- Design confines Hebrew/English bound labels to a chrome regex (`_GAUGE_BOUND_PAIR`), never as report
  titles or SQL.
- Fallback path preserves `_NUMBER_TOKEN` (space-as-thousands) so existing unit cases stay the contract.
- No new Layer 2 type; public `KPI` signatures unchanged.
- No unresolved `NEEDS CLARIFICATION` markers remain.