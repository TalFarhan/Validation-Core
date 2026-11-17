# Contract: Hosen Status Screen 2 Sanity

**Feature**: `051-hosen-screen2-sanity` | **Date**: 2026-11-16

Screen 1, Hasbara, Credit, Alerts, fleet, and `core/` stay unchanged. The smoke module stays a
one-line freshness check. `data/hosen/db_sanity.yaml` stays as checked in.

## Page

`pages/hosen_status/page.py`

Class `HosenStatusPage` inherits `ReportShell`. Existing surface, unchanged:

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `תמ"צ חוסן` |
| `_report_ready_locator()` | iframe text `תמ"צ ארצי - דיווחי קה"א יקל"ר`, exact |
| `LAST_REFRESH_PHRASE` | `מועד רענון` |
| `select_screen_1_filter` | date combobox path and smart-filter path, settling on Screen 1 |
| `wait_for_screen_1_idle` | spinner, then the Screen 1 ready locator |
| `read_screen_1_metrics` | landing-screen dict |
| `section_anchor_visible` | Screen 1 sections only; unknown keys stay `False` |

The sanity fixture in `tests/sanity/hosen_status_dashboard/conftest.py` stays
`bind_dashboard(HosenStatusPage, "hosen_status_dashboard")`. This slice does not add a fixture.

## Methods (additive)

### `open_investigation_screen(self, title: str) -> None`

Opens the investigation screen. `title` is `screen_2_investigation.title` from the test.

- Candidate labels are the full title and, when the title contains ` - `, the segment after the last separator.
- Match `"` and `״` as the same character when finding the control and when expecting the heading.
- Click the first visible `button`, `tab`, `link`, or `option` with that accessible name. Prefer a control inside `ניווט בין עמודים` / `Page navigation`.
- Store `title` as the Screen 2 anchor.
- Settle: hide a visible spinner, then expect the title visible.
- Do not change `_report_ready_locator`.

### `select_screen_2_filter(self, slicer_id: str, value: str) -> None`

Selects one golden label on Screen 2, then waits for the Screen 2 anchor.

- `date` uses `_select_date_combobox` with settle `_screen_2_settle`.
- `district` and `subdistrict` use `_select_smart_filter` with settle `_screen_2_settle`.
- `_select_slicer_date` receives that same settle when the open listbox is named `SlicerDate`.
- The default settle on those helpers stays `_screen_1_settle`. `select_screen_1_filter` does not pass a settle.
- Unknown id raises `KeyError`. This method does not call `_select_unnamed_combobox`.
- After the date settle, combobox text that does not contain `value` still raises `AssertionError`.
- No `sleep`, no `wait_for_timeout`, no `networkidle`.

`_screen_2_settle` uses the spinner locator already in `_wait_for_screen_1_settled`:

- Report iframe, visible `[class*='spinner']` or `[aria-busy='true']`, expected hidden within `self.timeout` when the count is greater than zero.
- Then the investigation title expected visible within `self.timeout`.

### `wait_for_screen_2_idle(self) -> None`

Runs `_screen_2_settle` once after the filter loop and before the metric read.

### `screen_2_section_visible(self, section: str) -> bool`

Screen 2 only. Does not replace `section_anchor_visible`.

| `section` | True when |
|-----------|-----------|
| `title` | investigation title text is visible |
| `date` | `_filter_control("date", ...)` is visible |
| `filters` | a smart-filter shell or a combobox is visible |
| `authorities_breakdown_table` | a visible column header containing `רשות` |
| `totals_row` | the summary label, or the sibling average visual, is visible |
| `trends_by_date_table` | the trends visual is visible |

Any other section returns `False`.

### `read_screen_2_metrics(self) -> dict`

Called only after `wait_for_screen_2_idle()`. Returns `title`, `date`, `filters`, and `tables`.

`tables` contains:

- `authorities_breakdown_table`: rows from `collect_virtualized_rows`. `authority` is the first line of the authority cell. Metric cells are compact percent strings. The summary row is not included.
- `totals_row`: the nine metric fields from the summary/average row.
- `trends_by_date_table`: rows from `VisualTable.read_rows`. `creation_date` is the `DD/MM/YYYY` cell. A blank cell is `""`.

Hebrew header constants live on the page. The test does not receive locators. `core/` is not edited. `rows_to_label_values` is not used.

The trends visual title is the page constant `_TRENDS_VISUAL_TITLE` (`מגמות המרכיבים לפי תאריך`). The golden file has no visual-title field for that chart.

`read_rows` receives the locator from `_mark_visual_host`, which is the nearest `div` matching `xpath=ancestor::div[contains(@class, 'visualContainer')][1]`. The title strip is not that locator. A right-click on the title strip is what raises `AssertionError: 'trends_by_date' has no show-as-table menu item`. When the ancestor is missing, `_trends_container` returns `None` and `_read_trends` returns `[]`. The helper does not mark the title node.

## Sanity test

`tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`

```python
@pytest.mark.sanity
def test_hosen_screen2_matches_golden(hosen_status_dashboard):
    page = hosen_status_dashboard
    expected = load_sanity_data()["screen_2_investigation"]
    page.open_investigation_screen(str(expected["title"]))
    report_date = expected.get("date")
    if report_date:
        page.select_screen_2_filter("date", str(report_date))
    for slicer_id, value in (expected.get("filters") or {}).items():
        page.select_screen_2_filter(str(slicer_id), str(value))
    page.wait_for_screen_2_idle()
    actual = page.read_screen_2_metrics()
```

`load_sanity_data` in this file reads `data/hosen/db_sanity.yaml` and returns the
`hosen_dashboard` mapping. It does not import the Screen 1 module.

Blocks, in this order:

| Block | Anchor section | Golden node |
|-------|----------------|-------------|
| `title` | `title` | string |
| `date` | `date` | string |
| `filters` | `filters` | map |
| `tables.authorities_breakdown_table` | `authorities_breakdown_table` | list keyed by `authority` |
| `tables.totals_row` | `totals_row` | map of metric fields |
| `tables.trends_by_date_table` | `trends_by_date_table` | list keyed by `creation_date` |

For each block:

- Anchor missing: record a skip and do not read that block's failure.
- Anchor visible and the golden node has data and the reader is empty: `AssertionError` whose message starts with `hosen_dashboard.screen_2_investigation.<block>`.
- Otherwise compare. A mismatch uses the same path prefix. Row paths include `[authority=...]` or `[creation_date=...]`.
- YAML `null` requires the published cell to be empty after the bidi trim.
- Percent strings and other strings compare as text. Extra authority rows, extra dates, and extra slicers are ignored.

If every block was skipped, `pytest.skip` names the skipped sections. One present anchor is still asserted.

Private helpers stay in this module. The module does not import Hasbara, Credit, or Alerts.

## Coverage catalog

`docs/COVERAGE_CATALOG.md` section 11 keeps the Screen 1 rows and gains Screen 2 rows:

| YAML key | Page method | Test |
|----------|-------------|------|
| `screen_2_investigation.title` | `open_investigation_screen` / `read_screen_2_metrics()` | `test_hosen_screen2_matches_golden` |
| `date` | `select_screen_2_filter("date", ...)` then `read_screen_2_metrics()` | `test_hosen_screen2_matches_golden` |
| `filters` | `select_screen_2_filter` for each id, then `read_screen_2_metrics()` | `test_hosen_screen2_matches_golden` |
| `tables.authorities_breakdown_table` | `read_screen_2_metrics()` (`collect_virtualized_rows`) | `test_hosen_screen2_matches_golden` |
| `tables.totals_row` | `read_screen_2_metrics()` | `test_hosen_screen2_matches_golden` |
| `tables.trends_by_date_table` | `read_screen_2_metrics()` (`VisualTable.read_rows`) | `test_hosen_screen2_matches_golden` |

The catalog states that the source is `data/hosen/db_sanity.yaml`, not SQL.

## Out of scope

- Editing `test_screen1_sanity.py` or its assertions.
- Editing `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`.
- Editing `core/portal` or `core/components`.
- Editing `data/hosen/db_sanity.yaml`.
- A SQL client, a shared compare package, or a second Hosen page module.
