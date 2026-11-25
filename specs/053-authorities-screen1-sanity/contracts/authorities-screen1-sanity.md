# Contract: Authorities Status Screen 1 Sanity

**Feature**: `053-authorities-screen1-sanity` | **Date**: 2026-11-18, survey read amended 2026-11-19

Hosen, Hasbara, Credit, Alerts, fleet, and `core/` stay unchanged. Root `conftest.py` stays.
`data/reshuyot/db_sanity.yaml` stays unchanged. The smoke module stays a one-line freshness
check. Screen 2 is not opened.

## Page

`pages/authorities_status/page.py`

Class `AuthoritiesStatusPage` inherits `ReportShell`. Existing surface, unchanged:

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `הערכת מצב רשויות` |
| `_report_ready_locator()` | iframe phrase `הערכת מצב רשויות` |
| Freshness | inherited `verify_freshness()` |

Smoke conftest stays:

```python
from tests.helpers.dashboard_fixture import bind_dashboard
from pages.authorities_status.page import AuthoritiesStatusPage

dashboard = bind_dashboard(AuthoritiesStatusPage)
```

## Methods (additive)

### `select_screen_1_filter(self, slicer_id: str, value: str) -> None`

Selects one label. The test calls this for `date` when that string is present, then once per
filter label.

- Resolve `slicer_id` with the page role table. Known ids: `date`, `district`, `sub_district`.
- Unknown id raises `KeyError` before the metric read.
- For `district` and `sub_district`, when the control is a combobox, build Layer 2 `Slicer`
  with one `SlicerDefinition`: that id, the Hebrew `role_name` from the page table,
  `kind="dropdown"`. `settle` is the Screen 1 hook. Call `Slicer.select(slicer_id, value)`.
  `core/` is not edited.
- Do not clear existing labels before the click. Two calls with `sub_district` leave both
  names selected.
- The settle hook, on `after_select`, runs `wait_for_screen_1_idle` and returns false so
  `Slicer.select` still checks the combobox text.
- Hebrew role names live only in this page. The test does not contain them.
- `date` does not use `collect_virtualized_rows`. When the open list is the virtualized
  dropdown, `_pick_open_date` clicks it. See below.

### `_pick_open_date` (date dropdown only)

Private method on `AuthoritiesStatusPage`. The test does not call it. All of the logic stays
in `pages/authorities_status/page.py`.

- Do not import or call `collect_virtualized_rows` on this path. Do not edit
  `core/components/slicer.py` or `core/components/virtual_grid.py`.
- Locate the scrollable container inside the open slicer. Prefer a node whose class contains
  `scrollRegion`. If that node is absent, send `PageDown` to the focused dropdown list.
- Loop at most 20 times.
  - If a locator for `value` is visible (`is_visible()`), click it and return.
  - Otherwise scroll down with `press("PageDown")` on the list container, or
    `evaluate("node => node.scrollTop += 150")` on the scrollable container.
  - When the container exposes `scrollTop`, read it before and after the scroll. If it does
    not change, the list is at the bottom. Break.
- If the loop ends without a click, raise `AssertionError` that includes the texts of the
  rows visible at that moment. The message keeps the current shape:
  `Open date option {value!r} was not visible. rows=...`.
- After a successful click, the caller still waits for Screen 1 idle and checks that the
  combobox text contains `value`.

### `wait_for_screen_1_idle(self) -> None`

- If the report iframe has a visible node whose class contains `spinner`, or a visible node
  with `aria-busy="true"`, expect that node hidden within `self.timeout`.
- A spinner that is not showing is not a failure.
- Then expect `_report_ready_locator()` visible within `self.timeout`.
- Does not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`.

### `read_screen_1_metrics(self) -> dict`

Reads Screen 1 after date and filters are applied and idle has been waited. Returns the keys
in [data-model.md](../data-model.md): `date`, `filters`, `survey_status`,
`authorities_status`, `facilities`, and `missing_daily_report`.

Does not return `title`. Does not change a slicer. Does not open Screen 2. Does not call
`sleep`, `wait_for_timeout`, or a network-idle wait. Does not embed golden numbers, authority
names, or filter values.

`filters.district` is a string. `filters.sub_district` is a list of the selected labels.
Authority rows under `authorities_status` use `name`, `score`, and `trend` when that row shows
an arrow. Facility `open.authorities`, `closed.authorities`, and
`missing_daily_report.authorities` are lists of names. `operation_centers.unknown_in` and
`protection_facilities.partially_open_count` are included.

A name list that virtualizes uses `collect_virtualized_rows` as it exists. The page supplies
the grid and the row callback. `core/components/virtual_grid.py` is not edited. That call is
not used by `_pick_open_date`.

### Survey `filled` and `out_of`

`survey_status.filled` and `survey_status.out_of` are read on the report frame, after
`wait_for_screen_1_idle()` has already returned.

| Field | SVG | Text node |
|-------|-----|-----------|
| `filled` | `svg[aria-label^='GOALS_COUNT_MUNI']` | descendant `tspan` or `text` whose text contains a digit |
| `out_of` | `svg[aria-label*='Muni_Code']` | same |

- `expect` the SVG `to_be_visible` within `self.timeout`.
- `expect` the digit text node `to_be_visible`, then `to_have_text` with a digit pattern, within `self.timeout`.
- Read that node with `text_content`. When the SVG has no digit `tspan` or `text`, apply the same `to_have_text` wait to the SVG and read its `text_content`.
- A timeout returns `""`. The test assertion stays `ui='' golden=18` for an empty `filled`. The page does not substitute the golden integer.
- `wait_for_screen_1_idle()` does not gain this wait. It still hides a visible spinner and shows the ready phrase.
- Callers of `_svg_text` for status and facility counts stay inside their section. This frame lookup is only the two survey measures.

The sanity helpers do not change:

- `assert_value` parses an integer from the returned string. `''` has no digit, so it fails against `18`. `''` is not parsed as `0`.
- `_assert_tree` walks `survey_status` and fails on `.filled` when that string is empty. It does not retry the browser.

### `section_anchor_visible(self, section: str) -> bool`

| `section` | True when |
|-----------|-----------|
| `date` | the date control is visible |
| `filters` | a Screen 1 filter control is visible |
| `survey_status` | the survey heading is visible |
| `authorities_status` | the status heading is visible |
| `facilities` | the facilities heading is visible |
| `missing_daily_report` | the missing-report heading is visible |
| `title` and anything else | false |

Heading text is copied from the live report onto the page during implementation. A locator
failure returns false. It does not raise.

## Sanity test

`tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`

Fixture, from `conftest.py`, matching Hosen:

```python
from pages.authorities_status.page import AuthoritiesStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

authorities_status_dashboard = bind_dashboard(
    AuthoritiesStatusPage, "authorities_status_dashboard"
)
```

The test is marked `sanity`. Name: `test_authorities_screen1_matches_golden`.

Apply and read:

1. Load `dashboard.screen_1_national_status`. Do not read `screen_2_service_targets`.
2. If `date` is present and non-empty, `select_screen_1_filter("date", str(date))`, then
   `wait_for_screen_1_idle()`.
3. For each `filters` item in YAML order, if the value is a list, select each item in order;
   otherwise select the value once. After each selection, `wait_for_screen_1_idle()`.
4. `wait_for_screen_1_idle()` once more.
5. `actual = read_screen_1_metrics()`.
6. Walk every key of the golden block. Skip a key whose anchor is not visible. A visible
   anchor with an empty read fails through the private tree walk. If the block is non-empty
   and every key was skipped, `pytest.skip`.

Private helpers in this module only:

- Integer: grouped or plain digits.
- Float: displayed number, so `93.0` matches `93` or `93.0`, and `86.9` stays `86.9`.
- String: display text after bidi marks and outer whitespace are removed.
- List of strings: golden names present; extra UI names ignored.
- List of objects: identity field `name`; compare only keys on the golden row, so `trend` is
  required only when the YAML row has it.
- Mapping: every golden key matches; extra UI keys ignored.

Failure messages include the YAML path. The module does not contain the golden date, the
district name, the sub-district names, authority names, or the golden counts.

## Catalog

`docs/COVERAGE_CATALOG.md` gains an Authorities Status section. Each checked key maps to
`read_screen_1_metrics()` and `test_authorities_screen1_matches_golden`. The section states
the source file is `data/reshuyot/db_sanity.yaml` and that Screen 2 has no reader in this slice.

## Out of scope

- `core/portal/` and `core/components/`
- `pages/hosen_status/` and `tests/sanity/hosen_status_dashboard/`
- `tests/ui/hosen_status_dashboard/`
- `tests/ui/authorities_status_dashboard/`
- `data/reshuyot/db_sanity.yaml`, including `screen_2_service_targets`
- `data/hosen/`, `data/hasbara/`, `data/credit/`, `data/alerts/`
- `tests/helpers/` other than the existing `bind_dashboard` call
- `db/`
- Root `conftest.py`
