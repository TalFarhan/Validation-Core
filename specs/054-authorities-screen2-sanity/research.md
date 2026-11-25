# Phase 0 Research: Authorities Status Screen 2 YAML Sanity

**Feature**: `054-authorities-screen2-sanity` | **Date**: 2026-11-24

All technical-context unknowns are resolved below. Nothing remains NEEDS CLARIFICATION.

## 1. Feature directory

- **Decision**: Plan this slice in `specs/054-authorities-screen2-sanity`. Repoint `.specify/feature.json` here. Stay on git branch `feature/reportportal-integration`.
- **Rationale**: `.specify/feature.json` previously pinned `specs/053-authorities-screen1-sanity`, which the user forbade editing. This repository already plans a new spec directory without switching the long-lived checkout (see `053` itself). Screen 2 is a new slice, not an amendment of Screen 1's plan.
- **Alternatives considered**: Write into `053` (rejects the closed Screen 1 spec). Create a new git branch (the user said do not switch git branches; the established checkout is `feature/reportportal-integration`).

## 2. Where Screen 2 is read

- **Decision**: Add the Screen 2 methods to the existing `AuthoritiesStatusPage` in `pages/authorities_status/page.py`. Add `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`. Leave `test_screen1_sanity.py`, the existing sanity conftest, and `tests/ui/authorities_status_dashboard/` unchanged.
- **Rationale**: Constitution IV puts new locators on that page. The class already subclasses `ReportShell` and already has Screen 1 select, idle, read, and `_pick_open_date`. The sanity fixture `authorities_status_dashboard` already binds it. A second page class under `tests/` is forbidden.
- **Alternatives considered**: A new page module beside `page.py` (the class is the binding and can grow in place). Editing Hosen and aliasing it (forbidden). Changing the Screen 1 test to also open Screen 2 (forbidden).

## 3. Source file and Screen 1 block

- **Decision**: Load `data/reshuyot/db_sanity.yaml` and use only `dashboard.screen_2_service_targets`. Do not edit the file. Do not read, apply, or compare `dashboard.screen_1_national_status` from the Screen 2 test.
- **Rationale**: The user named that block and said not to touch the YAML. A live mismatch fails the test. It is not a reason to rewrite the file.
- **Alternatives considered**: Recopy the live screen into the YAML (rejected). Point the test at `data/hosen/db_sanity.yaml` (wrong report). Compare Screen 1 in the same test (Screen 1 has its own module, which must not be edited).

## 4. As-loaded `grade_trends` and `data`

- **Decision**: Keep the checked-in indent. PyYAML `safe_load` of the current file yields `grade_trends is None` and a sibling key `data` that is a list of ten `{date, scores}` objects. `read_screen_2_metrics()` returns that shape. The walk compares trend rows on `data`. `screen_2_section_visible("grade_trends")` is false. `screen_2_section_visible("data")` is true when the trends visual is visible.
- **Rationale**: The user forbade editing `data/reshuyot/db_sanity.yaml`. Returning nested `grade_trends.data` would make golden key `data` missing and would fail `_assert_tree` on `grade_trends: null` versus a dict. Returning only `grade_trends: [rows]` would make `data` missing. The as-loaded keys are the contract.
- **Confirmed load** (2026-11-24): keys of `screen_2_service_targets` are `title`, `date`, `filters`, `sector_profile`, `protection_data`, `service_targets`, `grade_trends`, `data`. `filters.sub_district` is the string `נפת לכיש`, not a list.
- **Alternatives considered**: Indent `data` under `grade_trends` in the YAML (forbidden edit). Special-case the test to reparent `data` (hides the loaded document from the walk). Treat `grade_trends: null` as a visible empty mapping (would fail a visible-anchor-plus-empty-read rule if the chart has rows).

## 5. Navigation

- **Decision**: Add `open_screen_2(self, title: str) -> None`. The test passes `expected["title"]` from YAML. The page stores that string for the Screen 2 ready locator and clicks a page-navigation control whose accessible name equals the title or the trailing segment after ` - `. If the control is already the current page, require the ready locator visible and idle. Do not assert the title string in the test. `screen_2_section_visible("title")` returns false.
- **Rationale**: The user said the golden title is a navigation target only. Hardcoding `'הערכת מצב רשויות - תמ"צ יעדי השירות'` on the page or in the test would embed a golden value. Power BI page rails often show the short page name (`תמ"צ יעדי השירות`) rather than the full visual title. The live control's quote spelling (ASCII `"` vs Hebrew gershayim) is a locator variant copied during implementation, not a golden metric.
- **Ready locator**: After a successful click, Screen 2 idle expects the page-name text (last title segment, with quote variants) visible in the report iframe. This is not Screen 1's `_report_ready_locator()` for `הערכת מצב רשויות`. That phrase is a prefix of the Screen 2 title and would match too early or on the wrong page.
- **Alternatives considered**: Hardcode the tab label on the page (embeds the golden title). Assert `title` in the walk (the user said do not). Reuse Screen 1 ready for Screen 2 idle (the Screen 1 phrase is not the Screen 2 page). Copy Hosen `open_investigation_screen` (forbidden).

## 6. Apply order and list values

- **Decision**: After `open_screen_2`, the test applies `date` when the key is present, then each `filters` entry in YAML order. `PyYAML` preserves that order. A string is one `select_screen_2_filter` call. A list is one call per item, in list order, with the item passed as a string. After every call, and once more before `read_screen_2_metrics()`, the test calls `wait_for_screen_2_idle()`.
- **Rationale**: Screen 1 already applies `date` then `filters` this way. Screen 2 `sub_district` is currently a string, so it is one selection. The list branch stays so a later YAML list does not become `str(list)`.
- **Alternatives considered**: `Slicer.select_many` from the test (the test would have to know which id is multi-select). Stringifying a list (selects a label that is not on the slicer). Applying `filters` before `date` (the user said date first). Calling `select_screen_1_filter` on Screen 2 (would settle on Screen 1 idle).

## 7. Selection mechanism

- **Decision**: `select_screen_2_filter(slicer_id, value)` resolves the id on the page. Known ids stay `date`, `district`, and `sub_district`. Any other id raises `KeyError`. District and sub-district build a page-local `Slicer` (`kind="dropdown"`, Hebrew `role_name` on the page, settle hook that calls Screen 2 idle) and call `Slicer.select` when the control is a combobox. A sandbox input that is not a combobox keeps the existing page-local input path. Date reuses `_pick_open_date` (and the surrounding open-combobox / listbox / search path already on the page). A later call for the same id does not clear labels already selected.
- **Internal reuse without breaking Screen 1**: Private helpers such as `_slicer` and `_select_date` may take an optional settle callable that defaults to `_screen_1_settle`. Screen 2 passes `_screen_2_settle`. Public Screen 1 methods keep their signatures and still wait for Screen 1 idle. `_pick_open_date` is not copied and is not given to `collect_virtualized_rows`.
- **Rationale**: Screen 1 already proved the date list is virtualized and that district/sub-district may be sandbox inputs. Screen 2 uses the same English ids. Role names are report text, so they stay on the page. Exact accessible names are copied from the open Screen 2 report during implementation.
- **Alternatives considered**: Edit `Slicer` (forbidden `core/` edit). Copy Hosen smart-filter helpers (forbidden). Clear the slicer before each list item (would drop an earlier label). Call `select_screen_1_filter` (Screen 1 idle).

## 8. Idle

- **Decision**: `wait_for_screen_2_idle()` expects a visible `[class*='spinner']` or `[aria-busy='true']` node in the report iframe to be hidden, then expects the Screen 2 ready locator visible. A spinner that is not showing is ignored. The `Slicer` settle hook calls the same wait on `after_select` and returns false so `Slicer.select` still confirms the combobox text. No `sleep`, no `wait_for_timeout`, no `networkidle`.
- **Rationale**: Same wait shape as Screen 1, aimed at the Screen 2 ready locator. Playwright `expect` and `self.timeout`. Screen 1 `wait_for_screen_1_idle` is not redirected.
- **Alternatives considered**: Reuse `wait_for_screen_1_idle` (wrong ready phrase). `networkidle` (rejected). A fixed sleep (rejected).

## 9. Reader shape and anchors

- **Decision**: `read_screen_2_metrics()` returns `date`, `filters`, `sector_profile`, `protection_data`, `service_targets`, `grade_trends` (`None`/empty), and `data` (list of `{date, scores}`). It does not return `title` and it does not change a slicer. `screen_2_section_visible` is a new method. It does not change Screen 1 `section_anchor_visible`.

| `section` | True when |
|-----------|-----------|
| `date` | Screen 2 date control visible |
| `filters` | a Screen 2 filter control visible |
| `sector_profile` | sector-profile heading visible |
| `protection_data` | protection-data heading visible |
| `service_targets` | service-targets heading or grid visible |
| `data` | trends visual visible |
| `title`, `grade_trends`, unknown | false |

- **Rationale**: The walk checks every YAML key whose anchor is visible. `title` is navigation-only. `grade_trends` is null in the file, so a false anchor skips it the same way Screen 1 skips `title`. `filters.district` and `filters.sub_district` are strings in this block, so the Screen 2 reader returns strings (not Screen 1's list for `sub_district`).
- **Alternatives considered**: Extend `section_anchor_visible` with Screen 2 keys (risk of changing Screen 1 behavior if headings collide). Return Screen 1's filters list shape (would fail the Screen 2 string compare). Return `title` and assert it (the user said do not).

## 10. How each block is read

- **Decision**:
  - `date`: selected date combobox label, same role as Screen 1 (`בחירת תאריך`), read after Screen 2 is showing.
  - `filters.district` / `filters.sub_district`: selected label strings (first chip or combobox text).
  - `sector_profile`: six fields from Screen 2 cards/SVGs. Integers are digit text. `defense_policy` is display text. Headings and aria prefixes are copied from the live report onto the page during implementation. Digits wait with Playwright `expect` (`to_be_visible`, then `to_have_text` with a digit) bounded by `self.timeout`. Timeout returns `""`. The page does not insert a golden integer.
  - `protection_data`: four buckets, each `count` (digit text) and `population_percentage` (displayed number). Same wait rule as sector digits.
  - `service_targets`: list of `{name, score}`. If the visual is a `role=grid`, use `collect_virtualized_rows`. Do not hardcode the fourteen names.
  - `data`: `VisualTable(self.page, self._report_frame(), timeout_ms=self.timeout).read_rows(host, name=...)` on the trends visual host. Map each header→cell dict on the page: the `DD/MM/YYYY` cell is `date`; remaining numeric cells become `scores` keyed by the displayed header text. Do not hardcode category names. Return to the canvas before the caller continues. When the host cannot be marked, return `[]`.
  - `grade_trends`: `None`.
- **Visual host**: Page-local climb from the trends heading to a visual body large enough to right-click (prefer a `visualContainer` / `vcGroupBody` that is not a header strip). This helper stays on `AuthoritiesStatusPage`. It does not copy Hosen `_mark_visual_host` and it does not edit `VisualTable`.
- **Rationale**: The YAML shape is the contract. `VisualTable` already right-clicks, clicks `הצג כטבלה`, collects rows, and clicks back. `collect_virtualized_rows` is the existing grid walker. Card digits follow the Screen 1 survey wait, not a sleep.
- **Alternatives considered**: A new generic card reader in `core/` (forbidden). Import Hosen `VisualTable` wrappers (forbidden). Hardcode service names or trend categories (golden literals). Use `collect_virtualized_rows` on the trends chart without Show-as-a-table (the chart is not a grid until `VisualTable` opens it).

## 11. Private compare

- **Decision**: Duplicate the walk shape of Screen 1 `assert_value`, `_assert_rows`, and `_assert_tree` into `test_screen2_sanity.py`. Do not import `test_screen1_sanity.py`. Do not import Hosen. Do not add `tests/helpers/` code. Object-row identity: `name` if the golden row has `name`, else `date` if it has `date`, else `title`. Nested `scores` maps use `_assert_tree` (every golden key, extra UI keys ignored, floats use the float rule). Extra UI rows ignored. A visible anchor plus an empty actual value fails. If every block is skipped, `pytest.skip`.
- **Rationale**: Screen 1 helpers do not key on `date`. Changing them would edit `test_screen1_sanity.py`. Sharing Hosen helpers is forbidden. A new engine is forbidden.
- **Alternatives considered**: Import Screen 1 helpers and add a `date` key there (edits the closed file). Compare with `==` on the whole dict (extra UI rows would fail).

## 12. What this slice does not copy from Hosen or Screen 1 tests

- **Decision**: Do not copy Hosen smart-filter, date-iframe, KPI, resilience-color, or `_mark_visual_host` helpers. Do not import Hosen modules. Do not import Screen 1 test helpers. Mirror only the method set (`open` / `select` / `idle` / `read` / section visible), the apply-then-idle-then-read order, and the private tree walk.
- **Rationale**: The visuals and the YAML keys are the Authorities Screen 2 block. The user forbade Hosen copy/import and Screen 1 test edits.
- **Alternatives considered**: Moving settle into `core/` (one more report does not justify a Layer 0 change, and `core/` is closed).

## 13. Warehouse principle

- **Decision**: This slice does not add `db/clients/` and does not query SQL Server. The golden YAML is the source of truth.
- **Rationale**: The user scoped the work to `data/reshuyot/db_sanity.yaml`. Constitution V stays intact because no business SQL is added to Layer 0.
- **Alternatives considered**: Invent a reshuyot SQL client (no client exists, and the user named the YAML file).

## 14. Catalog

- **Decision**: Extend section 12 of `docs/COVERAGE_CATALOG.md`. Keep the Screen 1 rows. Add Screen 2 rows mapping `screen_2_service_targets` keys to `open_screen_2`, `select_screen_2_filter`, `read_screen_2_metrics`, and `test_authorities_screen2_matches_golden`. State that the source is the YAML file, not SQL, that `title` is navigation-only, and that trend rows are compared on as-loaded `data`.
- **Rationale**: The constitution says the coverage catalog stays consistent with page-object changes. The catalog currently says Screen 2 is not opened by the Screen 1 slice.
- **Alternatives considered**: Skip the catalog (fails the catalog gate). Replace the Screen 1 section (Screen 1 coverage must stay).
