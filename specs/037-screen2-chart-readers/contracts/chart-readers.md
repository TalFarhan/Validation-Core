# Contract: Screen 2 Chart Readers

**Feature**: 037-screen2-chart-readers | **Date**: 2026-10-19

The golden file stays. `core/` stays. The two card tests stay.

## Page

`pages/alerts_analysis/population_page.py`

### `set_hierarchy_level(level) -> bool`

`level` is `nafa`, `rashut`, or `yeshuv`.

Search the `התרעות לפי מחוז` visual for a visible button, tab, or option whose name is נפה, רשות, or יישוב. Click that control and return true. If it is not visible, return false and do not click anything else.

### `read_district_labels() -> dict[str, int]`

Unchanged call shape.

1. Scroll the district visual and collect visible rows.
2. If that map is empty, pair category text with mark labels.
3. If that map is still empty, hover each visible bar and read the tooltip.
4. Return `{}` when no name can be paired with an integer.

### `read_hour_daily_avg() -> dict[str, int]`

Read `גרף התרעות וגם ממוצע לפי שעה`. Keep a label that has `HH:MM` and a whole average count, including a label that contains `ממוצע`. Store the count as an `int`. Return `{}` when no hour can be paired.

`read_hour_buckets()` remains the sum reader. It still drops `ממוצע` and fractional labels. It may use the tooltip step only when its current reads are empty.

## Tests

`tests/sanity/alerts_analysis_dashboard/test_data_validation.py`

All four stay `@pytest.mark.sanity`. Comments inside the functions are English. Dates still go through `to_page_date`.

| Test | Steps |
|------|--------|
| `test_hierarchy_nafa_matches_db` | Golden range, `set_hierarchy_level("nafa")`, `set_district_aggregation("sum")`, compare `read_district_labels()` to `alerts_by_hierarchy.nafa.sum`. Skip with `Missing page object method for hierarchy level nafa` when the level call is false or the map is empty. |
| `test_hierarchy_rashut_matches_db` | Same for `rashut` and `alerts_by_hierarchy.rashut.sum`. |
| `test_hierarchy_yeshuv_matches_db` | Same for `yeshuv` and `alerts_by_hierarchy.yeshuv.sum`. |
| `test_alerts_by_hour_daily_avg_matches_db` | Golden range, compare `read_hour_daily_avg()` to `alerts_by_hour.daily_avg`. Skip with `Missing page object method for hour daily_avg` when the map is empty. |

Every golden key must match. Extra UI keys are ignored. These four functions take `population_dashboard`.

## Unchanged

- `test_global_metrics_match_db`
- `test_filtered_population_matches_db`
- `test_alerted_population_by_settlement_matches_db`
- `test_hierarchy_mahoz_sum_matches_db`
- `test_hierarchy_mahoz_daily_avg_matches_db`
- `test_alerts_by_date_matches_db`
- `test_alerts_by_hour_sum_matches_db`
- `data/alerts/db_sanity_am_kalavi.yaml`
- `core/`
