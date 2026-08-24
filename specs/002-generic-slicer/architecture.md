# Architecture: Generic Slicer Component

**Branch**: `002-generic-slicer` | **Date**: 2026-08-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-generic-slicer/spec.md`

This document is the architectural plan for Layer 2 (slicer interaction) and
Layer 3 (filter configuration). Formal implementation order is [tasks.md](./tasks.md).
The Strangler Fig sequence below is normative: tasks MUST follow it.

## Summary

Extract Power BI slicer *mechanics* from `MainDashboardPage` into a composed
Layer 2 component `core/components/slicer.py`. Domain filter *names, labels,
and which controls exist* stay on the fleet page plus `data/filters.json` /
`data/filter_matrix.json` (Layer 3). Public test-facing methods and locator
aliases on `MainDashboardPage` stay frozen. Delivery is Strangler Fig: wrap,
then move, never big-bang.

Technical approach: **composition + config + settle hook**. The component
knows how to operate dropdowns, checkboxes, search fields, and clear-all.
The fleet page knows that "district" is a dropdown whose accessible name is
`Unit`. After every major step, `pytest tests/ui/fleet_dashboard/` stays green.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, allure-pytest.
Existing helpers: `pages.base_page.BasePage`, `core.portal.page.ReportShell`,
`reports.test_run_report`.

**Storage**: Existing `data/filters.json` and `data/filter_matrix.json` stay
the Layer 3 files. No warehouse schema changes. `core/` MUST NOT read them.

**Testing**: `pytest` + Playwright Chromium. Binding gate:
`pytest tests/ui/fleet_dashboard/` (includes `test_dashboard_filters.py` and
slicer visibility in `test_dashboard_smoke.py`). Regression callers in
`tests/e2e/` (especially `test_filter_matrix.py`) must stay green. Do not
edit existing test modules or `conftest.py`.

**Target Platform**: Windows workstation + Chromium, organizational Agamim
portal + Microsoft SSO (same as today).

**Project Type**: Internal validation framework (pytest page objects).

**Performance Goals**: Preserve existing optional/required wait budgets
(`settings.DEFAULT_TIMEOUT`, `settings.KPI_OPTIONAL_WAIT_MS`). Do not add a
full timeout when clear-all is already a no-op.

**Constraints**: Constitution v1.0.0 with Principle VII amended for Layer 2
slicer chrome — zero domain leakage in `core/`; unchanged filter method
contracts; extract slicer interaction only; keep Allure steps and CSV logs.

**Scale/Scope**: One domain page (`pages/fleet_dashboard/main_dashboard_page.py`).
Move ~8 filter interaction methods into `Slicer`; keep ~8 wrappers + locator
aliases on the fleet page. KPI, tab, table, chart, tooltip, drilldown stay put.

## Constitution Check

*GATE: Must pass before implementation. Re-check after design.*

- **Layered portal**: PASS — Layer 0 `ReportShell` unchanged as navigation
  host. Layer 2 is `core/components/slicer.py`. Domain page still inherits
  `ReportShell`.
- **Zero domain leakage**: PASS — slicer ids, role names, and labels are
  arguments/config from the fleet page. `core/` forbids vehicles, district,
  subunit, KPI/chart titles. Generic chrome (Clear all slicers / Search) is
  allowed.
- **Test contract**: PASS — `pytest tests/ui/fleet_dashboard/` at 100% after
  each major Strangler step and at completion; no test-file edits.
- **Extract shared only**: PASS after Principle VII amendment (FR-015) —
  extract Power BI slicer chrome (dropdown/checkbox/search/clear-all). KPI,
  tabs, table, charts, tooltips, drilldown stay on the domain page.
- **Warehouse truth**: PASS — `db/` untouched; no SQL in Layer 2.
- **Observability**: PASS — fleet wrappers keep Allure titles; CSV
  `log_filter` / `log_ui` lines stay.

**Post-design re-check**: All gates PASS once Principle VII is amended in
the same feature. Complexity Tracking: one justified expansion (Layer 2).

## Layer Map

```text
Layer 0  core/portal/page.py          ReportShell — SSO, catalog, iframe, ready wait
Layer 1  pages/fleet_dashboard/       MainDashboardPage — domain names, wrappers, settle
Layer 2  core/components/slicer.py    Slicer — how to operate Power BI filter controls
Layer 3  data/*.json + domain map     catalogs, matrices, slicer definitions
```

Layer 1 is the existing domain page, not a new package. Layer 3 data stays in
`data/`. Layer 3 *types* (generic TypedDict / dataclass with no fleet values)
MAY live next to the slicer as `SlicerDefinition` so both layers share one
shape.

## Project Structure

```text
specs/002-generic-slicer/
├── spec.md
├── architecture.md          # This file
├── tasks.md
└── checklists/requirements.md

core/
├── portal/                  # Layer 0 — do not move filter logic here
│   └── page.py
└── components/              # Layer 2 (new)
    ├── __init__.py
    └── slicer.py            # Slicer + SlicerDefinition + SlicerKind

pages/
└── fleet_dashboard/
    └── main_dashboard_page.py   # composes Slicer; frozen public APIs

data/
├── filters.json             # Layer 3 value catalog (unchanged shape)
└── filter_matrix.json       # Layer 3 scenario matrix (unchanged shape)

tests/ui/fleet_dashboard/    # smoke gate — do not edit
tests/e2e/                   # regression callers — do not edit
conftest.py                  # unchanged fixtures
db/                          # out of scope
```

**Structure Decision**: Add only `core/components/`. Do not invent `src/`,
do not put slicers on `ReportShell`, do not load JSON from `core/`.

## Component Design (Layer 2)

### Responsibilities

`Slicer` knows **how**:

| Operation | Power BI behavior preserved from today |
|-----------|----------------------------------------|
| `close_open` | Escape twice so a leftover list does not steal the next click |
| `select` | Open combobox, click exact option, dismiss, retry once if not stuck |
| `select_many` | Checkbox list: open, tick each value, dismiss (new generic path; unused by fleet wrappers) |
| `search` | Focus field, fill, submit |
| `clear_search` | Clear button or empty+Enter; skip if already empty |
| `clear_all` | Click locale-tolerant "clear all slicers/filters" control |
| `control` / `option` | Locator factories from definition `role_name` |

`Slicer` does **not** know: district, vehicles, which KPI means "settled",
which JSON file holds labels, or apply-filters keyword names.

### Construction

```text
Slicer(
  page,                      # for keyboard Escape
  frame,                     # report iframe (page.frame_locator("main iframe"))
  definitions,               # Sequence[SlicerDefinition]
  settle,                    # Callable[..., None] supplied by domain
  clear_all_control,         # optional locator; default generic role/name pattern
)
```

The fleet page builds this once in `__init__` (or lazily) and keeps the
existing locator attributes as aliases:

```text
self.district_dropdown = self._slicer.control("district")
self.clear_filters_btn = self._slicer.clear_all_control
```

Ids such as `"district"` are **opaque strings** to Layer 2. They are not
fleet leakage inside `core/` as long as `core/` never interprets them.

### Settle hook

Today `_select_dropdown_option` clicks the total KPI card to dismiss the
list, then waits on `total` and `in_use` KPI updates.

Layer 2 MUST NOT name those cards. Contract:

```text
settle(kind: "after_select" | "after_clear" | "after_search", *, required: bool) -> None
```

Fleet implementation (stays on `MainDashboardPage`):

- `after_select`: dismiss via ready locator click (total KPI card) + optional
  wait on total and in_use (same as today).
- `after_clear`: optional wait on total.
- `after_search`: wait on table row-count change (existing
  `_wait_for_table_change`).

The slicer calls `settle` after the interaction; it does not poll KPIs.

### Generic chrome allowed in `core/`

- Clear-all button pattern: `נקה את כל|Clear all slicers|Clear all filters`
- Search placeholders: `חיפוש|Search`
- Visual sandbox iframe class `iframe.visual-sandbox` as a **host kind**
  selected by definition, not as "the vehicle search"

### Logging

`log_filter(role_name, option_name)` and `log_ui(...)` MAY be called from
Layer 2 using the definition's role name and the selected label (runtime
values, not hardcoded fleet terms). Fleet Allure step titles
(`Select district filter: {name}`) stay on the wrappers.

## Configuration Contract (Layer 3)

Three artifacts. Do not collapse them into one JSON blob in `core/`.

### 1. Slicer definitions (how)

Owned by the domain page as a tuple/list constant. Not loaded from
`filters.json`.

| Field | Meaning | Fleet example (lives on the page, not in core) |
|-------|---------|--------------------------------------------------|
| `id` | Opaque key used by the page | `"district"` |
| `role_name` | Power BI accessible name | `"Unit"` |
| `kind` | `dropdown` \| `checkbox` \| `search` | `dropdown` |
| `cascade_rank` | Lower applied first; `None` = unordered | district `0`, sub_unit `1` |
| `host` | `report` \| `visual_sandbox` | search uses `visual_sandbox` |

Fleet definition set (normative mapping, **page-owned**):

```text
district  → role Unit            kind dropdown  cascade 0
sub_unit  → role SubUnit         kind dropdown  cascade 1
category  → role VehicleCategory kind dropdown  cascade None (after parents)
source    → role VehicleSource   kind dropdown  cascade None
search    → host visual_sandbox  kind search    (vehicle search wrapper only)
```

`apply_filters` still applies district, then sub_unit, then category, then
source. Cascade rank encodes that order without putting those names in
`core/`: generic apply sorts provided ids by `cascade_rank` then stable
original order.

### 2. Value catalog (what)

File: `data/filters.json` — **shape unchanged**.

```json
{
  "districts": { "dan": "מחוז דן", "...": "..." },
  "categories": { "truck": "משאית" },
  "sources": { "organic": "יר\"ם", "transport_center": "מרכז הובלה" },
  "sub_units": { "south": "מחוז הדרום 6003", "dan": "מחוז דן 789" }
}
```

Domain map (already in `tests/helpers/dashboard_validation.py` as
`FILTER_SECTIONS`) stays outside `core/`:

```text
district → districts
sub_unit → sub_units
category → categories
source   → sources
```

Resolution happens before `Slicer.select`: alias `dan` becomes label
`מחוז דן`. The component only ever receives display labels.

### 3. Scenario matrix (which combinations)

File: `data/filter_matrix.json` — **shape unchanged**.

```json
{
  "single_filters": [ { "district": "dan" }, ... ],
  "combined_filters": [ { "district": "south", "sub_unit": "south" }, ... ]
}
```

Tests keep passing `**filter_combo` into the existing helper
`apply_filters(dashboard, filter_data, **filters)`, which still calls
`dashboard.apply_filters(district=..., sub_unit=..., category=..., source=...)`.

### What `core/` may type-check

```text
SlicerKind = "dropdown" | "checkbox" | "search"
SlicerHost = "report" | "visual_sandbox"

SlicerDefinition:
  id: str
  role_name: str
  kind: SlicerKind
  cascade_rank: int | None
  host: SlicerHost = "report"
```

No catalog TypedDict in `core/` that names `districts` / `vehicles`.

## Integration: MainDashboardPage

### Compose, do not inherit

```text
BasePage → ReportShell → MainDashboardPage
MainDashboardPage has-a Slicer
```

### Frozen public surface (tests depend on these)

Wrappers (Allure titles stay here):

- `select_district` / `select_sub_unit` / `select_source` / `select_category`
  → `self._slicer.select(id, label)`
- `apply_filters(...)` → skip Nones, sort by cascade_rank, `select` each
- `clear_all_applied_filters` / `reset_dashboard_filters`
  → `clear_search` (search id) + `clear_all`
- `option(option_name, listbox_name)` → `self._slicer.option_by_role(...)`
  (keep the two-arg signature tests use, including literal `"SubUnit"`)
- `search_vehicle` / `clear_vehicle_search` → search-kind operations

Locator aliases (smoke uses `.to_be_visible()`):

- `district_dropdown`, `sub_unit_dropdown`, `source_dropdown`,
  `category_dropdown`, `clear_filters_btn`, `vehicle_search`

### Domain leakage boundary

| Lives on fleet page | Lives in Slicer |
|---------------------|-----------------|
| `_SLICER_LISTBOXES` / definitions with Unit, SubUnit, … | Generic role lookup |
| `select_district` name and Allure text | `select(id, value)` |
| Settle waits on total / in_use KPIs | Call `settle` only |
| Catalog section names | Display labels as strings |
| `after_navigate` → `reset_dashboard_filters` | `clear_all` + `clear_search` |

### ReportShell

No change required except that `after_navigate` continues to call fleet
`reset_dashboard_filters`. Do not import `Slicer` from Layer 0.

## Implementation Approach: Strangler Fig

Each step MUST leave the project importable. After every **major** step
(marked GATE), run `pytest tests/ui/fleet_dashboard/` and fix before
continuing. Do not skip ahead to deleting `_select_dropdown_option` while
wrappers still need it.

### Step 0 — Baseline (GATE)

- Record current smoke result. Do not change behavior.
- Confirm callers: `select_*`, `apply_filters`, `option`, locator attributes,
  `reset_dashboard_filters` from `after_navigate`, helper in
  `tests/helpers/dashboard_validation.py`.

### Step 1 — Empty component + compose (GATE)

- Add `core/components/__init__.py` and `core/components/slicer.py`.
- `SlicerDefinition` + `Slicer` with methods raising `NotImplementedError`
  or empty stubs **not yet called**.
- Construct `self._slicer` on `MainDashboardPage` but keep all current
  method bodies.
- **Do not move methods.** Tests pass because behavior still sits on the
  page.

### Step 2 — Close-open + option locators (GATE)

- Move `_close_open_slicers` and `option(...)` bodies into `Slicer`.
- Fleet `option` and `_close_open_slicers` become one-line delegates.
- Tests that call `dashboard.option(..., "SubUnit")` still work.

### Step 3 — Dropdown select (GATE)

- Move `_select_dropdown_option` / `_dropdown_shows_selection` into
  `Slicer.select` for `kind=dropdown`.
- Inject settle hook; stop naming `total_vehicles_kpi` inside the moved
  body — fleet settle clicks that card.
- `select_district` and siblings become Allure wrappers around
  `self._slicer.select("district", name)`.
- Retry-once and CSV `log_filter` preserved.

### Step 4 — Clear-all (GATE)

- Move clear-all click + optional wait into `Slicer.clear_all`.
- `clear_all_applied_filters` and the filter-button half of
  `reset_dashboard_filters` delegate. Search clear still on the page until
  Step 5.

### Step 5 — Search (GATE)

- Move fill/submit/clear-search into `Slicer.search` / `clear_search`
  with `host=visual_sandbox`.
- `search_vehicle` / `clear_vehicle_search` become wrappers.
- `reset_dashboard_filters` delegates both search clear and clear-all.

### Step 6 — Config-driven apply (GATE)

- Fleet builds the definition list; `apply_filters` iterates resolved
  labels in cascade order via `Slicer`.
- Delete remaining duplicated click loops from the fleet page.
- Locator aliases still assigned from `slicer.control(id)`.

### Step 7 — Checkbox path (no fleet caller required)

- Implement `select_many` for `kind=checkbox`.
- No test rewrite. Covered by unit-level logic or left unused until a
  second report. MUST exist so Layer 2 matches the spec.

### Step 8 — Leakage audit

Search `core/` for: vehicles, district, subunit, fleet KPI titles, chart
titles, `total_vehicles`, `select_district`, `reset_dashboard_filters`,
`מחוז`, `רכבים`. Must be zero. Generic words (slicer, dropdown, combobox,
listbox, iframe, search, filter) are allowed. Runtime parameters are
allowed. Settings keys are allowed.

### Step 9 — Final gate

- `pytest tests/ui/fleet_dashboard/` MUST be 100% green.
- Do not edit test files. If e2e is run, `tests/e2e/` stays green.
- `conftest.py` unchanged.
- Constitution Principle VII updated and README layer table mentions
  Layer 2 / Layer 3.

## Constitution Amendment (FR-015)

Principle VII today forbids extracting filters until a second report needs
them. This feature **is** that extraction of shared slicer chrome.

Amend Principle VII to:

- Layer 0: login/SSO, catalog search, iframe wait, visual-load timeout.
- Layer 2: Power BI slicer interaction (dropdown, checkbox, search,
  clear-all) MAY live in `core/components/` when it is report-agnostic.
- Domain names, catalogs, matrices, KPI/tabs/charts/tables/drilldown stay
  on the domain page until a second report requires *those* behaviors.
- Do not invent unused generic APIs **beyond** the slicer kinds in this spec.

Also update README layer table and Architecture Constraints in the
constitution to mention `core/components/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Extract slicers before a second production report exists (Principle VII original text) | Requester's next architecture phase; Power BI chrome is identical across reports; waiting would keep duplicating click/retry in every page | Leave methods on `MainDashboardPage` — blocks the stated Layer 2/3 split and recopy cost |

## Risk Notes

- Tests click `dashboard.sub_unit_dropdown` and `dashboard.option(..., "SubUnit")`
  directly — aliases and the two-arg `option` signature are mandatory.
- Settle hook is easy to get wrong: if Layer 2 still clicks
  `total_vehicles_kpi`, leakage audit fails even if tests pass.
- Moving search before clear-all can break `reset_dashboard_filters` mid-
  sequence; keep reset as a fleet orchestrator until both delegates exist.
- `FILTER_SECTIONS` in the test helper is domain mapping — do not "clean it
  up" into `core/`.
- Checkbox API without a caller is allowed; do not change fleet dropdowns
  to checkboxes to "use" it.

## Out of Scope

- New reports, new `filters.json` shape, renaming catalog keys.
- Generic KPI, tab, table, chart, tooltip, or drilldown components.
- Editing `tests/`, `conftest.py`, or warehouse SQL.
- Changing `navigate` / `ReportShell` behavior.
- Loading Layer 3 JSON inside `core/`.
