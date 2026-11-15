---

description: "Task list for the Screen 1 top-settlement tie assertion"
---

# Tasks: Top Settlement Tie Assertion

**Input**: Design documents from `/specs/036-top-settlement-ties/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/top-settlement-ties.md, quickstart.md

**Tests**: The feature is the assertion inside the existing ranking test. Do not add a new test module. Do not run fleet smoke: this slice does not edit `core/portal`, `ReportShell`, or the fleet page.

**Organization**: Two user stories share one function. Story 1 checks the stable golden counts. Story 2 checks the four tie slots. They edit the same test, so Story 2 follows Story 1.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Test**: `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`
- **Golden record, unchanged**: `data/alerts/db_sanity_am_kalavi.yaml`
- **Page reader, unchanged**: `pages/status_picture/status_picture_page.py`
- **Do not edit**: `core/`, `tests/conftest.py`, `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, `pages/alerts_analysis/population_page.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the golden partition, and that the ranking assert still requires every golden name

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/036-top-settlement-ties"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `data/alerts/db_sanity_am_kalavi.yaml`, confirm `screen_1_status_picture.metrics.top_10_settlements.values` has ראשון לציון `39`, תל אביב-יפו `36`, רמת השרון `35`, נתניה `34`, ראש העין `32`, רמלה `32`, and four names at `31` (יגל, גינתון, צפרייה, חיפה). Do not edit the file. In `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`, confirm `test_screen_1_top_settlements` calls `_assert_golden_entries` and `test_screen_1_filtered_metrics` asserts only `warning_zones_under_fire` and `alerted_population`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the golden partition helpers the ranking test will call

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add two helpers to `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` per `specs/036-top-settlement-ties/data-model.md`. `_stable_rankings(expected)` returns the entries whose count is `>= 32`. `_tie_count(expected)` returns the single integer among entries whose count is `< 32`, and raises `AssertionError` when those values are not one integer. Do not call the helpers from a test yet. Do not hard-code the six settlement names or `31`. Comments inside the helpers are English

**Checkpoint**: The golden map can be split. The ranking test still uses `_assert_golden_entries`.

---

## Phase 3: User Story 1 - Stable settlements keep their golden counts (Priority: P1) 🎯 MVP

**Goal**: The six golden counts at or above 32 match the UI by name. The four golden tie names are no longer required.

**Independent Test**: `test_screen_1_top_settlements` fails when any stable name is missing or has the wrong count, and it no longer fails only because יגל, גינתון, צפרייה, or חיפה is absent.

### Implementation for User Story 1

- [X] T004 [US1] Update `test_screen_1_top_settlements` in `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` per `specs/036-top-settlement-ties/contracts/top-settlement-ties.md`. Keep `@pytest.mark.sanity`, the golden date conversion, `set_date_range`, and `pytest.skip("Missing Page Object reader for top_10_settlements")` when the UI map is empty. Stop calling `_assert_golden_entries` for this map. Load `top_10_settlements.values`, take `_stable_rankings`, and assert each stable name is present with that exact count. The failure text names the settlement and shows the UI count beside the golden count. Do not add the four-slot check in this task. Comments inside the function are English

**Checkpoint**: A shuffled tie name no longer fails the test by itself. A wrong stable count still fails.

---

## Phase 4: User Story 2 - The four tie slots are count 31 (Priority: P1)

**Goal**: After the stable names are removed, the UI map has exactly four rows and each count is the golden tie value.

**Independent Test**: The same test fails when the remainder is not four rows or any remainder count is not 31, including when the four names differ from the golden tie names.

### Implementation for User Story 2

- [X] T005 [US2] Extend `test_screen_1_top_settlements` in `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` per `specs/036-top-settlement-ties/contracts/top-settlement-ties.md`. After the stable asserts, call `_tie_count` on the golden map. Build the UI rows whose names are not in the stable set. Assert that map has length 4 and every value equals the tie count. On the current golden file that count is 31, read from the file rather than hard-coded. The failure text includes the remaining map. Do not require יגל, גינתון, צפרייה, or חיפה. Do not edit `test_screen_1_filtered_metrics`. Comments inside the function are English

**Checkpoint**: The ranking test accepts any four settlements at the golden tie count and still requires the six stable counts.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Confirm the slice did not edit the golden file, the page, or the other Screen 1 tests, then collect and run the ranking test

- [X] T006 [P] Confirm `data/alerts/db_sanity_am_kalavi.yaml`, `pages/status_picture/status_picture_page.py`, `core/`, `tests/conftest.py`, `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, and `pages/alerts_analysis/population_page.py` have no edits from this slice. Confirm `test_screen_1_global_metrics`, `test_screen_1_filtered_metrics`, and `test_screen_1_alerts_by_category` in `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` are unchanged
- [X] T007 [P] Run `python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py --collect-only` from `specs/036-top-settlement-ties/quickstart.md` and confirm the collected tests are `test_screen_1_global_metrics`, `test_screen_1_filtered_metrics`, `test_screen_1_alerts_by_category`, and `test_screen_1_top_settlements`
- [X] T008 Run `python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py::test_screen_1_top_settlements -v` from `specs/036-top-settlement-ties/quickstart.md`. Portal auth is required. A pass means the six stable settlements match and four other rows are each 31. An empty reader still skips with `Missing Page Object reader for top_10_settlements`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks both user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on User Story 2
- **User Story 2 (Phase 4)**: Depends on Foundational and on User Story 1, because both edit `test_screen_1_top_settlements`
- **Polish (Phase 5)**: Depends on both user stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T003. Uses `_stable_rankings` and replaces `_assert_golden_entries` for the ranking map
- **User Story 2 (P1)**: Starts after T004. Uses `_tie_count` and the stable names already asserted in that function

### Within Each User Story

- This feature is the test change. There is no separate production module to write first
- User Story 2 edits the same function User Story 1 edits, so it cannot start before T004

### Parallel Opportunities

- T001 and T002 read different files and can run together
- T004 and T005 edit `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`, so they stay sequential
- T006 and T007 can run together after T005. T008 waits until collection succeeds

---

## Parallel Example: Setup

```bash
# After the feature pin is known, the golden file and the current test can be read together:
Task: "Confirm .specify/feature.json pins specs/036-top-settlement-ties"
Task: "Confirm the golden top-10 partition and the current ranking assert"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete T004 so the six stable counts match and the golden tie names are not required
3. **STOP and VALIDATE**: a chart that swaps the 31-alert names no longer fails only for those names

### Incremental Delivery

1. Setup confirms the pin and the current golden partition
2. Foundational adds the partition helpers without changing test behavior
3. User Story 1 drops the full-name equality check
4. User Story 2 requires exactly four remaining rows at the golden tie count
5. Phase 5 collects the module and runs the ranking test

### Parallel Team Strategy

One person owns `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` for T003, T004, and T005. Those three stay in that order. T001 and T002 can be done by anyone before T003.

---

## Notes

- [P] tasks use different files or are read-only checks
- [US1] and [US2] both land in `test_screen_1_top_settlements`
- Do not hard-code the six settlement names or the tie count `31`
- Do not edit the golden YAML file
- Fleet smoke is not a gate for this slice
