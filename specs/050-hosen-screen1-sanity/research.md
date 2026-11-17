# Phase 0 Research: Hosen Status Screen 1 YAML Sanity

**Feature**: `050-hosen-screen1-sanity` | **Date**: 2026-11-16

All technical-context unknowns are resolved below. Nothing remains NEEDS CLARIFICATION.

The 2026-11-15 amendment supersedes the "do not click the slicer" line in section 3 and the
"no settle after a filter change" reading of section 10. Sections 11–13 are the current
filter-apply decisions. Section 14 is the 2026-11-16 search-click decision. Section 15 is the
2026-11-16 date-combobox decision. Section 16 is the category SVG `tspan` decision.
Section 17 is the resilience authority first-line decision.
`Slicer` and `KPI` are still not extended. `networkidle` is still rejected.

## 1. Feature directory

- **Decision**: Plan this slice in `specs/050-hosen-screen1-sanity`. Repoint
  `.specify/feature.json` here. Stay on git branch `feature/reportportal-integration`.
- **Rationale**: Setup initially resolved the pinned directory `specs/049-hasbara-ui-validation`,
  which already has a finished Hasbara plan. The user task is the Hosen landing screen. Writing
  into `049` would replace that plan. This repository already plans a new spec directory without
  switching the long-lived checkout (see `049` and `044`).
- **Alternatives considered**: Overwrite `049` (rejects the current Hasbara plan). Create a new
  git branch (the established checkout for these slices is `feature/reportportal-integration`).

## 2. Where Screen 1 is read

- **Decision**: Add `read_screen_1_metrics()` to the existing `HosenStatusPage` in
  `pages/hosen_status/page.py`. Leave `tests/ui/hosen_status_dashboard/page.py` absent. The UI
  package only has the smoke test, its conftest, and `__init__.py`. The conftest already imports
  `pages.hosen_status.page.HosenStatusPage`.
- **Rationale**: The page object is already the Layer 0 binding: search `תמ"צ חוסן`, ready text
  `תמ"צ ארצי - דיווחי קה"א יקל"ר`, freshness phrase `מועד רענון`. Constitution IV puts new
  locators on that page.
- **Alternatives considered**: A new page class under `tests/` (forbidden by the constitution).
  A second page module beside `page.py` (the class is small enough to extend in place).

## 3. Selected filter text

- **Decision**: Compose `Slicer` on the page. After the golden map has been applied, read the
  selection with the public `Slicer.control(slicer_id)` locator and `inner_text()`. Strip the
  Hebrew role name and bidi marks on the page so the returned string is the selected label.
  Do not add `Slicer.selected()`. Selection itself is `Slicer.select` (section 11), not a new
  Layer 2 method.
- **Rationale**: `Slicer` already exposes `control()` for dropdowns (`get_by_role("combobox")`)
  and `select()` for choosing an option. `_dropdown_shows_selection` is private and only answers
  a boolean during `select()`. A `selected()` helper would be a convenience used by one call
  site. Constitution VII says not to add generic APIs that have not earned a second report.
- **Alternatives considered**: Edit `slicer.py` to return selected text (stops the "do not touch
  core" rule for a wrapper around `inner_text`). Copy a Hasbara slicer reader (the original task
  forbade copying those scrapers). Leave the slicer unclicked (the 2026-11-12 rule). Rejected
  by the 2026-11-15 input: the golden file is a filtered slice, and an unfiltered read cannot
  match it.

## 4. KPI percentage and trend

- **Decision**: Locate each card with `KPI.card(title)` (and `KPI.read_text` for the value).
  Keep the percent sign in the string the test compares. Classify `trend` on the page from a
  non-canvas arrow inside that card: direction first (`up` / `down` / `flat`), then computed
  color (green → `up`, red → `down`, yellow → `flat`). Do not change `extract_kpi_value_text`.
- **Rationale**: `KPI.read_text` on a button returns the last paragraph, which can still contain
  `%`. On a group visual, `read_text` calls `extract_kpi_value_text`, which returns the longest
  numeric token and drops `%`. The page can recover `%` from the same card locator. `KPI` has
  no trend API. Arrow color is a Hosen display rule (`up` / `down` / `flat`), so it stays next
  to the Hebrew titles. Sampling a canvas would violate the task.
- **Alternatives considered**: `KPI.number`, which parses `55%` toward `55` and breaks exact
  string match. A new `KPI.trend()` in `core/` (not universal until a second report needs the
  same three-way map; this slice does not add it). Copying a Hasbara chart reader (those readers
  target different visuals).

## 5. Resilience rows and color

- **Decision**: Pass the `ציון חוסן` grid to `collect_virtualized_rows`. The page callback
  returns `authority`, score text, and `status`. Status comes from `getComputedStyle`
  background of the row or the score cell: green-dominant → `green`, yellow (high red and green,
  low blue) → `yellow`, otherwise the raw `rgb(...)` string. `row_id` is the authority name.
- **Rationale**: `collect_virtualized_rows` already scrolls a caller-supplied grid, dedupes by a
  caller-supplied id, and stores whatever fields the callback returns. It has no Hosen field
  names. Color vocabulary `green` / `yellow` is specified by this feature and belongs on the page.
  An unknown color must not be coerced, or a wrong paint would pass.
- **Alternatives considered**: A new color parameter on `virtual_grid.py` (domain status words
  would leak into Layer 2). Scraping the canvas bitmap (forbidden). Reading only the viewport
  without the collector (misses virtualized authorities).

## 6. Survey status

- **Decision**: Read the top-left submitted count, total count, and missing-authority list with
  Playwright locators on `HosenStatusPage`. Return counts as digit strings. No Layer 2 type is
  involved.
- **Rationale**: The block is report text, not a KPI card, slicer, or virtualized grid. The task
  assigns it to standard locators and forbids putting those Hebrew phrases in `core/`.
- **Alternatives considered**: Forcing the block through `KPI` (the two counts plus a name list
  are not one KPI value). A new generic "callout" reader (one report, so it has not earned a
  Layer 2 module).

## 7. Comparison

- **Decision**: Private helpers in `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
  implement subset match, integer coercion, and exact strings. They are not imported from
  Hasbara or Credit, and they are not placed in `tests/helpers/`.
- **Rationale**: The task says not to build a new comparison engine. Hasbara's `_assert_tree` /
  `assert_value` / `assert_rows` are the behavioral model (every golden key, ignore extra UI,
  `1324` matches `1,324`). Importing that module would couple the suites. A shared engine would
  be the new component the task rejects.
- **Alternatives considered**: `validate_dashboard_generic` (warehouse parity, no Hosen SQL).
  Importing the Hasbara helpers (edits the dependency boundary the task drew).

## 8. Golden literals

- **Decision**: The schema is fixed in data-model.md. During implementation, one live read of the
  open landing screen is written into `data/hosen/db_sanity.yaml`. The page and the test do not
  contain those numbers. Examples in the task (`7`, `12`, `55%`, `מחוז דרום`, `נפת לכיש`) document
  shape and the kind of label a slicer returns.
- **Rationale**: No checked-in Hosen golden file and no prior message in this workspace contain a
  verified full snapshot. Inventing `55%` would make the first run fail or, worse, hide a real
  value. Freezing the live screen is how the other YAML sanity files became the source of truth.
- **Alternatives considered**: Hardcode the examples as the golden file (treats illustrations as
  measurements). Leave the YAML empty and skip (the task requires a failing test when the golden
  block expects data and the reader is empty).

## 9. Empty visual versus skip

- **Decision**: If the section anchor is visible and the golden block has data, an empty reader
  fails. If that anchor is not rendered, skip that block and still assert the blocks that are
  present.
- **Rationale**: The task requires a failure when the generic component returns empty data for a
  visual that is on screen. Skipping the whole test when one corner is missing would hide the
  other three blocks. Hasbara uses the same present-versus-absent split.
- **Alternatives considered**: Always fail when an anchor is missing (breaks a report that has
  not finished publishing one visual). Always skip on empty (hides a broken reader).

## 10. Waits and canvas

- **Decision**: Visibility waits use Playwright `expect` with `self.timeout` (the `ReportShell`
  timeout). No `time.sleep`, no `wait_for_timeout`, no `networkidle`. No canvas pixel read.
  The post-filter idle wait is section 12, which uses the same `expect` budget.
- **Rationale**: `HosenStatusPage` already waits on a text locator inside the report iframe.
  `collect_virtualized_rows` already waits on animation frames inside its own loop. Adding a
  sleep or a network-idle wait would violate the page-object wait policy.
- **Alternatives considered**: `page.wait_for_load_state("networkidle")` (Power BI keeps sockets
  open; the wait does not arrive when the visuals are ready). Screenshot diff of the canvas
  (not a structured read, and canvas scraping stays forbidden).

## 11. Apply golden filters before the metric read

- **Decision**: `test_hosen_screen1_matches_golden` loads `screen_1_landing` first. It sets
  `filters = expected.get("filters", {})` and, for each pair in that map, calls
  `page.select_screen_1_filter(slicer_id, value)`. It then calls `page.wait_for_screen_1_idle()`
  and only then `page.read_screen_1_metrics()` and `_assert_tree`. The test function does not
  name `district` or `subdistrict` and does not construct a locator. An empty or missing map
  applies nothing and still waits once so the read is not racing the first paint.
- **Rationale**: `data/hosen/db_sanity.yaml` stores the slice for `מחוז דרום` / `נפת לכיש` under
  `filters`. The current test calls `read_screen_1_metrics()` before that map is loaded, so the
  UI numbers are the unfiltered landing screen and `_assert_tree` fails against the filtered
  golden block. Driving the loop from the YAML keeps a new filter id out of the test. Constitution
  IV puts the combobox locator on `HosenStatusPage`. Constitution I says the page composes
  `Slicer` and does not copy click-and-retry into the test.
- **Alternatives considered**: Locating the dropdown inside the test (the request's "locate the
  dropdown" step, rejected because it puts a report locator in the test body). Calling
  `Slicer.apply`, which reorders by `cascade_rank` and would hide a YAML file that listed the
  child before the parent. Hard-coding the two Hosen ids in the test (stops the loop from
  covering the next key added to the YAML).

## 12. Idle after each selection

- **Decision**: `select_screen_1_filter` passes a page settle hook into `Slicer`. On
  `after_select`, and again in `wait_for_screen_1_idle`, the page looks in the report iframe
  for a visible node whose class contains `spinner` or whose `aria-busy` is true. When that
  node is present it is expected hidden within `self.timeout`. The Screen 1 ready locator is
  then expected visible within `self.timeout`. A spinner that is not showing is not a failure.
  The hook returns false so `Slicer.select` still checks that the combobox text contains the
  chosen label and retries that click once.
- **Rationale**: Power BI repaints the KPI cards and the resilience grid after a slicer change.
  Reading on the next line races that paint. The same spinner-then-ready sequence is already
  the settle used by the public-inquiries page, and it stays on the domain page rather than in
  `core/`. `Slicer.select` already calls the hook, so each dropdown gets a settle, and the
  extra call after the loop covers the last paint before `_assert_tree`.
- **Alternatives considered**: `page.wait_for_load_state("networkidle")` or waiting on a
  Power BI query response. Rejected — the portal socket stays open, and the query URL is not
  a stable contract. `page.wait_for_timeout` for a fixed gap. Rejected — a sleep both flakes
  and hides a dropdown click that never changed the visual. Treating any missing spinner as a
  failure. Rejected — a fast repaint can finish before the check runs.

## 13. Filter ids match the YAML keys

- **Decision**: The page filter-role id for the sub-district slicer is `subdistrict`, matching
  `data/hosen/db_sanity.yaml`. `district` already matches. The reader returns that map under
  `filters`, which is the key `_assert_tree` walks. `section_anchor_visible("filters")` is true
  when the report iframe has a combobox, so the block is asserted rather than skipped. An id
  that is not in the page role table raises `KeyError` from `select_screen_1_filter`.
- **Rationale**: The live golden key is `filters`, with `subdistrict` rather than the earlier
  plan's `active_filters` / `sub_district`. A translation table inside the test would put Hosen
  ids back into the test. Failing an unknown id prevents a golden label from being silently
  skipped while the other blocks are compared against the wrong slice.
- **Alternatives considered**: Keep `active_filters` and `sub_district` and alias them in the
  test (two names for one slicer). Skip unknown YAML keys (hides a typo). Assert `filters` only
  as an input and not in `_assert_tree` (would not catch a dropdown that closed on the wrong
  label).

## 14. Force the `בחירת נפה` search click

- **Decision**: In the custom-card override that `select_screen_1_filter` uses for
  `בחירת נפה`, the search-input click is `search_input.click(force=True)`. That block is
  `_select_smart_filter`, which the page calls for `subdistrict` (role hints include
  `בחירת נפה`). The visible `li` option click stays `choice.first.click(force=True)`.
  Comments inside the function stay English. The test does not locate the input. `Slicer`
  is not edited.
- **Rationale**: The sanity run fails with `TimeoutError` on the search `<input>` click.
  Playwright's actionability check reports that `<ul class="TokensContainer">` intercepts
  pointer events, so an ordinary `click()` never lands. `force=True` dispatches the click
  through that overlay. The same flag is already how this block clicks the `li` option.
  The current helper names the input `field` and clicks the `TokensContainer` shell instead
  of the input; the implementation makes the input click the forced call above.
- **Alternatives considered**: Click the `TokensContainer` in place of the input (the current
  shell click; the failure is still the input click being intercepted). Raise the timeout
  (the overlay still wins hit-testing). Add `force=True` to `Slicer.select` (one report's
  custom card, and constitution VII keeps that flag off Layer 2). Put the locator in the
  test (constitution IV).

## 15. Screen 1 date combobox

- **Decision**: Leave `district` and `subdistrict` on `_select_smart_filter`. For `date`, keep
  the combobox `_filter_control` already returned and click it once. Choose the passed value
  in that control's owner frame and in iframes nested under that frame. Call `Slicer.select`
  only when the open listbox accessible name is `SlicerDate` and that same frame contains the
  combobox `Slicer.select` clicks. Pass that frame, which may be a nested iframe,
  `role_name="SlicerDate"`, `kind="dropdown"`, and `_screen_1_settle`. Do not edit `core/`.
  Otherwise click the open option and do not click the combobox again. Do not call
  `_choose_dropdown_option`. Remove `page.wait_for_timeout` from `select_screen_1_filter`.
  After `_screen_1_settle`, if the plain combobox text does not contain `value`, raise
  `AssertionError` and do not catch it. `section_anchor_visible("date")` is true when that
  combobox is visible. `read_screen_1_metrics()["date"]` is `_selected_label` on the same
  control. Do not embed the golden date. Do not edit `data/hosen/db_sanity.yaml`.
- **Rationale**: The current date branch clicks the `SlicerDate` combobox, then
  `_choose_dropdown_option` clicks it again and closes the list. The `except Exception`
  treats the miss as success, and `wait_for_timeout` fills the gap.
  `section_anchor_visible` has no `date` branch, so the test skips the golden date. Survey
  counts stay on the wrong day and `survey_status.submitted` comes back `0` against golden
  `7`. `Slicer.select` looks up the listbox by name in one frame. Pointing that frame at the
  open listbox covers a nested iframe without changing Layer 2. A listbox that is not named
  `SlicerDate` is not a target `Slicer.select` can address, so the page clicks the option
  that is already open. The text check after settle stops a silent return.
- **Alternatives considered**: Always call `Slicer.select` on `_report_frame()` (the option
  lookup misses a nested iframe, and the method clicks the combobox again). Keep the
  `except` and return after settle (the test skips `date` and fails later on
  `survey_status.submitted`). Hardcode the golden date on the page or in the test (the YAML
  value is already passed in). Edit `Slicer` to walk child iframes (constitution II and VII;
  this amendment forbids a `core/` edit). Change the YAML date (forbidden by this amendment).
  Leave `section_anchor_visible("date")` false (that skip is the defect).

## 16. Category grade inside SVG `tspan`

- **Decision**: On `HosenStatusPage`, read the category grade from the card-scoped locator
  `.value tspan` with Playwright `text_content()`. When that CSS misses, use
  `.//*[local-name()='text' and contains(concat(' ', normalize-space(@class), ' '), ' value ')]/*[local-name()='tspan']`
  and the same `text_content()` call. Do not call `inner_text()` for this node. Do not edit
  `core/components/kpi.py`. Publish each `kpis.categories` item as `title`, `score`, and
  `trend_direction`. Leave `kpis.national_average` as `title`, `percentage`, and `trend`.
  The grade string for both shapes is the SVG text (`88%` stays `88%`). Do not edit
  `data/hosen/db_sanity.yaml` or `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`.
- **Rationale**: The inspected node is `<g><text class="value"><tspan>83%</tspan></text></g>`.
  SVG text has no `innerText`, so `card.inner_text()` and a `<p>` read return `''`.
  `textContent` returns `83%` or `88%`. `_assert_rows` compares golden fields with
  `actual.get(field, "")`. The live category rows are keyed `score` and `trend_direction`.
  `_read_card` stores `percentage` and `trend`, so the assertion reports `ui='' golden='88%'`
  even when a percent was read under the other name. `KPI.read_text` on a group runs
  `extract_kpi_value_text`, which drops the percent sign, and on a button it reads the last
  `<p>`, which this visual does not use. Putting `.value tspan` into Layer 2 would change
  every report's KPI read. The selector stays on the Hosen page, scoped to `KPI.card(title)`.
- **Alternatives considered**: Change the YAML categories back to `percentage` and `trend`
  (this amendment does not edit the golden file). Teach `_assert_rows` to alias `score` to
  `percentage` (a locator would land in the test, and the helper would grow a Hosen field
  map). Extend `KPI.read_text` to query `.value tspan` (constitution VII and FR-010; group
  reads would still pass through `extract_kpi_value_text` and lose `%`). Keep `inner_text()`
  and only rename the keys (the SVG string would still be empty).

## 17. Resilience authority is the first line of the cell

- **Decision**: In `HosenStatusPage._visible_resilience_rows`, set `authority` from the first
  line of that cell only:

  ```python
  extracted_text = cells.nth(authority_index).inner_text(timeout=500) or ""
  authority = _plain(extracted_text.split("\n")[0])
  ```

  Leave the score assignment on `_plain` of the full cell. Do not change module-level
  `_plain`. Do not edit `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`,
  `data/hosen/db_sanity.yaml`, or `core/components/virtual_grid.py`.
- **Rationale**: `_assert_rows` indexes `resilience_scores` with
  `_plain(row.get("authority", ""))`. It does not read the table. The page stores the cell
  from `inner_text()`, and `_plain` only removes bidi marks and outer whitespace. The live
  cell is `קרית מלאכי\nעיצוב מותנה נוסף` (the second line is Power BI's hidden conditional
  formatting text). The golden file has `קרית מלאכי`, so the key lookup raises
  `AssertionError`. `collect_virtualized_rows` dedupes on that same `authority` string, so
  the published row and the scroll identity both need the visible name. Taking the first
  line does not hardcode the Hebrew accessibility phrase. `_plain` on that line still drops
  bidi marks, and `str.strip` inside `_plain` drops a `\r` left by `\r\n`.
- **Alternatives considered**: Strip the newline inside the test's `_plain` or `_assert_rows`
  (the page would still publish the dirty key, and every other string comparison would lose
  lines it did not ask to lose). Change module-level `_plain` (filter labels, the date, and
  grades share it). Put the split in `collect_virtualized_rows` (constitution VII; other
  reports did not ask for it). Rewrite the golden authority to include `עיצוב מותנה נוסף`
  (the YAML is the visible name, and this amendment does not edit it). Drop any line that
  equals that Hebrew phrase (brittle, and it encodes one accessibility string instead of the
  first-line rule). Apply the same split to the score cell (the reported mismatch is the
  authority key).
