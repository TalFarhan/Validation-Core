---

description: "Task list for the AlertsPopulationPage internal refactor"
---

# Tasks: Population Page Internal Refactor

**Input**: Design documents from `/specs/038-population-page-refactor/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/population-page.md, quickstart.md

**Tests**: Do not add a test module. Do not edit `tests/sanity/` or `tests/ui/`. Run the existing unit test, then the existing sanity and UI modules. Fleet smoke (`pytest` on `tests/ui/fleet_dashboard/`) is mandatory because `core/components/chart.py` changes, and it gates completion.

**Organization**: Three user stories. Story 1 locks the public surface that already exists. Story 2 consolidates the scroll loop, the row script, and the hover loop. Story 3 removes private `Chart` calls, bare `except Exception`, and blind appearance sleeps. Story 2 and Story 3 both edit `pages/alerts_analysis/population_page.py`, so Story 3 follows Story 2 on that file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Page**: `pages/alerts_analysis/population_page.py`
- **Chart**: `core/components/chart.py`
- **Contract**: `specs/038-population-page-refactor/contracts/population-page.md`
- **Unchanged**: `tests/sanity/`, `tests/ui/`, `data/alerts/db_sanity_am_kalavi.yaml`, `core/portal/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin and record the private call sites before any edit

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/038-population-page-refactor"` and the git checkout stays `feature/reportportal-integration`
- [X] T002 [P] In `pages/alerts_analysis/population_page.py`, confirm the public signatures match `specs/038-population-page-refactor/contracts/population-page.md`, `time.sleep` is absent, `Chart._container` is called only from `set_district_aggregation`, and `Chart._parse` is called only from `read_chart_categories`. Confirm `_sum_scrolled_alert_column`, `_collect_alert_rows`, `_first_row_key`, `_sum_alert_column`, and `_settled_visible_alert_total` have no callers. Confirm `_scroll_visual` is separate from `_scroll_dates_table`. Do not edit `tests/sanity/`, `tests/ui/`, or `data/alerts/db_sanity_am_kalavi.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Publish the chart parse the page already uses, without changing `Chart.read`

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add `parse_container(self, container: Locator, title: str) -> tuple[tuple[ChartCategory, ...], tuple[str, ...]]` to `Chart` in `core/components/chart.py` per `specs/038-population-page-refactor/research.md` Decision 5. Call the existing `_parse(container, title)` and return `(categories, series)`. Do not call `reading_state` and do not clear categories when the reading would be empty. Leave `read`, `category_count`, `is_descending`, and `displayed_title` unchanged. Add no report title and no Hebrew label. Comments inside the method are English

**Checkpoint**: `Chart.read` still blanks an empty reading. `parse_container` returns the raw parse pair for a caller-supplied locator.

---

## Phase 3: User Story 1 - Existing readers keep their results (Priority: P1) 🎯 MVP

**Goal**: The public surface in the contract is the surface the later edits must keep. The unit check is green before those edits.

**Independent Test**: Every signature in `specs/038-population-page-refactor/contracts/population-page.md` matches `pages/alerts_analysis/population_page.py`. `python -m pytest tests/unit/test_population_page.py -q` passes. No file under `tests/sanity/` or `tests/ui/` is edited.

### Implementation for User Story 1

- [X] T004 [P] [US1] Leave every public method signature and every class constant in `pages/alerts_analysis/population_page.py` as listed in `specs/038-population-page-refactor/contracts/population-page.md`. `read_chart_categories(self, title: str)` stays without a return annotation. `chart_total` keeps `series_index: int = 0` and still dispatches `DATES_CHART` to the dates-table total, `HOUR_CHART` to the SVG mark total, `DISTRICT_CHART` to the settled visible total, and every other title to `_rows_for_total`. If a signature already differs from the contract, stop and report it. Do not edit `tests/sanity/` or `tests/ui/`
- [X] T005 [P] [US1] Run `python -m pytest tests/unit/test_population_page.py -q` from `specs/038-population-page-refactor/quickstart.md` and confirm it passes before the consolidation edits. Do not edit `tests/unit/test_population_page.py`

**Checkpoint**: The baseline unit test is green and the public signatures are the ones the contract lists.

---

## Phase 4: User Story 2 - One scroll loop, one row script, one hover loop (Priority: P1)

**Goal**: The dates total and the date-count map share one visible-row scroll. Both entry helpers evaluate one script. District and hour tooltips share one hover loop.

**Independent Test**: `chart_total` for `התרעות לפי תאריך` and `read_date_counts()` both call `_collect_scrolled_rows`. Hidden rows are not stored. `read_district_labels()` and `read_hour_buckets()` hover only after the earlier reads return an empty map. `read_hour_daily_avg()` does not hover.

### Implementation for User Story 2

- [X] T006 [US2] Add a module-level `_ROW_CELLS_JS` string in `pages/alerts_analysis/population_page.py` per `specs/038-population-page-refactor/data-model.md`. The script returns `null` when the row contains `[role="columnheader"]`. Otherwise it returns `{rowIndex: row.getAttribute('aria-rowindex') || '', cells: [...row.querySelectorAll('[role="rowheader"], [role="gridcell"], [role="cell"]')].map(cell => ({role: cell.getAttribute('role') || '', text: (cell.textContent || '').trim()}))}`. The comment above the string is English
- [X] T007 [US2] Rewrite `_visible_alert_entry` and `_visible_date_entry` in `pages/alerts_analysis/population_page.py` to evaluate `_ROW_CELLS_JS` from T006. Keep the Python rules in `specs/038-population-page-refactor/data-model.md`: both omit a header row, a `סה"כ` row, a non-`gridcell` alerts column, and a non-integer. The alerts entry keys by `aria-rowindex` or the row-header text. The date entry keys by the row-header text only and returns `(None, None)` when that text is empty. Apply `_plain_cell` before the integer parse. Catch `playwright.sync_api.Error` around `evaluate`. Comments inside the methods are English
- [X] T008 [US2] Point `_visible_alert_value`, `_visible_district_value`, and `_visible_district_label` in `pages/alerts_analysis/population_page.py` at `_ROW_CELLS_JS`. Keep each method's current skip rules: the alert value accepts `gridcell` or `cell`; the district value uses the `התרעות` `gridcell` when the column index is in range, otherwise the first integer `gridcell` or `cell`; the district label still requires a row header. Catch `playwright.sync_api.Error` around `evaluate`. Comments inside the methods are English
- [X] T009 [US2] Add `_collect_scrolled_rows(self, table, column, *, key)` to `pages/alerts_analysis/population_page.py` per `specs/038-population-page-refactor/contracts/population-page.md`. `key="stable"` uses the alerts entry. `key="header"` uses the date entry. Scroll with the existing `_scroll_dates_table` to `"top"`, collect visible rows, page down, and stop at `self.timeout` or after two passes that add no key and do not move. A row that fails `is_visible()` is omitted. `0` is stored. Do not add a `finish_at_end` mode and do not read hidden rows. After a page-down, poll until the first visible row key changes or the step budget ends; a quiet step returns to the loop and does not raise. Catch `playwright.sync_api.Error` on the scroll evaluate. Comments inside the method are English
- [X] T010 [US2] In `pages/alerts_analysis/population_page.py`, change `_dates_table_total` to call `_collect_scrolled_rows(table, column, key="stable")` and return `(sum(values), len(map))`, still raising `AssertionError` when the included count is 0. Change `read_date_counts` to return `_collect_scrolled_rows(table, column, key="header")`. Keep the right-click, `הצג כטבלה` / `Show as a table`, and `חזרה לדוח` close in `finally`. Keep both public signatures. Delete `_sum_scrolled_visible_alert_column`, `_collect_visible_alert_rows`, `_collect_date_counts`, `_collect_visible_date_rows`, `_sum_scrolled_alert_column`, `_collect_alert_rows`, and `_first_row_key`. Delete `_sum_alert_column` and `_settled_visible_alert_total` only when they still have no caller. Leave `_scroll_visual` in place. Comments inside the edited methods are English
- [X] T011 [US2] Add `_hover_mark_values(self, container, parse)` to `pages/alerts_analysis/population_page.py` per `specs/038-population-page-refactor/research.md` Decision 4. Walk `svg rect, svg path, svg circle`, skip a mark that is not visible, hover with `timeout=1000`, stop at 40 marks, pass the tooltip text to `parse`, and call `_dismiss_overlay` once after the walk. Make `_tooltip_name_counts` pass a parser that skips `ממוצע`, uses the first integer line as the value, and uses the first other line as the name. Make `_hour_tooltip_buckets` pass `_hour_bucket`. Leave the call order in `read_district_labels` (visible rows, then mark labels, then tooltip) and in `read_hour_buckets` (aria labels, then categories, then mark labels, then tooltip). Do not hover when an earlier read returned a non-empty map. Do not call the hover helper from `read_hour_daily_avg`. Catch `playwright.sync_api.Error` on count, visibility, and hover. Comments inside the methods are English

**Checkpoint**: One scroll collector feeds both dates reads. One script feeds the row helpers. One hover loop feeds both tooltip fallbacks. Public signatures are unchanged.

---

## Phase 5: User Story 3 - Private Chart access, broad catches, and blind waits are gone (Priority: P2)

**Goal**: The page calls public `Chart` methods or its own locators. Playwright failures are `Error`. An element that must appear is waited on with `state="visible"`.

**Independent Test**: `pages/alerts_analysis/population_page.py` contains no `_chart._container`, no `_chart._parse`, no `except Exception`, and no `time.sleep`. `set_district_aggregation` still clicks the single exact button, or the first frame button when that count is not 1. `read_chart_categories` still returns categories for a page-scoped container that `Chart.read` would blank.

### Implementation for User Story 3

- [X] T012 [US3] Update `set_district_aggregation` in `pages/alerts_analysis/population_page.py` per `specs/038-population-page-refactor/contracts/population-page.md`. Resolve the district visual with `_visual_container(self.DISTRICT_CHART)`. Click `get_by_role("button", name=label, exact=True)` inside that visual only when the count is exactly 1. Otherwise click `self._report_frame().get_by_role("button", name=label, exact=True).first`. On `AssertionError` from `_visual_container`, use that frame fallback. `sum` still uses `SUM_MODE` (`סכום`) and `average` still uses `AVERAGE_MODE` (`ממוצע ליום`). Remove the `Chart._container` call. Keep the signature `set_district_aggregation(self, mode: AggregationMode) -> None`. Comments inside the method are English
- [X] T013 [US3] Update `read_chart_categories` in `pages/alerts_analysis/population_page.py` to keep `container = self._visual_container(title)` and to call `self._chart.parse_container(container, title)` from T003. Return that `(categories, series)` pair, including a reading `Chart.read` would blank. Remove the `Chart._parse` call. Leave the signature `read_chart_categories(self, title: str)` without a return annotation. In `read_hour_daily_avg`, keep `except AssertionError` around this call and return `{}`. In `read_district_labels`, keep `except AssertionError` around `_visual_container` and return `{}`. Comments inside the edited methods are English
- [X] T014 [US3] Replace every remaining `except Exception` in `pages/alerts_analysis/population_page.py` with `except Error`, importing `Error` from `playwright.sync_api`. Do not import or catch `ElementHandleError`. Leave the `AssertionError` handlers from T013. Leave `AssertionError` raised by an empty `chart_total`, a missing show-as-table item, a missing alerts table, and a missing `חזרה לדוח` button so those still propagate. Comments inside edited methods are English
- [X] T015 [US3] Update waits in `pages/alerts_analysis/population_page.py` per `specs/038-population-page-refactor/research.md` Decision 8. For `הצג כטבלה` / `Show as a table` and for the alerts grid or table, wait with `locator.wait_for(state="visible")` inside the existing deadline. On `playwright.sync_api.TimeoutError`, try the next candidate. Do not give the full `self.timeout` to the first missing label. Remove the unconditional `page.wait_for_timeout(800)` in `set_hierarchy_level`. When the clicked control's `aria-pressed` or `aria-selected` is not `None`, wait with `expect(control).to_have_attribute(..., "true", timeout=self.timeout)` and return `False` if that wait fails. When both attributes are `None`, keep the district-title `is_visible(timeout=3000)` check and add no new fixed sleep in front of it. Keep the two-equal-read polls in `clear_filters`, `set_date_range`, and `_district_visible_total`; `page.wait_for_timeout` may remain only as the interval inside those polls, because this Playwright build has no `expect.poll`. Do not add `time.sleep`. Keep `_plain_cell` on this page and do not import `Chart._dedupe_doubled`. Comments inside edited methods are English

**Checkpoint**: Private `Chart` calls, bare `except Exception`, and unconditional appearance sleeps are gone. Empty-map `AssertionError` paths still return `{}`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Prove the public surface, the suites, and the fleet gate

- [X] T016 [P] Confirm `tests/sanity/`, `tests/ui/`, `data/alerts/db_sanity_am_kalavi.yaml`, and `core/portal/` have no edits from this slice. In `pages/alerts_analysis/population_page.py`, confirm there is no `except Exception`, no `_chart._container`, no `_chart._parse`, no `time.sleep`, and no `_sum_scrolled_alert_column`. Confirm the public signatures still match `specs/038-population-page-refactor/contracts/population-page.md`. Confirm `core/components/chart.py` still has no alerts title and no Hebrew label
- [X] T017 [P] Run `python -m pytest tests/unit/test_population_page.py -q` from `specs/038-population-page-refactor/quickstart.md`. It must pass. Do not edit the test
- [X] T018 [P] Run `python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py tests/sanity/alerts_analysis_dashboard/test_data_validation.py -q` from `specs/038-population-page-refactor/quickstart.md`. Portal auth is required. Do not edit those tests. A non-empty map that misses a golden key fails. An empty map may still skip with the message already in the test
- [X] T019 [P] Run `python -m pytest tests/ui/fleet_dashboard/ -q` from `specs/038-population-page-refactor/quickstart.md`. This gates completion because `core/components/chart.py` changed. The run must be 100% green. Do not edit fleet page objects

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — blocks every user story
- **User Story 1 (Phase 3)**: Depends on Foundational. No dependency on User Story 2 or User Story 3
- **User Story 2 (Phase 4)**: Depends on Foundational. No functional dependency on User Story 1. It edits `pages/alerts_analysis/population_page.py` after the signature check so the public defs stay put
- **User Story 3 (Phase 5)**: Depends on T003 and on T011. It edits the same page file after the scroll and hover helpers exist, and it calls `parse_container`
- **Polish (Phase 6)**: Depends on all three user stories

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T003. Confirms signatures and the unit baseline. It does not change runtime behavior
- **User Story 2 (P1)**: Starts after T003. Uses `_ROW_CELLS_JS`, `_collect_scrolled_rows`, and `_hover_mark_values` in `pages/alerts_analysis/population_page.py`
- **User Story 3 (P2)**: Starts after T011. Uses `Chart.parse_container`, `_visual_container`, `playwright.sync_api.Error`, and visibility waits in `pages/alerts_analysis/population_page.py`

### Within Each User Story

- User Story 1 has no new test to write. T004 and T005 only read the current tree
- User Story 2: the script (T006) comes before the entry helpers (T007, T008). The collector (T009) comes before the dates wiring and deletions (T010). The hover helper (T011) comes after the dates wiring so the two page edits do not overlap
- User Story 3: the district button (T012) and category parse (T013) come before the remaining `except Exception` sweep (T014), so newly edited methods are not swept twice. Waits (T015) come last
- Story 2 and Story 3 are not parallel: they share `pages/alerts_analysis/population_page.py`

### Parallel Opportunities

- T001 and T002 touch different checks and can run together
- T004 and T005 can run together
- T016, T017, T018, and T019 can run together after Phase 5
- T003 is the only edit to `core/components/chart.py`. It does not run beside a page edit that calls `parse_container` until T013

---

## Parallel Example: User Story 1

```bash
# Signature check and the unit baseline read different artifacts:
Task: "T004 Leave public signatures in pages/alerts_analysis/population_page.py matching the contract"
Task: "T005 Run python -m pytest tests/unit/test_population_page.py -q"
```

## Parallel Example: Polish

```bash
# After T015, the four checks edit nothing:
Task: "T016 Confirm tests, YAML, portal, and the private-call search"
Task: "T017 Run python -m pytest tests/unit/test_population_page.py -q"
Task: "T018 Run the population invariant and sanity modules"
Task: "T019 Run python -m pytest tests/ui/fleet_dashboard/ -q"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (`parse_container` only)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Signatures match the contract and the unit test passes
5. Story 1 does not change reader results. The first behavior-preserving code increment is User Story 2

### Incremental Delivery

1. Setup + Foundational → `Chart.read` is unchanged and `parse_container` exists
2. User Story 1 → baseline signatures and unit test (MVP checkpoint)
3. User Story 2 → one scroll, one row script, one hover loop, public signatures still unchanged
4. User Story 3 → no private `Chart` call, no bare `except Exception`, appearance waits use `state="visible"`
5. Polish → unit, sanity, UI, and fleet smoke. Fleet smoke must be 100%

### Parallel Team Strategy

With multiple developers:

1. One developer completes T003 in `core/components/chart.py`
2. After T003, User Story 1 can be checked while that developer starts User Story 2
3. User Story 3 waits until T011, because it edits `pages/alerts_analysis/population_page.py` again

---

## Notes

- [P] tasks = different files or read-only checks, no incomplete dependency
- [US1], [US2], and [US3] map to the three stories in `specs/038-population-page-refactor/spec.md`
- Do not edit `tests/sanity/` or `tests/ui/`
- Comments inside new and edited functions are English
- `_plain_cell` stays. `Chart._dedupe_doubled` stays private
- `_scroll_visual` stays separate from the dates-table scroller
- The unused hidden-row scroll is deleted, not turned into a mode of `_collect_scrolled_rows`
