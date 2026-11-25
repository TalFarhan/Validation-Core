# Phase 1 Data Model: Authorities Status Screen 1 YAML Sanity

This slice adds no database schema. The entities are the golden YAML document and the dict
`read_screen_1_metrics()` returns. The page returns display text and numbers as read. The test
applies the integer rule when the golden node is an `int`, the float rule when it is a
`float`, and the string rule otherwise.

`date` and `filters` are both inputs and checked results. The test applies `date`, then
`filters`, waits until Screen 1 is idle after every selection and once more before the read,
and only then reads the screen. `title` is stored in the YAML and is not a reader key.
`section_anchor_visible("title")` is false, so the walk skips it.

`dashboard.screen_2_service_targets` is a sibling block in the same file. This slice does not
load it.

## Golden record (`data/reshuyot/db_sanity.yaml`)

Root key: `dashboard`. Checked block: `screen_1_national_status`. The file is not edited.

```yaml
dashboard:
  screen_1_national_status:
    title: ""                 # stored; anchor is absent; walk skips it
    date: ""                  # selected date label; applied first when present
    filters:                  # applied in this order after date
      district: ""            # one selection
      sub_district: []        # one selection per item, in order
    survey_status:
      filled: 0
      out_of: 0
    authorities_status:
      coping_well:
        count: 0
        authorities: []       # {name, score, trend?}
      may_struggle:
        count: 0
        authorities: []
      struggling:
        count: 0
        authorities: []
    facilities:
      operation_centers:
        unknown_in: 0
        open: {count: 0, authorities: []}
        closed: {count: 0, authorities: []}
      protection_facilities:
        partially_open_count: 0
        open: {count: 0, authorities: []}
        closed: {count: 0, authorities: []}
      call_centers_106:
        open: {count: 0, authorities: []}
        closed: {count: 0, authorities: []}
    missing_daily_report:
      count: 0
      authorities: []
```

The zeros and empty strings above are the schema, not a second snapshot. The checked-in file
holds the live golden values. This slice does not rewrite them.

### `date` and `filters`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `date` | string | selected date label | exact display text after bidi and outer whitespace are removed |
| `filters.district` | string | selected district label | exact display text |
| `filters.sub_district` | list of strings | selected sub-district labels | every golden name is present; extra UI labels are ignored |

**Validation**: `date` is applied only when the key is present and non-empty. The page clicks
that one label inside `_pick_open_date` by scrolling the open dropdown at most 20 steps. The
click does not go through `collect_virtualized_rows`. Each filter value is applied after the
date. A list is not passed to `Slicer` as one string. The second `sub_district` call does not
clear the first label. The read-back list contains both names.

### `survey_status`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `filled` | int | digit string in the survey block | integer rule |
| `out_of` | int | digit string in the same block | integer rule |

**Validation**: both counts are required when the anchor is visible. The page and the test do
not swap or "correct" them. The golden file is the source, including when `filled` is greater
than `out_of`.

**Read**: `filled` is the digit text of `svg[aria-label^='GOALS_COUNT_MUNI']` on the report
frame. `out_of` is the digit text of `svg[aria-label*='Muni_Code']` on the report frame. The
reader waits until that SVG is visible and a descendant `tspan` or `text` (or the SVG itself
when it has no such child) contains a digit, then returns `text_content`. The wait is
Playwright `expect` bounded by `self.timeout`. An empty string is a missed read. It is a
different value from `0`. The compare stays the integer rule: `''` fails against `18`, and
`"18"` passes.

### `authorities_status` bucket

Buckets, in YAML order: `coping_well`, `may_struggle`, `struggling`.

| Field | YAML type | Match |
|-------|-----------|--------|
| `count` | int | integer rule |
| `authorities` | list of objects | match on `name`; extra UI rows ignored |
| `authorities[].name` | string | exact display text; this is the row identity |
| `authorities[].score` | float | float rule |
| `authorities[].trend` | string, only on some rows | exact `up` or `down` when the golden row has the key |

**Validation**: a golden row without `trend` does not fail when the UI row also has a trend.
A golden row with `trend` fails when the UI omits it or shows a different word. An empty
golden `authorities` list does not fail because the UI has extra names. `count` is still
compared. A visible bucket whose whole read is empty while the golden bucket has data fails.

### `facilities`

| Facility | Extra field | `open` / `closed` |
|----------|-------------|-------------------|
| `operation_centers` | `unknown_in` (int) | `count` (int) and `authorities` (list of names) |
| `protection_facilities` | `partially_open_count` (int) | `count` (int) and `authorities` (list of names) |
| `call_centers_106` | none | `count` (int) and `authorities` (list of names) |

**Validation**: name lists match by membership. Extra UI names are ignored. A missing golden
name fails. `unknown_in` and `partially_open_count` are siblings of `open` and `closed`, not
fields inside them.

### `missing_daily_report`

| Field | YAML type | Match |
|-------|-----------|--------|
| `count` | int | integer rule |
| `authorities` | list of names | every golden name is present; extra UI names are ignored |

## Reader dict

`read_screen_1_metrics()` returns the same keys the walk can check:

- `date`: string
- `filters`: map with `district` (string) and `sub_district` (list of strings)
- `survey_status`: `{filled, out_of}`
- `authorities_status`: the three buckets
- `facilities`: the three facilities
- `missing_daily_report`: `{count, authorities}`

`title` is absent. Display text is what the screen shows. The page does not substitute a
golden literal when a node is blank.

## Compare rules

| Golden type | Rule |
|-------------|------|
| `int` | Parse the first integer in the display text after commas, spaces, and narrow spaces are removed. Grouped digits (`1,324`) and plain digits match. |
| `float` | Parse the display text as a float after grouping marks are removed. `93.0` matches `93` and `93.0`. `86.9` does not match `87`. |
| `str` | Exact match after bidi marks (`U+200E`, `U+200F`, `U+202A`–`U+202C`) and outer whitespace are removed. |
| list of strings | Every golden string is present. Extra UI strings are ignored. Order is not significant. |
| list of objects | Identity is `name`. Each golden field on that row is compared. Extra UI rows and extra UI fields are ignored. |
| mapping | Every golden key is present. A mapping that is empty while the golden mapping has data fails. Extra UI keys are ignored. |

## Anchor states

| Section | Anchor | Empty read while golden has data |
|---------|--------|-----------------------------------|
| `title` | not defined (always skipped) | not evaluated |
| `date` | date control visible | fail |
| `filters` | a Screen 1 filter control visible | fail |
| `survey_status` | survey block heading visible | fail |
| `authorities_status` | status block heading visible | fail |
| `facilities` | facilities block heading visible | fail |
| `missing_daily_report` | missing-report block heading visible | fail |

If the golden block is non-empty and every section above is skipped, the test calls
`pytest.skip`. One visible, checked section is enough to run the assertions.

## State transitions

Screen 1 has no workflow state. The only order is:

1. `navigate()` opens the report and the ready phrase is visible.
2. Optional `date` selection, then idle.
3. Each filter label, in YAML order, then idle after each label.
4. Idle once more.
5. One read.
6. Walk. The read does not select, clear, or open Screen 2.
