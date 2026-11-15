# Contract: Screen 2 Sanity Maps

**Feature**: 034-screen2-sanity-maps | **Date**: 2026-10-19

The two card tests stay. `tests/ui/` and `core/` are not edited. The golden file is not edited.

## Unchanged tests

`test_global_metrics_match_db` and `test_filtered_population_matches_db` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` keep their current steps and assertions.

## Shared setup for every new test

1. Load `data/alerts/db_sanity_am_kalavi.yaml` with `load_sanity_data()`.
2. Read `dashboard_sanity_checks.screen_2_alerts_analysis`.
3. Call `population_dashboard.set_date_range(to_page_date(start), to_page_date(end))`.
4. Mark the test `@pytest.mark.sanity`.
5. Comments inside functions are English.

## Settlement

`test_alerted_population_by_settlement_matches_db(population_dashboard)`

1. Apply the shared setup.
2. Build `Chart(page=population_dashboard.page, frame=population_dashboard._report_frame(), timeout_ms=population_dashboard.timeout)`.
3. `reading = chart.read(population_dashboard.SETTLEMENT_CHART, scope=population_dashboard.PAGE_TITLE)`.
4. Take the series index of `population_dashboard.WARNED_SERIES`.
5. Build `{category.label: category.values[index]}` for numeric cells.
6. For each name in `metrics.alerted_population_by_settlement.values`, assert the UI value equals the golden integer.

Do not skip this test. `Chart.read` already exists.

## מחוז

`read_district_labels(self) -> dict[str, int]` on `pages/alerts_analysis/population_page.py`

- Read visible rows in `DISTRICT_CHART` the same way `_sum_visible_district_rows` does.
- Key each alerts integer by the row-header text.
- Do not scroll.
- Do not change `chart_total`.

`test_hierarchy_mahoz_sum_matches_db`

1. Apply the shared setup.
2. `set_district_aggregation("sum")`.
3. Compare `read_district_labels()` to `alerts_by_hierarchy.mahoz.sum`.
4. If the map is empty, `pytest.skip("Missing page object method for district labels")`.

`test_hierarchy_mahoz_daily_avg_matches_db`

1. Apply the shared setup.
2. `set_district_aggregation("average")`.
3. Compare `read_district_labels()` to `alerts_by_hierarchy.mahoz.daily_avg`.
4. The same empty-map skip applies.

## Missing hierarchy levels

These tests apply no date range and click nothing:

| Test | Skip message |
|------|----------------|
| `test_hierarchy_nafa_matches_db` | `Missing page object method for hierarchy level nafa` |
| `test_hierarchy_rashut_matches_db` | `Missing page object method for hierarchy level rashut` |
| `test_hierarchy_yeshuv_matches_db` | `Missing page object method for hierarchy level yeshuv` |

Each message is passed to `pytest.skip` exactly.

## Dates

`read_date_counts(self) -> dict[str, int]`

1. Dismiss the overlay, right-click the dates visual, and click the show-as-table item, as `_dates_table_total` does.
2. Scroll visible rows and store each row header with its alerts integer.
3. Use the header text as the key, not `aria-rowindex`.
4. Call `_leave_dates_table()` before returning, including on failure after the table opened.
5. Do not change the value `chart_total(DATES_CHART)` returns.

`test_alerts_by_date_matches_db`

1. Apply the shared setup.
2. Normalize a `DD/MM/YYYY` header to `YYYY-MM-DD`.
3. Compare the map to `alerts_by_date.values`.
4. If the map is empty, `pytest.skip("Missing page object method for alerts by date")`.
5. A non-empty map that lacks a golden date fails the assertion.

## Hours

`read_hour_buckets(self) -> dict[str, int]`

- Read `aria-label` on `svg rect`, `svg path`, and `svg circle` inside `HOUR_CHART`.
- Keep a label that contains an `HH:MM` or `H:MM` token and an integer.
- Drop a label that contains `ממוצע` or a fractional number.
- Store `{HH:MM: integer}`.
- Do not call `set_district_aggregation`.
- Do not change `chart_total(HOUR_CHART)`.

`test_alerts_by_hour_sum_matches_db` compares that map to `alerts_by_hour.sum`. An empty map skips with `Missing page object method for hour sum`.

`test_alerts_by_hour_daily_avg_matches_db` calls `pytest.skip("Missing page object method for hour daily_avg")` and does not read the chart.

## Map comparison

For a non-empty UI map and a golden map:

- Every golden key is present after normalization.
- The integers are equal.
- UI keys that are not in the golden map are ignored.

## Examples (normative)

| Call | Golden path | Result |
|------|-------------|--------|
| `Chart.read` warned series | `alerted_population_by_settlement.values` | ר'ג'ר == 2752, and the other eight names |
| `set_district_aggregation("sum")` then `read_district_labels()` | `alerts_by_hierarchy.mahoz.sum` | מחוז צפון == 12, פיקוד דרום == 1 |
| `set_district_aggregation("average")` then `read_district_labels()` | `alerts_by_hierarchy.mahoz.daily_avg` | both names == 1 |
| `read_date_counts()` | `alerts_by_date.values` | five September 2023 keys |
| `read_hour_buckets()` | `alerts_by_hour.sum` | 00:00 == 5, 04:00 == 5, and three hours == 1 |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| The two card tests still pass | `test_global_metrics_match_db` and `test_filtered_population_matches_db` |
| Missing levels do not fail the run | the three hierarchy skips and the hour daily-average skip |
| `tests/ui/` and `core/` are untouched | review of the edit list |
