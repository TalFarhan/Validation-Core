# Feature Specification: Bound the Global Invariant Tests by Date

**Feature Branch**: `feature/reportportal-integration` (spec directory `031-invariant-date-bounds`; git checkout stays put)

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "Add a date range to the day/night and clear-restore invariant tests so they do not scan 11,000 unfiltered rows and time out. Re-apply that range after clear, before the after snapshot. Do not mark the tests expected-fail. Do not edit core/ or pages/."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Day plus night stays inside one date window (Priority: P1)

A validation author checks that day hours plus night hours equal the dates chart with both toggles off. The check runs on `01/09/2026` through `15/10/2026`, so the dates table is that window and not the unfiltered history.

**Why this priority**: `test_day_plus_night_equals_untoggled_sum` reads the dates chart three times. An unfiltered read scrolls more than 11,000 rows and the run hits a 13-minute timeout. The day/night identity is the logic under test.

**Independent Test**: The test sets `01/09/2026` and `15/10/2026` before the untoggled dates total. `day + night == untoggled` stays the assertion. The test has no `pytest.mark.xfail`.

**Acceptance Scenarios**:

1. **Given** the population page is cleared, **When** the day/night test starts, **Then** it applies `01/09/2026` through `15/10/2026` before it reads the untoggled dates total.
2. **Given** that window is in place, **When** day hours and night hours are totaled, **Then** their sum equals the untoggled dates total.
3. **Given** the test file, **When** this story is implemented, **Then** `test_day_plus_night_equals_untoggled_sum` has no `pytest.mark.xfail`.

---

### User Story 2 - Clear restore stays inside the same window (Priority: P2)

A validation author checks that clearing filters returns the population snapshot. Both the before snapshot and the after snapshot are taken with `01/09/2026` through `15/10/2026` applied. Clearing removes that range, so the test puts the range back before the after snapshot.

**Why this priority**: `take_snapshot` reads the dates chart. After `clear_filters()` the dates chart is the unfiltered table. Reading that table is the 13-minute timeout. The clear-restore identity is the logic under test.

**Independent Test**: The before snapshot follows the date range. After `clear_filters()`, the same date range is applied again, and only then is the after snapshot taken. The two snapshots match. The during snapshot still differs. The test has no `pytest.mark.xfail`.

**Acceptance Scenarios**:

1. **Given** the clear-restore test, **When** it takes the before snapshot, **Then** `01/09/2026` through `15/10/2026` is already applied.
2. **Given** the test has called `clear_filters()`, **When** it is about to take the after snapshot, **Then** it applies `01/09/2026` through `15/10/2026` again first.
3. **Given** both snapshots use that window, **When** the assertion runs, **Then** the after snapshot equals the before snapshot and the during snapshot does not.
4. **Given** the test file, **When** this story is implemented, **Then** `test_clear_restores_population_snapshot` has no `pytest.mark.xfail`.

---

### Edge Cases

- `clear_filters()` drops the date range. The after snapshot is invalid until `set_date_range("01/09/2026", "15/10/2026")` runs again.
- The clear test still changes the window to `01/09/2026`–`01/10/2026`, toggles day and night, and sets the 0–349 range. Those actions are what `clear_filters()` must undo.
- `test_hour_date_and_district_sums_match` already uses `01/09/2026` and `15/10/2026`. This slice does not edit that test.
- The page has `set_date_range` and `clear_filters`. It has no `filter_dates` and no `clear_all_filters`. This slice does not add them.
- Neither test gains `pytest.mark.xfail`.
- `core/` and `pages/` are not modified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `test_day_plus_night_equals_untoggled_sum` MUST call `set_date_range("01/09/2026", "15/10/2026")` after its opening `clear_filters()` and before the untoggled `chart_total` for the dates chart.
- **FR-002**: That test MUST keep `assert day + night == untoggled` and MUST NOT gain `pytest.mark.xfail`.
- **FR-003**: `test_clear_restores_population_snapshot` MUST call `set_date_range("01/09/2026", "15/10/2026")` after its opening `clear_filters()` and before `take_snapshot` for the before value.
- **FR-004**: After the later `clear_filters()`, that test MUST call `set_date_range("01/09/2026", "15/10/2026")` again before the after snapshot. The after snapshot MUST NOT be taken on the unfiltered page.
- **FR-005**: That test MUST keep `assert not same_snapshot(before, during)` and `assert same_snapshot(before, after)`. It MUST NOT gain `pytest.mark.xfail`.
- **FR-006**: The clear test MUST keep `set_between_dates("01/09/2026", "01/10/2026")`, both day/night calls, and `set_value_range(0, 349)` as the actions under test.
- **FR-007**: This feature MUST NOT modify `core/` or `pages/`. The tests MUST call the existing `set_date_range` and `clear_filters` methods.
- **FR-008**: `test_hour_date_and_district_sums_match`, `test_population_cards_within_total`, `test_settlement_series_match_legend`, and `test_population_suite_opens_second_page` MUST stay unchanged.
- **FR-009**: `tests/ui/alerts_analysis_dashboard/population_snapshot.py` MUST stay unchanged.

### Key Entities

- **Bounded window**: Start `01/09/2026`, end `15/10/2026`, day/month/year, applied with `set_date_range`.
- **Before snapshot**: Cards and chart totals taken after the bounded window is applied and before the clear test's mutations.
- **After snapshot**: The same reads taken only after `clear_filters()` and a second `set_date_range` for that window.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page is unchanged. The tests use `set_date_range` and `clear_filters`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `chart_total` and `take_snapshot` keep their names and arguments.
- **AC-005**: No new date labels are introduced in `core/` or `pages/`.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_day_plus_night_equals_untoggled_sum` passes without scanning the unfiltered dates table.
- **SC-002**: `test_clear_restores_population_snapshot` passes, and its after snapshot is taken only after the bounded window is applied again.
- **SC-003**: The diff for this slice contains no path under `core/` or `pages/`.

## Assumptions

- The method the request calls `filter_dates` is the existing `set_date_range`. The method it calls `clear_all_filters` is the existing `clear_filters`.
- The 13-minute timeout is `chart_total` on the dates chart scrolling the unfiltered virtualized table.
- `01/09/2026` through `15/10/2026` is small enough that those reads finish inside the test timeout.
- Day hours plus night hours still partition the dates total inside that window.
- `clear_filters()` removes the date range, so the after snapshot needs the range applied again.
- Inline comments in edited Python stay English.
