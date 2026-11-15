# Phase 1 Data Model: Complete Alerts DB Sanity Validations

This slice adds tests, not storage. The "entities" are the golden-file shapes the new and
edited tests read, plus the derived partitions they compute. All values are read from
`data/alerts/db_sanity_am_kalavi.yaml`; nothing is persisted.

## Entity: Hierarchy daily average (Screen 2)

- **Source**: `dashboard_sanity_checks.screen_2_alerts_analysis.metrics.alerts_by_hierarchy.<level>.daily_avg`
  for `<level>` in `nafa`, `rashut`, `yeshuv`.
- **Shape**: mapping of Hebrew level-member name → whole-number per-day average.
- **Current golden values**:
  - `nafa.daily_avg`: `נפת חירם` → 1, `חטמ'ר צפונית - 7643` → 1
  - `rashut.daily_avg`: `גליל עליון` → 1, `מבואות החרמון` → 1, `רג'ר` → 1, `שער הנגב` → 1
  - `yeshuv.daily_avg`: `הגושרים`→1, `יובל`→1, `מעיין ברוך`→1, `בית הלל`→1, `דפנה`→1, `מלכייה`→1, `מנרה`→1, `נחל עוז`→1, `רג'ר`→1
- **UI read**: `read_district_labels()` after `set_hierarchy_level(<level>)` and
  `set_district_aggregation("average")` → mapping name → int.
- **Validation rule**: every golden key is present in the UI map with an equal value
  (`_assert_golden_keys`); extra UI keys are ignored. Empty UI map or unreachable level → skip.

## Entity: Top-10 ranking partition (Screen 1)

- **Source**: `dashboard_sanity_checks.screen_1_status_picture.metrics.top_10_settlements.values`.
- **Shape**: mapping of Hebrew settlement name → integer alert count.
- **Current golden values**: ראשון לציון 39, תל אביב-יפו 36, רמת השרון 35, נתניה 34, ראש העין 32,
  רמלה 32, יגל 31, גינתון 31, צפרייה 31, חיפה 31.
- **Derived partitions** (computed from the loaded map, not hard-coded):
  - **Tie value**: the single count shared by the lowest rows (currently `31`). Asserted to be one value.
  - **Stable set**: entries with count greater than the tie value (currently the six ≥ 32 rows).
  - **Golden tie names**: entries with count equal to the tie value (currently יגל, גינתון, צפרייה, חיפה).
- **UI read**: `read_top_10_settlements()` → mapping name → int.
- **Validation rules**:
  1. Each stable name is present in the UI map with its exact golden count.
  2. UI names outside the stable set equal the golden tie names as an unordered set, and each such
     UI count equals the tie value.
  3. Empty UI map → `pytest.skip("Missing Page Object reader for top_10_settlements")`.

## Entity: Alerts locator budget (both screens)

- **Owner**: `AlertsPopulationPage.timeout` and `StatusPicturePage.timeout`, set in each `__init__`
  together with `page.set_default_timeout` / `set_default_navigation_timeout`.
- **Change**: value rises from `60_000` to `120_000` ms (plan target).
- **Invariant**: `LoadTimeoutError` is still raised when the budget is exhausted; only the ceiling
  grows. No early progressive step is removed.

## Test inventory (after this slice)

| Module | Test | State | Golden key |
|--------|------|-------|-----------|
| `alerts_analysis_dashboard/test_data_validation.py` | `test_hierarchy_nafa_matches_db` | existing | `alerts_by_hierarchy.nafa.sum` |
| same | `test_hierarchy_rashut_matches_db` | existing | `alerts_by_hierarchy.rashut.sum` |
| same | `test_hierarchy_yeshuv_matches_db` | existing | `alerts_by_hierarchy.yeshuv.sum` |
| same | `test_hierarchy_nafa_daily_avg_matches_db` | **new** | `alerts_by_hierarchy.nafa.daily_avg` |
| same | `test_hierarchy_rashut_daily_avg_matches_db` | **new** | `alerts_by_hierarchy.rashut.daily_avg` |
| same | `test_hierarchy_yeshuv_daily_avg_matches_db` | **new** | `alerts_by_hierarchy.yeshuv.daily_avg` |
| `status_picture_dashboard/test_status_picture_validation.py` | `test_screen_1_top_settlements` | **edited** | `top_10_settlements.values` (stable + tie names) |
