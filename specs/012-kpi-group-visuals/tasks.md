---
description: "Task list for Enhance Generic KPI Component to Support Group Visuals"
---

# Tasks: Enhance Generic KPI Component to Support Group Visuals

**Input**: Design documents from `/specs/012-kpi-group-visuals/`

**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/kpi-component.md, quickstart.md
(no spec.md — `/speckit-plan` was invoked directly from an inline feature request)

**Tests**: Unit tests ARE in scope (pure extraction logic). This feature changes **Layer 2**
(`core/components/kpi.py`), not `core/portal`/`ReportShell`/navigation, so fleet smoke is a **regression gate**
only (`tests/ui/fleet_dashboard/`), per Constitution III.

**Organization**: Tasks are grouped by user story. US1 is the MVP (read group-rendered KPIs); US2 is
button-path preservation & regression safety.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths are included in each task

## Path Conventions

- Validation Core layout: `core/components/` (Layer 2), `tests/unit/` (pure logic), `tests/ui/<report>/`
  (smoke), `tests/helpers/` (parity engine consumer)
- Target production file: `core/components/kpi.py`
- Target unit test file: `tests/unit/test_kpi_normalize.py`

---

## Phase 1: Setup (Baseline)

**Purpose**: Capture the pre-change baseline and the public surface that must stay stable.

- [X] T001 Record baseline: run `python -m pytest tests/unit/test_kpi_normalize.py` and note the existing `normalize_kpi_text` cases are green before edits
- [X] T002 [P] Inventory consumers of the component: run `rg "core.components.kpi|KPI\(" tests core` and confirm the public surface in use is `KPI.number/value/read_text/card` + `normalize_kpi_text` (notably `tests/helpers/db_parity_engine.py` calls `KPI.number(name)`) — these signatures MUST NOT change

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure, dependency-free helpers that both the group read path and its unit tests rely on.

**⚠️ CRITICAL**: `extract_kpi_value_text` (T004) must exist before the group value reader (T009) and the
extraction unit tests (T005) can be implemented.

- [X] T003 Refactor a `_strip_bidi(raw)` helper out of `normalize_kpi_text` in `core/components/kpi.py`, and have `normalize_kpi_text` call it — behavior of `normalize_kpi_text` MUST remain byte-for-byte identical (per contracts/kpi-component.md)
- [X] T004 Add `_NUMBER_TOKEN` regex and `extract_kpi_value_text(raw)` in `core/components/kpi.py`: strip bidi marks, return the longest numeric run (allowing internal `, . \u00a0 \u202f` + spaces), and fall back to the cleaned text when no digits are present (per data-model.md Rules 2–4) — depends on T003

**Checkpoint**: Pure numeric-extraction utilities are available and report-agnostic.

---

## Phase 3: User Story 1 - Read group-rendered KPI visuals (Priority: P1) 🎯 MVP

**Goal**: The generic `KPI` component locates and reads a KPI that Power BI renders as `role="group"`
(heading + data `img`), returning the correct number via the existing `KPI.number(title)` API.

**Independent Test**: With a group-style `aria-label` (e.g. `"אזורי התרעה ... 1,234"`),
`extract_kpi_value_text` yields `"1,234"` and `normalize_kpi_text(...)` → `"1234"`; unit suite passes. The
parity engine obtains a numeric value for a group-rendered metric with no code change.

### Tests for User Story 1

- [X] T005 [P] [US1] Add `test_extract_pulls_numeric_token_from_group_label` to `tests/unit/test_kpi_normalize.py`: plain value, Hebrew title+value bundle, RTL/bidi-wrapped value, nbsp thousands separator, decimal with trailing unit word, and no-digit fallback (`"N/A"` → `"N/A"`) — depends on T004
- [X] T006 [P] [US1] Add `test_extract_then_normalize_is_parseable` to `tests/unit/test_kpi_normalize.py`: assert `normalize_kpi_text(extract_kpi_value_text(raw))` yields the clean parseable value for mixed labels — depends on T004

### Implementation for User Story 1

- [X] T007 [US1] Add `KPI._resolve_card(title) -> tuple[Locator, str]` in `core/components/kpi.py`: try `get_by_role("button", name=re.compile(re.escape(title))).first`; if `.count() > 0` return `(button, "button")`, else return `(get_by_role("group", name=...).first, "group")` (per research.md Decision 1)
- [X] T008 [US1] Update `KPI.card(title)` to delegate to `self._resolve_card(title)[0]`, keeping its signature and return type unchanged — depends on T007
- [X] T009 [US1] Add `KPI._read_group_value(card)` in `core/components/kpi.py`: read the inner `img`'s `aria-label`, then `title`, then the group's `text_content()` (first non-empty), and return `extract_kpi_value_text(raw)` (per research.md Decision 2) — depends on T004, T007
- [X] T010 [US1] Update `KPI.read_text(title)` to resolve via `_resolve_card`, `expect(card).to_be_visible(...)`, then branch: `kind == "group"` → `_read_group_value(card)`; else keep the existing button path (`card.locator("p").last.text_content()`) byte-for-byte (per contracts/kpi-component.md) — depends on T007, T009
- [X] T011 [US1] Run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm all cases pass (17 cases) — depends on T003–T006, T009, T010

**Checkpoint**: Group-rendered KPIs are readable through the unchanged `KPI.number(title)` API. MVP complete.

---

## Phase 4: User Story 2 - Preserve button path & regression safety (Priority: P2)

**Goal**: Existing `role="button"` KPIs read exactly as before and no consumer requires changes; broader
suites remain green.

**Independent Test**: `KPI.value`/`KPI.number` are unchanged; `tests/helpers/db_parity_engine.py` needs no
edit; fleet smoke collects/passes with no KPI-component regression.

- [X] T012 [US2] Verify no consumer change is needed: `KPI.value`/`KPI.number` bodies are unchanged and `rg "core.components.kpi" tests` shows `tests/helpers/db_parity_engine.py` still calls `KPI.number(name)` unmodified (per contracts/kpi-component.md "Public Surface — unchanged")
- [ ] T013 [US2] Regression gate: run `python -m pytest tests/ui/fleet_dashboard/` and confirm 100% green (DEFERRED — requires live portal auth / configured `.env`; fleet uses its own page-object KPI methods and does not import `core/components/kpi.py`, so no button-path drift is expected). Collection verified clean 2026-10-11 (`--collect-only` → 11 fleet tests, no import errors) (Constitution III)

**Checkpoint**: Button-rendered behavior and downstream consumers are provably unaffected.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and hygiene.

- [X] T014 Audit `core/components/kpi.py` for English-only inline comments inside functions (project rule) and confirm no linter errors
- [X] T015 Run quickstart.md step 1 (unit verification) from `specs/012-kpi-group-visuals/quickstart.md`
- [ ] T016 Run quickstart.md step 3 e2e spot check: `python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -v` confirms group KPIs are read against the warehouse (DEFERRED — requires live Alerts portal + SQL Server access). Collection verified clean 2026-10-11 (`--collect-only` → `test_alerts_db_parity_last_30_days` collected, no import errors)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first.
- **Foundational (Phase 2)**: Depends on Setup. T003 → T004. BLOCKS the group read path and extraction tests.
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP.
- **User Story 2 (Phase 4)**: Depends on US1 (final method bodies must exist before verifying no drift).
- **Polish (Phase 5)**: Depends on US1 and US2.

### User Story Dependencies

- **US1 (P1)**: Core enhancement. Depends on Phase 2. Independently testable via the unit suite.
- **US2 (P2)**: Button-path preservation / regression. Depends on US1's finalized code. Independently testable
  via consumer inspection + fleet smoke.

### Within User Story 1

- T005, T006 (tests) depend only on T004 and may be written in parallel with T007.
- T007 → T008; T007 + T004 → T009 → T010 → T011.

### Parallel Opportunities

- T001 and T002 (baseline + inventory) are independent → run together.
- T005 and T006 edit the same test file as each other but are independent of T007–T010 (different file:
  `tests/unit/test_kpi_normalize.py` vs `core/components/kpi.py`) → test authoring can proceed alongside
  implementation.

---

## Parallel Example: User Story 1

```bash
# Unit tests (test file) alongside implementation (production file) — different files:
Task: "T005 Add group-label extraction tests in tests/unit/test_kpi_normalize.py"
Task: "T007 Add KPI._resolve_card button->group fallback in core/components/kpi.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (baseline + consumer inventory).
2. Phase 2: Foundational (`_strip_bidi`, `extract_kpi_value_text`).
3. Phase 3: US1 (locator fallback + group value read + unit tests).
4. **STOP and VALIDATE**: `python -m pytest tests/unit/test_kpi_normalize.py` is green.

### Incremental Delivery

1. Setup + Foundational → pure helpers ready.
2. US1 → group KPIs readable via unchanged public API (MVP).
3. US2 → confirm button path & consumers unaffected (fleet regression gate).
4. Polish → comment/lint audit + quickstart verification.

---

## Notes

- [P] tasks = different files, no dependencies.
- The `role="button"` branch of `read_text` is preserved byte-for-byte; only the group branch and pure helpers
  are added.
- `tests/helpers/db_parity_engine.py` and all other consumers require NO changes (uniform `KPI.number(title)`).
- Live-auth tasks (T013 fleet smoke, T016 Alerts parity) are deferred to an environment with portal + DB
  access; all logic is otherwise complete and unit-verified.
- Implementation for this feature was completed in the prior `/speckit-implement` run; `[X]` reflects shipped,
  verified work (17/17 unit cases passing, no linter errors).
