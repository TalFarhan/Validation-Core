# Phase 1 Data Model: Hosen Status Screen 1 YAML Sanity

This slice adds no database schema. The entities are the golden YAML document and the dict
`read_screen_1_metrics()` returns. The page returns display text. The test applies the integer
rule when the golden node is an `int`.

## Golden record (`data/hosen/db_sanity.yaml`)

Root key: `hosen_dashboard`. One screen block: `screen_1_landing`.

```yaml
hosen_dashboard:
  screen_1_landing:
    survey_status:
      submitted: 0          # int, live count
      total: 0              # int, live count
      missing_authorities: []
    kpis:
      national_average:
        title: ""           # live card title
        percentage: ""      # display string, includes %
        trend: up           # up | down | flat
      categories: []        # list of the same card shape
    resilience_scores: []   # list of {authority, score, status}
    active_filters: {}      # english id → selected Hebrew label
```

The zeros and empty lists above are the schema, not the golden snapshot. Implementation replaces
them with the live landing screen before the test is expected to pass.

### `survey_status`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `submitted` | int | digit string from the top-left block | integer rule |
| `total` | int | digit string from the same block | integer rule |
| `missing_authorities` | list of strings | authority names under that block | exact string; extra UI names ignored |

**Validation**: both counts are required when the block is visible. A golden name missing from
the UI fails. An empty UI list fails when the golden list is non-empty and the anchor is visible.

### `kpis.national_average` and each `kpis.categories` item

| Field | YAML type | Match |
|-------|-----------|--------|
| `title` | string | exact, after bidi and outer whitespace are removed |
| `percentage` | string | exact display text, including `%` |
| `trend` | string | `up`, `down`, or `flat` |

**Validation**: categories match on `title`. Extra category cards are ignored. A missing golden
title fails. `percentage` is never a float and never a bare integer in the YAML.

`trend` transitions, decided on the page from the card's non-canvas arrow:

| Signal | Stored word |
|--------|-------------|
| Up glyph, or green when no glyph direction is available | `up` |
| Down glyph, or red when no glyph direction is available | `down` |
| Flat glyph, or yellow when no glyph direction is available | `flat` |
| Canvas only, or no arrow node | `""` (golden word then fails) |

### `resilience_scores` row

| Field | YAML type | Match |
|-------|-----------|--------|
| `authority` | string | exact; this is the row identity |
| `score` | int when the cell is a whole number; otherwise string | integer rule, or exact string |
| `status` | string | `green` or `yellow` |

**Validation**: rows match on `authority`. Extra UI authorities are ignored. A golden authority
that the collector never sees fails. `status` is only the word `green` or `yellow` in the YAML.
A background that is neither color is returned as `rgb(...)` and fails that golden word.

Color transitions, from computed background of the row or the score cell:

| Paint | Stored word |
|-------|-------------|
| Green channel dominates | `green` |
| Red and green both high, blue low | `yellow` |
| Any other computed color | raw `rgb(...)` |

### `active_filters`

Flat map of English id → selected label.

| Id | Meaning | Example label shape |
|----|---------|---------------------|
| `district` | Right-hand district slicer | `מחוז דרום` |
| `sub_district` | Right-hand sub-district slicer | `נפת לכיש` |

Further ids are added only when the live right-hand rail has more selected slicers. The id is
the `SlicerDefinition.id`. The Hebrew accessible name is `role_name` on the page, not a YAML key.
Values are exact selected labels. The test does not click them.

## Runtime dict

`read_screen_1_metrics() -> dict` uses the same four keys as `screen_1_landing`.

- Counts, scores, and percentages are strings (`"12"`, `"1,324"`, `"55%"`).
- `trend` and `status` are the words in the tables above, or `""` / `rgb(...)` when the signal
  is not one of those words.
- `missing_authorities`, `categories`, and `resilience_scores` are lists. An unreadable visible
  section returns an empty list or an empty string so the test can fail it.
- Filter values are the selected label only, with the slicer title removed.

## State

This screen has no workflow state. `navigate()` leaves the report on Screen 1. The reader does
not change slicers, tabs, or scroll position except for the temporary scroll inside
`collect_virtualized_rows`, which starts at the top of the resilience grid and moves only that
grid.

## Relationships

- `active_filters` describes the slice of authorities the other three blocks are showing. The
  test does not re-apply them. It asserts they still show the golden labels.
- `survey_status.missing_authorities` names authorities. `resilience_scores.authority` names
  authorities in the score table. The two lists are not required to be equal.
- `kpis.national_average.title` is the anchor title for the assessment visual. Category cards
  are the other cards in that visual.
