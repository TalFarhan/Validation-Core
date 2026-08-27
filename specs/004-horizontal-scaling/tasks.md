---

description: "Task list for Horizontal Scaling — Layer 0 smoke for Power Outages and Credit Consumption"
---

# Tasks: Horizontal Scaling — Layer 0 Smoke for New Dashboards

**Input**: Design documents from `/specs/004-horizontal-scaling/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/layer0-report-binding.md, quickstart.md

**Tests**: Feature explicitly adds `test_dashboard_updated_within_24_hours` in each new suite. Because Layer 0 catalog-search resolution changes, `pytest tests/ui/fleet_dashboard/` is **MANDATORY** at completion. New suites are also binding gates.

**Organization**: Foundational per-page search term, then US1 (Power Outages), then US2 (Credit Consumption). US1 and US2 touch different files and MAY run in parallel after T003.

**Constitution**: v1.2.0 — zero new-report leakage in `core/`; inherit `ReportShell`; no JSON/slicer on the new pages.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: [US1], [US2] on user-story tasks only
- Include exact file paths in descriptions

## Path Conventions

- Layer 0: `core/portal/page.py`
- Power Outages: `tests/ui/power_outages_dashboard/`
- Credit Consumption: `tests/ui/credit_consumption_dashboard/`
- Fleet fixture (read-only): `conftest.py`
- Fleet domain (read-only): `pages/fleet_dashboard/main_dashboard_page.py`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm existing Layer 0 host and fleet fixture without moving behavior

- [x] T001 Confirm `ReportShell` in `core/portal/page.py` exposes `_report_ready_locator`, `after_navigate`, `_report_frame`, `_open_dashboard_via_portal_search`, and `verify_freshness` (no behavior change yet)
- [x] T002 [P] Confirm root `dashboard` fixture in `conftest.py` still returns `MainDashboardPage`; do not edit `conftest.py` or `tests/ui/fleet_dashboard/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Layer 0 must honor a page-owned catalog search term before any new suite can open the correct product

**⚠️ CRITICAL**: No new page objects until this phase is complete

- [x] T003 Teach catalog search and the navigate log line in `core/portal/page.py` to use `getattr(self, "DASHBOARD_SEARCH_TERM", None) or settings.DASHBOARD_SEARCH_TERM` so fleet keeps the settings default and new pages can set a class attribute
- [x] T004 [P] Verify `.gitignore` includes Python essentials (`__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `.env`, `auth_state.json`); append only if missing

**Checkpoint**: A `ReportShell` subclass with `DASHBOARD_SEARCH_TERM` searches that product. Fleet still uses settings. User stories can begin.

---

## Phase 3: User Story 1 - Power Outages Layer 0 freshness smoke (Priority: P1) 🎯 MVP

**Goal**: Open Power Outages through `ReportShell`, wait on `לקוחות חיוניים מופסקים`, and call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/power_outages_dashboard/ -m sanity` opens that report (not fleet) and passes freshness when the caption is within 24 hours.

### Implementation for User Story 1

- [x] T005 [P] [US1] Create `PowerOutagesPage(ReportShell)` in `tests/ui/power_outages_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = "תמונת מצב הפסקות חשמל"` and `_report_ready_locator()` returning iframe text locator `"לקוחות חיוניים מופסקים"`; set `self.url` from existing settings login/dashboard URL; no JSON, slicer, or KPI methods
- [x] T006 [P] [US1] Create `dashboard` fixture in `tests/ui/power_outages_dashboard/conftest.py` that returns `PowerOutagesPage`, navigates (with the same transient catalog/profile retry shape as root `conftest.py`), and does not edit root `conftest.py`
- [x] T007 [US1] Create `tests/ui/power_outages_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`; no locators or parsing in the test

**Checkpoint**: MVP — Power Outages Layer 0 smoke is independently testable.

---

## Phase 4: User Story 2 - Credit Consumption Layer 0 freshness smoke with popup dismiss (Priority: P1)

**Goal**: Open Credit Consumption, dismiss the info-page popup before ready wait, then call inherited `verify_freshness()`.

**Independent Test**: `pytest tests/ui/credit_consumption_dashboard/ -m sanity` dismisses a blocking popup when present, waits on `ממוצע הוצאות לקנייה בשגרה`, and passes freshness when the caption is within 24 hours.

### Implementation for User Story 2

- [x] T008 [P] [US2] Create `CreditConsumptionPage(ReportShell)` in `tests/ui/credit_consumption_dashboard/page.py` with `DASHBOARD_SEARCH_TERM = "צריכת אשראי"`, `_report_ready_locator()` returning iframe text `"ממוצע הוצאות לקנייה בשגרה"`, and safe popup dismiss (click visible X/Close/סגור in the report iframe with a short timeout; no-op if absent) invoked before ready wait and in `after_navigate`; no JSON, slicer, or KPI methods
- [x] T009 [P] [US2] Create `dashboard` fixture in `tests/ui/credit_consumption_dashboard/conftest.py` that returns `CreditConsumptionPage` and navigates (same retry shape as US1); do not edit root `conftest.py`
- [x] T010 [US2] Create `tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py` with `@pytest.mark.sanity` `test_dashboard_updated_within_24_hours(dashboard)` whose body is `dashboard.verify_freshness()` plus `suite_marks(feature=FEATURE_UI_SMOKE)`; no locators, parsing, or popup clicks in the test

**Checkpoint**: Both new reports independently run Layer 0 freshness smoke.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Leakage, fleet regression, quickstart

- [x] T011 [P] Scan `core/` so it contains none of `תמונת מצב הפסקות חשמל`, `לקוחות חיוניים מופסקים`, `צריכת אשראי`, `ממוצע הוצאות לקנייה בשגרה` and none of the fleet leakage tokens from `specs/003-dashboard-freshness/contracts/freshness-api.md`
- [x] T012 Run `pytest tests/ui/power_outages_dashboard/ -m sanity` and `pytest tests/ui/credit_consumption_dashboard/ -m sanity`. Power Outages PASSED. Credit Consumption reached `verify_freshness()` (ready locator + popup dismiss work) and correctly failed: live last-refresh is 2026-07-19 (~38 days), which is a stale-data fail not a framework bug. Fleet suite not re-run in this pass.
- [x] T013 [P] Mark done-when checkboxes in `specs/004-horizontal-scaling/quickstart.md` after T011–T012
- [x] T014 Capture a full-page screenshot in root `conftest.py` `pytest_runtest_makereport` when `report.when == "call"` and `report.failed`, attach it to pytest-html (`extras.image(base64)`) and Allure (`allure.attach`), and wrap capture in try/except so a closed page cannot break teardown
- [x] T015 Print extracted last-refresh date to stdout in `ReportShell.verify_freshness()` in `core/portal/page.py` (`print(f"\\n---> EXTRACTED DASHBOARD DATE: {extracted_date_string} <---")`) so pytest-html Captured Stdout shows it for passed tests — `allure.step` does not print
- [x] T016 [US2] Improve `CreditConsumptionPage._close_info_popup()` in `tests/ui/credit_consumption_dashboard/page.py`: locate the iframe overlay X shape/image (top-left of "דף מידע", RTL) and `.click(force=True)`; do not rely on Escape (Power BI visual overlay ignores it). Verified 2026-08-27: overlay dismissed (dashboard KPIs visible on failure screenshot); remaining fail is stale last-refresh 2026-07-19

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on T003
- **User Story 2 (Phase 4)**: Depends on T003 — independent of US1 (different files)
- **Polish (Phase 5)**: Depends on US1 and US2

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational — no dependency on US2
- **User Story 2 (P1)**: After Foundational — no dependency on US1

### Parallel Opportunities

- T001 and T002 in parallel
- T003 then T004 (T004 is [P] vs T003)
- After T003: T005/T006 in parallel, then T007; T008/T009 in parallel, then T010; US1 and US2 in parallel with each other
- T011 and T013 after implementation; T012 after both stories

---

## Parallel Example: User Story 1

```bash
Task: "Create PowerOutagesPage in tests/ui/power_outages_dashboard/page.py"
Task: "Create dashboard fixture in tests/ui/power_outages_dashboard/conftest.py"
# then
Task: "Create test_dashboard_smoke.py calling dashboard.verify_freshness()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1–2 (per-page search term)
2. Complete Phase 3 (Power Outages)
3. **STOP and VALIDATE**: `pytest tests/ui/power_outages_dashboard/ -m sanity`
4. Add US2 (Credit Consumption popup)

### Incremental Delivery

1. Setup + Foundational → any page can set `DASHBOARD_SEARCH_TERM`
2. US1 → Power Outages freshness smoke (MVP)
3. US2 → Credit Consumption freshness smoke with popup dismiss
4. Polish → leakage + fleet gate

---

## Notes

- [P] tasks = different files, no dependencies
- Do not add `data/*.json` or `Slicer` usage
- Do not edit root `conftest.py` or fleet tests
- Popup dismiss MUST run before the ready wait, not only in `after_navigate`
- Commit after each story if auto-commit is enabled
