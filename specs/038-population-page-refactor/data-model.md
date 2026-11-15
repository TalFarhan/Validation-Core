# Data Model: Population Page Internal Refactor

No new stored entity and no YAML change. The refactor preserves the maps and totals the current tests already read.

## Public results that must stay

| Method | Result | Notes |
|--------|--------|-------|
| `read_card(role)` | `int \| float` | `role` is `total`, `warned`, or `unprotected`. `0` is a value. |
| `chart_total(title, series_index=0)` | `int \| float` | Dates: visible scrolled sum. Hour: SVG mark sum. District: settled visible sum. Settlement: `_rows_for_total`. Empty numeric set still raises `AssertionError`. |
| `read_chart_categories(title)` | `(categories, series)` | Parsed from the page-scoped visual container, including a reading `Chart.read` would return as empty. |
| `read_district_labels()` | `dict[str, int]` | Rows, then mark labels, then tooltip. Empty stays `{}`. |
| `read_date_counts()` | `dict[str, int]` | Date header to alerts. Table is closed before return. |
| `read_hour_buckets()` | `dict[str, int]` | `HH:MM` to sum. Average and fractional labels stay out. Tooltip only if earlier reads are empty. |
| `read_hour_daily_avg()` | `dict[str, int]` | `HH:MM` to a whole average. Unpairable result stays `{}`. |
| `read_settlement_warned()` | `dict[str, int]` | Unchanged reader. It is not part of the scroll or hover merge. |
| `set_hierarchy_level(level)` | `bool` | `false` when נפה, רשות, or יישוב is not visible. No other control is clicked. |
| `set_district_aggregation(mode)` | `None` | `sum` clicks `סכום`. `average` clicks `ממוצע ליום`. Scoped click only when the count is 1. |

Class constants `PAGE_TITLE`, `DISTRICT_CHART`, `DATES_CHART`, `HOUR_CHART`, `SETTLEMENT_CHART`, `WARNED_SERIES`, `UNWARNED_SERIES`, and the card titles stay.

## Scrolled row map

Built only from rows that pass `is_visible()`.

| Field | Alerts total (`key="stable"`) | Date counts (`key="header"`) |
|-------|-------------------------------|------------------------------|
| Key | `aria-rowindex` if set, else the row-header text | Row-header text only |
| Value | Integer in the `התרעות` `gridcell`, including `0` | Same integer |
| Omitted | Header row, `סה"כ`, non-`gridcell`, hidden row, duplicate key | Same, plus a row with no header text |
| Stop | Timeout, or two passes with no new key and no scroll movement | Same |
| Caller result | `(sum of values, number of keys)` | The map itself |

The deleted `_sum_scrolled_alert_column` map (hidden rows, scroll-to-end, first-row-key stop) is not a state of this entity.

## Visible row payload

One script returns:

| Field | Meaning |
|-------|---------|
| `null` | The row contains a column header. |
| `rowIndex` | `aria-rowindex`, or an empty string. |
| `cells[].role` | `rowheader`, `gridcell`, or `cell`. |
| `cells[].text` | Trimmed text content, before `_plain_cell`. |

`_plain_cell` then strips and collapses a doubled label when the stripped length is at least 2 and the halves match. That normalized text is the header key and the integer source.

## Hover map

| Source | Key | Value | When it runs |
|--------|-----|-------|----------------|
| District tooltip | First non-numeric, non-`ממוצע` line | First integer line | `read_district_labels` rows and marks are both empty |
| Hour tooltip | `HH:MM` from `_hour_bucket` | Alert integer | `read_hour_buckets` aria, categories, and mark labels are all empty |

Hidden marks are skipped. At most 40 marks are hovered. The overlay is dismissed after the walk.

## Chart categories

`parse_container` returns the pair `_parse` already returns for that container and title:

| Field | Meaning |
|-------|---------|
| `categories` | `ChartCategory` rows. A missing cell stays `None`, not `0`. |
| `series` | Legend names, opaque to `Chart`. |

`Chart.read` still returns a `ChartReading` and still clears categories when the reading state is empty. Callers of `read` are unchanged. `read_chart_categories` uses `parse_container` so it does not take that wipe.

## State transitions

```text
dates total / date counts
  open table → scroll top → collect visible → page down
  → stop when two quiet passes or timeout → close with חזרה לדוח

district labels
  visible rows (scroll the visual) → mark labels → hover only if both are empty

hour sum
  aria labels → categories → mark labels → hover only if all are empty

hierarchy click
  control missing → false
  control clicked → selected attribute when present, else district title visible → true / false
```

No new persisted state. `_page_switch_attempts` and the slicer settle behavior stay.
