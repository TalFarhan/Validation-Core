# Contract: Authorities Status Screen 2 Sanity

**Feature**: `054-authorities-screen2-sanity` | **Date**: 2026-11-24

Hosen, Hasbara, Credit, Alerts, fleet, and `core/` stay unchanged. Root `conftest.py` stays.
`data/reshuyot/db_sanity.yaml` stays unchanged. The smoke module stays a one-line freshness
check. Screen 1 public methods and `test_screen1_sanity.py` stay unchanged.
`specs/053-authorities-screen1-sanity/` stays unchanged.

## Page

`pages/authorities_status/page.py`

Class `AuthoritiesStatusPage` inherits `ReportShell`. Existing surface, unchanged:

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `הערכת מצב רשויות` |
| `_report_ready_locator()` | iframe phrase `הערכת מצב רשויות` |
| Freshness | inherited `verify_freshness()` |
| Screen 1 methods | `select_screen_1_filter`, `wait_for_screen_1_idle`, `read_screen_1_metrics`, `section_anchor_visible` keep their contracts |

Smoke conftest stays:

```python
from tests.helpers.dashboard_fixture import bind_dashboard
from pages.authorities_status.page import AuthoritiesStatusPage

dashboard = bind_dashboard(AuthoritiesStatusPage)
```

Sanity conftest stays:

```python
from pages.authorities_status.page import AuthoritiesStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

authorities_status_dashboard = bind_dashboard(
    AuthoritiesStatusPage, "authorities_status_dashboard"
)
```

## Methods (additive)

### `open_screen_2(self, title: str) -> None`

Opens the Power BI page named by the golden title. The test passes `expected["title"]`.
The page does not hardcode that string.

- Use `title` as a navigation target only: click a visible page-navigation control whose
  accessible name equals `title` or the trailing segment after ` - `.
- Quote spelling of `תמ"צ` is a locator variant on the page (ASCII vs Hebrew gershayim).
  It is not a golden metric and is not copied from Hosen.
- Store `title` for the Screen 2 ready locator (page-name segment).
- If the control is missing and the ready locator is not already visible, raise
  `AssertionError` naming the title.
- Then `wait_for_screen_2_idle()`.
- The test does not assert `title`.

### `select_screen_2_filter(self, slicer_id: str, value: str) -> None`

Selects one label. The test calls this for `date` when that string is present, then once per
filter label.

- Resolve `slicer_id` with the page role table. Known ids: `date`, `district`, `sub_district`.
- Unknown id raises `KeyError` before the metric read.
- For `district` and `sub_district`, when the control is a combobox, build Layer 2 `Slicer`
  with one `SlicerDefinition`: that id, the Hebrew `role_name` from the page table,
  `kind="dropdown"`. `settle` is the Screen 2 hook. Call `Slicer.select(slicer_id, value)`.
  `core/` is not edited.
- When the control is the existing sandbox input, reuse the Screen 1 sandbox path, then
  `wait_for_screen_2_idle()`.
- Do not clear existing labels before the click.
- The settle hook, on `after_select`, runs `wait_for_screen_2_idle` and returns false so
  `Slicer.select` still checks the combobox text.
- Hebrew role names live only in this page. The test does not contain them.
- `date` reuses `_pick_open_date`. Do not call `collect_virtualized_rows` on the date path.
  Private date helpers may take an optional settle callable that defaults to Screen 1 idle.
  Screen 1 public methods still wait for Screen 1 idle.

### `wait_for_screen_2_idle(self) -> None`

- If the report iframe has a visible node whose class contains `spinner`, or a visible node
  with `aria-busy="true"`, expect that node hidden within `self.timeout`.
- A spinner that is not showing is not a failure.
- Then expect the Screen 2 ready locator (page-name from the stored title) visible within
  `self.timeout`.
- Does not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`.
- Does not call or replace `wait_for_screen_1_idle`.

### `read_screen_2_metrics(self) -> dict`

Reads Screen 2 after it is open, date and filters are applied, and idle has been waited.
Returns the keys in [data-model.md](../data-model.md): `date`, `filters`, `sector_profile`,
`protection_data`, `service_targets`, `grade_trends`, and `data`.

Does not return `title`. Does not change a slicer. Does not call Screen 1's reader as the
Screen 2 result. Does not call `sleep`, `wait_for_timeout`, or a network-idle wait. Does not
embed golden numbers, service names, dates, or filter values.

`filters.district` is a string. `filters.sub_district` is a string. `service_targets` rows
use `name` and `score`. Trend rows under `data` use `date` and `scores`. `grade_trends` is
`None`.

A name list that virtualizes uses `collect_virtualized_rows` as it exists. Trend rows use
`VisualTable.read_rows` as it exists. The page supplies the host and maps header→cell dicts
to `{date, scores}`. `core/components/visual_table.py` and `core/components/virtual_grid.py`
are not edited. `_pick_open_date` does not call `VisualTable`.

Sector-profile and protection digits wait with Playwright `expect` (`to_be_visible`, then
`to_have_text` with a digit) on the chosen node, bounded by `self.timeout`. A timeout
returns `""`. The page does not substitute a golden integer. `wait_for_screen_2_idle()`
does not gain those card waits.

### `screen_2_section_visible(self, section: str) -> bool`

| `section` | True when |
|-----------|-----------|
| `date` | the Screen 2 date control is visible |
| `filters` | a Screen 2 filter control is visible |
| `sector_profile` | the sector-profile heading is visible |
| `protection_data` | the protection-data heading is visible |
| `service_targets` | the service-targets heading or grid is visible |
| `data` | the trends visual is visible |
| `title`, `grade_trends`, anything else | false |

Heading text is copied from the live report onto the page during implementation. A locator
failure returns false. It does not raise. This method does not replace
`section_anchor_visible`.

## Sanity test

`tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`

Fixture, from existing `conftest.py`: `authorities_status_dashboard`.

The test is marked `sanity`. Name: `test_authorities_screen2_matches_golden`.

Apply and read:

1. Load `dashboard.screen_2_service_targets`. Do not read `screen_1_national_status`.
2. `open_screen_2(str(title))` when `title` is present. Do not assert `title`.
3. If `date` is present and non-empty, `select_screen_2_filter("date", str(date))`, then
   `wait_for_screen_2_idle()`.
4. For each `filters` item in YAML order, if the value is a list, select each item in order;
   otherwise select the value once. Never pass `str(list)`. After each selection,
   `wait_for_screen_2_idle()`.
5. `wait_for_screen_2_idle()` once more.
6. `actual = read_screen_2_metrics()`.
7. Walk every key of the golden block. Skip a key whose `screen_2_section_visible` is false.
   A visible anchor with an empty read fails through the private tree walk. If the block is
   non-empty and every key was skipped, `pytest.skip`.

Private helpers in this module only (Screen 1 shape, not imported):

- Integer: grouped or plain digits.
- Float: displayed number, so `100.0` matches `100` or `100.0`, and `94.46` stays `94.46`.
- String: display text after bidi marks and outer whitespace are removed.
- List of objects: identity field `name` if present, else `date` if present. Compare only
  keys on the golden row. Nested `scores` maps walk every golden category.
- Mapping: every golden key matches; extra UI keys ignored.

Failure messages include the YAML path. The module does not contain the golden date, the
district name, the sub-district name, service names, or the golden counts.

## Catalog

`docs/COVERAGE_CATALOG.md` section 12 keeps Screen 1 rows and gains Screen 2 rows. Each
checked Screen 2 key maps to `read_screen_2_metrics()` and
`test_authorities_screen2_matches_golden`. The section states the source file is
`data/reshuyot/db_sanity.yaml`, that `title` is navigation-only, and that trend rows are
compared on as-loaded `data`.

## Out of scope

- `core/portal/` and `core/components/`
- `pages/hosen_status/` and `tests/sanity/hosen_status_dashboard/`
- `tests/ui/hosen_status_dashboard/`
- `tests/ui/authorities_status_dashboard/`
- `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`
- `data/reshuyot/db_sanity.yaml`, including the `grade_trends`/`data` indent
- `data/hosen/`, `data/hasbara/`, `data/credit/`, `data/alerts/`
- `specs/053-authorities-screen1-sanity/`
- `tests/helpers/` other than the existing `bind_dashboard` call
- `db/`
- Root `conftest.py`
- Git branch switch
