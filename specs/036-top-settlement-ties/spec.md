# Feature Specification: Top Settlement Tie Assertion

**Feature Branch**: `feature/reportportal-integration` (spec directory `036-top-settlement-ties`; git checkout stays put)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Make `test_screen_1_top_settlements` resilient when several settlements tie at 31 alerts and Power BI shuffles those names. Do not edit `data/alerts/db_sanity_am_kalavi.yaml`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stable settlements keep their golden counts (Priority: P1)

A validation author runs the Screen 1 ranking check. Settlements whose golden count is 32 or higher must still appear with that exact count, even when the last four chart rows change names.

**Why this priority**: Those six counts are stable on the live chart. The failure is only the tie at 31.

**Independent Test**: `test_screen_1_top_settlements` loads `top_10_settlements.values`, keeps every entry whose count is at least 32, and asserts each of those names and counts on the UI map.

**Acceptance Scenarios**:

1. **Given** the golden ranking, **When** the test partitions it, **Then** the stable set is ראשון לציון `39`, תל אביב-יפו `36`, רמת השרון `35`, נתניה `34`, ראש העין `32`, and רמלה `32`.
2. **Given** the UI map from the ranking chart, **When** the stable set is checked, **Then** each of those names is present with its golden count.

---

### User Story 2 - The four tie slots are count 31 (Priority: P1)

The same test treats every UI row that is not in the stable set as a tie slot. There must be four of them, and each count must be 31. The settlement names in those slots are not compared to the golden names.

**Why this priority**: Power BI reorders equal counts on each load, so requiring יגל, גינתון, צפרייה, and חיפה fails when another settlement with 31 alerts takes a slot.

**Independent Test**: After the stable names are removed from the UI map, the remaining map has length 4 and every value is 31.

**Acceptance Scenarios**:

1. **Given** a UI map that contains the six stable settlements plus four other rows, **When** the tie check runs, **Then** those four rows each equal 31.
2. **Given** a UI map whose tie slots use different names than the golden file, **When** the tie check runs, **Then** the test still passes.
3. **Given** a tie slot whose count is not 31, or a remaining map whose length is not 4, **When** the tie check runs, **Then** the test fails.
4. **Given** the ranking reader returns an empty map, **When** the test runs, **Then** it skips with `Missing Page Object reader for top_10_settlements`.

---

### Edge Cases

- `test_screen_1_filtered_metrics` is not the ranking check. It keeps asserting only the two range cards.
- `test_screen_1_global_metrics` and `test_screen_1_alerts_by_category` stay as they are.
- `data/alerts/db_sanity_am_kalavi.yaml` is not edited.
- The page object, `core/`, the Screen 2 sanity module, and `tests/conftest.py` are not edited.
- Comments inside the edited test function are English.
- An empty ranking map still skips. A partial map does not skip.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Change only `test_screen_1_top_settlements` in `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`.
- **FR-002**: Partition `top_10_settlements.values` from the golden file. Entries with a count of 32 or higher are the stable set. The current file yields the six settlements named in User Story 1.
- **FR-003**: Each stable name MUST be present in the UI map with that exact count. The test MUST NOT hard-code those six names or their counts.
- **FR-004**: UI rows whose names are outside the stable set MUST number exactly four, and each count MUST be 31.
- **FR-005**: The test MUST NOT require the golden tie names (יגל, גינתון, צפרייה, חיפה).
- **FR-006**: An empty UI map MUST still call `pytest.skip("Missing Page Object reader for top_10_settlements")`.
- **FR-007**: `test_screen_1_filtered_metrics`, the global-metrics test, and the category test MUST stay unchanged.
- **FR-008**: Do not edit `data/alerts/db_sanity_am_kalavi.yaml`, `pages/status_picture/status_picture_page.py`, `core/`, or the Screen 2 sanity module.

### Key Entities

- **Stable ranking entry**: A golden settlement whose `top_10_settlements.values` count is 32 or higher. Name and count must both match the UI.
- **Tie slot**: A UI settlement that is not in the stable set. Four slots are required. The count is 31. The name is not compared to the golden file.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` are not edited.
- **AC-002**: `StatusPicturePage` is not edited. `read_top_10_settlements()` keeps its name and return type.
- **AC-003**: The ranking reader stays on the status-picture page. The test does not add locators.
- **AC-004**: The other three Screen 1 tests keep their assertions.
- **AC-005**: `core/` does not load `data/alerts/`.
- **AC-006**: No new page and no new SQL client.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a chart whose last four rows are any settlements with 31 alerts, `test_screen_1_top_settlements` passes when the six stable counts match.
- **SC-002**: The same test fails when a stable count is wrong, when fewer or more than four rows sit outside the stable set, or when one of those rows is not 31.
- **SC-003**: The golden YAML file is byte-for-byte unchanged.
- **SC-004**: The other three Screen 1 tests keep their current assertions.
- **SC-005**: Fleet smoke is not a gate. This slice does not edit Layer 0, Layer 2, or the fleet page.

## Assumptions

- The live ranking chart returns one name-to-count map of ten rows after the existing page reader scrolls the chart.
- The six golden counts at or above 32 stay unique and stable. Only the four rows at 31 change names between loads.
- The tie count 31 is the value on every golden row below 32. The test reads that value from the golden file rather than embedding a second settlement list.
- Portal auth remains required to run the test. This plan does not run the browser.
