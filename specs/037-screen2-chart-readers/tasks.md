---

description: "Task list for Screen 2 hierarchy and hour-average readers"
---

# Tasks: Screen 2 Chart Readers

**Input**: Design documents from `/specs/037-screen2-chart-readers/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/chart-readers.md, quickstart.md

**Tests**: The four functions that skip before opening the page are updated to call the new readers. Do not add a new test module. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Three user stories. Story 1 selects נפה, רשות, and יישוב and asserts each golden sum. Story 2 reads the hour daily average. Story 3 adds a tooltip only when the cheaper reads are empty. Story 1 and Story 2 both edit `pages/alerts_analysis/population_page.py`, so Story 2 follows Story 1 on that file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Page**: `pages/alerts_analysis/population_page.py`
- **Tests**: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- **Golden record, unchanged**: `data/alerts/db_sanity_am_kalavi.yaml`
- **Do not edit**: `core/`, `tests/conftest.py`, the two card tests in the sanity module

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and that the four target tests skip before any page call

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/037-screen2-chart-readers"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, confirm `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, `test_hierarchy_yeshuv_matches_db`, and `test_alerts_by_hour_daily_avg_matches_db` call `pytest.skip` and do not take `population_dashboard`. Confirm `test_hierarchy_mahoz_sum_matches_db` calls `set_district_aggregation("sum")` and `read_district_labels()`, and `test_alerts_by_hour_sum_matches_db` calls `read_hour_buckets()`. In `pages/alerts_analysis/population_page.py`, confirm `DISTRICT_CHART` is `התרעות לפי מחוז`, `HOUR_CHART` is `גרף התרעות וגם ממוצע לפי שעה`, and `SUM_MODE` is `סכום`. In `data/alerts/db_sanity_am_kalavi.yaml`, confirm `alerts_by_hierarchy.nafa.sum`, `.rashut.sum`, and `.yeshuv.sum` plus `alerts_by_hour.daily_avg` exist. Do not edit the YAML file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the visible-control lookup the level selector will click

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add `_hierarchy_control(self, label)` to `pages/alerts_analysis/population_page.py` per `specs/037-screen2-chart-readers/contracts/chart-readers.md`. It searches the `התרעות לפי מחוז` visual for a visible button, tab, or option whose accessible name equals `label`. Return that locator, or `None` when none is visible. Do not click. Comments inside the method are English

**Checkpoint**: A missing נפה, רשות, or יישוב control can be detected without changing the chart.

---

## Phase 3: User Story 1 - נפה, רשות, and יישוב can be read (Priority: P1) 🎯 MVP

**Goal**: Each missing hierarchy test selects that level, reads Sum, and compares the golden sum map.

**Independent Test**: `test_hierarchy_nafa_matches_db` compares `alerts_by_hierarchy.nafa.sum` (נפת חירם `12` and חטמ'ר צפונית - 7643 `1`). The רשות and יישוב tests compare their own `sum` maps. A missing control or an empty map skips with `Missing page object method for hierarchy level <level>`.

### Implementation for User Story 1

- [X] T004 [US1] Add `set_hierarchy_level(self, level) -> bool` to `pages/alerts_analysis/population_page.py` per `specs/037-screen2-chart-readers/contracts/chart-readers.md`. Accept `nafa`, `rashut`, and `yeshuv`, mapped to נפה, רשות, and יישוב. Call `_hierarchy_control`. Click the control and return true when it exists. Return false without clicking anything else when it does not. Comments inside the method are English
- [X] T005 [US1] Update `read_district_labels` in `pages/alerts_analysis/population_page.py` per `specs/037-screen2-chart-readers/data-model.md`. Scroll the `התרעות לפי מחוז` visual and merge visible rows into one `{name: int}` map before falling back to mark labels. Do not hover in this task. Keep the method name and the empty-dict result when nothing pairs. Comments inside the method are English
- [X] T006 [US1] Replace the bodies of `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, and `test_hierarchy_yeshuv_matches_db` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/037-screen2-chart-readers/contracts/chart-readers.md`. Each takes `population_dashboard`, stays `@pytest.mark.sanity`, calls `_apply_golden_range`, `set_hierarchy_level`, and `set_district_aggregation("sum")`, then compares `read_district_labels()` to that level's `sum` map through `_assert_golden_keys`. If `set_hierarchy_level` returns false or the map is empty, `pytest.skip("Missing page object method for hierarchy level <level>")` with `nafa`, `rashut`, or `yeshuv`. Do not assert `daily_avg` in these three functions. Do not edit the two card tests or the מחוז tests. Comments inside the functions are English

**Checkpoint**: The three level tests open the page. They assert Sum or skip with the existing message.

---

## Phase 4: User Story 2 - The hour daily average can be read (Priority: P1)

**Goal**: The hour daily-average test reads the average series instead of skipping before the page opens.

**Independent Test**: `test_alerts_by_hour_daily_avg_matches_db` compares `alerts_by_hour.daily_avg` (`00:00`, `04:00`, `14:00`, `15:00`, and `21:00`, each `1`). An empty map skips with `Missing page object method for hour daily_avg`.

### Implementation for User Story 2

- [X] T007 [US2] Add `read_hour_daily_avg(self) -> dict[str, int]` to `pages/alerts_analysis/population_page.py` per `specs/037-screen2-chart-readers/contracts/chart-readers.md`. Read `גרף התרעות וגם ממוצע לפי שעה`. Keep a label that has `HH:MM` and a whole average count, including a label that contains `ממוצע`. Store the count as an `int`. Omit a fraction that is not a whole number. Return `{}` when no hour pairs. Do not change `read_hour_buckets` so that it starts keeping `ממוצע` labels. Comments inside the method are English
- [X] T008 [US2] Replace `test_alerts_by_hour_daily_avg_matches_db` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` per `specs/037-screen2-chart-readers/contracts/chart-readers.md`. Give it `population_dashboard`, keep `@pytest.mark.sanity`, call `_apply_golden_range`, and compare `read_hour_daily_avg()` to `alerts_by_hour.daily_avg` through `_assert_golden_keys`. If the map is empty, `pytest.skip("Missing page object method for hour daily_avg")`. Do not edit `test_alerts_by_hour_sum_matches_db`. Comments inside the function are English

**Checkpoint**: The hour daily-average test calls the page. The hour-sum test still uses `read_hour_buckets`.

---

## Phase 5: User Story 3 - An empty district or hour map can fall back to a tooltip (Priority: P2)

**Goal**: When rows and mark labels are empty, hover the bars and parse the tooltip. A map that already has labels is left alone.

**Independent Test**: `test_hierarchy_mahoz_sum_matches_db` and `test_alerts_by_hour_sum_matches_db` keep their current asserts. The tooltip path runs only after the existing reads return nothing.

### Implementation for User Story 3

- [X] T009 [US3] Add a tooltip fallback to `read_district_labels` in `pages/alerts_analysis/population_page.py` per `specs/037-screen2-chart-readers/research.md` Decision 4. After the scrolled rows and the mark-label pairing are both empty, hover each visible bar in `התרעות לפי מחוז` and parse a name plus an integer from the tooltip. Return `{}` when that also fails. Do not hover when either earlier read returned a map. Keep the parser on this page. Comments inside the method are English
- [X] T010 [US3] Add the same last-step tooltip fallback to `read_hour_buckets` in `pages/alerts_analysis/population_page.py`. Use it only when the SVG labels and `read_chart_categories` produced no buckets. Keep dropping labels that contain `ממוצע` or a fractional number on the sum path. Do not call this fallback from `read_hour_daily_avg`. Comments inside the method are English

**Checkpoint**: מחוז sum and hour sum still call the same methods. Hover is only the empty-map path.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Confirm the golden file, `core/`, and the card tests stayed put, then collect and run the sanity module

- [X] T011 [P] Confirm `data/alerts/db_sanity_am_kalavi.yaml` and `core/` have no edits from this slice. Confirm `test_global_metrics_match_db`, `test_filtered_population_matches_db`, `test_alerted_population_by_settlement_matches_db`, `test_hierarchy_mahoz_sum_matches_db`, `test_hierarchy_mahoz_daily_avg_matches_db`, `test_alerts_by_date_matches_db`, and `test_alerts_by_hour_sum_matches_db` in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` keep their current assertions
- [X] T012 [P] Run `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only` from `specs/037-screen2-chart-readers/quickstart.md` and confirm the eleven tests from feature 034 are collected, including the four that now take `population_dashboard`
- [X] T013 Run `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -v` from `specs/037-screen2-chart-readers/quickstart.md`. Portal auth is required. A level test may skip with `Missing page object method for hierarchy level <level>` when that control is absent. The hour daily-average test may skip with `Missing page object method for hour daily_avg` when the average series cannot be paired. A non-empty map that misses a golden key fails

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks every user story
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on User Story 2 or User Story 3
- **User Story 2 (Phase 4)**: Depends on Foundational. No functional dependency on User Story 1. It edits `pages/alerts_analysis/population_page.py` after T005 so the two page edits do not overlap
- **User Story 3 (Phase 5)**: Depends on T005 and T007, because it extends `read_district_labels` and `read_hour_buckets` after those methods are in their Story 1 and Story 2 shape
- **Polish (Phase 6)**: Depends on all three user stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T003. Uses `_hierarchy_control`, `set_hierarchy_level`, scrolled `read_district_labels`, and the three level tests
- **User Story 2 (P1)**: Starts after T005. Uses `read_hour_daily_avg` and `test_alerts_by_hour_daily_avg_matches_db`
- **User Story 3 (P2)**: Starts after T008. Tooltip work does not change the test asserts

### Within Each User Story

- Page methods land before the test that calls them
- User Story 1 scrolls the district visual before User Story 3 adds hover
- User Story 2 adds the average reader before User Story 3 touches `read_hour_buckets`

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T006 edits the test module and can start only after T004 and T005
- T008 edits the test module and can start only after T007
- T011 and T012 can run together after T010. T013 waits until collection succeeds

---

## Parallel Example: Setup

```bash
# The pin and the current skip tests can be confirmed together:
Task: "Confirm .specify/feature.json pins specs/037-screen2-chart-readers"
Task: "Confirm the four unconditional skips and the golden sum maps"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004, T005, and T006 so נפה, רשות, and יישוב either assert Sum or skip with the existing message
3. **STOP and VALIDATE**: run those three tests when portal auth is available

### Incremental Delivery

1. Setup confirms the pin and the current skips
2. Foundational finds a visible level control without clicking
3. User Story 1 selects the level and asserts Sum
4. User Story 2 reads the hour daily average
5. User Story 3 hovers only when the cheaper reads are empty
6. Phase 6 collects the module and runs it

### Parallel Team Strategy

One person owns `pages/alerts_analysis/population_page.py` for T003, T004, T005, T007, T009, and T010, in that order. Another person can own the test edits T006 and T008 after the matching page methods exist.

---

## Notes

- [P] tasks use different files or are read-only checks
- Do not assert `daily_avg` inside the נפה, רשות, or יישוב tests
- Do not edit `data/alerts/db_sanity_am_kalavi.yaml` or `core/`
- Fleet smoke is not a gate for this slice
