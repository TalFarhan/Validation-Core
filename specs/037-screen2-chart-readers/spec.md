# Feature Specification: Screen 2 Chart Readers

**Feature Branch**: `feature/reportportal-integration` (spec directory `037-screen2-chart-readers`; git checkout stays put)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Add the missing Screen 2 readers for the hierarchy chart and the hour chart so the skipped sanity tests can run. Do not edit `data/alerts/db_sanity_am_kalavi.yaml`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - נפה, רשות, and יישוב can be read (Priority: P1)

A validation author runs the three hierarchy tests that today skip before touching the page. Each test selects that level on the district chart, reads a name-to-count map, and compares the golden sum.

**Why this priority**: Those three tests never call the page. A reader that is not wired into them cannot replace the skip.

**Independent Test**: `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, and `test_hierarchy_yeshuv_matches_db` each set the golden date range, select the level, select Sum, and compare `alerts_by_hierarchy.<level>.sum`.

**Acceptance Scenarios**:

1. **Given** a control named נפה, רשות, or יישוב inside the district chart, **When** that level test runs, **Then** the golden sum names match the UI counts.
2. **Given** no such control, or the reader returns an empty map, **When** that level test runs, **Then** it skips with `Missing page object method for hierarchy level <level>`.
3. **Given** the level is selected, **When** the map is non-empty, **Then** extra UI names are allowed and every golden sum key must match.

---

### User Story 2 - The hour daily average can be read (Priority: P1)

A validation author runs `test_alerts_by_hour_daily_avg_matches_db`. The hour chart already draws an average. The test reads that series instead of skipping before the page opens.

**Why this priority**: The sum reader already exists and deliberately drops average labels. The daily-average test is a separate skip.

**Independent Test**: The test sets the golden date range, calls `read_hour_daily_avg()`, and compares `alerts_by_hour.daily_avg`.

**Acceptance Scenarios**:

1. **Given** average labels that contain an hour and a whole count, **When** the test runs, **Then** `00:00`, `04:00`, `14:00`, `15:00`, and `21:00` match the golden daily-average integers.
2. **Given** the average series cannot be separated from the sum, **When** the reader returns an empty map, **Then** the test skips with `Missing page object method for hour daily_avg`.
3. **Given** a non-empty map that lacks a golden hour or has the wrong count, **When** the test runs, **Then** it fails.

---

### User Story 3 - An empty district or hour map can fall back to a tooltip (Priority: P2)

The existing מחוז and hour-sum tests already call `read_district_labels()` and `read_hour_buckets()`. They skip only when those maps are empty. When rows and mark labels are empty, the page hovers the bars and reads the tooltip.

**Why this priority**: Those tests already execute. The fallback is only for the empty-map path. It must not change a map that already has labels.

**Independent Test**: `test_hierarchy_mahoz_sum_matches_db` and `test_alerts_by_hour_sum_matches_db` keep their current asserts. A tooltip is consulted only after the existing row and mark reads return nothing.

**Acceptance Scenarios**:

1. **Given** visible district rows or hour mark labels, **When** the existing readers run, **Then** they return that map and do not hover.
2. **Given** no rows and no mark labels, **When** a bar tooltip names a category and an integer, **Then** that pair is included.
3. **Given** the tooltip also fails, **When** the map is still empty, **Then** the existing skip messages stay.

---

### Edge Cases

- `data/alerts/db_sanity_am_kalavi.yaml` is not edited.
- The two card tests and `test_alerted_population_by_settlement_matches_db` stay as they are.
- `test_alerts_by_date_matches_db` stays as it is.
- מחוז daily average stays on `set_district_aggregation("average")` and `read_district_labels()`. This slice does not add נפה, רשות, or יישוב daily-average tests. `pytest.skip` would hide a sum assert in the same function.
- A lower hierarchy level is selected only inside that level's test. The fixture is function-scoped, so the next test opens the report again.
- Comments inside new and edited functions are English.
- `core/` is not edited. Tooltips and drill clicks stay on the population page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Add `set_hierarchy_level(level)` on `AlertsPopulationPage` for `nafa`, `rashut`, and `yeshuv`. The visible labels are נפה, רשות, and יישוב. `mahoz` stays the chart titled `התרעות לפי מחוז` and does not need a new click.
- **FR-002**: The level control is a button, tab, or option inside the district visual. If it is not visible, `set_hierarchy_level` returns false and does not click another control.
- **FR-003**: `read_district_labels()` keeps its name and `{name: int}` result. It still reads visible rows, then mark labels. It scrolls the district visual when collecting rows. A tooltip hover runs only when both of those reads are empty.
- **FR-004**: Each of `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, and `test_hierarchy_yeshuv_matches_db` sets the golden date range, calls `set_hierarchy_level`, calls `set_district_aggregation("sum")`, and compares `read_district_labels()` to that level's `sum` map. A false level selection or an empty map skips with `Missing page object method for hierarchy level <level>`.
- **FR-005**: Add `read_hour_daily_avg() -> dict[str, int]` for `גרף התרעות וגם ממוצע לפי שעה`. It keeps hour labels that the sum reader drops because they name the average. A whole number is stored as an int. A map that cannot be paired is empty.
- **FR-006**: `test_alerts_by_hour_daily_avg_matches_db` sets the golden date range and compares `read_hour_daily_avg()` to `alerts_by_hour.daily_avg`. An empty map skips with `Missing page object method for hour daily_avg`.
- **FR-007**: `read_hour_buckets()` stays the sum reader. It still omits labels that contain `ממוצע` or a fractional number. It may use the same tooltip fallback when its current reads are empty.
- **FR-008**: Do not edit `data/alerts/db_sanity_am_kalavi.yaml`, `core/`, or the two card tests.

### Key Entities

- **Hierarchy level**: `nafa`, `rashut`, or `yeshuv`, selected on the district chart, then read as `{name: count}` in Sum mode.
- **Hour bucket**: `HH:MM` to an integer. Sum and daily average are separate maps from the same chart.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` are not edited.
- **AC-002**: `AlertsPopulationPage` still inherits `AlertsAnalysisPage`. Login and the iframe wait stay on `ReportShell`.
- **AC-003**: The new locators live on the population page.
- **AC-004**: `read_district_labels` and `read_hour_buckets` keep their names. The three level tests and the hour daily-average test change from an unconditional skip to a call.
- **AC-005**: `core/` does not load `data/alerts/`.
- **AC-006**: No new SQL client. The golden file remains the comparison source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With a visible level control, the נפה, רשות, and יישוב tests assert the golden sum maps instead of skipping before the page opens.
- **SC-002**: With a readable average series, the hour daily-average test asserts the five golden hours. Without one, it skips with the existing message.
- **SC-003**: The golden YAML file is unchanged.
- **SC-004**: The two card tests are unchanged.
- **SC-005**: Fleet smoke is not a gate. This slice does not edit Layer 0, Layer 2, or the fleet page.

## Assumptions

- The district chart can show נפה, רשות, and יישוב through a control on that visual. If the live page has no such control, the three tests keep their current skip messages.
- Sum mode (`סכום`) and daily average (`ממוצע ליום`) remain the buttons `set_district_aggregation` already clicks.
- The hour chart draws the sum and the average together. The average can be recognized by the word `ממוצע` or by the series that is not the integer sum.
- Golden daily-average counts are whole numbers. A fractional label that is not a whole number is not stored.
- Portal auth is required for a live run. This plan does not run the browser.
