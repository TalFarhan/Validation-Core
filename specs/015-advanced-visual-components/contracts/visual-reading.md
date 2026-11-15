# Contract: Visual Presence and Displayed Title (Layer 2)

**Feature**: 015-advanced-visual-components | **Module**: `core/components/visual.py` | **Date**: 2026-10-13

Shared helpers for "rendered 0 versus blank" and for the title currently shown on a visual. `KPI` and
`Chart` both use them. No map class is added; a caller that already holds a map container uses the
same presence rule.

## Public Surface

```python
def scope_host(frame: FrameLocator, scope: str | None) -> FrameLocator | Locator: ...

def classify_presence(
    numbers: Sequence[int | float | None],
    mark_count: int,
) -> Literal["value", "empty"]: ...

def displayed_title_text(container: Locator) -> str: ...
```

`KPI._scope_host` MUST delegate to `scope_host` with the feature 014 behavior:

1. `None` or blank → `frame`.
2. Else the first `role="group"` whose accessible name matches `re.compile(re.escape(scope.strip()))`.
3. Else the first `role="group"` filtered with `has_text` of that pattern.
4. Never `locator("*").filter(has_text=...)`.

## `classify_presence`

- MUST return `"value"` when any entry in `numbers` is not `None`, including `0`.
- MUST return `"value"` when `mark_count > 0`, even if every number is `None`.
- MUST return `"empty"` only when every number is `None` and `mark_count == 0`.
- MUST NOT return a numeric zero for the empty case.
- Title characters and axis chrome MUST NOT be passed in as marks. The caller counts plot marks
  (bars, columns, points) only.

A chart cell that failed to align is `None` inside `numbers`. That `None` MUST NOT be rewritten to
`0` before the call. If another cell has a number, or any mark exists, the visual state is still
`"value"` while the missing cell stays `None`.

## `displayed_title_text(container) -> str`

MUST return the first non-empty string among:

1. The visual's heading text.
2. The visual-title node's text.
3. The container's accessible name (`aria-label`, then the accessible name Playwright exposes).

MUST strip bidi marks. MUST NOT remove the lookup anchor from the string. MUST return `""` when all
three sources are empty. MUST NOT consult a catalog of slicer phrases.

Lookup of the container (on `Chart.displayed_title` and on any KPI wrapper) MUST use `scope_host` and
an escaped substring anchor. A longer accessible name that still contains the anchor MUST match, and
the returned text MUST be the full current title.

## Examples (normative)

| `numbers` | `mark_count` | Result |
|-----------|--------------|--------|
| `[0]` | `0` | `"value"` |
| `[0]` | `2` | `"value"` |
| `[None]` | `0` | `"empty"` |
| `[]` | `0` | `"empty"` |
| `[None, None]` | `3` | `"value"` |
| `[4, None]` | `2` | `"value"` (the `None` cell stays absent) |

A displayed title `"Weekly total — last seven days"` located by anchor `"Weekly total"` MUST be
returned in full. The suffix is not stored in `core/`.

## Invariants

- Empty is a state, not the number 0.
- A minimum or a reading of 0 stays a number on the scale/chart model; this helper only classifies.
- Dynamic title text never becomes a literal under `core/`.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| `0` versus no numbers and no marks | `tests/unit/test_visual_state.py` |
| `None` cell is not coerced to `0` | `tests/unit/test_visual_state.py` and `tests/unit/test_chart_shape.py` |
| Scope host still matches feature 014 | delegation review; fleet smoke for the default `scope=None` path |
