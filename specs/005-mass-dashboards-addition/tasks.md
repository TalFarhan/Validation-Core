---

description: "Task list for Mass Dashboards Addition — Layer 0 freshness smoke for four new reports"
---

# Tasks: Mass Dashboards Addition — Layer 0 Freshness Smoke

**Input**: Design documents from `/specs/005-mass-dashboards-addition/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/layer0-report-binding.md, quickstart.md

**Tests**: Feature explicitly adds `test_dashboard_updated_within_24_hours` in each new suite. Layer 0 is not changed, so fleet smoke is not a blocking gate unless `core/` is edited. New suites are binding gates; temporary ready locators may fail until live-run feedback.

**Organization**: Confirm Layer 0 host, then US1–US4 (one report each). The four stories touch different files and MAY run in parallel after T003.

**Constitution**: v1.2.0 — zero new-report leakage in `core/`; inherit `ReportShell`; no JSON/slicer; no `pages/`; no `.env`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: [US1], [US2], [US3], [US4] on user-story tasks only
- Include exact file paths in descriptions

## Path Conventions

- Layer 0 (read-only): `core/portal/page.py`
- Alerts Analysis: `tests/ui/alerts_analysis_dashboard/`
- Marsal: `tests/ui/marsal_dashboard/`
- Authorities Status: `tests/ui/authorities_status_dashboard/`
- Hosen Status: `tests/ui/hosen_status_dashboard/`
- Fleet fixture (read-only): `conftest.py`
- Do not create: `pages/<report>/`
- Do not edit: `.env`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing Layer 0 host and fleet fixture without moving behavior

- [x] T001 Confirm `ReportShell` in `core/portal/page.py` already exposes `_report_ready_locator`, `_iframe_phrase_locator`, `_catalog_search_term` (`getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM`), and `verify_freshness`; do not edit `core/portal/page.py`
- [x] T002 [P] Confirm root `dashboard` fixture in `conftest.py` still returns `MainDashboardPage`; do not edit `conftest.py`, `tests/ui/fleet_dashboard/`, `pages/`, or `.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ignore files and Layer 0 contract are already in place; confirm before adding suites

**⚠️ CRITICAL**: No new page objects until this phase is complete

- [x] T003 [P] Verify `.gitignore` includes Python essentials (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env`, `auth_state.json`); append only if missing

**Checkpoint**: A `ReportShell` subclass with `DASHBOARD_SEARCH_TERM` searches that product. Fleet still uses settings. User stories can begin.

---

## Phase 3: User Story 1 - Alerts Analysis Layer 0 freshness smoke (Priority: P1) 🎯 MVP

**Goal**: Open Alerts Analysis through `ReportShell`, wait on temporary iframe phrase `ניתוח התרעות`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/alerts_analysis_dashboard/ -m sanity` opens that report (not fleet) and passes freshness when the caption is within 24 hours (ready locator is temporary).

### Implementation for User Story 1

- [x] T004 [P] [US1] Create `AlertsAnalysisPage(ReportShell)` in `tests/ui/alerts_analysis_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = "ניתוח התרעות"` and `_report_ready_locator()` returning `_iframe_phrase_locator("ניתוח התרעות")`; set `self.url` from existing settings login/dashboard URL; no JSON, slicer, or KPI methods
- [x] T005 [P] [US1] Create `dashboard` fixture in `tests/ui/alerts_analysis_dashboard/conftest.py` that returns `AlertsAnalysisPage`, navigates (same transient catalog/profile retry shape as `tests/ui/power_outages_dashboard/conftest.py`), and does not edit root `conftest.py`
- [x] T006 [US1] Create `tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`; no locators or parsing in the test

**Checkpoint**: MVP — Alerts Analysis Layer 0 smoke is independently testable.

---

## Phase 4: User Story 2 - Marsal Layer 0 freshness smoke (Priority: P1)

**Goal**: Open Marsal through `ReportShell`, wait on temporary iframe phrase `מרס"ל`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/marsal_dashboard/ -m sanity`

### Implementation for User Story 2

- [x] T007 [P] [US2] Create `MarsalPage(ReportShell)` in `tests/ui/marsal_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = 'מרס"ל'` and `_report_ready_locator()` returning `_iframe_phrase_locator('מרס"ל')`; set `self.url` from existing settings login/dashboard URL; no JSON, slicer, or KPI methods
- [x] T008 [P] [US2] Create `dashboard` fixture in `tests/ui/marsal_dashboard/conftest.py` that returns `MarsalPage` and navigates (same retry shape as US1); do not edit root `conftest.py`
- [x] T009 [US2] Create `tests/ui/marsal_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`

**Checkpoint**: Marsal Layer 0 smoke is independently testable.

---

## Phase 5: User Story 3 - Authorities Status Layer 0 freshness smoke (Priority: P1)

**Goal**: Open Authorities Status through `ReportShell`, wait on temporary iframe phrase `הערכת מצב רשויות`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/authorities_status_dashboard/ -m sanity`

### Implementation for User Story 3

- [x] T010 [P] [US3] Create `AuthoritiesStatusPage(ReportShell)` in `tests/ui/authorities_status_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = "הערכת מצב רשויות"` and `_report_ready_locator()` returning `_iframe_phrase_locator("הערכת מצב רשויות")`; set `self.url` from existing settings login/dashboard URL; no JSON, slicer, or KPI methods
- [x] T011 [P] [US3] Create `dashboard` fixture in `tests/ui/authorities_status_dashboard/conftest.py` that returns `AuthoritiesStatusPage` and navigates (same retry shape as US1); do not edit root `conftest.py`
- [x] T012 [US3] Create `tests/ui/authorities_status_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`

**Checkpoint**: Authorities Status Layer 0 smoke is independently testable.

---

## Phase 6: User Story 4 - Hosen Status Layer 0 freshness smoke (Priority: P1)

**Goal**: Open Hosen Status through `ReportShell`, wait on exact iframe text `תמ"צ ארצי - דיווחי קה"א יקל"ר`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/hosen_status_dashboard/ -m sanity`

### Implementation for User Story 4

- [x] T013 [P] [US4] Create `HosenStatusPage(ReportShell)` in `tests/ui/hosen_status_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = 'תמ"צ חוסן'` and `_report_ready_locator()` returning `_iframe_phrase_locator('תמ"צ חוסן')`; set `self.url` from existing settings login/dashboard URL; no JSON, slicer, or KPI methods
- [x] T014 [P] [US4] Create `dashboard` fixture in `tests/ui/hosen_status_dashboard/conftest.py` that returns `HosenStatusPage` and navigates (same retry shape as US1); do not edit root `conftest.py`
- [x] T015 [US4] Create `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`
- [x] T020 [US4] Update `HosenStatusPage._report_ready_locator()` in `tests/ui/hosen_status_dashboard/page.py` to exact iframe text `תמ"צ ארצי - דיווחי קה"א יקל"ר` via `_report_frame().get_by_text(..., exact=True)` (discovery ARIA snapshot). Do not add popup dismiss.

**Checkpoint**: All four reports independently run Layer 0 freshness smoke.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Leakage, ignore files, quickstart

- [x] T016 [P] Scan `core/` so it contains none of `ניתוח התרעות`, `מרס"ל`, `הערכת מצב רשויות`, `תמ"צ חוסן`
- [x] T017 [P] Confirm no new files under `pages/` and `.env` was not modified
- [x] T018 Collect the four new suites with `pytest tests/ui/alerts_analysis_dashboard/ tests/ui/marsal_dashboard/ tests/ui/authorities_status_dashboard/ tests/ui/hosen_status_dashboard/ -m sanity --collect-only` to prove they are independently discoverable
- [x] T019 [P] Mark done-when checkboxes in `specs/005-mass-dashboards-addition/quickstart.md` after T016–T018

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on T003
- **User Story 2 (Phase 4)**: Depends on T003 — independent of US1
- **User Story 3 (Phase 5)**: Depends on T003 — independent of US1/US2
- **User Story 4 (Phase 6)**: Depends on T003 — independent of US1–US3
- **Polish (Phase 7)**: Depends on US1–US4

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational — no dependency on other stories
- **User Story 2 (P1)**: After Foundational — no dependency on other stories
- **User Story 3 (P1)**: After Foundational — no dependency on other stories
- **User Story 4 (P1)**: After Foundational — no dependency on other stories

### Parallel Opportunities

- T001 and T002 in parallel
- T003 in parallel with T001/T002
- After T003: US1–US4 in parallel (each story's page.py + conftest.py in parallel, then the smoke test)
- T016, T017, T019 after implementation; T018 after all stories

---

## Parallel Example: User Story 1

```bash
Task: "Create AlertsAnalysisPage in tests/ui/alerts_analysis_dashboard/page.py"
Task: "Create dashboard fixture in tests/ui/alerts_analysis_dashboard/conftest.py"
# then
Task: "Create test_dashboard_smoke.py calling dashboard.verify_freshness()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1–2 (confirm Layer 0)
2. Complete Phase 3 (Alerts Analysis)
3. **STOP and VALIDATE**: `pytest tests/ui/alerts_analysis_dashboard/ -m sanity --collect-only`
4. Add US2–US4 in parallel

### Incremental Delivery

1. Setup + Foundational → confirm per-page search already works
2. US1 → Alerts Analysis freshness smoke (MVP)
3. US2–US4 → remaining three reports
4. Polish → leakage + collect-only

---

## Notes

- [P] tasks = different files, no dependencies
- Do not add `data/*.json` or `Slicer` usage
- Do not edit root `conftest.py`, fleet tests, `pages/`, `.env`, or `core/`
- Ready locators are temporary copies of the search term
- Commit after implementation if auto-commit is enabled
