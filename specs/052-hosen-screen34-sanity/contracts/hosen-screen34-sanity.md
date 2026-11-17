# Contract: Hosen Status Screens 3 and 4 Sanity

**Feature**: `052-hosen-screen34-sanity` | **Date**: 2026-11-17

Screens 1 and 2, Hasbara, Credit, Alerts, fleet pages, and `core/portal` stay unchanged. The
smoke module stays a one-line freshness check. `data/hosen/db_sanity.yaml` stays as checked in.
`core/components/visual_table.py` and `core/components/slicer.py` stay as they are.
`core/components/virtual_grid.py` changes only the `scrollTop` stop inside
`collect_virtualized_rows`.

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
| `open_investigation_screen` | Screen 2 title, Screen 2 settle |
| `select_screen_2_filter` | Screen 2 date and smart filters, Screen 2 settle |
| `wait_for_screen_2_idle` | spinner, then the Screen 2 title |
| `read_screen_2_metrics` | investigation-screen dict |
| `screen_2_section_visible` | Screen 2 sections only |
| `_mark_visual_host` | marks `vcGroupBody` (width ≥ 200, height ≥ 120); does not mark `visualHeaderAbove` |
| `_FILTER_ROLES` | `district`, `subdistrict`, `date` only |
| `_select_smart_filter` / `_select_date_combobox` | optional settle; default remains `_screen_1_settle` |

The sanity fixture in `tests/sanity/hosen_status_dashboard/conftest.py` stays
`bind_dashboard(HosenStatusPage, "hosen_status_dashboard")`. This slice does not add a fixture.

## Methods (additive)

### `open_geographic_screen(self, title: str) -> None`

Opens the geographic screen. `title` is `screen_3_geographic_investigation.title` from the test.

- Candidate labels are the full title and, when the title contains ` - `, the segment after the last separator.
- Match `"` and `״` as the same character when finding the control and when expecting the heading.
- Click through the existing `_navigation_scopes` and `_click_named_control` helpers.
- Store `title` as the Screen 3 anchor.
- Settle: hide a visible spinner, then expect the title visible.
- Do not change `_report_ready_locator` or `open_investigation_screen`.

### `open_excel_export_screen(self, title: str) -> None`

Same click and quote rules. `title` is `screen_4_excel_export.title`. Store it as the Screen 4
anchor and settle on that title.

### `select_screen_3_date_range(self, start: str, end: str) -> None`

Applies `start`, then `end`, through `_select_date_combobox` with settle `_screen_3_settle`.

- Two visible date comboboxes: visual order (top, then left) is start, then end.
- Hebrew accessible names of those controls are page constants.
- After each settle, combobox text that does not contain the value still raises `AssertionError`.
- Does not call `select_screen_2_filter`.
- No `sleep`, no `wait_for_timeout`, no `networkidle`.

### `select_screen_3_filter(self, slicer_id: str, value: str) -> None`

Selects one non-null golden label on Screen 3, then waits for the Screen 3 anchor.

- `level_selected`, `district`, `subdistrict`, and `authority` use `_select_smart_filter` with settle `_screen_3_settle`.
- Placeholder hints for those ids live in a Screen 3 tuple. They are not added to `_FILTER_ROLES`.
- `level_selected` is not typed into the district control.
- The caller does not invoke this method when the YAML value is `null`.
- Unknown id raises `KeyError`.

### `select_screen_4_filter(self, slicer_id: str, value: str) -> None`

Selects one golden label on Screen 4, then waits for the Screen 4 anchor.

- `date` uses `_select_date_combobox` with settle `_screen_4_settle`.
- `sector`, `district`, `subdistrict`, and `authority` use `_select_smart_filter` with settle `_screen_4_settle` and a Screen 4 placeholder tuple.
- The caller does not invoke this method when the YAML value is `null`.
- Unknown id raises `KeyError`.
- After the date settle, combobox text that does not contain `value` still raises `AssertionError`.

### `wait_for_screen_3_idle(self) -> None` / `wait_for_screen_4_idle(self) -> None`

Run that screen's settle once after the filter loop and before the metric read.

Settle uses the spinner locator already in `_hide_visible_spinner`:

- Report iframe, visible `[class*='spinner']` or `[aria-busy='true']`, expected hidden within `self.timeout` when the count is greater than zero.
- Then that screen's title expected visible within `self.timeout`.

### `screen_3_section_visible(self, section: str) -> bool`

Screen 3 only.

| `section` | True when |
|-----------|-----------|
| `title` | geographic title text is visible |
| `date_range` | both date controls are visible |
| `filters` | a smart-filter shell or a combobox is visible |
| `final_resilience_score` | that chart title is visible |
| `categories` | at least one category chart title is visible |

Any other section returns `False`.

### `screen_4_section_visible(self, section: str) -> bool`

Screen 4 only.

| `section` | True when |
|-----------|-----------|
| `title` | export title text is visible |
| `date` | the date combobox is visible |
| `filters` | a smart-filter shell or a combobox is visible |
| `data_table` | a visible column header containing `רשות` |

Any other section returns `False`.

### `read_screen_3_metrics(self) -> dict`

Called only after `wait_for_screen_3_idle()`. Returns `title`, `date_range`, `filters`, and
`graphs`.

`graphs.final_resilience_score` contains `title`, `legend`, and `data` (`date`, `score`).
`graphs.categories` is a list of `title` plus `data`.

- Legend text is taken from the marked chart host before `read_rows`.
- Each chart calls `VisualTable.read_rows` with the `_mark_visual_host` locator.
- The mark is cleared in a `finally`.
- `date` is the `DD/MM/YYYY` cell. `score` is `_percent_token` of the percent cell, or `""`.
- The page does not embed golden dates, scores, or the eight category titles.

### `read_screen_4_metrics(self) -> dict`

Called only after `wait_for_screen_4_idle()`. Returns `title`, `date`, `filters`, and
`data_table`.

- `data_table` comes from `collect_virtualized_rows` on the authority grid.
- `VisualTable` is not used for this grid.
- No download is started.
- `authority` is the first line of the authority cell.
- Metric fields use the Screen 4 header tuple and `_percent_token`.
- `_SCREEN2_HEADERS` is not the map for this table.

## `collect_virtualized_rows` (existing signature)

`core/components/virtual_grid.py`

```text
collect_virtualized_rows(grid, read_visible, row_id, *, timeout_ms) -> list[dict]
```

The signature stays. Call sites in `VisualTable`, Screen 1, Screen 2, and fleet stay.

Stop rule after this slice:

1. Start with `scrollTop` at 0.
2. Store the painted rows. Dedupe by `row_id`. A later viewport may fill a blank cell.
3. Assign `scrollTop` forward by about one client height and read it back.
4. If that node did not move, try the other overflow nodes in the same family.
5. If no node's `scrollTop` changed, stop.
6. If `scrollTop` increased, store rows and continue, including when the viewport added no new id.
7. Stop as well when `timeout_ms` elapses.

No Hebrew, no date literal, and no report name is added to this module.

## Tests

`tests/sanity/hosen_status_dashboard/test_screen3_sanity.py`

- Marker: `sanity`.
- Test: `test_hosen_screen3_matches_golden`.
- Fixture: `hosen_status_dashboard`.
- Loads `hosen_dashboard.screen_3_geographic_investigation` with `yaml.safe_load`.
- Does not import `test_screen1_sanity` or `test_screen2_sanity`.
- Skips a filter whose value is `None` before calling `select_screen_3_filter`.
- Failure prefix: `hosen_dashboard.screen_3_geographic_investigation`.

`tests/sanity/hosen_status_dashboard/test_screen4_sanity.py`

- Marker: `sanity`.
- Test: `test_hosen_screen4_matches_golden`.
- Fixture: `hosen_status_dashboard`.
- Loads `hosen_dashboard.screen_4_excel_export`.
- Does not import the Screen 1, Screen 2, or Screen 3 test module.
- Skips a filter whose value is `None`.
- Failure prefix: `hosen_dashboard.screen_4_excel_export`.
- Does not assert a downloaded file.

Shared compare rules, private to each file:

- Display text matches after bidi trim. Percents are not parsed. `75.0%` does not match `75%`.
- Titles and authority names treat `"` and `״` as the same character.
- YAML `null` matches `""` and does not match `0%`.
- Chart rows match on `date`. Categories match on `title`. Export rows match on `authority`.
- Extra UI rows, extra dates, and extra charts are ignored.
- A visible anchor with an empty reader fails when the golden node has data.
- A missing anchor skips that block. Every block on that screen skipped calls `pytest.skip`.

## Catalog

`docs/COVERAGE_CATALOG.md` section 11 gains the Screen 3 and Screen 4 keys listed in the plan.
Screen 1 and Screen 2 rows stay. The source stays the YAML file.

## Gates

- `pytest tests/sanity/hosen_status_dashboard/test_screen3_sanity.py`
- `pytest tests/sanity/hosen_status_dashboard/test_screen4_sanity.py`
- `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
- `pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`
- `pytest tests/ui/fleet_dashboard/` at 100%, because `virtual_grid.py` changes
- `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` still calls `dashboard.verify_freshness()` and is not edited
