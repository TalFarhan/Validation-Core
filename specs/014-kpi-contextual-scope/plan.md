# Implementation Plan: Contextual Scoping for Duplicate KPI Visual Names

**Branch**: `014-kpi-contextual-scope` | **Date**: 2026-10-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature request — reports can render several KPI cards with the same title under different
section headers. Global `get_by_role(..., name=title).first` is ambiguous. Add an optional opaque
`scope` parameter to the Layer 2 `KPI` component so the title search is chained inside a parent
container.

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command).

## Summary

`KPI._resolve_card(title)` always searches `self._frame`. When two visuals share a title (e.g. "היום"
under two section groups), `.first` is undefined. This feature threads an optional `scope: str | None = None`
through `card` / `read_text` / `value` / `number` into `_resolve_card`. A new `_scope_host(scope)`
returns the iframe when scope is absent, otherwise a parent `role="group"` associated with that
opaque string (accessible-name match first, `has_text` filter fallback). The existing button→group
title search then runs **on that host**. Extract/normalize (including Gauge parsing from 013) is
untouched. Existing one-argument callers stay valid.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright sync API (`FrameLocator` / `Locator.get_by_role`, `.filter`).
No new package.

**Storage**: N/A — locate-only change on a live DOM.

**Testing**: `pytest`. Gates: (1) existing `tests/unit/test_kpi_normalize.py` stays green (extract
path unchanged); (2) Constitution III — `pytest tests/ui/fleet_dashboard/` stays 100% green (default
`scope=None` path). No new unit suite is required: host resolution needs a live iframe. Optional
later e2e can pass `scope` from a domain page.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework (Layer 0 `core/portal`, Layer 2 `core/components`,
domain `pages/<report>/` + `tests/ui/<report>/`).

**Performance Goals**: N/A — one extra role query only when `scope` is set.

**Constraints**:
- **No domain leakage** (Constitution II): `scope` and `title` remain opaque caller strings. No
  section titles such as "היום", "אתמול", or "סה\"כ בטווח שנבחר" enter `core/`.
- **Backward compatibility** (Constitution III): omitting `scope` MUST keep today's iframe-wide
  button→group `.first` search.
- **Do not match the report root**: never `locator("*").filter(has_text=scope)` — that ancestor
  contains every section.
- All inline code comments MUST be English only.

**Scale/Scope**: 1 production file edited. Parity YAML / `db_parity_engine` are **out of scope**
(callers pass `scope` in Python).

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/kpi.py` | EDIT | `_scope_host`; thread `scope` through `_resolve_card` / `card` / `read_text` / `value` / `number` |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. Change stays in Layer 2 `KPI`. No portal/SSO/iframe wait changes.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Scope is an opaque argument, same as title.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. New parameter is optional with
  default `None`; `KPI.number(title)` and the parity engine need no edit. Fleet smoke is the
  regression gate.
- **Page object discipline (IV)**: PASS. Tests/pages still go through `KPI`; no ad-hoc locators in
  test bodies.
- **Warehouse as source of truth (V)**: PASS. Only the UI locator is narrowed; comparison is still
  UI vs DB.
- **Observability (VI)**: PASS. Run-report hooks untouched.
- **Extract shared behavior only (VII)**: PASS. The generic `KPI` already exists (010–013). Duplicate
  titles on a real report are a second need for the same titled-scalar API, not a new abstraction.

**Result**: No violations. Complexity Tracking table left empty.

## Project Structure

### Documentation (this feature)

```text
specs/014-kpi-contextual-scope/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Inline request captured as user stories
├── research.md          # Phase 0 output (host strategy)
├── data-model.md        # Phase 1 output (resolution model)
├── quickstart.md        # Phase 1 output (verification)
└── contracts/
    └── kpi-component.md  # Phase 1 output (updated public API)
```

### Source Code (repository root)

```text
core/components/kpi.py                 # EDIT — Layer 2 generic KPI reader
  ├── KPI._scope_host(scope)           # NEW — FrameLocator | Locator
  ├── KPI._resolve_card(title, scope)  # CHANGED — search on host
  ├── KPI.card(title, scope=None)
  ├── KPI.read_text(title, scope=None)
  ├── KPI.value(title, scope=None)
  └── KPI.number(title, scope=None)
  # extract_kpi_value_text / normalize_kpi_text / _read_group_value UNCHANGED
```

**Structure Decision**: One optional parameter on the existing component. Do not add a `ScopedKPI`
class or a second locator module.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- Design keeps section titles out of `core/`.
- Default `scope=None` preserves the feature-012/013 locate path.
- Host is always a `role="group"` (or the iframe), never a `*` has_text ancestor.
- No unresolved `NEEDS CLARIFICATION` markers remain.
