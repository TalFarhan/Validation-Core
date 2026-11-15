# Implementation Plan: Hasbara Dashboard UI Sanity Validation

**Branch**: `feature/reportportal-integration` (spec directory `049-hasbara-ui-validation`) | **Date**: 2026-11-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/049-hasbara-ui-validation/spec.md`, the
2026-11-05 T017 failure brief, the 2026-11-10 duration-widget brief, the
2026-11-10 inquiries-count brief, the 2026-11-11 frame-and-visibility brief
(`AttributeError: 'FrameLocator' object has no attribute 'evaluate'` in the
inquiries settle, plus KPI and survey reads that attach to hidden tooltips or
stale SVGs), and the 2026-11-11 detail-grid brief: investigation and feedback
rows return `ui=[]` or drop clipped columns such as `handling_time` because the
canvas table is scraped instead of Show as a table, and the 2026-11-11 satisfaction
sub-tab brief: `test_hasbara_screen3_distributions_match_golden` times out
clicking `אופן מקצועי` because `select_satisfaction_tab` uses the page-rail
locator.

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`tasks.md` is the satisfaction sub-tab locator list. Shipped filter, KPI, chart, grid, and
smoke work is checked. The open tasks are T001, T002, T006, T007, and T010–T012.
`.specify/feature.json` stays on this directory. Planning does
not switch the git checkout (`feature/reportportal-integration`). Spec documents under
`specs/048-fleet-table-extraction/` are not edited. `core/components/visual_table.py` is edited
because Show as a table is the shared chart reader; its public signature stays the one in the
048 contract. The 2026-11-11 revision does not edit `core/`.

## Summary

Add a golden-YAML sanity suite for the Public Inquiries report (ניתוח פניות הסברה) so the live
UI for October 2026 matches `data/hasbara/db_sanity.yaml` (`hasbara_dashboard`).

`PublicInquiriesPage` already opens the report and hosts the first readers. This revision
changes `apply_date_range` so the period toggle is clicked before the date inputs are
filled. The sanity module under `tests/sanity/public_inquiries_dashboard/` stays the
compare. The smoke test stays a one-line `verify_freshness()` call. There is no SQL client.

1. **Date picker, then filters** — The global filter bar opens on a relative period. Its
   toggle shows `כלל התאריכים` or `יום נוכחי`, and the Start Date and End Date inputs stay
   hidden or disabled until that toggle is clicked once. `apply_date_range` performs that
   click when the inputs are not ready, fills the start and end taken from
   `dashboard_info.date_range` (`01/10/2026` and `31/10/2026` in the current file), and
   waits until any loading spinner is hidden and the screen's ready locator is visible.
   It does not sleep and it does not wait for network idle. When the inputs already show
   the YAML range, it does not click the toggle again. A silent return while the inputs
   are still missing is the defect this revision removes. `active_filters` values (all
   `הכל` in the current file) are read and compared. `הכל` is not clicked. Screen 3 has
   no `active_filters` map. Hours, Language, Platform, Topic, and Settlement are read
   when visible and must show `הכל`.
2. **Four tabs** — Screen 1 is the landing page. Screen 2 opens `תחקור מענה כתוב`, screen 3
   opens `ניתוח משובי שביעות רצון`, screen 4 opens `תחקור משובים`. Each switch waits until
   that screen's title or grid is visible.
3. **Subset asserts** — KPI and chart golden keys must exist and be equal. Screen 2 rows match
   on `request_id`. Screen 4 rows match on `inquiry_id`, including `comments`. Extra UI rows
   and extra chart categories are ignored. The hourly trend asserts series names and
   `x_axis_labels` only.
4. **Types** — YAML integers compare as integers (a displayed `1,324` matches `1324`). YAML
   strings compare as display text (`"59%"`, `"00:04:16:36"`, `"1,062"`, `"לא ידוע"`, `""`).
5. **Fail vs skip** — A rendered visual whose reader returns empty while the golden block has
   data fails. `pytest.skip` runs only when that visual title or grid is absent.

### Revision 2026-11-05 — T017 failures

Where this revision disagrees with an earlier bullet in this file, this revision wins.

The live sanity run failed before the golden compares could finish. `data/hasbara/db_sanity.yaml`
has no `last_updated` key (`dashboard_info` on screens 1 and 3 keeps title, date range, and
data source only). `test_hasbara_screen1_kpi_match_golden` and
`test_hasbara_screen3_surveys_match_golden` still call `assert_last_updated(..., info["last_updated"])`,
which raises `KeyError`. Chart reads return `ui=[]` because `VisualTable.read_rows` collects
rows as soon as a grid or table is visible, before any data cell exists. Screen 2 and screen 4
grids are virtualized: `PublicInquiriesPage._read_grid` scrolls ancestors only, by
`clientHeight - 24`, and can stop while later `request_id` / `inquiry_id` rows are still
unloaded. Screen 4 is skipped because `grid_is_rendered("screen_4")` requires the full
parenthetical title `ניתוח פניות הסברה - ניתוח משובי שביעות רצון (תחקור משובים)` before it
looks for a grid.

1. **Drop the obsolete timestamp** — Delete `assert_last_updated` and both call sites. Do not
   replace them with another caption read. Leave `verify_freshness` inherited. Do not edit
   the YAML.
2. **One virtualized-grid collector in Layer 2** — Add `core/components/virtual_grid.py`.
   It finds the scrollable container inside the caller-supplied grid (a node whose
   `overflow-y` is `auto`, `scroll`, or `overlay` and whose `scrollHeight` exceeds
   `clientHeight`; search descendants and ancestors). Each pass reads the rows the caller
   extracts, stores them in a dict keyed by the caller-supplied id, scrolls that container
   by its `clientHeight`, and stops when that scroll adds no new id or the scroll position
   does not move. A timeout bounds the loop. The module has no Hasbara field names.
   `PublicInquiriesPage._read_grid` and `VisualTable._collect_rows` both call it.
   `request_id` and `inquiry_id` stay on the page. Do not put this loop on `ReportShell`.
3. **Show as a table waits for a data row** — Immediately after the menu click, and after
   the visible grid or table is located, `expect` the first data cell (`td`, `gridcell`, or
   `cell` inside a `tr` or `row`) to be visible, bounded by `timeout_ms`. Then run the
   collector. Do not call `wait_for_timeout`. An empty table still fails the hasbara test
   with `ui=[]` when the golden block has rows (FR-011).
4. **Screen 4 rendered locator** — During implementation, confirm the live screen 4 DOM.
   `grid_is_rendered("screen_4")` and `_wait_until_ready("screen_4")` wait on a visible
   column header whose name is `הערות` or `הערה` inside the feedback grid. If that header
   has no accessible name, use the visible text `הערות` inside the grid. Do not use the
   full parenthetical title as the rendered gate. Screen 2 keeps its current grid check.

### Revision 2026-11-10 — Screen 1 KPI widgets

Where this revision disagrees with an earlier bullet about `read_kpi_metrics`, this
revision wins. Charts, grids, the date picker, and the `last_updated` removal stay as
previously planned. This revision does not edit the golden YAML or the sanity test.

`test_hasbara_screen1_kpi_match_golden` fails because `read_kpi_metrics()` returns
`inquiries_summary` and omits `request_closing_times`. The Screen 1 metric bar has three
widgets. The inquiries widget ("פניות") is already read. "זמני סגירת פנייה" (request
closing times) and "זמני המתנה למענה" (wait for a reply) are visible and are not read.
Each of those two widgets shows two captions, "ממוצע" and "מקסימלי", whose values are
`DD:HH:MM:SS` strings.

The current reader walks `_KPI_SPECS` as one measure image per golden leaf
(`AvgTimeToResolve`, `MaxTimeToResolve`, `AvgTimeToFirstReply`, `MaxTimeToFirstReply`).
Those images are not how the two duration widgets expose their values. The fallback calls
Layer 2 `KPI.read_text` on the shared widget title. That call resolves one button or group
and keeps a single numeric token. A duration contains colons, so the token is not
`00:04:35:46`, and the second caption under the same title is never visited. When the call
returns nothing, `if value is None: continue` never creates the parent key, so the dict
has no `request_closing_times` block. `_any_kpi_visible` only looks for the inquiries card,
which is why the test proceeds and then fails the golden tree.

1. **Walk every metric-bar widget.** `read_kpi_metrics` locates each Screen 1 KPI visual
   and reads it. It does not return after the inquiries widget. The four count cards stay
   on the existing measure-id path (`CountConversationsID`, `CountTotalTickets`,
   `CountOpen`, `CountTickets`) and still fill `inquiries_summary`.
2. **One visual, two captions.** For `request_closing_times`, find the visual container
   whose title is `זמני סגירת פנייה` (also accept `זמני סגירת פניה`). Inside that
   container, the string beside `ממוצע` is `average` and the string beside `מקסימלי` is
   `maximum`. Repeat for `response_wait_times` with title `זמני המתנה למענה`. Reuse
   `_visual_container` so the host is the widget that contains the title, not the first
   host on the page. Pair each caption with the next `DD:HH:MM:SS` after it in that
   container. Do not assign a duration from another widget.
3. **Durations stay display strings.** Match the existing `_DURATION` pattern. Do not pass
   these widgets through `KPI.read_text` or `extract_kpi_value_text`. Do not convert the
   text to a timedelta and do not strip the colons.
4. **Returned shape.** The dict includes `inquiries_summary`, `request_closing_times`
   (`average`, `maximum`), and `response_wait_times` (`average`, `maximum`). A caption
   that is not in its container is omitted so `_assert_tree` fails that golden key. The
   test is not changed and does not skip while the widgets are on screen.
5. **Wait.** Before reading a duration widget, expect its title to be visible, bounded by
   `self.timeout`. No `wait_for_timeout` and no `networkidle`. Locator names, comments,
   and any log text stay English. Hebrew is limited to the title and caption constants.
6. **Layers.** Edit `pages/public_inquiries/page.py` only. `ממוצע`, `מקסימלי`, and the
   two widget titles stay on the page. Layer 2 `KPI` remains a single-value card reader.
   This pair of captions is Hasbara-only, so it is not added to `core/components/`.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/public_inquiries/page.py` | EDIT | `read_kpi_metrics` walks the inquiries widget and both duration widgets |
| `tests/sanity/public_inquiries_dashboard/test_data_validation.py` | UNCHANGED | Already asserts the full `kpi_metrics` tree |
| `data/hasbara/db_sanity.yaml` | UNCHANGED | Current closing-times strings are `00:04:35:46` and `16:14:33:22` |
| `core/components/kpi.py`, `core/portal/`, `db/` | NONE | Off-limits for this revision |

Gate for the duration-widget revision: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen1_kpi_match_golden`.
Layer 0 and Layer 2 are not edited, so fleet smoke is not a new gate.

### Revision 2026-11-10 — visible inquiries counts

Where this revision disagrees with an earlier bullet about how
`inquiries_summary` is located or when it is read, this revision wins.
Duration widgets, charts, grids, the date-picker toggle, and the
`last_updated` removal stay as previously planned. This revision does not
edit the golden YAML or the sanity test.

The Screen 1 widget the report titles around the four count cards ("פניות")
displays `total_requests` as `1,324` and `open_requests` as `49`. Those match
`kpi_metrics.inquiries_summary` (`1324` and `49`). `read_kpi_metrics()`
returned `1,321` and `48`. `_read_kpi_value` asks the whole iframe for
`img[aria-label*='{measure_id}']` and keeps `.first`. That node can be a
hidden or stale SVG image whose `aria-label` still ends in the previous
count. The visible `<text>` inside the widget is never required to win.
`_wait_for_report_settled` then treats screen 1 as ready when the landing
phrase is visible and any `CountTotalTickets` image exists, including a
hidden one, so the read can run while the October filter is still painting.

1. **Wait on the inquiries widget after the date filter.** `apply_date_range`
   still commits the YAML start and end, then settles. For screen 1 that
   settle includes the inquiries widget, not only the landing phrase. The
   same wait runs at the start of `read_kpi_metrics`, so an early return
   from `apply_date_range` (inputs already show the range) still waits
   before the counts are extracted. Inside the widget container, a visible
   loading spinner or `[aria-busy='true']` must be hidden. Then the visible
   value nodes for `CountTotalTickets` and `CountOpen` must be visible and
   the same on two successive reads. The bound is `self.timeout`. No
   `wait_for_timeout` and no `networkidle`. The waiter does not search for
   the literals `1324`, `1,324`, or `49`. Those strings are what the current
   October widget shows; the golden assert is what checks them. A waiter
   that requires the golden integers would turn a real mismatch into a
   timeout and would skip the `ui=` / `golden=` message.
2. **Read the visible node inside the widget.** Resolve one container: the
   smallest visual host that contains both `סה"כ פניות` and `פניות פתוחות`.
   When the live DOM has a heading whose accessible name is `פניות`, that
   heading's host is the container only if both card titles are inside it.
   A page-wide substring match on `פניות` is not the container (chart titles
   contain the same word). For each of the four inquiries leaves, read a
   visible `svg text` (or other visible text node) that belongs to that card
   inside this container. A visible `img[aria-label*='{measure_id}']` inside
   the same container is the measure fallback. Hidden, `aria-hidden`,
   zero-size, and iframe-wide `.first` images are not candidates. When the
   visible text and an image `aria-label` disagree, keep the visible text.
   The four leaves stay `total_chats`, `total_requests`, `open_requests`, and
   `closed_requests`. Counts stay display strings (`1,324` still matches
   integer `1324` in the test).
3. **Assertions stay strict.** `test_hasbara_screen1_kpi_match_golden` keeps
   calling `_assert_tree` on the full `kpi_metrics` tree. `total_requests`
   and `open_requests` stay in that comparison. The test does not `pop`
   either key, and the page does not omit them when the widget is on screen.
4. **Layers and language.** Edit `pages/public_inquiries/page.py` only.
   `פניות` and the card titles stay on the page. `core/components/kpi.py`
   stays a single-value card reader and is not taught this container.
   Locator names, wait conditions, and comments stay English. Hebrew is
   limited to the title constants.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/public_inquiries/page.py` | EDIT | Screen 1 settle and `read_kpi_metrics` wait for the inquiries widget, then read its visible values |
| `tests/sanity/public_inquiries_dashboard/test_data_validation.py` | UNCHANGED | `_assert_tree` still compares `total_requests` and `open_requests` |
| `data/hasbara/db_sanity.yaml` | UNCHANGED | `1324` and `49` stay the golden integers |
| `core/components/kpi.py`, `core/portal/`, `db/` | NONE | Off-limits for this revision |

Gate for this revision: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen1_kpi_match_golden`.
Layer 0 and Layer 2 are not edited, so fleet smoke is not a new gate.

### Revision 2026-11-11 — iframe body script and visible KPI / survey nodes

Where this revision disagrees with an earlier bullet about how the inquiries
settle runs JavaScript, or about which DOM node a KPI or survey locator may
match, this revision wins. Duration pairing, the golden tree, the date-picker
toggle, the virtualized grid, and the `last_updated` removal stay as previously
planned. This revision does not edit the golden YAML or the sanity tests.

A live run raised `AttributeError: 'FrameLocator' object has no attribute 'evaluate'`.
`_expect_inquiry_counts_settled` assigns `self._dashboard_iframe().content_frame`.
In Playwright Python that property is a `FrameLocator` (the same object
`ReportShell._report_frame` returns). `FrameLocator` exposes `locator` and the
`get_by_*` queries. It does not expose `evaluate` or `wait_for_function`. The
following `iframe.wait_for_function(_INQUIRY_SETTLED_JS)` fails the same way
once the direct `evaluate` call is removed. The token reset and the settle
predicate both have to run in the report document.

KPI and survey reads still attach to hidden nodes. `_any_kpi_visible` treats
any `img[aria-label*='CountTotalTickets']` as present, including a hidden or
stale SVG. `_read_duration_widget` and the screen-ready title checks use
`get_by_text(...).first` with no visibility filter, so a hidden ARIA tooltip
that contains the same Hebrew is the node `expect` waits on.
`_inquiries_container` can select a host that is not the painted widget.
`_metric_under_box` walks every element under the iframe body and keeps a short
numeric string whose box sits near the label, including a tooltip or a stale
SVG that Playwright does not treat as visible. Survey totals then disagree with
`surveys_summary`, or the locator times out, before `_assert_tree` prints
`ui=` and `golden=`.

1. **Evaluate on the iframe body.** `_expect_inquiry_counts_settled` keeps the
   report `FrameLocator` from `_report_frame()`. It does not call `.evaluate`
   or `.wait_for_function` on that object. The token reset is
   `frame.locator("body").evaluate("() => { window.__vcInquiryToken = ''; }")`.
   The settle predicate uses that same body:
   `expect.poll(lambda: body.evaluate(_INQUIRY_SETTLED_JS), timeout=self.timeout).to_be(True)`.
   Playwright runs `locator.evaluate` in the element's frame, so `document` and
   `window` in the script are the report iframe. A `false` return is retried
   until two successive visible total and open counts match. A timeout still
   raises `AssertionError("Inquiries widget counts did not settle")`. No
   `wait_for_timeout` and no `networkidle`. `ReportShell._report_frame` stays a
   `FrameLocator`. This revision does not convert it into a `Frame`.
2. **Visible widget and KPI locators.** `_wait_for_inquiries_widget`,
   `_inquiries_container`, `_visible_svg_runs`, `_visible_measure_text`,
   `_read_duration_widget`, `_any_kpi_visible`, and the screen 1 ready title
   apply `.filter(visible=True)` before `.first` and before a count is accepted.
   A node inside `[role='tooltip']`, a node with `aria-hidden='true'`, and a
   node with an empty box are not candidates. The settle script applies the
   same exclusions to the host it picks and to `svg text`, so a tooltip or a
   stale hidden SVG cannot form the stability token. The waiter still does not
   search for `1324`, `1,324`, or `49`. After a date commit, screen 1 settle
   still calls this wait, and `read_kpi_metrics` still calls it before the
   count loop.
3. **Survey cards wait, then read visible metrics.** After a screen 3 tab click
   or date apply, `_wait_until_ready("screen_3")` and `read_satisfaction` wait
   until each survey section title the page already knows (`מוקד טלפוני`,
   `מענה כתוב`, `בקרת איכות`) is visible, any visible spinner in those cards
   is hidden, and a visible metric-shaped string (a number, `לא ידוע`, or
   `אין מידע`) under the card is unchanged on two reads. The bound is
   `self.timeout`. The waiter does not search for `1,062`, `129`, or `39`.
   `_metric_under_box` skips hidden, `aria-hidden`, zero-size, and
   `[role='tooltip']` nodes. Label lookups stay on `.filter(visible=True)`.
4. **Assertions stay strict.** `tests/sanity/public_inquiries_dashboard/test_data_validation.py`
   is not edited. `_assert_tree` still compares the full `kpi_metrics` tree,
   `surveys_summary`, and the other screen blocks. No key is popped, skipped,
   or weakened. `data/hasbara/db_sanity.yaml` is not edited.
5. **Language and layers.** Edit `pages/public_inquiries/page.py` only. New
   and edited locators, wait conditions, comments, and docstrings are English.
   Hebrew stays in the Power BI title and caption constants. `core/portal/`
   and `core/components/` are not edited.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/public_inquiries/page.py` | EDIT | Inquiry token and settle script run on `body`; KPI and survey locators require visible, non-tooltip nodes; survey cards wait after a date or tab change |
| `tests/sanity/public_inquiries_dashboard/test_data_validation.py` | UNCHANGED | `_assert_tree` still compares KPIs, survey summaries, and the other screen blocks |
| `data/hasbara/db_sanity.yaml` | UNCHANGED | Golden file stays the source of truth |
| `core/portal/`, `core/components/`, `db/` | NONE | Off-limits for this revision |

Gate for this revision: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k "test_hasbara_screen1_kpi_match_golden or test_hasbara_screen3_surveys_match_golden"`.
Layer 0 and Layer 2 are not edited, so fleet smoke is not a new gate.

### Revision 2026-11-11 — Show as a table for detail grids

Where this revision disagrees with an earlier bullet that
`PublicInquiriesPage._read_grid` scrolls the on-canvas grid, this revision wins.
Chart reads, the data-cell wait, the virtualized collector, duration widgets,
the inquiries settle, and the visible-node filters stay as previously planned.
This revision does not edit the golden YAML or the sanity tests. It does not
change the screen 4 rendered gate.

`read_investigation_rows` and `read_feedback_rows` return `ui=[]`, or rows whose
off-screen columns are blank. `handling_time` (`זמן טיפול`) is the reported
example. `_read_grid` reads the painted Power BI table. That visual virtualizes
columns: a cell outside the horizontal viewport is clipped or absent from the
DOM. `collect_virtualized_rows` already moves `scrollLeft`, and that sweep still
does not materialize the missing cells. The golden compare then fails the field
or the empty list.

1. **Open the tabular view from the visual container.** `_read_grid` locates the
   visual host that contains the visible screen grid: the smallest
   `visualContainer` / `visualContainerHost` ancestor of that grid, the same host
   shape `_visual_container` already uses. It does not right-click a single cell.
   It does not grow a second context-menu implementation. It calls
   `VisualTable.read_rows(container, name=...)`. That method right-clicks with
   `button="right"`, clicks the visible menu item `הצג כטבלה` or
   `Show as a table`, and waits until a data cell is visible. `name` is English
   (`investigation grid` or `feedback grid`) and is only for the assertion text.
   Hebrew stays in the existing header-alias maps and in the Power BI chrome
   strings already in Layer 2.
2. **Read the expanded grid.** After the Back to report button is visible,
   `VisualTable._visible_table` returns the data-view grid. When more than one
   visible grid or table has a data cell, choose the grid that shares an
   ancestor with that button. If several still match, choose the one with the
   most column headers. A single visible grid keeps today's behavior, so a
   chart's Show as a table is unchanged. `collect_virtualized_rows` still scrolls
   the chosen grid vertically. The canvas grid is not where `handling_time` comes
   from, and it is not a fallback if the menu click fails. Each data-view row is
   header → cell text. The page maps those headers through
   `_INVESTIGATION_HEADERS` or `_FEEDBACK_HEADERS` and `_field_for_header`. A
   `\x00` suffix that `_row_mapping` appends to a repeated header is stripped
   before that lookup. Blank cells stay `""`. A row whose first cell is a total
   label (`סה"כ` or `סה״כ`) is dropped on the page. `read_rows` itself still does
   not drop total rows. The page dedupes on `request_id` or `inquiry_id`. Extra
   UI rows stay ignored. `rows_to_label_values` and the `read_rows` signature
   stay as in the 048 contract.
3. **Close the data view before returning.** Once the menu item was clicked,
   `read_rows` clicks `חזרה לדוח` or `Back to report` in `finally` and waits until
   that button is hidden. A menu that never opened is dismissed with Escape. The
   page does not add a second close. After `read_rows` returns, `_read_grid`
   expects this screen's existing ready locator to be visible again, bounded by
   `self.timeout`, so the next test sees the dashboard. No `wait_for_timeout`
   and no `networkidle`.
4. **Empty versus failed open.** When `grid_is_rendered` is false, the test still
   skips. When the grid is rendered and the expanded table has zero data rows,
   the reader returns `[]` and the sanity test fails with `ui=[]` (FR-011). When
   the grid is rendered and the menu item, the back button, or the data cell
   never appears, `read_rows` raises. `_read_grid` does not catch that error and
   turn it into `[]`.
5. **Language and layers.** Edit `pages/public_inquiries/page.py` and, for the
   multi-grid choice only, `core/components/visual_table.py`. New and edited
   locators, wait conditions, method names, comments, and docstrings are English.
   Hebrew header aliases stay on the page. `core/portal/`, `virtual_grid.py`'s
   public signature, the golden YAML, and the sanity tests are not edited.
   `request_id`, `inquiry_id`, and `handling_time` do not appear in `core/`.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/public_inquiries/page.py` | EDIT | Detail grids open Show as a table through `VisualTable`, map headers, then confirm the dashboard is back |
| `core/components/visual_table.py` | EDIT | When several grids are visible, read the data-view grid. Public signature unchanged |
| `tests/sanity/public_inquiries_dashboard/test_data_validation.py` | UNCHANGED | Still compares every golden investigation and feedback field |
| `data/hasbara/db_sanity.yaml` | UNCHANGED | `handling_time` and `comments` stay the golden strings |
| `core/portal/`, `core/components/virtual_grid.py`, `db/` | NONE | Off-limits for this revision |

Gate for this revision: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k "test_hasbara_screen2_investigation_rows_match_golden or test_hasbara_screen4_feedback_rows_match_golden"`.
`VisualTable` changes, so `pytest tests/ui/fleet_dashboard/` must pass at 100% and
`pytest tests/unit/test_visual_table_rows.py` must stay green.

### Revision 2026-11-11 — satisfaction sub-tab locator

Where this revision disagrees with an earlier bullet that
`select_satisfaction_tab` clicks through `_click_tab` / `_tab_locator`, this
revision wins. Page-rail navigation for the four screens, the survey-card
wait, chart reads, and the golden compare stay as previously planned. This
revision does not edit the golden YAML, the sanity test, or `core/`.

`test_hasbara_screen3_distributions_match_golden` calls
`page.select_satisfaction_tab(service["active_tab"])`. The YAML block repeats
`active_tab`, `question`, and `responses`. PyYAML keeps the last value, so the
label passed in is `אופן מקצועי` and the bars compared afterward are the
professional-manner distribution. Those labels are the sub-tabs drawn above
the chart in the `התקבלות השירות` section. `select_satisfaction_tab` calls
`_click_tab`, and `_tab_locator` only matches the page rail: a visible link,
image, or button whose accessible name matches
`ניווט בין עמודים . {label}`. `אופן מקצועי` is not a page. Playwright raises
`TimeoutError`, or reports that the element was not found, before
`service_reception.responses` is read.

1. **Leave the page rail alone.** `_click_tab` and `_tab_locator` stay the
   navigation for screens 1–4. They still anchor on
   `ניווט בין עמודים . {label}` so `משובים` does not select `תחקור משובים`.
   `select_satisfaction_tab` stops calling `_click_tab`.
2. **Exact visible control in the report frame.** The method takes the report
   `FrameLocator` from `_report_frame()`. It looks for the exact label, in this
   order, and clicks the first paintable match from `_first_outside_tooltip`:
   a `tab`, `button`, or `link` whose accessible name equals the label
   (`exact=True`), then `get_by_text(label, exact=True)`. Every branch applies
   `.filter(visible=True)` before a count is accepted and before `.first`.
   A node inside `[role='tooltip']`, a node with `aria-hidden='true'`, and a
   node with an empty box are not candidates. When a visible visual host
   contains the section title `התקבלות השירות`, a match inside that host wins,
   because the sub-tabs sit above that chart. If that host has no visible
   match, the same exact locator runs on the report frame. The search does not
   use the page-rail pattern and does not substring-match, so `אופן מקצועי`
   is not `מקצועיות`.
3. **Click, then the phrase that is already waited on.** Expect the filtered
   locator to be visible, bounded by `self.timeout`, then click it. A visible
   spinner inside the section host is hidden with the same spinner locator the
   page already uses. The method still expects the label phrase to be visible
   after the click. No `wait_for_timeout` and no `networkidle`. The method
   still does not load YAML. The test still passes `service["active_tab"]` and
   still compares `service_reception.question` and `service_reception.responses`.
   A click that lands on the wrong distribution still fails with `ui=` and
   `golden=`.
4. **Language and layers.** Edit `pages/public_inquiries/page.py` only. New
   and edited locators, wait conditions, method names, comments, and
   docstrings are English. Hebrew stays in the section-title constant and in
   the label string the test already passes. `core/portal/` and
   `core/components/` are not edited. The golden file is not rewritten to
   remove the duplicate keys.

| Path | Change | Purpose |
|------|--------|---------|
| `pages/public_inquiries/page.py` | EDIT | `select_satisfaction_tab` clicks the visible exact sub-tab in the report frame |
| `tests/sanity/public_inquiries_dashboard/test_data_validation.py` | UNCHANGED | Still passes `active_tab` and compares the courtesy responses |
| `data/hasbara/db_sanity.yaml` | UNCHANGED | The loaded `active_tab` stays `אופן מקצועי` |
| `core/portal/`, `core/components/`, `db/` | NONE | Off-limits for this revision |

Gate for this revision: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen3_distributions_match_golden`.
Layer 0 and Layer 2 are not edited, so fleet smoke is not a new gate.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `bind_dashboard`. The page
composes Layer 2 `Slicer`, `KPI`, `VisualTable`, and the new virtualized-grid collector.
No new package.

**Storage**: Golden record `data/hasbara/db_sanity.yaml` (unchanged). No warehouse query and
no `db/clients/hasbara.py`.

**Testing**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity`
is the golden compare (T017). Public Inquiries smoke
`pytest tests/ui/public_inquiries_dashboard/` is the freshness gate (`verify_freshness` must
stay green). Layer 2 changes, so Constitution III also requires
`pytest tests/ui/fleet_dashboard/` at 100% and `pytest tests/unit/test_visual_table_rows.py`
unchanged and green. `rows_to_label_values` is not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework. Domain page under `pages/public_inquiries/`.
Sanity tests under `tests/sanity/public_inquiries_dashboard/`.

**Performance Goals**: N/A. One catalog open per test, one date-range apply, one tab switch
when the screen is not the landing page, then the reads that screen needs. A grid read
scrolls by one container height per pass and stops when a pass adds no row id.

**Constraints**:

- Expand `pages/public_inquiries/page.py`. Keep `PublicInquiriesPage`, `DASHBOARD_SEARCH_TERM`,
  and `_report_ready_locator` so the smoke import keeps working (FR-015, FR-016, AC-004).
- Leave `core/portal/` unchanged (Constitution I, AC-001). The virtualized-grid collector
  and the Show-as-a-table data-row wait live in `core/components/` and stay report-agnostic
  (Constitution II, VII, AC-005).
- Leave alerts, credit, status-picture, and fleet page sources unchanged. Fleet smoke is
  still run, because `VisualTable` is shared (Constitution III).
- Leave `db/`, the root `conftest.py`, and every YAML file unchanged (FR-015).
- Read the period from `dashboard_info.date_range`. Unlock the inputs with one click on
  the filter-bar toggle labeled `כלל התאריכים` or `יום נוכחי` when they are hidden or
  disabled, then fill start and end. Fail if the inputs never appear. Leave `הכל`
  unselected (FR-001, FR-002, FR-003).
- After a date commit and after each tab click, wait until a visible report spinner is
  hidden and the screen title or grid locator is visible. On screen 1, also wait until
  the inquiries widget spinner is hidden and its visible total and open texts have
  settled. That settle resets and polls `window.__vcInquiryToken` through
  `frame.locator("body").evaluate`, not through `FrameLocator.evaluate` or
  `FrameLocator.wait_for_function`. On screen 3, wait until the survey section
  titles are visible and a visible metric under each card has settled. KPI,
  duration, and survey locators use `.filter(visible=True)` and ignore tooltips,
  `aria-hidden` nodes, and empty boxes. No fixed sleep and no `networkidle` (FR-009).
- Do not read `last_updated`. The key is absent from the golden file. Leave `verify_freshness`
  inherited (FR-014, FR-016).
- Empty UI data against a non-empty golden block fails. Skip only when the visual or grid is
  absent (FR-011).
- Assertion text includes the YAML path, the UI actual, and the golden expected (FR-012).
- Integer golden fields compare as ints. String golden fields stay display strings (FR-013).
- Test names, locator names, and comments in new functions stay English (FR-010).
- Chart reads and screen 2 / screen 4 detail grids go through `VisualTable`. The page
  locates the visual host and calls `read_rows` (right-click, `button="right"`, then
  `הצג כטבלה` or `Show as a table`). After the data view opens, the reader waits for a
  data cell and collects rows from that expanded grid. When more than one grid is
  visible, the grid tied to the Back to report button wins, then the one with the most
  column headers. The page maps Hebrew headers and dedupes on `request_id` or
  `inquiry_id`. `read_rows` clicks Back to report before it returns, and the page then
  expects the screen ready locator to be visible. The canvas grid is not a fallback
  for `handling_time`. Locators, waits, method names, and comments stay English.
- Screen 1 `read_kpi_metrics` walks every metric-bar widget. After the date
  filter, it waits until the inquiries widget spinner is hidden and the
  visible `CountTotalTickets` and `CountOpen` texts have settled. The token
  reset and the settle script run on the iframe `body`. Those four counts are
  the visible text inside the host that contains `סה"כ פניות` and
  `פניות פתוחות`. A hidden measure image, a tooltip, and a stale SVG are not
  the value. Every KPI locator uses `.filter(visible=True)`. Duration widgets
  stay inside `זמני סגירת פנייה` and `זמני המתנה למענה`, from the `ממוצע` and
  `מקסימלי` captions, as `DD:HH:MM:SS` strings. Those titles stay on the page.
  Screen 3 waits for the survey cards to finish painting, then reads visible
  metrics only. The sanity test still compares `total_requests`,
  `open_requests`, and `surveys_summary`.
- `select_satisfaction_tab` does not call `_click_tab`. It clicks a visible
  `tab`, `button`, or `link` whose accessible name equals the label, or the
  exact visible text of that label, inside the report frame. `.filter(visible=True)`
  is applied before the click. A match inside the `התקבלות השירות` host is
  preferred. Tooltips, `aria-hidden` nodes, and empty boxes are skipped. The
  page-rail pattern `ניווט בין עמודים` stays on `_tab_locator` for the four
  screens. Locators, waits, method names, and comments stay English.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/public_inquiries/page.py` | EDIT | Period toggle, readers, screen 4 header gate; duration widgets; inquiries counts from the visible widget after a body-level settle; visible KPI and survey locators; detail grids via Show as a table; satisfaction sub-tab is an exact visible control in the report frame |
| `core/components/virtual_grid.py` | ADD | Report-agnostic scroll-and-dedup collector. Not the canvas-grid source for detail rows |
| `core/components/visual_table.py` | EDIT | Data-cell wait, then the collector. Prefer the expanded data-view grid when several grids are visible. Public signature unchanged |
| `core/components/__init__.py` | EDIT | Export the collector next to `VisualTable` |
| `tests/sanity/public_inquiries_dashboard/test_data_validation.py` | EDIT | Remove `assert_last_updated` and both `info["last_updated"]` reads |
| `tests/ui/public_inquiries_dashboard/` | UNCHANGED | `verify_freshness` stays |
| `data/hasbara/db_sanity.yaml` | UNCHANGED | Already has no `last_updated` |
| `docs/COVERAGE_CATALOG.md` | EDIT | Golden map; no last-updated row |
| `core/portal/`, `db/`, alerts, credit, fleet sources, root `conftest.py` | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `PublicInquiriesPage` already subclasses `ReportShell`. Login,
  catalog search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0. This
  slice calls the inherited caption reader and does not re-implement it.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Tab labels, chart titles, slicer names,
  column headers, `request_id`, and `inquiry_id` stay on the domain page. The new Layer 2
  module accepts a caller-supplied row id and a caller-supplied visible-row reader. Root
  `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS with a required gate.
  Smoke `verify_freshness` stays. `VisualTable.read_rows` keeps its public signature, and
  `rows_to_label_values` is not edited. Because Layer 2 is edited, fleet smoke
  `pytest tests/ui/fleet_dashboard/` must pass at 100% before this slice is done, and
  `tests/unit/test_visual_table_rows.py` must stay green. Public Inquiries smoke remains
  the freshness gate.
- **Page object discipline (IV)**: PASS. Tests call page methods (date apply, tab open,
  readers). Locators live on the page. Test bodies compare values.
- **Warehouse as source of truth (V)**: PASS with a recorded deviation. Assertions compare
  the UI to `data/hasbara/db_sanity.yaml`, not a live SQL query. The user named that golden
  file as the baseline. Layer 0 still has no business SQL. Same justification as 046/044/039.
- **Observability (VI)**: PASS. Existing screenshot, trace, HTML, and CSV hooks apply to the
  sanity module through the shared fixtures. No logging path is removed. The coverage catalog
  gains a Hasbara section.
- **Extract shared behavior only (VII)**: PASS. The new collector earns its place: the page
  and `VisualTable` both reimplement the same virtualized scroll, and the page copy walks
  ancestors only, so rows below the viewport never load. Header maps and id field names
  stay on the page. The collector is not added to `core/portal/`. The last-refresh reader
  stays the existing Layer 0 method and is not called from the sanity tests. The Screen 1
  duration widgets are a Hasbara pair of captions, so their parser stays on the page and
  is not added to Layer 2 `KPI`. The inquiries-widget wait and the visible-text
  locator are also Hasbara page behavior. They do not move into `core/components/kpi.py`.
  The 2026-11-11 body `evaluate` and the tooltip filter stay on the page.
  `ReportShell._report_frame` remains a `FrameLocator`. The detail-grid
  right-click stays inside `VisualTable.read_rows`. Choosing the data-view
  grid when several grids are visible is generic Power BI behavior: it uses the
  Back to report button and the column-header count, not a Hasbara field name.
  The page does not copy the menu click. The satisfaction sub-tab click stays on
  `PublicInquiriesPage`. It does not teach `core/` the labels `התקבלות השירות`
  or `אופן מקצועי`, and it does not replace the page-rail locator used by the
  four screens.

**Result**: No unjustified violations. Principle V deviation is recorded in Complexity Tracking.
The 2026-11-10 KPI revisions and the 2026-11-11 frame revision do not add a gate failure.
The Show-as-a-table detail-grid revision edits `VisualTable`, so the existing fleet-smoke
gate still applies. The satisfaction sub-tab revision edits only the page, so it
does not add a fleet-smoke gate.

## Project Structure

### Documentation (this feature)

```text
specs/049-hasbara-ui-validation/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── hasbara-ui-validation.md
│   └── virtual-grid.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
pages/public_inquiries/
└── page.py                          # EDIT: PublicInquiriesPage gains readers
      ├── DASHBOARD_SEARCH_TERM      # unchanged "ניתוח פניות הסברה"
      ├── _report_ready_locator()    # unchanged exact landing phrase
      ├── apply_date_range(text)     # one toggle click if inputs hidden; fill start/end
      ├── _wait_for_report_settled  # spinner hidden + ready locator; no sleep
      ├── open_screen(screen_id)     # tab click + title/grid wait
      ├── read_slicer_values(ids)    # visible text; הכל is not clicked
      ├── read_kpi_metrics()         # body-level settle, visible inquiries text, then both duration widgets
      ├── read_screen1_charts()      # compose VisualTable
      ├── read_investigation_rows()  # Show as a table on the grid visual; map request_id
      ├── read_satisfaction()        # cards, bars, channels
      ├── select_satisfaction_tab() # exact visible sub-tab in the report frame; not the page rail
      └── read_feedback_rows()       # Show as a table on the grid visual; map inquiry_id

core/components/virtual_grid.py      # ADD: vertical scroll inside the grid it is given
core/components/visual_table.py      # EDIT: data-cell wait; prefer the expanded data-view grid

data/hasbara/db_sanity.yaml          # UNCHANGED

tests/ui/public_inquiries_dashboard/
├── conftest.py                      # UNCHANGED
└── test_dashboard_smoke.py          # UNCHANGED verify_freshness

tests/sanity/public_inquiries_dashboard/
├── conftest.py                      # ADD fixture
└── test_data_validation.py          # ADD comparison rules

docs/COVERAGE_CATALOG.md             # ADD section 10
core/portal/  db/  alerts  credit  fleet sources   # UNCHANGED
```

**Structure Decision**: Validation Core layout. Domain behavior stays on
`pages/public_inquiries/page.py`. Show as a table, including the right-click and the
return to the dashboard, stays in Layer 2 `VisualTable`. Detail grids call that reader
on the visual host and only map headers on the page. The virtualized scroll loop stays
in Layer 2 and runs on the expanded grid. `ReportShell` is not a grid reader. No
`db/clients/hasbara.py`. The suite stays under `tests/sanity/` with the other YAML
suites.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: tests compare the Public Inquiries report to `data/hasbara/db_sanity.yaml` instead of a live warehouse query | The user named that golden file as the baseline for October 2026. The numbers are a snapshot under the YAML date range and `הכל` filters. | A Hasbara SQL client would ignore the file and fail whenever the warehouse moves past the snapshot. Features 044 and 046 already recorded this deviation for the same golden-file style. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- `PublicInquiriesPage` still inherits `ReportShell`. `verify_freshness` stays in Layer 0.
  The page does not gain a date parser. Sanity tests do not read `last_updated`.
- The period toggle (`כלל התאריכים` / `יום נוכחי`), the bilingual date inputs, tab
  labels, slicer definitions, chart titles, and grid header maps live on the page.
  The toggle is not a `Slicer` kind and is not added to `core/components/`. Tests do
  not grow locators.
- `apply_date_range` clicks that toggle at most once, and only when the start and end
  inputs are hidden or disabled. It then waits on the inputs. It does not return
  successfully when the fill finds no field.
- Settle waits use a hidden spinner plus the screen ready locator. On screen 1 the
  inquiries widget is part of that settle: its spinner is hidden and its visible
  total and open texts are stable. `networkidle` and `wait_for_timeout` are not
  the ready signal.
- Charts and the screen 2 / screen 4 detail grids use `VisualTable.read_rows` with a
  container the page locates. The detail-grid container is the visual host of the
  visible grid. The call right-clicks that host and opens Show as a table. After the
  data view is open, the reader waits for a visible data cell and, when several grids
  are visible, reads the one tied to Back to report (then the widest header set).
  Vertical collection still calls `collect_virtualized_rows` on that grid. `read_rows`
  clicks Back to report before returning, and the page then expects the screen ready
  locator. The canvas grid is not a fallback. `core/portal/` is not extended.
  `request_id`, `inquiry_id`, and `handling_time` stay on the page.
- Sanity tests use a local fixture. Root `conftest.py` is untouched. The smoke module still
  imports `PublicInquiriesPage` and calls `verify_freshness()`.
- Alerts, credit, fleet page sources, `core/portal/`, `db/`, and the golden YAML are absent
  from the edit list. Fleet smoke is executed because `VisualTable` changed.
- Empty parsed data fails when the golden block is non-empty. Skip is limited to a visual
  whose title or grid is absent.
- Public Inquiries smoke remains the freshness gate. Fleet smoke is required for the
  earlier `VisualTable` edit. The 2026-11-10 KPI revision does not edit Layer 0 or Layer 2.
- `read_kpi_metrics` still returns the nested `kpi_metrics` shape. It walks the inquiries
  widget and both duration widgets. `ממוצע`, `מקסימלי`, and the widget titles stay on
  `PublicInquiriesPage`. `core/components/kpi.py` is not taught those labels, and duration
  strings are not passed through `extract_kpi_value_text`.
- After the October date filter, screen 1 waits until the inquiries widget has no visible
  spinner and the visible total and open measures have the same text on two reads.
  The reset and the poll call `locator("body").evaluate` on the report `FrameLocator`.
  `total_requests` and `open_requests` come from that visible text. The sanity test still
  passes both keys through `_assert_tree`. The page does not embed `1324` or `49`.
- KPI, duration, and survey locators use `.filter(visible=True)`. Tooltips,
  `aria-hidden` nodes, empty boxes, and stale hidden SVGs are not values.
  Screen 3 waits for its survey titles and a stable visible metric before
  `read_satisfaction` returns. `surveys_summary` still goes through `_assert_tree`.
  The page does not embed `1,062`, `129`, or `39`.
- `select_satisfaction_tab` clicks a visible exact `tab`, `button`, `link`, or
  text node in the report frame. A match inside the `התקבלות השירות` host is
  preferred. `.filter(visible=True)` drops hidden and stale nodes. Tooltips are
  excluded with the existing paintable check. `_tab_locator` still serves the
  four report pages. The method does not load YAML. The sanity test still
  passes `active_tab` and still compares the courtesy responses. The loaded
  label is `אופן מקצועי` because PyYAML keeps the last duplicate key. That
  string is not copied into `core/`.

**Result**: No unjustified violations. The earlier "do not edit `core/`" constraint is
replaced by "do not edit `core/portal/`, and do not put report labels in `core/components/`".
The KPI revisions and the frame-body revision add no new violation. The detail-grid
revision edits only the report-agnostic grid choice inside `VisualTable` and the page's
call into `read_rows`. Fleet smoke remains the contract gate for that edit. The
satisfaction sub-tab revision adds no layer violation and no new gate.
