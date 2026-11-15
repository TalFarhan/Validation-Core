# Contract: Gauge Scale (Layer 2)

**Feature**: 015-advanced-visual-components | **Module**: `core/components/kpi.py` | **Date**: 2026-10-13

Extends the feature 012–014 KPI contract. `card`, `read_text`, `value`, `number`,
`extract_kpi_value_text`, and `normalize_kpi_text` keep their current results. This document adds
the scale reader.

## Public Surface

```python
class GaugeScale(TypedDict):
    state: Literal["value", "empty"]
    value: int | float | None
    minimum: int | float | None
    maximum: int | float | None

def extract_gauge_scale(raw: str) -> GaugeScale: ...

class KPI:
    def scale(self, title: str, scope: str | None = None) -> GaugeScale: ...
    # number / value / read_text / card unchanged, including optional scope
```

`tests/helpers/db_parity_engine.py` continues to call `KPI.number(name)` and requires no change.

## `extract_gauge_scale(raw) -> GaugeScale`

MUST strip bidi marks, then apply the first matching shape:

1. **Labeled** — one or more generic bound pairs (`ערך מינימלי`, `ערך מקסימלי`, `Minimum value`,
   `Maximum value`, English case-insensitive), each followed by a compact number and an optional
   period. A minimum-word pair sets `minimum`. A maximum-word pair sets `maximum`. After the pairs
   are removed, `value` is the longest remaining numeric token, or `None` when none remain.
2. **Compact** — else when compact tokenization yields exactly three tokens: `minimum`, `maximum`,
   `value` are those tokens in that order.
3. **Slash pair** — else when the text contains exactly one `number / number` (optional whitespace
   around `/`) and no other number: `value` is the left number, `maximum` is the right number,
   `minimum` is `None`.
4. **Single figure** — else when one number remains: `value` is that number; both limits are `None`.
5. **No number** — else `value`, `minimum`, and `maximum` are `None` and `state` is `"empty"`.

Each captured token MUST be passed through `normalize_kpi_text` and then parsed as `int` when
integral, otherwise `float`.

`state` MUST be `"value"` when `value` is not `None` (including `0`). The pure function does not see
data marks; mark-based presence is applied by `KPI.scale` via `classify_presence` (see
`visual-reading.md`).

MUST NOT read a caller title as a bound. Bound phrases are the generic chrome above only.

## `KPI.scale(title, scope=None)`

- MUST resolve the card with the feature 014 host and button-then-group rule.
- MUST parse the raw label (group: `img` `aria-label`, then `img` `title`, then group text; button:
  last `p` text) with `extract_gauge_scale` **before** current-value extraction.
- If the pure parse has `value is None`, MUST combine it with the card's data-mark count through
  `classify_presence`. Marks and a still-missing figure MUST yield `state="value"` and `value=None`.
  No marks MUST yield `state="empty"`.
- `scope` MUST default to `None` and MUST treat blank as no scope.

## Examples (normative)

Placeholders below are synthetic. They are not constants to copy into `core/`.

| Raw | Shape | `value` | `minimum` | `maximum` | `state` |
|-----|-------|---------|-----------|-----------|---------|
| `Series 3. ערך מינימלי 0. ערך מקסימלי 1,337.` | labeled | `3` | `0` | `1337` | `value` |
| `Minimum value 0. Maximum value 1,337. 3` | labeled | `3` | `0` | `1337` | `value` |
| `0 1,337 3` | compact | `3` | `0` | `1337` | `value` |
| `3 / 10` | slash | `3` | `None` | `10` | `value` |
| `1,234` | single | `1234` | `None` | `None` | `value` |
| `0` | single | `0` | `None` | `None` | `value` |
| `` | none | `None` | `None` | `None` | `empty` |

`extract_kpi_value_text` on these strings MUST stay as feature 013 defines it. In particular, a slash
pair is not a 013 gauge, and `KPI.number` MUST NOT start returning the left-hand number solely
because `scale` exists.

## Invariants

- No report title, metric name, or denominator literal in `core/`.
- `0` is a value or a bound. It is not the encoding of "missing".
- Existing one-argument and `scope=` KPI calls keep their results.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Labeled, compact, slash, single, and empty parses | `tests/unit/test_gauge_scale.py` |
| Feature 013 extract/normalize rows unchanged | `tests/unit/test_kpi_normalize.py` |
| `KPI.number(name)` still the parity call | `tests/helpers/db_parity_engine.py` |
| Fleet smoke | `pytest tests/ui/fleet_dashboard/` |
