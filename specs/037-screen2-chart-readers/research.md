# Research: Screen 2 Chart Readers

## Decision 1 — Wire the four unconditional skips to new page methods

**Decision**: Edit both `pages/alerts_analysis/population_page.py` and the four functions in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` that call `pytest.skip` before any page method.

**Rationale**: `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, `test_hierarchy_yeshuv_matches_db`, and `test_alerts_by_hour_daily_avg_matches_db` do not take the dashboard fixture. A new reader cannot run until those functions call it. מחוז sum, מחוז daily average, dates, hour sum, and settlement already call readers and skip only on an empty map.

**Alternatives considered**: Adding methods and leaving the four tests untouched. Rejected because they would still skip before the page opens.

## Decision 2 — Select נפה, רשות, and יישוב on the district chart

**Decision**: `set_hierarchy_level(level)` looks inside the `התרעות לפי מחוז` visual for a visible button, tab, or option named נפה, רשות, or יישוב. `mahoz` is that chart's default and is not given a new click. The method returns false when the named control is missing and does not click a different control.

**Rationale**: Feature 034 skipped these levels because no selector was implemented. The chart title is the מחוז level. The golden file stores the other three levels as separate name-to-count maps, so they are a level change on the same visual rather than three new charts. A click that is not actually that label could change the chart the מחוז tests read. Each sanity test uses a function-scoped fixture, so a level click does not leak into the next test.

**Alternatives considered**:

- *Drill down one step per level with the generic expand button*: rejected. The number of steps and the parent row are not in the golden file, and a wrong drill changes the מחוז chart.
- *Keep the unconditional skip*: rejected. The user asked for the readers so these tests can execute.

## Decision 3 — Compare each new level on Sum only

**Decision**: Each of the three level tests calls `set_district_aggregation("sum")` and compares `alerts_by_hierarchy.<level>.sum`. It does not also assert `daily_avg`.

**Rationale**: מחוז already has a separate daily-average test. The three missing tests are one function each. `pytest.skip` skips the whole function, so a daily-average skip after a successful sum assert would hide that pass. Sum is the map with the distinct counts (for example נפת חירם `12`). Daily average for these three levels stays unread until it has its own test.

**Alternatives considered**: Asserting both modes in one function. Rejected because a failed or skipped average would erase the sum result.

## Decision 4 — Read rows, then marks, then one tooltip pass

**Decision**: `read_district_labels()` keeps its order: visible table rows, then SVG mark labels. It scrolls the district visual and merges rows that appear. Only when both reads are empty does it hover each visible bar and parse the tooltip. `read_hour_buckets()` may use that same last step. The tooltip parser stays on the population page.

**Rationale**: The user asked for a table read when the visual is a matrix and a hover loop when it is a bar chart. The page already has the first two strategies. Hovering every bar when labels are already present is slower and can dismiss the level control. Constitution VII keeps tooltips on the domain page, so this does not move into `core/components`.

**Alternatives considered**: Hovering every bar first. Rejected because the existing row reader is enough when the visual is a matrix, and hover is the expensive path.

## Decision 5 — Read the hour average without changing the sum reader

**Decision**: `read_hour_daily_avg()` reads `גרף התרעות וגם ממוצע לפי שעה` and keeps labels the sum reader drops: text that contains `ממוצע`, or a whole number on the average series. The stored value is an `int`. A fractional value that is not a whole number is omitted. An empty map means the test skips with `Missing page object method for hour daily_avg`. `read_hour_buckets()` still omits `ממוצע` and fractional labels.

**Rationale**: The golden daily averages are integers (`1` on each listed hour). The current `_hour_bucket` helper treats `ממוצע` and any `d.d` token as "not the sum". Reusing that helper for the average would return nothing. A separate method keeps the sum test stable.

**Alternatives considered**: Rounding every fractional average to the nearest integer. Rejected because a value such as `0.4` is not the golden `1`, and storing it would fail the test instead of skipping a series that is not actually the daily average.
