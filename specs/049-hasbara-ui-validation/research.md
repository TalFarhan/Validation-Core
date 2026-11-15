# Phase 0 Research: Hasbara Dashboard UI Sanity Validation

All Technical Context items are resolved from the golden file, `PublicInquiriesPage`, and the
credit golden-YAML suite (046). No **NEEDS CLARIFICATION** remains.

## R1 — New sanity module on the existing page

- **Decision**: Edit `pages/public_inquiries/page.py` in place and add
  `tests/sanity/public_inquiries_dashboard/`. Keep
  `tests/ui/public_inquiries_dashboard/test_dashboard_smoke.py` and its conftest as they are.
- **Rationale**: The page already subclasses `ReportShell` with catalog term
  `ניתוח פניות הסברה`. The golden file exists and no suite reads it. The smoke import path
  is `pages.public_inquiries.page.PublicInquiriesPage`. Expanding that class preserves AC-004.
- **Alternatives considered**: A second page class such as `HasbaraPage`. Rejected — the
  catalog report already has one page object. Placing the suite under `tests/e2e/`. Rejected —
  `tests/e2e/` in this repo is the warehouse-parity family, and this compare has no SQL.
  A new `db/clients/hasbara.py`. Rejected — the user named the YAML as the baseline.

## R2 — Two-step date picker, then read `הכל`

- **Decision**: `apply_date_range` takes `dashboard_info.date_range` and splits once on
  ` - ` into start and end. In the current file those are `01/10/2026` and `31/10/2026`.
  When `read_date_range()` already equals that string, the method returns and does not
  touch the period toggle. Otherwise, when the Start Date and End Date inputs are hidden
  or disabled, it clicks the global filter-bar toggle once. That toggle is the visible
  action button whose text is `כלל התאריכים` or `יום נוכחי`. The click is what exposes
  `input[aria-label^='תאריך התחלה']` / `Start date` and `תאריך סיום` / `End date`. The
  method then waits until both inputs are visible and enabled, fills start, commits with
  Enter, fills end, commits with Enter, and waits for the report to settle. If the inputs
  never appear, it raises. It does not return as though the range were applied. Slicer
  values are read through `Slicer.control` and compared to `active_filters`. Hours,
  Language, Platform, Topic, and Settlement are included when visible. The value `הכל`
  is never passed to `Slicer.select`.
- **Rationale**: A live run of the first suite left the report on `יום נוכחי` (today) or,
  after one unaided click, on all dates. `apply_date_range` looked only for visible date
  inputs, found none, and returned. The October golden numbers were then compared to the
  wrong period. The filter bar keeps the inputs locked until the relative-period toggle
  is clicked. The YAML string stays the source of the two dates, so a later edit of the
  file changes the typed values without a test edit. Screen 3 has a date range and no
  `active_filters` map. The five named slicers are the landing default and are asserted,
  not re-selected.
- **Alternatives considered**: Hardcoding `01/10/2026` and `31/10/2026` in the test.
  Rejected — FR-001 requires the YAML string. Filling the inputs without the toggle
  click. Rejected — the inputs are hidden or disabled on open, which is why the first
  run never typed a date. Clicking the toggle a second time when the inputs stay hidden.
  Rejected — one click swaps the label between `כלל התאריכים` and `יום נוכחי`; a second
  click returns to the other relative period and can hide the inputs again. Treating
  either label as a successful date range. Rejected — neither label is
  `01/10/2026 - 31/10/2026`. Clicking `הכל` on every slicer. Rejected — that re-selects
  the landing default and can reset the date. Adding a date-toggle kind to Layer 2
  `Slicer`. Rejected — the control is a report action button, and Constitution VII keeps
  that label on the domain page. The same rejection is recorded for credit toggles in
  feature 044.

## R3 — Which slicers exist on which tab

- **Decision**: Screens 1 and 2 assert `hours`, `language`, `platform`, and `topic` from
  their `active_filters`. Screen 4 asserts `information`, `service_orientation`,
  `professionalism`, `platform`, `settlement`, and `hours`. On every tab, Hours, Language,
  Platform, Topic, and Settlement are additionally read when `Slicer.control` for that id
  is visible, and a visible one must show `הכל`. A missing control is not a failure.
- **Rationale**: The user named those five filters for every tab. The YAML does not list
  Settlement on screens 1–3, and it does not list Language or Topic on screen 4. Screen 4
  also lists three survey slicers the user did not name. Asserting the golden map plus the
  visible members of the user's list covers both without requiring a slicer the report hides.
- **Alternatives considered**: Requiring all five controls on all four tabs. Rejected — screen
  3's golden block has no slicer map, and a hidden slicer would fail a correct report.
  Ignoring screen 4's information, service-orientation, and professionalism slicers.
  Rejected — they are in `active_filters` and FR-002 covers that map.

## R4 — Settle after the date commit and after each tab

- **Decision**: `open_screen` clicks the Hebrew tab (screens 2–4) and waits with Playwright
  `expect` until the screen's YAML title is visible and the screen's data locator is visible
  (a KPI card on screen 1, the investigation grid on screen 2, a survey card on screen 3,
  the feedback grid on screen 4). Screen 1 does not click a tab when those locators are
  already visible. Both `open_screen` and `apply_date_range` finish through
  `_wait_for_report_settled`: if the report iframe is showing a loading spinner (a visible
  node whose class contains `spinner`, or an `aria-busy` loading overlay), that node is
  expected hidden within `self.timeout`; then the screen ready locator is expected visible.
  A spinner that never existed is not a failure. The ready locator is the settle signal in
  that case.
- **Rationale**: FR-009 asks for a dynamic wait tied to the rendered screen. Changing the
  date and changing the tab both leave Power BI visuals stale until the spinner clears.
  The shared `ReportShell` timeout is the budget. Power BI keeps a live connection, so
  `networkidle` does not arrive and cannot be the signal the user described as an example
  of a dynamic wait.
- **Alternatives considered**: `page.wait_for_load_state("networkidle")` after the date
  commit and after the tab click. Rejected — the portal socket stays active, so the wait
  runs out even when the visuals are ready. `page.wait_for_timeout` for a fixed interval.
  Rejected — a sleep both flakes and hides a toggle click that never revealed the inputs.
  Requiring one specific spinner class copied from another report. Rejected — this report's
  spinner class is confirmed on the live iframe during implementation and stored as a
  constant on `PublicInquiriesPage`. A missing spinner falls through to the ready locator.

## R5 — Subset match, and fail versus skip

- **Decision**: Comparison walks golden keys and rows only. Extra UI keys, extra chart
  categories, and extra grid rows do not fail. Screen 2's row key is `request_id` (13 golden
  rows in the current file). Screen 4's row key is `inquiry_id` (6 golden rows). The reader
  scrolls the grid until each golden id is present or the scroll position stops changing.
  Replace an empty read with an assertion when the golden side is non-empty. Call
  `pytest.skip` only before the read, and only when the visual title or the grid role is
  absent.
- **Rationale**: Screen 1 records 1,324 requests and the investigation block stores a short
  sample, so full-grid equality would fail a correct report. A missing id is still a real
  miss. An empty reader and a missing visual must not look the same (same rule as 046).
- **Alternatives considered**: Requiring the grid length to equal the YAML list. Rejected —
  the YAML is a sample. Failing on extra chart categories. Rejected — leading charts may
  draw more bars than the golden top list. Keeping a skip on every empty list. Rejected —
  FR-011 requires a failure when the golden block has data.

## R6 — Value types follow the YAML node

- **Decision**: The page returns display text. The test compares using the golden node's
  type. An `int` expected value parses the UI text after removing commas and spaces. A
  `str` expected value compares the trimmed display text, including `"59%"`, `"100.0%"`,
  `"76.79%"`, `"00:04:16:36"`, `"1,062"`, `"לא ידוע"`, `"אין מידע"`, and `""`. Platform
  spelling is exact (`WhatsApp` versus `Whatsapp`). Bidi marks are stripped before compare.
  Durations are not parsed into timedeltas.
- **Rationale**: The file mixes integers (`total_requests: 1324`, `surveys_filled: 129`)
  with display strings (`surveys_sent: "1,062"`). One coercion rule would either drop the
  comma the file stored or reject a grouped integer on screen.
- **Alternatives considered**: Parsing every numeric-looking string to a float. Rejected —
  percents and durations would change shape, and `"1,062"` would collapse to `1062`.
  Case-folding platform names. Rejected — the file itself uses both spellings on purpose.

## R7 — Hourly trend and the courtesy tab

- **Decision**: `requests_by_hour_trend` asserts `series[].name` and `x_axis_labels` in
  golden order. Numeric points are ignored because the file has none. `service_reception`
  selects `active_tab` (`אופן אדיב` in the current file) before reading `responses`.
  `message_reception` is read on the question already shown (`האם המידע שהתקבל סייע`).
- **Rationale**: Inventing Y values would test data the golden file does not contain.
  The courtesy distribution is behind a tab the file names.
- **Alternatives considered**: Skipping the hourly chart. Rejected — FR-005 includes its
  labels. Reading the courtesy bars without selecting `active_tab`. Rejected — another
  question could be showing.

## R8 — Charts versus detail grids

- **Decision**: Breakdown and topic charts use `VisualTable.read_rows` on a container the
  page finds by the Hebrew visual title. The page maps header cells onto the YAML fields
  (`platform`, `language`, `type`, `topic`, `channel`, `level`, `count`, `percentage`).
  The two investigation grids are already tables: the page reads `role="grid"` or
  `role="table"` and maps Hebrew headers to YAML fields. Scrolling is the Layer 2
  collector in R12. Header maps and visual titles are constants on the page.
- **Rationale**: `VisualTable` is the shared Show as a table reader and stays report-agnostic
  when the caller supplies the container. Constitution VII keeps report tables on the domain
  page. Copying the credit page's private `_show_as_table_rows` would duplicate Layer 2.
- **Alternatives considered**: Parsing SVG bar labels. Rejected — Show as a table is the
  path this repo already trusts. Putting the Hebrew titles inside `core/components/`.
  Rejected — AC-001 and AC-005. Importing `CreditConsumptionPage` helpers. Rejected — that
  couples two reports.

## R9 — Assertion text and test names

- **Decision**: Every mismatch uses `{yaml_path}: ui={actual!r} golden={expected!r}`.
  Paths are rooted at `hasbara_dashboard`. Test functions, in
  `tests/sanity/public_inquiries_dashboard/test_data_validation.py`, are:

  - `test_hasbara_screen1_filters_match_golden`
  - `test_hasbara_screen1_kpi_match_golden`
  - `test_hasbara_screen1_charts_match_golden`
  - `test_hasbara_screen2_filters_match_golden`
  - `test_hasbara_screen2_investigation_rows_match_golden`
  - `test_hasbara_screen3_filters_match_golden`
  - `test_hasbara_screen3_surveys_match_golden`
  - `test_hasbara_screen3_distributions_match_golden`
  - `test_hasbara_screen4_filters_match_golden`
  - `test_hasbara_screen4_feedback_rows_match_golden`

  Each is marked `sanity`. Locator variables and comments in new functions are English.
- **Rationale**: FR-010 and FR-012. One function per block keeps a failure pointed at a
  screen. The `sanity` marker matches the other golden suites and the existing smoke marker.
- **Alternatives considered**: One parametrized test for all four filter checks. Rejected —
  the user asked for names in the `test_hasbara_screen1_kpi_match_golden` shape, and a
  parameter id is easier to miss in the report. A custom exception type. Rejected — a pytest
  assertion string is enough.

## R10 — Titles and the smoke ready locator

Superseded for the timestamp by R11. The title and ready-locator decisions below still hold.

- **Decision**: `dashboard_info.title`, `data_source`, and `platforms_included` are visible
  iframe phrases. `_report_ready_locator` stays the existing exact text `ניתוח פניות הסברה`
  so smoke navigation does not change. Screen 1 and screen 2 share a title; the grid versus
  the KPI card distinguishes them after the tab click.
- **Rationale**: AC-003. Changing the catalog-open ready locator to a long title could break
  the smoke open if that longer string is not its own exact text node.
- **Alternatives considered**: Asserting `SCREEN_TITLE == yaml_title` from a Python constant
  alone. Rejected — that never looks at the iframe.

## R11 — `last_updated` is gone from the golden file

- **Decision**: Delete `assert_last_updated` from
  `tests/sanity/public_inquiries_dashboard/test_data_validation.py` and delete both call
  sites (`test_hasbara_screen1_kpi_match_golden` and
  `test_hasbara_screen3_surveys_match_golden`). Do not read `info["last_updated"]`. Do not
  comment the helper out. Do not add a replacement caption assertion. Leave
  `verify_freshness` on the smoke test. Do not edit `data/hasbara/db_sanity.yaml`.
- **Rationale**: The current YAML `dashboard_info` blocks have no `last_updated` key. The
  two call sites raise `KeyError` before any golden compare. FR-014 now forbids that read.
  Commenting the calls out would leave a helper that still indexes a missing key if someone
  uncomments one line. The 24-hour freshness gate is a different check and stays inherited.
- **Alternatives considered**: Restoring `last_updated` in the YAML. Rejected — the key was
  removed on purpose. Comparing the caption without a golden value. Rejected — that
  duplicates `verify_freshness`.

## R12 — One virtualized-grid collector in Layer 2

- **Decision**: Add `collect_virtualized_rows(grid, read_visible, row_id, *, timeout_ms)` in
  `core/components/virtual_grid.py` and export it from `core/components/__init__.py`.
  `read_visible(grid)` returns the rows currently in the DOM. `row_id(row)` returns the
  dedup key; an empty key is ignored. The function stores the first row for each key.

  The scroll target is the grid node, or a descendant or ancestor, whose computed
  `overflow-y` is `auto`, `scroll`, or `overlay` and whose `scrollHeight` exceeds
  `clientHeight` by more than one pixel. When several match, the largest extra height wins.
  Each pass sets `scrollTop` forward by that node's `clientHeight`. After a move, the next
  `read_visible` runs. The loop stops when a pass adds no new key, when `scrollTop` does
  not change, or when `timeout_ms` elapses. It does not call `wait_for_timeout`.

  `PublicInquiriesPage._read_grid` deletes its private `_SCROLL_JS` and calls this function.
  The page still maps Hebrew headers. Its `row_id` reads `inquiry_id` when that field is in
  the header map, otherwise `request_id`. `VisualTable._collect_rows` calls the same
  function. Its `row_id` is the full cell tuple joined as text, which preserves today's
  "one stored row per distinct cell tuple" behavior. `rows_to_label_values` is unchanged.

  `VisualTable.read_rows` waits, immediately after Show as a table is clicked and the
  visible grid or table is found, until a data cell is visible: a `td`, `[role="gridcell"]`,
  or `[role="cell"]` inside a `tr` or `[role="row"]`. The wait is `expect(...).to_be_visible`
  bounded by `timeout_ms`. Collection starts only after that.
- **Rationale**: Power BI recycles row nodes that are outside the viewport. The page scroller
  only walks ancestors and steps by `clientHeight - 24`, so the inner scrollport never
  moves and golden ids below the fold are missing (`ui=[]` or a missing id). Show as a
  table returns `ui=[]` for a different reason: `_visible_table` returns on the first
  visible grid, and `_collect_rows` reads before any `tr` has cells.
  Constitution I keeps grid reading out of `ReportShell`. Constitution II keeps
  `request_id` and `inquiry_id` off `core/`. Constitution VII allows the collector because
  two readers already share the behavior and the page copy is the one that drops rows.
  Constitution III requires fleet smoke after the `VisualTable` edit. The public
  `read_rows` signature in the 048 contract stays the same.
- **Alternatives considered**: Leaving the loop on `PublicInquiriesPage` only. Rejected —
  chart tables hit the same virtualizer, and the user asked for a core reader.
  Putting the loop on `ReportShell`. Rejected — Layer 0 is portal chrome, not grids.
  Hard-coding `request_id` inside `core/components/`. Rejected — AC-005. Scrolling with a
  fixed `wait_for_timeout` after each step. Rejected — FR-009; the stop condition is "no
  new id" after a scroll that moved. Keeping the 24px overlap. Rejected for this revision —
  the step is the container height, and duplicate rows across overlapping viewports are
  already collapsed by the id dict. If a live run misses a golden id that is present in
  the grid, shrink the step by one row height without changing the stop condition.

## R13 — Screen 4 rendered locator

- **Decision**: `grid_is_rendered("screen_4")` and `_wait_until_ready("screen_4")` succeed
  when a feedback-grid column header named `הערות` or `הערה` is visible. Implementation
  confirms that node on the live screen 4 DOM before editing the locator. If the header
  text is not an accessible name, the locator is the visible text `הערות` inside the grid.
  The full title `ניתוח פניות הסברה - ניתוח משובי שביעות רצון (תחקור משובים)` is not the
  rendered gate. Screen 2 stays on its current grid-or-row check. The YAML title assertion
  in the screen 4 test stays a phrase check and is separate from the skip.
- **Rationale**: The skip in `test_hasbara_screen4_feedback_rows_match_golden` is
  `grid_is_rendered("screen_4")`. That method returns false when
  `phrase_is_visible` of the full parenthetical title fails, even if the feedback grid is
  on screen. `_wait_until_ready` for screen 4 currently shares the generic
  `role=grid` locator with screen 2, which is not specific to the feedback table.
  `הערות` is the comments header on this page's feedback map and is not an investigation
  column. The catalog-open ready locator stays `ניתוח פניות הסברה` (R10).
- **Alternatives considered**: Treating any visible `role=grid` as screen 4. Rejected —
  that is the check that already fails to identify this screen. Using the screen 4 slicer
  `info_desc` as the ready signal. Rejected unless the live DOM has no comments header;
  the grid under test is the thing that must be visible before `read_feedback_rows`.

## R14 — Screen 1 duration widgets are separate visuals

- **Decision**: `read_kpi_metrics` keeps the four inquiries counts on their measure images
  (`CountConversationsID`, `CountTotalTickets`, `CountOpen`, `CountTickets`). It then
  locates two more visual containers and does not stop after the inquiries widget
  ("פניות"). `request_closing_times` is the container titled `זמני סגירת פנייה` (also
  `זמני סגירת פניה`). `response_wait_times` is the container titled `זמני המתנה למענה`.
  Inside each container, the `DD:HH:MM:SS` after `ממוצע` is `average` and the
  `DD:HH:MM:SS` after `מקסימלי` is `maximum`. The page reuses `_visual_container` and
  the existing `_DURATION` pattern. Before the read, the title is expected visible within
  `self.timeout`. The returned dict contains `inquiries_summary`, `request_closing_times`,
  and `response_wait_times`. A missing caption is omitted. The sanity test and the YAML
  stay unchanged. Current closing-times strings in the file are `00:04:35:46` and
  `16:14:33:22`. Current wait-times strings are `00:01:36:13` and `00:08:11:12`.
- **Rationale**: The live metric bar shows all three widgets. `_read_kpi_value` looks for
  `img[aria-label*='AvgTimeToResolve']` (and the three sibling measure ids). Those images
  are not the duration widgets. The fallback calls `KPI.read_text` on one shared title,
  and `extract_kpi_value_text` keeps the longest digit run, which splits a colon-separated
  duration. Both captions share that title, so the second value is never stored. A `None`
  value is skipped, and `setdefault` never creates `request_closing_times`. FR-004 requires
  both pairs. FR-013 keeps durations as display strings. Constitution II keeps `ממוצע`,
  `מקסימלי`, and the widget titles off `core/`. Constitution VII does not promote this
  parser: only this report has the pair.
- **Alternatives considered**: Teaching Layer 2 `KPI.read_text` to return every duration in
  a card. Rejected — that puts Hasbara captions into `core/` and changes the single-value
  contract used by fleet and credit. Treating average and maximum as two `KPI` cards that
  share one title. Rejected — `KPI.card` returns the first button or group, so both leaves
  read the same node. Hardcoding the current YAML durations in the page. Rejected — the
  test already compares the reader to the file. Editing `data/hasbara/db_sanity.yaml` to
  drop `request_closing_times`. Rejected — the widgets are on screen and FR-004 includes
  them.

## R15 — Inquiries counts come from the visible widget after it settles

- **Decision**: After the date filter is applied, screen 1 waits for the inquiries
  widget, then `read_kpi_metrics` reads `inquiries_summary` from the visible text
  inside that widget. The container is the smallest visual host that contains both
  `סה"כ פניות` and `פניות פתוחות`. A heading named `פניות` is that host only when
  both card titles sit inside it. The wait hides a visible spinner or
  `[aria-busy='true']` inside the container, then requires the visible
  `CountTotalTickets` and `CountOpen` texts to be unchanged on two successive
  reads, bounded by `self.timeout`. The same wait runs from screen 1 settle and
  from the start of `read_kpi_metrics`. Each of the four count cards prefers a
  visible `svg text` (or other visible text node) in that container. A visible
  `img[aria-label*='{measure_id}']` inside the same container is the fallback.
  Hidden, `aria-hidden`, zero-size, and iframe-wide `.first` images are ignored.
  When visible text and an image label disagree, the visible text is the value.
  Display strings stay display strings, so `1,324` still matches integer `1324`.
  `total_requests` and `open_requests` stay in the golden tree. The test file and
  the YAML stay unchanged. Duration widgets stay on the R14 path. The waiter does
  not search for `1324`, `1,324`, or `49`.
- **Rationale**: The live widget shows `1,324` and `49`, which are the golden
  integers `1324` and `49`. The reader returned `1,321` and `48` because
  `_read_kpi_value` uses `frame.locator("img[aria-label*='…']").first` with no
  visibility filter and no container. Power BI can leave a previous SVG image in
  the iframe whose `aria-label` still ends in the old count, and `.first` follows
  DOM order. `_any_kpi_visible` treats any `CountTotalTickets` image as ready, so
  settle can succeed while that stale image is the one the reader will take, or
  while the October query is still painting. FR-004 requires the four counts.
  FR-009 forbids a fixed sleep. FR-012 requires the mismatch to name the YAML
  path, the UI value, and the golden value, which a wait that demands `1324`
  would replace with a timeout. Constitution II keeps `פניות` and the card titles
  on the page. Constitution VII leaves Layer 2 `KPI` a single-value reader.
- **Alternatives considered**: Waiting until the text `1,324` or `1324` appears.
  Rejected — those literals are the current golden display. Requiring them makes
  a wrong UI time out instead of failing `_assert_tree` with `ui=` and `golden=`.
  Removing `total_requests` or `open_requests` from the comparison, or popping
  them in the test. Rejected — the user required the golden asserts to stay
  strict, and FR-004 already includes both leaves. Editing
  `data/hasbara/db_sanity.yaml` to `1321` and `48`. Rejected — the visible widget
  matches the current file. Teaching `core/components/kpi.py` to skip hidden
  images. Rejected for this revision — the defect is the page's iframe-wide
  `.first`, and a Layer 2 change would put the Hasbara container rule in `core/`
  and reopen the fleet gate. A page-wide locator for the substring `פניות`.
  Rejected — chart titles contain the same word, so the host must contain both
  count-card titles.

## R16 — Inquiry scripts run on the iframe body; KPI and survey nodes must be visible

Supersedes the *mechanism* in R15 that would call `evaluate` or `wait_for_function` on
the object returned by `content_frame`. The visible-text decision in R15 still holds.
R14 duration pairing still holds.

- **Decision**: `_expect_inquiry_counts_settled` uses the report `FrameLocator` from
  `_report_frame()`. Playwright Python's `Locator.content_frame` is that
  `FrameLocator`. It has no `evaluate` and no `wait_for_function`. The token reset is
  `frame.locator("body").evaluate("() => { window.__vcInquiryToken = ''; }")`. The
  settle poll is `expect.poll(lambda: body.evaluate(_INQUIRY_SETTLED_JS), timeout=self.timeout).to_be(True)`.
  The script keeps using `document` and `window` inside the iframe, because
  `locator.evaluate` runs in the element's frame. A timeout still raises
  `AssertionError("Inquiries widget counts did not settle")`.

  Every inquiries, duration, and survey candidate is `.filter(visible=True)` before
  `.first` or before its text is accepted. The list is `_wait_for_inquiries_widget`,
  `_inquiries_container`, `_visible_svg_runs`, `_visible_measure_text`,
  `_read_duration_widget`, `_any_kpi_visible`, the screen 1 ready title, survey
  section titles, and `_metric_under_box`. Nodes inside `[role='tooltip']`, nodes
  with `aria-hidden='true'`, and nodes with an empty box are dropped. The settle
  script applies the same exclusions so a tooltip or a stale hidden SVG cannot
  build the stability token. `_any_kpi_visible` no longer treats a hidden
  `CountTotalTickets` image as the widget being present.

  Screen 3 settle, from `_wait_until_ready("screen_3")` and from the start of
  `read_satisfaction`, waits until `מוקד טלפוני`, `מענה כתוב`, and `בקרת איכות`
  are visible, any visible spinner in those cards is hidden, and a visible
  metric-shaped string under each card (a number, `לא ידוע`, or `אין מידע`) is
  unchanged on two reads. The bound is `self.timeout`. The waiter does not search
  for `1,062`, `129`, `39`, `1324`, `1,324`, or `49`.

  `tests/sanity/public_inquiries_dashboard/test_data_validation.py` and
  `data/hasbara/db_sanity.yaml` stay unchanged. `_assert_tree` still compares
  `kpi_metrics`, `surveys_summary`, and the other screen blocks. No key is
  removed. Edit `pages/public_inquiries/page.py` only. New locators, waits,
  comments, and docstrings are English. `ReportShell._report_frame` stays a
  `FrameLocator`.
- **Rationale**: The live failure is `AttributeError: 'FrameLocator' object has no attribute 'evaluate'`
  on the token reset. `wait_for_function` is a `Frame` and `Page` method, so leaving
  it on the `FrameLocator` only moves the crash one line down. Evaluating on `body`
  is the call the iframe document actually accepts. Hidden Power BI tooltips and
  leftover SVGs share the Hebrew titles and the measure `aria-label`s. Playwright's
  `.first` without `.filter(visible=True)` binds the wait or the value to that
  hidden node, which times out or returns the previous count. A survey geometry
  scan that ignores visibility can return a tooltip number and fail
  `surveys_summary` even when the painted card is correct. FR-004 and FR-007 still
  require the golden trees. FR-009 forbids a fixed sleep. FR-011 and FR-012 require
  a mismatch to stay an assertion with the YAML path, the UI value, and the golden
  value, which a waiter that demands `1,062` or `1324` would replace with a timeout.
  Constitution I leaves `content_frame` as a `FrameLocator` in Layer 0. Constitution
  II keeps the Hebrew titles on the page.
- **Alternatives considered**: Resolving a Playwright `Frame` via `page.frames` and
  calling `Frame.evaluate` / `Frame.wait_for_function`. Rejected — the user named
  `iframe.locator("body").evaluate`, and the existing `FrameLocator` already
  exposes `locator("body")` without a second iframe lookup. Changing
  `ReportShell._report_frame` to return a `Frame`. Rejected — every report page
  calls that method as a `FrameLocator`, and this defect is the one Hasbara settle
  that treated it as a `Frame`. Dropping the two-read settle and reading the first
  visible text. Rejected — R15 exists because a single read can land mid-paint.
  Filtering only in the Python locators and leaving the settle script on every
  `svg text`. Rejected — the token would still stabilize on a tooltip. Loosening
  `_assert_tree`, skipping `surveys_summary`, or editing the golden YAML to the
  stale numbers. Rejected — the golden file stays the source of truth.

## R17 — Detail grids open Show as a table

Supersedes the part of R12 that reads screen 2 and screen 4 by scrolling the
on-canvas grid. The collector, the data-cell wait, and chart reads stay.

- **Decision**: `read_investigation_rows` and `read_feedback_rows` call
  `VisualTable.read_rows` on the visual host of the visible grid. The host is the
  smallest `visualContainer` or `visualContainerHost` ancestor of that grid.
  `read_rows` right-clicks with `button="right"`, clicks `הצג כטבלה` or
  `Show as a table`, waits for a visible data cell, and returns header → cell
  rows from the expanded grid. The page maps those headers with the existing
  alias maps. A `\x00` suffix on a repeated header is removed before the lookup.
  Blank cells stay `""`. A total row (`סה"כ` or `סה״כ`) is dropped on the page.
  The page dedupes on `request_id` or `inquiry_id`.

  When more than one visible grid has a data cell, `VisualTable._visible_table`
  chooses the grid that shares an ancestor with the visible Back to report
  button, then the candidate with the most column headers. One visible grid
  keeps the current chart behavior. `collect_virtualized_rows` still scrolls the
  chosen grid vertically. `read_rows` clicks `חזרה לדוח` or `Back to report` in
  `finally` and waits until that button is hidden. Escape dismisses a menu that
  never offered the item. After `read_rows` returns, the page expects the
  screen's existing ready locator to be visible. A rendered grid that fails to
  open the table raises. A rendered grid whose expanded table has no data rows
  returns `[]`, and the test fails with `ui=[]`. The canvas grid is not a
  fallback. The public `read_rows` signature and `rows_to_label_values` stay as
  in the 048 contract. New locators, waits, method names, and comments are
  English. `request_id`, `inquiry_id`, and `handling_time` stay off `core/`.
- **Rationale**: The canvas table virtualizes columns. `handling_time` is clipped
  or missing from the DOM, and moving `scrollLeft` does not bring that cell
  back, so the compare sees a blank field or `ui=[]`. Show as a table is the
  structured grid that contains every column. It already exists for charts in
  Layer 2. Copying the right-click onto the page would duplicate that chrome and
  violate Constitution VII. A table visual can leave the clipped canvas grid in
  the DOM next to the data view, so the first visible grid is the wrong one.
  Tying the choice to the Back button, then to the header count, stays
  report-agnostic and leaves a chart that opens one grid on the current path.
  Constitution III requires fleet smoke because `visual_table.py` changes.
  FR-006 and FR-008 require the golden cells, including handling time and
  comments. FR-009 forbids a fixed sleep. FR-010 requires English names.
  FR-011 still fails an empty read when the golden block has rows.
- **Alternatives considered**: More horizontal steps on the canvas grid.
  Rejected — the missing column is not in the DOM, which is why the current
  sweep already fails. Right-clicking a cell inside `_read_grid` and clicking
  the menu there. Rejected — `VisualTable.read_rows` already performs that
  sequence, and a second copy would drift. Catching a missing menu and falling
  back to the canvas grid. Rejected — that fallback is the defect, and it
  reports `ui=[]` for a menu miss. Dropping total rows inside `read_rows`.
  Rejected — the 048 contract keeps that filter on the caller. Teaching
  `virtual_grid.py` the Hebrew header `זמן טיפול`. Rejected — Constitution II.

## R18 — Satisfaction sub-tab is not a page-rail link

Supersedes the part of R7 that treats `select_satisfaction_tab` as the same
click as a report page. The golden compare, the loaded `active_tab` string,
and the four-screen rail stay.

- **Decision**: `select_satisfaction_tab` stops calling `_click_tab`. It
  searches the report `FrameLocator` for the exact label the test passes.
  Role order is `tab`, then `button`, then `link`, each with `exact=True`.
  When none of those is visible, it uses `get_by_text(label, exact=True)`.
  Every branch applies `.filter(visible=True)`, then `_first_outside_tooltip`,
  so a tooltip, an `aria-hidden` node, and an empty box are skipped. When a
  visible visual host contains `התקבלות השירות`, a match inside that host is
  the click target, because those sub-tabs sit above that chart. If the host
  has no visible match, the same exact locator runs on the frame. Expect the
  chosen node visible, click it, hide a visible spinner in the section, and
  keep the existing expect that the label phrase is visible. No
  `wait_for_timeout` and no `networkidle`. `_tab_locator` still matches
  `ניווט בין עמודים . {label}` for screens 1–4. The test, the YAML, and
  `core/` are not edited. New locators, waits, method names, and comments are
  English. Hebrew stays in the section-title constant and in the label
  argument.
- **Rationale**: A load of `data/hasbara/db_sanity.yaml` keeps the last
  duplicate `service_reception.active_tab`, which is `אופן מקצועי`. The
  distributions test passes that string to `select_satisfaction_tab`.
  `_tab_locator` only finds the page rail, and this label is not a page, so
  Playwright times out before `service_reception.responses` is compared.
  `.filter(visible=True)` is what drops a hidden or stale copy of the same
  Hebrew. Scoping to the section host avoids a same-text node elsewhere on
  screen 3. Exact match keeps `אופן מקצועי` distinct from `מקצועיות`. Leaving
  `_click_tab` unchanged protects the rail anchor that stops `משובים` from
  selecting `תחקור משובים`. Constitution II keeps both Hebrew strings on the
  page. FR-007 still requires the courtesy bars after the tab select. FR-009
  forbids a fixed sleep. FR-010 requires English names. A wrong chart after a
  successful click still fails with `ui=` and `golden=`.
- **Alternatives considered**: Replacing `_tab_locator` with
  `get_by_text(label, exact=True)` for every tab. Rejected — the four report
  pages rely on the rail pattern, and a bare text match would also hit titles.
  Clicking with `force=True` on the current rail locator. Rejected — the rail
  locator does not contain this sub-tab, so force cannot make it appear.
  Editing the YAML to delete the first `active_tab` or to keep `אופן אדיב`.
  Rejected — the file is the baseline, and the test already receives
  `אופן מקצועי` from PyYAML's last-key rule. Looping both courtesy blocks in
  the test. Rejected — the loader exposes one map, and this defect is the
  click, not the compare. Putting `התקבלות השירות` in `core/components/`.
  Rejected — Constitution II.
