---
description: "Task list for the Hasbara screen 3 satisfaction sub-tab locator"
---

# Tasks: Hasbara Dashboard UI Sanity Validation (satisfaction sub-tab locator)

**Input**: Design documents from `/specs/049-hasbara-ui-validation/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/hasbara-ui-validation.md, contracts/virtual-grid.md, quickstart.md

**Tests**: No new test module. `test_hasbara_screen3_distributions_match_golden` already calls `select_satisfaction_tab(service["active_tab"])` and compares `service_reception.responses`. This revision does not edit `tests/sanity/public_inquiries_dashboard/test_data_validation.py` and does not edit `data/hasbara/db_sanity.yaml`. `core/` is not edited, so fleet smoke is not a new gate (Constitution III).

**Already shipped**: Date range and `הכל` filters, duration widgets, the inquiries body settle and visible KPI locators, survey-card waits, screen 1 chart reads, the virtualized-grid collector, Show as a table for screen 2 and screen 4 (including the data-view grid choice), the screen 4 rendered gate, and the `last_updated` removal. Do not rewrite `_read_grid`, `_read_duration_widget`, `_expect_inquiry_counts_settled`, `_wait_for_survey_cards`, `apply_date_range`, `read_satisfaction`, `_click_tab`, or `_tab_locator`. Do not change the ten test names.

**Organization**: Tasks follow the six user stories in spec.md. User Story 4 is the open work: `select_satisfaction_tab` must click the visible courtesy sub-tab. The other stories stay as they shipped.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US6 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page edit: `pages/public_inquiries/page.py` (`select_satisfaction_tab` and a new `_satisfaction_tab_locator`)
- Sanity test (unchanged): `tests/sanity/public_inquiries_dashboard/test_data_validation.py`
- Golden record (read-only): `data/hasbara/db_sanity.yaml` root `hasbara_dashboard` → `screen_3_satisfaction_feedback.service_reception`
- Contract: `specs/049-hasbara-ui-validation/contracts/hasbara-ui-validation.md` section `select_satisfaction_tab`
- Research: `specs/049-hasbara-ui-validation/research.md` decision R18
- OFF-LIMITS: `core/portal/page.py`, `core/components/`, `pages/alerts_analysis/`, `pages/credit_consumption/`, `pages/fleet_dashboard/`, `pages/status_picture/`, `db/`, root `conftest.py`, `data/hasbara/db_sanity.yaml`, `tests/ui/public_inquiries_dashboard/`, `tests/sanity/public_inquiries_dashboard/test_data_validation.py`, `tests/unit/test_visual_table_rows.py`, `docs/PROJECT_GUIDE.md`, `specs/048-fleet-table-extraction/`

Do not add `pages/public_inquiries/__init__.py`. In-function comments, locator variable names, wait conditions, method names, and docstrings stay English (FR-010). Hebrew stays in the section-title constant and in the label string the test already passes. Do not call `page.wait_for_timeout` or `page.wait_for_load_state("networkidle")`. Do not load the YAML from the page.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the page-rail click is what times out, and confirm the label the test passes

- [X] T001 Read `select_satisfaction_tab`, `_click_tab`, `_tab_locator`, `_open_tab`, `_report_frame`, `_first_outside_tooltip`, `_visual_container`, and `_iframe_phrase_locator` in `pages/public_inquiries/page.py`, the `select_satisfaction_tab` call in `tests/sanity/public_inquiries_dashboard/test_data_validation.py` (`test_hasbara_screen3_distributions_match_golden`), and `service_reception` in `data/hasbara/db_sanity.yaml`. Confirm `select_satisfaction_tab` calls `_click_tab`, and that `_tab_locator` matches only `ניווט בין עמודים . {label}` on a visible link, image, or button. Confirm a `yaml.safe_load` of the golden file keeps the last `active_tab`, which is `אופן מקצועי`. Do not edit any file in this task (plan.md "satisfaction sub-tab locator", research.md R18).

**Checkpoint**: The distributions test clicks `אופן מקצועי` through the page-rail locator. The courtesy sub-tabs above the chart are not that rail. No file has changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Keep the four-screen page rail, and name the helpers the new locator will reuse

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 In `pages/public_inquiries/page.py`, confirm `_click_tab` and `_tab_locator` stay the only navigation for `open_screen` and `_open_tab`, and that the accessible-name pattern stays `ניווט בין עמודים . {label}` anchored at the end. Confirm `_report_frame()` returns the report `FrameLocator`, `_first_outside_tooltip` skips `[role='tooltip']` and non-paintable nodes, and `_visual_container` returns the smallest visible host for a title or raises `AssertionError` when that title has no host. Do not edit `_click_tab`, `_tab_locator`, `core/portal/page.py`, or `core/components/`. Depends on T001 (research.md R18, AC-001).

**Checkpoint**: Screen 1–4 tab clicks still use the page rail. The satisfaction locator will be a separate method on the same page.

---

## Phase 3: User Story 1 - Date range and default filters on every tab (Priority: P1) 🎯 MVP

**Goal**: The four filter tests still apply each screen's `dashboard_info.date_range` and read `הכל`. This revision does not change the date fill or the slicer asserts.

**Independent Test**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k filters_match_golden`

### Implementation for User Story 1

- [X] T003 [P] [US1] Leave `apply_date_range`, `_click_period_toggle`, and the date-input helpers in `pages/public_inquiries/page.py`, and leave the four `test_hasbara_screen*_filters_match_golden` functions in `tests/sanity/public_inquiries_dashboard/test_data_validation.py`, as they shipped. Do not click the period toggle a second time. Do not pass `הכל` to `Slicer.select`. Do not edit the test file or `data/hasbara/db_sanity.yaml` (FR-001, FR-002, FR-003).

**Checkpoint**: US1 stays the shipped date-and-filter compare.

---

## Phase 4: User Story 2 - Written Response KPIs and charts (Priority: P1)

**Goal**: Screen 1 KPI, duration, and chart readers stay as shipped.

**Independent Test**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k "test_hasbara_screen1_kpi_match_golden or test_hasbara_screen1_charts_match_golden"`

### Implementation for User Story 2

- [X] T004 [P] [US2] Leave `read_kpi_metrics`, `_read_duration_widget`, `_expect_inquiry_counts_settled`, `_read_category_chart`, and `_read_hourly_trend` in `pages/public_inquiries/page.py` as they shipped. Do not edit `core/components/visual_table.py` or `tests/sanity/public_inquiries_dashboard/test_data_validation.py`. Do not hard-code `1324`, `1,324`, or `49` (FR-004, FR-005).

**Checkpoint**: Screen 1 readers are untouched.

---

## Phase 5: User Story 3 - Written investigation rows (Priority: P1)

**Goal**: Investigation rows stay on the shipped Show as a table path, including `handling_time`.

**Independent Test**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen2_investigation_rows_match_golden`

### Implementation for User Story 3

- [X] T005 [US3] Leave `_read_grid`, `read_investigation_rows`, and `_INVESTIGATION_HEADERS` in `pages/public_inquiries/page.py` as they shipped. Do not point `_read_grid` back at the canvas grid. Do not edit `core/components/visual_table.py`, `core/components/virtual_grid.py`, or `tests/sanity/public_inquiries_dashboard/test_data_validation.py` (FR-006).

**Checkpoint**: Screen 2 still reads the expanded grid. This revision does not touch that reader.

---

## Phase 6: User Story 4 - Satisfaction cards and bars (Priority: P1)

**Goal**: `select_satisfaction_tab` clicks the visible courtesy sub-tab whose exact text is the loaded `active_tab` (`אופן מקצועי`), inside the report frame, preferably under `התקבלות השירות`.

**Independent Test**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen3_distributions_match_golden`

### Implementation for User Story 4

- [X] T006 [US4] In `pages/public_inquiries/page.py`, add an English-named class constant for the section title `התקבלות השירות` next to the other screen 3 title constants, and add `_satisfaction_tab_locator(self, label: str) -> Locator`. Build candidates on a scope in this order, each with `exact=True` and `.filter(visible=True)`: `get_by_role("tab", name=label)`, `get_by_role("button", name=label)`, `get_by_role("link", name=label)`, then `get_by_text(label)`. Do not combine them with `.or_().first` (DOM order can pick a text node ahead of the control). Walk that order and return `_first_outside_tooltip` of the first candidate whose visible count is greater than zero. Try the scope from `_visual_container` for the section title first. If that call raises `AssertionError` or `Error`, or the host has no visible match, repeat the same walk on `self._report_frame()`. If nothing matches, return the frame `get_by_text(label, exact=True).filter(visible=True)` passed through `_first_outside_tooltip`, so the caller still has a locator to expect. Do not use the `ניווט בין עמודים` pattern. Do not substring-match (`אופן מקצועי` is not `מקצועיות`). Do not change `select_satisfaction_tab` in this task. Depends on T002 (research.md R18, FR-010).

- [X] T007 [US4] In `pages/public_inquiries/page.py`, rewrite `select_satisfaction_tab` so it does not call `_click_tab`. Call `_satisfaction_tab_locator(label)`, `expect` that locator to be visible with `timeout=self.timeout`, then click the visible `.ui-role-button-fill` whose box contains the label center. If no fill covers the label, `click(force=True)` the label. A normal click on the text run times out because that path intercepts the pointer. If `_visual_container` for the section title returns a host, hide a visible spinner inside that host with `locator("[class*='spinner'], [aria-busy='true']").filter(visible=True)` and `expect(...).to_be_hidden(timeout=self.timeout)` when the count is greater than zero; swallow `Error` the same way `_hide_card_spinner` does. If the host cannot be resolved, hide a visible spinner on the report frame the same way `_wait_for_report_settled` does. Then keep `expect(self._iframe_phrase_locator(label)).to_be_visible(timeout=self.timeout)`. The docstring stays English and still says the method does not load YAML. Do not edit `read_satisfaction`, `_wait_for_survey_cards`, `_wait_until_ready`, `_click_tab`, `_tab_locator`, `tests/sanity/public_inquiries_dashboard/test_data_validation.py`, or `data/hasbara/db_sanity.yaml`. Do not call `wait_for_timeout` or `networkidle`. Depends on T006 (FR-007, FR-009, FR-010, contract `select_satisfaction_tab`).

**Checkpoint**: The distributions test can click `אופן מקצועי`. A chart that still disagrees fails later with `ui=` and `golden=`, not with a missing page-rail element. Screen 1–4 navigation is unchanged.

---

## Phase 7: User Story 5 - Feedback investigation rows (Priority: P1)

**Goal**: Feedback rows stay on the shipped Show as a table path, including `comments`.

**Independent Test**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen4_feedback_rows_match_golden`

### Implementation for User Story 5

- [X] T008 [US5] Leave `read_feedback_rows`, `_FEEDBACK_HEADERS`, and `_wait_until_ready("screen_4")` in `pages/public_inquiries/page.py` as they shipped. Do not replace the screen 4 rendered gate. Do not edit `tests/sanity/public_inquiries_dashboard/test_data_validation.py` or `data/hasbara/db_sanity.yaml` (FR-008).

**Checkpoint**: Screen 4 is unchanged. The satisfaction locator does not run on this screen.

---

## Phase 8: User Story 6 - Freshness smoke stays green (Priority: P2)

**Goal**: `test_dashboard_updated_within_24_hours` still calls `verify_freshness`. This revision does not add a caption parser.

**Independent Test**: Read `tests/ui/public_inquiries_dashboard/test_dashboard_smoke.py` and confirm it still calls only `dashboard.verify_freshness()`.

### Implementation for User Story 6

- [X] T009 [P] [US6] Leave `tests/ui/public_inquiries_dashboard/test_dashboard_smoke.py` unchanged. `PublicInquiriesPage` in `pages/public_inquiries/page.py` must not define `verify_freshness` or parse `הדשבורד עודכן לאחרונה ב:` while the satisfaction locator is added (FR-014, FR-016).

**Checkpoint**: The smoke module stays the freshness gate.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: English comments, a page-only diff, and the distributions gate

- [X] T010 [P] Review `_satisfaction_tab_locator` and `select_satisfaction_tab` in `pages/public_inquiries/page.py`. Comments, locator names, wait conditions, method names, and docstrings are English. Hebrew remains only in the section-title constant. `_click_tab` and `_tab_locator` are unchanged (FR-010). Depends on T007.
- [X] T011 [P] Verify the diff is limited to `pages/public_inquiries/page.py`. `core/portal/`, `core/components/`, `data/hasbara/db_sanity.yaml`, `tests/sanity/public_inquiries_dashboard/test_data_validation.py`, and `tests/ui/public_inquiries_dashboard/test_dashboard_smoke.py` are unchanged. `התקבלות השירות` and `אופן מקצועי` do not appear under `core/`. `select_satisfaction_tab` does not call `_click_tab` (FR-015, AC-001, AC-005). Depends on T007.
- [ ] T012 Run `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen3_distributions_match_golden` per `specs/049-hasbara-ui-validation/quickstart.md`. The test must get past `select_satisfaction_tab` and compare `service_reception.responses`. A mismatch fails with the YAML path, `ui=`, and `golden=`. Requires portal auth and a live browser. Depends on T010 and T011.

**Checkpoint**: The courtesy sub-tab click no longer times out on the page rail. Fleet smoke is not required for this revision.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Already shipped. No edit
- **User Story 2 (Phase 4)**: Already shipped. No edit
- **User Story 3 (Phase 5)**: Already shipped. No edit
- **User Story 4 (Phase 6)**: Depends on T002. Owns the new locator and the `select_satisfaction_tab` rewrite in `pages/public_inquiries/page.py`
- **User Story 5 (Phase 7)**: Already shipped. No edit
- **User Story 6 (Phase 8)**: Already shipped. The smoke file stays untouched
- **Polish (Phase 9)**: T010 and T011 after T007. T012 last

### User Story Dependencies

- **User Story 1 (P1)**: Shipped. Independent of the satisfaction locator
- **User Story 2 (P1)**: Shipped. Does not edit KPI or chart methods
- **User Story 3 (P1)**: Shipped. Does not edit `_read_grid`
- **User Story 4 (P1)**: After T002. The only story that edits `pages/public_inquiries/page.py` in this revision
- **User Story 5 (P1)**: Shipped. Does not share the new locator
- **User Story 6 (P2)**: Shipped. Different file from the page edit

### Within Each User Story

- US1: no edit (T003)
- US2: no edit (T004)
- US3: no edit (T005)
- US4: add `_satisfaction_tab_locator` (T006), then switch `select_satisfaction_tab` off `_click_tab` (T007). The test file is not edited
- US5: no edit (T008)
- US6: no edit (T009)

### Parallel Opportunities

- T003, T004, T005, T008, and T009 are already shipped and do not edit the new locator
- T006 and T007 are not parallel: both edit `pages/public_inquiries/page.py`, and T007 calls the helper from T006
- T010 (comment review) and T011 (diff audit) can run together after T007
- T012 needs a live browser and runs after T010 and T011

---

## Parallel Example: User Story 4

```bash
# After T007, the review and the diff audit do not edit the page:
Task: "Review English comments on select_satisfaction_tab in pages/public_inquiries/page.py (T010)"
Task: "Confirm the diff is only pages/public_inquiries/page.py (T011)"
```

T006 and T007 are not parallel: both edit `pages/public_inquiries/page.py`.

---

## Implementation Strategy

### MVP First (User Story 1 is already shipped)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (page rail stays)
3. User Story 1 is already shipped — stop here only to re-check filters if the date fill was touched
4. Complete Phase 6: User Story 4
5. **STOP and VALIDATE**: `pytest tests/sanity/public_inquiries_dashboard/test_data_validation.py -m sanity -k test_hasbara_screen3_distributions_match_golden`

User Story 1 remains the product MVP for filters. This revision's increment is User Story 4, because that is the distributions test whose sub-tab click times out.

### Incremental Delivery

1. Setup + Foundational → the four report pages still use `_tab_locator`
2. User Story 4 → `select_satisfaction_tab` clicks the visible exact sub-tab and the distributions test can compare the bars
3. User Stories 1, 2, 3, 5, and 6 stay as shipped
4. Polish → English comments, page-only diff, and the distributions gate

### Parallel Team Strategy

One developer owns `pages/public_inquiries/page.py` (T006, T007). A second developer can confirm T003, T004, T005, T008, and T009 without editing that file. Nobody edits `core/`, the golden YAML, or the sanity test.

---

## Notes

- [P] tasks use different files and do not wait on an unfinished edit of the same file
- [US1]–[US6] map to spec.md in order
- Checked tasks are the shipped readers. Do not reopen them
- `test_hasbara_screen3_distributions_match_golden` already passes `service["active_tab"]`. Do not add a second tab loop and do not edit the YAML to remove the duplicate `active_tab` key
- Do not hard-code `105`, `63%`, or the other courtesy counts. The test reads `data/hasbara/db_sanity.yaml`
- The page-rail locator stays for screens 1–4. A bare `get_by_text` on `_tab_locator` would also match report titles
- `.filter(visible=True)` is required before the click. A hidden or tooltip copy of the same Hebrew is not the target
- Fleet smoke is not a gate. Layer 0 and Layer 2 are not edited
