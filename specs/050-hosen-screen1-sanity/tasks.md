---
description: "Task list for Hosen Status Screen 1 golden-YAML sanity"
---

# Tasks: Hosen Status Screen 1 YAML Sanity

**Input**: Design documents from `/specs/050-hosen-screen1-sanity/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/hosen-screen1-sanity.md, quickstart.md

**Tests**: The feature is the page reader plus `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` (FR-006). Hosen smoke (`pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`) is the navigation gate and must stay a one-line `verify_freshness()` call (FR-009). Fleet smoke is not a gate: `core/`, Layer 0, and the fleet page are not edited.

**Organization**: Tasks follow the four user stories in spec.md. US1 builds the reader entry point and the compare rules. US2–US4 fill one golden block each from the live landing screen so that block can be checked on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 from spec.md
- Exact file paths are included in every task

## Path Conventions

- Page: `pages/hosen_status/page.py` (`HosenStatusPage`)
- Golden record (created here): `data/hosen/db_sanity.yaml`
- Sanity package: `tests/sanity/hosen_status_dashboard/`
- Existing smoke (do not edit): `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` and `tests/ui/hosen_status_dashboard/conftest.py`
- Coverage catalog: `docs/COVERAGE_CATALOG.md`
- Contract: `specs/050-hosen-screen1-sanity/contracts/hosen-screen1-sanity.md`
- OFF-LIMITS: `core/portal/`, `core/components/`, `data/hasbara/`, `data/credit/`, `data/alerts/`, Hasbara/Credit/Alerts page modules and tests, `db/`, root `conftest.py`

Do not add `pages/hosen_status/__init__.py`. Comments and new Python names stay English. Hebrew stays in locator constants on the page or in the YAML. Do not call `sleep`, `wait_for_timeout`, or a network-idle wait. Do not read a canvas bitmap. Do not import Hasbara, Credit, or Alerts modules.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the pin, the off-limits list, and the existing Layer 0 binding before adding readers

- [X] T001 Confirm `.specify/feature.json` contains `"feature_directory": "specs/050-hosen-screen1-sanity"` and that `specs/050-hosen-screen1-sanity/plan.md` edits only `pages/hosen_status/page.py`, `data/hosen/db_sanity.yaml`, `tests/sanity/hosen_status_dashboard/`, and `docs/COVERAGE_CATALOG.md`. Git checkout stays `feature/reportportal-integration`.
- [X] T002 [P] Inventory (read-only, do not edit): in `pages/hosen_status/page.py` confirm `HosenStatusPage` subclasses `ReportShell`, `DASHBOARD_SEARCH_TERM` is `תמ"צ חוסן`, `_report_ready_locator` uses exact text `תמ"צ ארצי - דיווחי קה"א יקל"ר`, and `LAST_REFRESH_PHRASE` is `מועד רענון`. In `tests/ui/hosen_status_dashboard/conftest.py` confirm `bind_dashboard(HosenStatusPage)` with fixture name `dashboard`. In `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` confirm the body is `dashboard.verify_freshness()`. Confirm `Slicer.control` exists in `core/components/slicer.py`, `KPI.card` and `KPI.read_text` exist in `core/components/kpi.py`, and `collect_virtualized_rows` exists in `core/components/virtual_grid.py`. Confirm root `conftest.py` does not import this page.

**Checkpoint**: Scope and Layer 0 inventory confirmed. No files changed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Sanity package, fixture, and an empty golden root so every story can open Screen 1 and write one block

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create an empty `tests/sanity/hosen_status_dashboard/__init__.py`. Do not add `pages/hosen_status/__init__.py`.
- [X] T004 [P] Add `hosen_status_dashboard = bind_dashboard(HosenStatusPage, "hosen_status_dashboard")` to `tests/sanity/hosen_status_dashboard/conftest.py`, importing `bind_dashboard` from `tests.helpers.dashboard_fixture` and `HosenStatusPage` from `pages.hosen_status.page`. Do not edit `tests/ui/hosen_status_dashboard/conftest.py` or root `conftest.py`.
- [X] T005 [P] Create `data/hosen/db_sanity.yaml` (UTF-8) with root `hosen_dashboard` and `screen_1_landing: {}` only. Do not invent counts, percentages, authority names, or filter labels. US2–US4 write the live blocks into this file.

**Checkpoint**: The sanity fixture can open תמ"צ חוסן. The golden file has an empty `screen_1_landing`. User stories can start.

---

## Phase 3: User Story 1 - Landing screen matches the golden YAML (Priority: P1) 🎯 MVP

**Goal**: `read_screen_1_metrics()` returns the four blocks, and one sanity test walks `screen_1_landing` with subset, integer, and exact-string rules. Smoke stays a freshness check.

**Independent Test**: `pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` passes. `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` opens the report, receives `survey_status`, `kpis`, `resilience_scores`, and `active_filters`, and compares whatever keys are already in `screen_1_landing`.

### Implementation for User Story 1

- [X] T006 [US1] In `pages/hosen_status/page.py`, add `read_screen_1_metrics(self) -> dict` that returns `survey_status`, `kpis`, `resilience_scores`, and `active_filters` by calling four private methods on this page (`_read_survey_status`, `_read_kpis`, `_read_resilience_scores`, `_read_active_filters`). Each private method returns the empty shape from `specs/050-hosen-screen1-sanity/data-model.md` until US2–US4 replace its body. Keep `navigate` and `verify_freshness` unchanged. English comments only (FR-001, AC-004).
- [X] T007 [P] [US1] Create `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` with private helpers (do not import Hasbara, Credit, or Alerts; do not add a file under `tests/helpers/`). Load `Path(__file__).resolve().parents[3] / "data" / "hosen" / "db_sanity.yaml"` as UTF-8 and read `hosen_dashboard.screen_1_landing`. `@pytest.mark.sanity` `test_hosen_screen1_matches_golden(hosen_status_dashboard)` calls `read_screen_1_metrics()` once. Require the four keys on the UI dict. Walk every golden key (extra UI rows, categories, names, and slicers do not fail). YAML `int` matches display text after removing bidi marks (`\u200f`, `\u200e`, `\u202a`, `\u202b`, `\u202c`), commas, spaces, and `\u00a0` (so `1324` matches `1,324` and `1324`). YAML `str` matches after bidi marks and outer whitespace are removed (`55%` stays a string). A golden dict or list that has data fails when the UI value is empty and that section's anchor is visible. `pytest.skip` only the block whose anchor is not rendered. Import the fixture from `tests.sanity.hosen_status_dashboard.conftest`. Do not hard-code `7`, `12`, or `55%`. English comments only (FR-006, FR-007, FR-008).

**Checkpoint**: Screen 1 returns the four-key dict and the compare rules are in the sanity module. Golden blocks are still empty, so value checks start with US2.

---

## Phase 4: User Story 2 - Survey status counts and missing authorities (Priority: P1)

**Goal**: The top-left block supplies submitted count, total count, and missing authority names, and those values are the `survey_status` golden block.

**Independent Test**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` matches `screen_1_landing.survey_status` (both integers, and every golden missing name). Extra names on screen do not fail.

### Implementation for User Story 2

- [X] T008 [US2] Replace `_read_survey_status` in `pages/hosen_status/page.py`. Wait with `expect` until the top-left survey anchor is visible, bounded by `self.timeout`. Return `submitted` and `total` as digit strings and `missing_authorities` as a list of name strings. Keep the Hebrew phrases in this file. Do not add a Layer 2 reader. Do not sample a canvas (FR-005, FR-011).
- [X] T009 [US2] Open the landing screen once, copy the live survey reading into `data/hosen/db_sanity.yaml` under `hosen_dashboard.screen_1_landing.survey_status` (`submitted` and `total` as integers, `missing_authorities` as strings). Do not type example numbers from the plan (`7`, `12`) unless that is what the screen shows (FR-012).

**Checkpoint**: `survey_status` is frozen from the live screen and the sanity test checks that block. KPI, resilience, and filter blocks are still absent from the YAML.

---

## Phase 5: User Story 3 - National assessment and category KPIs (Priority: P1)

**Goal**: `הערכת קה״א - ממוצע ארצי` and the category cards in that visual return title, percentage (with `%`), and trend (`up`, `down`, or `flat`).

**Independent Test**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` matches `kpis.national_average` and every `kpis.categories` item on `title`. Extra category cards do not fail. A visible card with an empty percentage fails when the golden card has a percentage.

### Implementation for User Story 3

- [X] T010 [US3] Replace `_read_kpis` in `pages/hosen_status/page.py`. Compose `KPI` from `core.components.kpi` with the report page and report iframe. Confirm the national accessible name (gershayim `״` versus `"`) and store that spelling in a page constant and, in T011, in the YAML `title`. Locate the card with `KPI.card`. Keep `%` in `percentage`: use `KPI.read_text` when it still contains `%`; when the group path returns digits only, take the `%` token from that same card's text. Do not call `KPI.number` and do not edit `extract_kpi_value_text`. Set `trend` from a non-canvas node inside the card: direction glyph first (`up` / `down` / `flat`); if there is no glyph, green → `up`, red → `down`, yellow → `flat`. If the only signal is a canvas, return `trend: ""`. `categories` is every other button or group card in the visual that contains the national title, each with `title`, `percentage`, and `trend`. English comments only (FR-003, FR-011).
- [X] T011 [US3] Copy the live KPI reading into `data/hosen/db_sanity.yaml` under `hosen_dashboard.screen_1_landing.kpis` (`national_average` plus `categories`). `percentage` values stay strings that include `%`. `trend` is `up`, `down`, or `flat`. Do not invent `55%` (FR-012).

**Checkpoint**: National and category cards match the golden `kpis` block. Survey status from US2 still matches.

---

## Phase 6: User Story 4 - Resilience scores and selected filters (Priority: P1)

**Goal**: `ציון חוסן` rows supply authority, score, and `green` or `yellow`. Right-hand slicers supply the selected labels. Nothing is clicked.

**Independent Test**: `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` matches every golden `resilience_scores` row on `authority` and every `active_filters` id. Extra authorities and extra slicers do not fail. An empty row list fails when the table title is visible and the golden list is non-empty.

### Implementation for User Story 4

- [X] T012 [US4] Replace `_read_active_filters` in `pages/hosen_status/page.py`. Compose `Slicer` from `core.components.slicer` with `SlicerDefinition` rows whose `id` is `district` and `sub_district` (add another id only when the live right-hand rail has another selected dropdown). Copy each Hebrew `role_name` from the live combobox. `kind` is `dropdown`. Read `Slicer.control(id)` after it is visible and return the selected label with the role name and bidi marks removed. Do not call `select`, `apply`, or `clear_all`. Do not edit `core/components/slicer.py` (FR-002).
- [X] T013 [US4] Replace `_read_resilience_scores` in `pages/hosen_status/page.py`. Wait until `ציון חוסן` is visible. Pass that visual's grid to `collect_virtualized_rows` from `core.components.virtual_grid` with `timeout_ms=self.timeout`. The visible-row callback returns `authority`, score text, and `status`. `row_id` is the authority name. Map computed background of the row or the score cell: green-dominant → `green`; high red and green with low blue → `yellow`; any other color → the raw `rgb(...)` string. Skip `canvas` nodes. Do not edit `core/components/virtual_grid.py` (FR-004, FR-011).
- [X] T014 [US4] Copy the live filter labels and resilience rows into `data/hosen/db_sanity.yaml` under `hosen_dashboard.screen_1_landing.active_filters` and `resilience_scores`. Whole-number scores are YAML integers; any other score stays a string. `status` is `green` or `yellow`. Use `מחוז דרום` and `נפת לכיש` only when those are the selected labels on screen (FR-012).

**Checkpoint**: All four golden blocks are populated from the live landing screen. The single sanity test compares each of them.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Catalog row, off-limits audit, and the quickstart commands

- [X] T015 [P] Add a Hosen section to `docs/COVERAGE_CATALOG.md` mapping `survey_status`, `kpis`, `resilience_scores`, and `active_filters` to `HosenStatusPage.read_screen_1_metrics()` and `test_hosen_screen1_matches_golden`. State that the source is `data/hosen/db_sanity.yaml`, not SQL.
- [X] T016 [P] Audit the diff for this slice. It may change `pages/hosen_status/page.py`, `data/hosen/db_sanity.yaml`, `tests/sanity/hosen_status_dashboard/`, `docs/COVERAGE_CATALOG.md`, `.specify/feature.json`, `.cursor/rules/specify-rules.mdc`, and `specs/050-hosen-screen1-sanity/`. It must not change `core/`, `data/hasbara/`, `data/credit/`, `data/alerts/`, Hasbara/Credit/Alerts pages or tests, `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py`, or root `conftest.py` (FR-010).
- [X] T017 Run `pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` and `pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` from `specs/050-hosen-screen1-sanity/quickstart.md`. Smoke still calls `verify_freshness()`. The sanity test fails with a YAML path when a golden key differs, and when a visible section is empty while its golden block has data (SC-001, SC-004).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational. US2, US3, and US4 also depend on US1 because they replace private methods and extend the test created in T006 and T007
- **Polish (Phase 7)**: Depends on US2, US3, and US4 so the YAML blocks and the catalog describe the same reader

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No dependency on US2–US4. MVP is the four-key reader and the compare module
- **User Story 2 (P1)**: Starts after US1. Writes only `survey_status`
- **User Story 3 (P1)**: Starts after US1. Can follow US2. Writes only `kpis`. Same page file as US2, so do not edit `_read_survey_status` in parallel
- **User Story 4 (P1)**: Starts after US1. Can follow US3. Writes `active_filters` and `resilience_scores`. Same page file, so run T012 then T013

### Within Each User Story

- Reader body in `pages/hosen_status/page.py` before the live copy into `data/hosen/db_sanity.yaml`
- US1 compare helpers land before any story expects a value failure
- A story's YAML block is what makes that story's independent pytest check meaningful

### Parallel Opportunities

- T002 can run with T001 (read-only, different files)
- T003, T004, and T005 can run together (new files, no overlap)
- T007 can be written with T006 (test module vs page module)
- T015 and T016 can run together after the stories
- US2, US3, and US4 are not parallel: they all edit `pages/hosen_status/page.py` and `data/hosen/db_sanity.yaml`

---

## Parallel Example: User Story 1

```text
# Different files, after Phase 2:
T006  pages/hosen_status/page.py                         read_screen_1_metrics + four private stubs
T007  tests/sanity/hosen_status_dashboard/test_screen1_sanity.py   subset compare
```

US2, US3, and US4 have no parallel split. Each story edits the page, then the YAML.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Smoke passes, and the sanity test opens Screen 1 and sees the four keys

### Incremental Delivery

1. Setup + Foundational → fixture opens the report, golden root exists
2. User Story 1 → compare rules and the public reader (MVP)
3. User Story 2 → live `survey_status` matches
4. User Story 3 → live `kpis` match; survey status still matches
5. User Story 4 → live resilience rows and selected filters match
6. Polish → catalog, off-limits audit, both pytest commands

### Parallel Team Strategy

After Foundational, one person owns `pages/hosen_status/page.py` and `data/hosen/db_sanity.yaml` and takes US1 → US2 → US3 → US4 in order. A second person can write T007 while T006 is in progress, then wait for the page before capturing YAML.

---

## Notes

- `[P]` tasks use different files and do not depend on an unfinished task
- `[US1]`–`[US4]` map to spec.md stories
- Numbers live only in `data/hosen/db_sanity.yaml` after a live read
- `core/` stays unchanged; `Slicer`, `KPI`, and `collect_virtualized_rows` are called, not edited
- Stop at any checkpoint and run that story's pytest command
