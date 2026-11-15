# Phase 0 Research: Bound the Global Invariant Tests by Date

**Feature**: 031-invariant-date-bounds | **Date**: 2026-10-18

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Call `set_date_range`, not a new `filter_dates`

**Decision**: Both tests call `population_dashboard.set_date_range("01/09/2026", "15/10/2026")`.
This slice does not add `filter_dates`.

**Rationale**: `AlertsPopulationPage.set_date_range` already fills `תאריך התחלה` and
`תאריך סיום`, then waits until `read_card("total")` repeats. The request names that step
`filter_dates`. The page has no method by that name, and this slice must not edit `pages/`.

**Alternatives considered**:

- *Add `filter_dates` as an alias*: rejected. That edits `pages/`.
- *Call `set_between_dates` for the baseline*: rejected. That fills the fields and does not wait for the total card. `set_date_range` is the settled call already used by the three-chart test.

## Decision 2 — Call `clear_filters`, not a new `clear_all_filters`

**Decision**: The clear test keeps `clear_filters()`. This slice does not add `clear_all_filters`.

**Rationale**: `clear_filters` clears every slicer and waits until the total card repeats.
The request names that step `clear_all_filters`. The page has no method by that name.

**Alternatives considered**:

- *Add `clear_all_filters`*: rejected. That edits `pages/`.

## Decision 3 — Put the window on both sides of the clear test

**Decision**: `test_clear_restores_population_snapshot` calls `set_date_range("01/09/2026", "15/10/2026")` after the opening `clear_filters()` and before the before snapshot. After the later `clear_filters()`, it calls `set_date_range("01/09/2026", "15/10/2026")` again, and only then takes the after snapshot.

**Rationale**: `take_snapshot` calls `chart_total` for the dates chart. `clear_filters()` removes the date range. An after snapshot taken on that cleared page scrolls the unfiltered virtualized table, which is the 13-minute timeout. The before and after snapshots match only when both use the same window.

**Alternatives considered**:

- *Apply the range only before the before snapshot*: rejected. The after snapshot would still scan the unfiltered table.
- *Skip the test*: rejected. The clear-restore check is the logic under test.

## Decision 4 — Day/night applies the window before the first dates read

**Decision**: `test_day_plus_night_equals_untoggled_sum` keeps its opening `clear_filters()`, then calls `set_date_range("01/09/2026", "15/10/2026")` before `chart_total` for the untoggled dates chart. The assertion stays `day + night == untoggled`.

**Rationale**: That test reads the dates chart three times. Each unfiltered read scrolls more than 11,000 rows. The date window is the same one the three-chart test already uses. Day and night still partition that window.

**Alternatives considered**:

- *Leave the test unfiltered*: rejected. That is the timeout.
- *Mark the test expected-fail*: rejected. The user ruled that out.

## Decision 5 — Leave the clear test's mutations in place

**Decision**: After the before snapshot, the test still calls `set_between_dates("01/09/2026", "01/10/2026")`, `set_day_night("day")`, `set_day_night("night")`, and `set_value_range(0, 349)`.

**Rationale**: Those calls are the change that the during snapshot must show and that `clear_filters()` must undo. The bounded window is the baseline, not a replacement for those actions.

**Alternatives considered**:

- *Drop `set_between_dates`*: rejected. The test would no longer show that a narrower date window is cleared.

## Decision 6 — Do not edit the snapshot helper or the other tests

**Decision**: `population_snapshot.py` stays. `test_hour_date_and_district_sums_match` stays, including its `01/09/2026` and `15/10/2026` strings. The card test, the settlement legend test, and the page-open test stay.

**Rationale**: The snapshot helper already calls page methods. The date range in the clear test is what keeps those reads off the unfiltered table. The three-chart test already has this window.

**Alternatives considered**:

- *Change `take_snapshot` to skip the dates chart*: rejected. That edits the helper and drops part of the restore check. The user forbade page edits and asked to keep the business logic.
