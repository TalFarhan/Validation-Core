---

description: "Task list for Screen 2 golden-record map checks"
---

# Tasks: Screen 2 Sanity Maps

**Input**: Design documents from `/specs/034-screen2-sanity-maps/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sanity-maps.md, quickstart.md

**Tests**: The feature is the new sanity tests plus three page readers. Do not add another test module. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Four user stories. Settlement uses the existing `Chart.read`. מחוז needs a new label reader. Dates and hour sums need new readers. נפה, רשות, יישוב, and the hour daily average only skip.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Tests**: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- **Page readers**: `pages/alerts_analysis/population_page.py`
- **Golden record, unchanged**: `data/alerts/db_sanity_am_kalavi.yaml`
- **Do not edit**: `tests/ui/`, `core/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the golden maps, and the readers that already exist

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/034-screen2-sanity-maps"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `data/alerts/db_sanity_am_kalavi.yaml`, confirm `screen_2_alerts_analysis.date_range` is `2026-09-01` through `2026-10-18`, `alerted_population_by_settlement.values` has nine names, `alerts_by_hierarchy` has `mahoz`, `nafa`, `rashut`, and `yeshuv` each with `sum` and `daily_avg`, `alerts_by_date.values` has the five `2023-09-*` keys, and `alerts_by_hour` has `sum` and `daily_avg` for `00:00`, `04:00`, `14:00`, `15:00`, and `21:00`. In `pages/alerts_analysis/population_page.py`, confirm `set_district_aggregation`, `chart_total`, `SETTLEMENT_CHART`, `DISTRICT_CHART`, `DATES_CHART`, `HOUR_CHART`, and `WARNED_SERIES` exist, and that no method selects נפה, רשות, or יישוב. In `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, confirm `test_global_metrics_match_db` and `test_filtered_population_matches_db` are present

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lock the card tests, `chart_total`, and the directories this slice must not edit

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Leave the function bodies of `test_global_metrics_match_db` and `test_filtered_population_matches_db` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` unchanged. Leave `chart_total`, `clear_filters`, `set_date_range`, `read_card`, and `set_district_aggregation` signatures in `pages/alerts_analysis/population_page.py` unchanged. Leave every path under `tests/ui/` and `core/` unmodified

**Checkpoint**: The card tests and the chart totals stay. New tests and new readers can be added beside them.

---

## Phase 3: User Story 1 - Settlement population matches the golden record (Priority: P1) 🎯 MVP

**Goal**: Each golden settlement equals the warned series after the screen date range.

**Independent Test**: `test_alerted_population_by_settlement_matches_db` sets `01/09/2026` through `18/10/2026`, reads `SETTLEMENT_CHART` with `Chart.read`, and checks the nine golden names against `WARNED_SERIES`.

### Implementation for User Story 1

- [X] T004 [US1] Add `test_alerted_population_by_settlement_matches_db(population_dashboard)` to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Decorate it with `@pytest.mark.sanity`. Load the golden screen with `load_sanity_data()`. Call `set_date_range(to_page_date(start), to_page_date(end))`. Construct `Chart(page=population_dashboard.page, frame=population_dashboard._report_frame(), timeout_ms=population_dashboard.timeout)` and call `chart.read(population_dashboard.SETTLEMENT_CHART, scope=population_dashboard.PAGE_TITLE)`. Use the series index of `population_dashboard.WARNED_SERIES`. For each name in `metrics["alerted_population_by_settlement"]["values"]`, assert that label's numeric cell equals the golden integer. Do not skip this test. Do not edit the two card tests. Import `Chart` from `core.components.chart`. Comments inside the function are English

**Checkpoint**: Settlement rows are testable. Hierarchy, dates, and hours are not required yet.

---

## Phase 4: User Story 2 - District hierarchy sum and daily average match (Priority: P1)

**Goal**: מחוז names match the golden sum and daily average. The district total stays a single number.

**Independent Test**: `test_hierarchy_mahoz_sum_matches_db` expects מחוז צפון `12` and פיקוד דרום `1`. `test_hierarchy_mahoz_daily_avg_matches_db` expects both names to be `1`. An empty label map skips only that test.

### Implementation for User Story 2

- [X] T005 [US2] Add `read_district_labels(self) -> dict[str, int]` to `pages/alerts_analysis/population_page.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Walk visible rows in `DISTRICT_CHART` the same way `_sum_visible_district_rows` does. Key each alerts integer by the row-header text from `_plain_cell`. Skip a header row and a `סה"כ` row. Do not scroll. Do not change `chart_total`. Comments inside the method are English
- [X] T006 [US2] Add `test_hierarchy_mahoz_sum_matches_db` and `test_hierarchy_mahoz_daily_avg_matches_db` to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Both use `@pytest.mark.sanity`, `load_sanity_data()`, and `set_date_range` with `to_page_date`. The sum test calls `set_district_aggregation("sum")` and compares `read_district_labels()` to `alerts_by_hierarchy.mahoz.sum` (מחוז צפון `12`, פיקוד דרום `1`). The daily-average test calls `set_district_aggregation("average")` and compares the labels to `mahoz.daily_avg` (both `1`). Every golden key must match. Extra UI labels are allowed. If `read_district_labels()` returns an empty dict, call `pytest.skip("Missing page object method for district labels")`. Do not edit the two card tests. Comments inside the functions are English

**Checkpoint**: מחוז sum and מחוז daily average each run as their own test.

---

## Phase 5: User Story 3 - Dates and hours match the golden record (Priority: P2)

**Goal**: Golden dates and hour sums are checked from new readers. The hour daily average skips.

**Independent Test**: `test_alerts_by_date_matches_db` compares the five `2023-09-*` keys. `test_alerts_by_hour_sum_matches_db` compares `00:00` and `04:00` to `5` and the other three hours to `1`. `test_alerts_by_hour_daily_avg_matches_db` skips.

### Implementation for User Story 3

- [X] T007 [US3] Add `read_date_counts(self) -> dict[str, int]` to `pages/alerts_analysis/population_page.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Open the dates table with the same right-click and show-as-table path as `_dates_table_total`. Scroll visible rows and store `{row header text: alerts integer}`. Use the row-header text as the key, not `aria-rowindex`. Call `_leave_dates_table()` before returning whenever the table opened, including when collection fails. Do not change the integer `chart_total(DATES_CHART)` returns. Comments inside the method are English
- [X] T008 [US3] Add `read_hour_buckets(self) -> dict[str, int]` to `pages/alerts_analysis/population_page.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Read `aria-label` from `svg rect`, `svg path`, and `svg circle` inside `HOUR_CHART`. Keep a label that contains `HH:MM` or `H:MM` and an integer. Drop a label that contains `ממוצע` or a fractional number. Return `{HH:MM: integer}` with the hour zero-padded. Do not call `set_district_aggregation`. Do not change `chart_total(HOUR_CHART)`. Comments inside the method are English
- [X] T009 [US3] Add `test_alerts_by_date_matches_db`, `test_alerts_by_hour_sum_matches_db`, and `test_alerts_by_hour_daily_avg_matches_db` to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Mark each `@pytest.mark.sanity`. The date test and the hour-sum test call `set_date_range` through `to_page_date`. Normalize a `DD/MM/YYYY` date header to `YYYY-MM-DD` before comparing `read_date_counts()` to `alerts_by_date.values`. Compare `read_hour_buckets()` to `alerts_by_hour.sum`. An empty date map calls `pytest.skip("Missing page object method for alerts by date")`. An empty hour map calls `pytest.skip("Missing page object method for hour sum")`. A non-empty map that lacks a golden key fails. `test_alerts_by_hour_daily_avg_matches_db` only calls `pytest.skip("Missing page object method for hour daily_avg")` and does not read the chart. Do not edit the golden file or the two card tests. Comments inside the functions are English

**Checkpoint**: Date and hour-sum checks are separate from the skipped hour daily average.

---

## Phase 6: User Story 4 - Unmapped hierarchy levels do not fail the suite (Priority: P2)

**Goal**: נפה, רשות, and יישוב are visible skips. They do not click the page.

**Independent Test**: Each level's test is skipped with `Missing page object method for hierarchy level <level>` and makes no page call.

### Implementation for User Story 4

- [X] T010 [US4] Add `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, and `test_hierarchy_yeshuv_matches_db` to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/034-screen2-sanity-maps/contracts/sanity-maps.md`. Mark each `@pytest.mark.sanity`. Each function only calls `pytest.skip` with `Missing page object method for hierarchy level nafa`, `Missing page object method for hierarchy level rashut`, or `Missing page object method for hierarchy level yeshuv`. Do not call `set_date_range` or any other page method in these three functions. Do not add a hierarchy-level click to `pages/alerts_analysis/population_page.py`. Comments inside the functions are English

**Checkpoint**: The three missing levels skip without affecting the settlement, מחוז, date, or hour tests.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Collect the module from `specs/034-screen2-sanity-maps/quickstart.md` and confirm this slice did not edit `tests/ui/` or `core/`

- [X] T011 Run `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only` from `specs/034-screen2-sanity-maps/quickstart.md` and confirm the collected tests are the two card tests, `test_alerted_population_by_settlement_matches_db`, `test_hierarchy_mahoz_sum_matches_db`, `test_hierarchy_mahoz_daily_avg_matches_db`, `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, `test_hierarchy_yeshuv_matches_db`, `test_alerts_by_date_matches_db`, `test_alerts_by_hour_sum_matches_db`, and `test_alerts_by_hour_daily_avg_matches_db`
- [X] T012 [P] Confirm the only edited implementation files for this slice are `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` and `pages/alerts_analysis/population_page.py`. Confirm `tests/ui/`, `core/`, and `data/alerts/db_sanity_am_kalavi.yaml` are unchanged, and that `chart_total` in `pages/alerts_analysis/population_page.py` still returns one number
- [X] T013 Run `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -v` from `specs/034-screen2-sanity-maps/quickstart.md`. Portal auth is required. The two card tests pass. נפה, רשות, יישוב, and the hour daily average are skipped. A date mismatch against the September 2023 golden keys fails only `test_alerts_by_date_matches_db`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks every user story
- **User Story 1 (Phase 3)**: Depends on Foundational. No new page method
- **User Story 2 (Phase 4)**: Depends on Foundational. Implement after User Story 1 because both add functions to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- **User Story 3 (Phase 5)**: Depends on Foundational. Implement after User Story 2 because `read_date_counts` and `read_hour_buckets` are added to `pages/alerts_analysis/population_page.py` after `read_district_labels`, and the new tests append to the same test module
- **User Story 4 (Phase 6)**: Depends on Foundational. Implement after User Story 3 so the three skip functions are appended after the other new tests. The skips do not depend on those readers
- **Polish (Phase 7)**: Depends on all four user stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T003. Uses `Chart.read`, `load_sanity_data`, `to_page_date`, and `set_date_range`
- **User Story 2 (P1)**: T006 starts after T005. Uses `set_district_aggregation` and `read_district_labels`. Does not require the settlement assertion to pass
- **User Story 3 (P2)**: T008 starts after T007. T009 starts after both readers. The hour daily-average skip does not call `read_hour_buckets`
- **User Story 4 (P2)**: No page reader. The three skips do not call the dashboard fixture

### Within Each User Story

- User Story 2 adds the page reader before its tests
- User Story 3 adds both page readers before its tests
- User Story 1 and User Story 4 are test-only
- The live portal run waits until every new test is in the module

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T005, T007, and T008 all edit `pages/alerts_analysis/population_page.py`, so they stay sequential
- T004, T006, T009, and T010 all edit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, so they stay sequential
- T012 can run beside T011. T013 waits until collection succeeds

---

## Parallel Example: Setup

```bash
# Phase 1 can read the pin and the golden file together:
Task: "Confirm .specify/feature.json pins specs/034-screen2-sanity-maps"
Task: "Confirm Screen 2 maps in data/alerts/db_sanity_am_kalavi.yaml and the existing readers in pages/alerts_analysis/population_page.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the settlement test checks the nine golden names on the warned series
3. **STOP and VALIDATE**: run `test_alerted_population_by_settlement_matches_db` together with the two card tests when portal auth is available

### Incremental Delivery

1. Setup confirms the golden maps and that no hierarchy-level method exists
2. User Story 1 checks settlements with `Chart.read`
3. User Story 2 adds `read_district_labels` and checks מחוז sum and daily average
4. User Story 3 adds the date and hour readers and checks those maps, skipping the hour daily average
5. User Story 4 skips נפה, רשות, and יישוב without a click
6. Phase 7 collects the module and runs it

### Parallel Team Strategy

One person owns `pages/alerts_analysis/population_page.py` for T005, T007, and T008. One person owns `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` for T004, T006, T009, and T010. The test tasks wait for the reader they call.

---

## Notes

- Do not edit the bodies of `test_global_metrics_match_db` or `test_filtered_population_matches_db`
- Do not edit `tests/ui/`, `core/`, or `data/alerts/db_sanity_am_kalavi.yaml`
- Do not change `chart_total` from a single total into a map
- Do not add a click that selects נפה, רשות, or יישוב
- Do not call `set_district_aggregation` from the hour reader
- `pytest.skip` applies to one new test. A missing reader must not fail the module
- The golden alert dates stay in September 2023. Do not rewrite them to 2026
- Comments inside functions stay English
- Do not run `pytest tests/ui/fleet_dashboard/`. This slice does not change Layer 0, Layer 2, or the fleet page
