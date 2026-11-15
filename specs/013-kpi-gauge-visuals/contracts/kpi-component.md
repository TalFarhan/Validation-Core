# Contract: Generic KPI Component — Gauge Extraction (Layer 2)

**Feature**: 013-kpi-gauge-visuals | **Module**: `core/components/kpi.py` | **Date**: 2026-10-12

Extends the feature-012 UI contract. Public `KPI` signatures are unchanged. This document specifies the
**new** `extract_kpi_value_text` guarantees for Power BI Gauge labels and restates the fallback that
standard cards rely on.

## Public Surface (unchanged signatures)

```python
class KPI:
    def __init__(self, page: Page, frame: FrameLocator, timeout_ms: int | None = None) -> None: ...
    def card(self, title: str) -> Locator: ...
    def read_text(self, title: str) -> str: ...
    def value(self, title: str) -> str: ...
    def number(self, title: str) -> int | float: ...

def normalize_kpi_text(raw: str) -> str: ...
def extract_kpi_value_text(raw: str) -> str: ...   # behavior extended
```

Existing callers (`tests/helpers/db_parity_engine.py` → `KPI.number(name)`) require **no changes**.

## Behavioral Contract

### `card` / `read_text` / `value` / `number`

Unchanged from feature 012, except that when `read_text` takes the group path, `extract_kpi_value_text`
now isolates a Gauge's **current** value instead of concatenating min/max/current.

### `extract_kpi_value_text(raw) -> str`

MUST strip Power BI bidi marks, then:

1. **Labeled Gauge** — if the string contains a bound-chrome pair (`ערך מינימלי` / `ערך מקסימלי` /
   `Minimum value` / `Maximum value`, case-insensitive English, each followed by a compact number and an
   optional `.`): MUST remove every such pair, then return the longest `_NUMBER_TOKEN` in the remainder
   (or the cleaned remainder if it has no digits).
2. **Compact Gauge** — else if compact tokenization (no ASCII space as an interior thousands separator)
   yields **exactly three** tokens: MUST return the last token, stripped.
3. **Fallback (standard KPI)** — else MUST keep the feature-012 behavior: longest `_NUMBER_TOKEN`
   (ASCII space allowed as interior), or the cleaned text when no digits are present.

MUST be idempotent for an already-clean single number (`"1,234"` → `"1,234"`).

MUST NOT interpret the caller's KPI title; bound phrases are generic Gauge chrome only.

## Examples (normative)

| Raw | Shape | `extract_kpi_value_text` | `normalize_kpi_text(...)` |
|-----|-------|--------------------------|---------------------------|
| `distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337.` | labeled | `3` | `3` |
| `Minimum value 0. Maximum value 1,337. 3` | labeled (EN) | `3` | `3` |
| `0 1,337 3` | compact | `3` | `3` |
| `אזורי התרעה 1,234` | fallback | `1,234` | `1234` |
| `Population 1 234` | fallback (space thousands) | `1 234` | `1234` |
| `avg 3.5 days` | fallback | `3.5` | `3.5` |
| `N/A` | fallback | `N/A` | `N/A` |

The pre-fix compact/labeled failure (`"1337133733"` or `"013373"`) MUST NOT occur.

## Invariants

- **No domain leakage**: no report metric titles, SQL, or CSS in `core/`.
- **Button path stability**: button-rendered cards never call this helper → fleet smoke contract holds.
- **Uniform numeric API**: `number(title)` returns the Gauge's current reading, not its scale max.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Labeled Hebrew Gauge yields the current value | `tests/unit/test_kpi_normalize.py` (new Gauge cases) |
| Compact three-number Gauge yields the last token | same |
| Standard single-figure / space-thousands / no-digit cases unchanged | existing `test_extract_*` cases |
| extract → normalize is parseable for Gauge strings | new extract-then-normalize Gauge rows |
| Button path / fleet contract unaffected | `pytest tests/ui/fleet_dashboard/` |
