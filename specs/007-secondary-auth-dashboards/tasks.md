---
description: "Task list for Secondary-Auth Dashboards — Layer 0 freshness smoke + bypass hook for four new reports"
---

# Tasks: Secondary-Auth Dashboards — Layer 0 Freshness Smoke + Bypass Hook

**Input**: Design documents from `/specs/007-secondary-auth-dashboards/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/layer0-report-binding.md, quickstart.md

**Tests**: Feature explicitly adds `test_dashboard_updated_within_24_hours` in each new suite. Layer 0 is changed (new no-op `_bypass_secondary_auth` seam), so fleet smoke IS a regression gate. New suites are binding gates; temporary ready locators and placeholder bypass overrides may fail until live-run feedback.

**Organization**: Add the Layer 0 seam, then US1–US4 (one report each). The four stories touch different files and MAY run in parallel after T004.

**Constitution**: v1.2.0 — zero new-report leakage in `core/` (only the generic hook); inherit `ReportShell`; no JSON/slicer; no `pages/`; no `.env`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: [US1]–[US4] on user-story tasks only
- Include exact file paths in descriptions

## Path Conventions

- Layer 0 (edited — generic hook only): `core/portal/page.py`
- Mass Events: `tests/ui/mass_events_dashboard/`
- Life-Saving Guidelines: `tests/ui/life_saving_guidelines_dashboard/`
- Maya System: `tests/ui/maya_system_dashboard/`
- Public Shelters: `tests/ui/public_shelters_dashboard/`
- Fleet fixture (read-only): `conftest.py`
- Shared fixture helper (read-only): `tests/helpers/dashboard_fixture.py`
- Do not create: `pages/<report>/`
- Do not edit: `.env`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing Layer 0 host and fleet fixture before editing

- [X] T001 Confirm `ReportShell` in `core/portal/page.py` exposes `_report_ready_locator`, `_report_frame`, `_catalog_search_term` (`getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM`), `_open_dashboard_via_portal_search`, and `verify_freshness`
- [X] T002 [P] Confirm root `dashboard` fixture in `conftest.py` still returns `MainDashboardPage`; do not edit `conftest.py`, `tests/ui/fleet_dashboard/`, `pages/`, or `.env`

---

## Phase 2: Foundational (Blocking Prerequisites) — Layer 0 seam

**Purpose**: Add the generic secondary-auth bypass seam that all four reports override

**⚠️ CRITICAL**: No new page objects until this phase is complete

- [X] T003 Add `def _bypass_secondary_auth(self) -> None: return` (report-agnostic no-op, docstring only) to `ReportShell` in `core/portal/page.py`, next to `after_navigate` / `before_report_ready_check`
- [X] T004 In `ReportShell.navigate()` in `core/portal/page.py`, call `self._bypass_secondary_auth()` AFTER the catalog-open branch (`ensure_single_tab(...)`) and BEFORE `ready = self._report_ready_locator()`; do not change `navigate()`'s signature
- [X] T005 [P] Verify `.gitignore` includes Python essentials (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env`, `auth_state.json`); append only if missing

**Checkpoint**: `ReportShell` runs a no-op bypass after the catalog click. Fleet behavior is unchanged. User stories can begin.

---

## Phase 3: User Story 1 - Mass Events Layer 0 freshness smoke (Priority: P1) 🎯 MVP

**Goal**: Open Mass Events through `ReportShell`, run the placeholder bypass hook, wait on temporary exact iframe text `תמ"צ אירועים המוניים`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/mass_events_dashboard/ -m sanity` opens that report (not fleet) and passes freshness when the caption is within 24 hours (ready locator + bypass are temporary).

### Implementation for User Story 1

- [X] T006 [P] [US1] Create `MassEventsPage(ReportShell)` in `tests/ui/mass_events_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = 'תמ"צ אירועים המוניים'`, `_report_ready_locator()` returning `self._report_frame().get_by_text('תמ"צ אירועים המוניים', exact=True)`, and a placeholder `_bypass_secondary_auth(self)` override; set `self.url` from `settings.LOGIN_URL or settings.DASHBOARD_URL`; no JSON, slicer, or KPI methods
- [X] T007 [P] [US1] Create `dashboard` fixture in `tests/ui/mass_events_dashboard/conftest.py` via `bind_dashboard(MassEventsPage)` (same shape as `tests/ui/hosen_status_dashboard/conftest.py`); do not edit root `conftest.py`
- [X] T008 [US1] Create `tests/ui/mass_events_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`; no locators or parsing in the test

**Checkpoint**: MVP — Mass Events Layer 0 smoke is independently testable.

---

## Phase 4: User Story 2 - Life-Saving Guidelines Layer 0 freshness smoke (Priority: P1)

**Goal**: Open Life-Saving Guidelines through `ReportShell`, run the placeholder bypass hook, wait on temporary exact iframe text `תמ"צ שליטה - סטטוס הנחיות מצילות חיים`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/life_saving_guidelines_dashboard/ -m sanity`

### Implementation for User Story 2

- [X] T009 [P] [US2] Create `LifeSavingGuidelinesPage(ReportShell)` in `tests/ui/life_saving_guidelines_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = 'תמ"צ שליטה - סטטוס הנחיות מצילות חיים'`, `_report_ready_locator()` returning `self._report_frame().get_by_text('תמ"צ שליטה - סטטוס הנחיות מצילות חיים', exact=True)`, and a placeholder `_bypass_secondary_auth(self)` override; set `self.url` from settings login/dashboard URL; no JSON/slicer/KPI methods
- [X] T010 [P] [US2] Create `dashboard` fixture in `tests/ui/life_saving_guidelines_dashboard/conftest.py` via `bind_dashboard(LifeSavingGuidelinesPage)`; do not edit root `conftest.py`
- [X] T011 [US2] Create `tests/ui/life_saving_guidelines_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`

**Checkpoint**: Life-Saving Guidelines Layer 0 smoke is independently testable.

---

## Phase 5: User Story 3 - Maya System Layer 0 freshness smoke (Priority: P1)

**Goal**: Open Maya System through `ReportShell`, run the placeholder bypass hook, wait on temporary exact iframe text `מערכת המא"יה`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/maya_system_dashboard/ -m sanity`

### Implementation for User Story 3

- [X] T012 [P] [US3] Create `MayaSystemPage(ReportShell)` in `tests/ui/maya_system_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = 'מערכת המא"יה'`, `_report_ready_locator()` returning `self._report_frame().get_by_text('מערכת המא"יה', exact=True)`, and a placeholder `_bypass_secondary_auth(self)` override; set `self.url` from settings login/dashboard URL; no JSON/slicer/KPI methods
- [X] T013 [P] [US3] Create `dashboard` fixture in `tests/ui/maya_system_dashboard/conftest.py` via `bind_dashboard(MayaSystemPage)`; do not edit root `conftest.py`
- [X] T014 [US3] Create `tests/ui/maya_system_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`

**Checkpoint**: Maya System Layer 0 smoke is independently testable.

---

## Phase 6: User Story 4 - Public Shelters Layer 0 freshness smoke (Priority: P1)

**Goal**: Open Public Shelters through `ReportShell`, run the placeholder bypass hook, wait on temporary exact iframe text `תמ"צ מחסים ציבוריים`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/public_shelters_dashboard/ -m sanity`

### Implementation for User Story 4

- [X] T015 [P] [US4] Create `PublicSheltersPage(ReportShell)` in `tests/ui/public_shelters_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = 'תמ"צ מחסים ציבוריים'`, `_report_ready_locator()` returning `self._report_frame().get_by_text('תמ"צ מחסים ציבוריים', exact=True)`, and a placeholder `_bypass_secondary_auth(self)` override; set `self.url` from settings login/dashboard URL; no JSON/slicer/KPI methods
- [X] T016 [P] [US4] Create `dashboard` fixture in `tests/ui/public_shelters_dashboard/conftest.py` via `bind_dashboard(PublicSheltersPage)`; do not edit root `conftest.py`
- [X] T017 [US4] Create `tests/ui/public_shelters_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`

**Checkpoint**: Public Shelters Layer 0 smoke is independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Leakage, fleet regression, collect

- [X] T018 [P] Scan `core/` so it contains none of `תמ"צ אירועים המוניים`, `תמ"צ שליטה - סטטוס הנחיות מצילות חיים`, `מערכת המא"יה`, `תמ"צ מחסים ציבוריים` (the generic `_bypass_secondary_auth` name IS allowed)
- [X] T019 [P] Confirm no new files under `pages/` and `.env` was not modified
- [X] T020 Collect the four new suites with `pytest tests/ui/mass_events_dashboard/ tests/ui/life_saving_guidelines_dashboard/ tests/ui/maya_system_dashboard/ tests/ui/public_shelters_dashboard/ -m sanity --collect-only` to prove they are independently discoverable
- [X] T021 [P] Mark done-when checkboxes in `specs/007-secondary-auth-dashboards/quickstart.md` after T018–T020

---

## Phase 8: Real Secondary-Auth Flow (ArcGIS entry) — replace placeholders

**Purpose**: Replace the placeholder `_bypass_secondary_auth` overrides with the real ArcGIS Online sign-in flow revealed from live use. Flow (manual reference): dialog "היכנס אל ArcGIS Online" → אישור → new tab "ענף אגמים - מפעל המידע" → "בחר סוג חשבון" = "משתמשי @agamimp.net" → account `Tal.Farhan@agamimp.net` → password → "אין לי אפשרות להתחבר" → "שלח הודעת טקסט למספר הטלפון…" → SMS one-time code.

**Constitution**: Flow lives OUTSIDE `core/` (shared helper under `tests/helpers/`) so Layer 0 stays report-agnostic; the four product names/strings still MUST NOT enter `core/`. No `.env` edits (credentials come from optional env vars); no new `pages/` packages.

- [X] T022 Create shared helper `tests/helpers/secondary_auth.py` exposing `bypass_secondary_auth(page)` that drives the ArcGIS flow: confirm "ArcGIS Online" dialog (אישור) + capture new tab → choose account type "משתמשי @agamimp.net" → select/type account (`AGAMIM_SECONDARY_EMAIL`, default `Tal.Farhan@agamimp.net`) → fill password (`AGAMIM_SECONDARY_PASSWORD`, else pause) → click "אין לי אפשרות להתחבר" → "שלח הודעת טקסט…" → pause for manual SMS code → wait for auth tab to close → `ensure_single_tab`. Every step is optional (short visibility probe) so it is a no-op when the screen is absent (reused/saved session).
- [X] T023 [P] [US1] Replace placeholder `_bypass_secondary_auth` in `tests/ui/mass_events_dashboard/page.py` with `bypass_secondary_auth(self.page)`
- [X] T024 [P] [US2] Replace placeholder `_bypass_secondary_auth` in `tests/ui/life_saving_guidelines_dashboard/page.py` with `bypass_secondary_auth(self.page)`
- [X] T025 [P] [US3] Replace placeholder `_bypass_secondary_auth` in `tests/ui/maya_system_dashboard/page.py` with `bypass_secondary_auth(self.page)`
- [X] T026 [P] [US4] Replace placeholder `_bypass_secondary_auth` in `tests/ui/public_shelters_dashboard/page.py` with `bypass_secondary_auth(self.page)`
- [X] T027 Re-confirm no new-report leakage in `core/` (helper is under `tests/helpers/`) and re-collect the four suites (`--collect-only` → 4 tests)
- [ ] T028 Live headed verification (`HEADLESS=false`, `MANUAL_LOGIN=true`): run each gated suite, confirm each `[secondary-auth]` step clicks the right control, and tighten selectors in `tests/helpers/secondary_auth.py` from live DOM feedback. Also update each page's temporary `_report_ready_locator()` from the real landing-page title once known.

**Checkpoint**: Placeholders replaced by the real ArcGIS flow. Selectors pending live confirmation (T028).

**Note**: `_report_ready_locator()` on all four pages remains the temporary search-term text (per T006/T009/T012/T015) until the live landing title is confirmed in T028.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (Layer 0 seam)
- **User Story 1 (Phase 3)**: Depends on T003–T004
- **User Story 2 (Phase 4)**: Depends on T003–T004 — independent of US1
- **User Story 3 (Phase 5)**: Depends on T003–T004 — independent of US1/US2
- **User Story 4 (Phase 6)**: Depends on T003–T004 — independent of US1/US2/US3
- **Polish (Phase 7)**: Depends on US1–US4

### User Story Dependencies

- **US1–US4 (all P1)**: After Foundational — no dependency on each other

### Parallel Opportunities

- T001 and T002 in parallel
- T005 in parallel with T001/T002
- After T004: US1–US4 in parallel (each story's page.py + conftest.py in parallel, then the smoke test)
- T018, T019, T021 after implementation; T020 after all stories

---

## Parallel Example: User Story 1

```bash
Task: "Create MassEventsPage in tests/ui/mass_events_dashboard/page.py"
Task: "Create dashboard fixture in tests/ui/mass_events_dashboard/conftest.py"
# then
Task: "Create test_dashboard_smoke.py calling dashboard.verify_freshness()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1–2 (Layer 0 seam)
2. Complete Phase 3 (Mass Events)
3. **STOP and VALIDATE**: `pytest tests/ui/mass_events_dashboard/ -m sanity --collect-only`
4. Add US2–US4 in parallel

### Incremental Delivery

1. Setup + Foundational → generic bypass seam in place, fleet still green
2. US1 → Mass Events freshness smoke (MVP)
3. US2–US4 → remaining reports
4. Polish → leakage + collect-only

---

## Notes

- [P] tasks = different files, no dependencies
- Do not add `data/*.json` or `Slicer` usage
- Do not edit root `conftest.py`, fleet tests, `pages/`, or `.env`
- The only `core/` edit is the generic `_bypass_secondary_auth` hook + its call
- Ready locators are temporary copies of the search term (`exact=True`)
- `_bypass_secondary_auth` overrides are placeholders (comment/`print`) until live feedback
- Commit after implementation if auto-commit is enabled
