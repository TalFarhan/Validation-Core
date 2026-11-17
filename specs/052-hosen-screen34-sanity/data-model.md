# Phase 1 Data Model: Hosen Status Screens 3 and 4 YAML Sanity

This slice adds no database schema and does not edit `data/hosen/db_sanity.yaml`. The entities
are the existing golden blocks and the dicts `read_screen_3_metrics()` and
`read_screen_4_metrics()` return. The page returns display text. The test applies the empty-cell
rule when the golden node is `null`.

Screen 3 `date_range` and `filters`, and Screen 4 `date` and `filters`, are both inputs and
checked results. Each test opens its screen, applies the date values, then the non-null filter
entries in YAML order, waits until that screen is idle, and only then reads.

## Golden record (`data/hosen/db_sanity.yaml`)

Root key: `hosen_dashboard`. This slice reads `screen_3_geographic_investigation` and
`screen_4_excel_export`. It does not rewrite `screen_1_landing` or `screen_2_investigation`.

```yaml
hosen_dashboard:
  screen_3_geographic_investigation:
    title: ""                      # geographic screen title
    date_range:
      start: ""                    # first date control
      end: ""                      # second date control
    filters: {}                    # english id → Hebrew label or null
    graphs:
      final_resilience_score:
        title: ""
        legend: ""                 # series label inside that chart
        data: []                   # date + score
      categories: []               # title + data rows of date + score
  screen_4_excel_export:
    title: ""                      # export screen title
    date: ""                       # selected date combobox label
    filters: {}                    # english id → Hebrew label or null
    data_table: []                 # authority rows; percents stay display text
```

The empty strings above are the schema. The checked-in file is the golden snapshot. This plan
does not copy those dates, percents, or `null`s into Python.

### Screen 3 `title`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `title` | string | visible geographic heading | exact after bidi trim; `"` and `״` are the same character |

### Screen 3 `date_range`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `start` | string | first date control's selected label | exact after bidi trim |
| `end` | string | second date control's selected label | exact after bidi trim |

Apply order is `start`, then `end`. The page does not embed the golden dates.

### Screen 3 `filters`

| Field | YAML type | Applied | UI reading | Match |
|-------|-----------|---------|------------|--------|
| `level_selected` | string | yes, through `_select_smart_filter` | that control's chip | exact after bidi trim |
| `district` | string | yes | that control's chip | exact after bidi trim |
| `subdistrict` | string | yes | that control's chip | exact after bidi trim |
| `authority` | `null` | no | empty chip | `""` |

Apply order is YAML order. Extra slicers in the UI reading are ignored. A listed id with a
different label fails. `level_selected` is a different control from `district`.

### Final resilience chart (`graphs.final_resilience_score`)

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `title` | string | visible chart title | exact after bidi trim; quotes fold |
| `legend` | string | legend text inside that chart host, read before show-as-table | exact after bidi trim |
| `data[].date` | string | `DD/MM/YYYY` cell | row identity |
| `data[].score` | string | percent cell | exact display text |

Extra dates in `data` are ignored. A missing golden `date` fails. The legend is not the
district chip outside the chart host.

### Category chart (`graphs.categories[]`)

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `title` | string | visible chart title | chart identity |
| `data[].date` | string | `DD/MM/YYYY` cell | row identity |
| `data[].score` | string | percent cell | exact display text |

The golden list has eight titles. Extra charts on screen are ignored. A missing golden title
fails when the categories anchor is visible. There is no `legend` field on a category chart.
The page does not invent one.

### Screen 4 `title` and `date`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `title` | string | visible export heading | exact after bidi trim; quotes fold |
| `date` | string | selected date combobox label | exact after bidi trim |

### Screen 4 `filters`

| Field | YAML type | Applied | UI reading | Match |
|-------|-----------|---------|------------|--------|
| `sector` | `null` | no | empty chip | `""` |
| `district` | string | yes | that control's chip | exact after bidi trim |
| `subdistrict` | string | yes | that control's chip | exact after bidi trim |
| `authority` | `null` | no | empty chip | `""` |

Apply order is YAML order after `date`. Extra slicers are ignored.

### Export row (`data_table[]`)

| Field | YAML type | Match |
|-------|-----------|--------|
| `authority` | string | row identity; first line of the cell; `"` and `״` are the same character |
| `care_for_welfare` | string | exact percent display text |
| `effective_behavior` | string | exact percent display text |
| `information_and_communication` | string | exact percent display text |
| `community_resources` | string | exact percent display text |
| `leadership` | string | exact percent display text |
| `narrative` | string | exact percent display text |
| `final_score` | string | exact percent display text |
| `functional_continuity` | string | exact percent display text |
| `belonging_and_solidarity` | string | exact percent display text |

There is no file-name field and no workbook bytes. A trailing decimal is part of the text:
`75.0%` does not match `75%`. Extra authority rows are ignored. A missing golden `authority`
fails. A YAML `null` is not in this table in the checked-in file. If one appears later, it
matches `""` and does not match `0%`.

## State transitions

```text
Screen 1 (navigate)
  → open_geographic_screen(title) → Screen 3 idle
  → select_screen_3_date_range(start, end) → Screen 3 idle
  → select_screen_3_filter for each non-null id → Screen 3 idle
  → wait_for_screen_3_idle → read_screen_3_metrics

Screen 1 (navigate)
  → open_excel_export_screen(title) → Screen 4 idle
  → select_screen_4_filter("date", value) → Screen 4 idle
  → select_screen_4_filter for each non-null id → Screen 4 idle
  → wait_for_screen_4_idle → read_screen_4_metrics
```

Each new test starts from `navigate()` on Screen 1. One test does not open the other screen.
Opening Screen 3 or Screen 4 does not change the Screen 1 ready locator.

## Relationships

- One geographic record has one date range, one filter map, one final-score chart, and many
  category charts.
- One final-score chart has one legend and many date rows.
- One category chart has one title and many date rows.
- One export record has one date, one filter map, and many authority rows.
- Chart collection and export collection both go through `collect_virtualized_rows`. Chart
  collection gets there through `VisualTable.read_rows`. The export grid does not.

## Validation rules

- The page publishes display text. The test owns the `null` → `""` comparison.
- Percent strings are not parsed.
- Subset match: extra UI rows, extra dates, and extra charts do not fail.
- A visible anchor plus an empty collection fails when the golden node has data.
- A missing anchor skips that block only.
- If every block on that screen is skipped, the test calls `pytest.skip`.
