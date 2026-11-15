# Contract: Top Settlement Tie Assertion

**Feature**: 036-top-settlement-ties | **Date**: 2026-10-19

The golden file stays. The page reader stays. Only the ranking test's comparison changes.

## Unchanged

- `data/alerts/db_sanity_am_kalavi.yaml`
- `pages/status_picture/status_picture_page.py` and `read_top_10_settlements()`
- `test_screen_1_global_metrics`
- `test_screen_1_filtered_metrics` (range cards only: warning zones under fire and alerted population)
- `test_screen_1_alerts_by_category`
- `core/`, `tests/conftest.py`, and `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`

## `test_screen_1_top_settlements`

Still `@pytest.mark.sanity`. Still calls `set_date_range` with the golden ISO dates converted to `DD/MM/YYYY`. Still calls `read_top_10_settlements()`.

Comments inside the function stay English.

1. If the UI map is empty, `pytest.skip("Missing Page Object reader for top_10_settlements")`.
2. Load `top_10_settlements.values`.
3. Stable set: entries with count `>= 32`. For each, assert `actual[name] == count`.
4. Tie count: the single value among golden entries with count `< 32`. On the current file that value is 31.
5. Tie slots: UI entries whose names are not in the stable set. Assert the slot count is 4 and every slot value equals the tie count.

Do not call `_assert_golden_entries` for this map. That helper still requires every golden key, including the tie names.

## Failure messages

The stable check names the settlement and shows the UI count beside the golden count.

The tie check names the actual remaining map when the length is not 4 or a value is not the tie count.
