---
description: "Task list for Credit Consumption Dashboard UI sanity page object and golden-record tests"
---

# Tasks: Credit Consumption Dashboard UI Sanity

**Input**: Design documents from `/specs/044-credit-consumption-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/credit-consumption-page.md, quickstart.md

**Tests**: The feature *is* the page object plus the sanity suite (`tests/sanity/credit_consumption_dashboard/test_data_validation.py`). Credit UI smoke (`pytest tests/ui/credit_consumption_dashboard/`) is the MANDATORY navigation-surface gate (Constitution III / FR-015). Fleet smoke is **not** a gate (no `core/` or fleet navigation change). Golden metric values in `data/credit/db_sanity_purim2026.yaml` are read-only.

**Organization**: Tasks are grouped by the five user stories from spec.md so each can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US5 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page implementation: `pages/credit_consumption/credit_consumption_page.py`
- Smoke re-export: `pages/credit_consumption/page.py`
- Credit UI smoke: `tests/ui/credit_consumption_dashboard/` (`conftest.py`, `test_dashboard_smoke.py`)
- Sanity package: `tests/sanity/credit_consumption_dashboard/`
- Golden record (read-only values): `data/credit/db_sanity_purim2026.yaml`
- Coverage catalog: `docs/COVERAGE_CATALOG.md`
- Contract: `specs/044-credit-consumption-sanity/contracts/credit-consumption-page.md`
- OFF-LIMITS (do not edit): `core/portal/`, `core/components/`, `pages/alerts_analysis/`, `pages/status_picture/`, `pages/fleet_dashboard/`, `tests/**/alerts_analysis_dashboard/`, `tests/**/status_picture_dashboard/`, `tests/**/fleet_dashboard/`, `db/`, root `conftest.py`

Do **not** add `pages/credit_consumption/__init__.py` (feature 018 namespace-package rule). In-function comments are English only (FR-014). Hebrew titles, toggle names, slicer `role_name`s, and export headers that are not already in the YAML or the Layer 0 page are copied from the live report (FR-016).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the golden document shape, and the existing Layer 0 binding before moving code

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/044-credit-consumption-sanity"` and that `specs/044-credit-consumption-sanity/plan.md` lists only credit page/sanity/catalog files (no alerts, status-picture, fleet, `core/`, or `db/` edits). Git checkout stays `feature/reportportal-integration`.
- [X] T002 [P] Inventory (read-only, do not edit): in `pages/credit_consumption/page.py` confirm class `CreditConsumptionPage` subclasses `ReportShell`, `DASHBOARD_SEARCH_TERM == "צריכת אשראי"`, `_report_ready_locator` uses `ממוצע הוצאות לקנייה בשגרה`, and info-overlay dismiss (`דף מידע` / `מושגים חשובים`) lives in `before_report_ready_check` / `after_navigate`. In `tests/ui/credit_consumption_dashboard/conftest.py` confirm `from pages.credit_consumption.page import CreditConsumptionPage`. In `data/credit/db_sanity_purim2026.yaml` confirm root `credit_consumption_dashboard` with `screen_1_summary.active_filters.time_range == "פורים 2026"`, four `daily_trends_by_toggle` keys, `kpi_metrics`, `expenses_by_authority_millions`, `daily_alerts`, and `screen_2_data_export.export_table_data`. Confirm root `conftest.py` does not import this page.

**Checkpoint**: Scope and Layer 0 inventory confirmed; golden keys known.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Move the page class, keep the smoke import, and add the sanity fixture so every story can open Screen 1

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create an empty `tests/sanity/credit_consumption_dashboard/__init__.py`. Do not add `pages/credit_consumption/__init__.py`.
- [X] T004 Move class `CreditConsumptionPage` from `pages/credit_consumption/page.py` into `pages/credit_consumption/credit_consumption_page.py`. Keep `ReportShell` inheritance, `DASHBOARD_SEARCH_TERM`, `_report_ready_locator`, and the existing info-overlay dismiss methods unchanged. Replace `pages/credit_consumption/page.py` with a re-export: `from pages.credit_consumption.credit_consumption_page import CreditConsumptionPage`. Do not change `tests/ui/credit_consumption_dashboard/conftest.py` or `test_dashboard_smoke.py`. English comments only (FR-001, FR-002, AC-004).
- [X] T005 Add `credit_consumption_dashboard = bind_dashboard(CreditConsumptionPage, "credit_consumption_dashboard")` to `tests/sanity/credit_consumption_dashboard/conftest.py`, importing `bind_dashboard` from `tests.helpers.dashboard_fixture` and `CreditConsumptionPage` from `pages.credit_consumption.credit_consumption_page`. Do not edit root `conftest.py`.

**Checkpoint**: Fixture opens Screen 1 through the moved class; smoke still imports `pages.credit_consumption.page`. User stories can start.

---

## Phase 3: User Story 1 - Open both screens under Hebrew or English chrome (Priority: P1) 🎯 MVP

**Goal**: Info overlay is dismissed, Screen 1 is ready, and Screen 2 opens through a bilingual page-rail so navigation does not raise `LoadTimeoutError`.

**Independent Test**: `pytest tests/ui/credit_consumption_dashboard/` stays green. `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k export_page_opens` switches via the bilingual page-rail and sees `צריכת אשראי - ייצוא נתונים`.

### Implementation for User Story 1

- [X] T006 [US1] In `pages/credit_consumption/credit_consumption_page.py`, add `open_export_page()` that locates the page-rail with a Playwright `.or_()` over `ניווט בין עמודים` and `Page navigation` across `get_by_role("link"|"button")` and `get_by_label(..., exact=False)` (same pattern as alerts 043, but do **not** import alerts code). Click, then wait for title `צריכת אשראי - ייצוא נתונים`. Subsequent ready checks on Screen 2 use that title. Keep popup dismiss on navigate. English comments only (FR-003).
- [X] T007 [US1] Create `tests/sanity/credit_consumption_dashboard/test_data_validation.py` with `@pytest.mark.sanity` `test_export_page_opens(credit_consumption_dashboard)` that imports the fixture from `tests.sanity.credit_consumption_dashboard.conftest`, calls `open_export_page()`, and asserts the Screen 2 title is visible through a page method (no raw iframe locators in the test body). Comments inside functions are English (FR-011, FR-014).
- [ ] T008 [US1] Run the independent tests `pytest tests/ui/credit_consumption_dashboard/` and `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k export_page_opens`. Confirm no `LoadTimeoutError` and freshness smoke still passes. **(BLOCKED: requires portal auth + live browser — run locally.)**

**Checkpoint**: Screen 1 and Screen 2 open under Hebrew or English chrome; US1 testable on its own.

---

## Phase 4: User Story 2 - Golden filters are applied before every assertion (Priority: P1)

**Goal**: Setup reads `active_filters` from the golden YAML and applies non-`הכל` values (`פורים 2026`) on each screen. Date fields, when present, fill through bilingual locators.

**Independent Test**: After this phase, a Screen 1 call to `apply_filters(screen_1_summary.active_filters)` selects `time_range: "פורים 2026"` and does not click `הכל`. Screen 2 export tests will reuse the same helper with `top_bar` + `side_bar`.

### Implementation for User Story 2

- [X] T009 [US2] In `pages/credit_consumption/credit_consumption_page.py`, compose Layer 2 `Slicer` with `SlicerDefinition` rows whose `id` matches the YAML filter keys (`time_range`, `period`, `guidelines_area`, `district`, `sub_district`, `sector`, `purchase_nature`, `vitality_status`, `category`, `index`, `authority`, `date`, `day_of_week`). Copy each `role_name` from the live report (FR-016). Kind is `dropdown` unless the live control is a checkbox list. Do **not** add a `SlicerKind`. Implement `apply_filters(self, filters: dict) -> None` that skips values equal to `הכל` and calls `Slicer.select` / `select_many` for the rest, then settles on the current screen's ready phrase. English comments only (FR-005).
- [X] T010 [US2] In `pages/credit_consumption/credit_consumption_page.py`, add bilingual date fill (when those inputs are visible): `input[aria-label^='תאריך התחלה']`.or_(`input[aria-label^='Start date']`) and the end-date pair (`תאריך סיום` / `End date`). `apply_filters` uses this path only when date fields are present; it does not invent a new `SlicerKind`. English comments only (FR-004).
- [X] T011 [US2] In `tests/sanity/credit_consumption_dashboard/test_data_validation.py`, add `load_sanity_data()` that opens `Path(__file__).resolve().parents[3] / "data" / "credit" / "db_sanity_purim2026.yaml"` as UTF-8 and returns `yaml.safe_load`. Add helpers that read `credit_consumption_dashboard.screen_1_summary.active_filters` and merged Screen 2 `top_bar` + `side_bar`, then call `page.apply_filters(...)`. Do not hard-code `פורים 2026`. English comments only (FR-005).

**Checkpoint**: Golden period can be applied on both screens; `הכל` is not re-clicked; US2 testable via `apply_filters` before any later assertion.

---

## Phase 5: User Story 3 - KPI cards match the golden record (Priority: P1)

**Goal**: After Screen 1 filters, `read_kpi_metrics()` matches nested `kpi_metrics` (population, routine expense, selected-range expense, change-vs-routine percent strings).

**Independent Test**: `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k test_kpi_metrics_match_golden` applies Screen 1 filters and asserts every golden KPI key.

### Implementation for User Story 3

- [X] T012 [US3] In `pages/credit_consumption/credit_consumption_page.py`, compose Layer 2 `KPI` and implement `read_kpi_metrics() -> dict` returning the nested golden shape (`num_population`, `average_purchase_expense_routine.physical_purchase`, `average_purchase_expense_selected_range.{total,physical_purchase,online_purchase}`, `average_change_percentage_vs_routine.{physical_purchase,online_purchase}`). Copy card titles from the live report (the ready visual `ממוצע הוצאות לקנייה בשגרה` maps under routine expense). Use `KPI.number` for numeric cards and `KPI.value` (or raw text) for percent strings so `"3.23%"` / `"4.23%"` are preserved. Omit a title that is not visible rather than raising for one missing card. English comments only (FR-006).
- [X] T013 [US3] Add `@pytest.mark.sanity` `test_kpi_metrics_match_golden(credit_consumption_dashboard)` to `tests/sanity/credit_consumption_dashboard/test_data_validation.py`. Apply Screen 1 `active_filters` via the US2 helper, call `read_kpi_metrics()`, and assert every golden key (extra UI keys ignored). Skip with a missing-reader / empty-read message if a required key is absent. Do not hard-code `10006812` or the percent literals. English comments only (FR-011).

**Checkpoint**: Screen 1 KPI cards are testable against the golden nested object without trends or Screen 2.

---

## Phase 6: User Story 4 - Daily trends follow the four toggle combinations (Priority: P1)

**Goal**: Metric and visualization toggles select each of the four `daily_trends_by_toggle` series. Extraction is Right-click → bilingual Show as a table. `transactions_count_bar` keeps a `values` list.

**Independent Test**: `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k test_daily_trends_match_golden` iterates the four YAML keys and matches date / day / value or values.

### Implementation for User Story 4

- [X] T014 [US4] In `pages/credit_consumption/credit_consumption_page.py`, add private Show-as-a-table helpers on this page only (do not import alerts; do not add a Layer 2 API): right-click the visual container, click menuitem `הצג כטבלה` or `Show as a table`, read the visible `grid`/`table`, then leave the table (`חזרה לדוח` or equivalent). English comments only (FR-008).
- [X] T015 [US4] In `pages/credit_consumption/credit_consumption_page.py`, add `set_metric(kind)` for `"expense_amount"` / `"transactions_count"` and `set_visualization(kind)` for `"line"` / `"bar"`. Copy toggle accessible names from the live report; `.or_()` an English name if one exists. Record `_active_metric` / `_active_visualization` only after selection. Do not add a `SlicerKind`. English comments only (FR-007).
- [X] T016 [US4] In `pages/credit_consumption/credit_consumption_page.py`, implement `read_daily_trends() -> list[dict]` using the Show-as-a-table helpers on the active trends visual. Return `{date, day, value}` for `expense_amount_line`, `transactions_count_line`, and `expense_amount_bar`, and `{date, day, values}` (list of numbers) for `transactions_count_bar`. Do not coerce `values` to a scalar. Return `[]` when the table cannot be read. Copy the chart title from the live report. English comments only (FR-008).
- [X] T017 [US4] Add `@pytest.mark.sanity` `test_daily_trends_match_golden(credit_consumption_dashboard)` to `tests/sanity/credit_consumption_dashboard/test_data_validation.py`. Apply Screen 1 filters, iterate the four `daily_trends_by_toggle` keys, call `set_metric` / `set_visualization`, then `read_daily_trends()`, and assert every golden row (extra UI dates ignored). `pytest.skip` only when the reader returns `[]`. Do not hard-code dates or values. English comments only (FR-011).

**Checkpoint**: All four toggle series are extractable via Show-as-a-table; US4 testable without Screen 2.

---

## Phase 7: User Story 5 - Authority chart and Screen 2 export matrix match (Priority: P2)

**Goal**: Screen 1 authority amounts and Screen 2 export rows match the golden lists. `daily_alerts` is asserted when readable and skipped when empty.

**Independent Test**: `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity -k "authority or export_table or daily_alerts"` — authority and export pass/fail when data is present; daily alerts may skip.

### Implementation for User Story 5

- [X] T018 [US5] In `pages/credit_consumption/credit_consumption_page.py`, implement `read_expenses_by_authority() -> list[dict]` via Show-as-a-table on the authority visual, returning `[{authority, amount}, ...]`. Copy the visual title from the live report. Return `[]` if unread. English comments only (FR-009).
- [X] T019 [US5] In `pages/credit_consumption/credit_consumption_page.py`, implement optional `read_daily_alerts() -> list[dict]` returning `[{date, day, alerts_count}, ...]` or `[]`. English comments only.
- [X] T020 [US5] In `pages/credit_consumption/credit_consumption_page.py`, implement `read_export_table() -> list[dict]` that reads the Screen 2 accessible `grid` / `table` and maps live-copied headers to `export_table_data` keys (`transaction_date`, `authority_name`, `vitality_status`, `category`, `sub_category`, `quantity`, `amount`, `purchase_nature`). Amount stays a thousands-separated string (e.g. `"1,944.97"`). Return `[]` if unread. English comments only (FR-010).
- [X] T021 [US5] Add `@pytest.mark.sanity` tests to `tests/sanity/credit_consumption_dashboard/test_data_validation.py`: `test_expenses_by_authority_match_golden` (Screen 1 filters + `read_expenses_by_authority` vs `expenses_by_authority_millions`; every golden authority must match; extra UI rows ignored), `test_daily_alerts_match_golden` (skip if empty), and `test_export_table_match_golden` (`open_export_page`, Screen 2 `active_filters`, `read_export_table` vs `export_table_data`). Skip form: `pytest.skip("... returned no rows (chart empty or not rendered)")`. Do not hard-code golden numbers. English comments only (FR-011).

**Checkpoint**: Remaining golden blocks are testable; a missing visual skips only its own test.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Catalog, comment language, off-limits audit, and the credit smoke gate

- [X] T022 [P] Add a Credit Consumption section to `docs/COVERAGE_CATALOG.md` mapping golden keys (`kpi_metrics`, `daily_trends_by_toggle`, `expenses_by_authority_millions`, `export_table_data`) to `CreditConsumptionPage` methods and `tests/sanity/credit_consumption_dashboard/test_data_validation.py`. Do not claim a warehouse SQL mapping (this slice has none).
- [X] T023 [P] Review every new or edited function in `pages/credit_consumption/credit_consumption_page.py`, `pages/credit_consumption/page.py`, and `tests/sanity/credit_consumption_dashboard/` and ensure in-function comments are English only (FR-014).
- [X] T024 [P] Verify no off-limits file was changed: `git diff --name-only` shows no edits under `core/`, `pages/alerts_analysis/`, `pages/status_picture/`, `pages/fleet_dashboard/`, `tests/**/alerts_analysis_dashboard/`, `tests/**/status_picture_dashboard/`, `tests/**/fleet_dashboard/`, `db/`, or root `conftest.py`, and no metric value changed in `data/credit/db_sanity_purim2026.yaml` (FR-012, FR-013).
- [X] T025 Run `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py --collect-only` and confirm collection of `test_export_page_opens`, `test_kpi_metrics_match_golden`, `test_daily_trends_match_golden`, `test_expenses_by_authority_match_golden`, `test_daily_alerts_match_golden`, and `test_export_table_match_golden`.
- [ ] T026 Run the credit UI smoke gate `pytest tests/ui/credit_consumption_dashboard/` — MUST pass (Constitution III / FR-015). **(BLOCKED: requires portal auth + live browser — run locally.)**
- [ ] T027 Run `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity` per `specs/044-credit-consumption-sanity/quickstart.md` and confirm the Done-When checklist (KPIs, four trends, authority, export; skips only for genuinely absent visuals). **(BLOCKED: requires portal auth + live browser — run locally.)**
- [X] T028 Confirm `core/**` matches none of `צריכת אשראי|ממוצע הוצאות לקנייה בשגרה|תמ״צ צריכת אשראי|פורים 2026` (contract leakage clause). Do not run fleet smoke as a gate unless a later change edits `core/`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational. MVP: bilingual Screen 2 switch
- **User Story 2 (Phase 4)**: Depends on Foundational. Same page file as US1 → implement after US1. Behavior does not require US3–US5
- **User Story 3 (Phase 5)**: Depends on US2 (`apply_filters` must run before KPI asserts). Independently testable once filters work
- **User Story 4 (Phase 6)**: Depends on US2 for filters. Show-as-a-table helpers are introduced here and reused by US5. Same page file → after US3
- **User Story 5 (Phase 7)**: Depends on US1 (`open_export_page`) and US2 (Screen 2 filters) and US4 (Show-as-a-table helpers for authority)
- **Polish (Phase 8)**: Depends on all desired user stories; T026 is the mandatory credit smoke gate

### User Story Dependencies

- **User Story 1 (P1)**: After T005. No dependency on later stories. Unblocks Screen 2
- **User Story 2 (P1)**: After US1 (same file). Unblocks every golden assertion
- **User Story 3 (P1)**: After US2. Does not need toggles or Screen 2
- **User Story 4 (P1)**: After US2. Does not need Screen 2. Provides Show-as-a-table for US5 authority
- **User Story 5 (P2)**: After US1, US2, and US4 helpers. Export test does not need KPI or trend results

### Within Each User Story

- US1: `open_export_page` (T006) → navigation test (T007) → live run (T008)
- US2: `Slicer` + `apply_filters` (T009) → bilingual dates (T010) → YAML helpers (T011)
- US3: `read_kpi_metrics` (T012) → KPI test (T013)
- US4: table helpers (T014) → toggles (T015) → `read_daily_trends` (T016) → trends test (T017)
- US5: authority (T018) → daily alerts (T019) → export table (T020) → three tests (T021)

### Parallel Opportunities

- T001 and T002 (plan pin vs code/YAML inventory) touch different files and can run together
- T003 (empty sanity `__init__.py`) can run beside T004 (page move)
- T005 waits on T004 because the fixture imports the moved class
- US1–US5 all edit `pages/credit_consumption/credit_consumption_page.py` and (from T007 on) `test_data_validation.py` → run sequentially, not in parallel
- T022, T023, T024 (catalog / comments / git scope) are different files and can run together
- T026 (credit smoke) and T027 (full sanity) both need auth; they can run as two pytest invocations after collection (T025)

## Parallel Example: Phase 1 / Foundational markers / Phase 8

```bash
# Phase 1
Task: "Confirm feature.json pin and plan edit list (T001)"
Task: "Inventory Layer 0 page, smoke import, and golden YAML keys (T002)"

# After Setup
Task: "Create empty tests/sanity/credit_consumption_dashboard/__init__.py (T003)"
Task: "Move CreditConsumptionPage and re-export page.py (T004)"

# Phase 8
Task: "Add credit rows to docs/COVERAGE_CATALOG.md (T022)"
Task: "Audit English-only in-function comments (T023)"
Task: "Verify off-limits git paths and unchanged golden values (T024)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (move class, fixture)
3. Complete Phase 3: User Story 1 (`open_export_page` + navigation test)
4. **STOP and VALIDATE**: credit smoke green; Screen 2 opens with no `LoadTimeoutError`

### Incremental Delivery

1. Setup + Foundational → fixture opens Screen 1
2. US1 → bilingual Screen 2 switch (MVP)
3. US2 → golden `פורים 2026` filters
4. US3 → KPI golden match
5. US4 → four toggle series via Show-as-a-table
6. US5 → authority + export (+ optional daily alerts)
7. Polish → catalog, comment audit, credit smoke gate, full sanity module

### Parallel Team Strategy

Limited: one domain page file and one test module. A second person can own T022 (catalog) and T024 (scope audit) during Polish while page work finishes. Do not split US1–US5 across two editors of `credit_consumption_page.py` at the same time.

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [USx] maps to spec.md user stories
- Skip guards stay as a safety net; they must not fire when data is present
- Do not import `pages.alerts_analysis` helpers; duplicate Show-as-a-table on this page
- Do not add `db/clients/credit.py` or change golden metric values
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Fleet smoke is not a completion gate unless `core/` is edited later
