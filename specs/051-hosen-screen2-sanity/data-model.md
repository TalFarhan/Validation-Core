# Phase 1 Data Model: Hosen Status Screen 2 YAML Sanity

This slice adds no database schema and does not edit `data/hosen/db_sanity.yaml`. The entities
are the existing golden block and the dict `read_screen_2_metrics()` returns. The page returns
display text. The test applies the empty-cell rule when the golden node is `null`.

`date` and `filters` are both inputs and checked results. The test opens the investigation
screen, applies `date`, then `filters` in YAML order, waits until Screen 2 is idle, and only
then reads.

## Golden record (`data/hosen/db_sanity.yaml`)

Root key: `hosen_dashboard`. This slice reads `screen_2_investigation` and does not rewrite
`screen_1_landing`.

```yaml
hosen_dashboard:
  screen_2_investigation:
    title: ""                 # investigation screen title; value lives in the YAML
    date: ""                  # selected date combobox label
    filters: {}               # english id → Hebrew label, applied then read back
    tables:
      authorities_breakdown_table: []  # list of authority rows
      totals_row: {}                   # nine metric fields, no authority
      trends_by_date_table: []         # list of date rows; a metric may be null
```

The empty strings above are the schema. The checked-in file is the golden snapshot, including
`תמ״צ התנהגות - מסך תחקור`, `08/06/2026`, `מחוז דרום`, `נפת לכיש`, the authority percents, the
totals percents, and the `null` under `trends_by_date_table` for `13/06/2025` /
`functional_continuity`. This plan does not copy those values into Python.

### `title`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `title` | string | visible investigation heading | exact after bidi trim; `"` and `״` are the same character |

### `date`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `date` | string | selected date combobox label | exact after bidi trim |

The page does not embed the golden date. It returns whatever label the combobox shows.

### `filters`

| Field | YAML type | UI reading | Match |
|-------|-----------|------------|--------|
| `district` | string | selected smart-filter chip | exact after bidi trim |
| `subdistrict` | string | selected smart-filter chip | exact after bidi trim |

Apply order is YAML order: `district`, then `subdistrict`. Extra slicers in the UI reading are
ignored. A listed id with a different label fails. The live file is the map above. The test
iterates the map and does not name the ids itself.

### Authority row (`tables.authorities_breakdown_table[]`)

| Field | YAML type | Match |
|-------|-----------|--------|
| `authority` | string | exact after bidi trim; this is the row identity |
| `leadership` | string | display text, including `%` |
| `welfare` | string | display text, including `%` |
| `effective_behavior` | string | display text, including `%` |
| `belonging` | string | display text, including `%` |
| `functional_continuity` | string | display text, including `%` |
| `narrative` | string | display text, including `%` |
| `community_resources` | string | display text, including `%` |
| `information` | string | display text, including `%` |
| `resilience_score` | string | display text, including `%` |

**Validation**: every golden `authority` is present. Extra UI rows are ignored. A visible table
anchor and an empty reader fail when the golden list is non-empty. `authority` published by the
page is the first line of the cell.

### Totals row (`tables.totals_row`)

The same nine metric fields as an authority row. The golden object has no `authority` key.

**Validation**: each listed field matches as display text. Extra UI fields are ignored. A
visible summary anchor and an empty dict fail when the golden object has fields.

### Trend row (`tables.trends_by_date_table[]`)

| Field | YAML type | Match |
|-------|-----------|--------|
| `creation_date` | string | `DD/MM/YYYY` display text; this is the row identity |
| nine metric fields | string or `null` | a string matches display text; `null` matches an empty cell |

**Validation**: every golden `creation_date` is present. Extra dates are ignored. `null` does
not match `0%`. A visible chart anchor and an empty reader fail when the golden list is
non-empty.

### Trends visual host

The title text node is not the host. The host is the nearest ancestor `div` whose class
contains `visualContainer`. That node wraps the title and the chart body. `visualTitle` is
inside it and is not a valid right-click target: its menu has no show-as-table item.

| Piece | Rule |
|-------|------|
| Title anchor | `מגמות המרכיבים לפי תאריך` (`_TRENDS_VISUAL_TITLE`) |
| Host | `xpath=ancestor::div[contains(@class, 'visualContainer')][1]` from that title |
| Mark | the caller's attribute (`data-hosen-trend`) set on the host only |
| Miss | no such ancestor → the reader returns no container (`None`), and does not mark the title |

## Reader dict (`read_screen_2_metrics`)

```text
{
  "title": "<visible heading>",
  "date": "<selected combobox label>",
  "filters": {"district": "<chip>", "subdistrict": "<chip>"},
  "tables": {
    "authorities_breakdown_table": [
      {
        "authority": "<first line>",
        "leadership": "67%",
        "welfare": "75%",
        "effective_behavior": "75%",
        "belonging": "83%",
        "functional_continuity": "38%",
        "narrative": "100%",
        "community_resources": "75%",
        "information": "75%",
        "resilience_score": "73%"
      }
    ],
    "totals_row": {
      "leadership": "88%",
      "welfare": "81%",
      "effective_behavior": "89%",
      "belonging": "89%",
      "functional_continuity": "66%",
      "narrative": "88%",
      "community_resources": "71%",
      "information": "91%",
      "resilience_score": "83%"
    },
    "trends_by_date_table": [
      {
        "creation_date": "13/06/2025",
        "leadership": "95%",
        "functional_continuity": ""
      }
    ]
  }
}
```

The percent examples show shape. The implementation reads them from the screen. It does not
paste the golden file into the page. An empty trend cell is `""`, not `None`. The test maps
YAML `null` onto that empty string.

## State

Screen 2 has no stored workflow beyond the test order:

1. Report opens on Screen 1 (`navigate` via the fixture).
2. `open_investigation_screen` shows the investigation title.
3. `select_screen_2_filter("date", ...)` then each filter id. Each call settles.
4. `wait_for_screen_2_idle` settles once more.
5. `read_screen_2_metrics` returns the dict above.

There is no reverse transition in this slice. The next test's fixture opens the report again.
