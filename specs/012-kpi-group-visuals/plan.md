# Implementation Plan: Enhance Generic KPI Component to Support Group Visuals

**Branch**: `012-kpi-group-visuals` | **Date**: 2026-10-11 | **Spec**: inline feature request (no `spec.md`; `/speckit-plan` invoked directly)

**Input**: Feature request — the Alerts pilot metrics render in Power BI as `role="group"` visuals
(a heading plus a data `img`) rather than the `role="button"` KPI cards the generic Layer 2 `KPI`
component currently assumes. Teach `core/components/kpi.py` to locate and read both renderings.

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command).

## Summary

The generic `KPI` component (`core/components/kpi.py`, Layer 2, introduced by feature 010) finds a KPI
by its opaque title via `get_by_role("button", name=title)` and reads the value from the card's last
`<p>`. The Alerts report renders its pilot metrics as `role="group"` visuals instead: a group whose
accessible name is the title, containing a heading and a data `img` whose `aria-label` carries the
number (often bundled with the Hebrew title). Against those visuals the button locator never matches,
so the parity engine cannot read the UI value.

This feature extends the **existing** generic component (no new abstraction, no second component) with a
**button→group fallback** locator strategy and group-aware value extraction: when no `role="button"`
card carries the title, fall back to `role="group"`, read the value from the inner `img`'s `aria-label`
(then `title`, then the group's own text), and pull the numeric token out of the possibly-title-bundled
label before handing it to the existing normalize → parse pipeline. The `role="button"` path is
unchanged byte-for-byte, so the fleet smoke contract is unaffected.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API) for DOM/role locators; pytest for the unit suite. No new
dependency is added.

**Storage**: N/A — this is a UI-reading component. The DB-parity engine that consumes it still compares
against the read-only Alerts DB, unchanged.

**Testing**: `pytest`. Primary gates: (1) `tests/unit/test_kpi_normalize.py` covers the pure extraction
logic (`extract_kpi_value_text`) with group-style labels; (2) regression gate — `pytest tests/ui/fleet_dashboard/`
stays 100% green (Constitution III), since the fleet KPIs use the untouched `role="button"` path.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework (layered portal architecture — Layer 0 `core/portal`,
Layer 2 `core/components`, domain `pages/<report>/` + `tests/ui/<report>/`).

**Performance Goals**: N/A — the fallback adds at most one extra role query (guarded by a `.count()` check)
only when the button is absent; the button path keeps its original single-locator cost.

**Constraints**:
- **No domain leakage** (Constitution II): only generic Power BI primitives (`role="button"`, `role="group"`,
  `img`, `aria-label`/`title`, bidi marks) appear in `core/`. The opaque title string is still supplied by the
  caller; no Alerts KPI names enter `core/`.
- **No button-path drift** (Constitution III): the existing `role="button"` branch of `read_text` is
  preserved exactly (value from the last `<p>`), so fleet smoke behavior cannot change.
- All inline code comments MUST be English only (project rule).

**Scale/Scope**: 1 production file edited + 1 unit test file extended:

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/kpi.py` | EDIT | Button→group fallback locator + group value extraction; refactor shared `_strip_bidi`; add `extract_kpi_value_text` |
| `tests/unit/test_kpi_normalize.py` | EDIT | Add coverage for `extract_kpi_value_text` and the extract→normalize chain |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. The change stays inside the existing Layer 2 `KPI` component. No portal/SSO/
  iframe logic is touched; the caller still composes `KPI` with the report frame.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Only generic ARIA roles and attributes are referenced.
  Titles remain opaque caller inputs; no Alerts strings, SQL, or CSS enter `core/`.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. The `role="button"` path is unchanged, so
  the fleet smoke suite is unaffected. A regression task re-runs `tests/ui/fleet_dashboard/`.
- **Page object discipline (IV)**: PASS. Tests/pages still drive the browser through the component's public
  API (`number`/`value`/`read_text`/`card`); no ad-hoc locators are added to test bodies.
- **Warehouse as source of truth (V)**: PASS. The parity engine still compares UI to the read-only DB; this
  feature only makes the UI value *readable* for group-rendered metrics.
- **Observability (VI)**: PASS. Run-report hooks, HTML/CSV artifacts, screenshots, and traces are untouched.
- **Extract shared behavior only (VII)**: PASS with justification. Principle VII says "do not genericize KPI
  cards until a second report requires them." The generic `KPI` component already exists (feature 010) and is
  consumed by the report-agnostic parity engine; a **second** report (Alerts) now renders KPIs as groups, which
  is exactly the trigger the principle authorizes. This extends the existing shared API to a real second need —
  it does not invent an unused abstraction.

**Result**: No violations. Complexity Tracking table left empty.

## Project Structure

### Documentation (this feature)

```text
specs/012-kpi-group-visuals/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (locator + extraction decisions)
├── data-model.md        # Phase 1 output (component surface + value-resolution model)
├── quickstart.md        # Phase 1 output (unit + regression verification)
└── contracts/
    └── kpi-component.md  # Phase 1 output (public API + behavior contract)
```

### Source Code (repository root)

```text
core/components/kpi.py                 # EDIT — Layer 2 generic KPI reader
  ├── _strip_bidi(raw)                 # NEW helper (factored out of normalize_kpi_text)
  ├── normalize_kpi_text(raw)          # unchanged behavior (now uses _strip_bidi)
  ├── extract_kpi_value_text(raw)      # NEW — pull numeric token from a mixed/group label
  └── class KPI
        ├── _resolve_card(title)       # NEW — returns (locator, kind: "button"|"group")
        ├── card(title)                # now delegates to _resolve_card (signature unchanged)
        ├── _read_group_value(card)    # NEW — read value from group's img aria-label/title/text
        ├── read_text(title)           # branches on kind; button path unchanged
        ├── value(title)               # unchanged (normalize_kpi_text(read_text))
        └── number(title)              # unchanged (_to_number(value))

tests/unit/test_kpi_normalize.py       # EDIT — add extract_kpi_value_text coverage
```

**Structure Decision**: Keep the single generic `KPI` component in Layer 2. Do not introduce a separate
`GroupKPI` class or a second component — the two renderings are the same business concept (a titled scalar)
and the parity engine already depends on one uniform `KPI.number(title)` API. Button and group resolution
are collapsed behind `_resolve_card`, so callers and the engine need zero changes.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |
