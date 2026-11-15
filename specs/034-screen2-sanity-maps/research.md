# Phase 0 Research: Screen 2 Sanity Maps

**Feature**: 034-screen2-sanity-maps | **Date**: 2026-10-19

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Pin a new spec directory

**Decision**: Plan this work as `specs/034-screen2-sanity-maps`. `.specify/feature.json` now points there. The git checkout stays `feature/reportportal-integration`.

**Rationale**: `033-population-sanity-tests` is the finished card slice. Its spec says settlement, hierarchy, dates, and hours are out of that slice. This request is that next slice. Overwriting 033 would erase the card plan.

**Alternatives considered**:

- *Append this design to `033-population-sanity-tests`*: rejected. That directory's tasks are already complete for the three card assertions.

## Decision 2 — Leave the two card tests in place

**Decision**: Do not edit the bodies of `test_global_metrics_match_db` or `test_filtered_population_matches_db`. New tests call `load_sanity_data` and `to_page_date` themselves.

**Rationale**: Those two tests passed against the live dashboard. The request says not to break them. Sharing a new setup helper would rewrite working functions for no change in behavior.

**Alternatives considered**:

- *Extract one `apply_golden_range` helper and switch the filtered card test over to it*: rejected. That edits a passing test.

## Decision 3 — Read settlements with the existing `Chart.read`

**Decision**: The settlement test constructs `Chart` the way `test_settlement_series_match_legend` does: `Chart(page=page.page, frame=page._report_frame(), timeout_ms=page.timeout)` and `chart.read(page.SETTLEMENT_CHART, scope=page.PAGE_TITLE)`. The warned value is the series whose name is `page.WARNED_SERIES`.

**Rationale**: `chart_total` only returns a sum. `Chart.read` already returns `ChartCategory` rows with a label and per-series values, and the invariant test already uses it for this chart. No new settlement method is required, so this test does not skip.

**Alternatives considered**:

- *Add `read_settlement_population` on the page*: rejected. The reader already exists on `Chart`.
- *Compare `chart_total(SETTLEMENT_CHART, 0)` to the sum of the golden values*: rejected. The golden section is a name-to-value map, not one total.

## Decision 4 — Treat the district chart as מחוז, and skip the other levels

**Decision**: `alerts_by_hierarchy.mahoz` is read from `DISTRICT_CHART` (`התרעות לפי מחוז`) after `set_district_aggregation("sum")` or `set_district_aggregation("average")`. `nafa`, `rashut`, and `yeshuv` each have one test that only calls `pytest.skip("Missing page object method for hierarchy level <level>")`.

**Rationale**: The page has Sum (`סכום`) and daily average (`ממוצע ליום`) for the district chart. It has no method that selects נפה, רשות, or יישוב. Feature 019 recorded that this page does not drill the hierarchy. A guessed click could change the chart the other tests read. The request allows a skip when the method is missing.

**Alternatives considered**:

- *Click buttons named נפה, רשות, and יישוב*: rejected. Those controls are not on the page object, and this slice has no evidence they are the drill.
- *Fail the three levels*: rejected. The request says a missing method must not fail the suite.

## Decision 5 — Add `read_district_labels` without changing `chart_total`

**Decision**: Add `read_district_labels()` on `AlertsPopulationPage`. It walks the same visible district rows `_sum_visible_district_rows` already uses and returns `{row header: alerts integer}`. It does not scroll. `chart_total(DISTRICT_CHART)` still returns the settled visible total.

**Rationale**: `chart_total` and `set_district_aggregation` cannot return a name. The row payload already has the row header and the alerts cell. A labeled map is the basic reader this metric lacks. An empty map means the מחוז test skips with `Missing page object method for district labels`.

**Alternatives considered**:

- *Use `Chart.read` for the district chart*: rejected. Later slices stopped using that path for the district total because the visible-row reader is the one that matches the page.
- *Change `chart_total` to return a dict*: rejected. The invariant tests add that return value.

## Decision 6 — Add `read_date_counts` on the existing table path

**Decision**: Add `read_date_counts()` that opens the dates chart with the same right-click and "show as a table" path as `_dates_table_total`, scrolls visible rows once each, stores `{row header: alerts integer}`, and calls `_leave_dates_table()` before returning. The key is the row-header text, not `aria-rowindex`.

**Rationale**: `chart_total(DATES_CHART)` returns one sum. The private collector prefers `aria-rowindex` as its key, so it is not a date map. A public method can keep the date text without changing the sum. The table must be closed so later chart reads still see the canvas.

**Alternatives considered**:

- *Call `Chart.read` on `DATES_CHART`*: rejected. That path returned no dates total in the SVG work and is not what `chart_total` uses now.
- *Return the private row-index map*: rejected. The golden keys are dates.

## Decision 7 — Add `read_hour_buckets` for sums, and skip the hour daily average

**Decision**: Add `read_hour_buckets()` that reads SVG `aria-label`s inside `HOUR_CHART`, keeps a label that contains `HH:MM` and an integer, and drops a label that contains `ממוצע` or a fractional number. The result is `{HH:MM: integer}`. `test_alerts_by_hour_daily_avg_matches_db` calls `pytest.skip("Missing page object method for hour daily_avg")`.

**Rationale**: `chart_total` sums those integers and discards the hour text. The average line is a float labeled `ממוצע`, which the hour total already ignores. `set_district_aggregation` targets the district chart, so it is the wrong control for the hour visual. No hour-scoped daily-average reader exists. The request allows that test to skip.

**Alternatives considered**:

- *Call `set_district_aggregation("average")` before reading hours*: rejected. That toggles the district chart.
- *Treat the average-line float as `daily_avg`*: rejected. The golden hour averages are integers, and the existing parser drops fractional labels on purpose.

## Decision 8 — Compare golden keys, and normalize date and hour text

**Decision**: A map assertion passes when every golden key is present and the integers are equal. Extra UI rows are allowed. A UI date that parses as `DD/MM/YYYY` is compared as `YYYY-MM-DD`. An hour token `H:MM` or `HH:MM` is compared as `HH:MM`.

**Rationale**: The golden maps are the rows the user asked to validate. The charts can show more categories than the file. The file stores ISO dates and zero-padded hours. The page table and SVG labels do not have to use that spelling.

**Alternatives considered**:

- *Require the UI map to equal the golden map exactly*: rejected. A chart that also shows a category the file omits would fail a correct golden row.
- *Fuzzy-match settlement spelling*: rejected. Settlement names are compared as read. A mismatch should surface the actual label.

## Decision 9 — Assert the file's 2023 dates after the 2026 range

**Decision**: `test_alerts_by_date_matches_db` sets `2026-09-01` through `2026-10-18` (page format `01/09/2026` to `18/10/2026`) and then expects the golden keys `2023-09-29`, `2023-09-21`, `2023-09-17`, `2023-09-10`, and `2023-09-02`. The YAML is not edited.

**Rationale**: The request says to set the screen date range and validate `alerts_by_date`. Those keys are outside that range. That is a property of the golden file. This test may fail on the data. It must not be skipped for that reason, and it must not change the two card tests.

**Alternatives considered**:

- *Skip the date test because the years differ*: rejected. The date reader is being added. A data mismatch is an assertion failure, not a missing method.
- *Rewrite the golden dates to September 2026*: rejected. This slice does not edit the golden file.

## Decision 10 — One test per map

**Decision**: Settlement, מחוז sum, מחוז daily average, each skipped hierarchy level, dates, hour sum, and hour daily average are separate tests. Each is marked `@pytest.mark.sanity`.

**Rationale**: `pytest.skip` marks the whole test skipped. A skip after a successful מחוז sum assertion would hide that pass. Separate tests keep a missing reader on the metric that lacks it.

**Alternatives considered**:

- *One test function for all of `alerts_by_hierarchy`*: rejected. The first missing level would skip the מחוז checks in that same function.
