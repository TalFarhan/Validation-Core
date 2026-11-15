# Contract: Generic KPI Component — Contextual Scope (Layer 2)

**Feature**: 014-kpi-contextual-scope | **Module**: `core/components/kpi.py` | **Date**: 2026-10-12

Extends the feature-012/013 UI contract. Existing one-argument calls remain valid. This document
adds the optional `scope` parameter.

## Public Surface

```python
class KPI:
    def __init__(self, page: Page, frame: FrameLocator, timeout_ms: int | None = None) -> None: ...
    def card(self, title: str, scope: str | None = None) -> Locator: ...
    def read_text(self, title: str, scope: str | None = None) -> str: ...
    def value(self, title: str, scope: str | None = None) -> str: ...
    def number(self, title: str, scope: str | None = None) -> int | float: ...

def normalize_kpi_text(raw: str) -> str: ...
def extract_kpi_value_text(raw: str) -> str: ...
```

`tests/helpers/db_parity_engine.py` continues to call `KPI.number(name)` with no `scope` and
**requires no change**.

## Behavioral Contract

### `scope` (all of `card` / `read_text` / `value` / `number`)

- MUST default to `None`.
- MUST treat `""` and whitespace-only as `None` (global iframe search).
- When set to a non-empty string, MUST resolve a host via `_scope_host` and search for `title`
  only under that host.
- MUST remain opaque: `core/` MUST NOT embed report section titles.

### `_scope_host(scope) -> FrameLocator | Locator`

1. No scope → `self._frame`.
2. Else `get_by_role("group", name=re.compile(re.escape(scope))).first` if present.
3. Else `get_by_role("group").filter(has_text=re.compile(re.escape(scope))).first`.

MUST NOT use `locator("*").filter(has_text=scope)`.

### `card` / `read_text` / `value` / `number`

Unchanged from 012/013 except the search root is the host above. Button-first then group;
group values still go through `extract_kpi_value_text` (Gauge-aware).

## Invariants

- One-argument calls behave as they did before this feature.
- No domain leakage of section or KPI titles.
- Extract/normalize semantics unchanged.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Extract/normalize unchanged | `tests/unit/test_kpi_normalize.py` |
| One-argument callers still type-check / run | `tests/helpers/db_parity_engine.py` still `KPI.number(name)` |
| Fleet / unique-title path unaffected | `pytest tests/ui/fleet_dashboard/` (Constitution III) |
