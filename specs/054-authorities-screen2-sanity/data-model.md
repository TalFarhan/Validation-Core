# Phase 1 Data Model: Authorities Status Screen 2 YAML Sanity

This slice adds no database schema. The entities are the golden YAML document as loaded by
PyYAML and the dict `read_screen_2_metrics()` returns. The page returns display text and
numbers as read. The test applies the integer rule when the golden node is an `int`, the
float rule when it is a `float`, and the string rule otherwise.

`date` and `filters` are both inputs and checked results. The test opens Screen 2, applies
`date`, then `filters`, waits until Screen 2 is idle after every selection and once more
before the read, and only then reads the screen. `title` is stored in the YAML and is used
only as a navigation argument. `screen_2_section_visible("title")` is false, so the walk
skips it.

`dashboard.screen_1_national_status` is a sibling block in the same file. This slice does
not load it.

## Golden record (`data/reshuyot/db_sanity.yaml`)

Root key: `dashboard`. Checked block: `screen_2_service_targets`. The file is not edited.

PyYAML `safe_load` of the checked-in indent:

```yaml
dashboard:
  screen_2_service_targets:
    title: ""                      # stored; passed to open_screen_2; walk skips it
    date: ""                       # selected date label; applied first when present
    filters:                       # applied in this order after date
      district: ""                 # one selection (string)
      sub_district: ""             # one selection (string in this file)
    sector_profile:
      average_final_score: 0
      national_average_score: 0
      number_of_residents: 0
      resilience_score_percentage: 0
      defense_policy: ""
      total_alerts_last_24h: 0
    protection_data:
      mamad_mamak:
        count: 0
        population_percentage: 0.0
      shared_shelter:
        count: 0
        population_percentage: 0.0
      public_shelters_capacity:
        count: 0
        population_percentage: 0.0
      without_shelter:
        count: 0
        population_percentage: 0.0
    service_targets: []            # {name, score}; identity is name
    grade_trends: null             # as-loaded; anchor is absent; walk skips it
    data: []                       # {date, scores: {category: float}}; identity is date
```

The zeros and empty strings above are the schema, not a second snapshot. The checked-in file
holds the live golden values. This slice does not rewrite them. `grade_trends` is `null`
because `data` is not indented under it in the file.

### `date` and `filters`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `date` | string | selected date label | exact display text after bidi and outer whitespace are removed |
| `filters.district` | string | selected district label | exact display text |
| `filters.sub_district` | string (this file) | selected sub-district label | exact display text |

**Validation**: `date` is applied only when the key is present and non-empty. The page clicks
that one label inside `_pick_open_date` by scrolling the open dropdown at most 20 steps.
Each filter value is applied after the date. A list, if present, is not passed to `Slicer`
as one string. A later call does not clear the first label. Screen 2 read-back of these two
filters is a string, not Screen 1's `sub_district` list.

### `sector_profile`

| Field | YAML type | Match |
|-------|-----------|--------|
| `average_final_score` | int | integer rule |
| `national_average_score` | int | integer rule |
| `number_of_residents` | int | integer rule |
| `resilience_score_percentage` | int | integer rule |
| `defense_policy` | string | exact display text after bidi strip |
| `total_alerts_last_24h` | int | integer rule |

**Validation**: all six keys are required when the anchor is visible. An empty digit string
is a missed read. It is a different value from `0`. The page does not substitute a golden
integer.

### `protection_data` bucket

Buckets, in YAML order: `mamad_mamak`, `shared_shelter`, `public_shelters_capacity`,
`without_shelter`.

| Field | YAML type | Match |
|-------|-----------|--------|
| `count` | int | integer rule |
| `population_percentage` | float | float rule |

**Validation**: `6.0` matches `6` and `6.0`. Extra UI buckets are ignored. A missing golden
bucket key fails.

### `service_targets`

| Field | YAML type | Match |
|-------|-----------|--------|
| `[]` | list of objects | match on `name`; extra UI rows ignored |
| `[].name` | string | exact display text; this is the row identity |
| `[].score` | float | float rule |

**Validation**: a missing golden `name` fails when the anchor is visible. Extra UI rows do
not fail. `100.0` matches `100` and `100.0`.

### Trend rows (`data`)

As loaded, this is a sibling of `grade_trends`, not a child of it.

| Field | YAML type | Match |
|-------|-----------|--------|
| `[]` | list of objects | match on `date`; extra UI dates ignored |
| `[].date` | string | exact display text; this is the row identity |
| `[].scores` | mapping of string → float | every golden key; extra UI categories ignored |
| `[].scores.<category>` | float | float rule |

**Validation**: a missing golden `date` fails when the `data` anchor is visible. A missing
golden score key on a matched date fails. Extra UI dates and extra UI score keys are
ignored. `grade_trends` is not this list.

## Reader dict

`read_screen_2_metrics()` returns the same keys the walk can check:

- `date`: string
- `filters`: map with `district` (string) and `sub_district` (string)
- `sector_profile`: the six fields
- `protection_data`: the four buckets
- `service_targets`: list of `{name, score}`
- `grade_trends`: `None`
- `data`: list of `{date, scores}`

`title` is absent. Display text is what the screen shows. The page does not substitute a
golden literal when a node is blank.

## Compare rules

| Golden type | Rule |
|-------------|------|
| `int` | Parse the first integer in the display text after commas, spaces, and narrow spaces are removed. Grouped digits (`617,843`) and plain digits match. |
| `float` | Parse the display text as a float after grouping marks are removed. `100.0` matches `100` and `100.0`. `94.46` does not match `94.5`. |
| `str` | Exact match after bidi marks (`U+200E`, `U+200F`, `U+202A`–`U+202C`) and outer whitespace are removed. |
| `None` | Not evaluated: `grade_trends` has no Screen 2 anchor. |
| list of objects | Identity is `name` if that field exists on the golden row, else `date` if that field exists, else `title`. Each golden field on that row is compared. Extra UI rows and extra UI fields are ignored. |
| mapping | Every golden key is present. A mapping that is empty while the golden mapping has data fails. Extra UI keys are ignored. |

## Anchor states

| Section | Anchor | Empty read while golden has data |
|---------|--------|-----------------------------------|
| `title` | not defined (always skipped) | not evaluated |
| `date` | Screen 2 date control visible | fail |
| `filters` | a Screen 2 filter control visible | fail |
| `sector_profile` | sector-profile heading visible | fail |
| `protection_data` | protection-data heading visible | fail |
| `service_targets` | service-targets heading or grid visible | fail |
| `grade_trends` | not defined (null node; always skipped) | not evaluated |
| `data` | trends visual visible | fail |

If the golden block is non-empty and every section above is skipped, the test calls
`pytest.skip`. One visible, checked section is enough to run the assertions.

## State transitions

Screen 2 has no workflow state. The only order is:

1. `navigate()` opens the report and the Screen 1 ready phrase is visible.
2. `open_screen_2(title)` clicks the page-navigation target and Screen 2 idle holds.
3. Optional `date` selection, then Screen 2 idle.
4. Each filter label, in YAML order, then Screen 2 idle after each label.
5. Screen 2 idle once more.
6. One read.
7. Walk. The read does not select, clear, or return to asserting Screen 1 metrics.
