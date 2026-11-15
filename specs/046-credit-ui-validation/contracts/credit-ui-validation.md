# Contract: Credit Consumption UI Sanity Validation

**Feature**: `046-credit-ui-validation` | **Date**: 2026-11-04

Expands the feature 044 page and sanity module. Alerts, status-picture, fleet, `core/`,
`db/`, the root `conftest.py`, and `data/credit/db_sanity_purim2026.yaml` stay unchanged.
`verify_freshness` stays inherited and the credit smoke test stays a one-line call.

## Page

`pages/credit_consumption/credit_consumption_page.py`

Class `CreditConsumptionPage` still inherits `ReportShell`. Existing methods stay. This
slice adds the checks below and keeps the value shapes in the readers.

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `"צריכת אשראי"` (unchanged) |
| Screen 1 title phrase | existing `SCREEN_1_TITLE` (`תמ״צ צריכת אשראי`) |
| Screen 2 title phrase | existing `SCREEN_2_TITLE` (`צריכת אשראי - ייצוא נתונים`) |
| Freshness reader | inherited `_last_refresh_caption_text()` — no override, no new parser |
| Smoke | inherited `verify_freshness` — no override |
| Charts | existing Show as a table (`הצג כטבלה` / `Show as a table`) |

`pages/credit_consumption/page.py` stays a re-export. Do not add
`pages/credit_consumption/__init__.py`.

## Methods added

### `title_is_visible(self, title: str) -> bool`

True when the existing `_iframe_phrase_locator(title)` is visible. The argument is the
YAML title. No new selector.

### `visual_is_rendered(self, title: str) -> bool`

True when the existing chart title is visible as text or as a `group` name (the same
lookup `_visual_container` uses), without opening Show as a table. False when that title
is absent. Does not catch a missing title and return rows.

### `export_grid_is_rendered(self) -> bool`

True when Screen 2 shows a visible `grid` or `table` (the same roles `_visible_table_rows`
already searches). False when neither role is visible.

### `any_kpi_card_rendered(self) -> bool`

True when at least one title in the existing `_KPI_SPECS` is visible through the existing
KPI card locator. False when none of those titles are visible.

## Methods kept (shape rules)

### `apply_filters(self, filters: dict) -> None`

Unchanged rule: skip `None` and `הכל`. Apply the remaining ids through the existing
`Slicer` definitions. The period string is whatever the YAML map contains.

### `open_export_page(self) -> None`

Unchanged. Bilingual page-rail (`ניווט בין עמודים` / `Page navigation`), then wait for
`SCREEN_2_TITLE`.

### `read_kpi_metrics(self) -> dict`

Nested `kpi_metrics` shape. Percent cards stay strings that include `%`. A missing card
is omitted so the test can fail the golden key. Do not skip inside the reader.

### `set_metric(self, kind: str) -> None` / `set_visualization(self, kind: str) -> None`

`kind` is `expense_amount` or `transactions_count`, and `line` or `bar`. The test obtains
those two tokens from `key.rsplit("_", 1)`.

### `read_daily_trends(self) -> list[dict]`

Show as a table on `TRENDS_CHART`. Rows include `date` and string `day`. Scalar `value`
unless the active toggle is transactions-count + bar, in which case `values` is the list
of numbers from that row. Do not unwrap the list. Return `[]` when the table has no data
rows. Do not turn a missing chart into a skip; the test asks `visual_is_rendered` first.

### `read_daily_alerts(self) -> list[dict]`

Show as a table on `ALERTS_CHART`. Rows `{date, day, alerts_count}`. Key used by the test
is `date`. `day` stays a string.

### `read_expenses_by_authority(self) -> list[dict]`

Show as a table on `AUTHORITY_CHART`. Rows `{authority, amount}`. Key is `authority`.

### `read_export_table(self) -> list[dict]`

Visible grid mapped through `_EXPORT_HEADERS`. `quantity` is an `int`. `amount` is the
plain cell string and keeps commas. Other fields are plain strings.

## Fixture

Unchanged:

```text
credit_consumption_dashboard = bind_dashboard(
    CreditConsumptionPage, "credit_consumption_dashboard"
)
```

`tests/conftest.py` does not import the page.

## Tests

File: `tests/sanity/credit_consumption_dashboard/test_data_validation.py`.

All data tests stay `@pytest.mark.sanity`. Comments inside functions stay English.
Expected values are loaded from `credit_consumption_dashboard` in the YAML. The period
name is not a literal in the test. `הכל` is not passed as a click.

### Shared asserts

`_assert_nested(actual, expected, path)` walks golden dicts. Extra UI keys are ignored.
If `expected` is non-empty and `actual` is empty, it asserts (it does not skip). A leaf
mismatch asserts `{path}: ui={actual!r} golden={expected!r}`.

`_assert_golden_rows(actual, expected, key_fields, path)` indexes UI rows by `key_fields`.
Extra UI rows are ignored. If `expected` is non-empty and `actual` is empty, it asserts
with `ui=[]`. Each golden field asserts `{path}[{key}].{field}: ui=... golden=...`.

### `test_screen_1_dashboard_info_matches_golden`

1. `apply_filters(screen_1_summary.active_filters)`.
2. Assert `title_is_visible(dashboard_info.title)` with path
   `credit_consumption_dashboard.screen_1_summary.dashboard_info.title`.
3. Read `_last_refresh_caption_text()`, collapse whitespace, and assert
   `dashboard_info.last_updated` is contained in that text. Path:
   `credit_consumption_dashboard.screen_1_summary.dashboard_info.last_updated`.
   Do not parse the timestamp.

### `test_kpi_metrics_match_golden`

1. Apply Screen 1 filters.
2. If `any_kpi_card_rendered()` is false, `pytest.skip` with the reason that the KPI
   cards are not rendered.
3. `read_kpi_metrics()` then `_assert_nested` at path
   `credit_consumption_dashboard.screen_1_summary.kpi_metrics`.

### `test_daily_trends_match_golden`

1. Apply Screen 1 filters.
2. If `visual_is_rendered(TRENDS_CHART)` is false, `pytest.skip`.
3. For each `daily_trends_by_toggle` key: `metric, visualization = key.rsplit("_", 1)`,
   `set_metric`, `set_visualization`, `read_daily_trends`, then
   `_assert_golden_rows` with key `("date",)` and path
   `credit_consumption_dashboard.screen_1_summary.daily_trends_by_toggle.<key>`.
4. `day` is compared as a string. `values` on `transactions_count_bar` is compared as a
   list.

### `test_daily_alerts_match_golden`

1. Apply Screen 1 filters.
2. If `visual_is_rendered(ALERTS_CHART)` is false, `pytest.skip`.
3. Otherwise `_assert_golden_rows` on `read_daily_alerts()` with key `("date",)`.
   Empty rows fail.

### `test_expenses_by_authority_match_golden`

1. Apply Screen 1 filters.
2. If `visual_is_rendered(AUTHORITY_CHART)` is false, `pytest.skip`.
3. Otherwise `_assert_golden_rows` on `read_expenses_by_authority()` with key
   `("authority",)`. Empty rows fail.

### `test_export_table_match_golden`

1. `open_export_page()`.
2. `apply_filters` on `top_bar` updated with `side_bar`.
3. Assert `title_is_visible(screen_2_data_export.title)` with path
   `credit_consumption_dashboard.screen_2_data_export.title`.
4. If `export_grid_is_rendered()` is false, `pytest.skip`.
5. Otherwise `_assert_golden_rows` on `read_export_table()` with key
   `("transaction_date", "authority_name", "sub_category")`. Empty rows fail.
   `quantity` must compare equal to the YAML int. `amount` must compare equal to the
   YAML string.

### `test_export_page_opens`

Stays. It only checks that `open_export_page()` lands on Screen 2.

## Out of scope

No edits under:

- `core/portal/`
- `core/components/`
- `pages/alerts_analysis/` and `tests/**/alerts_analysis_dashboard/`
- `pages/status_picture/` and `tests/**/status_picture_dashboard/`
- `pages/fleet_dashboard/` and `tests/**/fleet_dashboard/`
- `db/`
- root `conftest.py`
- `data/**/*.yaml`

No SVG parsing, no tooltip parsing, and no import of an alerts page helper.
