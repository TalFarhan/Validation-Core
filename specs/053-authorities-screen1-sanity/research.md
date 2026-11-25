# Phase 0 Research: Authorities Status Screen 1 YAML Sanity

**Feature**: `053-authorities-screen1-sanity` | **Date**: 2026-11-18, section 14 added 2026-11-19

All technical-context unknowns are resolved below. Nothing remains NEEDS CLARIFICATION.

## 1. Feature directory

- **Decision**: Plan this slice in `specs/053-authorities-screen1-sanity`. Repoint `.specify/feature.json` here. Stay on git branch `feature/reportportal-integration`.
- **Rationale**: Setup initially resolved the pinned directory `specs/052-hosen-screen34-sanity`, which already has a finished Hosen Screens 3 and 4 plan. The user task is Authorities Screen 1. Writing into `052` would replace that plan. This repository already plans a new spec directory without switching the long-lived checkout (see `050` and `052`).
- **Alternatives considered**: Overwrite `052` (rejects the current Hosen plan). Create a new git branch (the established checkout for these slices is `feature/reportportal-integration`).

## 2. Where Screen 1 is read

- **Decision**: Add the Screen 1 methods to the existing `AuthoritiesStatusPage` in `pages/authorities_status/page.py`. Add the sanity package `tests/sanity/authorities_status_dashboard/`. Leave `tests/ui/authorities_status_dashboard/` unchanged.
- **Rationale**: The page already subclasses `ReportShell`, searches `הערכת מצב רשויות`, and waits for that phrase. Constitution IV puts new locators on that page. The smoke conftest already imports it and binds the fixture name `dashboard`.
- **Alternatives considered**: A new page class under `tests/` (forbidden). Editing Hosen and aliasing it (the user forbade Hosen edits, and the reports are different). A second page module beside `page.py` (the class is a binding only and can grow in place).

## 3. Source file and Screen 2

- **Decision**: Load `data/reshuyot/db_sanity.yaml` and use only `dashboard.screen_1_national_status`. Do not edit the file. Do not read, apply, or open `dashboard.screen_2_service_targets`.
- **Rationale**: The user named that block and said not to touch Screen 2 and not to edit the YAML to fix numbers. The checked-in file is the golden record, including values that look surprising (`survey_status.filled` is 24 and `out_of` is 23). A live mismatch fails the test. It is not a reason to rewrite the file in this slice.
- **Alternatives considered**: Recopy the live screen into the YAML (rejected: the user said the numbers stay). Point the test at `data/hosen/db_sanity.yaml` (wrong report). Compare Screen 2 in the same test (explicitly out of scope).

## 4. Apply order and list values

- **Decision**: The test applies `date` when the key is present, then each `filters` entry in YAML order. `PyYAML` preserves that order. A string is one `select_screen_1_filter` call. A list is one call per item, in list order, with the item passed as a string. `filters.sub_district` is therefore two calls. After every call, and once more before `read_screen_1_metrics()`, the test calls `wait_for_screen_1_idle()`.
- **Rationale**: Hosen Screen 1 already applies `date` then `filters`, but it does `str(value)` on every filter value. That would turn the Authorities sub-district list into one label. The Authorities test must branch on `list` before calling the page. The second idle wait matches the Hosen test, which settles inside select and waits once more before the read.
- **Alternatives considered**: `Slicer.select_many` from the test (the test would have to know which id is multi-select, and the user asked for one `select_screen_1_filter` call per value). Stringifying the list (selects a label that is not on the slicer). Applying `filters` before `date` (the user said date first).

## 5. Selection mechanism

- **Decision**: `select_screen_1_filter(slicer_id, value)` resolves the id on the page. Known ids are `date`, `district`, and `sub_district`. Any other id raises `KeyError`. District and sub-district build a page-local `Slicer` (`kind="dropdown"`, Hebrew `role_name` on the page, settle hook that calls the Screen 1 idle wait) and call `Slicer.select` when the control is a combobox. A sandbox input that is not a combobox keeps the existing page-local input path. The date label is chosen by `_pick_open_date` (section 13) when the open list is the virtualized dropdown. A later call for the same id does not clear labels already selected. The page does not press a clear-all control between `sub_district` items.
- **Rationale**: District and sub-district are ordinary dropdowns, and `Slicer.select` already clicks a named combobox and option. The date list is virtualized. `Slicer` has no method that scrolls until one label is visible, and this slice cannot edit `core/`. Role names are report text, so they stay on `AuthoritiesStatusPage`. Exact accessible names are copied from the open report during implementation; they are not golden data and they are not written into the YAML. Hosen's smart-filter and date-iframe helpers solve תמ"צ חוסן visuals and are not copied.
- **Alternatives considered**: Edit `Slicer` to learn Authorities names or to scroll a virtualized list (breaks zero leakage and edits `core/`). Copy `_select_smart_filter` and `_select_date_combobox` from Hosen (those paths are Hosen-specific, and Hosen stays untouched). Clear the slicer before each list item (the second sub-district would replace the first). Use `collect_virtualized_rows` to find the date (section 13).

## 6. Idle

- **Decision**: `wait_for_screen_1_idle()` expects a visible `[class*='spinner']` or `[aria-busy='true']` node in the report iframe to be hidden, then expects the existing ready locator (`הערכת מצב רשויות`) to be visible. A spinner that is not showing is ignored. The `Slicer` settle hook calls the same wait on `after_select` and returns false so `Slicer.select` still confirms the combobox text.
- **Rationale**: This is the Hosen Screen 1 settle, aimed at the Authorities ready locator. It uses Playwright `expect` and the page timeout. It does not sleep, does not call `wait_for_timeout`, and does not wait for network idle.
- **Alternatives considered**: `page.wait_for_load_state("networkidle")` (rejected by the user). A fixed sleep (rejected). A new ready phrase (the page already waits for the search term, and this slice does not change that contract).

## 7. Reader shape and anchors

- **Decision**: `read_screen_1_metrics()` returns `date`, `filters`, `survey_status`, `authorities_status`, `facilities`, and `missing_daily_report`. It does not return `title` and it does not change a slicer. `section_anchor_visible` is true only for those six keys when that block's control or heading is visible. `title` and any unknown key return false, so the walk skips `title` and leaves it in the YAML.
- **Rationale**: The walk checks every YAML key whose anchor is visible. Date and filters are in the YAML and are applied, so they are read back the way Hosen reads them back. The four metric groups are the blocks the user named. `title` stays in the file and is not a checked block. Hebrew headings for the four metric blocks are copied from the live screen onto the page during implementation.
- **Alternatives considered**: Return only the four metric groups and skip date and filters (a visible date or filter anchor would then fail as an empty read, or those keys would be silently skipped). Remove `title` from the YAML (the user said to leave it and not edit the file).

## 8. How each block is read

- **Decision**: Counts and names are read with locators on `AuthoritiesStatusPage`, scoped to that block. `survey_status` returns `filled` and `out_of`. Each of `coping_well`, `may_struggle`, and `struggling` returns `count` and `authorities` rows of `name`, `score`, and `trend` when the row shows an arrow. `operation_centers` includes `unknown_in`. `protection_facilities` includes `partially_open_count`. Each facility includes `open` and `closed`, each with `count` and a list of authority names. `missing_daily_report` returns `count` and a list of names. `filters.district` is the selected label. `filters.sub_district` is the list of selected labels. `date` is the selected date label.
- **Rationale**: The YAML shape is the contract. The page publishes display text. The test applies integer, float, and string rules. `trend` may be present on a UI row when the golden row omits it; the walk ignores that extra key. A name list that is a virtualized grid uses the existing `collect_virtualized_rows` without editing it. A short list that is plain text is read from the block. That helper is not used to click the date dropdown (section 13).
- **Alternatives considered**: A new generic card reader in `core/` (one report, and the user forbade `core/` edits). Reuse Hosen `KPI` category readers (those cards are תמ"צ חוסן grades, not these buckets). Hardcode the northern authority names on the page (the user said those literals stay in the YAML).

## 9. Private compare

- **Decision**: Copy the walk shape of Hosen `_assert_tree`, `_assert_rows`, and `assert_value` into `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` as private functions. Do not import the Hosen module. Do not add `tests/helpers/` code. Authority object rows match on `name`. A list of strings matches by membership. Extra UI rows are ignored. A YAML float matches `float` of the displayed number after grouping marks are removed. A visible anchor plus an empty actual value fails. If every block is skipped, call `pytest.skip`.
- **Rationale**: Hosen's default row key is `title`. Authorities rows use `name`, so the private row matcher must key on `name` when the golden row has that field. Sharing the Hosen helpers would couple the suites and would edit the "do not edit Hosen" boundary if those helpers had to learn `name`. A new engine under `tests/helpers/` is forbidden.
- **Alternatives considered**: Import `_assert_tree` from the Hosen test (couples the suites and misses `name`). Extend the parity engine (new engine, and this slice has no SQL). Compare with `==` on the whole dict (extra UI rows would fail).

## 10. What this slice does not copy from Hosen

- **Decision**: Do not copy Screen 2, Screen 3, or Screen 4 methods. Do not copy the category SVG `tspan` reader, the resilience color map, or the smart-filter token search. Do not edit `pages/hosen_status/page.py` or `tests/sanity/hosen_status_dashboard/`.
- **Rationale**: The mirror is the Screen 1 method set, the fixture binding, the apply-then-idle-then-read order, and the private tree walk. The visuals and the YAML keys are the Authorities block.
- **Alternatives considered**: Moving shared settle code into `core/` (one more report does not justify a Layer 0 change, and `core/` is closed).

## 11. Warehouse principle

- **Decision**: This slice does not add `db/clients/` and does not query SQL Server. The golden YAML is the source of truth, matching the existing sanity suites for Hosen, Hasbara, and Credit.
- **Rationale**: The user scoped the work to `data/reshuyot/db_sanity.yaml`. Constitution V stays intact because no business SQL is added to Layer 0. A later warehouse slice is out of scope.
- **Alternatives considered**: Invent a reshuyot SQL client so the test is UI-versus-warehouse (no client exists, and the user named the YAML file).

## 13. Virtualized date dropdown

- **Decision**: `_pick_open_date` in `pages/authorities_status/page.py` scrolls the open date dropdown and clicks `value` when that row is visible. The method does not call `collect_virtualized_rows` and does not add an import for that purpose. `core/` is not edited. `Slicer` does not gain a scroll-and-search method. District, sub-district, and virtualized name-list reads stay on their current paths.
- **Rationale**: `collect_virtualized_rows` starts at the top of a grid, sweeps each horizontal page, then advances `scrollTop` by the container height until the grid is exhausted or the timeout elapses. It returns every deduped row. That is the reader for a long authority-name table. It is the wrong tool for one dropdown click. `Slicer.select` opens a combobox, expects an `option` or `checkbox` with the exact name to be visible, then calls `scroll_into_view_if_needed`. A virtualized Power BI date row that is not in the current viewport never becomes that locator. Both helpers live under `core/`, which this slice must not edit. A short loop on the page is enough to page the open list until the date is visible, click it, or fail with the rows that were on screen.
- **Algorithm** (all of it inside `_pick_open_date`):
  1. Locate the scrollable container inside the open slicer. Prefer a node whose class contains `scrollRegion`. If that node is not there, send `PageDown` to the focused dropdown list.
  2. Loop at most 20 times.
  3. On each pass, if a locator for `value` is visible (`locator.is_visible()`), click it and return.
  4. If it is not visible, scroll down. Either `press("PageDown")` on the list container, or `evaluate("node => node.scrollTop += 150")` on the scrollable container.
  5. Read `scrollTop` before and after the scroll when the container exposes it. If the value does not change, the list is at the bottom. Break.
  6. If the loop ends without a click, raise `AssertionError` with the texts of the rows that are visible then. Keep the current failure shape: `Open date option {value!r} was not visible. rows=...`.
- **Alternatives considered**: Call `collect_virtualized_rows` and click a collected label (scrapes the whole dropdown, and the user forbade that helper for this click). Add `Slicer` scroll-until-visible in `core/components/slicer.py` (forbidden `core/` edit, and it would be a one-report API). Copy Hosen's date combobox helper (Hosen stays untouched). Keep the current timeout loop that rechecks the DOM and never scrolls (an off-screen date never appears). An unbounded loop (can hang the sanity run; 20 steps plus a stuck-`scrollTop` break is the cap).

## 12. Catalog

- **Decision**: Add an Authorities Status section to `docs/COVERAGE_CATALOG.md` mapping `screen_1_national_status` keys to `read_screen_1_metrics` and `test_authorities_screen1_matches_golden`. State that the source is the YAML file, not SQL, and that Screen 2 is not in this slice.
- **Rationale**: The constitution says the coverage catalog stays consistent with page-object changes. The catalog has no Authorities section today.
- **Alternatives considered**: Skip the catalog (fails the catalog gate). Document Screen 2 readers that this slice does not add.

## 14. Empty `survey_status.filled`

- **Decision**: Fix the empty read in `pages/authorities_status/page.py`. Keep `assert_value` and `_assert_tree` as synchronous compares. Leave `data/reshuyot/db_sanity.yaml` at `filled: 18`.
- **Rationale**: The failure string `dashboard.screen_1_national_status.survey_status.filled: ui='' golden=18` is built in `assert_value` when the golden node is an `int` and the UI string has no digit. `actual` is `""`. That string is what `_read_survey_status` stores. The survey anchor is visible (`_document_visible("רשויות הזינו את הסקר")`), otherwise the walk would have skipped the block. `_assert_tree` then walks a non-empty dict and fails on the key `filled`. The idle wait only hides a spinner and shows `הערכת מצב רשויות`. It does not wait for this count.
  `_svg_text` locates `svg[aria-label^='GOALS_COUNT_MUNI']` inside `_section("רשויות הזינו את הסקר")` and calls `text_content()` on the SVG. A missing node, an empty `text_content`, or any exception becomes `""`. The heading visual can contain some other `svg[aria-label]`, so `_section` stops before the count. Power BI also paints the digits on a child `tspan` or `text` after the SVG exists. Hosen already records that `innerText` on `tspan` is empty; this page uses `text_content`, and the read target has to be that text node.
  `out_of` uses `svg[aria-label*='Muni_Code']` on the same section and is unread by this failure, because the walk stops at `filled`. It gets the same text-node wait.
- **Read algorithm** (survey measures only):
  1. On the report frame, take `svg[aria-label^='GOALS_COUNT_MUNI']` for `filled` and `svg[aria-label*='Muni_Code']` for `out_of`.
  2. `expect` that SVG `to_be_visible` within `self.timeout`.
  3. Prefer a descendant `tspan` or `text` filtered to a digit. `expect` it `to_be_visible`, then `expect` it `to_have_text` with a digit pattern, then read `text_content`.
  4. When no digit text node appears, `expect` the SVG itself `to_have_text` with a digit pattern and read its `text_content`.
  5. On timeout, return `""`. The sanity assertion keeps the YAML path. Do not write the golden `18` into the page.
- **Assertion review**: No code change. `assert_value` must keep failing `''` against `18`. It must not treat `''` as `0` (`struggling.count` is a real `0` and is a different string, `"0"`). `_assert_tree` must keep descending into `survey_status` and failing on `.filled`. A retry inside the test would move a locator into the test body and would hide a reader that returned early. `wait_for_screen_1_idle()` stays the spinner and ready-phrase wait.
- **Scope**: Status counts and facility SVG reads stay section-scoped. The report-frame lookup is only the two survey measures. `_facility_sides` is unchanged in this fix.
- **Alternatives considered**: Sleep or `wait_for_timeout` until the card looks ready (forbidden). `networkidle` (forbidden). Edit the YAML to `""` or to whatever the early read captured (the golden file stays). Retry inside `assert_value` (the test would own the wait). Copy Hosen `_svg_grade` (`.value tspan` on a different card, and Hosen stays untouched). Parse the aria-label for the number (the accessible name is the measure id; the digits are the text node). Coerce `''` to `0` (would pass a missed read when the golden count is `0`).
