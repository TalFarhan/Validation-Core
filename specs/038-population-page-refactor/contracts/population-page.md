# Contract: AlertsPopulationPage public surface

The refactor may change private helpers only. These public signatures stay. Tests under `tests/sanity/` and `tests/ui/` are not edited.

## Methods

| Signature | Observable result |
|-----------|-------------------|
| `__init__(page: Page)` | Composes `KPI` and `Chart` on the report frame. Timeout stays 60 seconds. |
| `before_report_ready_check() -> None` | Selects this page when the district chart is not showing. A missing control returns. It does not raise. |
| `clear_filters() -> None` | Clears slicers, then returns when two total-card reads match or the timeout ends. |
| `set_between_dates(start: str, end: str) -> None` | Fills the start and end date fields. |
| `set_date_range(start_date: str, end_date: str) -> None` | Commits both dates, then waits until the total card settles. |
| `set_day_night(mode: DayNightMode) -> None` | `off`, `day`, or `night`. |
| `set_value_range(low: int, high: int) -> None` | Fills the numeric range. |
| `set_district_aggregation(mode: AggregationMode) -> None` | `sum` or `average`. Clicks the exact button inside the district visual when that count is 1; otherwise clicks the first exact button in the frame. |
| `set_hierarchy_level(level: str) -> bool` | `nafa`, `rashut`, `yeshuv`. `false` when that control is not visible. No substitute click. |
| `read_card(role: CardRole) -> int \| float` | `total`, `warned`, `unprotected`. |
| `chart_total(title: str, series_index: int = 0) -> int \| float` | Dates, hour, district, and settlement branches stay the ones documented in the data model. |
| `read_chart_categories(title: str)` | Categories and series for the page-scoped container. Return annotation stays absent. |
| `read_district_labels() -> dict[str, int]` | Rows, then marks, then tooltip. `{}` when the container is missing. |
| `read_settlement_warned() -> dict[str, int]` | Warned population by settlement. |
| `read_date_counts() -> dict[str, int]` | Date header to count. The table is closed before return. |
| `read_hour_buckets() -> dict[str, int]` | Hour sum. Tooltip only when the map is still empty. |
| `read_hour_daily_avg() -> dict[str, int]` | Whole daily average. `{}` when it cannot be paired. |

`DayNightMode`, `CardRole`, and `AggregationMode` stay the same literals.

## Constants

`PAGE_TITLE`, `DISTRICT_CHART`, `DATES_CHART`, `HOUR_CHART`, `SETTLEMENT_CHART`, `WARNED_SERIES`, `UNWARNED_SERIES`, `TOTAL_CARD`, `WARNED_CARD`, `UNPROTECTED_CARD`, `DAY_TOGGLE`, `NIGHT_TOGGLE`, `SUM_MODE`, and `AVERAGE_MODE` keep their current strings.

## Private behavior the public results depend on

### Scroll collector

`chart_total` for `DATES_CHART` and `read_date_counts()` both use `_collect_scrolled_rows`.

- Scroll to the top, then collect, then page down.
- A row that fails `is_visible()` is omitted.
- Two passes that add no key and do not move end the loop. `self.timeout` ends it as well.
- The total's key is `aria-rowindex` or the row header. The date map's key is the row header.
- The alerts cell is a `gridcell`. `סה"כ` is omitted. `0` is included.
- There is no scroll-to-end pass and no read of hidden rows.
- `חזרה לדוח` still runs before either public method returns. A failure to open or close the table still raises `AssertionError`.

### Row script

`_visible_alert_entry` and `_visible_date_entry` evaluate `_ROW_CELLS_JS`. Other row readers in this file use that same script. Their Python skip rules stay.

### Hover

`_hover_mark_values` is the only mark-hover loop. District names and hour buckets pass different parsers. Hover still does not run when an earlier read returned a non-empty map.

### Chart access

- `set_district_aggregation` does not call `Chart._container`. It uses `_visual_container`. An `AssertionError` from that locator falls through to the frame-level button.
- `read_chart_categories` does not call `Chart._parse`. It calls `Chart.parse_container(container, title)`.
- `Chart.parse_container` is public, takes a `Locator` and a title string, and returns `(categories, series)` from the existing `_parse`. It does not blank an empty reading.
- `Chart.read`, `category_count`, `is_descending`, and `displayed_title` keep their signatures and behavior.
- The page does not import `Chart._dedupe_doubled`.

### Failures and waits

- No `except Exception` in `population_page.py`.
- Locator and evaluate failures are `playwright.sync_api.Error`.
- `read_district_labels` and the hour-average category fallback still turn `AssertionError` into `{}`.
- Menu and grid appearance use `wait_for(state="visible")`.
- Card, date-range, and district-total settle stay polls until two reads match.
- `set_hierarchy_level` does not start with a fixed 800 ms sleep. It waits for `aria-pressed` or `aria-selected` when the control has that attribute.

## Out of scope

- Editing any file under `tests/sanity/` or `tests/ui/`.
- Editing `data/alerts/db_sanity_am_kalavi.yaml`.
- Editing `core/portal/`.
- Adding report titles or Hebrew labels under `core/`.
- Merging `_scroll_visual` into the dates-table scroller.
- Changing fleet page objects.
