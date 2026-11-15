# Feature Specification: Alerts Population Page

**Feature Branch**: `019-alerts-population-page` (spec directory; git checkout is not switched by planning)

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Alerts Analysis Page 2 - Population & Distribution (UI Invariants & Contract). Validate UI mechanics, math invariants, and state snapshots before SQL parity. Scope every metric with the page title. Strip dynamic date suffixes. Two-series settlement population chart. Snapshot and clear. Day/night and cross-chart sums. Population bounds. SQL stubs only."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open the population page from the alerts report (Priority: P1)

A validation author opens the Alerts Analysis report and lands on the second page, the population and distribution page, without a second catalog search. Page 1 tests still open the first page.

**Why this priority**: Every later check reads this page. If the suite stays on page 1, the new cards and charts are not the visuals under test.

**Independent Test**: The population suite opens the same catalog product as the alerts report, selects the second page, and shows a visual that exists only on that page. The existing alerts smoke and parity suite still opens the first page.

**Acceptance Scenarios**:

1. **Given** the Alerts Analysis report is the catalog product, **When** the population suite starts, **Then** the second report page is the active page before any assertion.
2. **Given** a page-1 alerts test, **When** it starts, **Then** it still opens the first page and does not select the population page.
3. **Given** the report was already open on the first page, **When** the population suite starts, **Then** it still ends on the second page.

---

### User Story 2 - Contract rows cannot collide with page 1 (Priority: P1)

A validation author adds this page's metrics to the alerts contract. Each metric is tied to this page's title, so a repeated card title is not read from a page-1 section.

**Why this priority**: Page 1 already uses titles such as the warned-population card. A second page that reuses a title without a page scope will check the wrong visual.

**Independent Test**: Every new metric's scope is the page title and no other string. No new metric name contains a dynamic date suffix. The two settlement-population series are separate metrics.

**Acceptance Scenarios**:

1. **Given** the population page's metrics, **When** the contract is loaded, **Then** each one's scope is the exact page-tab title and none use a page-1 section name or a blank scope.
2. **Given** a visual whose on-screen title grows a date suffix such as `התרעות לפי מחוז בין ה...`, **When** the contract names it, **Then** the name is the stable prefix `התרעות לפי מחוז`.
3. **Given** the chart `אוכלוסייה לפי יישוב`, **When** the contract is loaded, **Then** one metric uses the series position for `מותרעות` and another uses the series position for `לא מותרעות`.

---

### User Story 3 - Clear returns the page to its arrival state (Priority: P1)

A validation author records the three population cards and the chart totals as soon as the page is ready, changes the date, day/night, and numeric-range slicers, clears, and sees the same numbers again.

**Why this priority**: Slicer bugs often leave a stale total. A snapshot proves the clear control, not a single hard-coded expected value.

**Independent Test**: After the listed slicer changes, clear restores every snapshotted card and every snapshotted total to the same number. The interaction must change at least one of those numbers before clear, so a no-op slicer cannot pass.

**Acceptance Scenarios**:

1. **Given** the population page has just become ready, **When** the snapshot is taken, **Then** it stores the three card values and the totals of the distribution charts.
2. **Given** that snapshot, **When** the between-dates control, the day/night controls, and the numeric range 0 through 349 are applied, **Then** at least one snapshotted figure changes.
3. **Given** those slicers were applied, **When** clear is clicked, **Then** every snapshotted card and total equals the arrival snapshot exactly, including zeros.

---

### User Story 4 - Distribution totals agree without the warehouse (Priority: P1)

A validation author checks that the page's own numbers obey the population and time splits. No database query is required.

**Why this priority**: These identities can fail while SQL is still unknown. They are the gate that runs before parity.

**Independent Test**: With slicers cleared, the day total plus the night total equals the untoggled total; the 24-hour chart, the dates chart, and the district chart in Sum mode share one total; warned and unprotected populations are each at most the total population.

**Acceptance Scenarios**:

1. **Given** day/night is off, **When** the dates-chart total is taken, then again with only day on, then again with only night on, **Then** the day total plus the night total equals the untoggled total.
2. **Given** slicers are cleared and the district chart is in Sum mode, **When** the three distribution totals are read, **Then** the 24-hour chart total, the dates-chart total, and the district-chart total are equal.
3. **Given** the three population cards, **When** they are read, **Then** warned population is less than or equal to total population and unprotected population is less than or equal to total population.

---

### User Story 5 - Warehouse stubs are named, not compared (Priority: P2)

A validation author can see the future SQL rules next to a placeholder query for each new metric. This feature does not claim the UI matches the warehouse.

**Why this priority**: The identities in story 4 must stay trustworthy even when the warehouse statement is still a placeholder. Mixing them into today's parity run would fail for the wrong reason.

**Independent Test**: Each new metric points at a placeholder statement. Comments record half-open dates, one grouping level at a time, and the average-versus-sum rule. The existing page-1 parity run does not execute these placeholders.

**Acceptance Scenarios**:

1. **Given** a new card metric, **When** its query is inspected, **Then** it is a placeholder that returns 0 and it is not compared to the UI in this feature.
2. **Given** a new chart metric, **When** its query is inspected, **Then** it returns no category rows, and the comment states the future date, grouping, and average rules.
3. **Given** the existing last-30-days parity test, **When** it runs, **Then** it does not read or query the population-page metrics.

---

### Edge Cases

- A missing bar is not the number 0. An empty chart is not a total of 0. The sum and snapshot tests fail closed on an empty distribution chart.
- A rendered 0 is a real value and must be restored exactly by clear.
- Day and night are applied one at a time. The untoggled state is both off. The test does not assume warned plus unprotected equals total population.
- The district comparison uses Sum mode only. Average mode is documented for a later query and is not an identity in this feature.
- The page title must not be a substring of a page-1 scope, and a page-1 scope must not be a substring of the page title. Otherwise a scoped lookup can hit the wrong group.
- Dynamic suffixes that begin with `בין` are removed from contract names. The static page-1 chart that already contains `ביממה הנוכחית והקודמת` is unchanged.
- Clear is the report's clear-all control. The snapshot is the state on arrival, not a second hard-coded baseline.
- If applying the between-dates control, day/night, and the 0–349 range changes nothing, the clear test fails. A restore of an untouched page is not evidence.
- Connection errors and skip markers on the existing parity test stay as they are. This feature does not add a skip.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The population suite MUST open the Alerts Analysis catalog product and then select the second report page before assertions. Page-1 tests MUST keep opening the first page.
- **FR-002**: The second page MUST be represented by its own page object under `pages/alerts_analysis/`. It MUST reuse portal login, catalog search, iframe wait, and last-refresh behavior. It MUST NOT copy those steps.
- **FR-003**: Every new metric MUST set `scope` to the exact accessible name of this report page. That string MUST be defined once and reused. It MUST NOT be a page-1 section scope, and it MUST NOT be blank.
- **FR-004**: Contract `name` values MUST be stable title prefixes. A displayed suffix that starts with `בין` MUST be omitted. The district chart name MUST be `התרעות לפי מחוז`.
- **FR-005**: `אוכלוסייה לפי יישוב` MUST be two chart metrics on this page scope. One series position MUST be the `מותרעות` series and the other MUST be the `לא מותרעות` series. The positions MUST differ.
- **FR-006**: The three population cards MUST be readable as total population, warned population, and unprotected population. Their contract names MUST be the stable on-screen prefixes, not a date suffix.
- **FR-007**: A snapshot MUST record the three card values and the totals of the 24-hour chart, the dates chart, the district chart, and both series of `אוכלוסייה לפי יישוב` at arrival.
- **FR-008**: The clear test MUST apply a between-dates window, the day control, the night control, and the numeric range whose bounds are 0 and 349, then clear. At least one snapshotted figure MUST change before clear. After clear, every snapshotted figure MUST equal the arrival snapshot.
- **FR-009**: With day/night otherwise cleared, the dates-chart total with only day on plus the dates-chart total with only night on MUST equal the dates-chart total with day/night off.
- **FR-010**: With slicers cleared, the 24-hour chart total, the dates-chart total, and the district-chart total while that chart is in Sum mode MUST be equal.
- **FR-011**: Warned population MUST be less than or equal to total population. Unprotected population MUST be less than or equal to total population. This feature MUST NOT require those two parts to sum to the total.
- **FR-012**: A chart total MUST add only numeric cells. A missing cell MUST NOT be treated as 0. An empty chart MUST fail the sum tests.
- **FR-013**: New card queries MUST be the placeholder `SELECT 0`. New chart queries MUST return no rows. Comments on those placeholders MUST state: dates use `>=` and `<` (half-open); each result is one grouping level from district down to settlement, never a parent added to its children; Sum is the grouped sum; Average is that sum divided by the group count. This feature MUST NOT replace the placeholders with warehouse SQL and MUST NOT compare them to the UI.
- **FR-014**: The existing page-1 parity run MUST ignore metrics whose scope is this page title. It MUST NOT gain a skip, and it MUST NOT catch connection errors.
- **FR-015**: Hebrew titles, the page title, slicer names, and series names MUST stay in the alerts page and the alerts contract. `core/` MUST NOT gain those strings. Inline comments in edited Python and YAML MUST be English only.
- **FR-016**: The coverage catalog MUST record the new metrics as UI checks plus unconfirmed placeholders.

### Key Entities

- **Population page**: The second page of the Alerts Analysis report. Its tab title is the scope of every metric on it.
- **Population card**: One of three numbers: total population, warned population, unprotected population.
- **Distribution chart**: The 24-hour chart, the dates chart, or the district chart `התרעות לפי מחוז`. Each has a total that is the sum of its numeric categories. The district chart has Sum mode and Average mode.
- **Settlement population chart**: `אוכלוסייה לפי יישוב`, with series `מותרעות` and `לא מותרעות`.
- **Arrival snapshot**: The three cards and the chart totals taken when the page becomes ready, before the clear test changes slicers.
- **Placeholder query**: A statement that stands in for future warehouse SQL and is not a parity assertion in this feature.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. It MUST NOT contain vehicles, district, fleet KPI/chart titles, or other report-specific labels. Generic last-refresh chrome (`הדשבורד עודכן לאחרונה ב:`) MAY live in Layer 0 and MUST be located by regex or text inside the report iframe, never by dashboard-specific CSS or visual ids.
- **AC-002**: The population page object MUST inherit or compose `ReportShell` rather than re-implement login, catalog search, iframe wait, visual-load timeout, or last-refresh verification.
- **AC-003**: Report-ready state for the population page MUST be supplied by that page (locator, predicate, or override), never hardcoded in `ReportShell`.
- **AC-004**: Public test-facing page-object APIs on the first alerts page and on the fleet page MUST keep their contracts unless tests are updated in the same change. The page-1 `dashboard` fixture MUST stay on the first page.
- **AC-005**: Layer 2 (`core/components/`) MUST remain report-agnostic. This feature MUST NOT add alerts titles, series names, or the page title to `core/`. Date-between, day/night, and numeric-range controls stay on the population page. Clear MUST use the existing generic clear-all control.
- **AC-006**: The population page MUST live in `pages/alerts_analysis/`. New placeholder SQL MUST live in `db/clients/alerts.py`. The contract MUST stay `data/alerts/alerts_contract.yaml`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The population suite is on the second page before its first assertion, and a page-1 alerts test still starts on the first page.
- **SC-002**: 100% of the new contract metrics use the page title as scope, and none of their names contain a `בין` suffix.
- **SC-003**: After the date, day/night, and 0–349 range changes, clear restores 100% of the snapshotted cards and totals to the arrival values.
- **SC-004**: The day-plus-night identity, the three-chart identity in Sum mode, and both population bounds hold on one cleared page load.
- **SC-005**: The existing page-1 parity test executes none of the new metrics. Fleet and `core/` behavior are unchanged because those modules are not edited.
- **SC-006**: Each new card placeholder is `SELECT 0`, each new chart placeholder returns no rows, and the three future SQL rules are written in comments beside those placeholders.

## Assumptions

- The validation author is the audience. "Page 2" means the second page inside the existing Alerts Analysis report (`ניתוח התרעות`), not a new catalog product.
- The page-tab accessible name is not stored in the repo today. It is copied from the live tab into one constant during implementation. The plan does not invent a Hebrew page title.
- The 24-hour chart and the dates chart keep their live title prefixes after the `בין` suffix is removed. Those prefixes are copied from the report during implementation. The district chart and the settlement chart use the titles given in the request.
- The three cards are the total, warned, and unprotected population figures on this page. Their visible titles are copied as stable prefixes. Warned plus unprotected is not assumed to equal the total.
- Day and night partition the same dates-chart total. The numeric range used to disturb the page is 0 through 349 inclusive.
- Sum mode is a control on the district chart. The cross-chart identity reads that chart only in Sum mode. Average mode is a later SQL rule, not a UI identity here.
- Power BI mounts the active report page. Scoped reads run only after the population page is active.
- Placeholder chart SQL cannot be a one-column `SELECT 0` because a chart result needs a label column and a value column, and a blank label is a contract error. Card placeholders remain `SELECT 0`. Chart placeholders return no rows so they are never executed as a fake category.
- `label` on a metric remains documentation. The engine continues to ignore it. Series identity for parity later is `series_index`. A UI test still checks that those indexes are the `מותרעות` and `לא מותרעות` legend names.
- Existing page-1 metrics, their SQL, and their scopes stay. This feature does not drill the hierarchy and does not add tooltip checks.
