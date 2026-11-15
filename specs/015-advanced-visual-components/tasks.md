---
description: "Task list for Advanced Power BI Visual Components"
---

# Tasks: Advanced Power BI Visual Components

**Input**: Design documents from `/specs/015-advanced-visual-components/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md,
contracts/gauge-scale.md, contracts/visual-reading.md, contracts/chart-component.md, quickstart.md

**Tests**: FR-009 requires portal-free unit tests. Write each story's tests first and confirm they
fail before the matching implementation. Fleet smoke (`pytest tests/ui/fleet_dashboard/`) is the
Constitution III gate because `core/components/kpi.py` changes. Do **not** add live-portal tests.

**Organization**: US1 is the MVP (gauge scale numbers). US2 adds empty-versus-zero. US3 adds the
bar/column reader. US4 adds the dynamic displayed title. US1–US3 are P1; US4 is P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths are included in each task

## Path Conventions

- Production: `core/components/kpi.py`, `core/components/visual.py`, `core/components/chart.py`, `core/components/__init__.py`
- Unit tests: `tests/unit/test_gauge_scale.py`, `tests/unit/test_visual_state.py`, `tests/unit/test_chart_shape.py`
- Untouched consumers: `tests/helpers/db_parity_engine.py`, `pages/fleet_dashboard/main_dashboard_page.py`

---

## Phase 1: Setup (Baseline)

**Purpose**: Record the pre-change KPI contract so later edits cannot silently change `number()`.

- [X] T001 Run `python -m pytest tests/unit/test_kpi_normalize.py -v` and confirm every extract/normalize row is green, including the labeled and compact Gauge rows, before any edit
- [X] T002 [P] Inventory the parity caller: run `rg "kpi\.number\(" tests/helpers/db_parity_engine.py` and confirm it calls `KPI.number(name)` with one argument — that call MUST stay valid (per contracts/gauge-scale.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: One scope-host implementation for `KPI` and `Chart`. Do **not** change scale parsing,
presence, or chart reading in this phase.

**⚠️ CRITICAL**: No user story locate-path work starts until `scope_host` exists and `KPI` delegates to it.

- [X] T003 Add `scope_host(frame, scope: str | None)` in `core/components/visual.py`: `None` or whitespace returns `frame`; else `frame.get_by_role("group", name=re.compile(re.escape(scope.strip()))).first` when `.count() > 0`; else `frame.get_by_role("group").filter(has_text=that pattern).first`. MUST NOT use `locator("*").filter(has_text=...)`. English comments only; no report titles (per research.md Decision 6, data-model.md Scope host)
- [X] T004 Replace the body of `KPI._scope_host` in `core/components/kpi.py` with a delegate to `scope_host(self._frame, scope)`. Do not change `card`, `read_text`, `value`, `number`, `extract_kpi_value_text`, or `normalize_kpi_text` (per research.md Decision 6) — depends on T003

**Checkpoint**: Host resolution is shared. Public KPI results are unchanged.

---

## Phase 3: User Story 1 - Gauge scale as structured data (Priority: P1) 🎯 MVP

**Goal**: `extract_gauge_scale` / `KPI.scale` return `value`, `minimum`, and `maximum`. A slash
denominator is `maximum`. Missing limits are `None`, not `0`. `KPI.number` stays as it is today.

**Independent Test**: `python -m pytest tests/unit/test_gauge_scale.py -v` with no browser. Labeled,
compact, slash, single-figure, rendered `0`, and blank-string rows match contracts/gauge-scale.md.
`extract_kpi_value_text` on those strings is unchanged.

### Tests for User Story 1

- [X] T005 [P] [US1] Add failing tests in `tests/unit/test_gauge_scale.py` that import `extract_gauge_scale` and `extract_kpi_value_text` from `core/components/kpi.py`. Cover the normative rows in `specs/015-advanced-visual-components/contracts/gauge-scale.md`: labeled Hebrew chrome, labeled English chrome, compact `0 1,337 3` → value 3 / min 0 / max 1337, slash `3 / 10` → value 3 / min None / max 10, single `1,234` → 1234 with both limits None, lone `0` → value 0 and state `"value"`, empty string → all None and state `"empty"`. Assert `extract_kpi_value_text` on the compact and labeled rows still returns the feature-013 current token, and is not redefined for the slash row. Use synthetic numbers only — no report titles or a hardcoded denominator (FR-001, FR-002, FR-008)

### Implementation for User Story 1

- [X] T006 [US1] Add a `GaugeScale` TypedDict (`state`, `value`, `minimum`, `maximum`) and `extract_gauge_scale(raw)` in `core/components/kpi.py`. Strip bidi marks, then apply the first match: (1) labeled bound pairs using the existing chrome (`ערך מינימלי`, `ערך מקסימלי`, `Minimum value`, `Maximum value`) set minimum or maximum and the longest remaining numeric token is `value`; (2) exactly three compact tokens → min, max, value in that order; (3) exactly one `number / number` and no other number → left is value, right is maximum, minimum is None; (4) one remaining number → value only; (5) no number → all None and state `"empty"`. Normalize each token with `normalize_kpi_text` and parse int-when-integral else float. State is `"value"` when `value` is not None, including 0. Do not change `extract_kpi_value_text` (per contracts/gauge-scale.md, research.md Decision 2) — depends on T005
- [X] T007 [US1] Add `KPI._read_raw(self, title, scope=None)` and `KPI.scale(self, title, scope=None)` in `core/components/kpi.py`. Resolve with the existing button-then-group path and `scope`. Raw group text is inner `img` `aria-label`, then `img` `title`, then group text; raw button text is the last `p` — do not run `extract_kpi_value_text` on that raw string. `scale` returns `extract_gauge_scale(raw)`. Leave mark-count combination for T011. `number` / `value` / `read_text` / `card` stay unchanged (per contracts/gauge-scale.md) — depends on T004, T006
- [X] T008 [US1] Run `python -m pytest tests/unit/test_gauge_scale.py tests/unit/test_kpi_normalize.py -v` and confirm both files pass (FR-002, FR-009) — depends on T007

**Checkpoint**: Scale parsing is independently testable. MVP complete. Blank visuals are not yet distinguished from a missing number by data marks.

---

## Phase 4: User Story 2 - True zero versus empty visual (Priority: P1)

**Goal**: A rendered `0` is state `"value"`. A visual with no numeric token and no data mark is
`"empty"`, not the number 0. A missing series slot stays `None`.

**Independent Test**: `python -m pytest tests/unit/test_visual_state.py -v`. The rows in
contracts/visual-reading.md pass. `classify_presence([0], 0)` is `"value"`. `classify_presence([None], 0)`
is `"empty"`.

### Tests for User Story 2

- [X] T009 [P] [US2] Add failing tests in `tests/unit/test_visual_state.py` for `classify_presence` in `core/components/visual.py`, using the table in `specs/015-advanced-visual-components/contracts/visual-reading.md`: `[0]`/`0` → `"value"`; `[None]`/`0` and `[]`/`0` → `"empty"`; `[None, None]`/`3` → `"value"`; `[4, None]`/`2` → `"value"` while the `None` cell is not rewritten to 0 (FR-003, FR-004)

### Implementation for User Story 2

- [X] T010 [US2] Implement `classify_presence(numbers, mark_count) -> Literal["value", "empty"]` in `core/components/visual.py`. Return `"value"` when any number is not None (including 0) or when `mark_count > 0`. Return `"empty"` only when every number is None and `mark_count == 0`. Never return numeric 0 for the empty case. English comments only (per contracts/visual-reading.md, research.md Decision 3) — depends on T009
- [X] T011 [US2] Update `KPI.scale` in `core/components/kpi.py` so that when `extract_gauge_scale` leaves `value is None`, it counts data marks inside the resolved card (plot glyphs such as `svg` `rect`/`path` that are data marks, not the title text) and assigns `state` from `classify_presence`. Marks with no readable number MUST yield `state="value"` and `value=None`. No marks MUST yield `state="empty"`. Do not coerce `None` to 0. Do not change `KPI.number` (per contracts/gauge-scale.md `KPI.scale`, data-model.md State transitions) — depends on T007, T010
- [X] T012 [US2] Run `python -m pytest tests/unit/test_visual_state.py tests/unit/test_gauge_scale.py -v` and confirm both pass (FR-003, FR-009) — depends on T011

**Checkpoint**: Rendered zero and a blank KPI visual are different results. Chart cells are not built yet.

---

## Phase 5: User Story 3 - Generic bar/column chart (Priority: P1)

**Goal**: `Chart` returns categories in visual order, a numeric descending check (ties pass), a
category count (not a bar count), and legend series with one cell per series. A missing cell is
`None`.

**Independent Test**: `python -m pytest tests/unit/test_chart_shape.py -v` with no browser. The
normative table in contracts/chart-component.md passes, including two series and an empty chart.

### Tests for User Story 3

- [X] T013 [P] [US3] Add failing tests in `tests/unit/test_chart_shape.py` for the pure helpers that back `Chart` (import them from `core/components/chart.py`). Cover `specs/015-advanced-visual-components/contracts/chart-component.md`: descending ties on the first series pass; a later larger value fails; one category whose cell is 0 passes and counts as 1; a `None` in the selected series fails descending and is not stored as 0; `category_count` equals the number of categories, not bars, when two series exist; two series keep legend order; zero categories and zero marks → count 0, descending false, state `"empty"` (FR-004, FR-005)

### Implementation for User Story 3

- [X] T014 [US3] Add frozen `ChartCategory` (`label`, `values`) and `ChartReading` (`title`, `categories`, `series`, `state`) plus pure helpers in `core/components/chart.py`: descending check on one series index (`previous >= current`, ties pass, any `None` or empty category list fails, a single numeric cell passes, out-of-range index fails), category count = `len(categories)`, and series alignment so each category has one cell per legend name with `None` for a missing mark. No domain strings. English comments only (per data-model.md ChartCategory / ChartReading, contracts/chart-component.md) — depends on T013
- [X] T015 [US3] Implement `Chart.__init__(page, frame, timeout_ms=None)`, locate-by-opaque-title, and `read` / `category_count` / `is_descending` in `core/components/chart.py`. Locate with `scope_host` and an escaped title substring inside a generic Power BI visual container (group and/or visual-container chrome — no report-specific id). Parse marks in this order: accessible name (`aria-label` or `title`) carrying category, optional series, and a number; else category tick text paired with numeric data labels in visual order; legend names are non-numeric legend texts excluding the visual title and category ticks. Set `state` with `classify_presence`. Do not implement tooltips, drilldown, or hover, and do not edit `pages/fleet_dashboard/main_dashboard_page.py` (per research.md Decision 4) — depends on T004, T010, T014
- [X] T016 [US3] Export `Chart` from `core/components/__init__.py` — depends on T015
- [X] T017 [US3] Run `python -m pytest tests/unit/test_chart_shape.py -v` and confirm it passes (FR-005, FR-009) — depends on T014

**Checkpoint**: Sort, Top-N count, and legend alignment are unit-tested. Displayed-title source order is still US4. `is_descending` takes `series_index: int`, never a series display name.

---

## Phase 6: User Story 4 - Dynamic visual title (Priority: P2)

**Goal**: Callers can read the full title currently shown on a visual. The lookup anchor stays an
opaque argument. Slicer-dependent phrases are not stored in `core/`.

**Independent Test**: `displayed_title_text` returns the first non-empty of heading, visual-title
node, and accessible name, with bidi marks stripped and the anchor left in the string. A title
longer than the anchor still matches. `rg` over `core/components/` finds no slicer-phrase literal.

### Implementation for User Story 4

- [X] T018 [US4] Add `displayed_title_text(container) -> str` in `core/components/visual.py`. Return the first non-empty of: the visual heading text, the visual-title node text, then the container accessible name (`aria-label`, then Playwright's accessible name). Strip bidi marks. Do not remove the lookup anchor. Return `""` when all sources are empty. Do not embed slicer phrases (per contracts/visual-reading.md, research.md Decision 5) — depends on T003
- [X] T019 [US4] Add `Chart.displayed_title(self, title, scope=None)` in `core/components/chart.py` and set `Chart.read(...).title` from `displayed_title_text` of the located container. Lookup stays an escaped substring anchor inside `scope_host`, so a longer accessible name that still contains the anchor matches and the return value is the full current title (per contracts/chart-component.md Locate, contracts/visual-reading.md) — depends on T015, T018
- [X] T020 [US4] Audit `core/components/kpi.py`, `core/components/visual.py`, and `core/components/chart.py`: no report names, metric titles, denominator literals, or slicer-dependent title phrases; inline comments and docstrings are English only (FR-007, FR-008, FR-010) — depends on T019

**Checkpoint**: Dynamic title text is returned to the caller and is not hardcoded.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Prove existing callers and the fleet smoke suite still pass.

- [X] T021 [P] Confirm this feature does not modify `pages/fleet_dashboard/main_dashboard_page.py` or `tests/helpers/db_parity_engine.py` (research.md Decision 7). `rg "kpi\.number\(" tests/helpers/db_parity_engine.py` still shows a one-argument call
- [X] T022 Run the quickstart unit commands from `specs/015-advanced-visual-components/quickstart.md`: `python -m pytest tests/unit/test_kpi_normalize.py tests/unit/test_gauge_scale.py tests/unit/test_visual_state.py tests/unit/test_chart_shape.py -v` — depends on T008, T012, T017
- [X] T023 Regression gate: run `python -m pytest tests/ui/fleet_dashboard/` and confirm 100% green (Constitution III, SC-005) — depends on T022
- [X] T024 [P] Check that `KPI.scale`, `Chart.read`, `Chart.category_count`, `Chart.is_descending`, and `Chart.displayed_title` signatures match the caller sketch in `specs/015-advanced-visual-components/quickstart.md` — depends on T019

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run first.
- **Foundational (Phase 2)**: Depends on Setup. T003 → T004 BLOCKS locate-path work in US1, US3, and US4.
- **User Story 1 (Phase 3)**: Depends on Foundational for `KPI.scale` locate (T007). The pure parser test (T005) and parser (T006) do not need the host. The MVP.
- **User Story 2 (Phase 4)**: T009–T010 do not need US1. T011 (wire `KPI.scale`) depends on T007 and T010.
- **User Story 3 (Phase 5)**: Pure helpers (T013–T014, T017) do not need other stories. `Chart.read` (T015) depends on Foundational and on T010.
- **User Story 4 (Phase 6)**: T018 can follow Foundational. T019 depends on `Chart.read` (T015).
- **Polish (Phase 7)**: Depends on the stories you include. T023 is the completion gate for the full feature.

### User Story Dependencies

- **US1 (P1)**: Gauge scale text. Independently testable via `tests/unit/test_gauge_scale.py`. No dependency on US2–US4 for the parser.
- **US2 (P1)**: Presence classifier. Independently testable via `tests/unit/test_visual_state.py`. Integrates into `KPI.scale` only at T011.
- **US3 (P1)**: Chart shape. Independently testable via `tests/unit/test_chart_shape.py`. DOM `read` needs `scope_host` and `classify_presence`. Does not need US4 for sort, count, or series.
- **US4 (P2)**: Displayed title. Needs the `Chart` class from US3 before `Chart.displayed_title` can delegate. The helper itself has no story dependency.

### Within Each User Story

- Tests fail before implementation (T005 before T006, T009 before T010, T013 before T014).
- Parser / pure helper before the Playwright method that calls it.
- Story checkpoint before treating the next story as required.

### Parallel Opportunities

- T001 and T002 (baseline + inventory).
- T005, T009, and T013 (three new test files) can be written together.
- After those tests exist: T006 (`kpi.py`), T010 (`visual.py`), and T014 (`chart.py`) touch different files.
- T021 and T024 can run together after the implementation tasks they name.

---

## Parallel Example: User Story 1

```bash
# Test files for US1, US2, and US3 are independent — write them together:
Task: "T005 Failing gauge-scale tests in tests/unit/test_gauge_scale.py"
Task: "T009 Failing presence tests in tests/unit/test_visual_state.py"
Task: "T013 Failing chart-shape tests in tests/unit/test_chart_shape.py"

# Then implement pure pieces in different modules:
Task: "T006 extract_gauge_scale in core/components/kpi.py"
Task: "T010 classify_presence in core/components/visual.py"
Task: "T014 Chart shape helpers in core/components/chart.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (baseline + parity inventory).
2. Phase 2: Foundational (`scope_host` delegate).
3. Phase 3: US1 (failing scale tests, then `extract_gauge_scale` and `KPI.scale`).
4. **STOP and VALIDATE**: `tests/unit/test_gauge_scale.py` and `tests/unit/test_kpi_normalize.py` are green.

### Incremental Delivery

1. Setup + Foundational → shared host, public `KPI.number` unchanged.
2. US1 → structured gauge scale (MVP).
3. US2 → rendered 0 versus empty, wired into `KPI.scale`.
4. US3 → bar/column sort, category count, legend series.
5. US4 → full displayed title.
6. Polish → quickstart unit commands, then fleet smoke at 100%.

### Parallel Team Strategy

1. Complete Setup + Foundational together.
2. Then split by file: one person on `kpi.py` (US1, then T011), one on `visual.py` (US2 classifier, then US4 title helper), one on `chart.py` (US3 pure helpers, then `read` after T010).
3. T019 waits until both `Chart.read` and `displayed_title_text` exist.

---

## Notes

- [P] tasks = different files, no dependencies.
- Do **not** change `extract_kpi_value_text`, `normalize_kpi_text`, or the one-argument `KPI.number` contract.
- Do **not** edit `pages/fleet_dashboard/main_dashboard_page.py` or `tests/helpers/db_parity_engine.py`.
- Do **not** add a `Gauge` class, a `Map` class, SQL, or a new package.
- Do **not** hardcode report titles, metric names, Top-N, or a denominator in `core/`.
- `0` is a real value or bound. `None` means absent. Empty is the state `"empty"`, not the number 0.
- All inline comments MUST be English only.
