---
description: "Task list for Contextual Scoping for Duplicate KPI Visual Names"
---

# Tasks: Contextual Scoping for Duplicate KPI Visual Names

**Input**: Design documents from `/specs/014-kpi-contextual-scope/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/kpi-component.md, quickstart.md

**Tests**: No new unit suite (plan: host resolution needs a live iframe). Existing
`tests/unit/test_kpi_normalize.py` is an extract-path **regression** only. Fleet smoke
(`tests/ui/fleet_dashboard/`) is the Constitution III gate. Do **not** add TDD locator tests.

**Organization**: US1 is the MVP (scoped lookup). US2 is one-argument / global-search compatibility.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths are included in each task

## Path Conventions

- Target production file: `core/components/kpi.py`
- Extract regression: `tests/unit/test_kpi_normalize.py`
- Consumer (must stay one-argument): `tests/helpers/db_parity_engine.py`

---

## Phase 1: Setup (Baseline)

**Purpose**: Capture the pre-change baseline and the public surface that must stay compatible.

- [X] T001 Record baseline: run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm extract/normalize (including Gauge) cases are green before edits
- [X] T002 [P] Inventory consumers: run `rg "core.components.kpi|KPI\(|kpi\.(number|value|read_text|card)\(" tests core` and confirm `tests/helpers/db_parity_engine.py` calls `KPI.number(name)` with one argument — that call MUST remain valid after adding optional `scope` (per contracts/kpi-component.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the host resolver both stories use. Do **not** change `card` / `read_text` / `value` /
`number` signatures yet.

**⚠️ CRITICAL**: `_scope_host` (T003) must exist before `_resolve_card` is switched onto a host (T004).

- [X] T003 Add `KPI._scope_host(self, scope: str | None)` in `core/components/kpi.py` returning `FrameLocator | Locator`: if `scope` is `None` or whitespace-only, return `self._frame`; else `self._frame.get_by_role("group", name=re.compile(re.escape(scope))).first` when `.count() > 0`; else `self._frame.get_by_role("group").filter(has_text=re.compile(re.escape(scope))).first`. MUST NOT use `locator("*").filter(has_text=...)`. English comments only; no report section titles in `core/` (per research.md Decision 2, data-model.md Rules 1–3)

**Checkpoint**: Host resolution exists; public methods still search the full iframe.

---

## Phase 3: User Story 1 - Scoped KPI lookup (Priority: P1) 🎯 MVP

**Goal**: Callers can pass `scope` so title search runs inside the matching parent `role="group"`,
disambiguating duplicate KPI titles.

**Independent Test**: `card(title, scope=section)` / `read_text` / `value` / `number` chain from
`_scope_host` then the existing button→group title search. `scope` is an opaque string — `core/`
contains no section titles such as "היום". Blank/`None` still uses `self._frame`.

### Implementation for User Story 1

- [X] T004 [US1] Update `KPI._resolve_card(self, title: str, scope: str | None = None)` in `core/components/kpi.py` to take `host = self._scope_host(scope)` and run the existing button-then-group search (`re.compile(re.escape(title))`, `.first`) on `host` instead of `self._frame` (per data-model.md pipeline) — depends on T003
- [X] T005 [US1] Thread `scope: str | None = None` through `card`, `read_text`, `value`, and `number` in `core/components/kpi.py`: each method passes `scope` into `_resolve_card` / `read_text` as needed; `_read_group_value`, `extract_kpi_value_text`, and `normalize_kpi_text` MUST stay unchanged (per FR-001, FR-004, contracts/kpi-component.md) — depends on T004
- [X] T006 [US1] Audit `core/components/kpi.py`: no `locator("*")` has_text host; no hardcoded section/KPI titles; new/updated docstrings and inline comments are English only (FR-002, FR-005, Constitution II)

**Checkpoint**: Scoped lookup is available. MVP complete.

---

## Phase 4: User Story 2 - Backward-compatible global search (Priority: P2)

**Goal**: Omitting `scope` keeps today's iframe-wide button→group `.first` search; existing callers
need no edit.

**Independent Test**: `KPI.number(title)` still accepts one argument. `tests/helpers/db_parity_engine.py`
is unmodified. `tests/unit/test_kpi_normalize.py` stays green.

- [X] T007 [US2] Verify one-argument compatibility: `card` / `read_text` / `value` / `number` in `core/components/kpi.py` default `scope=None`, and `rg "kpi\.number\(" tests/helpers/db_parity_engine.py` still shows `KPI.number(name)` with no `scope` (per contracts/kpi-component.md, FR-003)
- [X] T008 [US2] Run `python -m pytest tests/unit/test_kpi_normalize.py` and confirm extract/normalize cases still pass (scope is locate-only; Gauge rows from 013 must remain green)
- [X] T009 [US2] Regression gate: run `python -m pytest tests/ui/fleet_dashboard/` and confirm 100% green (DEFERRED — live portal auth not run; `--collect-only` 2026-10-13 → 11 fleet tests, no import errors) (Constitution III)

**Checkpoint**: Global unique-title path and downstream consumers are provably unaffected.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and hygiene.

- [X] T010 Confirm no linter errors on `core/components/kpi.py` after the signature changes
- [X] T011 Run quickstart.md steps 1–2 from `specs/014-kpi-contextual-scope/quickstart.md` (unit extract suite + `rg` on `tests/helpers/db_parity_engine.py`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first.
- **Foundational (Phase 2)**: Depends on Setup. T003 BLOCKS US1 locate wiring.
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP.
- **User Story 2 (Phase 4)**: Depends on US1 (final signatures must exist before compatibility proof).
- **Polish (Phase 5)**: Depends on US1–US2.

### User Story Dependencies

- **US1 (P1)**: Scoped lookup. Depends on Phase 2. Independently testable by calling methods with a
  non-empty `scope` (host is a group, not the iframe).
- **US2 (P2)**: Global default. Depends on US1's finalized signatures. Independently testable via
  one-argument calls + extract suite + consumer `rg`.

### Within User Story 1

- T004 → T005 → T006.

### Parallel Opportunities

- T001 and T002 (baseline + inventory) are independent → run together.
- T007 (inspection) can overlap with T008 (unit re-run) — no file conflict.

---

## Parallel Example: User Story 2

```bash
# Inspection vs extract regression — different work, no shared writes:
Task: "T007 Verify KPI.number(name) still one-arg in tests/helpers/db_parity_engine.py"
Task: "T008 Run tests/unit/test_kpi_normalize.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (baseline + consumer inventory).
2. Phase 2: Foundational (`_scope_host`).
3. Phase 3: US1 (wire `scope` through resolve + public methods).
4. **STOP and VALIDATE**: `_resolve_card(title, scope=...)` searches under a group host.

### Incremental Delivery

1. Setup + Foundational → host helper ready, public API unchanged.
2. US1 → scoped lookup (MVP).
3. US2 → confirm default path and consumers.
4. Polish → lint + quickstart steps 1–2.

---

## Notes

- [P] tasks = different files, no dependencies.
- Do **not** change `extract_kpi_value_text`, `normalize_kpi_text`, `_read_group_value`, or
  `tests/helpers/db_parity_engine.py`.
- Do **not** add a YAML `scope` field (research.md Decision 4).
- Do **not** hardcode report section titles in `core/`.
- Live-auth fleet smoke (T009) may be deferred; record `--collect-only` if deferred.
- All inline comments MUST be English only.
