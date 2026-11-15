# Contract: Hasbara Dashboard UI Sanity Validation

**Feature**: `049-hasbara-ui-validation` | **Date**: 2026-11-11

Adds readers to the existing Public Inquiries page and adds a sanity module. The
2026-11-05 revision also adds the collector in [virtual-grid.md](./virtual-grid.md).
Alerts, credit, fleet page sources, `core/portal/`, `db/`, the root `conftest.py`, the
smoke module, and `data/hasbara/db_sanity.yaml` stay unchanged. `verify_freshness` stays
inherited. Sanity tests do not read `last_updated`.

## Page

`pages/public_inquiries/page.py`

Class `PublicInquiriesPage` still inherits `ReportShell`.

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `"ניתוח פניות הסברה"` (unchanged) |
| Ready locator | existing exact iframe text `"ניתוח פניות הסברה"` (unchanged) |
| Freshness | inherited `verify_freshness` — no override |
| Caption | inherited last-refresh caption reader — no new parser |
| Charts | `VisualTable.read_rows` on a container the page locates by title. The reader waits for a data cell, then scrolls with `collect_virtualized_rows` |
| Detail grids | Page maps Hebrew headers, then `collect_virtualized_rows` scrolls. The page passes `request_id` or `inquiry_id` |
| Default slicer value | `"הכל"` is read, never passed to `Slicer.select` |

Hebrew tab labels, slicer labels, chart titles, and column headers are constants on this
page. Comments and locator variable names are English.

## Methods added

### `apply_date_range(self, date_range: str) -> None`

The argument is the YAML `dashboard_info.date_range` string. Split once on `" - "` into
start and end. The current file yields `01/10/2026` and `31/10/2026`. The test does not
pass those literals.

1. When `read_date_range()` already equals the normalized string, return. Do not click
   the period toggle.
2. When the start input and the end input are not both visible and enabled, click the
   global filter-bar toggle once. The toggle is the visible action button whose text is
   `כלל התאריכים` or `יום נוכחי` (`.visual-actionButton`, also matched by role `button`).
   Click whichever of those two labels is showing. Click at most once.
3. Wait until both inputs are visible and enabled:
   `input[aria-label^='תאריך התחלה']` or `Start date`, and
   `input[aria-label^='תאריך סיום']` or `End date`. The wait is
   `expect(...).to_be_visible()` and `to_be_enabled()` with `self.timeout`. When they
   stay hidden, raise. Do not return as if the range were applied.
4. Fill start, press Enter, fill end, press Enter. Escape closes a leftover calendar
   popup. Do not call `Slicer.select`.
5. Call `_wait_for_report_settled()` before any later read.

### `read_date_range(self) -> str`

Return `DD/MM/YYYY - DD/MM/YYYY` from the two inputs when both values match that
pattern. Before the inputs exist, the body text may contain `יום נוכחי`. That label is
not a successful apply. After a successful apply the return value is the YAML range.

### `_wait_for_report_settled(self) -> None`

Used at the end of `apply_date_range` and `open_screen`.

- When the report iframe shows a visible loading spinner (a node whose class contains
  `spinner`, or an `aria-busy` loading overlay), `expect` it hidden within `self.timeout`.
  A spinner that is not in the DOM is not a failure.
- Then `expect` the current screen's ready locator visible (KPI card, investigation
  grid, survey card, or feedback grid).
- Do not call `page.wait_for_timeout`.
- Do not call `page.wait_for_load_state("networkidle")`. The portal socket stays open,
  so network idle does not arrive. The spinner-hidden check plus the ready locator is
  the dynamic settle this report can observe.

### `open_screen(self, screen_id: str) -> None`

`screen_id` is `screen_1`, `screen_2`, `screen_3`, or `screen_4`.

| Id | Tab label | Ready locator |
|----|-----------|---------------|
| `screen_1` | landing; click only if the KPI card is absent | screen 1 KPI card |
| `screen_2` | `תחקור מענה כתוב` | investigation grid |
| `screen_3` | `ניתוח משובי שביעות רצון` | survey summary card |
| `screen_4` | `תחקור משובים` | visible column header `הערות` or `הערה` |

After the click, call `_wait_for_report_settled` and wait until the ready locator in the
table above is visible. Screen 4's ready locator is the comments header, not the full
parenthetical title. The wait uses the page timeout. It does not use `networkidle` and it
does not sleep a fixed interval. The filter bar is
global: a later screen in the same session keeps a range the inputs already show, and
`apply_date_range` then returns without a second toggle click. Each test still calls
`apply_date_range` because each test opens the report on its own.

### `slicer_is_visible(self, slicer_id: str) -> bool`

True when that id has a definition and its control is visible. False when the screen does
not show it.

### `read_slicer_text(self, slicer_id: str) -> str`

Visible text of `Slicer.control(slicer_id)`, with bidi marks removed. Does not open the
dropdown and does not select a value.

### `phrase_is_visible(self, phrase: str) -> bool`

True when the iframe shows `phrase`. Used for `title`, `data_source`, and
`platforms_included`.

### `read_kpi_metrics(self) -> dict`

Nested map shaped like `kpi_metrics`. The reader walks every Screen 1 metric-bar widget.
It does not stop after the inquiries widget.

Before the inquiries counts are extracted, the reader waits for that widget to finish
the update that follows the date filter. Screen 1 settle uses the same wait. Inside the
widget, a visible spinner or `[aria-busy='true']` is hidden, then the visible
`CountTotalTickets` and `CountOpen` texts are unchanged on two successive reads. The
bound is the page timeout. The wait does not search for `1324`, `1,324`, or `49`, and
it does not call `wait_for_timeout` or `networkidle`.

The settle runs on the report `FrameLocator`'s body. The token reset is
`frame.locator("body").evaluate("() => { window.__vcInquiryToken = ''; }")`. The poll
is `expect.poll(lambda: body.evaluate(_INQUIRY_SETTLED_JS), timeout=self.timeout).to_be(True)`.
The code does not call `.evaluate` or `.wait_for_function` on the `FrameLocator`.
A timeout raises `AssertionError("Inquiries widget counts did not settle")`.

Widget hosts, `svg text`, measure images, duration titles, and the screen 1 ready
title use `.filter(visible=True)`. A node inside `[role='tooltip']`, a node with
`aria-hidden='true'`, and a node with an empty box are ignored. The settle script
uses the same exclusions. `_any_kpi_visible` does not treat a hidden
`CountTotalTickets` image as the widget being present.

- `inquiries_summary` comes from the four count cards (`total_chats`, `total_requests`,
  `open_requests`, `closed_requests`). The container is the smallest visual host that
  contains both `סה"כ פניות` and `פניות פתוחות`. Each value is the visible `svg text`
  (or other visible text node) for that card inside the container. A visible
  `img[aria-label*='{measure_id}']` in the same container is the fallback. Hidden,
  `aria-hidden`, zero-size, and iframe-wide `.first` images are not read. When visible
  text and an image label disagree, the visible text wins. Counts stay display strings.
  The test parses an integer golden value, so a grouped `1,324` still matches `1324`.
  `total_requests` and `open_requests` stay in the returned dict when the widget is on
  screen. The test does not remove either key.
- `request_closing_times.average` and `request_closing_times.maximum` are the `ממוצע` and
  `מקסימלי` strings inside the visual titled `זמני סגירת פנייה`.
- `response_wait_times.average` and `response_wait_times.maximum` are the same two captions
  inside the visual titled `זמני המתנה למענה`.

Each duration is the `DD:HH:MM:SS` text that follows its caption in that container. The
reader does not call `KPI.read_text` for these two widgets. A caption that is absent from
its container is omitted so the golden assert fails that key. The reader does not skip.
The test `test_hasbara_screen1_kpi_match_golden` is unchanged and compares the whole tree,
including `total_requests` and `open_requests`.

### `read_screen1_charts(self) -> dict`

Keys: `written_media_breakdown`, `language_breakdown`, `recurring_requests_breakdown`,
`leading_topics`, `requests_by_hour_trend`. Category rows come from `VisualTable`. The
hourly entry provides `series` names and `x_axis_labels`. Counts may stay display strings;
the test applies the YAML type.

### `read_investigation_rows(self) -> list[dict]`

Locates the visual host of the visible investigation grid and calls
`VisualTable.read_rows` (`button="right"`, then `הצג כטבלה` or `Show as a table`).
Rows come from the expanded grid. `read_rows` clicks Back to report and waits until
that button is hidden before it returns. The page then expects the screen 2 ready
locator to be visible. Hebrew headers are mapped to the YAML field names on the page.
The page dedupes on `request_id`. Blank cells are `""`. A total row is dropped on the
page. The reader returns `[]` when the expanded grid has no data rows. It does not
skip, and it does not fall back to the canvas grid. A missing menu item, back
button, or data cell raises.

### `select_satisfaction_tab(self, label: str) -> None`

Clicks one courtesy sub-tab on screen 3. The test passes
`service_reception.active_tab`. The page does not load YAML. With the current
file, PyYAML's last-key rule makes that argument `אופן מקצועי`.

The locator is built on the report frame. It prefers a visible `tab`,
`button`, or `link` whose accessible name equals `label` (`exact=True`), then
visible text equal to `label` (`get_by_text`, `exact=True`). Each candidate
uses `.filter(visible=True)`. The first paintable match outside a tooltip is
the click target. A visible host that contains `התקבלות השירות` is searched
first. The page-rail pattern `ניווט בין עמודים . {label}` is not used here.
`_click_tab` and `_tab_locator` stay the four-screen navigation.

The method expects the chosen node to be visible, clicks it, hides a visible
spinner in that section, and expects the label phrase to be visible. The bound
is the page timeout. It does not call `wait_for_timeout` or `networkidle`.
Locators, waits, the method name, and comments are English.

### `read_satisfaction(self) -> dict`

`surveys_summary`, `message_reception`, `service_reception`, `leading_contact_channels`,
and `platforms_breakdown`. The distributions test calls `select_satisfaction_tab`
with `service_reception.active_tab` before reading that distribution. See that
method for the visible exact-text locator. The page does not load the file.

Before the survey cards are read, screen 3 settle and this method wait until
`מוקד טלפוני`, `מענה כתוב`, and `בקרת איכות` are visible, any visible spinner in
those cards is hidden, and a visible metric-shaped string under each card (a
number, `לא ידוע`, or `אין מידע`) is unchanged on two reads. The bound is the page
timeout. The wait does not search for `1,062`, `129`, or `39`. Section titles and
the geometry scan use `.filter(visible=True)` and skip `[role='tooltip']`,
`aria-hidden`, and empty boxes. The returned `surveys_summary` is still compared
in full by `_assert_tree`.

### `read_feedback_rows(self) -> list[dict]`

Same Show-as-a-table sequence as the investigation grid, on the feedback grid's
visual host. The page dedupes on `inquiry_id`. Field names match
`feedback_investigation_table_data`, including `comments`. The data view is closed
before the method returns. The canvas grid is not a fallback.

### `visual_is_rendered(self, title: str) -> bool` / `grid_is_rendered(self, screen_id: str) -> bool`

`visual_is_rendered` is true when the chart title is visible. `grid_is_rendered("screen_2")`
stays true when the screen title is showing and a grid or table is visible.
`grid_is_rendered("screen_4")` is true when the feedback comments header is visible, as
in [virtual-grid.md](./virtual-grid.md). It does not require the full parenthetical title.
The test calls these before a read that might skip.

## Fixture

New file `tests/sanity/public_inquiries_dashboard/conftest.py`:

```text
public_inquiries_dashboard = bind_dashboard(
    PublicInquiriesPage, "public_inquiries_dashboard"
)
```

The smoke conftest keeps `dashboard = bind_dashboard(PublicInquiriesPage)`.

The test module loads `data/hasbara/db_sanity.yaml` and uses the `hasbara_dashboard` node.
It does not edit the file.

## Tests

Module: `tests/sanity/public_inquiries_dashboard/test_data_validation.py`.
Marker: `sanity`.

| Test | YAML block | Page calls |
|------|------------|------------|
| `test_hasbara_screen1_filters_match_golden` | `screen_1_written_response.dashboard_info.date_range`, `active_filters` | `apply_date_range`, `read_slicer_text` |
| `test_hasbara_screen1_kpi_match_golden` | `kpi_metrics`, title, data source | `read_kpi_metrics`, `phrase_is_visible` |
| `test_hasbara_screen1_charts_match_golden` | `charts` | `read_screen1_charts` |
| `test_hasbara_screen2_filters_match_golden` | screen 2 date range, `active_filters`, `platforms_included` | `open_screen("screen_2")`, slicer read |
| `test_hasbara_screen2_investigation_rows_match_golden` | `investigation_table_data` | `read_investigation_rows` |
| `test_hasbara_screen3_filters_match_golden` | screen 3 date range; visible members of the five named slicers | `open_screen("screen_3")` |
| `test_hasbara_screen3_surveys_match_golden` | `surveys_summary`, title, data source | `read_satisfaction` |
| `test_hasbara_screen3_distributions_match_golden` | `message_reception`, `service_reception`, `leading_contact_channels`, `platforms_breakdown` | `select_satisfaction_tab`, `read_satisfaction` |
| `test_hasbara_screen4_filters_match_golden` | screen 4 date range and `active_filters` | `open_screen("screen_4")` |
| `test_hasbara_screen4_feedback_rows_match_golden` | `feedback_investigation_table_data` | `read_feedback_rows` |

Row paths:

- `screen_2_written_response_investigation.investigation_table_data[request_id=<id>].<field>`
- `screen_4_feedback_investigation.feedback_investigation_table_data[inquiry_id=<id>].<field>`

KPI and chart paths follow the YAML keys under `screen_1_written_response` and
`screen_3_satisfaction_feedback`.

Mismatch text: `{yaml_path}: ui={actual!r} golden={expected!r}`.

## Comparison rules

- Walk golden keys and rows only.
- Screen 2 identity is `request_id`. Screen 4 identity is `inquiry_id`.
- `handling_time`, `platform`, `topic`, and `request_id` are required fields on screen 2
  and are covered because the whole golden row is compared.
- `comments` and `inquiry_id` are required fields on screen 4 and are covered the same way.
- An `int` golden node parses the UI text (commas and spaces removed). A `str` golden node
  compares trimmed display text.
- Empty golden strings match blank cells.
- Relative order is required for `x_axis_labels` and for `requests_by_hour_trend.series`.
  Grid row order is not required.
- Skip only when `visual_is_rendered` or `grid_is_rendered` is false. An empty list after
  a true rendered check fails.

## Catalog

Add section 10 to `docs/COVERAGE_CATALOG.md` mapping each YAML block above to the page
method and the test name. State that this report has no warehouse client.

## Out of scope

- Editing `data/hasbara/db_sanity.yaml`.
- Adding `db/clients/hasbara.py` or a `db_parity` test.
- Editing `core/portal/`.
- Putting a Hasbara or fleet label inside `core/components/`.
- Calling `assert_last_updated` or reading `info["last_updated"]`.
- Editing the smoke module or changing `_report_ready_locator`.
- Editing `docs/PROJECT_GUIDE.md`.
- Editing fleet, alerts, credit, and status-picture page sources. Fleet smoke is still run.
