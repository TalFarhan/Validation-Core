---
description: "Task list for Support Power BI Gauge Visual Parsing in KPI Component"
---

# Tasks: Support Power BI Gauge Visual Parsing in KPI Component

**Input**: Design documents from `/specs/013-kpi-gauge-visuals/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/kpi-component.md, quickstart.md

**Tests**: Unit tests ARE in scope (explicit request + FR-004). This feature changes **Layer 2**
(`core/components/kpi.py`), not `core/portal`/`ReportShell`/navigation, so fleet smoke is a **regression
gate** only (`tests/ui/fleet_dashboard/`), per Constitution III.

**Organization**: Tasks are grouped by user story. US1 is the MVP (labeled Gauge current value); US2 is
compact three-token Gauges; US3 is standard-KPI fallback and regression safety.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in each task

## Path Conventions

- Validation Core layout: `core/components/` (Layer 2), `tests/unit/` (pure logic), `tests/ui/<report>/`
  (smoke), `tests/helpers/` (parity engine consumer)
- Target production file: `core/components/kpi.py`
- Target unit test file: `tests/unit/test_kpi_normalize.py`

---

## Phase 1: Setup (Baseline)

**Purpose**: Capture the pre-change baseline and the public surface that must stay stable.

- [X] T001 Record baseline: run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm existing `normalize_kpi_text` / `extract_kpi_value_text` cases are green before edits
- [X] T002 [P] Inventory consumers: run `rg "core.components.kpi|KPI\(" tests core` and confirm the public surface in use is `KPI.number/value/read_text/card` + `normalize_kpi_text` (notably `tests/helpers/db_parity_engine.py` calls `KPI.number(name)`) — these signatures MUST NOT change (per contracts/kpi-component.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the two module regexes that labeled and compact Gauge detection share. Do **not** change
`extract_kpi_value_text` yet.

**⚠️ CRITICAL**: No user-story extract logic until T003 and T004 exist. Do not edit `_NUMBER_TOKEN` (space-as-thousands fallback must stay).

- [X] T003 Add `_NUMBER_TOKEN_COMPACT` in `core/components/kpi.py` as `re.compile(r"-?\d[\d.,\u00a0\u202f]*\d|-?\d")` (no ASCII space) with an English comment that it is for Gauge detection only (per data-model.md New Symbols)
- [X] T004 Add `_GAUGE_BOUND_PAIR` in `core/components/kpi.py`: match generic chrome `ערך מינימלי` / `ערך מקסימלי` / `Minimum value` / `Maximum value` (English case-insensitive) each followed by a compact number and an optional `.` — MUST NOT include report metric titles (per research.md Decision 3, contracts/kpi-component.md) — depends on T003

**Checkpoint**: Compact and bound-pair regexes exist; existing extract behavior is still unchanged.

---

## Phase 3: User Story 1 - Labeled Gauge current value (Priority: P1) 🎯 MVP

**Goal**: Labeled Gauge accessibility strings (Hebrew or English min/max chrome) yield only the current
value via the existing `extract_kpi_value_text` → `normalize_kpi_text` pipeline.

**Independent Test**: `extract_kpi_value_text("distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337.")`
returns `"3"`; English chrome also returns the current figure; `normalize_kpi_text(...)` → `"3"`. Concatenated
results (`"1337133733"`, `"1,337"` as the "value") MUST NOT occur.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T006)**

- [X] T005 [US1] Add labeled Gauge rows to `tests/unit/test_kpi_normalize.py` in `test_extract_pulls_numeric_token_from_group_label` and `test_extract_then_normalize_is_parseable`: Hebrew `"distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337."` → extract `"3"` / normalize `"3"`; English `"Minimum value 0. Maximum value 1,337. 3"` → extract `"3"` / normalize `"3"` (per contracts/kpi-component.md Examples) — confirm they FAIL on current longest-token behavior — depends on T001

### Implementation for User Story 1

- [X] T006 [US1] Update `extract_kpi_value_text` in `core/components/kpi.py`: after `_strip_bidi`, if `_GAUGE_BOUND_PAIR` matches, `sub` all bound pairs out of the string and return the existing longest `_NUMBER_TOKEN` on the remainder (or the cleaned remainder if no digits) (per research.md Decision 2 labeled path, data-model.md Rule 2) — depends on T004, T005
- [X] T007 [US1] Run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm labeled Gauge cases pass and all pre-existing extract/normalize cases still pass — depends on T005, T006

**Checkpoint**: Labeled Gauges return the current value. MVP complete.

---

## Phase 4: User Story 2 - Compact Gauge current value (Priority: P2)

**Goal**: Compact three-number Gauge labels (`min max current`) yield the last token; two-token
space-thousands strings are not treated as Gauges.

**Independent Test**: `extract_kpi_value_text("0 1,337 3")` returns `"3"`. `"Population 1 234"` still
returns `"1 234"`.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation (T009)**

- [X] T008 [US2] Add compact Gauge rows to `tests/unit/test_kpi_normalize.py` in `test_extract_pulls_numeric_token_from_group_label` and `test_extract_then_normalize_is_parseable`: `"0 1,337 3"` → extract `"3"` / normalize `"3"` (per contracts/kpi-component.md Examples) — confirm they FAIL until T009 — depends on T007

### Implementation for User Story 2

- [X] T009 [US2] Update `extract_kpi_value_text` in `core/components/kpi.py`: after the labeled branch, if `_NUMBER_TOKEN_COMPACT.findall` yields **exactly three** tokens, return the last token stripped; otherwise keep the existing longest `_NUMBER_TOKEN` fallback (per research.md Decision 2 compact path, data-model.md Rule 3) — depends on T003, T008
- [X] T010 [US2] Run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm compact + labeled + existing cases all pass — depends on T008, T009

**Checkpoint**: Compact Gauges return the current value; space-thousands labels are unchanged.

---

## Phase 5: User Story 3 - Standard KPI fallback (Priority: P3)

**Goal**: Non-Gauge strings keep feature-012 behavior; public API and consumers are untouched; fleet smoke
is the Constitution III regression gate.

**Independent Test**: Existing `test_extract_*` / `test_normalize_*` cases stay green; `rg` shows
`tests/helpers/db_parity_engine.py` still calls `KPI.number(name)` unmodified; button path in
`KPI.read_text` is unedited.

- [X] T011 [US3] Re-run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm fallback rows still match contracts/kpi-component.md Examples: `"אזורי התרעה 1,234"` → `"1,234"`, `"Population 1 234"` → `"1 234"`, `"avg 3.5 days"` → `"3.5"`, `"N/A"` → `"N/A"` — depends on T010
- [X] T012 [US3] Verify no consumer or locator change: `KPI.card` / `read_text` / `value` / `number` signatures and the `role="button"` branch of `read_text` in `core/components/kpi.py` are unedited, and `tests/helpers/db_parity_engine.py` still calls `KPI.number(name)` (per contracts/kpi-component.md Public Surface)
- [X] T013 [US3] Regression gate: run `python -m pytest tests/ui/fleet_dashboard/` and confirm 100% green (DEFERRED — live portal auth not run; `--collect-only` 2026-10-12 → 11 fleet tests, no import errors) (Constitution III)

**Checkpoint**: Standard KPI extraction and downstream consumers are provably unaffected.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and hygiene.

- [X] T014 Audit `core/components/kpi.py` and `tests/unit/test_kpi_normalize.py` for English-only inline comments (project rule / FR-006) and confirm no linter errors
- [X] T015 Run quickstart.md step 1 (unit verification) from `specs/013-kpi-gauge-visuals/quickstart.md`
- [X] T016 Run quickstart.md step 3 e2e spot check: `python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -v` (DEFERRED — live Alerts portal + SQL Server not run; `--collect-only` 2026-10-12 → `test_alerts_db_parity_last_30_days` collected, no import errors)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first.
- **Foundational (Phase 2)**: Depends on Setup. T003 → T004. BLOCKS US1 labeled implementation (T006) and US2 compact implementation (T009).
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP.
- **User Story 2 (Phase 4)**: Depends on US1 unit suite being green so compact tests are added on a known baseline. Independently testable via compact strings.
- **User Story 3 (Phase 5)**: Depends on US1 + US2 (final extract body must exist before fallback/regression proof).
- **Polish (Phase 6)**: Depends on US1–US3.

### User Story Dependencies

- **US1 (P1)**: Labeled Gauge extract. Depends on Phase 2. Independently testable via Hebrew/English labeled strings.
- **US2 (P2)**: Compact Gauge extract. Depends on US1 checkpoint (same function). Independently testable via `"0 1,337 3"`.
- **US3 (P3)**: Fallback + regression. Depends on the final `extract_kpi_value_text`. Independently testable via existing unit cases + consumer inspection.

### Within Each User Story

- Tests MUST be written and FAIL before implementation (T005 before T006; T008 before T009).
- Regexes (Phase 2) before extract branches.
- Story unit run before moving to the next priority.

### Parallel Opportunities

- T001 and T002 (baseline + inventory) are independent → run together.
- After T004, T005 (test file) can start immediately; T006 waits for T005 to fail first.
- T012 (inspection) can overlap with T011 (unit re-run) — different kind of work, no file conflict.

---

## Parallel Example: User Story 1

```bash
# After Phase 2, baseline inventory can still overlap with the first failing test:
Task: "T002 Inventory KPI consumers in tests/ and core/"
Task: "T005 Add failing labeled Gauge cases in tests/unit/test_kpi_normalize.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (baseline + consumer inventory).
2. Phase 2: Foundational (`_NUMBER_TOKEN_COMPACT`, `_GAUGE_BOUND_PAIR`).
3. Phase 3: US1 (failing labeled tests → labeled pre-pass → unit green).
4. **STOP and VALIDATE**: labeled Gauge strings extract `"3"`.

### Incremental Delivery

1. Setup + Foundational → regexes ready, extract unchanged.
2. US1 → labeled Gauges parse (MVP).
3. US2 → compact Gauges parse.
4. US3 → fallback + fleet regression gate.
5. Polish → comments/lint + quickstart verification.

---

## Notes

- [P] tasks = different files, no dependencies.
- Do **not** change `_NUMBER_TOKEN`, `normalize_kpi_text`, `KPI` locators, or the parity engine.
- Bound phrases are generic Power BI Gauge chrome only — no Alerts KPI titles in `core/`.
- Live-auth tasks (T013 fleet smoke, T016 Alerts parity) may be deferred to an environment with portal + DB
  access; record `--collect-only` if deferred.
- All inline comments MUST be English only.
