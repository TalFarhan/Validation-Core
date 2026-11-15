# Contract: Status Picture Sanity

**Feature**: 035-status-picture-sanity | **Date**: 2026-10-19

Screen 2 tests stay. `tests/conftest.py` and `core/` stay. The golden file stays.

## Page

`pages/status_picture/status_picture_page.py`

`StatusPicturePage` inherits `AlertsAnalysisPage`.

- Catalog search remains `ניתוח התרעות`.
- `_report_ready_locator` looks for `אזורי התרעה תחת ירי`.
- The page does not click `ניווט בין עמודים`.
- `pages/status_picture/__init__.py` is empty.

## Methods

### `clear_filters()`

Clear every slicer through the composed `Slicer`, then wait until `אזורי התרעה תחת ירי` repeats.

### `set_date_range(start, end)`

Fill `input[aria-label^='תאריך התחלה']` with `start` and `input[aria-label^='תאריך סיום']` with `end`. Each commit is `_dismiss_overlay`, expect visible, `click(force=True)`, `fill`, Enter, `_dismiss_overlay`. Then wait until `אזורי התרעה תחת ירי` repeats.

The test passes `13/06/2025` and `25/06/2025` for the current golden file.

### `read_cards() -> dict[str, int]`

Read these titles with `KPI.number` inside the report frame. Omit a title that is not visible. Do not raise for one missing title.

| Key | Title |
|-----|--------|
| `total_warning_zones` | `מספר אזורי התרעה` |
| `warning_zones_under_fire` | `אזורי התרעה תחת ירי` |
| `total_alerted_population` | `כמות אוכלוסייה מותרעת` |
| `alerted_population` | `אוכלוסייה מותרעת` |

### `read_alerts_by_category() -> dict[str, int]`

Read `סה"כ בטווח שנבחר` in each scope. Return `{}` when none of the three scopes can be read.

| Key | Scope |
|-----|--------|
| `category_1_rockets` | `ירי רקטות וטילים` |
| `category_2_aircraft` | `חדירת מחבלים` |
| `category_10_terrorists` | `חדירת כלי טיס עוין` |

### `read_top_10_settlements() -> dict[str, int]`

Read `{name: count}` from `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר`. Return `{}` when names and counts cannot be paired. Do not read the chart whose title ends in `ביממה הנוכחית והקודמת`.

## Fixture

`tests/sanity/status_picture_dashboard/conftest.py`:

```text
status_picture_dashboard = bind_dashboard(StatusPicturePage, "status_picture_dashboard")
```

`tests/sanity/status_picture_dashboard/__init__.py` is empty. The test module imports `status_picture_dashboard` from that conftest. `tests/conftest.py` does not import the page.

## Tests

All four are `@pytest.mark.sanity`. Comments inside functions are English. Dates are converted from `YYYY-MM-DD` to `DD/MM/YYYY` in this module.

| Test | Steps |
|------|--------|
| `test_screen_1_global_metrics` | `clear_filters`, then `read_cards`. Assert `total_warning_zones == 1337` and `total_alerted_population == 10142584` through the golden `expected_value` fields. Skip with `Missing Page Object reader for total_warning_zones` or `Missing Page Object reader for total_alerted_population` when that key is absent. |
| `test_screen_1_filtered_metrics` | `set_date_range` with the translated golden range. Assert `warning_zones_under_fire == 1271` and `alerted_population == 10091037`. The same skip form applies when a key is absent. This test does not read categories or settlements. |
| `test_screen_1_alerts_by_category` | Set the same range. Compare `read_alerts_by_category()` to `alerts_by_category.values`. An empty map calls `pytest.skip("Missing Page Object reader for alerts_by_category")`. |
| `test_screen_1_top_settlements` | Set the same range. Compare `read_top_10_settlements()` to `top_10_settlements.values`. Every golden name must match. Extra UI names are allowed. An empty map calls `pytest.skip("Missing Page Object reader for top_10_settlements")`. |

## Unchanged

- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- `pages/alerts_analysis/population_page.py`
- `tests/conftest.py`
- `tests/ui/`
- `core/`
- `data/alerts/db_sanity_am_kalavi.yaml`

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Screen 1 collects four tests | `python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py --collect-only` |
| Screen 2 module is untouched | review of the edit list |
| Root conftest has no status-picture import | review of `tests/conftest.py` |
