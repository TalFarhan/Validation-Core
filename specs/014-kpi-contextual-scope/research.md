# Phase 0 Research: KPI Contextual Scope

**Feature**: 014-kpi-contextual-scope | **Date**: 2026-10-12

No `NEEDS CLARIFICATION` markers in Technical Context. Research records host-resolution decisions.

## Decision 1 — Optional `scope` on the existing methods (not a new type)

**Decision**: Add `scope: str | None = None` to `card`, `read_text`, `value`, `number`, and
`_resolve_card`. Add `_scope_host(scope)` that returns the search root. Do not invent `ScopedKPI`.

**Rationale**: Callers already hold one `KPI` instance per iframe (`db_parity_engine` does this). A
per-call scope keeps that model and leaves one-argument calls valid (Constitution III). A second
class would fork `KPI.number(title)`.

**Alternatives considered**:
- *Constructor-level default scope*: rejected — one iframe often has many sections; scope is per
  metric, not per page.
- *Require callers to pass a Playwright `Locator` host*: rejected — leaks DOM details into every
  contract/page and breaks the opaque-string style of `title`.

## Decision 2 — Host is a named `role="group"`, then a `has_text` group filter

**Decision**: `_scope_host(scope)`:

1. Treat `None` or whitespace-only as "no scope" → return `self._frame`.
2. Else `self._frame.get_by_role("group", name=re.compile(re.escape(scope))).first`. If
   `.count() > 0`, use that locator (accessible name of the section group).
3. Else `self._frame.get_by_role("group").filter(has_text=re.compile(re.escape(scope))).first`.

`_resolve_card` then runs the existing button→group title search on that host.

**Rationale**:
- Power BI section chrome is typically a `role="group"` whose accessible name is the header.
- `name=` matches the group's own name and does not select an outer group that merely *contains*
  the header text.
- `has_text` fallback covers groups whose accessible name is empty but whose descendant text is
  the header. Restricting the filter to `role="group"` avoids matching the report root
  (`locator("*").filter(has_text=scope)` would).
- `re.escape` keeps the caller's string literal (same as titles).

**Alternatives considered**:
- *`locator("*").filter(has_text=scope)` only*: rejected — matches the iframe/report ancestor that
  contains every section; scoped search would still be global.
- *Heading + sibling walk*: rejected — Power BI heading/visual sibling structure is unstable.
- *CSS / visual GUID*: rejected — report-specific, Constitution II.

## Decision 3 — Locate only; do not change extract/normalize

**Decision**: `_read_group_value`, `extract_kpi_value_text`, Gauge parsing (013), and
`normalize_kpi_text` stay as they are. Scope only changes **which** node is read.

**Rationale**: Duplicate titles are a locator collision, not a parse bug. Mixing the two concerns
would risk regressing unique-title and Gauge cases.

## Decision 4 — Parity YAML `scope` is out of scope

**Decision**: Do not add a `scope` key to `alerts_contract.yaml` or `validate_dashboard_generic` in
this feature. Callers that need disambiguation pass `scope=` in Python (`KPI.number(title, scope=...)`).

**Rationale**: The request lists only the `KPI` component. The engine can grow a contract field later
without changing this locate design.

**Alternatives considered**:
- *Add optional YAML `scope` now*: deferred — useful, but not requested; would expand the consumer
  contract in the same change.

## Open Questions

None. Follow-on (not this plan): optional `scope` on parity contract metrics.
