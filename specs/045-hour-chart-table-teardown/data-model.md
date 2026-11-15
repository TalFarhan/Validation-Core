# Phase 1 Data Model: YAML-Only UI Blockers

This slice skips one SQL-backed test and changes two runtime locators on the alerts population
page. No persistent schema is added. Golden YAML and the alerts SQL contract are not edited.

## Skipped parity test (collection state)

| Field | Value |
|-------|--------|
| Node | `tests/ui/alerts_analysis_dashboard/test_db_parity.py::test_alerts_db_parity_last_30_days` |
| Marker | `db_parity`, plus `skip` |
| Skip reason | `Focusing strictly on YAML validation; DB checks temporarily disabled` |
| Fixture | `alerts_db` → `AlertsDBRunner` (not entered while the test is skipped) |
| SQL source | `data/alerts/alerts_contract.yaml` metrics whose `sql_query` reads `[FACT].[AlertsRedWeb]` |
| Body | Unchanged `validate_dashboard_generic(...)` call |

**Validation rule**: the decorator is the only behavioral change on this test. The contract
file and `db/clients/alerts.py` are not fields of this change.

**State**: collected as skipped. Removing the decorator returns the test to executed.

## YAML golden record — UNCHANGED, still executed

`tests/sanity/alerts_analysis_dashboard/test_data_validation.py` loads
`data/alerts/db_sanity_am_kalavi.yaml`. Those tests are not given a skip mark. Their
`*_matches_db` names are labels, not a SQL client.

Hierarchy maps consumed after `set_hierarchy_level`:

- `metrics.alerts_by_hierarchy.nafa.sum` / `nafa.daily_avg`
- `metrics.alerts_by_hierarchy.rashut.sum` / `rashut.daily_avg`
- `metrics.alerts_by_hierarchy.yeshuv.sum` / `yeshuv.daily_avg`

Hour maps consumed after the hour title can be anchored:

- `metrics.alerts_by_hour.sum`
- `metrics.alerts_by_hour.daily_avg`

**Validation rule**: this slice does not edit the file. Quote folding in `_assert_golden_keys`
stays.

## Hierarchy control (runtime)

| Field | Value |
|-------|--------|
| Method | `AlertsPopulationPage.set_hierarchy_level(level) -> bool` |
| Names | `nafa` → `נפה`, `rashut` → `רשות`, `yeshuv` → `יישוב` |
| Lookup | Visible `button`, `tab`, or `option` inside the district visual |
| Action | `click(force=True)` |
| Failure | Returns `False` when the control is missing or the retitled chart does not appear. Does not raise on a toolbar intercept. |

`set_district_aggregation` is a separate control (`סכום` / `ממוצע ליום`) and is not this entity.

## Hour-chart title anchor (runtime)

| Field | Value |
|-------|--------|
| Constant | `HOUR_CHART = "גרף התרעות וגם ממוצע לפי שעה"` |
| Finder | `_title_anchor` |
| Visible match | Preferred when Playwright reports one |
| Hidden match | Accepted only when an ancestor is `visualContainer` or `visual-container` |
| Rejected node | Hidden tooltip with no visual-container ancestor |
| Post-back wait | `_leave_visual_table`: attached, not `to_be_visible`, for this title only |

Other chart titles (`district_chart_title()`, `DATES_CHART`, `SETTLEMENT_CHART`) stay on a
visible text or visible group. `_SCREEN2_READY_ANCHOR` (`מרחק מהגבול`) stays a visible text
match and is not an hour-title field.

## Unit scan (source contract)

Three tests in `tests/unit/test_db_parity_engine.py` read the parity file as text.

| Assertion | After this slice |
|-----------|------------------|
| `"mark.skip" not in` parity source | Removed |
| `"pytest.skip" not in` parity source | Kept |
| `"importorskip" not in` parity source | Kept |

---

# Phase 1 Data Model: Screen 2 Page-Switch Click

This slice changes how `before_report_ready_check` clicks the Screen 2 tab. The ready phrase
stays `מרחק מהגבול`. The filtered-data wait, hour-column extraction, table teardown, and quote
folding are already in the code and stay. No persistent schema is added. Golden YAML is not
edited by this slice.

## Golden record (`data/alerts/db_sanity_am_kalavi.yaml`) — UNCHANGED

Loaded by `load_sanity_data()` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
under `dashboard_sanity_checks.screen_2_alerts_analysis`.

- **`date_range`** — `start: 2026-09-01`, `end: 2026-10-18`. Applied by `_apply_golden_range`
  through `set_date_range` before each read.
- **`metrics.alerted_population_selected_range.expected_value`** — `9474`. This is the
  range-sensitive warned card (`אוכלוסייה מותרעת`). Blank or `0` on that card means the filter
  has not finished for this file.
- **`metrics.total_population_all_time`** — `10142584`, still read through `read_card("total")`
  and `TOTAL_CARD` (`סה"כ אוכלוסייה`). Not the ready locator.
- **`metrics.unprotected_population`** — `3389879`, description `אוכלוסייה לא ממוגנת`. Still read
  through `read_card("unprotected")` and `UNPROTECTED_CARD`. Unique to Screen 2 in this file, and
  not the ready locator.
- **`metrics.alerts_by_hour.daily_avg`** — `HH:MM` → integer. Consumed by
  `test_alerts_by_hour_daily_avg_matches_db` through `read_hour_daily_avg()`.
- **`metrics.alerts_by_hour.sum`** — same hour keys, different counts for some hours. Consumed by
  `read_hour_buckets` (header `התרעות`, sum mode). Unchanged reader.
- **`metrics.alerts_by_hierarchy.nafa.sum` / `nafa.daily_avg`** — includes
  `חטמ'ר צפונית - 7643` (ASCII `'`). The UI label uses `חטמ"ר` (ASCII `"`). The file spelling
  stays. Comparison folds quotes in `_assert_golden_keys`.
- **`metrics.alerts_by_hierarchy.rashut` / `yeshuv`** — unchanged maps. Their tests fail in
  fixture setup when `navigate` never leaves Screen 1, so `מרחק מהגבול` stays absent until
  `LoadTimeoutError`. The maps themselves are not edited.

The distance filter `מרחק מהגבול` is not a field in this file. The locator change does not add
one.

**Validation rule**: this locator slice does not edit the file.

## Screen 2 ready anchor (runtime)

- **Owner**: `AlertsPopulationPage._report_ready_locator() -> Locator`.
- **Phrase**: `מרחק מהגבול`, the Screen 2 distance filter. Held by `_SCREEN2_READY_ANCHOR`, used
  only by this method. `_SCREEN2_READY_TITLE` is removed.
- **Match**: `self._report_frame().get_by_text(...).filter(visible=True).first`. Not
  `_iframe_phrase_locator`. Not `self.page`. Not an exact document title.
- **Not this anchor**: Screen 1 title `ניתוח התרעות | תמונת מצב ב [Filter]`; Screen 2 title
  `ניתוח התרעות | ניתוח התרעות`; the global header and side navigation text `ניתוח התרעות`;
  `PAGE_TITLE` (`ניתוח התרעות`), which stays the metric and chart scope; `TOTAL_CARD`
  (`סה"כ אוכלוסייה`); `UNPROTECTED_CARD` (`אוכלוסייה לא ממוגנת`); `סה"כ בטווח שנבחר`;
  `WARNED_CARD`.
- **Value independence**: any selected distance still shows the label. The ready check does not
  read the selected kilometers.
- **Page switch**: not this anchor. The hook below clicks the tab. The anchor is only the
  visibility check the hook and `navigate` share.
- **Wait**: existing `ReportShell.navigate` / `reload_and_measure_ready_ms` visibility wait.
  Timeout remains `AlertsPopulationPage.timeout` (`120_000`). Failure remains `LoadTimeoutError`
  from `navigate`, not from the hook.

## Screen 2 page tab (runtime)

- **Owner**: `AlertsPopulationPage.before_report_ready_check()`.
- **Rail**: visible page-navigation control named `ניווט בין עמודים` or `Page navigation`
  (`navigation`, `group`, or label) on `self._report_frame()`. Not `self.page`.
- **Tab**: first visible exact `PAGE_TITLE` (`ניתוח התרעות`) inside that rail, as `button`,
  `tab`, `link`, `option`, or exact text. This is the Screen 2 page. The same words outside
  the rail (header, Screen 1 title `ניתוח התרעות | תמונת מצב ב [Filter]`, side navigation) are
  not the tab.
- **Fallback**: when the inner exact-name locator matches nothing, the first visible rail
  control (Hebrew/English link, button, or label) is clicked instead.
- **Click**: `click(force=True)`, then `page.wait_for_timeout(400)`. No `no_wait_after`. No
  `networkidle`.
- **Success**: `_report_ready_locator()` is visible (`מרחק מהגבול`). The district chart title
  is not the success probe.
- **Retry**: the hook repeats the click while the anchor is absent, for at most about 8 seconds
  per call, then returns. `_page_switch_attempts >= 3` and the 12-second cooldown do not stop
  later calls. The next `navigate` poll calls the hook again. The suite gives up only when
  `navigate` raises `LoadTimeoutError` after `self.timeout`.
- **Relationship**: the tab is not a measure. `PAGE_TITLE` stays the metric and chart scope.
  The anchor phrase is not rewritten.
- **Relationship**: visibility only. It does not supply the integer for `read_card("total")`,
  `read_card("unprotected")`, or `read_card("warned")`.

## Filtered-data ready value (runtime)

- **Owner**: `set_date_range(start_date, end_date)`. Signature unchanged.
- **Card**: `WARNED_CARD` = `אוכלוסייה מותרעת` (`read_card("warned")`).
- **Not ready**: blank text, or a numeric value of `0` / `0.0`.
- **Ready**: any other number. For the golden range that number is `9474`.
- **Not a signal**: two equal reads of `TOTAL_CARD`, including a stable non-zero all-time total.
- **Mechanism**: Playwright `expect` (card visible, then poll until the value leaves blank and
  `0`). Timeout is `self.timeout`. Not `networkidle`.
- **Callers**: `_apply_golden_range` and any other `set_date_range` caller. They read charts only
  after this method returns.

## Hour daily-avg mapping (runtime) — unchanged

- **Producer**: `read_hour_daily_avg() -> dict[str, int]`.
- **Shape**: hour token `HH:MM` → whole-number count. Unchanged type.
- **Mode**: `_press_average_on_chart(self.HOUR_CHART)` selects `AVERAGE_MODE` (`ממוצע ליום`) on
  the hour chart before the read. The district toggle is not this control.
- **Source**: Show-as-a-table column header exact `התרעות`, then `_hour_keyed`.
- **Ignored**: `ממוצע` headers, series names containing `ממוצע`, aria/inner-text average labels,
  and any float rounding (`0.54` is not stored).
- **Failure mode**: `{}` when the alerts column has no integer hour rows, so the test's
  `pytest.skip` guard still fires.
- **Session**: the existing table session (below) closes the table before the method returns.

## Table session (runtime) — unchanged

A table session starts when `_click_show_as_table` returns and ends when `_leave_visual_table`
restores the canvas.

| Field | Rule |
|-------|------|
| `opened` | `True` immediately after a successful Show-as-a-table click |
| Back control | `חזרה לדוח` or `Back to report` |
| Exit | `finally` clicks Back whenever `opened` is true |
| Success | mapping returned, then Back |
| Empty / timeout / exception | mapping `{}` or raise, then Back |
| Menu never opened | `opened` stays false; Back is not clicked |

**Producers that own a session**: `_visual_table_map`, `read_date_counts`, `_dates_table_total`.

## Quote-folded key (comparison only) — unchanged

- **Owner**: `_assert_golden_keys(actual, expected, normalize=None)`.
- **Input key**: `str` from the UI dict or the golden dict.
- **Steps**: optional `normalize` (dates use `_normalize_date_key`), then `replace('"', "'")`.
- **Both sides**: actual keys and expected keys use the same fold before membership and equality.
- **Values**: unchanged. Integer counts still compare with `==`.
- **Example**: UI `חטמ"ר צפונית - 7643` and golden `חטמ'ר צפונית - 7643` share one folded key.
- **Non-example**: Hebrew geresh (U+05F3) and gershayim (U+05F4) are not folded.

## Unchanged readers

`read_hour_buckets` keeps header `התרעות` (sum) and its existing non-table paths.
`read_district_labels` keeps header `התרעות`.
`read_card("total")` keeps `TOTAL_CARD`.
`read_card("unprotected")` keeps `UNPROTECTED_CARD`.
`read_card("warned")` keeps `WARNED_CARD`. The date-range wait reads it; it does not change the
reader.
`read_date_counts` / `_dates_table_total` keep header `התרעות` and `DATES_CHART`.
`clear_filters` keeps its total-card settle loop. This slice does not change it.
Public names and return types are unchanged.
