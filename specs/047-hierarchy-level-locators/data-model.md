# Data Model: Fix Hierarchy Level Locators

This slice does not add stored fields and does not edit
`data/alerts/db_sanity_am_kalavi.yaml`. It defines the tab the page clicks and the level
state the readers already use.

## Hierarchy tab

A custom label drawn above the district chart, inside the report iframe.

| Field | Value |
|-------|--------|
| Level key | `nafa`, `rashut`, or `yeshuv` |
| Exact visible text | `נפה`, `רשות`, `יישוב` |
| Source of the text | `AlertsPopulationPage._HIERARCHY_LEVEL_NAMES` |
| Role | Unspecified. The locator does not require `button`, `tab`, or `option` |
| Placement | Above the district chart. The locator does not require the district visual container |

Validation: `set_hierarchy_level` accepts only `nafa`, `rashut`, and `yeshuv`. Any other
string returns false and clicks nothing.

## Hierarchy level (page state)

| Field | Before the click | After a successful click |
|-------|------------------|--------------------------|
| `_active_hierarchy_level` | `mahoz` | the requested key |
| District title | `התרעות לפי מחוז` | `התרעות לפי ` + the Hebrew name |
| Selection attribute | May be absent on the custom tab | Absence still counts as selected; the title wait confirms the grain |

Transition: `mahoz` → `nafa` | `rashut` | `yeshuv`. This slice does not click a `מחוז` tab
to return to the base level.

The title wait uses the existing `district_chart_title_for`. A title that does not become
visible within the page timeout makes `set_hierarchy_level` return false. The sanity
helper then fails.

## Golden hierarchy block (unchanged)

Root path in the alerts sanity YAML: `metrics.alerts_by_hierarchy`.

| Level key | Sum block | Daily-average block | Test helpers |
|-----------|-----------|---------------------|--------------|
| `nafa` | `.nafa.sum` | `.nafa.daily_avg` | `_assert_hierarchy_sum` / `_assert_hierarchy_daily_avg` |
| `rashut` | `.rashut.sum` | `.rashut.daily_avg` | same |
| `yeshuv` | `.yeshuv.sum` | `.yeshuv.daily_avg` | same |
| `mahoz` | `.mahoz.sum` | `.mahoz.daily_avg` | existing mahoz tests; no tab click |

Row comparison stays `_assert_golden_keys`. This slice does not change key folding or
numeric comparison.

## Skip and fail rules

| Condition | Result |
|-----------|--------|
| Tab text not actionable before the page timeout | Test error from Playwright `click()` |
| `set_hierarchy_level` returns false | Test failure asserted by the helper |
| Level selected and `read_district_labels()` is empty | Existing skip: `District chart returned no rows for level {level!r} (chart empty or not rendered)` |
| Level selected and rows are present | Golden comparison |
