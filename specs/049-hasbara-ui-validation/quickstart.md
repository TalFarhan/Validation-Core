# Quickstart: Hasbara Dashboard UI Sanity Validation

## What this slice does

Adds readers on `PublicInquiriesPage` and a sanity module that compares the live
ניתוח פניות הסברה report to `data/hasbara/db_sanity.yaml`:

- Four tabs: Written Response, Written Response Investigation (`תחקור מענה כתוב`),
  Satisfaction Feedback (`ניתוח משובי שביעות רצון`), Feedback Investigation (`תחקור משובים`).
- Date range from each screen's `dashboard_info.date_range`. Current file:
  `01/10/2026 - 31/10/2026`. The test does not hardcode that string. The page clicks the
  filter-bar toggle (`כלל התאריכים` or `יום נוכחי`) once when the start and end inputs
  are hidden or disabled, then types the YAML start and end. It waits until the loading
  spinner is gone and the screen locator is visible. It does not sleep.
- Secondary slicers (Hours, Language, Platform, Topic, Settlement, plus the golden
  `active_filters` on screens 1, 2, and 4) are read. `הכל` is not clicked.
- Screen 1 KPIs and charts, screen 2 investigation rows, screen 3 survey cards and bars,
  screen 4 feedback rows including comments. After the date filter, `read_kpi_metrics`
  waits until the inquiries widget spinner is hidden and the visible total and open
  texts have settled, then reads those counts from the visible text inside the host
  that contains `סה"כ פניות` and `פניות פתוחות`. The token reset and the settle script
  call `frame.locator("body").evaluate`. They do not call `evaluate` on the
  `FrameLocator`. A hidden measure image, a tooltip, and a stale SVG are not the
  value. KPI locators use `.filter(visible=True)`. The reader also reads both duration
  widgets (`זמני סגירת פנייה`, `זמני המתנה למענה`). `ממוצע` and `מקסימלי` stay
  `DD:HH:MM:SS` strings under `request_closing_times` and `response_wait_times`.
  Screen 3 waits until the survey titles are visible and a visible metric under each
  card has settled, then reads that visible text. `total_requests`, `open_requests`,
  and `surveys_summary` stay in the golden comparison.
- `select_satisfaction_tab` clicks the courtesy sub-tab by its exact visible
  text inside the report frame (`tab`, `button`, `link`, or exact text), with
  `.filter(visible=True)`. A match inside `התקבלות השירות` is preferred. It
  does not use the page-rail locator. The loaded label is `אופן מקצועי`.
- Golden keys and rows must match. Extra UI rows are ignored. There is no `last_updated`
  compare.
- Screen 2 and screen 4 rows are read by right-clicking the grid visual and opening
  Show as a table. The expanded grid supplies every column, including handling time.
  Back to report closes that view, and the page then waits until the screen's ready
  locator is visible. The canvas grid is not a fallback. Vertical scrolling inside
  the expanded grid still uses `collect_virtualized_rows`. Show as a table waits
  until a data cell is visible before that scroll.
- Screen 4 counts as rendered when the comments header (`הערות` or `הערה`) is visible.
- An empty read fails when the golden block has data. Skip only when that visual or grid
  is not on the page.
- Failures print the YAML path, the UI value, and the golden value.

The existing smoke test stays a one-line `verify_freshness()` call.

## Prerequisites

- Portal auth configured (the sanity tests open the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.

## Files you will touch

- `pages/public_inquiries/page.py` — period toggle, date inputs, spinner wait, four
  screens, slicer reads, KPI, charts. `read_kpi_metrics` waits for the inquiries widget
  by evaluating the settle script on the iframe `body`, reads its visible count text,
  then reads both duration widgets. Survey reads wait for the visible cards and ignore
  tooltips and hidden SVGs. `read_investigation_rows` and `read_feedback_rows` locate
  the grid visual and call `VisualTable.read_rows`, then map Hebrew headers. They do
  not scrape the clipped canvas grid. `select_satisfaction_tab` clicks a visible
  exact sub-tab in the report frame and does not call `_click_tab`. Keep
  `DASHBOARD_SEARCH_TERM` and `_report_ready_locator`.
- `core/components/virtual_grid.py` — vertical collector used on the grid it is given.
  No report labels. Not the source of detail-grid columns.
- `core/components/visual_table.py` — wait for a data cell, then call the collector.
  When several grids are visible, read the data-view grid (Back to report ancestor,
  then the most column headers). Do not change `read_rows`'s signature or
  `rows_to_label_values`. Close with Back to report.
- `core/components/__init__.py` — export the collector.
- `tests/sanity/public_inquiries_dashboard/conftest.py` — sanity fixture, if it is not
  already present.
- `tests/sanity/public_inquiries_dashboard/test_data_validation.py` — remove
  `assert_last_updated` and every `info["last_updated"]` read.
- `docs/COVERAGE_CATALOG.md` — section 10 for this golden map, with no last-updated row.

## Do not change

- `core/portal/`.
- `pages/alerts_analysis/`, `pages/credit_consumption/`, `pages/fleet_dashboard/`,
  `pages/status_picture/`.
- `db/` and the root `conftest.py`.
- `data/hasbara/db_sanity.yaml` and any other YAML file.
- `tests/ui/public_inquiries_dashboard/test_dashboard_smoke.py`.
- `tests/unit/test_visual_table_rows.py`.
- `docs/PROJECT_GUIDE.md`.
- Spec documents under `specs/048-fleet-table-extraction/`.

## Run

```text
pytest tests/unit/test_visual_table_rows.py
pytest tests/ui/public_inquiries_dashboard/
pytest tests/ui/fleet_dashboard/
pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity
```

The unit file guards `rows_to_label_values`. Public Inquiries smoke is the freshness gate.
Fleet smoke is required because `VisualTable` changed. The sanity command is the golden
compare, including the former T017 run. The two browser commands need portal auth.
The satisfaction sub-tab gate is the distributions test:

```text
pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen3_distributions_match_golden
```

Layer 0 and Layer 2 are unchanged by that click, so fleet smoke is not a new gate for it.

## Done when

- Each `test_hasbara_screen*` name in the contract exists and compares the YAML block that
  the contract names.
- A wrong KPI, chart cell, `request_id` row, or `comments` cell fails with
  `yaml_path`, `ui=`, and `golden=` in the message.
- `apply_date_range` clicks the period toggle at most once, and only when the date
  inputs are hidden or disabled. A missing input raises. It does not return early.
- `הכל` does not appear as an argument to `Slicer.select` in the new page methods.
- Date commits and tab changes do not call `wait_for_timeout` or `networkidle`.
- `verify_freshness` is still the body of `test_dashboard_updated_within_24_hours`.
- `test_data_validation.py` has no `assert_last_updated` and no `last_updated` lookup.
- `core/portal/`, `db/`, and `data/hasbara/db_sanity.yaml` are unchanged.
- `core/components/virtual_grid.py` contains no `request_id`, `inquiry_id`, or Hasbara title.
- Screen 4's rendered check does not require the full parenthetical title.
- Show as a table does not collect rows before a data cell is visible.
- Screen 2 and screen 4 row reads right-click the grid visual, read the expanded
  table, and leave through Back to report. `handling_time` is not taken from the
  canvas grid. New locators, waits, method names, and comments are English.
- New comments, waits, and log text are English.
- `read_kpi_metrics()` includes `request_closing_times.average`,
  `request_closing_times.maximum`, `response_wait_times.average`, and
  `response_wait_times.maximum` when those widgets are on screen.
- `read_kpi_metrics()` returns `inquiries_summary.total_requests` and
  `inquiries_summary.open_requests` from the visible inquiries widget after that
  widget has settled. The test still compares both keys. It does not pop them.
- The inquiries token reset and settle poll call `locator("body").evaluate` on the
  report frame. They do not call `FrameLocator.evaluate` or
  `FrameLocator.wait_for_function`.
- KPI and survey locators use `.filter(visible=True)` and skip tooltips,
  `aria-hidden` nodes, and empty boxes. Screen 3 waits for the survey cards before
  `read_satisfaction` returns. `surveys_summary` is still fully asserted.
- `core/components/kpi.py` has no Hasbara title and no `ממוצע` / `מקסימלי` caption.
- `select_satisfaction_tab` does not call `_click_tab`. Its locator uses
  `.filter(visible=True)` and an exact tab, button, link, or text match in the
  report frame. `_tab_locator` still anchors the four report pages on
  `ניווט בין עמודים`. Comments and waits added for that click are English.
