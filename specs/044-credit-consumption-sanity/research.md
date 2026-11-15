# Phase 0 Research: Credit Consumption Dashboard UI Sanity

All Technical Context items are known from the existing code (features 004, 018, 035, 039, 043)
and the feature request. No **NEEDS CLARIFICATION** remains.

## R1 — Page class location and the existing Layer 0 binding

- **Decision**: Implement class `CreditConsumptionPage` in
  `pages/credit_consumption/credit_consumption_page.py`. Keep
  `pages/credit_consumption/page.py` as a one-line re-export so
  `tests/ui/credit_consumption_dashboard/conftest.py` continues
  `from pages.credit_consumption.page import CreditConsumptionPage`.
  The class still subclasses `ReportShell`, keeps
  `DASHBOARD_SEARCH_TERM = "צריכת אשראי"`, keeps
  `_report_ready_locator` on `ממוצע הוצאות לקנייה בשגרה`, and keeps the
  existing info-overlay dismiss (`דף מידע` / `מושגים חשובים`) in
  `before_report_ready_check` and `after_navigate`. Do not add
  `pages/credit_consumption/__init__.py` (feature 018 namespace-package rule).
- **Rationale**: Feature 018 moved this report to `pages/credit_consumption/page.py`.
  The smoke suite already imports that path. The user asked for
  `credit_consumption_page.py`; a re-export satisfies both without a second
  catalog product. Popup dismiss is already proven on this report (feature 004).
  A new `ReportShell` subclass would re-implement login/catalog/iframe.
- **Alternatives considered**: Replacing `page.py` in place and ignoring the
  requested filename. Rejected — the user named `credit_consumption_page.py`.
  A second class for Screen 2. Rejected — one report, two pages, same catalog
  term; Screen 2 is a tab switch (feature 019 pattern), not a second product.
  Putting the page under `tests/`. Rejected — Constitution AC-006.

## R2 — How the suite lands on Screen 1 vs Screen 2

- **Decision**: Default navigate stays on Screen 1 (summary). Screen 2
  (`צריכת אשראי - ייצוא נתונים`) is selected by overriding a dedicated
  `open_export_page()` (or `before_report_ready_check` only when a Screen 2
  fixture asks for it) that clicks the page-rail control through a bilingual
  `.or_()` over `ניווט בין עמודים` and `Page navigation` (link / button /
  label), copied from the Alerts Analysis pattern in feature 043. Ready
  anchor on Screen 2 is the export page title from the golden YAML
  (`צריכת אשראי - ייצוא נתונים`). Do not use the Screen 1 KPI phrase as the
  Screen 2 ready signal.
- **Rationale**: `ReportShell.navigate` waits on `_report_ready_locator`.
  Screen 1's `ממוצע הוצאות לקנייה בשגרה` is not mounted on Screen 2.
  Feature 043 showed that a Hebrew-only page-rail raises `LoadTimeoutError`
  when Power BI renders `Page navigation`. `.or_()` is order-independent
  and does not need a language flag.
- **Alternatives considered**: Detecting UI language once. Rejected — extra
  state; `.or_()` already works. Switching in the test body with raw
  locators. Rejected — Principle IV. Importing the alerts page-rail helper.
  Rejected — alerts is off-limits (FR-012).

## R3 — Golden filters vs `הכל`

- **Decision**: Load `data/credit/db_sanity_purim2026.yaml` once. Screen 1
  setup iterates `screen_1_summary.active_filters` and applies every value
  that is not `הכל`. The current file only needs `time_range: "פורים 2026"`.
  Screen 2 setup does the same for `top_bar` then `side_bar`
  (`period: "פורים 2026"`). Compose Layer 2 `Slicer` with `SlicerDefinition`
  rows whose `id` matches the YAML keys and whose `role_name` is copied from
  the live report. Kind is `dropdown` unless the live control is a checkbox
  list. Date text fields, if present, use bilingual `_fill_input` and are
  not a new `SlicerKind`.
- **Rationale**: `הכל` is the Power BI default; re-clicking it is a no-op
  that still costs a settle. Named period `פורים 2026` is the snapshot the
  golden numbers were taken under. Layer 2 already selects dropdowns;
  Constitution VII forbids a new slicer kind for one report.
- **Alternatives considered**: Always applying every YAML value including
  `הכל`. Rejected — extra clicks, flake risk. Hard-coding `פורים 2026` in
  the test. Rejected — the fixture must read `active_filters` from YAML
  (FR-005). Extending `SlicerKind` with `toggle` / `date_between`. Rejected
  for this slice (same as feature 019 R5).

## R4 — KPI titles and nested `kpi_metrics`

- **Decision**: `read_kpi_metrics() -> dict` returns the nested golden
  shape. Compose Layer 2 `KPI.number` / `KPI.value` (percents stay strings).
  Titles are copied from the live report during implementation. The only
  title already known is the ready visual `ממוצע הוצאות לקנייה בשגרה`
  (routine expense; maps under `average_purchase_expense_routine`). Do not
  invent the population, selected-range, or change-vs-routine Hebrew
  strings in this research file. Percent cards use `KPI.value` (or raw
  text) so `"3.23%"` is preserved; `KPI.number` would strip the `%`.
- **Rationale**: Feature 012/014 already read KPI cards by opaque title.
  The golden file nests physical / online / total; flattening would force
  the test to re-nest. Inventing Hebrew titles is how previous slices
  mismatched the live report (feature 019 R4: copy from live).
- **Alternatives considered**: One flat dict of YAML leaf paths. Rejected —
  FR-006 asks for the nested `kpi_metrics` shape. Parsing percents as
  floats. Rejected — the golden values are quoted percent strings.

## R5 — Toggles and `daily_trends_by_toggle`

- **Decision**: Domain methods `set_metric(kind)` and `set_visualization(kind)`
  click Screen 1 buttons. Accessible names are copied from the live report
  (Hebrew and, if present, English `.or_()`). Internal state maps:

  | YAML key | metric | visualization | row field |
  |----------|--------|---------------|-----------|
  | `expense_amount_line` | expense amount | line | `value` (number) |
  | `transactions_count_line` | transactions count | line | `value` (number) |
  | `expense_amount_bar` | expense amount | bar | `value` (number) |
  | `transactions_count_bar` | transactions count | bar | `values` (list of numbers) |

  `read_daily_trends()` right-clicks the active visual, clicks bilingual
  `הצג כטבלה` / `Show as a table`, reads date / day / value columns, leaves
  the table (`_leave_visual_table`). It does not use SVG marks or tooltips
  as the assertion path. `transactions_count_bar` keeps a list (`[3, 1]`)
  because the golden file stores split series that way.
- **Rationale**: Feature 043 made Show-as-a-table the primary extraction
  for flaky Power BI charts. The user named that strategy. Toggle buttons
  are page chrome, not catalog slicers (feature 019 day/night). Coercing
  the bar-transactions list into a sum would hide a golden series.
- **Alternatives considered**: Layer 2 `Chart.read` as the assertion path.
  Rejected — SVG/tooltip is the flake the user asked to bypass. Extracting
  Show-as-a-table into `core/components`. Rejected this slice: migrating
  alerts is off-limits, and an unused-by-fleet Layer 2 API violates VII
  ("do not invent unused generic APIs"). Duplicate the helper on the
  credit page. Hover tooltips. Rejected — known flake.

## R6 — Authority chart, daily alerts, export matrix

- **Decision**: `read_expenses_by_authority()` uses the same Show-as-a-table
  path on the authority visual; return a list of `{authority, amount}`
  matching `expenses_by_authority_millions`. Extra UI authorities are
  ignored by the test. `read_daily_alerts()` is optional: implement when
  the visual is on Screen 1; the test skips if the reader returns `[]`.
  `read_export_table()` reads the Screen 2 accessible `grid` / `table`
  (already a matrix, not a chart) and maps headers to
  `export_table_data` keys. Header labels are copied from the live report
  and folded to the YAML keys. Amount stays a thousands-separated string
  (`"1,944.97"`) to match the golden file.
- **Rationale**: Authority is a chart, so Show-as-a-table applies. The
  export page is already a table. Parsing amounts to floats would fail
  equality with the quoted strings. `daily_alerts` is in the YAML but was
  not named in the user story list; a skip-if-absent test covers it
  without blocking P1.
- **Alternatives considered**: Using Layer 2 `Chart` categories for
  authority. Rejected as the primary path — same flake. Normalizing export
  amounts to floats. Rejected — golden strings include commas.

## R7 — Sanity package, smoke gate, and off-limits modules

- **Decision**: New package `tests/sanity/credit_consumption_dashboard/`
  with `conftest.py` binding `credit_consumption_dashboard =
  bind_dashboard(CreditConsumptionPage, "credit_consumption_dashboard")`
  and `test_data_validation.py`. Tests are `@pytest.mark.sanity`. Shared
  setup helper applies golden filters. Root `conftest.py` does not import
  the page. Credit UI smoke stays the navigation-surface gate
  (`pytest tests/ui/credit_consumption_dashboard/`). Fleet smoke is not a
  gate. No edit under `pages/alerts_analysis/`, `pages/status_picture/`,
  `pages/fleet_dashboard/`, `core/`, `db/`, or any `tests/**/alerts_*` /
  `status_picture_*` / `fleet_*` path. Coverage catalog gains a credit
  section that maps YAML keys to page methods (Constitution V documentation,
  not a SQL mapping).
- **Rationale**: Alerts and status-picture sanity packages already use a
  local fixture + golden YAML. Principle II forbids a root-conftest import.
  Principle III requires the existing credit smoke contract to stay green
  when this domain page's navigation surface is extended. Fleet is
  untouched, so its smoke suite is not the gate.
- **Alternatives considered**: Reusing the smoke `dashboard` fixture name
  inside the sanity package. Acceptable via `bind_dashboard` default, but
  a distinct fixture name matches status-picture and avoids confusion.
  Adding `db/clients/credit.py`. Rejected — this slice is UI vs golden
  YAML (Principle V deviation, same as 035/039).

## R8 — Comments and live-copied labels

- **Decision**: Every new or edited function comment is English. Hebrew
  appears only in string literals (titles, role names, golden keys).
  Slicer role names, toggle names, KPI titles (except the known ready
  visual), chart titles, and export headers are copied from the live
  report in the same change that first uses them. They are not guessed
  here.
- **Rationale**: FR-014 / FR-016. Previous slices failed when a guessed
  title did not match Power BI.
- **Alternatives considered**: Recording guessed Hebrew in the spec.
  Rejected — FR-016.
