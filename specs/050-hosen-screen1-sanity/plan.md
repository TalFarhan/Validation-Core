# Implementation Plan: Hosen Status Screen 1 YAML Sanity

**Branch**: `feature/reportportal-integration` (spec directory `050-hosen-screen1-sanity`) | **Date**: 2026-11-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/050-hosen-screen1-sanity/spec.md`

**Amendment (2026-11-16)**: Fix the Screen 1 date combobox in `pages/hosen_status/page.py`.
`district` and `subdistrict` stay on the smart-filter path. `data/hosen/db_sanity.yaml` and
`core/` stay unchanged. The golden date is the value the test already passes; the page does
not embed it.

**Amendment (2026-11-16, category grades)**: Category KPI grades are painted in
`<text class="value"><tspan>88%</tspan></text>`. `HosenStatusPage._read_card` reads that
node with Playwright `text_content()` (DOM `textContent`). It does not use `inner_text()`.
`kpis.categories` items are published as `title`, `score`, and `trend_direction`, matching
`data/hosen/db_sanity.yaml`. The national card stays `percentage` and `trend`. The YAML,
the sanity test, and `core/` stay unchanged.

**Amendment (2026-11-16, authority cell)**: `resilience_scores` rows are keyed by
`authority`. `_visible_resilience_rows` reads that cell with `inner_text()`, and Power BI
appends a hidden accessibility line, so the published key is
`קרית מלאכי\nעיצוב מותנה נוסף` while `data/hosen/db_sanity.yaml` has `קרית מלאכי`.
The page keeps the first line only: `extracted_text.split("\n")[0]` then the existing
`_plain` trim. `_assert_rows` is not the extractor and is not edited. The YAML and `core/`
stay unchanged.

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Spec documents under `specs/049-hasbara-ui-validation/` are not edited.

## Summary

Add a Screen 1 reader on the existing Hosen Status page and a golden-YAML sanity test for the
landing screen of תמ"צ חוסן.

`HosenStatusPage` already opens the report (`DASHBOARD_SEARCH_TERM = תמ"צ חוסן`), waits until
`תמ"צ ארצי - דיווחי קה"א יקל"ר` is visible, and overrides the freshness caption to `מועד רענון`.
This slice adds `read_screen_1_metrics()` and compares it to `data/hosen/db_sanity.yaml`
(`hosen_dashboard.screen_1_landing`). The smoke test stays a one-line `verify_freshness()` call.
There is no SQL client and no new comparison engine.

1. **Filters** — Before any metric read, the test loads `screen_1_landing.filters` and, for each
   id in YAML order, calls the page. The page resolves that id to its combobox and calls Layer 2
   `Slicer.select`. Hebrew role names stay on the page. After each selection, and once more
   before the read, a visible spinner is expected hidden and the Screen 1 ready locator is
   expected visible. The later reading of `filters` is a subset: every listed id matches; extra
   slicers are ignored. A missing or empty map applies nothing.
   The `בחירת נפה` search is the custom-card override inside `select_screen_1_filter` (the
   smart-filter input, not a named combobox). Its search-input click is
   `search_input.click(force=True)`. An unforced click times out because
   `ul.TokensContainer` intercepts pointer events. The `li` option click in that block already
   uses `force=True`. Comments inside the function stay English.
6. **Date** — `screen_1_landing.date` is applied with `select_screen_1_filter("date", value)`
   before the district and subdistrict smart filters. The page opens the combobox
   `_filter_control` already returned, once. It chooses `value` in that control's frame,
   including a nested iframe. `Slicer.select` runs only when the open listbox is named
   `SlicerDate`. Any other open list is an option click, with no second combobox click.
   After `_screen_1_settle`, the combobox text must contain `value` or the method raises.
   A visible date combobox makes `section_anchor_visible("date")` true, and
   `read_screen_1_metrics()` returns that selected label under `date`.
2. **KPIs** — Read `הערכת קה״א - ממוצע ארצי` and the category cards in that assessment through
   Layer 2 `KPI` for the card, then read the grade from `text.value` / `.value tspan` on that
   card with `text_content()`. The national card returns `title`, `percentage` (the display
   string, including `%`), and `trend`. Each category returns `title`, `score` (the same
   display string), and `trend_direction` (`up`, `down`, or `flat`) from a non-canvas arrow
   on that card.
3. **Resilience table** — Collect `ציון חוסן` with `collect_virtualized_rows`. The page callback
   returns `authority`, `score`, and `status` (`green` or `yellow`) from the row or cell
   background. `authority` is the first line of the cell's `inner_text()`, so a following
   accessibility line is not part of the row key. Extra authorities are ignored.
4. **Survey status** — Page locators read the top-left submitted count, total count, and missing
   authority names. Those locators stay on the page.
5. **Compare** — Private helpers in `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
   walk the golden block. YAML integers match grouped or plain digits. YAML strings match
   display text. A visible anchor plus an empty reader fails. A missing anchor skips that block.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `bind_dashboard`. Layer 2
`Slicer`, `KPI`, and `collect_virtualized_rows`. No new package.

**Storage**: New golden record `data/hosen/db_sanity.yaml`. No warehouse query and no
`db/clients/hosen.py` in this slice.

**Testing**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`. Hosen smoke
`pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` must still pass. Fleet smoke is
not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal validation framework. Domain page `pages/hosen_status/page.py`.
Golden YAML `data/hosen/db_sanity.yaml`. Sanity test `tests/sanity/hosen_status_dashboard/`.

**Performance Goals**: N/A. One catalog open and one landing-screen read per test.

**Constraints**:

- Do not edit `core/portal` or `core/components`. `Slicer.control`, `KPI.card` / `KPI.read_text`,
  and `collect_virtualized_rows` already cover this screen. A trend method and a selected-text
  method are conveniences, not missing universal readers (see research.md).
- Do not edit `data/hasbara/`, `data/credit/`, `data/alerts/`, or those reports' pages and tests.
- Do not import Hasbara, Credit, or Alerts page modules or their sanity helpers.
- Do not add `tests/helpers/` comparison code. The subset walk stays private in the Hosen test.
- Hebrew titles, slicer role names, and survey phrases live in `pages/hosen_status/page.py` or
  in the YAML. They do not move into `core/`.
- Numbers and filter labels live only in the YAML. The page and the test do not embed `7`,
  `12`, `55%`, `מחוז דרום`, or `נפת לכיש`. The test does not name `district` or `subdistrict`;
  it iterates whatever keys `filters` contains.
- No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`, no canvas
  bitmap sampling. Post-filter idle is a spinner-hidden check plus the ready locator.
- Inline comments inside functions stay English.
- The `בחירת נפה` search click is `search_input.click(force=True)` on `HosenStatusPage`.
  `force=True` stays on that page. It is not added to `Slicer` or to the test.
- `select_screen_1_filter("date", value)` does not call `page.wait_for_timeout`. A missed date
  option is not caught. After `_screen_1_settle`, combobox text that does not contain `value`
  raises.
- The date option is resolved from the control's frame and iframes nested in that frame.
  The page does not repeat the lookup with only `_report_frame()`.
- `data/hosen/db_sanity.yaml` is not edited by this amendment. The page and the test do not
  embed the golden date literal.
- Category grades are read on `HosenStatusPage` from `.value tspan` with `text_content()`.
  `inner_text()` is not used for that node. `core/components/kpi.py` is not edited.
  `kpis.categories` uses the golden keys `score` and `trend_direction`. The national card
  keeps `percentage` and `trend`. The sanity test is not edited.
- The resilience `authority` key is the first line of that cell's `inner_text()`, passed
  through `_plain`. The cleanup stays in `_visible_resilience_rows`. It is not added to
  `_plain`, to `_assert_rows`, or to `collect_virtualized_rows`. The score cell is unchanged.
  `data/hosen/db_sanity.yaml` is not edited to absorb the accessibility line.
- `navigate` and `verify_freshness` stay as they are. Root `conftest.py` does not import this page.
- Comments and new Python identifiers stay English. Hebrew is limited to locator constants and YAML values.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/hosen_status/page.py` | EDIT | Date combobox stays as already planned. Category grades: `.value tspan` via `text_content()` inside `_read_card`, published as `score` and `trend_direction`. National card stays `percentage` and `trend`. Resilience `authority` is the first line of the cell text. |
| `data/hosen/db_sanity.yaml` | UNCHANGED | `screen_1_landing.date` stays the golden value the test already passes |
| `tests/sanity/hosen_status_dashboard/__init__.py` | NEW | Package marker |
| `tests/sanity/hosen_status_dashboard/conftest.py` | NEW | `hosen_status_dashboard` fixture |
| `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` | UNCHANGED | `_assert_rows` already compares each golden field. It indexes `authority` after the page has published it. It does not strip cell lines. |
| `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` | UNCHANGED | `verify_freshness()` smoke |
| `tests/ui/hosen_status_dashboard/conftest.py` | UNCHANGED | Smoke fixture name stays `dashboard` |
| `docs/COVERAGE_CATALOG.md` | EDIT | Hosen YAML block ↔ reader ↔ test rows |
| `core/` | NONE | Existing readers are sufficient |
| hasbara / credit / alerts | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `HosenStatusPage` already subclasses `ReportShell`. Login, catalog
  search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0. The ready locator
  stays on the domain page. This slice does not add a tab switch.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Hebrew titles, slicer role names, the
  resilience title, and the survey phrases stay on `pages/hosen_status/page.py` and in
  `data/hosen/db_sanity.yaml`. `core/` is not edited. Root `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. `read_screen_1_metrics` is
  additive. Smoke `verify_freshness` stays. Fleet smoke is not the gate because Layer 0, Layer 2,
  and the fleet navigation surface are not edited. The Hosen smoke module is the navigation gate
  for this page and must stay green.
- **Page object discipline (IV)**: PASS. The sanity test iterates the YAML map and calls
  `select_screen_1_filter`. Combobox locators and `Slicer.select` stay on `HosenStatusPage`.
  The test body does not locate a dropdown.
- **Warehouse as source of truth (V)**: PASS for this slice. The user scoped the work to golden
  YAML, which this repository already keeps in `tests/sanity/` (Hasbara, Credit). No business SQL
  is added to Layer 0 or to a new client. A later warehouse slice would use an existing parity
  helper only after a real client exists; that work is out of scope here.
- **Observability (VI)**: PASS. The new test is a normal pytest sanity test. Existing CSV,
  screenshot, and trace hooks on the shared session stay in place. This slice does not remove them.
- **Extract shared behavior only (VII)**: PASS. The page composes `Slicer`, `KPI`, and
  `collect_virtualized_rows`. Trend classification, color-to-status mapping, survey text, and
  filter role names stay on the domain page. No new generic API is added. The `בחירת נפה`
  `search_input.click(force=True)` stays on `HosenStatusPage`. `Slicer` does not grow a force flag.
  `Slicer.select` is used for the date listbox only when that open listbox is named
  `SlicerDate`. A differently named open list is one option click on the page. See Complexity
  Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/050-hosen-screen1-sanity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── hosen-screen1-sanity.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pages/hosen_status/page.py                         # HosenStatusPage + Screen 1 readers
data/hosen/db_sanity.yaml                          # hosen_dashboard.screen_1_landing
tests/sanity/hosen_status_dashboard/               # fixture + subset compare
tests/ui/hosen_status_dashboard/                   # existing smoke, unchanged
core/components/slicer.py                          # used, not edited
core/components/kpi.py                             # used, not edited
core/components/virtual_grid.py                    # used, not edited
```

**Structure Decision**: Validation Core layout. Domain behavior stays on
`pages/hosen_status/page.py`. The golden file stays under `data/hosen/`. The sanity module
stays under `tests/sanity/hosen_status_dashboard/`. Layer 2 is called and not modified.

## Phase 0 — Research

Unknowns from the technical context are resolved in [research.md](./research.md). None remain
marked NEEDS CLARIFICATION.

Decisions locked there:

- Golden `filters` are applied with the existing `Slicer.select` before `read_screen_1_metrics()`.
  `Slicer` is not extended. The test does not locate dropdowns.
- Idle after a selection is a visible spinner expected hidden, then the Screen 1 ready locator.
  `networkidle` is not the signal.
- Percentage text comes from the card `KPI` already resolves. `KPI.read_text` is used when it
  still contains `%`. When the group path returns digits only, the page keeps the `%` token from
  that same card's text. `extract_kpi_value_text` is not changed.
- Trend and resilience color are page-level classifications of non-canvas DOM. Canvas sampling
  is a failure, not a fallback scraper.
- Golden literals are copied once from the live landing screen into the YAML during implementation.
- Subset comparison is private to the Hosen test module.
- The `בחירת נפה` search input is clicked with `force=True` inside the custom-card override
  that `select_screen_1_filter` already uses. `ul.TokensContainer` intercepts an unforced click.
  `Slicer` is not given a force flag.
- The date combobox is opened once on the locator `_filter_control` returned. The option is
  taken from that control's frame, including a nested iframe. `Slicer.select` runs only when
  the open listbox is named `SlicerDate`. The page does not edit `core/`. After
  `_screen_1_settle`, combobox text must contain the passed value. `section_anchor_visible("date")`
  follows visibility of that combobox. `read_screen_1_metrics()["date"]` is the selected label.
- Category grades come from `.value tspan` via `text_content()` on the card `KPI.card` already
  resolved. `inner_text()` is not used for that node. Categories are published as `score` and
  `trend_direction`. The national card stays `percentage` and `trend`. `KPI.read_text` and
  `extract_kpi_value_text` are not changed. See research.md section 16.
- Resilience `authority` is the first line of the authority cell. `_plain` still removes bidi
  marks. The accessibility line is not stored, and it is not written into the golden file.
  See research.md section 17.

## Phase 1 — Design

- Data shapes: [data-model.md](./data-model.md)
- Page and test contract: [contracts/hosen-screen1-sanity.md](./contracts/hosen-screen1-sanity.md)
- How to run the slice: [quickstart.md](./quickstart.md)
- Agent context: `.cursor/rules/specify-rules.mdc` points at this plan.

### `read_screen_1_metrics`

Returns one dict. Each section reader waits until its anchor is visible, bounded by
`self.timeout`, then reads. The method does not sleep and does not wait for network idle.

```text
{
  "survey_status": {"submitted": "<digits>", "total": "<digits>", "missing_authorities": ["..."]},
  "kpis": {
    "national_average": {"title": "...", "percentage": "83%", "trend": "up"},
    "categories": [{"title": "...", "score": "88%", "trend_direction": "up"}]
  },
  "resilience_scores": [{"authority": "...", "score": "<digits or text>", "status": "green"}],
  "filters": {"district": "מחוז דרום", "subdistrict": "נפת לכיש"},
  "date": "<selected combobox label>"
}
```

`date` is the label read from the date combobox after the golden value has been selected. It is
not a literal written in the page.

The test, not the page, coerces YAML integers. The page returns display text for counts, scores,
percentages, labels, and the trend/status words.

### Filters

`filters` in `data/hosen/db_sanity.yaml` is the map the test applies. The live keys are
`district` and `subdistrict`. The test does not hard-code those names.

```python
expected = load_sanity_data().get("screen_1_landing") or {}
report_date = expected.get("date")
if report_date:
    page.select_screen_1_filter("date", str(report_date))
filters = expected.get("filters", {})
for slicer_id, value in filters.items():
    page.select_screen_1_filter(str(slicer_id), str(value))
page.wait_for_screen_1_idle()
actual = page.read_screen_1_metrics()
```

The test already does this. This amendment does not hardcode the date and does not edit the test
or the YAML. `date` is a sibling of `filters`, not a key inside the filters map.

`select_screen_1_filter` lives on `HosenStatusPage`. It resolves the id through the page's
filter-role table (the same table `_read_active_filters` already uses; the `subdistrict` id
matches the YAML key). `district` and `subdistrict` stay on `_select_smart_filter`. The date
path is the Date combobox section below. An unknown id raises `KeyError`. An empty `filters`
map skips the filter loop. The date call still runs when `screen_1_landing.date` is present.

Apply order is YAML order. The golden file lists `district` before `subdistrict` so the child
dropdown is opened after its parent. The page does not reorder the map.

Settle, used as `Slicer`'s `after_select` hook and again from `wait_for_screen_1_idle`:

- In the report iframe, a visible node whose class contains `spinner`, or a visible
  `aria-busy="true"` node, is expected hidden within `self.timeout`. A count of zero is not a
  failure.
- The existing ready locator (`תמ"צ ארצי - דיווחי קה"א יקל"ר`) is expected visible within
  `self.timeout`.

The hook returns false so `Slicer.select` still confirms the label on the combobox and retries
once. No `sleep`, no `wait_for_timeout`, no `wait_for_load_state("networkidle")`.

### `בחירת נפה` search click

`subdistrict` role hints include `בחירת נפה`. That control is the custom-card (smart-filter)
override, not the combobox passed to `Slicer.select`. `select_screen_1_filter` reaches it
through `_select_smart_filter`.

Today that helper's input locator is named `field`. It clicks the ancestor
`ul.TokensContainer` and fills with `force=True`. The visible option is already
`choice.first.click(force=True)`. There is no line `search_input.click()`.

The failing step is the click on that search `<input>`. Playwright reports `TimeoutError`
because `<ul class="TokensContainer">` intercepts pointer events. The input click in this
block becomes:

```python
search_input.click(force=True)
```

`force=True` is the same bypass the `li` option click in this block already uses. The option
click stays forced. Comments inside the function stay English. The test body does not gain a
locator. `core/components/slicer.py` is not edited.

The reader publishes the same map as `filters` (selected label, role name and bidi marks
removed). `_assert_tree` then checks each golden label. Extra slicers are ignored. `section_anchor_visible("filters")`
is true when the report iframe has a combobox.

### Date combobox

`district` and `subdistrict` stay on `_select_smart_filter`. `date` does not.

Today `select_screen_1_filter("date", value)` gets the `SlicerDate` combobox from
`_filter_control`, clicks it, then `_choose_dropdown_option` clicks that same combobox again.
The second click closes the list. The `except Exception` around that helper swallows the miss,
`page.wait_for_timeout` pads the fallback, and the method returns after `_screen_1_settle`.
The test then skips `date` because `section_anchor_visible("date")` has no date branch and
returns false. Survey counts stay on the unselected date, so `survey_status.submitted` is `0`
where the golden file has `7`.

Replacement, still on `HosenStatusPage`:

1. Call `_filter_control` once. Keep that locator. Do not query `_report_frame()` again for a
   combobox named `SlicerDate`.
2. Click that locator once. Do not call `_choose_dropdown_option`. That helper clicks the
   combobox again. Remove every `page.wait_for_timeout` from `select_screen_1_filter`.
3. Resolve the open listbox and the option for `value` from the control's owner frame and from
   iframes nested in that frame. A search rooted only at `_report_frame()`, with child frames
   omitted, is the defect.
4. When the open listbox accessible name is `SlicerDate` and that same frame has the combobox
   `Slicer.select` will click, call `Slicer.select` with `frame` set to the listbox frame
   (a nested iframe when that is where the listbox was found), `role_name="SlicerDate"`,
   `kind="dropdown"`, and `settle=self._screen_1_settle`. Do not edit `core/`. Page code does
   not click the combobox again around that call. `Slicer.select` closes the classification
   popup and performs its own combobox click in the frame it was given.
5. Otherwise click the open option whose name is `value` in that same frame tree. Do not click
   the combobox again. Do not call `Slicer.select`.
6. Call `_screen_1_settle("after_select")`.
7. Read the same control's text. If the plain text does not contain `value`, raise
   `AssertionError`. Do not catch that raise, and do not catch a failure from step 4 or 5.

`section_anchor_visible("date")` is true when the date combobox from `_filter_control` is
visible. It does not search for a date literal.

`read_screen_1_metrics()` adds `date`: the selected label on that combobox, role name and bidi
marks removed, via the existing `_selected_label` path. The string is whatever the combobox
shows. The page does not contain the golden date. `_assert_tree` then matches
`screen_1_landing.date` once the anchor is true. The other four keys stay.

### KPIs

National title constant: `הערכת קה״א - ממוצע ארצי`. Implementation confirms the quote character
against the accessible name (`״` versus `"`) and stores the live spelling in the page constant
and in the YAML `title`.

`KPI` is constructed with the report iframe. `KPI.card(title)` locates the card. The grade is
not taken from `KPI.read_text` and not from `Locator.inner_text()`.

The live grade is this node, confirmed by DOM inspection:

```html
<g><text class="value"><tspan>83%</tspan></text></g>
```

`innerText` on that SVG text is empty, so `card.inner_text()` and a `<p>` locator both yield
`''`. Playwright `text_content()` reads DOM `textContent`, which is the percent string.

On `HosenStatusPage`, scoped to the card (or the marked host when `KPI.card` misses):

```python
def _svg_grade(self, root: Locator) -> str:
    """Percent painted in the card SVG. innerText is empty on tspan."""
    node = root.locator(".value tspan").first
    if node.count() == 0:
        node = root.locator(
            "xpath=.//*[local-name()='text' and contains("
            "concat(' ', normalize-space(@class), ' '), ' value ')]"
            "/*[local-name()='tspan']"
        ).first
    if node.count() == 0:
        return ""
    raw = node.text_content(timeout=self.timeout) or ""
    grade = _main_percentage(_plain(raw))
    return grade or _plain(raw)
```

`_read_card` uses that string as the grade. It does not call `inner_text()` on the card for
the percentage. `core/components/kpi.py` stays as it is: `read_text` on a group still runs
`extract_kpi_value_text`, which drops `%`, and on a button it still reads the last `<p>`.

Trend, on that same card locator, in this order: an element whose accessible name says up, down,
or flat; otherwise the arrow node's computed `fill` or `color`. Green → `up`, red → `down`,
yellow → `flat`. The search skips `canvas`. If the only signal is a canvas, `trend` is `""`.

`_assert_rows` compares whatever field the golden row names, and a missing field is `""`:

```python
actual.get(field, "")
```

The checked-in categories use `score` and `trend_direction`. A card that stored `percentage`
and `trend` therefore fails as `ui='' golden='88%'` even after the SVG read. `_read_kpis`
publishes the two shapes the YAML already has. The test is not edited.

```python
national_card = self._read_card(national) or {
    "title": national,
    "percentage": "",
    "trend": "",
}
categories = []
for title in _CATEGORY_TITLES:
    record = self._read_card(title)
    if record is None:
        continue
    categories.append({
        "title": record["title"],
        "score": record["percentage"],
        "trend_direction": record["trend"],
    })
```

`_read_card` still returns `percentage` and `trend` internally. Only the category list is
renamed to the golden keys. The national card is returned as `_read_card` built it
(`title`, `percentage`, `trend`), with `percentage` set from `_svg_grade`.

A visible card whose SVG text is empty still returns the row, with `score` `""` for a
category and `percentage` `""` for the national card, so the golden percent fails. The test
matches categories by `title`. Extra category cards do not fail the test.

### Resilience table

Anchor: visible text `ציון חוסן`. The grid passed to `collect_virtualized_rows` is the table or
grid inside that visual. `row_id` is the authority name. `read_visible` reads the authority text,
the score text, and `getComputedStyle` background color of the row or the score cell. Mapping:

- Green-dominant background → `green`
- Yellow (high red and green, low blue) → `yellow`
- Anything else → the raw `rgb(...)` string, so a golden `green` or `yellow` fails

The callback does not read pixels from `canvas`.

The authority cell is the defect in this amendment. `_assert_rows` does not read the DOM. It
indexes whatever `authority` the page stored:

```python
indexed[_plain(row.get(key, ""))] = row
```

`_read_resilience_scores` passes `lambda row: row.get("authority", "")` as `row_id`, so the
same string is the virtualized-grid identity. The dirty value is assigned here:

```python
authority = _plain(cells.nth(authority_index).inner_text(timeout=500) or "")
```

`Locator.inner_text()` includes the hidden accessibility line Power BI adds for conditional
formatting. `_plain` removes bidi marks and outer whitespace and keeps the internal newline.
The golden key `קרית מלאכי` therefore misses
`קרית מלאכי\nעיצוב מותנה נוסף`.

Replacement, still inside `_visible_resilience_rows`, authority cell only:

```python
extracted_text = cells.nth(authority_index).inner_text(timeout=500) or ""
authority = _plain(extracted_text.split("\n")[0])
```

`split("\n")[0]` is the visible name. `_plain` then drops bidi marks and strips that line,
including a trailing `\r` from `\r\n`. The score line below it stays
`_plain(cells.nth(score_index).inner_text(...))`. `_plain` itself is not changed, so filter
labels, dates, and grades keep every line they already had. The test, the YAML, and
`core/components/virtual_grid.py` are not edited.

### Survey status

Anchor: the top-left block that shows the submitted/total pair. The page locators extract the two
counts and the list of missing authority names. The returned counts are digit strings. The test
applies the integer rule. Missing names are exact strings. Golden names must all appear.

### Sanity test

`conftest.py`:

```python
from pages.hosen_status.page import HosenStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

hosen_status_dashboard = bind_dashboard(HosenStatusPage, "hosen_status_dashboard")
```

`test_hosen_screen1_matches_golden` loads `hosen_dashboard.screen_1_landing`, applies `filters`,
waits until Screen 1 is idle, then compares the golden block to `page.read_screen_1_metrics()`.
`read_screen_1_metrics()` is not called before that wait. Inline comments inside the test
functions stay English.

- Required UI keys: `survey_status`, `kpis`, `resilience_scores`, and `filters`.
- Dict: every golden key is present. Extra UI keys are ignored. An empty actual dict fails when
  the golden dict has keys and the section anchor is visible. `filters` is checked, not skipped.
- List of rows (`resilience_scores`, `kpis.categories`, `missing_authorities`): match on
  `authority`, `title`, or the name string. Extra UI entries are ignored. An empty actual list
  fails when the golden list is non-empty and the anchor is visible.
- `int`: strip bidi marks, commas, spaces, and no-break spaces, then compare the integer.
- `str`: strip bidi marks and outer whitespace, then compare exactly.
- Anchor absent: `pytest.skip` that block only. The other blocks still run. If every anchor is
  absent, the test skips.

### Golden file

`data/hosen/db_sanity.yaml` already holds `hosen_dashboard.screen_1_landing`, including `date`.
This amendment does not edit that file and does not copy a new snapshot. The page and the test
do not embed the date literal. Do not copy values from Hasbara, Credit, or Alerts files.

### Coverage catalog

Add a short Hosen section to `docs/COVERAGE_CATALOG.md` mapping each `screen_1_landing` block to
`read_screen_1_metrics` and `test_hosen_screen1_matches_golden`. State that the source is the YAML
file, not SQL.

## Constitution Check (post-design)

Re-checked after data-model.md and the contract. The design still passes.

- No `core/` edit. District and subdistrict stay on the smart-filter path. `Slicer.select` is
  only the date path whose open listbox is named `SlicerDate`. The spinner wait and the
  role-name table stay on the domain page (I, II, VII).
- The test iterates YAML keys and does not locate dropdowns (IV).
- No new shared compare module. The subset walk is private to the Hosen test (VII).
- No SQL in Layer 0. Sanity YAML is the source of truth named by the spec (V).
- Smoke `verify_freshness` is unchanged (III, IV).
- `networkidle` stays rejected. The idle signal is the spinner plus the ready locator (FR-011).
- `search_input.click(force=True)` stays on `HosenStatusPage`. It does not add a force flag to
  Layer 2 and does not put a locator in the test (I, II, IV, VII).
- The date path does not edit `core/`. `Slicer.select` is limited to an open listbox named
  `SlicerDate` in the frame that contains that listbox. The other branch is one click of the
  already-open option on the page (I, II, VII). Justified in Complexity Tracking.
- The date failure after `_screen_1_settle` propagates. `wait_for_timeout` is absent from
  `select_screen_1_filter` (FR-011).
- `data/hosen/db_sanity.yaml` is unchanged. The selected date is read back, not embedded (FR-012).
- The category SVG locator stays on `HosenStatusPage`. `KPI.card` still finds the card.
  `.value tspan` is not added to `core/components/kpi.py` (II, VII, FR-010).
- The test body still has no locator. `_assert_rows` is unchanged (IV).
- The authority first-line split stays in `_visible_resilience_rows`. `collect_virtualized_rows`
  is not taught a text cleaner, and the golden file is not rewritten to include the
  accessibility line (II, IV, V, VII).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| I, VII — when the open date listbox is not named `SlicerDate`, the page clicks that open option | The list can sit in an iframe nested under the combobox `_filter_control` returned. `Slicer.select` resolves one frame and a listbox named exactly `SlicerDate`, and it clicks the combobox. | Calling `Slicer.select` for every date popup searches the outer report iframe and clicks the combobox again. Editing `Slicer` to walk nested iframes would change every report. The page click is one option click, with no retry loop and no `wait_for_timeout`. |
