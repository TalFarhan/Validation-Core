# Implementation Plan: Advanced Power BI Visual Components

**Branch**: `015-advanced-visual-components` | **Date**: 2026-10-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/015-advanced-visual-components/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration` at the time of this plan).

## Summary

Layer 2 can already read a KPI's current figure and can ignore Gauge min/max chrome (features 012–014).
This feature adds the missing generic readers, still with opaque caller strings:

- `extract_gauge_scale` / `KPI.scale` return `value`, `minimum`, and `maximum`. A slash denominator is
  `maximum`. `KPI.number` and `extract_kpi_value_text` stay on their current contracts.
- `classify_presence` separates a rendered number, including 0, from a visual with no numeric token and
  no data mark. A missing series slot stays null, not 0.
- A new `Chart` component reads bar/column categories, checks numeric descending order, counts category
  rows (Top-N is the caller's assertion), and returns legend series.
- `displayed_title` returns the full title currently shown on a visual located by an opaque anchor.

Fleet chart tooltips, drilldown, and hover stay on `pages/fleet_dashboard/`. No report name, metric
title, or concrete denominator is added under `core/`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright sync API (`FrameLocator`, `Locator.get_by_role`, `.filter`) and the
standard library (`re`, `dataclasses`). No new package.

**Storage**: N/A — readers over a live report iframe plus pure parsers tested without a browser.

**Testing**: `pytest`. Gates: (1) existing `tests/unit/test_kpi_normalize.py` stays green; (2) new unit
tests for scale parsing, presence, and chart order/count/series alignment; (3) Constitution III —
`pytest tests/ui/fleet_dashboard/` stays 100% green. Chart DOM location is exercised later by a domain
page; this plan does not require a live portal for the pure helpers.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework (Layer 0 `core/portal`, Layer 2 `core/components`,
domain `pages/<report>/` + `tests/ui/<report>/`).

**Performance Goals**: N/A — one visual lookup and a bounded scan of that visual's marks and text
nodes (same order of cost as today's fleet chart label harvest, capped).

**Constraints**:
- **No domain leakage** (Constitution II): titles, scopes, category labels, and series names are opaque
  caller data. Forbidden in `core/`: report names, metric titles, and any hardcoded denominator.
- **Backward compatibility** (Constitution III): `KPI.number`, `extract_kpi_value_text`, and
  `normalize_kpi_text` keep today's results. Optional `scope` stays optional.
- **Zero is not empty**: a parsed 0 is a value; null means absent. Missing bounds are null, including
  when the other bound is 0.
- **Do not migrate fleet chart interaction**: tooltips, drilldown, and hover remain on the fleet page.
- All inline code comments MUST be English only.
- Generic Gauge chrome already accepted in feature 013 (`ערך מינימלי`, `ערך מקסימלי`,
  `Minimum value`, `Maximum value`) may still be recognized. That chrome is Power BI scale wording,
  not a report title.

**Scale/Scope**: Two production modules edited or added for parsing (`kpi.py`, new chart/visual
helpers). Fleet page and the parity engine are out of scope except the smoke regression gate.

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/kpi.py` | EDIT | `extract_gauge_scale`; `KPI.scale`; raw label read; delegate scope host |
| `core/components/visual.py` | NEW | `scope_host`, `classify_presence`, displayed-title text |
| `core/components/chart.py` | NEW | Bar/column reader: categories, descending check, row count, series |
| `core/components/__init__.py` | EDIT | Export `Chart` |
| `tests/unit/test_gauge_scale.py` | NEW | Labeled, compact, slash, single-figure, null bounds |
| `tests/unit/test_visual_state.py` | NEW | Rendered 0 versus empty; null slot versus 0 |
| `tests/unit/test_chart_shape.py` | NEW | Descending order, category count, two-series alignment |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. No change to `core/portal` or `ReportShell`. Domain pages keep
  composing the shell.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. New APIs take opaque title and scope strings
  and return strings and numbers. Gauge chrome reused from feature 013 is generic scale wording.
  Slicer-dependent title phrases are caller assertions only.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. `KPI.number` / extract / normalize
  are unchanged, so parity and fleet KPI calls stay valid. Fleet chart methods are not rewritten.
  Fleet smoke remains the regression gate.
- **Page object discipline (IV)**: PASS. Tests reach charts and KPIs through Layer 2 or the domain
  page. No new locators in test bodies.
- **Warehouse as source of truth (V)**: PASS. These readers only structure UI text. They do not embed
  SQL or compare to the warehouse.
- **Observability (VI)**: PASS. HTML/CSV run reports, screenshots, and traces are untouched.
- **Extract shared behavior only (VII)**: PASS with the justification in Complexity Tracking. Bar/column
  read, gauge scale, and empty-versus-zero now recur beyond a single report. Fleet-only interaction
  (tooltip, drilldown, hover) is not extracted.

**Result**: No unjustified violations. The new Layer 2 chart surface is recorded below because it goes
past slicer chrome.

## Project Structure

### Documentation (this feature)

```text
specs/015-advanced-visual-components/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # User stories and requirements
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── gauge-scale.md
    ├── visual-reading.md
    └── chart-component.md
```

### Source Code (repository root)

```text
core/components/kpi.py                     # EDIT — scale parser + KPI.scale
  ├── extract_gauge_scale(raw) -> GaugeScale
  ├── KPI._read_raw(title, scope)          # label before current-value extraction
  └── KPI.scale(title, scope=None) -> GaugeScale
  # extract_kpi_value_text / normalize_kpi_text / number() UNCHANGED

core/components/visual.py                  # NEW — shared generic visual helpers
  ├── scope_host(frame, scope)             # feature 014 host rule, one implementation
  ├── classify_presence(numbers, mark_count) -> "value" | "empty"
  └── displayed_title_text(container) -> str

core/components/chart.py                   # NEW — Layer 2 bar/column reader
  ├── Chart.read(title, scope=None) -> ChartReading
  ├── Chart.category_count(...) -> int
  ├── Chart.is_descending(..., series_index=0) -> bool
  └── Chart.displayed_title(...) -> str

pages/fleet_dashboard/main_dashboard_page.py   # UNCHANGED — tooltips, drilldown, hover
tests/helpers/db_parity_engine.py              # UNCHANGED — still KPI.number(name)
```

**Structure Decision**: Extend `KPI` for gauge scale (same titled-scalar visual). Add `Chart` for
bar/column structure, which is not a scalar. Put scope host, presence, and displayed title in
`visual.py` so `KPI` and `Chart` share one host rule and one empty-versus-zero rule. Do not add a
`Gauge` or `Map` class. A map is empty or not by `classify_presence` on a container the caller
already located.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Layer 2 chart reader beyond slicer chrome (Constitution governance; VII until a second report needs it) | The same bar/column questions — descending order, category count, legend series, blank versus 0 — now show up on more than one dashboard. The framework rule is that a second occurrence is generic. | Copying another page-object chart parser per report forks Power BI chrome the way Constitution I forbids for portal steps. Leaving the logic only on the fleet page blocks the next dashboard. Fleet tooltip, drilldown, and hover stay put, so the extract is the shared read path only. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the chart-reader row above still the only
justified expansion:

- Design returns numbers and opaque strings. No report title, metric name, or denominator literal is
  part of `core/`.
- `KPI.number` and `extract_kpi_value_text` are specified as unchanged, including the feature 013
  current-value rules. Slash pairs are visible only through `KPI.scale`.
- Presence uses null for "no number" and 0 only for a parsed zero. A missing series slot is null.
- Displayed title is the visual's current text. The anchor used to find it is a caller argument.
- Scope host matches feature 014, including the ban on `locator("*").filter(has_text=...)`.
- No unresolved `NEEDS CLARIFICATION` markers remain.
