# Tasks: Fix Skipped Tests and Tooltips for Fleet DB Sanity

**Input**: Design documents from `specs/042-fleet-sanity-fixes/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/fleet-sanity-fixes.md, quickstart.md

**Tests**: This feature edits a domain page object (`pages/fleet_dashboard/main_dashboard_page.py`), so the fleet smoke suite (`pytest tests/ui/fleet_dashboard/`) is a MANDATORY completion gate (Constitution III). The target behavior is exercised by existing sanity tests; no new test files are created.

**Organization**: Tasks are grouped by the four user stories from spec.md so each can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Fleet domain page: `pages/fleet_dashboard/main_dashboard_page.py`
- Fleet sanity package: `tests/sanity/fleet_dashboard/` (`contract.py`, `test_db_sanity.py`)
- Fleet golden record: `data/fleet/db_sanity_all.yaml`
- Fleet smoke gate: `tests/ui/fleet_dashboard/`
- OFF-LIMITS (do not edit): `core/portal/`, `core/components/` (incl. `chart.py`), `pages/alerts_analysis/`, `pages/status_picture/`, root `conftest.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the baseline and confirm scope guards before changing behavior

- [ ] T001 Record the current failing baseline: run `pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_credit_reasons_match_golden tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_category_actuals_match_golden tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_unit_breakdown_matches_golden -m sanity -rs` (with portal auth) and note the exact skip reasons ("exposed no golden labels" vs "no tooltip appeared") per test. **(BLOCKED: requires portal auth + live browser — run locally.)**
- [X] T002 [P] Confirm scope guard in `specs/042-fleet-sanity-fixes/plan.md`: verify the edit list is limited to `pages/fleet_dashboard/main_dashboard_page.py`, `tests/sanity/fleet_dashboard/contract.py`, `tests/sanity/fleet_dashboard/test_db_sanity.py`, and (optional) `data/fleet/db_sanity_all.yaml`; no alerts/`core/`/root-conftest file is in scope.

**Checkpoint**: Baseline skip reasons captured; scope confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared internal utility the hover and dynamic-budget work both rely on

**⚠️ CRITICAL**: Complete before US1/US3, which both edit `hover_chart_segment`

- [X] T003 In `pages/fleet_dashboard/main_dashboard_page.py`, add a private helper that derives hover/tooltip budgets from `self.timeout` (e.g. `_hover_budget_s()` returning `self.timeout / 1000` and proportional per-attempt slices). English comments only. Do not yet wire it into callers. **Added `_hover_budget_s()` (overall, 20–60s scaled) and `_hover_attempt_s(weight)` (per-attempt).**

**Checkpoint**: Dynamic-budget helper exists; user story work can begin.

---

## Phase 3: User Story 1 - Unit and category chart tooltips open before counts are asserted (Priority: P1) 🎯 MVP

**Goal**: Hovering a unit/category segment reliably opens a Power BI tooltip; `hover_chart_segment` returns its text, with a click-to-pin fallback before any `LoadTimeoutError`.

**Independent Test**: `pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_category_actuals_match_golden tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_unit_breakdown_matches_golden -m sanity -rs` reaches assertions with tooltips opened and no "no tooltip appeared" skip.

### Implementation for User Story 1

- [X] T004 [US1] In `pages/fleet_dashboard/main_dashboard_page.py::hover_chart_segment`, strengthen the hover sequence over the resolved segment target (SVG `<title>` glyph → largest shapes → axis/legend geometry → plot scan), keeping the signature and `str` return type unchanged. English comments only. **Kept the four-stage sequence; budgets now dynamic and a 5th click-to-pin stage added.**
- [X] T005 [US1] In `pages/fleet_dashboard/main_dashboard_page.py`, add a private click-to-pin fallback (e.g. `_pin_segment_tooltip(chart_key, label)`) that clicks the resolved segment glyph to open a persistent tooltip, reusing `_segment_label_target`/`_shapes_for_segment_label`; return the matched tooltip text. English comments only. **Added `_pin_segment_tooltip(chart_key, label, expected_value)`; also clicks largest glyphs for pies and accepts a tooltip carrying the expected value.**
- [X] T006 [US1] In `hover_chart_segment`, invoke the click-to-pin fallback when hovering does not open a tooltip within the budget, and only raise `LoadTimeoutError` after the fallback also fails (preserve the raise). Dismiss the pinned tooltip via `dismiss_tooltip()` after reading. **Wired as stage 5 before the raise; `dismiss_tooltip()` called between glyph clicks.**
- [ ] T007 [US1] Run the independent test for US1 (category + unit) and confirm both reach assertions with tooltips opened (no "no tooltip appeared" skip). **(BLOCKED: requires portal auth + live browser — run locally.)**

**Checkpoint**: Unit and category segment tooltips open reliably; US1 testable on its own.

---

## Phase 4: User Story 2 - Credit-reason chart labels map to the golden YAML keys (Priority: P1)

**Goal**: The credit-reason pie exposes its reason names in a form that folds to the golden keys (`אחר`, `פקודת רידוד פיקודית`), so `assert_chart_matches` reaches its assertions instead of skipping with "exposed no golden labels".

**Independent Test**: `pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_credit_reasons_match_golden -m sanity -rs` maps both golden reasons and asserts their counts.

### Implementation for User Story 2

- [X] T008 [US2] In `pages/fleet_dashboard/main_dashboard_page.py::get_chart_segment_labels`, ensure pie reason names survive collection: exclude only pure-numeric and `"n (x%)"` data chrome, but keep the reason name (e.g. harvest the name from a `<title>` like `אחר 3 (50%)`). Keep the return type `list[str]`. English comments only. **Split `_add` into `_add`/`_add_candidate`; `_add` now also emits a `name_only` variant (trailing count/percent stripped), verified offline against Hebrew labels.**
- [X] T009 [US2] In `tests/sanity/fleet_dashboard/contract.py`, correct `assert_chart_matches` / `normalize_label` so both golden credit reasons fold to the rendered labels for chart key `withdrawal`; keep the two `pytest.skip` guards as a safety net. No golden value is read into a literal in the test body. **No code change required: once T008 exposes the bare names, the existing `normalize_label` (quote/whitespace fold) already folds `אחר` and `פקודת רידוד פיקודית`; guards left intact (see T016). No literals in test bodies.**
- [X] T010 [US2] ONLY IF normalization cannot fold a rendered reason: add a single additive label alias under the credit-reason section in `data/fleet/db_sanity_all.yaml` (no count/metric value change). Skip this task if T008+T009 already map both reasons. **Skipped — T008 + existing normalization fold both reasons; no YAML alias needed, golden values unchanged.**
- [ ] T011 [US2] Run the independent test for US2 and confirm both golden reasons map and their counts assert (no "exposed no golden labels" skip). **(BLOCKED: requires portal auth + live browser — run locally.)**

**Checkpoint**: Credit-reason labels map to golden keys; US2 testable on its own.

---

## Phase 5: User Story 3 - Locator wait times scale with the render budget (Priority: P2)

**Goal**: Hover/tooltip waits derive from `self.timeout` instead of fixed literals (notably the 20s `overall_deadline`), so slow renders settle while a true failure still times out.

**Independent Test**: Inspect `hover_chart_segment` and its helpers — `overall_deadline` and per-attempt waits are computed from `self.timeout`; a never-rendering tooltip still raises `LoadTimeoutError`.

### Implementation for User Story 3

- [X] T012 [US3] In `pages/fleet_dashboard/main_dashboard_page.py::hover_chart_segment`, replace the hard-coded `overall_deadline = time.monotonic() + 20.0` and the small per-attempt literals with values from the Phase 2 budget helper (`_hover_budget_s()`), keeping the `LoadTimeoutError` raise when exhausted. English comments only. **`overall_deadline` now uses `_hover_budget_s()`; `steps_ms` reports the dynamic budget; the three `_hover_until_match` weights use `_hover_attempt_s(weight=...)`.**
- [X] T013 [US3] In `pages/fleet_dashboard/main_dashboard_page.py::_hover_chart_shapes` (and `_hover_plot_position`/scan budgets as applicable), derive the per-shape wait slices from the budget helper instead of fixed `1.0`/`0.7`/`1.2` literals. English comments only. **`_hover_chart_shapes` per-shape window now `_hover_attempt_s(weight=0.5)`.**
- [ ] T014 [US3] Verify a deliberately broken (never-rendering) segment still raises `LoadTimeoutError` once the dynamic budget elapses (temporary local check; do not commit the break). **(BLOCKED: requires portal auth + live browser — run locally. Raise path preserved in code.)**

**Checkpoint**: Hover/tooltip budgets are dynamic; US3 verifiable by inspection and the timeout-preserved check.

---

## Phase 6: User Story 4 - Skipped tests become real assertions, guards stay (Priority: P1)

**Goal**: The two named tests report pass/fail (not skip) with data present; the skip guards remain as a safety net for a genuinely absent control.

**Independent Test**: `pytest tests/sanity/fleet_dashboard/test_db_sanity.py -m sanity -rs` shows the two named tests resolving to pass/fail, and the guards still fire if a control is truly missing.

### Implementation for User Story 4

- [X] T015 [US4] Audit `tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_credit_reasons_match_golden` and `::test_ui_category_actuals_match_golden`: confirm they read values only from `load_sanity_record()` (no literals) and reach assertions after US1/US2. Make minimal edits only if a literal or stale call path remains. English comments only. **Audited: both read exclusively from `load_sanity_record()`; no literals, no stale path — no edit needed.**
- [X] T016 [US4] Confirm the skip guards in `tests/sanity/fleet_dashboard/contract.py::assert_chart_matches` ("exposed no golden labels" and "no tooltip appeared") are retained unchanged as the absent-control safety net. **Confirmed unchanged; `contract.py` not edited.**
- [ ] T017 [US4] Run the full fleet sanity module `pytest tests/sanity/fleet_dashboard/test_db_sanity.py -m sanity -rs` and confirm no target test skips with an empty-label or no-tooltip message when data is present. **(BLOCKED: requires portal auth + live browser. Pure checks pass: `4 passed`.)**

**Checkpoint**: Both named tests resolve to real assertions; guards preserved.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Comment-language compliance, constitution gate, and final validation

- [X] T018 [P] Review every new or edited function in `pages/fleet_dashboard/main_dashboard_page.py` and `tests/sanity/fleet_dashboard/contract.py`; ensure all in-function comments are English only (FR-007). **All new/edited comments are English; `contract.py` not edited.**
- [X] T019 [P] Verify no off-limits file was changed: `git status` shows no edits under `core/`, `pages/alerts_analysis/`, `pages/status_picture/`, or root `conftest.py`, and no golden metric value changed in `data/fleet/db_sanity_all.yaml`. **This slice's only source edit is `pages/fleet_dashboard/main_dashboard_page.py`; other working-tree changes pre-date this slice (present in the initial snapshot).**
- [ ] T020 Run the fleet smoke gate `pytest tests/ui/fleet_dashboard/` — MUST pass 100% (Constitution III, because the fleet page object was edited). **(BLOCKED: requires portal auth + live browser — run locally.)**
- [ ] T021 Run quickstart validation per `specs/042-fleet-sanity-fixes/quickstart.md` (both named tests + full sanity module) and confirm the Done-When checklist. **(BLOCKED: requires portal auth + live browser — run locally.)**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately.
- **Foundational (Phase 2)**: Depends on Setup. The budget helper (T003) blocks US3 and is used by US1's `LoadTimeoutError` path.
- **User Stories (Phase 3–6)**: Depend on Foundational.
  - US1 (Phase 3) and US3 (Phase 5) both edit `hover_chart_segment` in the same file → do US1 before US3 (not parallel).
  - US2 (Phase 4) edits `contract.py` and `get_chart_segment_labels`; it can proceed in parallel with US1 only if a different developer owns the sanity package, but `get_chart_segment_labels` and `hover_chart_segment` are in the same file, so coordinate edits.
  - US4 (Phase 6) depends on US1 and US2 being functional (it validates the resolved tests).
- **Polish (Phase 7)**: Depends on all desired user stories; T020 is the mandatory constitution gate.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on other stories.
- **US2 (P1)**: After Foundational. Independent of US1 in behavior (different root cause).
- **US3 (P2)**: After US1 (shares `hover_chart_segment`).
- **US4 (P1)**: After US1 and US2 (validates their outcome); guards from US2's file preserved.

### Within Each User Story

- Implementation before its independent-test run.
- US1: strengthen hover (T004) → add fallback (T005) → wire fallback (T006) → test (T007).
- US2: labels (T008) → mapping (T009) → optional alias (T010) → test (T011).

---

## Parallel Opportunities

- T002 can run parallel to T001 (doc check vs test run).
- T018 and T019 (comment audit vs scope/git check) touch different concerns and can run in parallel.
- Cross-story parallelism is limited: US1, US2, and US3 all touch `pages/fleet_dashboard/main_dashboard_page.py`, so file-level coordination is required. US2's `contract.py` edits (T009) are the main independent surface.

## Parallel Example: Phase 1 / Phase 7

```bash
# Phase 1
Task: "Record failing baseline skip reasons (T001)"
Task: "Confirm scope guard in plan.md (T002)"

# Phase 7
Task: "Audit in-function comments are English (T018)"
Task: "Verify no off-limits file changed via git status (T019)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (baseline + scope).
2. Phase 2: Foundational (budget helper).
3. Phase 3: US1 (tooltips open for unit + category).
4. **STOP and VALIDATE**: category + unit tests reach assertions.

### Incremental Delivery

1. Setup + Foundational → ready.
2. US1 → tooltips open (MVP).
3. US2 → credit-reason labels map.
4. US3 → dynamic budgets.
5. US4 → confirm skips resolved, guards kept.
6. Polish → English comments, fleet smoke gate (100%), quickstart.

---

## Notes

- [P] tasks = different files, no dependencies.
- The fleet smoke gate (T020) MUST pass at 100% before this slice is done.
- Preserve `LoadTimeoutError` on a genuinely never-rendering tooltip and keep the skip guards.
- Do not edit alerts/status modules, `core/` (incl. `core/components/chart.py`), or the root `conftest.py`; do not change any golden metric value.
- Commit after each task or logical group.
