# Data Model: Hasbara Dashboard UI Sanity Validation

Source file (unchanged): `data/hasbara/db_sanity.yaml`.
Root key: `hasbara_dashboard`.

This slice does not add fields and does not change values. It defines how each existing
field is compared to the live UI. `dashboard_info` has no `last_updated` key. Tests do
not read one.

Shared date string in the current file: `01/10/2026 - 31/10/2026`.

## Screen 1 — `screen_1_written_response`

Landing tab. No tab click when the KPI card is already visible.

| Path | Type | Match rule |
|------|------|------------|
| `dashboard_info.title` | string | Visible iframe phrase. Current file: `ניתוח פניות הסברה - תחקור פניות מענה כתוב`. |
| `dashboard_info.date_range` | string | Split on ` - `. If the start and end inputs are hidden or disabled, one click on the filter-bar toggle (`כלל התאריכים` or `יום נוכחי`) exposes them. The inputs are then filled and the visible range equals this string. |
| `dashboard_info.data_source` | string | Visible phrase. Current file: `מענה כתוב דיגיטל 99`. |
| `active_filters` | map of string to string | Read after the date apply. Keys: `hours`, `language`, `platform`, `topic`. Current values: `הכל`. Not passed to `select`. |
| `kpi_metrics.inquiries_summary.*` | int | Visible text inside the inquiries widget (the host that contains `סה"כ פניות` and `פניות פתוחות`), read after that widget's spinner is hidden and the visible total and open texts have settled. The settle script runs on the iframe `body`. Current file: `total_chats` 779, `total_requests` 1324, `open_requests` 49, `closed_requests` 1234. A grouped display such as `1,324` matches the int. A hidden measure image, a tooltip, and a stale SVG are not the value. Both `total_requests` and `open_requests` stay in the comparison. |
| `kpi_metrics.request_closing_times.average` | string | Exact `DD:HH:MM:SS` beside `ממוצע` inside the `זמני סגירת פנייה` widget. Current file: `00:04:35:46`. |
| `kpi_metrics.request_closing_times.maximum` | string | Exact `DD:HH:MM:SS` beside `מקסימלי` in that same widget. Current file: `16:14:33:22`. |
| `kpi_metrics.response_wait_times.average` | string | Exact `DD:HH:MM:SS` beside `ממוצע` inside the `זמני המתנה למענה` widget. Current file: `00:01:36:13`. |
| `kpi_metrics.response_wait_times.maximum` | string | Exact `DD:HH:MM:SS` beside `מקסימלי` in that same widget. Current file: `00:08:11:12`. |
| `charts.written_media_breakdown[]` | rows | Key `platform`. Fields `count` (int) and `percentage` (string, e.g. `59%`, `0%`). |
| `charts.language_breakdown[]` | rows | Key `language`. Current row: `עברית`, count 1233, `100.0%`. |
| `charts.recurring_requests_breakdown[]` | rows | Key `type`. |
| `charts.leading_topics[]` | rows | Key `topic`. Field `count` (int). No percentage in the file. |
| `charts.requests_by_hour_trend.series[].name` | string | Both names present, golden order: `ממוצע פניות`, `מקסימום פניות`. |
| `charts.requests_by_hour_trend.x_axis_labels` | list of string | Exact list, golden order. Current file: `00:00` through `21:00` step 3 hours. No Y values. |

## Screen 2 — `screen_2_written_response_investigation`

Tab label: `תחקור מענה כתוב`. Ready when the investigation grid is visible.
Title equals screen 1's title in the current file. The grid locator distinguishes the tab.

| Path | Type | Match rule |
|------|------|------------|
| `dashboard_info.title` | string | Visible phrase after the tab wait. |
| `dashboard_info.date_range` | string | Same toggle-then-fill rule as screen 1. The bar is global, so a range already showing this string is not typed again. |
| `dashboard_info.platforms_included` | string | Visible phrase. Current file lists SMS, Facebook/Instagram Messenger, WhatsApp, Email, Facebook Feed. |
| `active_filters` | map | Same four keys as screen 1, all `הכל`. |
| `investigation_table_data[]` | rows | Key `request_id`. 13 rows in the current file. The reader opens Show as a table on the grid visual, reads the expanded grid, closes that view, and dedups on this key. Extra UI rows ignored. `handling_time` comes from that expanded grid. |

### Investigation row fields

| Field | Type | Rule |
|-------|------|------|
| `request_id` | string | Row key. Example `124369`. |
| `handling_time` | string | Exact duration. User-required column. Read from the expanded Show-as-a-table grid, not from the clipped canvas viewport. |
| `platform` | string | Exact. User-required column. Example `Email`, `WhatsApp`. |
| `topic` | string | Exact, including comma-separated topics. User-required column. |
| `initial_response_wait_time` | string | Exact duration. |
| `initial_response_time` | string | Exact `DD/MM/YYYY HH:MM:SS`. |
| `opening_time` | string | Exact `DD/MM/YYYY HH:MM:SS`. |
| `language` | string | Exact. Current rows: `עברית`. |
| `agent_name` | string | Exact. Current rows: `""` matches a blank cell. |
| `customer_name` | string | Exact. |
| `chat_id` | string | Exact. |

## Screen 3 — `screen_3_satisfaction_feedback`

Tab label: `ניתוח משובי שביעות רצון`. Ready when the three survey section titles are
visible and a visible metric under each card has settled. Hidden tooltips and stale
SVGs are not that metric. No `active_filters` map. Date range still applies. The five
named slicers are read only when visible. The golden strings and integers below are
unchanged.

| Path | Type | Match rule |
|------|------|------------|
| `dashboard_info.title` | string | Current file: `ניתוח פניות הסברה - ניתוח משובי שביעות רצון`. |
| `dashboard_info.date_range` | string | Same toggle-then-fill rule. A range already showing this string is not typed again. |
| `dashboard_info.platforms_included` | string | Visible phrase. |
| `dashboard_info.data_source` | string | Visible phrase. Current file: `משובי שביעות רצון דיגיטל 99`. |
| `surveys_summary.phone_center.surveys_sent` | string | Exact. Current file: `לא ידוע`. |
| `surveys_summary.phone_center.surveys_filled` | int | Exact. Current file: `129`. |
| `surveys_summary.written_response.surveys_sent` | string | Exact, comma kept. Current file: `1,062`. |
| `surveys_summary.written_response.surveys_filled` | int | Exact. Current file: `39`. |
| `surveys_summary.quality_control.valid_calls_checked` | string | Exact. Current file: `אין מידע`. |
| `surveys_summary.quality_control.validity_percentage` | string | Exact. Current file: `אין מידע`. |
| `message_reception.question` | string | Visible. Current file: `האם המידע שהתקבל סייע`. |
| `message_reception.responses[]` | rows | Key `level`. Fields `count` (int) and `percentage` (string). |
| `service_reception.active_tab` | string | Selected before the read by `select_satisfaction_tab`. The file repeats this key. PyYAML keeps the last value. Loaded value: `אופן מקצועי`. The click target is a visible exact `tab`, `button`, `link`, or text node in the report frame, preferably inside the `התקבלות השירות` host. It is not the page-rail control. |
| `service_reception.question` | string | Visible after the tab select. Loaded value: `האם השירות שהתקבל היה מקצועי`. |
| `service_reception.responses[]` | rows | Key `level`. Loaded rows are the professional-manner distribution (last duplicate block). |
| `leading_contact_channels[]` | rows | Key `channel`. Field `count` (int). |
| `platforms_breakdown[]` | rows | Key `platform`. Current spellings: `מוקד טלפוני`, `Whatsapp`, `Messenger`. `percentage` stays a string such as `76.79%`. |

## Screen 4 — `screen_4_feedback_investigation`

Tab label: `תחקור משובים`. Ready when a visible column header named `הערות` or `הערה` is in the feedback grid. The full parenthetical title is not that check.

| Path | Type | Match rule |
|------|------|------------|
| `dashboard_info.title` | string | Current file: `ניתוח פניות הסברה - ניתוח משובי שביעות רצון (תחקור משובים)`. |
| `dashboard_info.date_range` | string | Same toggle-then-fill rule. A range already showing this string is not typed again. |
| `dashboard_info.platforms_included` | string | Visible phrase. |
| `active_filters` | map | Keys: `information`, `service_orientation`, `professionalism`, `platform`, `settlement`, `hours`. Current values: `הכל`. |
| `feedback_investigation_table_data[]` | rows | Key `inquiry_id`. 6 rows in the current file. The reader opens Show as a table on the grid visual, reads the expanded grid, closes that view, and dedups on this key. Extra UI rows ignored. |

### Feedback row fields

| Field | Type | Rule |
|-------|------|------|
| `inquiry_id` | string | Row key. Example `124455`. |
| `comments` | string | Exact Hebrew text, or `""` for a blank cell. Bidi marks stripped. Punctuation kept. |
| `opening_time` | string | Exact `DD/MM/YYYY HH:MM:SS`. |
| `initial_response_time` | string | Exact, or `""` when the golden cell is empty. |
| `platform` | string | Exact. Current rows use `Whatsapp` and `Messenger`. |
| `customer_name` | string | Exact. |
| `agent_name` | string | Exact. Current rows: `""`. |
| `survey_sent_time` | string | Exact `DD/MM/YYYY HH:MM`. |
| `is_service_courteous` | string | Exact level. |
| `is_service_professional` | string | Exact level. |
| `did_info_help` | string | Exact level. |
| `phone_number` | string | Exact, including a number that already contains dashes. |

## Comparison state

```text
golden block non-empty
        │
        ▼
visual title or grid absent? ── yes ──► pytest.skip
        │ no
        ▼
reader returns empty? ── yes ──► FAIL (path, ui=[], golden=...)
        │ no
        ▼
each golden key/row equal? ── no ──► FAIL (path, ui, golden)
        │ yes
        ▼
pass (extra UI keys/rows ignored)
```

## Relationships

- One golden file, four screen blocks, one shared October range. The range is typed only
  after the filter-bar toggle exposes the start and end inputs. A later screen in the
  same session reads the inputs and skips a second toggle click when they already match.
- Screen 1 and screen 2 share a title and a four-slicer filter map. The tab and the grid
  separate them.
- Screen 3 has cards and charts and no detail table. Its courtesy bars depend on
  `service_reception.active_tab`. The loader keeps one value for that key
  (`אופן מקצועי`). The page clicks that exact visible sub-tab. It does not
  click the page rail.
- Screen 4's row identity is `inquiry_id`. Screen 2's row identity is `request_id`.
  The two id columns are not interchangeable. `VisualTable` stores each expanded-grid
  row by its full cell tuple and does not know either field name. The page maps Hebrew
  headers and then keeps the first row for each id.
- A chart table row's identity, inside `VisualTable`, is the full cell tuple. That identity
  is also an argument. It is not a golden key.
- `PublicInquiriesPage` reads this file only from the test module. The page does not load
  YAML. `core/` does not load it.
