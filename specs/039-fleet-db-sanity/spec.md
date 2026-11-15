# Feature Specification: Fleet DB Sanity and Validation Tests

**Feature Branch**: `feature/reportportal-integration` (spec directory `039-fleet-db-sanity`; git checkout stays put)

**Created**: 2026-10-29

**Status**: Draft

**Input**: User description: "Implement Fleet DB Sanity & Validation Tests. Validate `data/fleet/db_sanity_all.yaml` for summary balances, breakdown integrity, category standard rates, and the credited-vehicle ledger. Keep validation generic and free of hardcoded environment state. Follow the alerts sanity pattern. UI checks use the existing fleet page. Error messages name the drift."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Summary balances hold (Priority: P1)

A validation author checks the fleet baseline: vehicles in use, vehicles received, vehicles transferred, and vehicles credited. The four counters come from the golden file. In use is not larger than received. The file does not treat received as the sum of in use, credited, and transferred.

**Why this priority**: Every later breakdown is checked against one of these counters. A wrong baseline makes the other checks meaningless.

**Independent Test**: Load the golden file and read `summary` only. No browser and no warehouse connection.

**Acceptance Scenarios**:

1. **Given** the golden file, **When** summary balances are checked, **Then** `total_vehicles_in_use`, `total_vehicles_received`, `vehicles_transferred`, and `vehicles_credited` are present and are whole numbers, and in use is less than or equal to received.
2. **Given** those four numbers, **When** the check runs, **Then** it does not require `total_vehicles_received` to equal in use plus credited plus transferred.

---

### User Story 2 - Breakdowns reconcile to the counters (Priority: P1)

A validation author checks that unit counts and pull-source counts each add up to vehicles in use, and that credit-reason counts add up to vehicles credited.

**Why this priority**: A chart can look plausible while its slices no longer match the card above it.

**Independent Test**: Sum each breakdown mapping and compare it to the matching summary counter. No browser.

**Acceptance Scenarios**:

1. **Given** `units_breakdown`, **When** its values are summed, **Then** the sum equals `summary.total_vehicles_in_use`.
2. **Given** `pull_source_breakdown`, **When** its values are summed, **Then** the sum equals `summary.total_vehicles_in_use`.
3. **Given** `credit_reasons_summary`, **When** its values are summed, **Then** the sum equals `summary.vehicles_credited`.

---

### User Story 3 - Category rates match the standard (Priority: P1)

A validation author checks each vehicle category's actual count against its standard and the published utilization rate. The rate is computed from actual and standard. Category names are not hard-coded in the checker.

**Why this priority**: The rate string is a derived figure. A pasted citation or a hand-edited percent can disagree with the two counts.

**Independent Test**: For every row under `vehicle_categories`, compute the rate and compare it to the stored rate. The sum of `actual` equals vehicles received.

**Acceptance Scenarios**:

1. **Given** a category row, **When** the rate is checked, **Then** it equals actual divided by standard, shown as a percent with two decimal places.
2. **Given** every category row, **When** `actual` values are summed, **Then** the sum equals `summary.total_vehicles_received`.
3. **Given** a standard of zero, **When** the rate is checked, **Then** the check fails and names that category. It does not divide by zero.

---

### User Story 4 - Credited ledger is complete (Priority: P1)

A validation author checks each credited or transferred asset row. Credit reason, credit date, pull source, unit, subunit, and vehicle number are filled in. The rows account for every credited vehicle, and the reasons match the reason summary.

**Why this priority**: The summary can be right while a row is missing a date or a vehicle number.

**Independent Test**: Walk `credited_vehicles_details` and compare reason counts to `credit_reasons_summary`. No browser.

**Acceptance Scenarios**:

1. **Given** the ledger, **When** rows are counted, **Then** the count equals `summary.vehicles_credited`.
2. **Given** a ledger row, **When** it is checked, **Then** credit reason, credit date (`DD/MM/YYYY`), pull source, unit, subunit, and vehicle number are present. Vehicle numbers are unique.
3. **Given** the ledger grouped by credit reason, **When** those counts are compared to `credit_reasons_summary`, **Then** every reason and count matches.

---

### User Story 5 - The open fleet report matches the golden baseline (Priority: P2)

A validation author opens the fleet report with slicers cleared and compares the four KPI cards, the unit chart, the pull-source chart, the credit-reason chart, the category actuals, and the credited-vehicle rows to the same golden file.

**Why this priority**: The file checks prove the contract is internally consistent. This story proves the report the author is looking at still shows that baseline.

**Independent Test**: With portal auth, open the fleet report, clear filters, and assert each surface against the loaded record. A missing chart visual skips only that chart's test. A value that is present and different fails with the golden value and the value read from the page.

**Acceptance Scenarios**:

1. **Given** a cleared fleet report, **When** the four KPI cards are read, **Then** received, in use, credited, and transferred match `summary`.
2. **Given** the unit, pull-source, and credit-reason charts, **When** each visible segment is read, **Then** its count matches the golden mapping for that segment.
3. **Given** a credited vehicle number from the ledger, **When** that number is searched on the credited-vehicles tab, **Then** the row shows that vehicle's reason, date, pull source, and unit metadata.

---

### Edge Cases

- `data/fleet/db_sanity_all.yaml` currently has `rate: "0.57%"[cite: 1]` (and the same suffix on the other three rates). That text is not valid YAML. The citation suffix is removed so the file loads. The percent values stay.
- Ledger pull sources and unit names are a finer grain than the in-use breakdowns. A ledger pull source does not have to be a key of `pull_source_breakdown`. A ledger unit does not have to be a key of `units_breakdown`.
- `vehicles_transferred` has no slice list in the file. Nothing is summed to that counter.
- Received is not required to equal in use plus credited plus transferred. Those credited and transferred counts come from different facts than the received count.
- Category standards are staffing standards. They are checked in the file. The category chart is asked only for actual counts.
- If a chart exposes no golden labels, that chart's UI test skips and names the chart. A label that is present with the wrong count fails. Structural tests do not skip.
- Quote characters in Hebrew labels (`"`, `״`) are treated as the same character when a UI label is compared to the file.
- The checker does not read `DB_ENVIRONMENT` and does not embed a district, a portal URL, or the numeric baselines. Baselines stay in the YAML.
- `core/`, the fleet page object, `tests/ui/`, `tests/e2e/`, and `db/clients/fleet.py` stay unchanged.
- Comments inside new functions are English.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A loader MUST read `data/fleet/db_sanity_all.yaml` as UTF-8 with `yaml.safe_load`. The path is relative to the repository, not to an environment variable.
- **FR-002**: The loader MUST require `summary`, `units_breakdown`, `pull_source_breakdown`, `vehicle_categories`, `credit_reasons_summary`, and `credited_vehicles_details`. A missing section fails with that section's name.
- **FR-003**: Summary checks MUST require the four counters in User Story 1, require them to be non-negative integers, and require in use ≤ received. They MUST NOT assert received = in use + credited + transferred.
- **FR-004**: Breakdown checks MUST assert the three sums in User Story 2. Keys and values come from the loaded mappings. Unit names and source names are not hard-coded.
- **FR-005**: Category checks MUST assert that the sum of `actual` equals `total_vehicles_received`, that each `standard` is a positive integer, and that each stored rate equals the computed percent (two decimal places, half up).
- **FR-006**: Ledger checks MUST require the six fields in User Story 4 on every row, unique vehicle numbers, a row count equal to `vehicles_credited`, and reason counts equal to `credit_reasons_summary`.
- **FR-007**: Failure messages MUST name the section, the key or vehicle, the actual value, and the expected value.
- **FR-008**: UI checks MUST open the existing fleet report, clear slicers and vehicle search, and compare page reads to the loaded record. They MUST NOT select a district or other slicer.
- **FR-009**: KPI binding is received → the received card, in use → the in-use card, credited → the credited card, transferred → the transferred/allocated card. Chart binding is units → the in-use unit chart, pull source → the in-use source chart, credit reasons → the credit-reason chart, category actuals → the category chart.
- **FR-010**: An empty chart read skips only that chart's UI test. A present label with a different count fails. Structural tests never skip for a missing visual.
- **FR-011**: New validation code lives with the fleet sanity suite. It MUST NOT be added under `core/`, `tests/helpers/`, or the root `conftest.py`.
- **FR-012**: This slice MUST NOT edit `core/`, `pages/fleet_dashboard/main_dashboard_page.py`, `tests/ui/`, `tests/e2e/`, or `db/clients/fleet.py`.
- **FR-013**: The only golden-file edit is removal of the trailing `[cite: …]` suffixes so each rate is a quoted percent string.

### Key Entities

- **Summary**: Four baseline counters — in use, received, transferred, credited.
- **Breakdown**: A name-to-count mapping (units, pull sources, or credit reasons) that must sum to one summary counter.
- **Vehicle category**: Category name, actual count, standard allocation, and utilization rate.
- **Credited vehicle row**: One ledger line with reason, date, pull source, unit, subunit, and vehicle number.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) stays report-agnostic. This slice does not edit it.
- **AC-002**: The fleet page keeps inheriting `ReportShell`. This slice does not add portal steps.
- **AC-003**: Report-ready state stays on the fleet page. This slice does not change it.
- **AC-004**: Public fleet page methods keep their names and arguments. UI tests call the methods that already exist.
- **AC-005**: `core/` does not load `data/fleet/`. The sanity suite loads the golden file.
- **AC-006**: No new report page and no new SQL. Live warehouse checks stay in the existing end-to-end suite.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The golden file loads with a YAML parser after the citation suffixes are removed, and the four stored rates still display as `0.57%`, `16.92%`, `34.24%`, and `10.74%`.
- **SC-002**: Structural checks pass on the current file: unit sum 358, pull-source sum 358, category actual sum 363, credit-reason sum 6, ledger length 6.
- **SC-003**: A deliberately changed counter, rate, or blank ledger field fails, and the message contains both the golden value and the value that drifted.
- **SC-004**: With a cleared report, each readable KPI and chart segment equals the golden value for that name. A visual that exposes no golden labels skips only its own UI test.
- **SC-005**: Fleet smoke is not a gate for this slice. `core/` and the fleet page object are not in the change.

## Assumptions

- The four summary keys map to the four fleet KPI cards already on the page: received, in use, credited (`רכבים שזוכו`), and transferred (`רכבים שווסתו`, the allocated card).
- "API" in the request means the existing page-object reads and a pure checker over the loaded file. This slice does not add an HTTP service and does not compare the golden snapshot to live SQL.
- The golden numbers are a baseline snapshot. They are allowed to differ from today's warehouse. The existing end-to-end suite remains the live SQL comparison.
- Portal auth is required for the UI tests and is not required for the structural tests.
- Hebrew UI text may use a different quotation mark than the file. Comparison normalizes those marks.
