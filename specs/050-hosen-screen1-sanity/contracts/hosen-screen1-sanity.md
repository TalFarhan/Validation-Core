# Contract: Hosen Status Screen 1 Sanity

**Feature**: `050-hosen-screen1-sanity` | **Date**: 2026-11-16

Hasbara, Credit, Alerts, fleet, and `core/` stay unchanged. Root `conftest.py` stays. The smoke
module stays a one-line freshness check.

## Page

`pages/hosen_status/page.py`

Class `HosenStatusPage` inherits `ReportShell`. Existing surface, unchanged:

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `תמ"צ חוסן` |
| `_report_ready_locator()` | iframe text `תמ"צ ארצי - דיווחי קה"א יקל"ר`, exact |
| `LAST_REFRESH_PHRASE` | `מועד רענון` |
| Freshness | inherited `verify_freshness()` |

Smoke conftest keeps:

```python
from pages.hosen_status.page import HosenStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

dashboard = bind_dashboard(HosenStatusPage)
```

## Method (additive)

### `select_screen_1_filter(self, slicer_id: str, value: str) -> None`

Selects one golden label. The test calls this for `screen_1_landing.date` when that string is
present, then once per entry in `filters`, in YAML order, before `read_screen_1_metrics`.

- Resolve `slicer_id` with the page filter-role table. The sub-district id is `subdistrict`.
- Unknown id raises `KeyError`. The metric read does not run.
- `district` and `subdistrict` use `_select_smart_filter`. `date` uses the Date section
  below. `Slicer.select` is the date call only when the open listbox is named `SlicerDate`.
- The settle hook, on `after_select`: if the report iframe has a visible `spinner` class or
  `aria-busy="true"` node, expect it hidden within `self.timeout`; then expect the Screen 1
  ready locator visible. A missing spinner is not a failure. The hook returns false.
- The `בחירת נפה` control is the custom-card override (`_select_smart_filter` for
  `subdistrict`), not the combobox passed to `Slicer.select`.
- The search `<input>` click in that block is `search_input.click(force=True)`. An unforced
  click times out because `<ul class="TokensContainer">` intercepts pointer events.
- The visible `li` option click in that block stays `force=True`.
- Inline comments in this method are English.
- `district` and `subdistrict` stay on `_select_smart_filter`. `date` does not.

#### Date

When `slicer_id` is `date`:

- Resolve the combobox once with `_filter_control`. Do not query `_report_frame()` again for
  a combobox named `SlicerDate`.
- Click that locator once. Do not call `_choose_dropdown_option` (it clicks the combobox again).
- Find the open listbox and the option for `value` in the control's owner frame and in iframes
  nested in that frame.
- Call `Slicer.select` only when the open listbox accessible name is `SlicerDate` and that same
  frame contains the combobox `Slicer.select` clicks. The `Slicer` `frame` is that listbox
  frame. `role_name` is `SlicerDate`. `kind` is `dropdown`. `settle` is `_screen_1_settle`.
  `core/` is not edited. Page code does not click the combobox again around this call.
- Otherwise click the open option for `value` in that frame tree. Do not click the combobox
  again. Do not call `Slicer.select`.
- Then call `_screen_1_settle("after_select")`.
- If the plain combobox text does not contain `value`, raise `AssertionError`. Do not catch
  that raise, and do not catch a miss from the option click or from `Slicer.select`.
- This method does not call `page.wait_for_timeout`.

### `wait_for_screen_1_idle(self) -> None`

Runs the same spinner-then-ready settle once after the filter loop and before the metric read.
Does not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`.

### `read_screen_1_metrics(self) -> dict`

Reads the landing screen after the golden date and filters have been applied and
`wait_for_screen_1_idle()` has returned. Returns the keys in
[data-model.md](../data-model.md): `survey_status`, `kpis`, `resilience_scores`, `filters`,
and `date`.

Waits use `expect(...).to_be_visible(timeout=self.timeout)` on each section anchor. The method
does not call `sleep`, `wait_for_timeout`, or a network-idle wait. It does not read a canvas
bitmap. It does not change a slicer.

#### Filters

- Build `Slicer` with page-local `SlicerDefinition` rows (`id`, Hebrew `role_name`, `kind="dropdown"`).
- For each id in the page role table, read `control(id)` once it is visible.
- Return the map under `filters`. The role name is not part of a returned label.
- `section_anchor_visible("filters")` is true when the report iframe has a combobox.

#### Date

- `date` is the selected label on the date combobox, role name and bidi marks removed.
- The page reads that label. It does not embed the golden date string.
- `section_anchor_visible("date")` is true when that combobox is visible.

#### KPIs

- Construct `KPI` with the report page and the report iframe.
- National card title constant starts as `הערכת קה״א - ממוצע ארצי`. Replace the quote character
  with the live accessible name if the DOM uses `"` instead of `״`.
- The national card's `percentage` is the display string, including `%`.
- `trend` on the national card is `up`, `down`, or `flat`, from a non-canvas node inside
  `KPI.card(title)`.
- The grade on every card, national and category, is `text_content()` of `.value tspan`
  scoped to that card. The page does not use `inner_text()` for that node and does not edit
  `KPI.read_text`.
- `kpis.categories` lists the category cards. Each item has `title`, `score`, and
  `trend_direction`. `score` is the same SVG string. `trend_direction` uses the same
  `up` / `down` / `flat` classification as `trend`.

#### Resilience table

- Anchor text: `ציון חוסן`.
- Call `collect_virtualized_rows(grid, read_visible, row_id, timeout_ms=self.timeout)`.
- `read_visible` returns rows with `authority`, `score`, and `status`.
- `authority` is the first line of that cell:

  ```python
  extracted_text = cells.nth(authority_index).inner_text(timeout=500) or ""
  authority = _plain(extracted_text.split("\n")[0])
  ```

  A following accessibility line is not part of the key. The score cell is not split.
- `row_id` returns that same `authority` string.
- `status` is `green`, `yellow`, or the raw `rgb(...)` when the computed background is neither.

#### Survey status

- Locators live on this page.
- `submitted` and `total` are the digit strings from the top-left block (a `7` out of `12`
  shape, whatever separator the live text uses).
- `missing_authorities` is the list of names in that block.

## Sanity module

`tests/sanity/hosen_status_dashboard/conftest.py`

```python
from pages.hosen_status.page import HosenStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

hosen_status_dashboard = bind_dashboard(HosenStatusPage, "hosen_status_dashboard")
```

`tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`

| Rule | Behavior |
|------|----------|
| Fixture | `hosen_status_dashboard` |
| Entry | `test_hosen_screen1_matches_golden` |
| Golden path | `data/hosen/db_sanity.yaml` → `hosen_dashboard` → `screen_1_landing` |
| Date step | `expected.get("date")`, then `select_screen_1_filter("date", value)` when the string is present. The value comes from the YAML |
| Filter step | `filters = expected.get("filters", {})`, then `select_screen_1_filter` per item. `district` and `subdistrict` stay on the smart-filter path |
| Idle step | `wait_for_screen_1_idle()` after the loop, before the read |
| Call | `read_screen_1_metrics()` once, only after the idle step |
| Required keys | `survey_status`, `kpis`, `resilience_scores`, `filters` |
| Subset | Every golden key matches. Extra UI rows, categories, names, and slicers do not fail |
| Comments | English inside functions. The test does not name `district` or `subdistrict` |
| Integers | YAML `1324` matches UI `1,324` and `1324` |
| Strings | Exact match after bidi marks and outer whitespace are removed |
| Empty reader | Fail when the anchor is visible and the golden block has data |
| Missing anchor | `pytest.skip` that block only |
| Helpers | Private functions in this module. No import from Hasbara, Credit, or Alerts. No new file under `tests/helpers/` |

## Out of scope

- `core/portal/`, `core/components/`
- `data/hasbara/`, `data/credit/`, `data/alerts/`
- Pages and tests of those three reports
- `db/clients/`
- Editing `test_dashboard_updated_within_24_hours`
- A second Hosen screen or a tab click
