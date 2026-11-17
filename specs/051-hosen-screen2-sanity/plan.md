# Implementation Plan: Hosen Status Screen 2 YAML Sanity

**Branch**: `feature/reportportal-integration` (spec directory `051-hosen-screen2-sanity`) | **Date**: 2026-11-16 (host revision 2026-11-17) | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/051-hosen-screen2-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Spec documents under `specs/050-hosen-screen1-sanity/` are not edited.

## Summary

Add a Screen 2 reader on the existing Hosen Status page and a golden-YAML sanity test for the
investigation screen of תמ"צ חוסן.

`HosenStatusPage.navigate()` still opens the report on Screen 1 and still waits for
`תמ"צ ארצי - דיווחי קה"א יקל"ר`. This slice adds a method that opens the investigation screen
whose title is `hosen_dashboard.screen_2_investigation.title`, applies that block's `date` and
`filters`, and compares the reading to the existing YAML. The golden file is not edited. There
is no SQL client and no new comparison engine. Screen 1's test behavior stays.

1. **Open** — `open_investigation_screen(title)` clicks the page-navigation control for the
   golden title, then waits until a visible spinner is hidden and that title is visible.
2. **Date** — `select_screen_2_filter("date", value)` uses the existing `_select_date_combobox`
   path. The settle callable is the Screen 2 anchor. `select_screen_1_filter` still settles on
   Screen 1.
3. **Filters** — each `filters` entry, in YAML order, uses the existing `_select_smart_filter`
   path with the same Screen 2 settle. The test body does not hold locators.
4. **Authority table** — `collect_virtualized_rows` on the bottom grid. Match each golden
   `authority`. Extra UI rows are ignored. Percent fields stay display text.
5. **Totals** — the summary/average row of that grid, same metric fields, no authority name.
6. **Trends** — the chart is read with the existing `VisualTable.read_rows` (right-click, then
   `הצג כטבלה`). The right-click target is the nearest `visualContainer` ancestor of the title
   `מגמות המרכיבים לפי תאריך`, not the title strip. Match each golden `creation_date`. A YAML
   `null` is an empty cell. Extra dates are ignored.
7. **Compare** — private helpers in `test_screen2_sanity.py`. A visible anchor plus an empty
   reader fails. A missing anchor skips that block. If every block is skipped, `pytest.skip`.
   Failure messages name the YAML path.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through the existing
`hosen_status_dashboard` fixture. Layer 2 `Slicer` (already used by the date path),
`collect_virtualized_rows`, and `VisualTable`. No new package.

**Storage**: Existing golden record `data/hosen/db_sanity.yaml`
(`hosen_dashboard.screen_2_investigation`). This slice does not edit it. No warehouse query
and no `db/clients/hosen.py`.

**Testing**: `pytest tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`. Screen 1 must
still pass: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`. The freshness
smoke module is not edited. Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page
are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal validation framework. Domain page `pages/hosen_status/page.py`.
Golden YAML `data/hosen/db_sanity.yaml`. Sanity test
`tests/sanity/hosen_status_dashboard/test_screen2_sanity.py`.

**Performance Goals**: N/A. One catalog open, one page switch, and one Screen 2 read per test.

**Constraints**:

- Do not edit `core/portal` or `core/components`. The date combobox path, the smart-filter path,
  `collect_virtualized_rows`, and `VisualTable.read_rows` already cover this screen.
- Do not edit `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, or
  those reports' pages and tests.
- Do not import Hasbara, Credit, or Alerts page modules or their tests.
- Do not add `tests/helpers/` comparison code. The subset walk stays private in the Screen 2 test.
- Do not change `test_screen1_sanity.py` behavior. Do not change
  `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` (`dashboard.verify_freshness()`).
- Hebrew titles, slicer role names, and column headers live in `pages/hosen_status/page.py` or
  in the YAML. They do not move into `core/`.
- `_mark_visual_host` stays on the domain page. It marks the nearest `visualContainer`. It does
  not stop on `visualTitle`, and it does not change `VisualTable`.
- Numbers, `null`, and the golden title live only in the YAML. The page and the test do not
  embed `08/06/2026`, `88%`, or an authority percent. The test passes `expected["title"]` and
  iterates `filters`. It does not name `district` or `subdistrict`.
- No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`.
- `_report_ready_locator()`, `navigate()`, and `verify_freshness()` stay as they are.
- New Python identifiers and comments inside functions stay English.
- `select_screen_1_filter` keeps settling on Screen 1. The new settle argument on the private
  helpers defaults to `_screen_1_settle`.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/hosen_status/page.py` | EDIT | Open Screen 2, select its date and filters, read the three table blocks |
| `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` | NEW | `test_hosen_screen2_matches_golden` and private compare helpers |
| `tests/sanity/hosen_status_dashboard/conftest.py` | UNCHANGED | Existing `hosen_status_dashboard` fixture |
| `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` | UNCHANGED | Screen 1 behavior stays |
| `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` | UNCHANGED | `verify_freshness()` smoke |
| `data/hosen/db_sanity.yaml` | UNCHANGED | `screen_2_investigation` is already the source of truth |
| `docs/COVERAGE_CATALOG.md` | EDIT | Screen 2 YAML keys, page methods, and test name. Screen 1 rows stay |
| `core/` | NONE | Existing readers are sufficient |
| hasbara / credit / alerts | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `HosenStatusPage` already subclasses `ReportShell`. Login,
  catalog search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0.
  `navigate()` still lands on Screen 1. This slice adds a page-navigation click on the domain
  page. It does not copy portal steps.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The investigation title, the page-rail
  labels, the column headers, and the summary-row tokens stay on `pages/hosen_status/page.py`
  and in `data/hosen/db_sanity.yaml`. `core/` is not edited. Root `conftest.py` does not import
  the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Screen 2 methods are
  additive. `select_screen_1_filter`, `read_screen_1_metrics`, `navigate`, and
  `verify_freshness` keep their contracts. The Screen 1 sanity test is the regression gate for
  this page. Fleet smoke is not the gate because Layer 0, Layer 2, and the fleet page are not
  edited. The Hosen smoke module is not edited and still calls `verify_freshness()`.
- **Page object discipline (IV)**: PASS. The sanity test calls `open_investigation_screen`,
  `select_screen_2_filter`, `wait_for_screen_2_idle`, and `read_screen_2_metrics`. Locators stay
  on `HosenStatusPage`. The test body does not locate a dropdown, a page tab, or a chart.
- **Warehouse as source of truth (V)**: PASS for this slice. The user scoped the work to the
  existing golden YAML, which this repository already uses for Hosen Screen 1, Hasbara, and
  Credit. No business SQL is added to Layer 0 or to a new client. A later warehouse slice would
  use a real client; that work is out of scope here.
- **Observability (VI)**: PASS. The new test is a normal pytest sanity test. Existing CSV,
  screenshot, and trace hooks on the shared session stay in place. This slice does not remove them.
- **Extract shared behavior only (VII)**: PASS. The page composes the existing date path, the
  existing smart-filter path, `collect_virtualized_rows`, and `VisualTable`. Header maps, the
  investigation title, and the `null`-means-empty rule stay on the domain page and in the
  Screen 2 test. No new generic API is added. `rows_to_label_values` is not used because it
  collapses a row to one integer and drops percent-only cells.

## Project Structure

### Documentation (this feature)

```text
specs/051-hosen-screen2-sanity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hosen-screen2-sanity.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pages/hosen_status/page.py                         # HosenStatusPage + Screen 2 readers
data/hosen/db_sanity.yaml                          # hosen_dashboard.screen_2_investigation (unchanged)
tests/sanity/hosen_status_dashboard/               # existing fixture + new Screen 2 test
tests/ui/hosen_status_dashboard/                   # existing smoke, unchanged
core/components/visual_table.py                    # used, not edited
core/components/virtual_grid.py                    # used, not edited
core/components/slicer.py                          # used by the existing date path, not edited
```

**Structure Decision**: Validation Core layout. Domain behavior stays on
`pages/hosen_status/page.py`. The golden file stays under `data/hosen/`. The sanity module
stays under `tests/sanity/hosen_status_dashboard/`. Layer 2 is called and not modified.

## Phase 0 — Research

Unknowns from the technical context are resolved in [research.md](./research.md). None remain
marked NEEDS CLARIFICATION.

Decisions locked there:

- Spec directory `051-hosen-screen2-sanity` on the current git checkout. `050` is not overwritten.
- Screen 2 is opened by a new page method. `_report_ready_locator()` stays the Screen 1 text.
- Date and smart-filter clicks are the existing helpers. An optional settle defaults to
  `_screen_1_settle`. Screen 2 passes `_screen_2_settle`.
- Idle is a visible spinner expected hidden, then the investigation title.
- The authority grid uses `collect_virtualized_rows` and the Screen 1 Hebrew header vocabulary.
- The totals row is the summary row of that grid.
- The trends chart uses `VisualTable.read_rows`. The container is the nearest `visualContainer`
  ancestor of the title, not the first node whose class contains `visual`. A blank cell is
  `""`. YAML `null` matches that empty cell in the test.
- `screen_2_section_visible` is separate from `section_anchor_visible`, so Screen 1's skip of
  an unknown key stays.
- Compare helpers are private to `test_screen2_sanity.py`.

## Phase 1 — Design

- Data shapes: [data-model.md](./data-model.md)
- Page and test contract: [contracts/hosen-screen2-sanity.md](./contracts/hosen-screen2-sanity.md)
- How to run the slice: [quickstart.md](./quickstart.md)
- Agent context: `.cursor/rules/specify-rules.mdc` points at this plan.

### Open the investigation screen

`navigate()` is unchanged. The fixture therefore still lands on Screen 1. The test then calls:

```python
page.open_investigation_screen(str(expected["title"]))
```

`title` is the YAML string `תמ״צ התנהגות - מסך תחקור`. The page also tries the segment after
the last ` - `, and it treats `"` and `״` as the same character, because Screen 1's ready
locator uses an ASCII quote while the YAML uses gershayim. The YAML is not rewritten.

The click target is a visible `button`, `tab`, `link`, or `option` inside the report iframe,
preferring the page-navigation group `ניווט בין עמודים` / `Page navigation`. After the click
the full title is expected visible, and `_screen_2_settle` runs.

### Filters

```python
report_date = expected.get("date")
if report_date:
    page.select_screen_2_filter("date", str(report_date))
filters = expected.get("filters") or {}
for slicer_id, value in filters.items():
    page.select_screen_2_filter(str(slicer_id), str(value))
page.wait_for_screen_2_idle()
actual = page.read_screen_2_metrics()
```

`date` is a sibling of `filters`, not a key inside the map. Apply order for the map is YAML
order (`district`, then `subdistrict`). The page does not reorder the map.

Settle threading, so Screen 1 stays on its current hook:

```python
def _select_smart_filter(self, role_names, value, settle=None) -> bool:
    hook = settle or self._screen_1_settle
    ...
    hook("after_select")

def _select_date_combobox(self, control, value, settle=None) -> None:
    hook = settle or self._screen_1_settle
    ...
    self._select_slicer_date(listbox_frame, value, settle=hook)
    ...
    hook("after_select")
```

`select_screen_1_filter` calls these without `settle`. `select_screen_2_filter` passes
`settle=self._screen_2_settle`. `_select_slicer_date` forwards that callable into `Slicer`.
`core/components/slicer.py` is not edited.

`_screen_2_settle` hides a visible spinner with the same locator Screen 1 already uses, then
expects the investigation title. A spinner that is not showing is not a failure. The helper
returns without sleeping.

### `read_screen_2_metrics`

Returns one dict after `wait_for_screen_2_idle()`:

```text
{
  "title": "<visible heading>",
  "date": "<selected combobox label>",
  "filters": {"district": "...", "subdistrict": "..."},
  "tables": {
    "authorities_breakdown_table": [{"authority": "...", "leadership": "67%", "...": "100%"}],
    "totals_row": {"leadership": "88%", "...": "83%"},
    "trends_by_date_table": [{"creation_date": "13/06/2025", "functional_continuity": ""}]
  }
}
```

`date` and `filters` reuse `_read_screen_1_date` and `_read_active_filters`. Those readers
already return the selected label. They do not click.

Authority rows: the grid whose column header contains `רשות`, collected with
`collect_virtualized_rows`. `authority` is `_plain(extracted_text.split("\n")[0])`. Metric
columns map by the Hebrew headers listed in research.md. The page publishes a compact percent
(`88%`). The summary row is excluded from this list.

Totals: that summary row's nine metric fields. The label cell is a summary token (`ממוצע`,
`ממוצע ארצי`, `סה"כ`, `סה״כ`, or `Total`). If the live grid has no such row, the page reads
the sibling visual of those nine percents and stores that visual's live title as a page
constant. The published object still has no `authority` key.

Trends: `VisualTable(self.page, self._report_frame(), timeout_ms=self.timeout).read_rows(container, name="trends_by_date")`.
The title constant is `מגמות המרכיבים לפי תאריך`. `container` is the locator
`_mark_visual_host` returns for that title. The page maps rows. The `DD/MM/YYYY` cell becomes
`creation_date`. A cell with no visible value becomes `""`. `rows_to_label_values` is not
called. The page does not reimplement the right-click menu.

`_mark_visual_host` today walks parents in JavaScript and stops at the first class that
contains `visual`. That node is the title strip (`visualTitle`). `VisualTable.read_rows`
right-clicks it, the title menu has no `הצג כטבלה` / `Show as a table` item, and the reader
raises `AssertionError: 'trends_by_date' has no show-as-table menu item`.

The replacement climbs with the same ancestor working screens already use
(`pages/fleet_dashboard/main_dashboard_page.py`, `core/components/chart.py`). Playwright only
treats the string as XPath when it starts with `xpath=`. A bare `ancestor::` string is not a
CSS selector. `contains(@class, 'visualContainer')` does not match `visualTitle`. `[1]` on the
ancestor axis is the nearest match, so an inner `visualContainer` wins over an outer
`visualContainerHost` (the host class also contains that substring). There is no fallback that
marks the title node.

```python
def _mark_visual_host(self, node: Locator, attr: str) -> Locator | None:
    """Mark the visual that wraps the title and the chart body.

    The first ancestor whose class contains ``visual`` is ``visualTitle``.
    Right-clicking that strip opens a menu with no "Show as a table" item.
    """
    frame = self._report_frame()
    host = node.locator(
        "xpath=ancestor::div[contains(@class, 'visualContainer')][1]"
    )
    try:
        if host.count() == 0:
            return None
        host.first.evaluate(
            "(el, attr) => el.setAttribute(attr, 'active')",
            attr,
        )
    except Exception:
        return None
    marked_node = frame.locator(f"[{attr}='active']")
    try:
        if marked_node.count() == 0:
            return None
    except Exception:
        return None
    return marked_node.first
```

`_read_totals_sibling` uses the same helper. Its `inner_text` is then the visual that owns the
summary label, which still contains the nine percent headers. `_clear_mark` is unchanged.

### Anchors and the test

`screen_2_section_visible` is the skip/fail switch. `section_anchor_visible` is not given a
`title` branch, because `test_hosen_screen1_matches_golden` iterates every Screen 1 key and
today skips keys the method does not know.

Blocks: `title`, `date`, `filters`, `tables.authorities_breakdown_table`, `tables.totals_row`,
`tables.trends_by_date_table`. A missing anchor skips that block. A visible anchor with an
empty reader fails when the golden node has data. The trends reader is not called when its
anchor is missing. If all six are skipped, `pytest.skip`.

Private compare rules in `test_screen2_sanity.py`:

- Failure prefix: `hosen_dashboard.screen_2_investigation`.
- Strings, including percents, match after bidi marks and outer whitespace are removed.
- Title matching also treats `"` and `״` as the same character.
- YAML `null` matches `""`. It does not match `0%`.
- Authority identity is `authority`. Trend identity is `creation_date`. Extra rows and extra
  dates are ignored. Extra slicers are ignored.

The test is marked `sanity`. It does not import `test_screen1_sanity`, Hasbara, Credit, or Alerts.

### Coverage catalog

Section 11 of `docs/COVERAGE_CATALOG.md` keeps the Screen 1 table and gains rows for
`screen_2_investigation.title`, `date`, `filters`, `tables.authorities_breakdown_table`,
`tables.totals_row`, and `tables.trends_by_date_table`, naming `open_investigation_screen`,
`select_screen_2_filter`, `read_screen_2_metrics`, and `test_hosen_screen2_matches_golden`.
The source line stays the YAML file, not SQL.

### Golden file

`data/hosen/db_sanity.yaml` already holds `hosen_dashboard.screen_2_investigation`. This slice
does not edit that file and does not invent a replacement snapshot. The page and the test do
not embed the date, the percents, or the `null`.

## Constitution Check (post-design)

Re-checked after data-model.md and the contract. The design still passes.

- No `core/` edit. Screen 2 reuses the date combobox path, the smart-filter path,
  `collect_virtualized_rows`, and `VisualTable.read_rows` (I, II, VII).
- The optional settle defaults to `_screen_1_settle`. `select_screen_1_filter` is not given a
  new argument. `_report_ready_locator()` stays the Screen 1 text (III, IV).
- The test calls page methods and does not locate controls (IV).
- No new shared compare module. The `null` rule lives only in the Screen 2 test, so Screen 1's
  helpers stay as they are (III, VII).
- No SQL in Layer 0. The existing sanity YAML is the source of truth named by the spec (V).
- Smoke `verify_freshness` is unchanged (III, IV).
- `networkidle` stays rejected. The idle signal is the spinner plus the investigation title.
- The authority first-line split is applied in the new Screen 2 row reader. It is not added to
  `collect_virtualized_rows`, and `_visible_resilience_rows` is not rewritten (II, VII).
- Header names and the trends visual title stay on the page. They are not added to
  `visual_table.py` (II, VII).
- The trends right-click target is fixed on `HosenStatusPage._mark_visual_host`. `VisualTable`
  and `Chart` are not edited. The ancestor string is the same `visualContainer` climb those
  working readers already use, copied onto the domain page (II, IV, VII).

## Complexity Tracking

No constitution violation needs a waiver. The settle argument is a defaulted parameter on
private helpers so the existing Screen 1 calls keep their hook. The date path's existing
"click the open option when the listbox is not named `SlicerDate`" behavior is reused and not
extended.
