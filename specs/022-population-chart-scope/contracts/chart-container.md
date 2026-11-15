# Contract: Population Chart Container

**Feature**: 022-population-chart-scope | **Module**: `pages/alerts_analysis/population_page.py` | **Date**: 2026-10-15

Page-local behavior. `Chart.read`, `Chart._container`, and `scope_host` are unchanged.

## `_visual_container(self, title: str) -> Locator`

Used for `DATES_CHART` and `HOUR_CHART` only.

1. Find the first text node in the report frame that contains `title`.
2. Walk ancestors whose class contains `visualContainer` or `visual-container`, nearest first.
   A `visualContainerHost` is included in that walk.
3. Accept the first ancestor that has at least one numeric token and whose visible text does not
   contain any other title in `{DISTRICT_CHART, DATES_CHART, HOUR_CHART, SETTLEMENT_CHART}`
   besides `title`.
4. If none qualifies, raise `AssertionError`. Do not call `Chart.read` as a fallback.

## `chart_total(self, title: str, series_index: int = 0) -> int | float`

1. When `title` is `DATES_CHART` or `HOUR_CHART`, parse `_visual_container(title)` with
   `Chart._parse`. Do not pass `PAGE_TITLE` into `Chart.read` for these two titles.
2. For every other title, keep `Chart.read(title, scope=PAGE_TITLE)`.
3. If the reading is empty or has no categories, raise `AssertionError`.
4. Add a selected cell only when it is an `int` or `float` and not a `bool`. Skip every other cell.
5. If no cell was added, raise `AssertionError`.
6. If the sum is a whole float, return `int`. Otherwise return the sum.

MUST NOT add 0 for a skipped cell. MUST NOT import new symbols from a new module. MUST NOT edit `core/`.

## Ready and clear

- `AlertsPopulationPage.__init__` sets `self.timeout = 60_000` before `KPI` and `Chart` are constructed.
- `before_report_ready_check` returns when the district chart is visible. It clicks the page
  switcher only when that switcher is visible and the district chart is not.
- `clear_filters` waits until the total population card is visible, then calls `Slicer.clear_all`.

## Examples (normative)

| Read root text | Dates total |
|----------------|-------------|
| Date labels and their numbers only | Sum of those numbers |
| Date labels plus `אשדוד` from another visual | Rejected container; walk stops before that box |
| Header with the title and no number | Rejected; walk continues outward |
| No qualifying ancestor | Raise |

Day total plus night total equals the untoggled dates total.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Day plus night equals the untoggled dates total | `test_day_plus_night_equals_untoggled_sum` |
| Hour, dates, and district totals match in Sum mode | `test_hour_date_and_district_sums_match` |
| Clear restores the arrival snapshot | `test_clear_restores_population_snapshot` |
| Page open, cards, and settlement legend still pass | the other tests in `test_population_invariants.py` |
| No `core/` file in the slice diff | review of the edit; only `pages/alerts_analysis/population_page.py` |
