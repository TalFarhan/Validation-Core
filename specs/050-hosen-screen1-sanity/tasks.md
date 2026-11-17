---
description: "Task list for resilience authority first-line cleanup"
---

# Tasks: Hosen Status Screen 1 YAML Sanity

**Input**: Design documents from `/specs/050-hosen-screen1-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/hosen-screen1-sanity.md, quickstart.md

**Tests**: The feature already has `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`. This amendment does not add a test file. Hosen smoke stays `dashboard.verify_freshness()`. Fleet smoke is not a gate: `core/` is not edited.

**Organization**: Screen 1 readers, the date combobox, the category SVG grade, the golden file, and the filter loop already exist. This list is the 2026-11-16 authority-cell amendment (research.md section 17). `_visible_resilience_rows` stores `authority` from `inner_text()`, so the key is `קרית מלאכי\nעיצוב מותנה נוסף` while `data/hosen/db_sanity.yaml` has `קרית מלאכי`. `_assert_rows` only indexes that stored string. Tasks follow user stories in spec.md. US4 owns the first-line split. US1 keeps the existing comparison. US2 and US3 keep their readers.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page: `pages/hosen_status/page.py` (`HosenStatusPage._visible_resilience_rows`)
- Golden record (do not edit): `data/hosen/db_sanity.yaml` (`screen_1_landing.resilience_scores[].authority`, including `קרית מלאכי`)
- Sanity test (do not edit): `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` (`_assert_rows`)
- Existing smoke (do not edit): `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`
- Contract: `specs/050-hosen-screen1-sanity/contracts/hosen-screen1-sanity.md`
- OFF-LIMITS: `core/portal/`, `core/components/` (including `core/components/virtual_grid.py`), `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, those reports' pages and tests, `db/`, root `conftest.py`

Do not add `pages/hosen_status/__init__.py`. Comments inside functions stay English. Hebrew stays in locator constants or the YAML. Do not call `sleep`, `wait_for_timeout`, or `page.wait_for_load_state("networkidle")`. Do not add `split("\n")` inside module-level `_plain`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm this amendment is only the resilience authority line on the Hosen page

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/050-hosen-screen1-sanity"` and that this amendment edits `pages/hosen_status/page.py` only. Git checkout stays `feature/reportportal-integration`. Do not edit `data/hosen/db_sanity.yaml`, `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, or `core/components/virtual_grid.py`.
- [X] T002 [P] Inventory without editing. In `pages/hosen_status/page.py`, confirm `_visible_resilience_rows` assigns `authority = _plain(cells.nth(authority_index).inner_text(timeout=500) or "")` and assigns `score` from `_plain` of the full score cell. In `data/hosen/db_sanity.yaml`, confirm `screen_1_landing.resilience_scores` keys `קרית מלאכי` with no second line. In `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, confirm `_assert_rows` indexes `_plain(row.get(key, ""))` and `_ROW_KEY["resilience_scores"]` is `authority`.

**Checkpoint**: The dirty key site is known. No files changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Keep the shared text helper whole so the first-line rule stays on the authority cell.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 In `pages/hosen_status/page.py`, leave `def _plain` as bidi-mark removal plus `text.strip()`. Do not add `split("\n")` inside `_plain`. Do not edit `_visible_resilience_rows` in this task. The later authority assignment will call `_plain` on the first line only.

**Checkpoint**: `_plain` still trims one string. The authority cell is unchanged.

---

## Phase 3: User Story 1 - Landing screen matches the golden YAML (Priority: P1) 🎯 MVP

**Goal**: The existing sanity comparison still matches each golden field after the page publishes a clean `authority`.

**Independent Test**: `test_hosen_screen1_matches_golden` in `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`

### Implementation for User Story 1

- [X] T004 [US1] In `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, leave `test_hosen_screen1_matches_golden`, `_assert_rows`, and `_plain` as they are. `_assert_rows` must keep indexing `_plain(row.get(key, ""))` for `resilience_scores`. Do not split lines in the test. If the file already does this, do not edit it.

**Checkpoint**: The test still fails a dirty `authority` and passes once the page publishes `קרית מלאכי`.

---

## Phase 4: User Story 2 - Survey status counts and missing authorities (Priority: P1)

**Goal**: Survey counts and missing-authority names stay full cell text.

**Independent Test**: The `survey_status` object inside `test_hosen_screen1_matches_golden`

### Implementation for User Story 2

- [X] T005 [US2] In `pages/hosen_status/page.py`, leave `_visible_missing_rows` and `_read_survey_status` as they are. The missing-authority cell stays `_plain(cells.nth(cell_index).inner_text(timeout=500) or "")` with no `split("\n")`. Do not edit `data/hosen/db_sanity.yaml`.

**Checkpoint**: Missing authorities are not cut to the first line.

---

## Phase 5: User Story 3 - National assessment and eight category KPIs (Priority: P1)

**Goal**: Category grades stay on `.value tspan` via `text_content()`, published as `score` and `trend_direction`.

**Independent Test**: The `kpis` object inside `test_hosen_screen1_matches_golden`

### Implementation for User Story 3

- [X] T006 [US3] In `pages/hosen_status/page.py`, leave `_svg_grade`, `_read_card`, and `_read_kpis` as they are. `_svg_grade` still reads `.value tspan` with `text_content()` and does not call `inner_text()`. Category dicts stay `title`, `score`, and `trend_direction`. The national card stays `percentage` and `trend`. Do not edit `core/components/kpi.py`.

**Checkpoint**: The authority cleanup does not change a category grade.

---

## Phase 6: User Story 4 - Resilience scores and selected filters (Priority: P1)

**Goal**: `resilience_scores[].authority` is the first line of the authority cell, so `קרית מלאכי` matches the golden file.

**Independent Test**: The `resilience_scores` list and the `filters` map inside `test_hosen_screen1_matches_golden`

### Implementation for User Story 4

- [X] T007 [US4] In `_visible_resilience_rows` in `pages/hosen_status/page.py`, replace the authority assignment with `extracted_text = cells.nth(authority_index).inner_text(timeout=500) or ""` and `authority = _plain(extracted_text.split("\n")[0])`. Leave the score assignment as `_plain(cells.nth(score_index).inner_text(timeout=500) or "")`. Leave `_read_resilience_scores` on `collect_virtualized_rows` with `lambda row: row.get("authority", "")`. Leave `select_screen_1_filter("district", value)` and `select_screen_1_filter("subdistrict", value)` on `_select_smart_filter`. Do not edit `data/hosen/db_sanity.yaml` or `core/components/virtual_grid.py`. Do not read row color from a `canvas`.

**Checkpoint**: A cell whose text is `קרית מלאכי\nעיצוב מותנה נוסף` publishes `authority` `קרית מלאכי`. The score cell is still the full plain text.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Run the sanity check from quickstart.md and keep the diff on the authority assignment

- [ ] T008 [P] Run `pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` from the repo root. The body in `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` must still be `dashboard.verify_freshness()`.
- [ ] T009 Run `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` from the repo root. `resilience_scores` must match `קרית מלאכי` and must not fail with `קרית מלאכי\nעיצוב מותנה נוסף`. A mismatch must name `hosen_dashboard.screen_1_landing.resilience_scores`.
- [ ] T010 Confirm the diff for this amendment does not edit `core/`, `data/hosen/db_sanity.yaml`, `data/hasbara/`, `data/credit/`, `data/alerts/`, those reports' page and test modules, `db/`, `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`, or `tests/ui/hosen_status_dashboard/`. In `pages/hosen_status/page.py`, `_visible_resilience_rows` sets `authority` from `_plain(extracted_text.split("\n")[0])`, `def _plain` has no `split`, and the score cell is not split. Comments inside `_visible_resilience_rows` are English. Fleet smoke is not required.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Story 1 (Phase 3)**: Depends on T003. No code edit. The live `קרית מלאכי` check in the independent test needs T007.
- **User Story 2 (Phase 4)**: Depends on T003. The survey reader stays as it is.
- **User Story 3 (Phase 5)**: Depends on T003. The SVG reader stays as it is.
- **User Story 4 (Phase 6)**: Depends on T003. This is the code change.
- **Polish (Phase 7)**: T009 needs T007. T008 can run any time the smoke file is untouched. T010 runs last.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after T003. T004 does not edit the test. The MVP proof is the sanity test after T007.
- **User Story 2 (P1)**: Starts after T003. No survey code change.
- **User Story 3 (P1)**: Starts after T003. No KPI code change.
- **User Story 4 (P1)**: Starts after T003. T007 is the only edit to `_visible_resilience_rows`.

### Within Each User Story

- T002 before T003 (know the dirty assignment, the golden `קרית מלאכי`, and `_assert_rows` before freezing `_plain`).
- T003 before T004, T005, T006, and T007.
- T007 before T009.
- T009 before T010.

### Parallel Opportunities

- T001 and T002 can run together (read-only, different files).
- T004, T005, and T006 confirm files that T007 must not rewrite. Do not edit `pages/hosen_status/page.py` in parallel with T007.
- T008 touches a different file from T007 and can run once the smoke module is confirmed unchanged.

---

## Parallel Example: User Story 4

```bash
# After T003, the code change is one assignment in pages/hosen_status/page.py:
Task: "T007 authority = _plain(extracted_text.split(\"\\n\")[0]) in pages/hosen_status/page.py"

# Different file, safe once smoke is confirmed untouched:
Task: "T008 Run pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py"
```

---

## Implementation Strategy

### MVP First (User Story 4 authority, checked by User Story 1)

1. Complete Phase 1: Setup.
2. Complete Phase 2: `def _plain` in `pages/hosen_status/page.py` stays bidi removal plus `strip`.
3. Complete Phase 6: User Story 4 (`authority` is the first line of the cell).
4. **STOP and VALIDATE**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`.
5. `קרית מלאכי` matches the golden file. The score cell is still the full plain text.

### Incremental Delivery

1. Setup + Foundational → `_plain` is unchanged and `core/` is untouched.
2. User Story 1 → the sanity test still indexes the published `authority`.
3. User Story 2 → missing-authority cells stay whole.
4. User Story 3 → category `score` still comes from `.value tspan`.
5. User Story 4 → the resilience authority key drops the accessibility line (the failing assertion).
6. Polish → Hosen smoke, sanity pytest, diff check.

### Parallel Team Strategy

One developer owns `pages/hosen_status/page.py` for T003, T005, T006, and T007. A second developer can take T002 and T008 (read-only on the YAML, the sanity test, and the smoke module). Do not split T007.

---

## Notes

- [P] tasks = different files, no dependencies on an unfinished edit.
- [US1]–[US4] map to spec.md. Setup, Foundational, and Polish have no story label.
- The code change is the authority assignment inside `_visible_resilience_rows` in `pages/hosen_status/page.py`.
- Commit after each task or logical group.
- Stop at the US4 checkpoint and run the sanity test before polishing.
- Avoid: `split("\n")` inside `_plain`, a line split in `_assert_rows` or on the score cell, rewriting `data/hosen/db_sanity.yaml` to include `עיצוב מותנה נוסף`, and teaching `collect_virtualized_rows` a text cleaner.
