# Phase 0 Research: Alerts Population Page

All items below were resolved against the current code (features 015, 016, 017, and 018) and the
feature request. No **NEEDS CLARIFICATION** remains.

## R1 — Page class, fixture, and the unknown tab title

- **Decision**: Add `pages/alerts_analysis/population_page.py` with class `AlertsPopulationPage`.
  The module name is snake case, matching `page.py` and `main_dashboard_page.py`. The class
  subclasses `AlertsAnalysisPage` so the catalog term stays `ניתוח התרעות` and portal steps stay
  on `ReportShell`. `PAGE_TITLE` is one class constant: the accessible name of the second
  report-page tab, copied from the live report during implementation. Do not invent that Hebrew
  string in the spec or the YAML ahead of the copy. `tests/ui/alerts_analysis_dashboard/conftest.py`
  gains `population_dashboard = bind_dashboard(AlertsPopulationPage)`. The existing `dashboard`
  fixture keeps `AlertsAnalysisPage`.
- **Rationale**: Feature 018 requires report pages under `pages/<report>/`. A PascalCase module
  filename would be the only one in `pages/`. Subclassing reuses search and the iframe without
  copying `navigate`. A second fixture is required because replacing `dashboard` would send
  page-1 smoke and parity onto page 2. `bind_dashboard` already opens whatever page class it is
  given, on the shared tab.
- **Alternatives considered**: `AlertsPopulationPage.py` as the filename. Rejected. It breaks the
  package import style used everywhere else. A new catalog search term. Rejected. The request
  says to navigate from the main alerts report. Switching the shared `dashboard` fixture.
  Rejected. Page-1 tests must stay on page 1 (FR-001, AC-004).

## R2 — How the suite lands on page 2

- **Decision**: Override `before_report_ready_check` to select the page tab whose accessible name
  is `PAGE_TITLE`, idempotently. Override `_report_ready_locator` to the stable district anchor
  `התרעות לפי מחוז` via `_iframe_phrase_locator`. Do not use the report product name as the ready
  signal: that phrase is already true on page 1.
- **Rationale**: `ReportShell.navigate` calls `before_report_ready_check` before every ready
  check, including the reuse path inside `_dashboard_ready`. If the report is sitting on page 1,
  the district anchor is not visible, so navigate does not treat the session as ready. After the
  tab click, the district anchor becomes the ready signal. `after_navigate` alone is not enough:
  the full-navigation path waits on the ready locator without calling `after_navigate` first.
- **Alternatives considered**: Clicking the tab only inside the test body. Rejected. The request
  says the suite setup performs the navigation, and a missed click would assert against page 1.
  Putting the tab label in `ReportShell`. Rejected. That is domain leakage.

## R3 — Scope is the page title, and `scope_host` must actually contain the visuals

- **Decision**: Every new metric's `scope` is exactly `AlertsPopulationPage.PAGE_TITLE`. Page-1
  rows keep their current scopes (`ירי רקטות וטילים`, `חדירת מחבלים`, `חדירת כלי טיס עוין`,
  `אוכלוסייה מותרעת`, `אזורי התרעה תחת ירי`, and blank). A unit test fails if `PAGE_TITLE` equals
  or is a substring of any page-1 scope, or the reverse. Implementation confirms that
  `scope_host` for `PAGE_TITLE` is a group that contains `התרעות לפי מחוז`. If the tab text is
  not a group name around the visuals, stop. Do not retarget `scope` to a section title and do
  not change `scope_host` in `core/`.
- **Rationale**: `scope_host` compiles `re.escape(scope)` with no anchors, then prefers
  `role=group` by accessible name and otherwise the first group whose text contains the scope.
  Page 1 already repeats titles such as `אוכלוסייה מותרעת`. The page title is the only scope the
  request allows for page 2. A substring collision would bind the wrong group. Feature 014 added
  scope for that collision, and this page is the next collision. Power BI's active page is the
  one mounted for the read; the scope still has to be a real group, not only a tab button.
- **Alternatives considered**: Leaving page-2 `scope` blank because the other page is unmounted.
  Rejected. The request says every metric uses the page title. Encoding the page name into
  `name`. Rejected. `name` is the visual title anchor; `scope` is the feature 014 disambiguator.
  Changing `scope_host` to require an exact accessible-name match. Rejected for this slice.
  That is a Layer 2 behavior change for every report.

## R4 — Titles, series indexes, and chart placeholders

- **Decision**: Contract names are stable prefixes. If the displayed title contains ` בין `, the
  name is the text before that marker. Known names are written now:

  - District chart: `התרעות לפי מחוז` (the request's example; not `התרעות לפי מחוז בין ה...`).
  - Settlement chart: `אוכלוסייה לפי יישוב`, twice.
    - `series_index: 0`, `label: מותרעות`
    - `series_index: 1`, `label: לא מותרעות`

  The 24-hour chart, the dates chart, and the three card titles are copied from the live page
  with the same `בין` rule. They are not guessed here. `label` stays documentation; the engine
  ignores it. A UI test reads `Chart.read(...).series` and requires index 0 to be `מותרעות` and
  index 1 to be `לא מותרעות`. If the live legend is the other way around, swap the two indexes
  in the YAML in that same change. The names stay the identity.

  Card SQL constant: `POPULATION_PAGE_KPI_STUB_SQL = "SELECT 0"`.
  Chart SQL constant: the feature 017 empty two-column statement (`WHERE 1 = 0`), named
  `POPULATION_PAGE_CHART_STUB_SQL`. Do not reuse `POPULATION_KPI_STUB_SQL` or
  `PERIOD_COMPARISON_CHART_SQL`, so a later real query can replace one page without the other.
- **Rationale**: `Chart._container` and `KPI` title lookup use an unanchored escaped pattern, so
  the stable prefix still matches a title that has grown a date suffix. `rows()` raises
  `ValueError` on a null or blank label, so a chart placeholder must return no rows rather than
  one row of nulls or a one-column `SELECT 0`. `series_index` is already the engine's series
  key (feature 015). Two YAML rows with the same name and scope and different indexes are two
  metrics; the loader does not collapse them.
- **Alternatives considered**: One YAML row that lists both series. Rejected. The engine compares
  one `series_index` per metric. Using `SELECT 0` for charts because the request said that
  phrase. Rejected for charts only. A one-column result is not a category/value row, and a null
  label fails `rows()`. Cards still use `SELECT 0`, as requested. Hard-coding series indexes
  with no legend check. Rejected. The indexes would silently follow the wrong series.

## R5 — Snapshot, clear, and the slicers Layer 2 does not operate

- **Decision**: `AlertsPopulationPage` composes `Slicer` and calls `clear_all` for the restore
  step. The clear control stays the generic button (`נקה את כל` / `Clear all slicers` /
  `Clear all filters`). Between-dates, day/night, the numeric range, and the district Sum/Average
  control are methods on `AlertsPopulationPage`. Their accessible names are page constants copied
  from the live report. No new `SlicerKind`.

  `tests/ui/alerts_analysis_dashboard/population_snapshot.py` stores the three card numbers and
  these totals: 24-hour chart, dates chart, district chart, and each series of
  `אוכלוסייה לפי יישוב`. The clear test applies a between-dates window, day, night, and the range
  0 through 349, requires at least one stored figure to change, then clears and requires exact
  equality with the arrival snapshot, including zeros.

  Chart totals add numeric cells only. `None` is not coerced to 0. `state="empty"` fails the
  total. A rendered 0 counts.
- **Rationale**: `Slicer` supports `dropdown`, `checkbox`, `search`, and `clear_all` only.
  Constitution VII forbids a new generic range API that only this report would call. Principle IV
  still puts the locators on the page object, and the test helper only calls page methods.
  `tests/helpers/` is limited to the parity engine and `bind_dashboard`. An exact snapshot is
  what "returns to the snapshot" means; a hard-coded expected total would mix data freshness
  into a mechanics test. Requiring a change before clear stops a broken slicer from passing.
- **Alternatives considered**: Extending `SlicerKind` with `date_between`, `toggle`, and `range`.
  Rejected for this slice. Extract them when a second report needs the same control. Putting
  the snapshot helper in `tests/helpers/`. Rejected. It knows card roles and chart titles.
  Comparing clear against a second fixed baseline instead of the arrival read. Rejected. The
  request says the arrival snapshot.

## R6 — UI identities, and which total day/night uses

- **Decision**: Sum(toggle state) is the dates-chart total, series 0, after `set_day_night` with
  the other slicers cleared.

  - `off`: neither day nor night
  - `day`: only day
  - `night`: only night

  `off + wait` is not used. The assertion is `day + night == off`.

  The cross-chart assertion, with slicers cleared, is:

  `total(24-hour) == total(dates) == total(district while Sum mode is selected)`

  The page method `set_district_aggregation("sum")` runs before that read. Average mode is not
  an identity here.

  Card bounds, on the arrival (or cleared) page: warned ≤ total and unprotected ≤ total.
  Do not assert warned + unprotected == total.

  These tests do not take `alerts_db` and are not marked `db_parity`.
- **Rationale**: The request names those three identities and does not name a fourth
  (warned + unprotected = total). Overlap or a third bucket would make that equality a false
  failure. The dates chart is the daily distribution the day/night split filters; the district
  chart is explicitly "on Sum mode"; the 24-hour chart is the third count of the same alerts.
  Empty-versus-zero already exists on `ChartReading.state` and must not be reimplemented in the
  test with a coercion to 0.
- **Alternatives considered**: Using the three cards as Sum(day) and Sum(night). Rejected. The
  request pairs day/night with a sum, and pairs the cards with the inequality. Using Average
  mode in the cross-chart check. Rejected. The request says Sum mode. Requiring the two
  population parts to exhaust the total. Rejected. It was not in the request.

## R7 — Placeholders stay out of the page-1 parity run

- **Decision**: Add an optional keyword to the engine:

  `validate_dashboard_generic(..., exclude_scopes: Collection[str] | None = None)`

  `None` or an empty collection excludes nothing. A metric whose normalized scope is in the set
  is not read and not queried. `test_alerts_db_parity_last_30_days` passes
  `exclude_scopes={AlertsPopulationPage.PAGE_TITLE}`. Positional callers stay valid. A unit test
  with two metrics and one excluded scope asserts a single `scalar` call.
- **Rationale**: The loader runs every metric in the file. Page-2 chart placeholders return no
  rows, and page-2 card placeholders return 0, so including them in the page-1 run fails parity
  for a reason this feature explicitly postpones. A keyword defaulting to "exclude nothing"
  preserves `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)`.
  Filtering inside the test by rewriting a temporary YAML would duplicate the loader.
- **Alternatives considered**: A second YAML file that the page-1 test does not load. Rejected.
  The request says to add the elements to `data/alerts/alerts_contract.yaml`. Leaving the new
  rows in the page-1 run. Rejected. Stubs would fail that test. Catching the failure. Rejected.
  Connection errors and real mismatches must still fail, and a caught stub failure hides both.

## R8 — Comments for the SQL that this feature does not write

- **Decision**: The comment block above the two new constants states the future rules in English,
  and the constants stay placeholders:

  - Half-open window: `AlertDate >= :start_date AND AlertDate < :end_date`. The upper bound is
    exclusive. Dates stay bound parameters.
  - Grouping: one grain per statement, from district down to settlement. A parent total is not
    added to its children in the same result. This feature does not drill the chart and does not
    invent intermediate Hebrew level names in SQL.
  - Sum versus average: Sum mode is `SUM` of the grouped measure. Average mode is that same sum
    divided by the number of groups (`SUM / NULLIF(COUNT, 0)`), not a different warehouse
    measure. The UI test checks Sum mode only.

  No new method on `AlertsDBRunner`. No `try/except` around connect.
- **Rationale**: The request asks for `SELECT 0` placeholders and for those three rules as
  comments, and it says to validate UI before SQL parity. Writing the real `GROUP BY` now would
  be the parity slice this feature is not. The half-open predicate is already the page-1 rule
  in `test_db_parity.py` and the six real category queries.
- **Alternatives considered**: Implementing the district `GROUP BY` now behind the placeholder
  name. Rejected. The UI tests would still not call it, and an unconfirmed grain would become
  a silent contract. Documenting Average as a second column such as `AVG(...)`. Rejected. The
  rule is sum divided by the group count of the same grouped set.
