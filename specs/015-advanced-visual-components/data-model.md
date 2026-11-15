# Data Model: Advanced Power BI Visual Components

**Feature**: 015-advanced-visual-components | **Date**: 2026-10-13

Runtime structures returned by Layer 2. They carry numbers and opaque strings. They do not carry
report identity, SQL, or expected Top-N.

## GaugeScale

Parsed scale of one titled KPI or Gauge.

| Field | Type | Meaning |
|-------|------|---------|
| `state` | `"value"` \| `"empty"` | `"value"` if a number was parsed or a data mark is present. `"empty"` if neither is present. |
| `value` | `int` \| `float` \| `None` | Current figure or slash numerator. `0` is a real reading. `None` if no figure was parsed. |
| `minimum` | `int` \| `float` \| `None` | Lower bound when the label states one. `None` when absent (including slash pairs). `0` is a real bound. |
| `maximum` | `int` \| `float` \| `None` | Upper bound, or the slash denominator. `None` when the label has no upper figure. |

**Relationships**: Built from the raw accessible text of the card `KPI` already resolves (`title`,
optional `scope`). Not built from the string `extract_kpi_value_text` returns, because that string
has already dropped min/max.

**Validation**:

- Labeled chrome is applied before the compact and slash rules.
- Compact form is exactly three compact tokens and zero bound-chrome pairs.
- Slash form is exactly one pair and no additional number.
- `state == "empty"` implies `value`, `minimum`, and `maximum` are all `None`.
- `state == "value"` may still have `value is None` when marks exist but no number was readable.
- A parsed `value == 0` implies `state == "value"`.

## VisualPresence

The empty-versus-zero decision shared by KPI and Chart. Not a stored record; the result of
`classify_presence`.

| Input | Type | Meaning |
|-------|------|---------|
| `numbers` | sequence of `int` \| `float` \| `None` | Parsed readings. `None` entries are ignored for the zero check. A present `0` forces `"value"`. |
| `mark_count` | `int` | Data marks inside the visual (bars, columns, points). Title text and axis chrome are not marks. |

| Output | When |
|--------|------|
| `"value"` | Any non-null number, or `mark_count > 0` |
| `"empty"` | Every number is null and `mark_count == 0` |

**Validation**: The classifier never returns `0` for the empty case. It returns a state. Callers that
need a number read `GaugeScale.value` or a chart cell, and treat `None` as absent.

## ChartCategory

One row of a bar or column visual, in axis order.

| Field | Type | Meaning |
|-------|------|---------|
| `label` | `str` | Opaque category text. `core/` does not interpret it. |
| `values` | sequence of `int` \| `float` \| `None` | One cell per legend series, legend order. `None` is a missing mark, not `0`. |

## ChartReading

Full read of one bar/column visual.

| Field | Type | Meaning |
|-------|------|---------|
| `title` | `str` | Displayed title after bidi stripping. May be longer than the lookup anchor. |
| `categories` | sequence of `ChartCategory` | Axis order. |
| `series` | sequence of `str` | Opaque legend names, legend order. Empty when the visual has a single unnamed measure. |
| `state` | `"value"` \| `"empty"` | From `classify_presence` over all cell values and the plot's mark count. |

**Validation**:

- `len(category.values) == len(series)` when `series` is non-empty. A single unnamed measure uses one
  cell per category and an empty `series` tuple.
- `category_count` is the number of categories.
- Descending order reads one `series_index` (default `0`) down the categories. Each pair must satisfy
  `previous >= current`. Ties pass. Any `None` in that column fails the check. Zero categories fail.
  One category passes.
- `state == "empty"` implies there are no categories and no data marks. A title may still be non-empty.

## VisualTitle

Not a separate stored entity. The string `displayed_title_text` returns for the container found by
`anchor` + optional `scope`.

| Rule | Detail |
|------|--------|
| Lookup | Escaped substring of the accessible name, inside `scope_host`. |
| Sources, first non-empty | Heading text, visual-title node, container accessible name. |
| Cleanup | Strip bidi marks. Do not strip the caller's anchor out of the result. |
| Leakage | The dynamic suffix is part of the returned string only. It is not a constant in `core/`. |

## Scope host (shared)

Unchanged from feature 014. `KPI._scope_host` delegates to `visual.scope_host`.

| `scope` | Host |
|---------|------|
| `None`, `""`, or whitespace | Report iframe |
| Non-empty | `role="group"` whose accessible name matches, else a `role="group"` that contains the text |

The host is never `locator("*").filter(has_text=scope)`.

## State transitions

These readers are stateless snapshots. There is no stored workflow. A second read after a slicer
change may show a different `VisualTitle`, a different `ChartReading.categories` length, or a
different `GaugeScale`. The caller supplies the settle; Layer 2 does not wait on a report-specific
KPI.

```text
located visual
    ├─ raw label has a number (including 0)  → state "value"
    ├─ no number, mark_count > 0             → state "value", figure None
    └─ no number, mark_count == 0            → state "empty", figures None
```
