# Feature Specification: Complete Alerts DB Sanity Validations

**Feature Branch**: `feature/reportportal-integration` (spec directory `040-alerts-db-sanity-completion`; git checkout stays put)

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "Complete the missing UI vs. Golden YAML sanity coverage for the Alerts dashboards (Screens 1 & 2). Screen 2: read and validate the missing daily averages for `alerts_by_hierarchy.nafa.daily_avg`, `rashut.daily_avg`, and `yeshuv.daily_avg`. Screen 1: for tied `top_10_settlements` (e.g. 31 alerts), extract and verify the exact settlement names from the UI instead of only the row count. Load expected metrics only from the YAML. Increase locator timeouts for Power BI rendering to prevent `LoadTimeoutError`. Do NOT touch the fleet module. English-only comments inside functions."

## Clarifications

### Session 2026-11-01

- Q: Screen 1 feature 036 deliberately removed exact-name checks on the four tie slots because Power BI reorders equal counts on each load. This feature reverses that. How are tie names compared? → A: Order-independent set equality between the UI tie slot names and the golden tie names (`top_10_settlements` entries whose count equals the tie value). The golden names are read from the YAML, not hard-coded.
- Q: Does Screen 2 daily-average coverage need a new page-object reader? → A: No. `set_hierarchy_level(level)`, `set_district_aggregation("average")`, and `read_district_labels()` already exist and already back the `mahoz.daily_avg` test. The three new levels reuse them.
- Q: Where does the locator timeout increase live? → A: In the two Alerts domain page objects (`StatusPicturePage`, `AlertsPopulationPage`), which already own a hard-coded `self.timeout`. `core/` is not edited.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Screen 2 nafa daily averages match the golden record (Priority: P1)

A validation author opens the Alerts Analysis population page, applies the Screen 2 golden date range, selects the נפה hierarchy level, switches the district chart to the per-day average, and compares each nafa name to `alerts_by_hierarchy.nafa.daily_avg`.

**Why this priority**: The nafa sum is already covered; the daily average for the same level is the first missing surface and the smallest increment of value.

**Independent Test**: Run only the nafa daily-average test with portal auth. It passes when every golden nafa daily-average name and value appears on the chart in average mode.

**Acceptance Scenarios**:

1. **Given** the Screen 2 golden range and the נפה level, **When** the district chart is set to the per-day average, **Then** נפת חירם reads `1` and חטמ'ר צפונית - 7643 reads `1`.
2. **Given** a level control that is not visible or a reader that returns nothing, **When** the test runs, **Then** it skips with a message that names the missing reader, and does not fail.

---

### User Story 2 - Screen 2 rashut and yeshuv daily averages match the golden record (Priority: P1)

The same author repeats the average-mode comparison for the רשות and יישוב levels against `alerts_by_hierarchy.rashut.daily_avg` and `alerts_by_hierarchy.yeshuv.daily_avg`.

**Why this priority**: These two levels close the remaining Screen 2 hierarchy gap. They share the nafa pattern, so they ship together.

**Independent Test**: Run the rashut and yeshuv daily-average tests. Each passes when every golden daily-average name and value for that level appears in average mode.

**Acceptance Scenarios**:

1. **Given** the רשות level in average mode, **When** the chart is read, **Then** גליל עליון, מבואות החרמון, רג'ר, and שער הנגב each read `1`.
2. **Given** the יישוב level in average mode, **When** the chart is read, **Then** every golden yeshuv daily-average name (הגושרים, יובל, מעיין ברוך, בית הלל, דפנה, מלכייה, מנרה, נחל עוז, רג'ר) reads `1`.
3. **Given** a level that is not reachable, **When** the test runs, **Then** it skips and names the missing reader.

---

### User Story 3 - Screen 1 tied settlements are verified by exact name (Priority: P1)

A validation author runs the Screen 1 ranking check. The settlements whose golden count stays above the tie keep their exact name-and-count assertions. The four rows that share the tie count are now checked by their exact names drawn from the UI, compared to the golden tie names, instead of only counting four rows.

**Why this priority**: The request explicitly strengthens the tie slots from a count-only check to a name check, which catches a wrong settlement appearing in a tie slot.

**Independent Test**: Run `test_screen_1_top_settlements`. It passes when the stable names and counts match and the UI tie-slot names equal the golden tie names as a set.

**Acceptance Scenarios**:

1. **Given** the golden ranking, **When** the test partitions it, **Then** the stable set (count above the tie) keeps its exact names and counts.
2. **Given** the UI ranking map, **When** the stable names are removed, **Then** the remaining UI names equal the golden tie names (יגל, גינתון, צפרייה, חיפה) as an unordered set, each with the tie count.
3. **Given** the ranking reader returns an empty map, **When** the test runs, **Then** it skips with `Missing Page Object reader for top_10_settlements`.

---

### User Story 4 - Power BI rendering has a larger locator budget (Priority: P2)

A validation author runs the Alerts sanity suite on a cold Power BI iframe. Visuals that take longer than the previous budget to render no longer fail with `LoadTimeoutError`; the larger budget lets them appear.

**Why this priority**: The missing-coverage tests above add more visual reads. A larger budget reduces false `LoadTimeoutError` failures without changing any assertion.

**Independent Test**: With auth and a cold load, the Screen 1 and Screen 2 sanity tests reach their assertions rather than raising `[LOAD_TIMEOUT]`.

**Acceptance Scenarios**:

1. **Given** the Alerts page objects, **When** the suite runs, **Then** the Alerts locator/navigation timeout is larger than the previous 60s value.
2. **Given** a visual that never renders, **When** the budget is exhausted, **Then** the test still raises `LoadTimeoutError` so a real load failure is not hidden.

---

### Edge Cases

- A golden daily-average value that is not a whole number cannot be read by the existing integer reader; the current golden values for these three levels are all `1`, so this does not occur in this slice.
- A level control (נפה / רשות / יישוב) that is not visible makes the test skip with the missing-reader message; it does not fail.
- If a tie-slot settlement in the UI is not one of the golden tie names, User Story 3 fails and names the drift.
- A tie count other than the golden tie value, or a tie-slot count that is not uniform, fails.
- The golden file `data/alerts/db_sanity_am_kalavi.yaml` is read only; it is not edited.
- Fleet modules (`pages/fleet_dashboard/`, `tests/ui/fleet_dashboard/`, `tests/sanity/fleet_dashboard/`, `db/clients/fleet.py`) are not edited.
- Comments inside new or edited functions are English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Expected values MUST be read only from `data/alerts/db_sanity_am_kalavi.yaml`. No metric name or count is hard-coded in the test or the page object.
- **FR-002**: Three new Screen 2 tests MUST compare the per-day-average district chart to `alerts_by_hierarchy.nafa.daily_avg`, `alerts_by_hierarchy.rashut.daily_avg`, and `alerts_by_hierarchy.yeshuv.daily_avg`, each after selecting that level and `set_district_aggregation("average")`.
- **FR-003**: The Screen 2 daily-average tests MUST reuse the existing readers (`set_hierarchy_level`, `set_district_aggregation`, `read_district_labels`) and the existing golden-key assertion helper. They MUST skip with the existing missing-reader message when the level or reader is unavailable.
- **FR-004**: `test_screen_1_top_settlements` MUST keep exact name-and-count assertions for the stable set (golden count above the tie value) and MUST compute that set from the YAML, not from hard-coded names.
- **FR-005**: `test_screen_1_top_settlements` MUST assert that the UI tie-slot names equal the golden tie names as an unordered set, and that each tie-slot count equals the golden tie value.
- **FR-006**: `test_screen_1_top_settlements` MUST still skip with `Missing Page Object reader for top_10_settlements` when the ranking reader returns an empty map.
- **FR-007**: The Alerts page objects (`StatusPicturePage`, `AlertsPopulationPage`) MUST raise their locator/navigation timeout above the current 60s so Power BI rendering is less likely to raise `LoadTimeoutError`. A visual that never renders MUST still raise `LoadTimeoutError`.
- **FR-008**: This slice MUST NOT edit any fleet module, `core/`, the root `conftest.py`, or `data/`.
- **FR-009**: Comments inside new or edited functions MUST be English.

### Key Entities

- **Hierarchy daily average**: A level name (nafa / rashut / yeshuv) to whole-number per-day-average count, read from the district chart in average mode.
- **Stable ranking entry**: A golden `top_10_settlements` settlement whose count is above the tie value; name and count both match the UI.
- **Tie slot**: A UI ranking settlement at the tie count; its name is compared, as a set, to the golden tie names.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` are not edited.
- **AC-002**: The Alerts page objects keep inheriting `AlertsAnalysisPage` → `ReportShell`. Only the timeout value changes; no portal step is added.
- **AC-003**: Public reader names and return types on the Alerts pages are unchanged (`read_district_labels`, `set_hierarchy_level`, `set_district_aggregation`, `read_top_10_settlements`).
- **AC-004**: `core/` does not load `data/alerts/`. The sanity tests load the golden file.
- **AC-005**: No new report page and no new SQL client.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Three new Screen 2 tests exist and, with auth, pass when the nafa, rashut, and yeshuv daily-average names and values match the golden file.
- **SC-002**: A deliberately changed golden daily-average value makes its test fail with both the UI and golden values in the message.
- **SC-003**: `test_screen_1_top_settlements` fails when a UI tie slot holds a settlement that is not a golden tie name, and passes when the four golden tie names fill the four slots in any order.
- **SC-004**: The Alerts locator/navigation budget is larger than 60s, and a never-rendering visual still raises `LoadTimeoutError`.
- **SC-005**: Fleet smoke is not a gate for this slice: no fleet module, `core/`, or `data/` file is edited.

## Assumptions

- The golden daily-average values for nafa, rashut, and yeshuv are whole numbers (all `1` in the current file), so the existing integer reader can read them.
- The live ranking chart returns one ten-row name-to-count map after the existing reader scrolls, and the four tie rows carry the four golden tie names in some order.
- Portal auth is required to run the UI tests. This plan does not run the browser.
- Raising `self.timeout` on the Alerts pages is sufficient; the generic budget in `settings` is not changed because the Alerts pages override it.
