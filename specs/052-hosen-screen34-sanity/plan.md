# Implementation Plan: Hosen Status Screens 3 and 4 YAML Sanity

**Branch**: `feature/reportportal-integration` (spec directory `052-hosen-screen34-sanity`) | **Date**: 2026-11-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/052-hosen-screen34-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Spec documents under `specs/050-hosen-screen1-sanity/` and
`specs/051-hosen-screen2-sanity/` are not edited.

## Summary

Add Screen 3 and Screen 4 readers on the existing Hosen Status page, plus one golden-YAML sanity
test for each screen of תמ"צ חוסן.

`HosenStatusPage.navigate()` still opens the report on Screen 1 and still waits for
`תמ"צ ארצי - דיווחי קה"א יקל"ר`. This slice adds methods that open the geographic screen and the
Excel export screen by their golden titles, apply that block's date and filters, and compare
the reading to the existing YAML. The golden file is not edited. There is no SQL client and no
new comparison engine. Screen 1 and Screen 2 test behavior stays.

1. **Open** — `open_geographic_screen(title)` and `open_excel_export_screen(title)` use the
   page-navigation click Screen 2 already uses (`_navigation_scopes`, `_click_named_control`).
   Each method stores its own title and settles on that title. `open_investigation_screen` is
   not edited.
2. **Screen 3 dates** — `select_screen_3_date_range(start, end)` calls the existing
   `_select_date_combobox` once per end, start then end, with `_screen_3_settle`.
3. **Screen 4 date** — `select_screen_4_filter("date", value)` uses that same combobox path
   with `_screen_4_settle`.
4. **Filters** — non-null entries, in YAML order, use the existing `_select_smart_filter` with
   that screen's settle. A YAML `null` is not passed to the selector. `select_screen_1_filter`
   still settles on Screen 1. `select_screen_2_filter` still settles on Screen 2.
5. **Screen 3 charts** — each chart is read with the existing `VisualTable.read_rows`. The
   right-click target is the locator `_mark_visual_host` already returns: `vcGroupBody`, not
   the ~38px `visualHeaderAbove` header. The legend is read from that host before the menu
   opens. Row identity is `date`.
6. **Screen 4 table** — the grid is already a table. `collect_virtualized_rows` reads it. Row
   identity is `authority`. No workbook is downloaded.
7. **Scroll** — `collect_virtualized_rows` keeps evaluating `scrollTop`. A viewport that adds
   no new row id does not end the walk while `scrollTop` can still increase. The page does not
   grow a second scroller. `VisualTable.read_rows` stays the chart caller and is not edited.
8. **Compare** — private helpers in each new test file. A visible anchor plus an empty reader
   fails. A missing anchor skips that block. If every block on that screen is skipped,
   `pytest.skip`. Failure messages name the YAML path.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through the existing
`hosen_status_dashboard` fixture. The existing date combobox path, `_select_smart_filter`,
`collect_virtualized_rows`, and `VisualTable`. No new package.

**Storage**: Existing golden record `data/hosen/db_sanity.yaml`
(`hosen_dashboard.screen_3_geographic_investigation` and
`hosen_dashboard.screen_4_excel_export`). This slice does not edit it. No warehouse query
and no `db/clients/hosen.py`.

**Testing**: `pytest tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` and
`test_screen4_sanity.py`. Screen 1 and Screen 2 must still pass:
`pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` and
`test_screen2_sanity.py`. The freshness smoke module is not edited. Because
`core/components/virtual_grid.py` changes, fleet smoke is a gate:
`pytest tests/ui/fleet_dashboard/`.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal validation framework. Domain page `pages/hosen_status/page.py`.
Golden YAML `data/hosen/db_sanity.yaml`. Sanity tests
`tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` and `test_screen4_sanity.py`.

**Performance Goals**: N/A. Each new test does one catalog open, one page switch, and one
screen read. Screen 3 reads nine charts (the final-score chart and eight category charts),
one `VisualTable` cycle each.

**Constraints**:

- Do not edit `core/portal`. Do not edit `core/components/visual_table.py` or
  `core/components/slicer.py`. The only Layer 2 edit is the `scrollTop` stop inside
  `collect_virtualized_rows`. That edit stays report-agnostic: no Hosen title, date, header,
  or Hebrew string.
- Do not rewrite `_select_smart_filter`, `_select_date_combobox`, `VisualTable.read_rows`, or
  `collect_virtualized_rows` as new functions. Call them.
- Do not edit `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or
  those reports' pages and tests.
- Do not import Hasbara, Credit, or Alerts page modules or their tests.
- Do not add `tests/helpers/` comparison code. The subset walk stays private in each new test.
- Do not change `test_screen1_sanity.py` or `test_screen2_sanity.py` behavior. Do not change
  `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` (`dashboard.verify_freshness()`).
- Do not edit `open_investigation_screen`, `select_screen_2_filter`, `read_screen_2_metrics`,
  `select_screen_1_filter`, `read_screen_1_metrics`, `navigate`, `_report_ready_locator`, or
  `verify_freshness`.
- Do not add a `title` branch to `section_anchor_visible`.
- Hebrew titles, slicer placeholders, chart titles, and column headers live in
  `pages/hosen_status/page.py` or in the YAML. They do not move into `core/`.
- `_mark_visual_host` stays as it is. It marks `vcGroupBody` (width at least 200, height at
  least 120) and does not mark the 38px `visualHeaderAbove` header. Screen 2's trends read
  uses that climb.
- Numbers, `null`, and the golden titles live only in the YAML. The page and the tests do not
  embed `01/01/2026`, `85%`, `75.0%`, or an authority percent. The tests pass `expected["title"]`
  and iterate `filters`. They skip a `null` value instead of calling the selector.
- No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`.
- New Python identifiers and comments inside functions stay English.
- The default settle on `_select_smart_filter` and `_select_date_combobox` stays
  `_screen_1_settle`.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/hosen_status/page.py` | EDIT | Open Screens 3 and 4, select their dates and filters, read charts and the export grid |
| `core/components/virtual_grid.py` | EDIT | Keep walking while `scrollTop` can still increase |
| `tests/sanity/hosen_status_dashboard/test_screen3_sanity.py` | NEW | `test_hosen_screen3_matches_golden` and private compare helpers |
| `tests/sanity/hosen_status_dashboard/test_screen4_sanity.py` | NEW | `test_hosen_screen4_matches_golden` and private compare helpers |
| `tests/sanity/hosen_status_dashboard/conftest.py` | UNCHANGED | Existing `hosen_status_dashboard` fixture |
| `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` | UNCHANGED | Screen 1 behavior stays |
| `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` | UNCHANGED | Screen 2 behavior stays |
| `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` | UNCHANGED | `verify_freshness()` smoke |
| `data/hosen/db_sanity.yaml` | UNCHANGED | Screen 3 and Screen 4 blocks are already the source of truth |
| `docs/COVERAGE_CATALOG.md` | EDIT | Screen 3 and Screen 4 YAML keys, page methods, and test names. Screen 1 and Screen 2 rows stay |
| `core/portal` | NONE | Login, catalog, iframe, and freshness stay |
| `core/components/visual_table.py` | NONE | Chart menu stays |
| hasbara / credit / alerts | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `HosenStatusPage` already subclasses `ReportShell`. Login,
  catalog search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0.
  `navigate()` still lands on Screen 1. This slice adds page-navigation clicks on the domain
  page. It does not copy portal steps.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Geographic and export titles, the
  page-rail labels, chart titles, the level and sector placeholders, and the export column
  headers stay on `pages/hosen_status/page.py` and in `data/hosen/db_sanity.yaml`. The
  `virtual_grid.py` edit evaluates `scrollTop` only. It does not learn a date, an authority,
  or a Hebrew header. Root `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS, with the fleet gate this
  principle requires. Screen 3 and Screen 4 methods are additive. Screen 1 and Screen 2 public
  methods keep their contracts. The Screen 1 and Screen 2 sanity tests are the regression gate
  for this page. `core/components/virtual_grid.py` is Layer 2, so
  `pytest tests/ui/fleet_dashboard/` must pass at 100% before this slice is done. The Hosen
  smoke module is not edited and still calls `verify_freshness()`.
- **Page object discipline (IV)**: PASS. The sanity tests call `open_geographic_screen`,
  `select_screen_3_date_range`, `select_screen_3_filter`, `wait_for_screen_3_idle`,
  `read_screen_3_metrics`, and the Screen 4 twins. Locators stay on `HosenStatusPage`. The
  test body does not locate a dropdown, a page tab, or a chart.
- **Warehouse as source of truth (V)**: PASS for this slice. The user scoped the work to the
  existing golden YAML, which this repository already uses for Hosen Screens 1 and 2. No
  business SQL is added to Layer 0 or to a new client. Screen 4's golden block is the on-screen
  grid. A downloaded workbook is not a source of truth in that file.
- **Observability (VI)**: PASS. The new tests are normal pytest sanity tests. Existing CSV,
  screenshot, and trace hooks on the shared session stay in place. This slice does not remove them.
- **Extract shared behavior only (VII)**: PASS. The page composes the existing date path, the
  existing smart-filter path, `collect_virtualized_rows`, and `VisualTable`. The scroll change
  is a stop rule inside the reader the charts and the export grid already need. It is not a new
  public function. Header maps, titles, and the `null`-means-empty rule stay on the domain page
  and in the new tests. `rows_to_label_values` is not used.

## Project Structure

### Documentation (this feature)

```text
specs/052-hosen-screen34-sanity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hosen-screen34-sanity.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pages/hosen_status/page.py                         # HosenStatusPage + Screen 3 and Screen 4 readers
data/hosen/db_sanity.yaml                          # screen_3 and screen_4 blocks (unchanged)
tests/sanity/hosen_status_dashboard/               # existing fixture + two new tests
tests/ui/hosen_status_dashboard/                   # existing smoke, unchanged
tests/ui/fleet_dashboard/                          # fleet smoke gate for the virtual-grid edit
core/components/virtual_grid.py                    # scrollTop stop only
core/components/visual_table.py                    # used, not edited
core/components/slicer.py                          # used by the existing date path, not edited
```

**Structure Decision**: Validation Core layout. Domain behavior stays on
`pages/hosen_status/page.py`. The golden file stays under `data/hosen/`. The sanity modules
stay under `tests/sanity/hosen_status_dashboard/`. Layer 2 is called. The one Layer 2 edit is
the scroll stop in `collect_virtualized_rows`.

## Phase 0 — Research

Unknowns from the technical context are resolved in [research.md](./research.md). None remain
marked NEEDS CLARIFICATION.

Decisions locked there:

- Spec directory `052-hosen-screen34-sanity` on the current git checkout. `050` and `051` are
  not overwritten.
- Screen 3 and Screen 4 are opened by new page methods. `_report_ready_locator()` stays the
  Screen 1 text. `open_investigation_screen` is not edited.
- Date clicks are the existing `_select_date_combobox`. Screen 3 calls it twice (start, then
  end). Screen 4 calls it once. Smart-filter clicks are the existing `_select_smart_filter`.
  The default settle stays `_screen_1_settle`.
- A YAML `null` filter is not applied. The read-back is an empty string.
- Idle is a visible spinner expected hidden, then that screen's title.
- Charts use `VisualTable.read_rows` on the host `_mark_visual_host` already marks
  (`vcGroupBody`). The right-click does not land on `visualHeaderAbove`. The helper is not
  rewritten, because Screen 2 depends on it.
- The export grid uses `collect_virtualized_rows` directly. It is already a table.
- `collect_virtualized_rows` continues while an evaluated `scrollTop` still increases. A
  viewport with no new row id is not, by itself, the end of the table. No second scroller is
  added on the page. `VisualTable` is not edited.
- `screen_3_section_visible` and `screen_4_section_visible` are separate from
  `section_anchor_visible` and from `screen_2_section_visible`.
- Compare helpers are private to each new test file.
- Screen 4 does not download a file.

## Phase 1 — Design

- Data shapes: [data-model.md](./data-model.md)
- Page and test contract: [contracts/hosen-screen34-sanity.md](./contracts/hosen-screen34-sanity.md)
- How to run the slice: [quickstart.md](./quickstart.md)
- Agent context: `.cursor/rules/specify-rules.mdc` points at this plan.

### Open a screen

`navigate()` is unchanged. Each new test then calls one opener with the golden title:

```python
page.open_geographic_screen(str(expected["title"]))
page.open_excel_export_screen(str(expected["title"]))
```

The click path is the one `open_investigation_screen` already uses: candidate labels are the
full title and the segment after the last ` - `; `"` and `״` match; the first visible
`button`, `tab`, `link`, or `option` inside `ניווט בין עמודים` / `Page navigation` is clicked.
`open_investigation_screen` is left as it is, including its Screen 2 settle. The new methods
store their own title and run their own settle.

### Screen 3 filters

```python
date_range = expected.get("date_range") or {}
page.select_screen_3_date_range(str(date_range["start"]), str(date_range["end"]))
filters = expected.get("filters") or {}
for slicer_id, value in filters.items():
    if value is None:
        continue
    page.select_screen_3_filter(str(slicer_id), str(value))
page.wait_for_screen_3_idle()
actual = page.read_screen_3_metrics()
```

`start` is applied before `end`. Both go through `_select_date_combobox` with
`settle=self._screen_3_settle`. When the screen shows two date comboboxes, visual order (top,
then left) is start, then end. The Hebrew accessible names are page constants copied from the
live control. `select_screen_2_filter("date", ...)` is not used here: it settles on the
Screen 2 title.

`level_selected`, `district`, `subdistrict`, and `authority` go through `_select_smart_filter`
with the same Screen 3 settle. Their placeholder hints live in a Screen 3 tuple. They are not
inserted into `_FILTER_ROLES`, so `_smart_filter_label` still treats the first chip as district
and the next as subdistrict for Screens 1 and 2. `level_selected` is `מחוז` and must not be
typed into the district box that holds `מחוז דרום`. `authority: null` is skipped in the test.
The read-back of that id is `""`.

### Screen 4 filters

```python
report_date = expected.get("date")
if report_date:
    page.select_screen_4_filter("date", str(report_date))
filters = expected.get("filters") or {}
for slicer_id, value in filters.items():
    if value is None:
        continue
    page.select_screen_4_filter(str(slicer_id), str(value))
page.wait_for_screen_4_idle()
actual = page.read_screen_4_metrics()
```

`date` uses `_select_date_combobox` with `_screen_4_settle`. `sector` and `authority` are
`null` in the golden file, so the loop does not call the selector for them. `district` and
`subdistrict` use `_select_smart_filter`. The Screen 4 placeholder tuple is separate from
`_FILTER_ROLES`.

`_select_smart_filter` and `_select_date_combobox` already take an optional settle. The default
stays `_screen_1_settle`. This slice does not change that default and does not edit
`core/components/slicer.py`.

`_screen_3_settle` and `_screen_4_settle` call the existing `_hide_visible_spinner`, then expect
that screen's title. A spinner that is not showing is not a failure. The helper returns without
sleeping.

### `read_screen_3_metrics`

Returns one dict after `wait_for_screen_3_idle()`:

```text
{
  "title": "<visible heading>",
  "date_range": {"start": "<start label>", "end": "<end label>"},
  "filters": {
    "level_selected": "<chip or ''>",
    "district": "<chip or ''>",
    "subdistrict": "<chip or ''>",
    "authority": ""
  },
  "graphs": {
    "final_resilience_score": {
      "title": "<chart title>",
      "legend": "<legend inside that chart>",
      "data": [{"date": "18/03/2026", "score": "85%"}]
    },
    "categories": [
      {"title": "<category title>", "data": [{"date": "25/03/2026", "score": "87%"}]}
    ]
  }
}
```

The page discovers chart titles that are visible in the report iframe. It does not embed the
eight category strings. The test subsets by the golden `title`. For each chart it reads:

1. Locate the visible title text.
2. `_mark_visual_host(node, attr)` — existing climb to `vcGroupBody`. Do not change this
   helper. Do not pass the title node or a `visualHeaderAbove` node to `VisualTable`.
3. Read the legend from that host's text before opening the menu. For the final-score chart
   the published `legend` is that string. Category charts have no legend field in the YAML;
   the page does not invent one.
4. `VisualTable(self.page, self._report_frame(), timeout_ms=self.timeout).read_rows(host, name=...)`.
5. Clear the mark in a `finally`, including when `read_rows` raises.
6. Map rows on the page. The `DD/MM/YYYY` cell becomes `date`. The percent cell becomes
   `score` through the existing `_percent_token`, which keeps a decimal (`85%`, `75.0%`).
   A cell with no visible value becomes `""`. `rows_to_label_values` is not called.

`read_rows` right-clicks the center of the marked host, clicks `הצג כטבלה`, collects with
`collect_virtualized_rows`, and returns to the report before the next chart. The page does not
reimplement that menu.

### `read_screen_4_metrics`

Returns `title`, `date`, `filters`, and `data_table`. `data_table` is a list of authority rows
from `collect_virtualized_rows` on the grid whose header contains `רשות`. The page does not
call `VisualTable` for this grid. `authority` is `_plain(text.split("\n")[0])`, then quote-folded
only in the test. Metric cells use `_percent_token`, so `75.0%` stays `75.0%`.

Column identity is a Screen 4 header tuple on the page, not `_SCREEN2_HEADERS`. Screen 2's
`_field_for_header` is not retargeted. The live header spelling is copied into the page
constant. The planned English keys are the golden keys: `care_for_welfare`,
`effective_behavior`, `information_and_communication`, `community_resources`, `leadership`,
`narrative`, `final_score`, `functional_continuity`, `belonging_and_solidarity`.

### Scroll

`VisualTable._collect_rows` calls `collect_virtualized_rows` and then `_leave_table` runs
before the page sees the rows. A second scroll on the page cannot reach dates that the generic
reader already skipped. The continuation therefore stays inside `collect_virtualized_rows`:

- The public signature stays `(grid, read_visible, row_id, *, timeout_ms)`.
- The walk still starts at `scrollTop = 0`.
- Each step still assigns `scrollTop` by about one client height and reads the value back.
- If that evaluation did not change `scrollTop`, the step tries the other overflow nodes in
  the same family, the way the horizontal sweep already tries more than one node.
- If no node's `scrollTop` changed, the walk ends.
- If `scrollTop` increased, the walk stores the painted rows and continues even when every id
  was already stored.
- The walk also ends when `timeout_ms` elapses.
- Deduping by `row_id` stays. A later viewport may still fill a blank cell on a stored row.
- No Hosen date, authority, or Hebrew string is added.

Screen 1, Screen 2, Screen 4, and every fleet caller keep calling this function. A more
complete grid is the intended result. Fleet smoke is the proof those callers still pass.

### Anchors and the tests

`screen_3_section_visible` and `screen_4_section_visible` are the skip/fail switches.
`section_anchor_visible` and `screen_2_section_visible` are not given new branches.

Screen 3 blocks: `title`, `date_range`, `filters`, `graphs.final_resilience_score`,
`graphs.categories`. Screen 4 blocks: `title`, `date`, `filters`, `data_table`. A missing
anchor skips that block. A visible anchor with an empty reader fails when the golden node has
data. A chart reader is not called when its title is absent. If every block on that screen is
skipped, `pytest.skip`.

Private compare rules, copied into each new test file and not imported across files:

- Failure prefix: `hosen_dashboard.screen_3_geographic_investigation` or
  `hosen_dashboard.screen_4_excel_export`.
- Strings, including percents, match after bidi marks and outer whitespace are removed.
  `75.0%` does not match `75%`.
- Title matching treats `"` and `״` as the same character. Authority matching does too, so
  `בני עי"ש` matches the gershayim spelling.
- YAML `null` matches `""`. It does not match `0%`.
- Chart identity is `date` inside `data`. Category identity is `title`. Export identity is
  `authority`. Extra rows, extra dates, and extra charts are ignored.
- The tests are marked `sanity`. They do not import `test_screen1_sanity`,
  `test_screen2_sanity`, Hasbara, Credit, or Alerts.

### Coverage catalog

Section 11 of `docs/COVERAGE_CATALOG.md` keeps the Screen 1 and Screen 2 tables and gains rows
for `screen_3_geographic_investigation` (`title`, `date_range`, `filters`,
`graphs.final_resilience_score`, `graphs.categories`) and `screen_4_excel_export` (`title`,
`date`, `filters`, `data_table`), naming the new page methods and
`test_hosen_screen3_matches_golden` / `test_hosen_screen4_matches_golden`. The source line
stays the YAML file, not SQL.

### Golden file

`data/hosen/db_sanity.yaml` already holds both blocks. This slice does not edit that file and
does not invent a replacement snapshot. The page and the tests do not embed the dates, the
percents, or the `null`s.

## Constitution Check (post-design)

Re-checked after data-model.md and the contract. The design still passes.

- `core/portal` is not edited. Screen 3 and Screen 4 reuse the date combobox path,
  `_select_smart_filter`, `collect_virtualized_rows`, and `VisualTable.read_rows` (I, II, VII).
- The one Layer 2 edit is the `scrollTop` stop in `collect_virtualized_rows`. It names no
  report. Fleet smoke is required because Layer 2 changed (II, III, VII).
- The optional settle defaults to `_screen_1_settle`. `select_screen_1_filter` and
  `select_screen_2_filter` are not given a new argument. `_report_ready_locator()` stays the
  Screen 1 text (III, IV).
- `open_investigation_screen`, `read_screen_2_metrics`, and `_mark_visual_host` stay as they
  are. The graph body Screen 3 right-clicks is the host Screen 2 already marks (III, IV).
- The tests call page methods and do not locate controls (IV).
- No new shared compare module. The `null` rule lives only in the new tests, so Screen 1 and
  Screen 2 helpers stay as they are (III, VII).
- No SQL in Layer 0. The existing sanity YAML is the source of truth named by the spec (V).
  Screen 4 does not download a workbook.
- Smoke `verify_freshness` is unchanged (III, IV).
- `networkidle` stays rejected. The idle signal is the spinner plus that screen's title.
- Header names and chart titles stay on the page. They are not added to `visual_table.py` or
  `virtual_grid.py` (II, VII).
- `_FILTER_ROLES` and `_smart_filter_label` stay on the Screen 1 / Screen 2 chip index. Screen 3
  and Screen 4 keep their own placeholder tuples (III).

## Complexity Tracking

The Layer 2 scroll edit is the complexity this constitution asks to justify. It is not a failed
gate. The principles still pass because the edit stays report-agnostic and fleet smoke is the
contract for Layer 2.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `collect_virtualized_rows` keeps walking while `scrollTop` still increases | A golden `date` or `authority` can sit below the first viewport. `VisualTable.read_rows` collects and then leaves the table before the page sees the rows, so the page cannot scroll afterward. | A second scroll loop on the page would copy the reader the user said to reuse. Stopping when one viewport adds no new id drops later dates even though `scrollTop` can still move. Leaving the stop as it is fails the geographic charts for that reason. |
