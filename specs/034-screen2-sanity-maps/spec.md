# Feature Specification: Screen 2 Sanity Maps

**Feature Branch**: `feature/reportportal-integration` (spec directory `034-screen2-sanity-maps`; git checkout stays put)

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "Expand the population sanity tests to the remaining Screen 2 golden-record sections: settlement population, geographic hierarchy (sum and daily average), alerts by date, and alerts by hour (sum and daily average). Use the page object's existing chart readers. If a reader is missing, add a basic one or skip that assertion. Do not break the tests already in `test_data_validation.py`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Settlement population matches the golden record (Priority: P1)

A validation author sets the Screen 2 date range and checks each settlement in the golden record against the warned series of the settlement chart.

**Why this priority**: The settlement chart already has a category reader. This story needs no new page method.

**Independent Test**: `test_alerted_population_by_settlement_matches_db` sets the golden date range, reads `אוכלוסייה מותרעת לפי יישוב` the same way the invariant test reads that chart, and compares each golden settlement to the warned series.

**Acceptance Scenarios**:

1. **Given** the golden date range is applied, **When** the settlement chart is read, **Then** each name under `alerted_population_by_settlement.values` equals the warned-series value for that name.
2. **Given** the two card tests already in the module, **When** this story is added, **Then** those two functions are unchanged.

---

### User Story 2 - District hierarchy sum and daily average match (Priority: P1)

A validation author sets the same date range, switches the district chart between Sum and daily average, and checks the district names in the golden record.

**Why this priority**: Sum and daily average already exist as `set_district_aggregation`. The district chart is the מחוז level. The missing piece is a label-to-value map, not a new chart.

**Independent Test**: Two tests set the date range, select `sum` or `average`, and compare `alerts_by_hierarchy.mahoz` to the district labels. An empty label map skips only that test.

**Acceptance Scenarios**:

1. **Given** Sum mode, **When** district labels are read, **Then** `מחוז צפון` is `12` and `פיקוד דרום` is `1`.
2. **Given** daily-average mode, **When** district labels are read, **Then** both golden district names are `1`.

---

### User Story 3 - Dates and hours match the golden record (Priority: P2)

A validation author sets the same date range and checks the golden date rows and hour buckets.

**Why this priority**: The page can total these charts. It cannot yet return a date or an hour as a key. Those maps are new basic readers. A reader that cannot produce keys skips only that test.

**Independent Test**: `test_alerts_by_date_matches_db` compares `alerts_by_date.values`. `test_alerts_by_hour_sum_matches_db` and `test_alerts_by_hour_daily_avg_matches_db` compare the two hour maps.

**Acceptance Scenarios**:

1. **Given** the dates table can be keyed by its row header, **When** the date test runs, **Then** each golden date equals the alerts count for that date.
2. **Given** an hour mark label contains an `HH:MM` token, **When** the hour-sum test runs, **Then** each golden hour equals that bucket's sum.
3. **Given** no reader can separate the hour daily average from the district toggle, **When** the hour daily-average test runs, **Then** it skips with `Missing page object method for hour daily_avg`.

---

### User Story 4 - Unmapped hierarchy levels do not fail the suite (Priority: P2)

נפה, רשות, and יישוב have golden rows. The population page has no control that selects those levels.

**Why this priority**: A guessed drill would change the district chart without a known control. Skipping those levels keeps the suite green while the gap stays visible.

**Independent Test**: One test per missing level calls `pytest.skip("Missing page object method for hierarchy level <level>")` and does not click the page.

**Acceptance Scenarios**:

1. **Given** no hierarchy-level method exists, **When** the נפה, רשות, and יישוב tests run, **Then** each one skips and the settlement, district, date, and hour tests still run.

---

### Edge Cases

- `test_global_metrics_match_db` and `test_filtered_population_matches_db` stay byte-for-byte in behavior. Their assertions are not edited.
- `pytest.skip` applies to one new test. It does not wrap the two existing tests.
- Golden alert dates are in September 2023. The screen date range is `2026-09-01` through `2026-10-18`. The date test still asserts the file. This slice does not edit the YAML.
- Screen 1 stays out of scope.
- Comments inside new and edited functions are English.
- `core/` and `tests/ui/` stay unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: New checks MUST be added only in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`. The two existing test functions MUST keep their steps and assertions.
- **FR-002**: Every new test MUST set `screen_2_alerts_analysis.date_range` through the existing `to_page_date` helper and `set_date_range`.
- **FR-003**: Settlement checks MUST use `Chart.read` on `SETTLEMENT_CHART` with `scope=PAGE_TITLE`, the same construction as `test_settlement_series_match_legend`, and the warned series named by `WARNED_SERIES`.
- **FR-004**: מחוז checks MUST call `set_district_aggregation("sum")` and `set_district_aggregation("average")` in separate tests. They MUST compare `alerts_by_hierarchy.mahoz.sum` and `.daily_avg`.
- **FR-005**: The page MUST gain a basic district label reader only if the current public methods cannot return name-to-value rows. `chart_total` MUST keep returning a single total.
- **FR-006**: נפה, רשות, and יישוב MUST skip with `pytest.skip("Missing page object method for hierarchy level <level>")` until a level-selection method exists. This slice MUST NOT invent that click.
- **FR-007**: The page MUST gain a basic date-to-count reader that reuses the dates-table path and leaves the table before returning. The date test compares `alerts_by_date.values`.
- **FR-008**: The page MUST gain a basic hour-bucket reader from the hour chart's SVG labels. The sum test compares `alerts_by_hour.sum`. The daily-average hour test skips with `pytest.skip("Missing page object method for hour daily_avg")` when no hour-scoped average reader exists.
- **FR-009**: A new reader that returns no labels MUST skip that test with `pytest.skip("Missing page object method for <metric>")`. It MUST NOT fail the module.
- **FR-010**: Comments inside functions MUST be English.
- **FR-011**: This feature MUST NOT modify `tests/ui/` or `core/`.

### Key Entities

- **Golden screen**: `dashboard_sanity_checks.screen_2_alerts_analysis` in `data/alerts/db_sanity_am_kalavi.yaml`.
- **Settlement map**: `metrics.alerted_population_by_settlement.values`.
- **Hierarchy maps**: `metrics.alerts_by_hierarchy` levels `mahoz`, `nafa`, `rashut`, `yeshuv`, each with `sum` and `daily_avg`.
- **Date map**: `metrics.alerts_by_date.values`.
- **Hour maps**: `metrics.alerts_by_hour.sum` and `.daily_avg`.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: `core/portal` and `core/components` stay unchanged. `Chart.read` is called as it exists.
- **AC-002**: New readers live on `pages/alerts_analysis/population_page.py`. They do not change `clear_filters`, `set_date_range`, `read_card`, `chart_total`, or `set_district_aggregation` signatures.
- **AC-003**: Tests call page methods or `Chart.read`. They do not add their own Power BI locators.
- **AC-004**: `tests/ui/alerts_analysis_dashboard/` stays unchanged.
- **AC-005**: The golden file stays where it is. `core/` does not load it.
- **AC-006**: No report SQL is added.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The two existing sanity tests still pass.
- **SC-002**: Settlement rows and מחוז sum and daily average are asserted against the golden maps, or the single test whose reader returns no labels is skipped.
- **SC-003**: נפה, רשות, and יישוב are skipped with the missing-method message and do not fail the run.
- **SC-004**: The edit list is the sanity test module plus, where a reader is missing, `pages/alerts_analysis/population_page.py`. `tests/ui/` and `core/` are absent.

## Assumptions

- The warned settlement series is `WARNED_SERIES` (`מותרעת`), which is the series the invariant test treats as the first series.
- `set_district_aggregation("average")` is the daily-average mode (`ממוצע ליום`) for the district chart only.
- The visible district chart is the מחוז level because its title is `התרעות לפי מחוז`.
- Golden comparison for a map is: every golden key is present and equal. Extra UI rows do not fail the test.
- Date labels on the page may be `DD/MM/YYYY`. The test normalizes those to `YYYY-MM-DD` before comparing them to the file.
- Hour labels may include `HH:MM`. The test compares those tokens to the golden keys.
- Portal auth is required to pass. Collection is not.
