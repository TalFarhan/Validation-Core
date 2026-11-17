# Phase 0 Research: Hosen Status Screen 2 YAML Sanity

**Feature**: `051-hosen-screen2-sanity` | **Date**: 2026-11-16

All technical-context unknowns are resolved below. Nothing remains NEEDS CLARIFICATION.

## 1. Feature directory

- **Decision**: Plan this slice in `specs/051-hosen-screen2-sanity`. Repoint `.specify/feature.json` here. Stay on git branch `feature/reportportal-integration`.
- **Rationale**: Setup would otherwise keep the pinned directory `specs/050-hosen-screen1-sanity`, which already has a finished Screen 1 plan. The user task is Screen 2 and says to leave Screen 1 unchanged. This repository already plans a new spec directory without switching the long-lived checkout (see `050` and `049`).
- **Alternatives considered**: Overwrite `050` (would replace the Screen 1 plan). Create a new git branch (the user said the checkout stays `feature/reportportal-integration`).

## 2. Where Screen 2 is opened

- **Decision**: Add `open_investigation_screen(title)` on the existing `HosenStatusPage`. `navigate()` still opens תמ"צ חוסן on Screen 1. `_report_ready_locator()` stays the Screen 1 text `תמ"צ ארצי - דיווחי קה"א יקל"ר`. The test passes `screen_2_investigation.title` into the new method.
- **Rationale**: Screen 2 is not the landing screen. Changing the ready locator would make `navigate()` and the freshness smoke test wait for a heading that is not on Screen 1. Constitution IV puts the new click on the domain page.
- **Alternatives considered**: A second page class (the report is the same catalog entry). Overriding `_report_ready_locator()` after the switch (the smoke test and Screen 1 both depend on the current locator). Hard-coding the title inside the test as a locator (forbidden by the page-object rule).

The open algorithm uses only the title string the test passed:

1. Build candidate labels from that string: the full title, and the segment after the last ` - ` when one exists (`מסך תחקור` is that segment of the golden title, not a second literal).
2. Also accept the ASCII-quote and Hebrew-gershayim spellings of each candidate. Screen 1 already found the report paints `תמ"צ` while the YAML writes `תמ״צ`. The YAML is not edited.
3. Click the first visible `button`, `tab`, `link`, or `option` in the report iframe whose accessible name equals a candidate. Search a page-navigation group named `ניווט בין עמודים` or `Page navigation` first, then the iframe.
4. Expect the full title text (either quote spelling) to be visible.
5. Run the Screen 2 settle: hide a visible spinner, then expect that title.

A control that never appears fails inside `self.timeout`. The method does not call `sleep`, `wait_for_timeout`, or `networkidle`.

## 3. Date and smart filters without changing Screen 1

- **Decision**: Add `select_screen_2_filter(slicer_id, value)`. `date` calls the existing `_select_date_combobox` path. `district` and `subdistrict` call the existing `_select_smart_filter` path. Both gain an optional settle callable. The default remains `_screen_1_settle`, and `select_screen_1_filter` does not pass one. Screen 2 passes `_screen_2_settle`.
- **Rationale**: `_select_date_combobox` and `_select_smart_filter` call `_screen_1_settle`, which expects the Screen 1 ready text. After the investigation screen is open, that text is gone, so calling `select_screen_1_filter` from the Screen 2 test would time out. A defaulted argument keeps every current Screen 1 call on the same settle. `_select_slicer_date` receives the same callable so `Slicer.select` does not settle on Screen 1 either. `core/components/slicer.py` is not edited.
- **Alternatives considered**: Call `select_screen_1_filter` from the Screen 2 test (settles on the wrong title). Copy the click bodies into new private methods (two date implementations that will drift). Change `_screen_1_settle` to look for whichever screen is current (changes the Screen 1 contract).

`select_screen_2_filter` does not fall through to `_select_unnamed_combobox`. The user named two paths: the date combobox, then the smart filters, in YAML order. An unknown id raises `KeyError`.

After `_screen_2_settle`, the date path still raises when the combobox text does not contain `value`. That check already lives in `_select_date_combobox` and stays there.

## 4. Idle signal

- **Decision**: Extract the spinner check that `_wait_for_screen_1_settled` already uses into a private helper, and call it from both settles. Screen 1 then still expects `_report_ready_locator()`. Screen 2 expects the investigation title stored by `open_investigation_screen`. `wait_for_screen_2_idle()` runs that settle once more before `read_screen_2_metrics()`.
- **Rationale**: The user asked for the same wait Screen 1 uses, pointed at the Screen 2 anchor: a visible node whose class contains `spinner`, or a visible `aria-busy="true"` node, is expected hidden; a count of zero is not a failure; then the anchor is expected visible. No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`.
- **Alternatives considered**: `networkidle` (rejected on Screen 1 and rejected again here). A fixed pause. Waiting for the Screen 1 ready text after the page switch.

The Screen 2 anchor used for this wait is the investigation title, not each visual. Per-block anchors are a separate skip/fail decision (section 8).

## 5. Authority breakdown

- **Decision**: Read the bottom authority grid with `collect_virtualized_rows`. Map columns by header text on the page. Publish English keys. The row key is `authority`, using the first line of that cell (`_plain(extracted_text.split("\n")[0])`), the same rule `_visible_resilience_rows` already applies. Do not edit `_visible_resilience_rows`.
- **Rationale**: The golden comment marks this as the bottom table, not a chart. `collect_virtualized_rows` is the reader Screen 1 uses for a virtualized grid. `VisualTable` is reserved for the trends chart, which the user called out as a chart until "show as table". Header text is the stable identity; column position is not. The planned header map is the Screen 1 vocabulary already stored on the page:

  | YAML field | Header constant |
  |------------|-----------------|
  | `authority` | `רשות` |
  | `leadership` | `מנהיגות` |
  | `welfare` | `דאגה לרווחה` |
  | `effective_behavior` | `התנהגות אפקטיבית` |
  | `belonging` | `שייכות וסולידריות` |
  | `functional_continuity` | `רציפות תפקודית` |
  | `narrative` | `נרטיב` |
  | `community_resources` | `מיצוי משאבי קהילה` |
  | `information` | `מידע ותקשורת` |
  | `resilience_score` | `ציון חוסן` |

  Implementation copies a live header spelling that differs into the page constant. It does not edit the YAML and does not put the Hebrew header in the test. A percent cell is published as compact display text (`88%`). Internal spaces inside the token are removed on the page. The test does not parse a float.
- **Alternatives considered**: `VisualTable` for this grid (the user reserved that gesture for the trends chart). Editing `collect_virtualized_rows` to know Hosen headers (domain leakage). Indexing columns by position (breaks when Power BI inserts a selection column).

## 6. Totals row

- **Decision**: `totals_row` is the summary/average row of that same authority grid. The page recognizes it by a label cell whose text is a summary token (`ממוצע`, `ממוצע ארצי`, `סה"כ`, `סה״כ`, or `Total`), quote-folded. That row is not published as an authority. Its nine metric cells use the same header map. If the live grid has no such row, the page reads the sibling visual that shows those nine percents without an authority name, and stores that visual's title as a page constant copied from the live screen.
- **Rationale**: The golden object has the nine metric fields and no `authority`. Its values are the slice averages (the same percents Screen 1 shows as category grades). The user called it the summary/average row. The YAML is not edited to add a label the file does not have.
- **Alternatives considered**: Treating the first or last body row as the total (it would be an authority). Averaging the authority rows in the test (a new calculation, and it would not match a golden file that is a snapshot). Putting the summary label into the YAML (the user said not to edit that file).

## 7. Trends chart

- **Decision**: Locate the trends visual by the page constant `_TRENDS_VISUAL_TITLE` = `מגמות המרכיבים לפי תאריך`. Resolve its host with `_mark_visual_host` as specified in section 11. Call the existing `VisualTable.read_rows(container, name="trends_by_date")`. Do not call `rows_to_label_values`. Map the returned header → cell dicts on the page. The row key is the cell that matches `DD/MM/YYYY`, published as `creation_date`. Metric columns use the same Hebrew header map as the authority table. A cell with no visible value is published as `""`.
- **Rationale**: `VisualTable.read_rows` already right-clicks (`button="right"`), clicks `הצג כטבלה` or `Show as a table`, scrolls, and clicks `חזרה לדוח` before returning. `rows_to_label_values` keeps a single integer and drops percent-only cells, so it cannot represent nine percent fields or an empty cell. The date header text is not in the YAML. Recognizing a `DD/MM/YYYY` cell avoids inventing that header. A second date-shaped column is ignored; the first one is `creation_date`.
- **Alternatives considered**: Reimplement the right-click menu on the page (duplicates Layer 2). Edit `visual_table.py` (no universal reader is missing; the miss is the host the page passes in). Parse percents to floats (the user said percent strings stay display text).

## 11. Trends visual host (2026-11-17)

- **Decision**: `_mark_visual_host` returns the nearest ancestor `div` whose class contains `visualContainer`, then sets the caller's mark attribute on that node. The locator is `xpath=ancestor::div[contains(@class, 'visualContainer')][1]`. If that count is 0, the helper returns `None`. It does not mark the title text node.
- **Rationale**: The live failure is `AssertionError: 'trends_by_date' has no show-as-table menu item`. `VisualTable._click_show_as_table` only raises that after the right-click. The click target is whatever `_mark_visual_host` marked. The current walk is `className.toLowerCase().includes('visual')` and returns on the first hit. From the title text `מגמות המרכיבים לפי תאריך`, that hit is the title strip (`visualTitle`). The title context menu does not contain `הצג כטבלה`. The chart body menu does. Working readers already climb past the title: `Chart._container` and `MainDashboardPage.chart_section` use `ancestor::*[contains(@class,"visualContainer")][1]` (host first, then container). `[1]` on the XPath ancestor axis is the nearest match, so the inner `visualContainer` is chosen when an outer `visualContainerHost` also contains that substring. `contains(@class, 'visualContainer')` does not match `visualTitle`. Playwright requires the `xpath=` prefix; `ancestor::` alone is not CSS. The same helper feeds `_read_totals_sibling`. Marking the visual that owns the summary label still includes the nine percent headers in `inner_text`. `core/components/visual_table.py` stays unchanged because the menu click is already correct.
- **Alternatives considered**: Keep `includes('visual')` and skip a class that contains `title` (the next `visual` node is still not guaranteed to be the chart body, and `visualHeader` can match first). Right-click the title node and look for a different menu item (that menu does not offer show-as-table). Edit `VisualTable` to climb from any node it is given (a Layer 2 change, and the page would still hand it the wrong host). Mark `visualContainerHost` ahead of `visualContainer` (the host is the outer wrapper; the nearest `visualContainer` already encloses the title and the chart body, which is the node the user named). Fall back to `el.setAttribute` on the original text node (that is the title, and it recreates this failure).

## 8. Anchors, empty reads, and skip

- **Decision**: The Screen 2 test asks `screen_2_section_visible(section)` and does not call `section_anchor_visible`. The Screen 1 method stays as it is, including its fall-through `False` for a key it does not know (`title` on Screen 1 stays skipped).
- **Rationale**: Adding a `title` branch to `section_anchor_visible` would change `test_screen1_sanity.py`, which iterates every Screen 1 key. A separate method keeps that loop stable.

  | Section | Visible when |
  |---------|----------------|
  | `title` | the investigation title text is visible |
  | `date` | the date combobox from `_filter_control` is visible |
  | `filters` | a smart-filter shell or a combobox is visible |
  | `authorities_breakdown_table` | the authority-grid header `רשות` is visible |
  | `totals_row` | the summary label, or the sibling average visual, is visible |
  | `trends_by_date_table` | the trends visual is visible |

  A visible section whose reader is empty while the golden block has data fails. A missing section is skipped. The trends reader is not called when its anchor is missing. If all six sections are skipped, the test calls `pytest.skip`.
- **Alternatives considered**: One anchor for the whole `tables` object (a missing chart would skip the authority table, or a present table would fail a missing chart). Reusing `section_anchor_visible` (changes Screen 1).

## 9. Comparison

- **Decision**: Private helpers in `tests/sanity/hosen_status_dashboard/test_screen2_sanity.py` walk the golden block. They are not imported from `test_screen1_sanity.py`, Hasbara, Credit, or Alerts. No file is added under `tests/helpers/`.
- **Rationale**: The user forbade a new comparison engine and forbade changing Screen 1 behavior. Sharing the Screen 1 helpers would make a `null` rule in that module part of Screen 1's behavior. A local copy of the string and row walk is the smaller change.

  Rules:

  - Strings, including percents, match after bidi marks and outer whitespace are removed. They are not parsed.
  - The title comparison also treats `"` and `״` as the same character. Filter labels and authority names stay exact after the bidi trim.
  - YAML `null` (`None` after `yaml.safe_load`) matches an empty cell. It does not match `0%`.
  - Authority rows match on `authority`. Trend rows match on `creation_date`. Extra UI rows and extra dates are ignored.
  - `filters` matches every listed id. Extra slicers are ignored.
  - Failure text starts with `hosen_dashboard.screen_2_investigation` and includes the field path.

## 10. Files that stay

- **Decision**: Do not edit `data/hosen/db_sanity.yaml`, `core/`, `test_screen1_sanity.py`, `test_dashboard_smoke.py`, or any Hasbara, Credit, or Alerts path. Do not add `db/clients/hosen.py`.
- **Rationale**: The golden numbers are the source of truth and already exist. `VisualTable`, `collect_virtualized_rows`, `Slicer.select` for a `SlicerDate` listbox, and the smart-filter click path already exist. The smoke test stays `verify_freshness()`.
- **Alternatives considered**: A warehouse client (the user said there is no SQL client). Extending `VisualTable` with a Hosen header map (domain leakage). Editing the Screen 1 test to share helpers (changes its behavior).
