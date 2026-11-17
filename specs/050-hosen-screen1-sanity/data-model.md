# Phase 1 Data Model: Hosen Status Screen 1 YAML Sanity

This slice adds no database schema. The entities are the golden YAML document and the dict
`read_screen_1_metrics()` returns. The page returns display text. The test applies the integer
rule when the golden node is an `int`.

`date` and `filters` are both inputs and checked results. The test applies `date`, then
`filters`, waits until Screen 1 is idle, and only then reads the other blocks. The reader
returns the selected date and the same filter map so `_assert_tree` can confirm each control
kept its golden label.

## Golden record (`data/hosen/db_sanity.yaml`)

Root key: `hosen_dashboard`. One screen block: `screen_1_landing`.

```yaml
hosen_dashboard:
  screen_1_landing:
    date: ""                # selected date combobox label; value lives in the YAML
    survey_status:
      submitted: 0          # int, live count
      total: 0              # int, live count
      missing_authorities: []
    kpis:
      national_average:
        title: ""           # live card title
        percentage: ""      # display string, includes %
        trend: up           # up | down | flat
      categories: []        # list of {title, score, trend_direction}
    resilience_scores: []   # list of {authority, score, status}
    filters: {}             # english id → Hebrew label to select, then to read back
```

The zeros and empty strings above are the schema, not a second snapshot. The checked-in
`data/hosen/db_sanity.yaml` is the golden file. This date amendment does not rewrite it.

### `survey_status`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `submitted` | int | digit string from the top-left block | integer rule |
| `total` | int | digit string from the same block | integer rule |
| `missing_authorities` | list of strings | authority names under that block | exact string; extra UI names ignored |

**Validation**: both counts are required when the block is visible. A golden name missing from
the UI fails. An empty UI list fails when the golden list is non-empty and the anchor is visible.

### `kpis.national_average`

| Field | YAML type | Match |
|-------|-----------|--------|
| `title` | string | exact, after bidi and outer whitespace are removed |
| `percentage` | string | exact display text, including `%`, from `.value tspan` `textContent` |
| `trend` | string | `up`, `down`, or `flat` |

### `kpis.categories` item

| Field | YAML type | Match |
|-------|-----------|--------|
| `title` | string | exact; this is the row identity |
| `score` | string | exact display text, including `%`, from the same `.value tspan` read |
| `trend_direction` | string | `up`, `down`, or `flat` |

**Validation**: categories match on `title`. Extra category cards are ignored. A missing golden
title fails. `percentage` and `score` are never floats and never bare integers in the YAML.
The page reads both strings with `text_content()` on `.value tspan`. `innerText` is not the
source. A visible card with an empty SVG string fails the golden percent (`ui=''`).

`trend` and `trend_direction` use the same classification, decided on the page from the card's non-canvas arrow:

| Signal | Stored word |
|--------|-------------|
| Up glyph, or green when no glyph direction is available | `up` |
| Down glyph, or red when no glyph direction is available | `down` |
| Flat glyph, or yellow when no glyph direction is available | `flat` |
| Canvas only, or no arrow node | `""` (golden word then fails) |

### `resilience_scores` row

| Field | YAML type | Match |
|-------|-----------|--------|
| `authority` | string | exact; this is the row identity. First line of the cell only |
| `score` | int when the cell is a whole number; otherwise string | integer rule, or exact string |
| `status` | string | `green` or `yellow` |

**Validation**: rows match on `authority`. Extra UI authorities are ignored. A golden authority
that the collector never sees fails. `status` is only the word `green` or `yellow` in the YAML.
A background that is neither color is returned as `rgb(...)` and fails that golden word.

`authority` is `_plain` of the first line of the authority cell's `inner_text()`. A second
line such as `עיצוב מותנה נוסף` is Power BI accessibility text and is not stored. The golden
value stays `קרית מלאכי`. The score cell is still the full `_plain` text. The test's
`_assert_rows` indexes the published `authority` and does not split lines itself.

Color transitions, from computed background of the row or the score cell:

| Paint | Stored word |
|-------|-------------|
| Green channel dominates | `green` |
| Red and green both high, blue low | `yellow` |
| Any other computed color | raw `rgb(...)` |

### `date`

String sibling of `filters` on `screen_1_landing`. The test reads it from the YAML and passes
it to `select_screen_1_filter("date", value)` before the `filters` loop. The reader returns
the same string: the selected date-combobox label, with the role name and bidi marks removed.

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `date` | string | selected label on the date combobox | exact, after bidi and outer whitespace are removed |

**Validation**: the page does not embed the golden date. `section_anchor_visible("date")` is
true when that combobox is visible, so `_assert_tree` checks the key. A combobox whose text
does not contain the value passed to `select_screen_1_filter` raises before the metric read.
The YAML file is not edited to satisfy this check.

### `filters`

Flat map of English id → label. The test selects each value before the metric read. The reader
returns the same ids with the label then showing on the combobox.

| Id | Meaning | Live golden label |
|----|---------|-------------------|
| `district` | Right-hand district slicer | `מחוז דרום` |
| `subdistrict` | Right-hand sub-district slicer | `נפת לכיש` |

Further ids are added by a YAML pair plus a row in the page filter-role table. The id is the
`SlicerDefinition.id` and the YAML key. The Hebrew accessible name is `role_name` on the page,
not a YAML key. Values are exact option labels.

**Validation**: YAML order is the apply order. `district` is listed before `subdistrict`. A
missing or empty map applies nothing. An id with no page role row fails before the metric read.
After the idle wait, every golden id is present in the UI map and its label matches. Extra
slicer ids on screen do not fail the test.

**Apply click**: `subdistrict` (`בחירת נפה`) is a custom-card search input. The page focuses
it with `search_input.click(force=True)` so `ul.TokensContainer` does not intercept the pointer.
The chosen `li` is clicked with `force=True`. `district` and `subdistrict` stay on that path.
The date combobox is the `date` section above: `Slicer.select` only when the open listbox is
named `SlicerDate`.

## Runtime dict

`read_screen_1_metrics() -> dict` uses `survey_status`, `kpis`, `resilience_scores`,
`filters`, and `date`. It is called only after the date and `filters` have been applied and
the screen is idle. `date` is the selected combobox label, not a hardcoded literal.

- Counts, scores, and percentages are strings (`"12"`, `"1,324"`, `"55%"`).
- `trend` and `status` are the words in the tables above, or `""` / `rgb(...)` when the signal
  is not one of those words.
- `missing_authorities`, `categories`, and `resilience_scores` are lists. An unreadable visible
  section returns an empty list or an empty string so the test can fail it.
- Filter values are the selected label only, with the slicer title removed.

## State

Screen 1 has one setup transition for this test: default slicers → golden `date` → golden
`filters` → idle → read. The reader does not change slicers or tabs. `collect_virtualized_rows` still scrolls the
resilience grid only, and it starts at the top of that grid after the idle wait.

| Step | Slicers | Metrics |
|------|---------|---------|
| After `navigate()` | Report default | Not read |
| `select_screen_1_filter("date", value)` | Date combobox text contains `value` | Not read; a miss raises |
| Each `filters` `select_screen_1_filter` | That id shows its YAML label | Not read |
| `wait_for_screen_1_idle` | Unchanged | Spinner hidden, ready locator visible |
| `read_screen_1_metrics` | Unchanged | `survey_status`, `kpis`, `resilience_scores`, `filters`, `date` |

## Relationships

- `date` is applied before `filters`. The survey, KPI, and resilience blocks describe that
  date plus the district and subdistrict slice. The reader returns `date` so `_assert_tree`
  can confirm the combobox kept the golden label.
- `filters` is the district and subdistrict slice. The test applies it after `date`, then
  asserts those smart-filter labels.
- `survey_status.missing_authorities` names authorities. `resilience_scores.authority` names
  authorities in the score table. The two lists are not required to be equal.
- `kpis.national_average.title` is the anchor title for the assessment visual. Category cards
  are the other cards in that visual.
