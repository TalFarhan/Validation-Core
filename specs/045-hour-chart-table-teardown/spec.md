# Feature Specification: Fix Hour Chart Data Extraction and Ensure Safe Table Teardown

**Feature Branch**: `feature/reportportal-integration` (spec directory `045-hour-chart-table-teardown`; git checkout stays put)

**Created**: 2026-11-02

**Status**: Draft

**Input**: User description: "Fix Hour Chart Data Extraction and Ensure Safe Table Teardown. The test `test_alerts_by_hour_daily_avg_matches_db` skips because it attempts to parse the "ממוצע" (average) column which contains decimal values (e.g., 0.54), leading to an empty result. Furthermore, when this skip occurs, the "Show as a table" view is left open, causing subsequent tests (like `test_hierarchy_nafa_matches_db`) to fail with a Timeout. The goal is to always read from the "התרעות" column and ensure the table view is safely closed. (1) Fix Column Target for Average Mode: Update the data extraction logic in `population_page.py` (specifically for `read_hour_daily_avg` and its underlying parsers). When the chart is toggled to the daily average ("ממוצע ליום") mode and opened as a table, the code must extract the integer values from the "התרעות" column, NOT the "ממוצע" column. (2) Implement Safe Table Teardown: Wrap the entire "Show as a table" reading process in a `try...finally` block. You MUST guarantee that the "Back to report" ("חזרה לדוח" / "Back to report") button is clicked in the `finally` clause so the table is closed and the UI returns to the main dashboard state, regardless of whether the extraction succeeds, returns empty, or throws an exception. (3) Scope: Limit changes strictly to `pages/alerts_analysis/population_page.py`. Do not modify the golden YAML files or any other test files. (4) Code Standard: Ensure all in-code comments remain in English."

**Revised input (2026-11-03)**: Remaining Screen 2 failures, without touching `core/`. (1) In daily-average mode (`ממוצע ליום`), `read_hour_daily_avg` MUST read the `התרעות` column only. Do not use the `ממוצע` column and do not apply float rounding. (2) Golden nafa keys use a single quote (`חטמ'ר`) while the UI returns a double quote (`חטמ"ר`). `_assert_golden_keys` treats `'` and `"` as equal. (3) Comments inside functions stay English.

**Revised input (2026-11-03, ready title and slow render)**: This brief replaces any ready phrase that is a metric card. (1) `_report_ready_locator()` targets the main document title exactly: `ניתוח התרעות`. It does not wait on `סה"כ אוכלוסייה`, `סה"כ בטווח שנבחר`, or any other KPI card. (2) After a date filter is applied, the page waits until filtered data has finished rendering before a caller reads it. The wait is an `expect` condition on the main range KPI (`אוכלוסייה מותרעת`): the value must stop being `0` or blank. `networkidle` is not the wait. (3) `_assert_golden_keys` keeps `label.replace('"', "'")` so `'` and `"` match. (4) Comments inside functions stay English.

**Revised input (2026-11-03, exact Screen 2 title)**: This brief replaces the short ready phrase `ניתוח התרעות`. The metric cards stay flaky, and that short phrase is also the first clause of the Screen 1 title. (1) `_report_ready_locator()` waits for the exact Screen 2 document title `ניתוח התרעות | ניתוח התרעות`. Screen 1 is `ניתוח התרעות | תמונת מצב ב [Filter]` and must not satisfy the wait. (2) The locator does not call `_iframe_phrase_locator`, does not substring-match `PAGE_TITLE`, and does not fall back to `סה"כ אוכלוסייה`, `סה"כ בטווח שנבחר`, or any other metric card. (3) `PAGE_TITLE` stays `ניתוח התרעות` for metric and chart scope. (4) The only code edit is the ready-locator logic in `pages/alerts_analysis/population_page.py`. Golden YAML is already updated and is not edited again. (5) Comments inside functions stay English.

**Revised input (2026-11-03, unique Screen 2 anchor)**: This brief replaces the exact document title as the ready phrase. That title still contains `ניתוח התרעות`, and the same words are on Screen 1 (document title, global header, side navigation). A wait on them returns while the report is still on Screen 1, and the next Screen 2 interaction then raises `LoadTimeoutError`. (1) `_report_ready_locator()` waits for visible text `מרחק מהגבול`, the Screen 2 distance filter. That string is not on Screen 1. The unprotected card `אוכלוסייה לא ממוגנת` is also unique to Screen 2 and is not the ready phrase: it is a KPI title, and those titles are often images rather than text. (2) The locator is report-frame `get_by_text`, limited to a visible match. It does not use `self.page` (the report is in an iframe), does not call `_iframe_phrase_locator`, and does not match `ניתוח התרעות`, `PAGE_TITLE`, or `ניתוח התרעות | ניתוח התרעות`. (3) `PAGE_TITLE` stays `ניתוח התרעות` for metric and chart scope. `UNPROTECTED_CARD` stays the unprotected-population measure. (4) The ready-locator logic in `pages/alerts_analysis/population_page.py` stays on that filter. (5) Comments inside functions stay English.

**Revised input (2026-11-03, page-switch click)**: This brief does not change the ready phrase. `_report_ready_locator` already waits for `מרחק מהגבול`, and the test still raises `LoadTimeoutError` because the report never leaves Screen 1. `before_report_ready_check` clicks the page-navigation chrome and then stops after three attempts while that filter is still absent. (1) The hook clicks the Screen 2 tab inside the page-navigation control (`ניווט בין עמודים` / `Page navigation`): the inner button, tab, link, option, or exact text named `ניתוח התרעות`. The click uses `force=True`, then a short settle, then a check for `_SCREEN2_READY_ANCHOR`. An unscoped `ניתוח התרעות` match is not the target (that phrase is also the Screen 1 header and title). (2) Three clicks are not success. The hook does not keep a lifetime stop. It clicks again until `מרחק מהגבול` is visible or that call's short retry budget ends, and the next call tries again while the anchor is absent. `ReportShell.navigate` still owns `LoadTimeoutError`. (3) `_SCREEN2_READY_ANCHOR` stays `מרחק מהגבול`. `_report_ready_locator` is not edited. (4) The only code edit is `before_report_ready_check` (and a private helper it uses) in `pages/alerts_analysis/population_page.py`. (5) Comments inside functions stay English.

**Revised input (2026-11-03, YAML-only UI blockers)**: This brief does not reopen the page-switch, the ready phrase, the hour column, quote folding, or the date wait. UI-to-YAML sanity stays. Direct SQL checks for this dashboard are ignored for now. (1) `test_alerts_db_parity_last_30_days` in `tests/ui/alerts_analysis_dashboard/test_db_parity.py` is the alerts UI smoke test that runs contract SQL against `[FACT].[AlertsRedWeb]` through `alerts_db`. Mark it `@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")`. Do not skip the YAML sanity module. Its `*_matches_db` names load `data/alerts/db_sanity_am_kalavi.yaml` and do not open SQL. Do not edit that YAML, `alerts_contract.yaml`, or `db/clients/alerts.py`. Three unit assertions in `tests/unit/test_db_parity_engine.py` reject the substring `mark.skip` in the parity test file; those three lines are updated with the skip. `pytest.skip` and `importorskip` stay forbidden in that file. (2) `set_hierarchy_level` clicks `נפה` and `רשות` (and `יישוב`, the same method) with `control.click()`. The Power BI visual header toolbar intercepts that click. The click becomes `control.click(force=True)`. (3) The hour-chart title wait treats a Power BI title Playwright marks invisible as missing. `_title_anchor` and the post-back wait in `_leave_visual_table` drop `.filter(visible=True)` for `HOUR_CHART` only. Other chart titles keep the visible filter. The ready locator for `מרחק מהגבול` keeps its visible filter. (4) Comments inside functions stay English.

## Clarifications

### Session 2026-11-02

- Q: Why does `test_alerts_by_hour_daily_avg_matches_db` skip? → A: `read_hour_daily_avg` used to fall through to `_visual_table_map(self.HOUR_CHART, "ממוצע", contains=True)`. The table's `ממוצע` column holds decimals such as `0.54`. `_table_integer` accepts only whole numbers, so the grid is rejected and the reader returns `{}`.
- Q: Why do later tests time out after that skip? → A: Show-as-a-table was left open when the column lookup failed. `finally` now clicks Back once the table view is on screen. That teardown stays in place.
- Q: Which column is the source of truth in daily-average mode? → A: After the visual is in `ממוצע ליום` mode, the integer `התרעות` column is the golden mapping. The `ממוצע` column is ignored.
- Q: How must the table close? → A: Every Show-as-a-table read on this page wraps the open/read in `try...finally`. The `finally` clause clicks the bilingual Back control (`חזרה לדוח` / `Back to report`) whenever the table view was opened.

### Session 2026-11-03

- Q: Why do rashut/yeshuv tests crash in setup with `LoadTimeoutError`? → A: `ReportShell.navigate` waits on `AlertsPopulationPage._report_ready_locator()`. That locator targets `TOTAL_CARD` (`סה"כ אוכלוסייה`). The wait exhausts `self.timeout` (120s) on a metric card and raises `LoadTimeoutError`.
- Q: What is the ready anchor? → A: Superseded by the Screen 2 distance filter below. The short phrase `ניתוח התרעות` and the exact title `ניתוח התרעות | ניתוח התרעות` both contain words that are also on Screen 1. Neither is the ready locator.
- Q: Why does a title wait still attach to Screen 1? → A: `ניתוח התרעות` is in the global header, the side navigation, and both document titles (`ניתוח התרעות | תמונת מצב ב [Filter]` on Screen 1, `ניתוח התרעות | ניתוח התרעות` on Screen 2). The ready wait then succeeds on Screen 1, and the next Screen 2 click raises `LoadTimeoutError`. The anchor that is not on Screen 1 is the distance filter `מרחק מהגבול`.
- Q: Why not the unprotected card? → A: `אוכלוסייה לא ממוגנת` is unique to Screen 2, and it stays `UNPROTECTED_CARD` for `read_card("unprotected")`. It is not the ready phrase. KPI titles on this report are often images or buttons, so a text wait on a card is the same miss that spent 120s on `סה"כ אוכלוסייה`. The distance filter is a text label.
- Q: Does `TOTAL_CARD` change with the ready locator? → A: No. `read_card("total")` and `clear_filters` keep `סה"כ אוכלוסייה`. The distance filter is a visibility anchor only. It is not a measure.
- Q: Why do assertions see default 0 after a date filter? → A: `set_date_range` returns when the all-time total card is stable. That card is already non-zero while filtered visuals are still calculating and still show `0` or blank. After the dates are committed, wait until `אוכלוסייה מותרעת` is neither blank nor `0`.
- Q: Why can `read_hour_daily_avg` still miss the alerts column? → A: The table fallback already passes header `התרעות`, but the method returns earlier from `_hour_average` (aria and inner text) and from the chart series whose name contains `ממוצע`. `_hour_average` parses a float and keeps it only when `float.is_integer()`, which is float rounding of a whole decimal. Those paths are removed. After `ממוצע ליום` is selected, the only value source is the `התרעות` column.
- Q: Why do nafa keys fail when the counts match? → A: `data/alerts/db_sanity_am_kalavi.yaml` stores `חטמ'ר צפונית - 7643` (ASCII `'`). The UI returns `חטמ"ר צפונית - 7643` (ASCII `"`). Fold `"` to `'` on both sides with `label.replace('"', "'")`. Do not edit the YAML and do not change values.
- Q: Which files may change? → A: This page-switch revision edits `before_report_ready_check` in `pages/alerts_analysis/population_page.py` only. `_report_ready_locator`, `_assert_golden_keys`, golden YAML, `core/`, fleet, status-picture, and credit stay untouched. In-function comments stay English.
- Q: Why does setup still raise `LoadTimeoutError` after the ready locator is `מרחק מהגבול`? → A: The locator is correct and does not match Screen 1. `before_report_ready_check` never lands the page change. It clicks the page-rail chrome (`ניווט בין עמודים`), counts that click, and returns for good after three attempts (`_page_switch_attempts >= 3`) and during a 12-second cooldown. `navigate` then waits on the distance filter until `self.timeout` and raises `LoadTimeoutError`.
- Q: What must the click hit? → A: The Screen 2 page tab inside the page-navigation visual. The tab name is `ניתוח התרעות` (`PAGE_TITLE`). Power BI often ignores a click on the rail container. The hook uses `click(force=True)` on the inner button, tab, link, option, or exact text, then waits briefly and checks `_SCREEN2_READY_ANCHOR`. It does not click an unscoped `ניתוח התרעות` node in the header or Screen 1 title.
- Q: When may the hook stop clicking? → A: When `_report_ready_locator()` (`מרחק מהגבול`) is visible, or when that call's short retry budget ends. A count of three is not success. The attempt counter must not suppress later calls. `navigate` still raises `LoadTimeoutError` if the anchor is absent after `self.timeout`. The hook does not block for the full `120_000` on every call, because `_dashboard_ready` and `reload_and_measure_ready_ms` invoke it on short polls.

### Session 2026-11-03 (YAML-only UI blockers)

- Q: Which test queries `[FACT].[AlertsRedWeb]`? → A: `tests/ui/alerts_analysis_dashboard/test_db_parity.py::test_alerts_db_parity_last_30_days`. It passes `alerts_db` into `validate_dashboard_generic` with `data/alerts/alerts_contract.yaml`. That file's confirmed KPIs `SELECT` from `[FACT].[AlertsRedWeb]`. The YAML sanity module loads `db_sanity_am_kalavi.yaml` and does not open a connection. Skip only the parity test.
- Q: Can the parity file gain `@pytest.mark.skip` as written? → A: Not until three scans in `tests/unit/test_db_parity_engine.py` (`test_remaining_visuals_use_stub_sql`, `test_alerts_stubs_do_not_hide_connection_errors`, `test_population_page_stubs`) stop asserting `"mark.skip" not in` that file. `@pytest.mark.skip` does not contain the substrings `pytest.skip` or `importorskip`. Those two bans stay.
- Q: Where is the hierarchy click that the toolbar intercepts? → A: `AlertsPopulationPage.set_hierarchy_level` calls `control.click()` after `_hierarchy_control` finds a visible button, tab, or option named `נפה`, `רשות`, or `יישוב`. One `click(force=True)` covers all three. The lookup stays visible. `set_district_aggregation` is a different click and is not this change.
- Q: Where does the hour title require visibility? → A: `_title_anchor` uses `get_by_text(title).filter(visible=True)` and then a visible group, and raises `Chart {title!r} title is not visible`. `_leave_visual_table` then does `expect(...filter(visible=True).first).to_be_visible` for the same title after Back. Both drop the visible filter only when `title == HOUR_CHART`. A hidden tooltip that is not inside a visual container is not the anchor.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hour daily averages come from the alerts column (Priority: P1)

A validation author runs `test_alerts_by_hour_daily_avg_matches_db`. The hour chart is in daily-average mode (`ממוצע ליום`). The reader maps each hour to the integer in the `התרעות` column and returns a non-empty `HH:MM` → count mapping that matches `alerts_by_hour.daily_avg`. It does not read the `ממוצע` column and does not round floats.

**Why this priority**: Decimal `ממוצע` cells and float-to-int rounding produce the wrong series or an empty map, so the hour daily-avg assertion never checks the golden integers.

**Independent Test**: With the golden date range applied, `read_hour_daily_avg()` returns the golden hour keys as integers taken from the `התרעות` column. The test reports pass/fail instead of skip when data is present.

**Acceptance Scenarios**:

1. **Given** the hour chart is in `ממוצע ליום` mode and opened as a table, **When** `read_hour_daily_avg` extracts rows, **Then** values come from the `התרעות` column and not from any `ממוצע` header or series.
2. **Given** a `ממוצע` cell such as `0.54`, **When** the reader runs, **Then** that cell is not parsed, not rounded, and not stored as a bucket value.
3. **Given** integer `התרעות` cells for hours present in the golden record, **When** the reader finishes, **Then** it returns a non-empty `dict[str, int]` keyed as `HH:MM`.

---

### User Story 2 - Show-as-a-table always returns to the canvas (Priority: P1)

A validation author runs the alerts sanity module. Any Show-as-a-table read — success, empty mapping, timeout, or exception — clicks `חזרה לדוח` / `Back to report` before the method returns, so the next test finds the district/hour canvas instead of a leftover table.

**Why this priority**: A leftover table turns one hour-chart miss into `Timeout` failures on the hierarchy family. This behavior is already implemented and MUST stay.

**Independent Test**: Force the table path to return `{}` or raise. After the call, the named visual is visible on the canvas again.

**Acceptance Scenarios**:

1. **Given** Show-as-a-table opened and the alerts column parsed successfully, **When** the reader returns, **Then** Back to report has been clicked and the calling visual is visible.
2. **Given** Show-as-a-table opened and extraction returns empty or raises, **When** the method exits, **Then** the `finally` clause still clicks Back to report.
3. **Given** Power BI renders the English name `Back to report`, **When** teardown runs, **Then** that button is clicked (the Hebrew `חזרה לדוח` still matches when Hebrew is rendered).

---

### User Story 3 - Screen 2 becomes ready on its distance filter (Priority: P1)

A validation author runs `test_hierarchy_rashut_matches_db` or `test_hierarchy_yeshuv_matches_db`. Fixture setup calls `navigate`, which waits on `_report_ready_locator()`. The locator matches the visible Screen 2 filter `מרחק מהגבול`. Setup does not treat Screen 1 as ready because the header, the side navigation, or either document title contains `ניתוח התרעות`, and it does not raise `LoadTimeoutError` on the next Screen 2 interaction.

**Why this priority**: A shared ready phrase marks Screen 1 as ready. The following Screen 2 action then times out before any hierarchy assertion runs.

**Independent Test**: `AlertsPopulationPage._report_ready_locator()` is visible text `מרחק מהגבול` inside the report frame. It is not built from `PAGE_TITLE`, `_iframe_phrase_locator`, `ניתוח התרעות | ניתוח התרעות`, `סה"כ אוכלוסייה`, or `אוכלוסייה לא ממוגנת`. Opening the population page reaches that filter.

**Acceptance Scenarios**:

1. **Given** the Screen 2 filter `מרחק מהגבול` is visible, **When** `navigate` waits for the ready locator, **Then** the wait succeeds inside the existing timeout.
2. **Given** Screen 1 is showing, and its header or title contains `ניתוח התרעות`, **When** the population page checks ready, **Then** that text does not satisfy the locator.
3. **Given** the metric card `סה"כ אוכלוסייה` or `אוכלוסייה לא ממוגנת` is slow or absent, **When** setup runs, **Then** the ready locator does not wait on either card.
4. **Given** Screen 1 is showing and the page-navigation tab `ניתוח התרעות` is inside `ניווט בין עמודים`, **When** `before_report_ready_check` runs, **Then** it force-clicks that inner tab and does not treat three clicks as done while `מרחק מהגבול` is absent.

---

### User Story 4 - Nafa acronym quotes compare equal (Priority: P1)

A validation author runs `test_hierarchy_nafa_matches_db`. The UI label `חטמ"ר צפונית - 7643` matches the golden key `חטמ'ר צפונית - 7643`. Counts are still compared exactly.

**Why this priority**: The hierarchy assertion fails on the quote character even when the district and the count are the same.

**Independent Test**: `_assert_golden_keys` treats a key that differs only by `'` versus `"` as the same key. A real missing district still fails. Golden YAML bytes are unchanged.

**Acceptance Scenarios**:

1. **Given** the UI key uses `"` and the golden key uses `'`, **When** `_assert_golden_keys` runs, **Then** the keys match and the integer values are compared.
2. **Given** a golden key that is absent even after quote folding, **When** the helper runs, **Then** the assertion fails with the missing key.
3. **Given** two keys that differ by more than quotes, **When** the helper runs, **Then** they stay distinct.

---

### User Story 5 - Date filters wait until filtered data leaves zero (Priority: P1)

A validation author applies the golden date range. `set_date_range` does not return while the main range KPI (`אוכלוסייה מותרעת`) is blank or `0`. Readers that run after it see calculated filtered values, not the default zero state.

**Why this priority**: Assertions that run during calculation compare golden counts to `0` and fail even when the filter is correct.

**Independent Test**: After `set_date_range` returns for the golden range, `read_card("warned")` is not `0` and not blank.

**Acceptance Scenarios**:

1. **Given** dates were just committed and `אוכלוסייה מותרעת` still shows `0` or blank, **When** `set_date_range` is waiting, **Then** it does not return yet.
2. **Given** that card then shows a non-zero value, **When** the wait condition passes, **Then** `set_date_range` returns and callers may read charts.
3. **Given** the all-time total card is already stable and non-zero, **When** the warned card is still `0`, **Then** the date-range wait continues.

---

### Edge Cases

- `_alert_column_table` timing out while looking for integers must still close the table (`opened` is true as soon as the table view is on screen).
- `read_date_counts` and `_dates_table_total` keep the same `try...finally` guarantee.
- A Show-as-a-table menu click that never succeeds does not click Back (no table was opened).
- A genuinely empty hour chart still returns `{}` so the existing `pytest.skip` guard can fire; teardown still runs if a table was opened.
- Decimal `ממוצע` labels on SVG/aria paths are not a substitute for the `התרעות` column. `read_hour_daily_avg` does not call them.
- `_hour_average` float-then-`int` is not used. A value such as `0.54` is never rounded to `1` or `0`.
- Quote folding applies to keys only. Values are not rewritten. `"` becomes `'` on both the UI key and the golden key before lookup.
- An optional key normalizer (dates) runs first; quote folding runs on that result.
- `TOTAL_CARD` (`סה"כ אוכלוסייה`) stays the measure title for `read_card("total")`. `UNPROTECTED_CARD` (`אוכלוסייה לא ממוגנת`) stays the measure title for `read_card("unprotected")`. The ready phrase is the Screen 2 filter `מרחק מהגבול`, not either card and not `PAGE_TITLE`.
- Screen 1's title, header, and side navigation contain `ניתוח התרעות`. Screen 2's title `ניתוח התרעות | ניתוח התרעות` contains the same words. None of those strings is a Screen 2 ready match.
- Two equal reads of the all-time total, including a stable non-zero total, are not proof that filtered charts have finished. A warned-card value of `0` or blank keeps the date-range wait going.
- The golden selected-range warned population is `9474`, so `0` on that card means the filter has not finished for this suite.
- Comments inside new or edited functions are English.
- Three page-rail clicks are not proof that Screen 2 opened. The hook keeps clicking while `מרחק מהגבול` is absent, until the call's short budget ends, and the next call tries again.
- A click on the page-navigation container, or on `ניתוח התרעות` outside that container, does not count as the Screen 2 tab click.
- The district chart title is not the signal that Screen 2 is open. The distance filter is.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When `read_hour_daily_avg` reads the hour chart in daily-average (`ממוצע ליום`) mode, it MUST extract integer values from the `התרעות` column. It MUST NOT target a `ממוצע` column header, a series whose name contains `ממוצע`, or any aria/inner-text parser that looks for `ממוצע`.
- **FR-002**: `read_hour_daily_avg` MUST put the visual into `ממוצע ליום` mode before that table read. The sanity test MUST NOT grow a new aggregation toggle.
- **FR-003**: `read_hour_daily_avg` MUST NOT parse decimals or apply float rounding. `_hour_average` (float parse, then `int` when `is_integer()`) MUST NOT be on this path. `_table_integer` stays whole-number only. A cell such as `0.54` MUST NOT become a bucket value.
- **FR-004**: Every Show-as-a-table read on `AlertsPopulationPage` (`_visual_table_map`, `read_date_counts`, `_dates_table_total`) MUST keep the open-and-read work in `try...finally`.
- **FR-005**: The `finally` clause MUST click the bilingual Back control (`חזרה לדוח` / `Back to report`) whenever the table view was opened, whether extraction succeeded, returned empty, or raised.
- **FR-006**: `_leave_visual_table` MUST keep resolving Back via a bilingual locator over `חזרה לדוח` and `Back to report`, then wait until the calling visual is back on the canvas. For every title except `HOUR_CHART`, that wait stays a visible title. `HOUR_CHART` follows FR-016.
- **FR-007**: This page-switch revision MUST edit only `before_report_ready_check` in `pages/alerts_analysis/population_page.py` (a private helper used only by that hook is allowed). It MUST NOT modify `_report_ready_locator`, `_assert_golden_keys`, golden YAML, `core/`, fleet, status-picture, or credit modules.
- **FR-008**: Public reader names and return types (`read_hour_daily_avg`, `read_hour_buckets`, `read_date_counts`, `read_district_labels`, and the other existing population readers) MUST stay the same.
- **FR-009**: Comments inside new or edited functions MUST be English.
- **FR-010**: `_report_ready_locator` MUST target the visible Screen 2 filter label `מרחק מהגבול` on the report frame (`get_by_text`, then a visible match, then `.first`). It MUST NOT search `self.page` (the report is inside the iframe). It MUST NOT call `_iframe_phrase_locator`. It MUST NOT match `ניתוח התרעות`, `PAGE_TITLE`, `ניתוח התרעות | ניתוח התרעות`, Screen 1's title `ניתוח התרעות | תמונת מצב ב [Filter]`, `סה"כ אוכלוסייה`, `סה"כ בטווח שנבחר`, or `אוכלוסייה לא ממוגנת`. `PAGE_TITLE` stays the metric and chart scope. `UNPROTECTED_CARD` stays the unprotected-population measure. The selected distance value MUST NOT matter; the filter label is enough.
- **FR-011**: `_assert_golden_keys` MUST treat ASCII `"` and ASCII `'` as the same character in keys (fold `"` to `'` on the UI key and the golden key via `replace('"', "'")`). Values MUST stay exact. The golden YAML file MUST NOT be edited.
- **FR-012**: After `set_date_range` commits the start and end dates, it MUST wait until the warned-population card (`אוכלוסייה מותרעת`) is neither blank nor `0` before returning. A stable all-time total MUST NOT end that wait. The wait MUST NOT be `networkidle`.
- **FR-013**: `before_report_ready_check` MUST force-click the Screen 2 tab inside the page-navigation control (`ניווט בין עמודים` / `Page navigation`). The tab is the inner button, tab, link, option, or exact text named `ניתוח התרעות` (`PAGE_TITLE`). The click MUST use `force=True`, then a short settle, then a visibility check of `_SCREEN2_READY_ANCHOR` via `_report_ready_locator`. Three clicks MUST NOT be treated as success. A lifetime attempt counter MUST NOT suppress later clicks while `מרחק מהגבול` is absent. The hook MUST NOT search `self.page` and MUST NOT click an unscoped `ניתוח התרעות` node. It MUST NOT change `_SCREEN2_READY_ANCHOR` or `_report_ready_locator`. It MUST NOT raise `LoadTimeoutError`; `ReportShell.navigate` still does. One call MUST NOT block for the full `self.timeout`, because short probes call this hook. Comments inside the function MUST be English.
- **FR-014**: `test_alerts_db_parity_last_30_days` MUST be skipped with `@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")`. The YAML sanity module MUST keep running. Golden YAML, `data/alerts/alerts_contract.yaml`, and `db/clients/alerts.py` MUST NOT be edited. The three `assert "mark.skip" not in` scans of that parity file in `tests/unit/test_db_parity_engine.py` MUST be updated so the decorator is allowed. Those scans MUST still reject `pytest.skip` and `importorskip`.
- **FR-015**: `set_hierarchy_level` MUST click the district drill-down control (`נפה`, `רשות`, and `יישוב` on the same method) with `click(force=True)` so the visual header toolbar does not intercept the pointer. The control lookup MAY still require a visible role match. The method's return type stays `bool`.
- **FR-016**: For `HOUR_CHART` only (`גרף התרעות וגם ממוצע לפי שעה`), `_title_anchor` and the canvas-return wait in `_leave_visual_table` MUST NOT require `.filter(visible=True)`. A title Playwright treats as hidden still anchors the visual when it is attached inside a visual container. Other chart titles keep `.filter(visible=True)`. `_report_ready_locator` keeps its visible filter on `מרחק מהגבול`.

### Key Entities

- **Hour daily-avg mapping**: `dict[str, int]` of `HH:MM` → integer count produced by `read_hour_daily_avg` from the `התרעות` column, compared to `alerts_by_hour.daily_avg`.
- **Alerts column**: The Show-as-a-table header `התרעות`. Sole value source for `read_hour_daily_avg` after `ממוצע ליום` is selected.
- **Average column**: The Show-as-a-table header `ממוצע` (decimals). Out of scope as a value source. Not rounded.
- **Table session**: The interval after a successful Show-as-a-table click and before Back to report restores the canvas.
- **Screen 2 ready anchor**: The visible filter label `מרחק מהגבול` waited on by `_report_ready_locator`. It is not on Screen 1. Distinct from both document titles, from `PAGE_TITLE`, from `TOTAL_CARD`, and from `UNPROTECTED_CARD`. This revision does not change it.
- **Screen 2 page tab**: The inner control named `ניתוח התרעות` inside the page-navigation visual `ניווט בין עמודים` / `Page navigation`. `before_report_ready_check` force-clicks it. It is not the unscoped header or Screen 1 title, and it is not a measure.
- **Filtered-data ready value**: The warned-population card `אוכלוסייה מותרעת` after a date range. Blank and `0` mean the filter has not finished. A non-zero value means `set_date_range` may return.
- **Quote-folded key**: A golden or UI label after `"` is replaced with `'`, used only for key membership. Example: `חטמ"ר צפונית - 7643` and `חטמ'ר צפונית - 7643`.
- **Skipped alerts parity test**: `test_alerts_db_parity_last_30_days`. It is the only alerts UI test that executes `[FACT].[AlertsRedWeb]` SQL. This slice skips it. The SQL client and the contract file stay.
- **Hierarchy drill-down control**: The button, tab, or option named `נפה`, `רשות`, or `יישוב` inside the district visual. `set_hierarchy_level` force-clicks it.
- **Hour-chart title anchor**: The node named `גרף התרעות וגם ממוצע לפי שעה` used to find that visual. For this title, attached inside a visual container is enough. Playwright visibility is not required.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` are NOT edited. Show-as-a-table and the ready phrase stay on the domain page (Constitution VII).
- **AC-002**: `AlertsPopulationPage` keeps inheriting `AlertsAnalysisPage` → `ReportShell`. No portal step is added or removed. The Screen 2 ready locator, the page-switch hook, and the post-filter wait stay on this page.
- **AC-003**: Public test-facing APIs keep their names and return types. Quote folding inside `_assert_golden_keys` stays. This slice's test edits are the parity skip and the three unit scans in AC-007.
- **AC-004**: `core/` does not load `data/alerts/`. The existing sanity tests keep loading the golden file.
- **AC-005**: No new report page and no SQL client change.
- **AC-006**: The page-switch revision edits `before_report_ready_check` in `pages/alerts_analysis/population_page.py` (a private helper used only by that hook is part of the same edit). `_report_ready_locator` and `_SCREEN2_READY_ANCHOR` stay. `_assert_golden_keys` is already folded and stays. Golden YAML is not edited again.
- **AC-007**: This YAML-only slice edits `set_hierarchy_level`, `_title_anchor`, and the hour-chart branch of `_leave_visual_table` in `pages/alerts_analysis/population_page.py`; adds the skip on `tests/ui/alerts_analysis_dashboard/test_db_parity.py`; and updates the three `mark.skip` scans in `tests/unit/test_db_parity_engine.py`. It does not edit YAML, `core/`, the SQL client, or the alerts contract.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `read_hour_daily_avg()` returns a non-empty hour→integer mapping from the `התרעות` column while the chart is in `ממוצע ליום` mode, with no `ממוצע` read and no float rounding, so `test_alerts_by_hour_daily_avg_matches_db` can reach its assertion when data is present.
- **SC-002**: After any Show-as-a-table read on this page object, the canvas visual is visible again.
- **SC-003**: `test_alerts_by_hour_daily_avg_matches_db` matches `data/alerts/db_sanity_am_kalavi.yaml` `alerts_by_hour.daily_avg` without a YAML edit.
- **SC-004**: Rashut and yeshuv sanity setup reaches Screen 2. The ready locator stays the visible filter `מרחק מהגבול`. `before_report_ready_check` force-clicks the inner `ניתוח התרעות` tab and keeps trying while that filter is absent, so setup does not spend `self.timeout` on Screen 1 after three rail clicks. Alerts UI smoke still opens the population page. Fleet smoke is not the gate (`core/` and the fleet page are not edited).
- **SC-005**: `test_hierarchy_nafa_matches_db` treats `חטמ'ר` and `חטמ"ר` as the same key. This revision does not edit the test file or the golden YAML.
- **SC-006**: `read_card("total")` still addresses `סה"כ אוכלוסייה`.
- **SC-007**: For the golden date range, `set_date_range` returns only after `read_card("warned")` is neither blank nor `0`, so later assertions are not comparing golden counts to the default zero state.
- **SC-008**: `pytest tests/ui/alerts_analysis_dashboard/` skips `test_alerts_db_parity_last_30_days` and does not open `[FACT].[AlertsRedWeb]`. The YAML sanity module is still collected and still reads `db_sanity_am_kalavi.yaml`.
- **SC-009**: A toolbar covering `נפה` or `רשות` does not fail `set_hierarchy_level`. The click uses `force=True`.
- **SC-010**: An hour-chart title Playwright marks invisible still yields a visual container, and the post-back wait for that title does not require `visible=True`. Other chart titles and `מרחק מהגבול` still require a visible match.

## Assumptions

- `read_hour_daily_avg` already presses `ממוצע ליום` on the hour chart itself (`_press_average_on_chart`). The district `set_district_aggregation` control does not change that chart. This slice leaves that path in place.
- In `ממוצע ליום` mode the `התרעות` column holds the integer daily averages that match the golden `daily_avg` map.
- The Show-as-a-table teardown from the 2026-11-02 slice is already in `population_page.py` and remains correct.
- The Screen 2 distance filter `מרחק מהגבול` is visible once the report is on Screen 2, for any selected distance. It is not rendered on Screen 1. Screen 1's title is `ניתוח התרעות | תמונת מצב ב [Filter]`. Screen 2's title is `ניתוח התרעות | ניתוח התרעות`. Both contain `ניתוח התרעות`, which is also in the global header and side navigation. The page tab to click is that same name scoped inside `ניווט בין עמודים` / `Page navigation`. The district chart is not the switch signal. The ready locator itself is the distance filter, not a card and not `PAGE_TITLE`.
- `סה"כ בטווח שנבחר` is a Screen 1 card. `אוכלוסייה לא ממוגנת` is a Screen 2 card and stays a measure. Neither is the ready phrase.
- `PAGE_TITLE` (`ניתוח התרעות`) remains the scope string for card and chart reads. Changing it would retarget those readers. The ready locator does not use it.
- The golden `alerted_population_selected_range` is `9474`. On this suite, `0` or blank on `אוכלוסייה מותרעת` means the date filter is still calculating.
- The nafa mismatch is ASCII apostrophe versus ASCII quotation mark, not a different district name. Hebrew geresh (U+05F3) and gershayim (U+05F4) are not part of this fold.
- Portal auth is required to run the UI/sanity tests; this spec does not run the browser.
- Git checkout stays on `feature/reportportal-integration`. `.specify/feature.json` stays pointed at `specs/045-hour-chart-table-teardown`.
