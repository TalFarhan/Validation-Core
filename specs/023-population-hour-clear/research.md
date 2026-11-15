# Phase 0 Research: Population Hour Sum and Clear Baseline

**Feature**: 023-population-hour-clear | **Date**: 2026-10-15

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Drop the average on the hour chart only

**Decision**: When `chart_total` totals `HOUR_CHART`, it keeps the series names from `Chart._parse`.
It does not add a series whose name contains `ממוצע`. It also does not add a cell that is a
`float` and is not a whole number. `int` cells, and whole floats such as `1.0`, are still added.
`bool` stays excluded. Dates, district, and settlement totals are unchanged.

**Rationale**: On 2026-10-15 the hour total was `5895.54`. The same chart's tooltip was
`ממוצע 5,895.54`, and the bars beside it were integers (`5293`, `4181`, and the other hours).
`_categories_for_total` currently discards the series tuple, so the sum cannot tell the average
series from the bars. Keeping that tuple on the page is enough. A fractional float is a second
guard when the average is not labeled.

**Alternatives considered**:

- *Skip every float, including whole floats*: rejected. A bar parsed as `1.0` is still a bar.
  The live average is not a whole number.
- *Filter inside `population_snapshot.py`*: rejected. The three-chart test calls `chart_total`
  directly.
- *Teach `Chart.read` to ignore averages*: rejected. That is a `core/` change.

## Decision 2 — The clear baseline is the first clear

**Decision**: `test_clear_restores_population_snapshot` calls `page.clear_filters()` before
`take_snapshot`. It then applies `01/09/2026`–`01/10/2026`, day, night, and the range `0`–`349`,
asserts the snapshot changed, calls `clear_filters()` again, and asserts the baseline returned.

**Rationale**: Arrival warned was `10136795` while the total card was `10142584`. After clear,
warned equaled the total card. The report opens with default filters. Clear is the unfiltered
state. The test was comparing those two states.

**Alternatives considered**:

- *Compare only the cards that clear does not change*: rejected. The test's purpose is that the
  full snapshot returns.
- *Stop calling clear and snapshot the arrival state twice*: rejected. The test is about clear.

## Decision 3 — What the three-chart comparison uses

**Decision**: `test_hour_date_and_district_sums_match` stays as it is. After this slice its hour
value is the integer bar sum, not `5895.54`. Dates and district totals stay on their current readers.

**Rationale**: The failing assertion was `5895.54 == 0`. The `5895.54` side is the average this
slice removes. The dates side was `0` because the visible date categories were zeros. The test
remains the check that the bar sum, the dates sum, and the district sum agree.

**Alternatives considered**:

- *Change the test to ignore the dates chart*: rejected. The user asked for the three existing
  tests to pass, not for a weaker comparison.
