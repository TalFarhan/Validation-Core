---
description: "Task list for 041-fix-dashboard-data-rendering"
---

# Tasks: Fix Skipped Tests and Load Errors for Alerts and Status Dashboards

**Input**: Design documents from `specs/041-fix-dashboard-data-rendering/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dashboard-data-rendering.md, quickstart.md

**Tests**: The deliverables are themselves the existing sanity tests. No new TDD test scaffolding is added. This slice does **not** edit `core/portal`, `ReportShell`, or shared page-object navigation — it overrides `_report_ready_locator()` on a domain page and adds a domain method — so the fleet smoke suite is a non-gating safety check, not a mandatory gate.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths are included in each task

## Path Conventions

Validation Core layout: `pages/<report>/` (domain pages), `data/<report>/` (Layer 3 golden records), `tests/sanity/<suite>/` (sanity tests), `tests/ui/fleet_dashboard/` (fleet smoke).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working context before editing.

- [X] T001 Confirm `.specify/feature.json` points to `specs/041-fix-dashboard-data-rendering` and the git checkout stays on `feature/reportportal-integration` (no branch switch per plan.md)
- [X] T002 [P] Re-read the target files to confirm current state: `pages/alerts_analysis/population_page.py` (`_report_ready_locator`, `TOTAL_CARD`, `before_report_ready_check`), `pages/status_picture/status_picture_page.py` (`set_date_range`, `_OPERATION_RANGES`, `_wait_until_gauge_changes`, `_slicer`), and both sanity modules under `tests/sanity/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The golden-record `operation` key is required before Status Picture can select by name.

**⚠️ CRITICAL**: T003 blocks US2 and US3.

- [X] T003 Add `operation: "עם כלביא"` under `dashboard_sanity_checks.screen_1_status_picture` in `data/alerts/db_sanity_am_kalavi.yaml`, immediately below `description` and above `date_range`; change no existing metric or `date_range` value (additive only)

**Checkpoint**: Golden record exposes the operation name; user-story work can begin.

---

## Phase 3: User Story 1 - Alerts Analysis charts render after the golden range is applied (Priority: P1) 🎯 MVP

**Goal**: `navigate()` reaches the population page under the default empty filter, then the golden `date_range` makes the Screen 2 charts render.

**Independent Test**: With auth, run `pytest -m sanity tests/sanity/alerts_analysis_dashboard/test_data_validation.py` — the suite reaches its assertions without `LoadTimeoutError` and no chart test skips with an empty-reader message.

### Implementation for User Story 1

- [X] T004 [US1] In `pages/alerts_analysis/population_page.py`, change `_report_ready_locator()` to return `self._iframe_phrase_locator(self.TOTAL_CARD)` instead of `self.DISTRICT_CHART`; keep the method's English docstring/comment explaining it is a filter-independent Screen-2 anchor
- [X] T005 [US1] In `pages/alerts_analysis/population_page.py`, leave `before_report_ready_check()` using `DISTRICT_CHART` for the Screen 1 → Screen 2 page switch; add a short English comment noting the ready anchor and the page-switch probe are intentionally different
- [X] T006 [US1] Audit `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`: confirm every chart-reading test calls `_apply_golden_range(population_dashboard)` (which reads `screen_2_alerts_analysis.date_range` and calls `set_date_range`) before any reader; add the call where missing; ensure no date literal appears in a test body
- [X] T007 [US1] Verify the negative path by inspection: a never-rendering ready anchor still raises `LoadTimeoutError` from `navigate()` (no code change — confirm the raise path in `core/portal/page.py` is unaffected by the anchor swap)

**Checkpoint**: Screen 2 navigation succeeds on a cold empty filter; chart tests assert against the golden values.

---

## Phase 4: User Story 2 - Status Picture selects the operation by name (Priority: P1)

**Goal**: Screen 1 setup selects `עם כלביא` directly on the `FilterName` slicer (name read from the golden record), replacing the date→operation reverse mapping on the golden path.

**Independent Test**: With auth, run `pytest -m sanity tests/sanity/status_picture_dashboard/test_status_picture_validation.py` — the operation is selected by name and `read_cards`, `read_alerts_by_category`, `read_top_10_settlements` return populated maps.

**Depends on**: T003 (golden `operation` key).

### Implementation for User Story 2

- [X] T008 [US2] In `pages/status_picture/status_picture_page.py`, add additive method `select_operation(self, name: str) -> None`: dismiss overlay, capture the warning-zones gauge value, call `self._slicer.select("date_range", name)`, then wait for the gauge to change and settle via `_wait_until_gauge_changes`; English comments only
- [X] T009 [US2] In `select_operation`, surface a clear `AssertionError` naming the missing operation when `name` is not a selectable slicer option (do not swallow the `Slicer.select` failure)
- [X] T010 [US2] In `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`, change `_apply_golden_range(page)` to read `screen["operation"]` and call `page.select_operation(screen["operation"])` instead of `page.set_date_range(start, end)`; keep returning the Screen 1 block; English comments only
- [X] T011 [US2] Confirm `set_date_range`, `_OPERATION_RANGES`, and `_date_fields_visible()` remain intact for non-golden callers (no deletion); only the golden path stops depending on them

**Checkpoint**: Status Picture populates its visuals from a named operation selection.

---

## Phase 5: User Story 3 - Skipped tests resolve and required DOM renders (Priority: P1)

**Goal**: With data loaded, the empty-reader `pytest.skip` paths stop firing while the skip guards remain as a safety net.

**Independent Test**: Run both sanity modules with auth — no test skips with an empty-reader/missing-reader message when data is present.

**Depends on**: US1 (T004–T006) and US2 (T008–T010).

### Implementation for User Story 3

- [X] T012 [US3] Verify the skip guards are preserved (not deleted) in both modules: `_require_card`/empty-reader skips in `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` and the `if not actual: pytest.skip(...)` guards in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
- [ ] T013 [US3] With auth, run `pytest -m sanity tests/sanity/alerts_analysis_dashboard/test_data_validation.py tests/sanity/status_picture_dashboard/test_status_picture_validation.py` and confirm no empty-reader/missing-reader skips occur; capture the result CSV/HTML under `result/`

**Checkpoint**: Previously-skipped chart tests now assert against the golden record.

---

## Phase 6: User Story 4 - Report-ready locator is a consistently visible element (Priority: P1)

**Goal**: Each Alerts page awaits a consistently visible, filter-independent anchor in `navigate()`.

**Independent Test**: Inspect `_report_ready_locator()` on both Alerts pages; the population anchor is `TOTAL_CARD` (not `DISTRICT_CHART`) and the status-picture anchor is the warning-zones gauge card.

**Depends on**: US1 (T004).

### Implementation for User Story 4

- [X] T014 [US4] Confirm `pages/alerts_analysis/population_page.py` `_report_ready_locator()` returns `TOTAL_CARD` (from T004) and document in an English comment why it is filter-independent and Screen-2-specific
- [X] T015 [P] [US4] Confirm `pages/status_picture/status_picture_page.py` `_report_ready_locator()` returns the `UNDER_FIRE_CARD` gauge anchor; add a one-line English comment noting it is already a consistently visible Screen-1 element (no behavioral change)

**Checkpoint**: Both pages' navigation readiness is decoupled from filtered chart data.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final consistency checks across the slice.

- [X] T016 [P] Audit all new/edited functions in `pages/alerts_analysis/population_page.py`, `pages/status_picture/status_picture_page.py`, and both sanity modules for English-only in-function comments (FR-009)
- [X] T017 [P] Confirm no fleet module, `core/portal`, `core/components`, or root `conftest.py` was edited, and that the only `data/` change is the Screen 1 `operation` key (FR-008)
- [ ] T018 Run `quickstart.md` validation: execute both run commands and verify the expected results and negative checks (broken anchor still raises `LoadTimeoutError`; unknown `operation` raises a named assertion)
- [ ] T019 Non-gating safety check: run `pytest tests/ui/fleet_dashboard/` and confirm it stays green (unaffected — no Layer 0 or fleet-navigation change)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2 / T003)**: Blocks US2 and US3.
- **US1 (Phase 3)**: After Setup; independent of US2.
- **US2 (Phase 4)**: After T003.
- **US3 (Phase 5)**: After US1 and US2 (needs data loading from both).
- **US4 (Phase 6)**: After US1 (shares the population anchor change).
- **Polish (Phase 7)**: After all desired stories.

### User Story Dependencies

- **US1 (P1)**: Independent — the MVP root-cause fix.
- **US2 (P1)**: Needs the golden `operation` key (T003).
- **US3 (P1)**: Verification that depends on US1 + US2 landing.
- **US4 (P1)**: Confirms/anchors the US1 change plus the status-picture anchor.

### Within Each User Story

- Code edits before verification/run tasks.
- Same-file tasks are sequential (e.g., T004/T005/T014 all touch `population_page.py`).

### Parallel Opportunities

- T002 (read-only) runs alongside T001.
- Across stories after T003: US1 code (T004–T006) and US2 code (T008–T010) touch different files and can proceed in parallel by different developers.
- T015, T016, T017 are [P] (different files / read-only audits).
- Same-file edits (`population_page.py`: T004, T005, T014) must NOT run in parallel.

---

## Parallel Example: after Foundational

```bash
# Developer A (US1 — population page + alerts sanity):
Task: "T004 Change _report_ready_locator() to TOTAL_CARD in pages/alerts_analysis/population_page.py"
Task: "T006 Audit golden-range application in tests/sanity/alerts_analysis_dashboard/test_data_validation.py"

# Developer B (US2 — status picture page + status sanity):
Task: "T008 Add select_operation() in pages/status_picture/status_picture_page.py"
Task: "T010 Refactor _apply_golden_range to select by name in tests/sanity/status_picture_dashboard/test_status_picture_validation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup.
2. Phase 2: Foundational (T003).
3. Phase 3: US1 — retarget the population ready anchor and audit the golden-range application.
4. **STOP and VALIDATE**: Screen 2 sanity reaches assertions without `LoadTimeoutError`.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 → Screen 2 unblocked (MVP).
3. US2 → Screen 1 selects by operation name.
4. US3 → confirm skips resolved across both screens.
5. US4 → confirm both ready anchors are filter-independent.
6. Polish → English-comment + scope audits, quickstart + fleet-smoke checks.

---

## Notes

- [P] = different files, no dependencies.
- The timeout budget is unchanged (`self.timeout = 120_000` already present).
- Skip guards stay as a safety net — do not delete them.
- Commit after each task or logical group (optional `/speckit-git-commit` hook).
