# Contract: Hierarchy Level Tabs

**Feature**: `047-hierarchy-level-locators` | **Date**: 2026-11-04

The district grain controls are custom labels above the district chart. This contract
covers how `AlertsPopulationPage` clicks them and how the YAML sanity helpers treat a
miss. `core/`, the golden YAML, and other reports stay unchanged.

## Page

`pages/alerts_analysis/population_page.py`

Class `AlertsPopulationPage`. Existing inheritance stays.

| Rule | Value |
|------|--------|
| Level names | `_HIERARCHY_LEVEL_NAMES`: `nafa` → `נפה`, `rashut` → `רשות`, `yeshuv` → `יישוב` |
| Frame | `_report_frame()` (the Power BI iframe) |
| Locator | `get_by_text(label, exact=True)` |
| Click | `locator.first.click()` with Playwright's actionability wait |
| Timeout | The page's existing `self.timeout` (120 seconds) |

### `_hierarchy_control(self, label: str) -> Locator`

Returns the exact-text locator in the report iframe. Always returns a locator. Does not
return `None` when the node is missing, does not filter by role, and does not search
inside `_visual_container`.

### `set_hierarchy_level(self, level: str) -> bool`

Signature stays.

1. `level` outside `nafa` / `rashut` / `yeshuv` returns false. No click.
2. Resolve the Hebrew label and the text locator.
3. Dismiss the overlay, then `click()` the first match. Do not `count()` first. Do not
   pass `force=True`. Let a timeout propagate.
4. Keep `_wait_for_level_selection`. A tab with neither `aria-pressed` nor
   `aria-selected` is treated as selected.
5. Wait until `התרעות לפי ` plus the level name is visible. If that wait fails, return
   false.
6. On success, set `_active_hierarchy_level` and return true.

Comments inside the function are English.

`set_district_aggregation` is a different control and stays as it is.

## Sanity helpers

`tests/sanity/alerts_analysis_dashboard/test_data_validation.py`

`_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg`:

| Step | Behavior |
|------|----------|
| Select level | Call `set_hierarchy_level(level)` |
| False return | `assert` the return. The message may name the level. This is a failure |
| Control-not-visible skip | Removed. The reason string `control not visible on district chart` is gone from both helpers |
| Aggregation | Unchanged: `"sum"` or `"average"` |
| Empty read | Unchanged skip: `District chart returned no rows for level {level!r} (chart empty or not rendered)` |
| Rows present | Unchanged `_assert_golden_keys` against the golden block for that level |

The six tests `test_hierarchy_{nafa,rashut,yeshuv}_matches_db` and
`test_hierarchy_{nafa,rashut,yeshuv}_daily_avg_matches_db` keep their names and keep
calling these helpers. The two `מחוז` tests do not call `set_hierarchy_level`.

## Out of scope

- `data/alerts/db_sanity_am_kalavi.yaml`
- `core/portal/` and `core/components/`
- `db/clients/alerts.py` and `data/alerts/alerts_contract.yaml`
- Fleet, status-picture, and credit pages and tests
- A `מחוז` tab click
