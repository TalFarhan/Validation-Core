# Phase 1 Data Model: KPI Contextual Scope

**Feature**: 014-kpi-contextual-scope | **Date**: 2026-10-12

No persistent entities. This updates the locate side of the KPI value-resolution model from features
012/013.

## Conceptual Entities

### ScopeHost

The root against which a title search runs.

| Field | Type | How obtained |
|-------|------|----------------|
| `scope` | `str \| None` | Opaque caller string. Blank/`None` → no scope. |
| `host` | `FrameLocator \| Locator` | `_scope_host(scope)` (see rules). |

### KpiVisual (locate rules extended)

| Field | Type | Notes |
|-------|------|-------|
| `title` | str | Opaque accessible name of the card. |
| `scope` | `str \| None` | Opaque section / parent-group name. |
| `kind` | `"button"` \| `"group"` | Unchanged: button if present under the host, else group. |
| `locator` | Playwright `Locator` | `.first` match under `host`. |

### RawValueText / KpiValue

Unchanged from 012/013. Scope does not affect extract or normalize.

## Transformation Pipeline

```text
title, scope
  └─ _scope_host(scope)
       scope empty ──────────────► self._frame
       else named group? ────────► group[name=scope]
       else ─────────────────────► group.filter(has_text=scope).first
            └─ _resolve_card(title, scope) on host
                 button[name=title].first if present
                 else group[name=title].first
                      └─ read_text (button last <p> / group img) ─► extract ─► normalize ─► number
```

## Rules & Invariants

1. **Default is global**: `scope is None` or `not scope.strip()` → host is `self._frame`.
2. **Name before has_text**: a group whose accessible name equals `scope` wins over a larger group
   that only contains the text.
3. **No star-filter**: never `locator("*").filter(has_text=scope)`.
4. **Title search unchanged under the host**: button first, then group; `re.escape(title)`.
5. **Extract path untouched**: `_read_group_value` → `extract_kpi_value_text` (incl. Gauge) →
   `normalize_kpi_text`.
6. **Opacity**: `core/` does not interpret `scope` or `title` as domain language.
7. **English comments only**.

## New / Changed Symbols

| Symbol | Kind | Status |
|--------|------|--------|
| `KPI._scope_host(scope)` | method | NEW |
| `KPI._resolve_card(title, scope=None)` | method | CHANGED (default preserves old behavior) |
| `KPI.card/read_text/value/number` | methods | CHANGED (optional `scope=None`) |
| extract / normalize / `_read_group_value` | — | UNCHANGED |
