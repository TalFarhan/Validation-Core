# Feature Specification: Contextual Scoping for Duplicate KPI Visual Names

**Feature Branch**: `014-kpi-contextual-scope`
**Created**: 2026-10-12
**Status**: Ready for planning
**Input**: Inline `/speckit-plan` request — a report can render several KPI cards with the same title
under different section headers. Global title search is ambiguous. Add an optional opaque `scope` to the
generic Layer 2 `KPI` component so callers can search inside one section.

## Problem Statement

`KPI._resolve_card(title)` searches the whole report iframe for `role="button"` then `role="group"` whose
accessible name matches `title`, and takes `.first`. When two or more visuals share a title (e.g. "היום",
"אתמול", "סה\"כ בטווח שנבחר") under different section headers, that global query either fails or returns
the wrong card. Callers need a way to name the **section** without putting those section strings into
`core/`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Scoped KPI lookup (Priority: P1)

As a validation engineer, I pass an optional `scope` (the section header / parent group name) with a
duplicate KPI title so `KPI.number(title, scope=...)` reads the card **inside that section**.

**Why this priority**: This is the failure mode; without it, duplicate titles are unreadable.

**Independent Test**: Given two group/button visuals that share a title under different named parent
groups, `card(title, scope=section_a)` resolves inside section A and `card(title, scope=section_b)`
resolves inside section B. `scope` is an opaque caller string — no report titles live in `core/`.

**Acceptance Scenarios**:

1. **Given** a `scope` that matches a parent `role="group"` accessible name, **When** `read_text` /
   `value` / `number` / `card` are called with that scope, **Then** the title search is chained from
   that container, not the full iframe.
2. **Given** a `scope` that does not match a named group, **When** resolving, **Then** the host falls
   back to a `role="group"` filtered by `has_text=scope` (still a container, not the report root).
3. **Given** `scope=None` or a blank string, **When** resolving, **Then** behavior matches today's
   global iframe search.

---

### User Story 2 — Backward-compatible global search (Priority: P2)

As a validation engineer, existing callers that omit `scope` (`KPI.number(title)`, the parity engine)
keep working with no code changes.

**Why this priority**: Constitution III — public signatures must stay compatible.

**Independent Test**: `KPI.number(title)` / `value(title)` / `read_text(title)` / `card(title)` still
accept a single title argument. `tests/helpers/db_parity_engine.py` is unchanged. Existing unit extract
tests stay green.

**Acceptance Scenarios**:

1. **Given** no `scope` argument, **When** a unique title is looked up, **Then** the result is identical
   to pre-feature behavior (button first, then group, `.first`).
2. **Given** existing parity / fleet callers, **When** they call `KPI.number(name)`, **Then** they need
   no edit.

---

### Edge Cases

- `scope` is opaque: `core/` MUST NOT hardcode section titles such as "היום" or "סה\"כ בטווח שנבחר".
- Empty / whitespace-only `scope` is treated as "no scope".
- Scope host MUST be a section container (`role="group"`), not `locator("*").filter(has_text=scope)`,
  which would match the report root that contains every section.

## Requirements

### Functional Requirements

- **FR-001**: `card`, `read_text`, `value`, and `number` MUST accept `scope: str | None = None`.
- **FR-002**: When `scope` is a non-empty string, title search MUST run inside a host container
  associated with that scope (named `role="group"` first; `has_text` group filter as fallback).
- **FR-003**: When `scope` is omitted or blank, title search MUST use the existing full-iframe
  button→group strategy.
- **FR-004**: `_read_group_value` and the extract/normalize pipeline MUST stay unchanged (scope is
  locate-only).
- **FR-005**: All inline comments in production code MUST be English only.

### Non-Goals

- No YAML `scope` field and no parity-engine change in this feature (callers pass `scope` in Python).
- No new `GaugeKPI` / section component.
- No hardcoded report section titles in `core/`.

## Success Criteria

- Duplicate titles are disambiguated when the caller supplies a scope string.
- Existing `KPI.number(title)` callers remain valid.
- `pytest tests/ui/fleet_dashboard/` stays 100% green (regression gate).
