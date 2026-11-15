# Contract: Generic KPI Component (Layer 2)

**Feature**: 012-kpi-group-visuals | **Module**: `core/components/kpi.py` | **Date**: 2026-10-11

This is the UI contract the generic `KPI` component exposes to its callers (domain pages, tests, and the
DB-parity engine). It documents the **public surface** and the **behavioral guarantees** after adding group
visual support. The component is report-agnostic: titles are opaque caller inputs.

## Public Surface (unchanged signatures)

```python
class KPI:
    def __init__(self, page: Page, frame: FrameLocator, timeout_ms: int | None = None) -> None: ...
    def card(self, title: str) -> Locator: ...
    def read_text(self, title: str) -> str: ...
    def value(self, title: str) -> str: ...
    def number(self, title: str) -> int | float: ...

# module-level
def normalize_kpi_text(raw: str) -> str: ...
def extract_kpi_value_text(raw: str) -> str: ...   # NEW
```

The four `KPI` methods keep their signatures and return types. Existing callers (notably
`tests/helpers/db_parity_engine.py`, which calls `KPI.number(name)`) require **no changes**.

## Behavioral Contract

### `card(title) -> Locator`
- MUST return a `role="button"` locator whose accessible name matches `title` when such a button exists.
- MUST otherwise return a `role="group"` locator whose accessible name matches `title`.
- Matching uses a case-sensitive `re.escape(title)` regex and returns the first match (`.first`).

### `read_text(title) -> str`
- For a **button** visual: MUST return the raw text of the card's last `<p>` (unchanged from prior behavior).
- For a **group** visual: MUST return the numeric value text extracted from the inner `img`'s `aria-label`
  (preferred), then its `title` attribute, then the group's own text — with the numeric token isolated via
  `extract_kpi_value_text`.
- MUST wait for the resolved visual to be visible (up to the configured timeout) before reading.

### `value(title) -> str`
- MUST return `normalize_kpi_text(read_text(title))` — bidi marks, commas, and whitespace/nbsp removed.

### `number(title) -> int | float`
- MUST return an `int` when the value is integral, else a `float`.
- MUST raise `ValueError` when the resolved text contains no parseable number.

### `extract_kpi_value_text(raw) -> str` (NEW, pure)
- MUST strip Power BI bidi marks, then return the longest numeric run (allowing internal `, . \u00a0 \u202f`
  and spaces) found in the string.
- MUST return the cleaned text unchanged when the string contains no digits.
- MUST be idempotent for an already-clean numeric string (e.g. `"1,234"` → `"1,234"`).

## Invariants (what callers can rely on)

- **No domain leakage**: the component references only generic ARIA roles/attributes; it never embeds
  report-specific titles, SQL, or CSS.
- **Button path stability**: for button-rendered visuals the resolved locator and read text are identical to
  the pre-feature behavior → the fleet smoke contract is preserved.
- **Uniform numeric API**: `number(title)` returns the metric regardless of whether it rendered as a button
  or a group.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| `extract_kpi_value_text` isolates the number from mixed/group labels | `tests/unit/test_kpi_normalize.py::test_extract_pulls_numeric_token_from_group_label` |
| extract → normalize yields a parseable value | `tests/unit/test_kpi_normalize.py::test_extract_then_normalize_is_parseable` |
| `normalize_kpi_text` behavior unchanged | `tests/unit/test_kpi_normalize.py::test_normalize_strips_marks_commas_and_whitespace` |
| Button path / fleet contract unaffected | `pytest tests/ui/fleet_dashboard/` (Constitution III regression gate) |
