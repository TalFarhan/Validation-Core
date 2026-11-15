# Data Model: Centralize Show as a Table Extraction (Fleet MVP)

This slice does not add stored fields and does not edit `data/fleet/db_sanity_all.yaml`.
It defines the row the shared reader returns and the segment the fleet page builds
from that row.

## Visual table row

One data row from Show as a table. Produced by `VisualTable.read_rows`. The reader
does not interpret the headers.

| Field | Type | Rule |
|-------|------|------|
| Header | `str` | Column header text, bidi marks removed, trimmed. Header order is the dict order. |
| Cell | `str` | Cell text, same cleanup. Empty cells stay empty strings. |

A header row (cells equal to the header texts) is not a visual table row.
A row already stored under the same cell tuple is not stored again.

Validation: `read_rows` returns `list[dict[str, str]]`. It does not return integers.
`name` is only an opaque string for the error text.

## Chart segment

One fleet category and its count. Produced by `rows_to_label_values` from a visual
table row, then returned by `read_chart_segments`.

| Field | Type | Rule |
|-------|------|------|
| Label | `str` | First cell that is not a pure number and not only a percent. A trailing `N` or `N (P%)` is stripped from that cell. |
| Value | `int` | First pure integer cell, after removing thousands separators, spaces, and bidi marks. If none, the leading integer of an `N (P%)` cell on that row. `0` is kept. |

Validation:

- A row with any cell equal to a `skip_labels` entry, or starting with one, is omitted.
  Fleet passes `סה"כ`.
- A row with no label or no integer is omitted.
- The same label twice keeps the first value.
- Dict order is first-seen order.

The chart key selects the visual host. It is not a field on the segment.

| Chart key | Visual title (unchanged, on the page) | Golden block (unchanged) |
|-----------|----------------------------------------|---------------------------|
| `unit` | `פילוח רכבים בשימוש ביחידות` | `units_breakdown` |
| `source` | `פילוח מקור משיכת רכבים בשימוש` or `פילוח מקור משיכה רכבים בשימוש` | `pull_source_breakdown` |
| `category` | `פילוח קטגוריות רכב` | `vehicle_categories[].actual` |
| `withdrawal` | `פילוח סיבות לזיכוי רכב` | `credit_reasons_summary` |

An unknown chart key raises `ValueError` before any click.

## Canvas label list (unchanged)

`get_chart_segment_labels(chart_key) -> list[str]` stays the SVG `<title>` and
legend/axis harvest. Hierarchy methods and the 200ms poll read this list. It is not
a chart segment and it does not carry a count.

## State transitions

```text
canvas visual
    → right-click chart_section
    → menu item shown
    → grid or table visible
    → scroll and collect rows
    → back button clicked
    → canvas visual (back button hidden)
```

If the menu or the grid never appears, the state stays on the canvas (menu dismissed
by the failed attempt) and `read_rows` raises. If the grid was opened and the back
button never appears, `read_rows` still attempts to leave, then raises.

Hierarchy expand does not enter this transition. It stays on the canvas label list.
