# Phase 0 Research: Hosen Status Screens 3 and 4 YAML Sanity

**Feature**: `052-hosen-screen34-sanity` | **Date**: 2026-11-17

All technical-context unknowns are resolved below. Nothing remains NEEDS CLARIFICATION.

## 1. Feature directory

- **Decision**: Plan this slice in `specs/052-hosen-screen34-sanity`. Repoint `.specify/feature.json` here. Stay on git branch `feature/reportportal-integration`.
- **Rationale**: Setup would otherwise keep the pinned directory `specs/051-hosen-screen2-sanity`, which already has a finished Screen 2 plan. The user task is Screens 3 and 4 and says Screens 1 and 2 stay untouched. This repository already plans a new spec directory without switching the long-lived checkout (see `050` and `051`).
- **Alternatives considered**: Overwrite `051` (would replace the Screen 2 plan). Create a new git branch (the checkout stays `feature/reportportal-integration`).

## 2. Where the screens are opened

- **Decision**: Add `open_geographic_screen(title)` and `open_excel_export_screen(title)` on the existing `HosenStatusPage`. Both call the private helpers `open_investigation_screen` already uses (`_navigation_scopes`, `_click_named_control`, `_control_name_matches`). `navigate()` still opens תמ"צ חוסן on Screen 1. `_report_ready_locator()` stays `תמ"צ ארצי - דיווחי קה"א יקל"ר`. `open_investigation_screen` is not edited.
- **Rationale**: Screens 3 and 4 are not the landing screen. Changing the ready locator would make `navigate()` and the freshness smoke test wait for a heading that is not on Screen 1. Refactoring `open_investigation_screen` into a shared public opener would touch the Screen 2 method the user said to leave in place. Constitution IV puts the new clicks on the domain page.
- **Alternatives considered**: A second page class (the report is the same catalog entry). Overriding `_report_ready_locator()` after the switch (the smoke test and Screen 1 both depend on the current locator). Editing `open_investigation_screen` to accept a settle callback (changes a Screen 2 method to serve a later screen).

The open algorithm, per new method, uses only the title string the test passed:

1. Build candidate labels from that string: the full title, and the segment after the last ` - ` when one exists.
2. Accept the ASCII-quote and Hebrew-gershayim spellings of each candidate. The YAML writes `תמ״צ`. The live control may paint `תמ"צ`. The YAML is not edited.
3. Click the first visible `button`, `tab`, `link`, or `option` in the report iframe whose accessible name equals a candidate. Search a page-navigation group named `ניווט בין עמודים` or `Page navigation` first, then the iframe.
4. Expect the full title text (either quote spelling) to be visible.
5. Run that screen's settle: hide a visible spinner, then expect that title.

A control that never appears fails inside `self.timeout`. The method does not call `sleep`, `wait_for_timeout`, or `networkidle`.

## 3. Date range and a single date

- **Decision**: Screen 3 `date_range.start` then `date_range.end` each call the existing `_select_date_combobox` with `settle=self._screen_3_settle`. Screen 4 `date` calls the same helper with `settle=self._screen_4_settle`. The default settle stays `_screen_1_settle`. `select_screen_1_filter` and `select_screen_2_filter` do not pass a new argument.
- **Rationale**: `_select_date_combobox` already opens the combobox, chooses the label, settles, and raises when the combobox text does not contain the value. Screen 3 has two endpoints in the YAML, so it needs two calls and two controls. Visual order (top, then left) assigns start and end when two date comboboxes are visible. Hebrew accessible names are page constants copied from the live control at implementation time. Another report's range helper is not imported: Alerts `set_between_dates` sleeps, and Hasbara `apply_date_range` belongs to a different page.
- **Alternatives considered**: Call `select_screen_2_filter("date", ...)` (settles on the Screen 2 title). One new date engine on the page (a second implementation of a path that already exists). Edit `core/components/slicer.py` (no generic gap; the page already resolves the control).

## 4. Smart filters, including `null`

- **Decision**: Non-null filter values call the existing `_select_smart_filter(role_names, value, settle=...)`. Screen 3 ids are `level_selected`, `district`, `subdistrict`, `authority`. Screen 4 ids are `sector`, `district`, `subdistrict`, `authority`. Placeholder hints for the new ids live in screen-specific tuples on the page. `_FILTER_ROLES` is not extended. A YAML `null` is not passed to the selector. The read-back of that id is `""`.
- **Rationale**: `_select_smart_filter` is the reader the user named. Screen 2's test does `str(value)` for every map entry, which is safe there because that map has no `null`. Screen 3 `authority` and Screen 4 `sector` and `authority` are `null`. `str(None)` is the label `None`, which would type a word the golden file does not contain. `level_selected` is the word `מחוז`, which is also the first word of `מחוז דרום`. A shared chip index would put that word in the district box. `_smart_filter_label` still maps chip 0 to district and chip 1 to subdistrict for Screens 1 and 2; leaving `_FILTER_ROLES` alone keeps that index.
- **Alternatives considered**: Reuse `select_screen_2_filter` for every id (unknown ids raise `KeyError`, and the settle is the Screen 2 title). Append the new ids to `_FILTER_ROLES` (the chip index is safe today, but the next edit of that tuple is how Screen 1's district chip moves). Apply `null` as a cleared selection click (the golden file says the chip is empty; not sending a value leaves a chip that was already empty, and a clear-all would wipe `district`).

The Screen 3 and Screen 4 read-back finds the chip for that id's own placeholder, or returns `""` when the box still shows its placeholder. It does not call `_smart_filter_label`.

## 5. Idle signal

- **Decision**: `_screen_3_settle` and `_screen_4_settle` call the existing `_hide_visible_spinner`, then expect the title stored by the opener. `wait_for_screen_3_idle()` and `wait_for_screen_4_idle()` run that settle once more before the metric read. `_wait_for_screen_1_settled` and `_screen_2_settle` are not edited.
- **Rationale**: The user asked for the same wait Screens 1 and 2 use, pointed at the current screen's anchor. A visible node whose class contains `spinner`, or a visible `aria-busy="true"` node, is expected hidden; a count of zero is not a failure; then the anchor is expected visible. No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`.
- **Alternatives considered**: `networkidle` (rejected on Screens 1 and 2). A fixed pause. Waiting for the Screen 1 ready text after the page switch.

## 6. Graph body, not the header

- **Decision**: Screen 3 passes the locator `_mark_visual_host` already returns into `VisualTable.read_rows`. That helper walks ancestors until it finds `vcGroupBody` with width at least 200 and height at least 120, and marks that node. It does not mark the title text and it does not mark the ~38px `visualHeaderAbove` / `visualContainer` header. The helper is not edited.
- **Rationale**: The live helper was written for this report because the nearest `visualContainer` from a chart title is the header strip, and that strip's menu has no `הצג כטבלה`. `vcGroupBody` is the wrapper whose menu does. `VisualTable.read_rows` right-clicks the center of the locator it is given. The center of a host at least 120px tall sits below a 38px header. Changing the climb would change Screen 2's trends read, which uses the same helper. `core/components/visual_table.py` stays unchanged because the menu click is already correct when the host is the graph body.
- **Alternatives considered**: Revert `_mark_visual_host` to `ancestor::div[contains(@class, 'visualContainer')][1]` (that node is the header on this report, which is the miss the user named). Right-click the title text. Teach `VisualTable` to climb out of `visualHeaderAbove` (a Layer 2 change, and Screen 2 would still depend on the page helper). A new marker that duplicates the `vcGroupBody` walk.

The legend is read from the marked host's text before `read_rows`, because the show-as-table view replaces the chart. The final-score `legend` is that string (`מחוז דרום` in the golden file). It is not the district chip outside the host. Category charts have no `legend` field. The page does not add one.

## 7. Charts through `VisualTable`

- **Decision**: For each visible chart title, call `VisualTable.read_rows(host, name=...)`. Do not call `rows_to_label_values`. Map header → cell dicts on the page. The row key is the cell that matches `DD/MM/YYYY`, published as `date`. The percent cell is published as `score` via the existing `_percent_token`. A cell with no visible value is `""`. The page discovers titles that are on screen. The test subsets by the golden `title`. The page does not embed the eight category titles or the final-score title.
- **Rationale**: `VisualTable.read_rows` already right-clicks, clicks `הצג כטבלה` or `Show as a table`, collects rows, and clicks back to the report before returning. Nine sequential cycles (one final-score chart and eight category charts) are the Screen 3 read. `rows_to_label_values` keeps a single integer and cannot represent a date plus a percent string. `_percent_token` keeps the matched token, including a decimal, so `85%` and `75.0%` stay display text.
- **Alternatives considered**: Reimplement the right-click menu on the page. Edit `visual_table.py` to know Hosen chart titles (domain leakage). Parse percents to floats.

## 8. Export grid through `collect_virtualized_rows`

- **Decision**: Screen 4 `data_table` is the grid that is already a table. Read it with `collect_virtualized_rows`. Do not open `הצג כטבלה`. Do not download an `.xlsx`. Map columns with a Screen 4 header tuple. Publish the golden English keys. `authority` is the first line of that cell. Metric cells go through `_percent_token`. `_SCREEN2_HEADERS` and `_field_for_header` are not retargeted.
- **Rationale**: The golden block is `data_table`, a list of authorities and percents. It has no file name and no bytes. The user reserved `VisualTable` for graphs. Screen 2's header map uses different English keys (`welfare`, `resilience_score`, `information`, `belonging`) for headers that Screen 4 publishes as `care_for_welfare`, `final_score`, `information_and_communication`, and `belonging_and_solidarity`. A shared map would rename Screen 2 fields. The live header spelling, including the column that is `final_score`, is copied into the Screen 4 tuple. The YAML is not edited to match a guessed header.
- **Alternatives considered**: `VisualTable` on a grid that is already a table. A download listener (nothing in the golden file to compare the file to). Editing `_field_for_header` so one Hebrew header returns a Screen 4 key (breaks Screen 2).

## 9. `scrollTop` continuation

- **Decision**: Keep the public function `collect_virtualized_rows`. Change its stop rule. Today the walk ends when `_scroll(grid, "page")` reports that `scrollTop` did not change, or when the next viewport adds no new row id. The second stop is removed. After a step assigns `scrollTop`, the function reads the value back. If the largest overflow node did not move, the step tries the other overflow nodes in that family, which is what the horizontal sweep already does. If no node moved, the walk ends. If `scrollTop` increased, painted rows are stored and the walk continues even when every id was already known. `timeout_ms` still ends the walk. Deduping by the caller-supplied `row_id` stays. `VisualTable._collect_rows` stays a call to this function. The page does not copy `_SCROLL_JS`.
- **Rationale**: Screen 3 dates and Screen 4 authorities are virtualized. `VisualTable.read_rows` collects and then leaves the table before the caller can scroll. The page therefore cannot finish a partial chart read by itself. The current "no new id" stop is what drops a later date when the first paint after a scroll repeats ids that were already stored, or when the first candidate's `scrollTop` assignment does not stick while another node in the family still scrolls. The user required dynamic `scrollTop` evaluation and forbade a rewritten reader. Continuing inside the existing function is that evaluation. The signature stays, so Screen 1, Screen 2, fleet, and `VisualTable` keep their call sites. No Hebrew and no golden date are added to `core/`.
- **Alternatives considered**: A Hosen-only scroll loop after `read_rows` (the table is already closed). Copying `_SCROLL_JS` into `page.py` (a second reader). Leaving the stop unchanged (later dates stay missing). A new public `collect_until(row_id)` (a new generic API the constitution says not to invent; the existing function is the API).

Fleet smoke (`pytest tests/ui/fleet_dashboard/`) is the gate for this edit, together with the Hosen Screen 1 and Screen 2 sanity tests. Those callers must still receive every row they already matched. A later viewport may fill a blank cell on a stored row, which the function already does.

## 10. Anchors, empty reads, and skip

- **Decision**: The new tests ask `screen_3_section_visible` and `screen_4_section_visible`. They do not call `section_anchor_visible` or `screen_2_section_visible`. Those two methods stay as they are, including the fall-through `False` for a key they do not know.
- **Rationale**: Adding a `title` branch to `section_anchor_visible` would change `test_screen1_sanity.py`. Adding a branch to `screen_2_section_visible` would put Screen 3 titles on the Screen 2 skip switch.

  Screen 3:

  | Section | Visible when |
  |---------|----------------|
  | `title` | the geographic title text is visible |
  | `date_range` | both date controls used for start and end are visible |
  | `filters` | a smart-filter shell or a combobox is visible |
  | `final_resilience_score` | that chart's title text is visible |
  | `categories` | at least one category-chart title is visible |

  Screen 4:

  | Section | Visible when |
  |---------|----------------|
  | `title` | the export title text is visible |
  | `date` | the date combobox is visible |
  | `filters` | a smart-filter shell or a combobox is visible |
  | `data_table` | a visible column header containing `רשות` on this screen |

  A visible section whose reader is empty while the golden block has data fails. A missing section is skipped. A chart reader is not called when its title is absent. If every section on that screen is skipped, the test calls `pytest.skip`. Inside a visible `categories` block, a golden `title` that was not read still fails. That is a missing golden chart, not a skip.
- **Alternatives considered**: One anchor for the whole screen (a missing chart would skip the filters, or a present title would fail a missing chart). Reusing `section_anchor_visible` (changes Screen 1).

## 11. Comparison

- **Decision**: Private helpers in `test_screen3_sanity.py` and `test_screen4_sanity.py` walk the golden block. They are not imported from `test_screen1_sanity.py`, `test_screen2_sanity.py`, Hasbara, Credit, or Alerts. No file is added under `tests/helpers/`.
- **Rationale**: The user forbade a new comparison engine and forbade changing Screen 1 and Screen 2 behavior. Sharing the Screen 2 helpers would make a Screen 3 `null` rule part of that module.

  Rules:

  - Strings, including percents, match after bidi marks and outer whitespace are removed. They are not parsed. `75.0%` does not match `75%`.
  - The title comparison treats `"` and `״` as the same character. Authority names do too.
  - YAML `null` (`None` after `yaml.safe_load`) matches an empty cell or an empty chip. It does not match `0%`.
  - Chart rows match on `date`. Category charts match on `title`. Export rows match on `authority`. Extra UI rows, extra dates, and extra charts are ignored.
  - `filters` matches every listed id. Extra slicers are ignored. A listed `null` matches `""`.
  - Failure text starts with `hosen_dashboard.screen_3_geographic_investigation` or `hosen_dashboard.screen_4_excel_export` and includes the field path.

## 12. Files that stay

- **Decision**: Do not edit `data/hosen/db_sanity.yaml`, `core/portal`, `core/components/visual_table.py`, `core/components/slicer.py`, `test_screen1_sanity.py`, `test_screen2_sanity.py`, `test_dashboard_smoke.py`, or any Hasbara, Credit, or Alerts path. Do not add `db/clients/hosen.py`. Do not edit `_mark_visual_host`, `_FILTER_ROLES`, `_field_for_header`, `open_investigation_screen`, `select_screen_2_filter`, or `read_screen_2_metrics`.
- **Rationale**: The golden numbers are the source of truth and already exist. The date path, the smart-filter path, `VisualTable.read_rows`, and the graph-body climb already exist. The smoke test stays `verify_freshness()`. The only core edit is the scroll stop in section 9.
- **Alternatives considered**: A warehouse client (the user said there is no SQL client). Extending `VisualTable` with a Hosen header map (domain leakage). Editing the Screen 2 test to share helpers (changes its behavior).
