# Contract: Generic Chart Component (Layer 2)

**Feature**: 015-advanced-visual-components | **Module**: `core/components/chart.py` | **Date**: 2026-10-13

Bar and column reader. Category labels and legend names are opaque. This contract does not cover
tooltips, drilldown, or hover; those stay on the domain page that already owns them.

## Public Surface

```python
@dataclass(frozen=True)
class ChartCategory:
    label: str
    values: tuple[int | float | None, ...]

@dataclass(frozen=True)
class ChartReading:
    title: str
    categories: tuple[ChartCategory, ...]
    series: tuple[str, ...]
    state: Literal["value", "empty"]

class Chart:
    def __init__(self, page: Page, frame: FrameLocator, timeout_ms: int | None = None) -> None: ...
    def read(self, title: str, scope: str | None = None) -> ChartReading: ...
    def category_count(self, title: str, scope: str | None = None) -> int: ...
    def is_descending(
        self, title: str, scope: str | None = None, series_index: int = 0
    ) -> bool: ...
    def displayed_title(self, title: str, scope: str | None = None) -> str: ...
```

Pure helpers (unit-tested without a browser) MUST implement the order, count, and alignment rules
below so the DOM locator is not the only specification.

## Locate

- `title` and `scope` MUST be opaque. `scope` MUST follow `scope_host` (feature 014).
- The visual container MUST be the Power BI host that contains that title (group and/or generic
  visual-container chrome). It MUST NOT be chosen by a report-specific CSS id.
- `displayed_title` MUST return `displayed_title_text` of that container (see `visual-reading.md`).
  `read().title` MUST be that same string.

## Parse

Inside the container, in order:

1. Prefer each data mark's accessible name when it carries a category, an optional series name, and
   a number.
2. Otherwise pair category tick texts with numeric data labels in visual order.
3. `series` MUST be legend texts in legend order, excluding the visual title and the category labels.
   When there is no legend, `series` MUST be empty and each category MUST have a single cell.

Alignment:

- Cells follow `series` order.
- A category with no mark for a series MUST store `None` in that cell, not `0`.
- `len(category.values)` MUST equal `len(series)` when `series` is non-empty.

`state` MUST be `classify_presence` over every cell and the plot mark count. A visual whose title is
visible but which has no categories and no data marks MUST be `"empty"`.

## `category_count`

MUST equal `len(reading.categories)`. MUST NOT equal the number of bars when a category has more than
one series. An empty visual MUST return `0`. Top-N is not a parameter; the caller compares the count.

## `is_descending`

MUST read `categories[i].values[series_index]` from top to bottom.

- MUST pass when every pair satisfies `previous >= current` (ties pass).
- MUST fail when a later value is greater.
- MUST fail when any selected cell is `None`, when `series_index` is out of range, or when there are
  zero categories.
- MUST pass when there is exactly one category and that cell is a number (including `0`).
- MUST compare numbers only. MUST NOT sort or compare category labels.

`series_index` MUST be an integer. `core/` MUST NOT accept a series display name as a sort key; the
caller maps a returned name to an index.

## Examples (normative)

Synthetic categories `A`, `B` and series `left`, `right`. These words are not product copy.

| Categories (values) | `series_index` | `category_count` | `is_descending` |
|---------------------|----------------|------------------|-----------------|
| `A=(5, 1)`, `B=(5, 4)`, `C=(2, 0)` | `0` | `3` | `True` (ties on 5) |
| `A=(5,)`, `B=(9,)` | `0` | `2` | `False` |
| `A=(0,)` | `0` | `1` | `True` |
| `A=(4, None)`, `B=(1, 2)` | `1` | `2` | `False` (`None` in the column) |
| no categories, no marks | `0` | `0` | `False`, `state="empty"` |

Two series MUST yield two cells per category and `series == ("left", "right")` in legend order.

## Invariants

- No report titles, metric names, Top-N literals, or denominator literals in `core/`.
- Fleet tooltip, drilldown, and hover code is not part of this type.
- A rendered `0` is a cell value. A missing bar is `None`. A blank plot is `state="empty"`.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Descending ties, inversion, single row, `None` cell | `tests/unit/test_chart_shape.py` |
| Count is categories, not bars | `tests/unit/test_chart_shape.py` |
| Two series align in legend order | `tests/unit/test_chart_shape.py` |
| Fleet chart behavior unchanged | `pytest tests/ui/fleet_dashboard/` (page object not modified) |
