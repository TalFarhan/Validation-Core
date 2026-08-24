# Feature Specification: Generic Slicer Component

**Feature Branch**: `002-generic-slicer`

**Created**: 2026-08-24

**Status**: Draft

**Audience**: Validation and BI leads own the user scenarios. The Layer 2 / Layer 3
split, configuration contract, and frozen test-facing filter APIs in Requirements
/ Architectural Constraints are normative for this platform refactor (Constitution
v1.0.0, amended for slicer chrome). They are not optional design notes.

**Input**: User description: "Design the Generic Slicer Component: extract Layer 2 filtering UI logic (dropdowns, checkboxes, search fields, clearing filters) into a domain-agnostic component; define a Layer 3 contract for domain filter data currently in filters.json and filter_matrix.json; MainDashboardPage instantiates the component without leaking domain terms into core/; Strangler Fig swap of old filter methods while existing UI tests stay 100% green."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same filter path after extraction (Priority: P1)

A Validation engineer runs the existing fleet filter and smoke checks. They still
select district, sub-unit, category, and source the same way; they still apply
combined filters, clear filters, inspect cascade options, and see the same
dropdown controls on load. No test file is rewritten to learn a new filter API.
KPI cards still settle after a selection the way they do today.

**Why this priority**: If filter verbs or locators change for callers, the
extraction has failed regardless of how clean the layering looks. This is the MVP.

**Independent Test**: Run the fleet smoke suite (`tests/ui/fleet_dashboard/`)
against the refactored page object, including filter and visibility checks.
All tests MUST pass. Callers still invoke `select_district`, `select_category`,
`select_source`, `select_sub_unit`, `apply_filters`, `clear_all_applied_filters`,
`reset_dashboard_filters`, `option(...)`, and still read `district_dropdown`,
`sub_unit_dropdown`, `source_dropdown`, `category_dropdown`, and
`clear_filters_btn` on the fleet page object.

**Acceptance Scenarios**:

1. **Given** the fleet report is open at baseline, **When** a test selects a
   district and a category using the existing page methods, **Then** the total
   count decreases relative to baseline and the clear-all control remains visible.
2. **Given** stacked district, category, and source selections, **When** each
   selection is applied in the current order, **Then** the total count narrows
   monotonically and stays positive.
3. **Given** a parent district is selected, **When** a test opens the sub-unit
   list, **Then** only child options for that district appear.
4. **Given** a district filter is applied, **When** a test clears all applied
   filters, **Then** the total count returns to the exact baseline.
5. **Given** a successful report open, **When** a test checks load visibility,
   **Then** the four fleet dropdowns and the clear-all control are still visible
   through the same page-object attributes as today.
6. **Given** the public filter method and locator names listed in Independent
   Test, **When** the extraction is complete, **Then** those contracts are
   unchanged and existing callers compile and run without edits.

---

### User Story 2 - Generic slicer knows how; domain knows what (Priority: P1)

The shared slicer component can open a dropdown, tick checkboxes, type into a
search field, close an open list, and click clear-all because those are Power BI
control behaviors. It does not know that this report's filters are district,
sub-unit, vehicle category, or vehicle source. The fleet page supplies which
controls exist, their accessible names, their interaction kind, and the labels
to pick. A second report could later pass a different set of slicers without
copying click-and-retry logic.

**Why this priority**: Zero domain leakage is a non-negotiable constitution
rule. Shipping a "generic" slicer that still names district or vehicles would
block every future report.

**Independent Test**: Inspect Layer 2 (`core/components/`) for fleet-specific
labels (vehicles, district, subunit, fleet KPI titles, fleet slicer display
names). Confirm the fleet page constructs the component with a report-specific
definition list and a settle hook. Confirm `core/` never loads `filters.json`
or `filter_matrix.json`.

**Acceptance Scenarios**:

1. **Given** the generic slicer has no fleet filter names of its own, **When**
   `MainDashboardPage` passes slicer definitions and resolved labels, **Then**
   selections, search, and clear-all run through that component and not through
   duplicated click logic on the fleet page.
2. **Given** Layer 2 source under `core/`, **When** a reviewer searches for
   vehicles, district, subunit, fleet KPI titles, or fleet chart titles, **Then**
   there are zero matches. Opaque ids and role names supplied at runtime by the
   domain page are not hardcoded in `core/`.
3. **Given** a future report page that supplies different slicer definitions,
   **When** it reuses the generic slicer, **Then** it does not inherit fleet
   district/category/source methods or Hebrew fleet labels.
4. **Given** a selection that must wait for visuals to refresh, **When** the
   generic slicer finishes a click, **Then** it only waits through a domain-
   supplied settle hook — never by naming a fleet KPI card.

---

### User Story 3 - Filter data stays a domain catalog with a stable contract (Priority: P2)

Engineers keep authoring example values in `data/filters.json` and scenario
rows in `data/filter_matrix.json`. Those files remain domain data. What changes
is the contract: alias keys resolve to display labels, then the fleet page
passes those labels plus slicer ids into the generic component. The component
never parses the JSON files. Combined scenarios still apply parent filters
before children (district before sub-unit).

**Why this priority**: This is the Layer 3 outcome. It can be verified after P1
still passes. Without a written contract, the next report will invent a second
JSON shape and leak mapping logic into `core/`.

**Independent Test**: Confirm `filters.json` and `filter_matrix.json` still
drive existing tests through the current helper/page entry points. Confirm a
documented schema describes slicer definitions (how a control behaves) versus
value catalogs (what labels exist) versus scenario matrices (which combinations
to run). Confirm `core/` does not import those data files.

**Acceptance Scenarios**:

1. **Given** `filters.json` aliases such as `dan` → a Hebrew district label,
   **When** a test asks to apply `district="dan"`, **Then** the display label is
   resolved before the generic slicer is invoked, and the slicer receives the
   label plus an opaque slicer id.
2. **Given** a combined matrix row that includes both district and sub-unit,
   **When** filters are applied, **Then** the parent slicer is applied before
   the child, matching today's cascade order.
3. **Given** `filter_matrix.json` single and combined rows, **When** existing
   matrix tests run, **Then** they still load those rows and still call
   `apply_filters` on the fleet page object with the same keyword names.
4. **Given** Layer 3 files, **When** a new report is added later, **Then** it
   can supply its own catalog and matrix that conform to the same contract
   without changing the generic slicer.

---

### User Story 4 - Incremental swap keeps the suite green (Priority: P2)

The old filter methods on the fleet page are not deleted on day one. They
become thin wrappers over the generic slicer, one behavior at a time (close
open lists, dropdown select, clear-all, search, then config-driven apply).
After every major step the fleet UI tests still pass. The Strangler Fig
sequence is the required delivery shape, not a big-bang rewrite.

**Why this priority**: The constitution treats existing tests as the contract.
A cleaner architecture that breaks smoke is rejected.

**Independent Test**: After each major swap step, run `pytest tests/ui/fleet_dashboard/`.
Do not edit test files. Existing `tests/e2e/` filter-matrix callers stay green
when that suite is run.

**Acceptance Scenarios**:

1. **Given** an empty generic slicer module exists, **When** the fleet page
   still owns all filter behavior, **Then** the smoke suite passes (introduction
   without behavior change).
2. **Given** dropdown select has moved into the generic slicer, **When** fleet
   methods `select_district` / `select_category` / `select_source` /
   `select_sub_unit` still exist as wrappers, **Then** the smoke suite passes.
3. **Given** clear-all and search have moved, **When** `reset_dashboard_filters`
   and `clear_all_applied_filters` still exist with the same names, **Then**
   the smoke suite passes.
4. **Given** all filter interaction lives in the generic slicer, **When** a
   reviewer inspects the fleet page, **Then** remaining filter methods are
   wrappers, locator aliases, and domain mapping — not a second copy of
   click-and-retry logic.

---

### Edge Cases

- Cascading hide: a child option that belongs to another parent MUST stay
  absent from the open list (today: Dan sub-unit under South).
- Selection that does not stick on first click: retry the open-and-click path
  the same way as today (dropdown text or a visual change counts as success).
- Clear-all when nothing is filtered: MUST NOT fail; baseline totals stay the
  same (today's optional wait).
- Open dropdown covering other controls: close open lists (Escape) before the
  next selection.
- Search field already empty: skip the clear path (today's short-circuit).
- Search field lives in a nested visual frame: the generic search interaction
  MUST support a host that is not the main report frame, with the fleet page
  declaring that host in config — not by hardcoding a vehicle-search name in
  `core/`.
- Checkbox slicers: the generic component MUST support multi-select checkbox
  lists even though the current fleet report uses dropdowns. Fleet wrappers
  keep calling single-select dropdown behavior.
- Option missing because cascade yielded zero rows: fail or skip with the same
  observable outcome as today (visible-option assertion), not a new error type
  invented in `core/`.
- Post-navigate baseline: `after_navigate` still resets filters through the
  existing fleet method name; that method may delegate to the generic slicer
  but Layer 0 MUST NOT learn fleet slicer names.
- Headless flake after select: settle waits remain optional unless the caller
  required a change, matching today's KPI optional-wait behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST introduce a generic slicer component at
  `core/components/slicer.py` that owns Power BI slicer *interaction*: open
  dropdown, select option, multi-select checkbox, type/submit/clear a search
  field, close an open list, and click a generic clear-all-slicers control.
- **FR-002**: `MainDashboardPage` MUST *compose* the slicer component (hold
  and call it). It MUST NOT inherit from the slicer. Layer 0 `ReportShell`
  remains the navigation host; this feature MUST NOT move SSO, catalog, or
  iframe loading into the slicer.
- **FR-003**: Public test-facing filter APIs on `MainDashboardPage` MUST keep
  their contracts. Tests MUST NOT be edited to adopt a new filter API. Frozen
  names:
  - `select_district(district_name)`
  - `select_sub_unit(sub_unit_name)`
  - `select_source(source_name)`
  - `select_category(category_name)`
  - `apply_filters(*, district=, sub_unit=, category=, source=)`
  - `clear_all_applied_filters()`
  - `reset_dashboard_filters()`
  - `option(option_name, listbox_name)`
  - locator aliases `district_dropdown`, `sub_unit_dropdown`,
    `source_dropdown`, `category_dropdown`, `clear_filters_btn`
  - search methods `search_vehicle`, `clear_vehicle_search` and locator
    `vehicle_search` (fleet names stay on the page; mechanics may delegate)
- **FR-004**: After extraction, `pytest tests/ui/fleet_dashboard/` MUST pass at
  100%. Existing `tests/e2e/` tests that apply filters through
  `MainDashboardPage` / helpers MUST remain green without test rewrites.
- **FR-005**: Layer 2 (`core/components/` and the rest of `core/`) MUST NOT
  contain vehicles, district, subunit, fleet KPI titles, fleet chart titles,
  or fleet slicer display names. Generic Power BI chrome phrases (clear all
  slicers / clear all filters, Search / חיפוש placeholders) MAY live in
  `core/` as locale-tolerant patterns.
- **FR-006**: The generic slicer MUST accept a domain-supplied definition list
  whose fields are opaque to `core/`: identity, accessible role name,
  interaction kind (`dropdown` | `checkbox` | `search`), cascade rank, and
  optional search-host hint. `core/` MUST NOT hardcode Unit / SubUnit /
  VehicleCategory / VehicleSource.
- **FR-007**: After a selection, the generic slicer MUST wait for the report
  to settle only through a domain-supplied hook (callback or protocol). It
  MUST NOT read fleet KPI cards by name. The fleet page's hook MAY wait on
  the same cards it waits on today.
- **FR-008**: Combined apply MUST honor cascade rank from the definition list
  so parents are selected before children. Today's fleet order (district /
  Unit before sub-unit / SubUnit) MUST be preserved via fleet config, not via
  those names inside `core/`.
- **FR-009**: `data/filters.json` and `data/filter_matrix.json` MUST remain
  domain data files. `core/` MUST NOT open, parse, or import them. Resolution
  of alias → display label stays in the domain page, domain helper, or a
  domain catalog module under `pages/fleet_dashboard/` (not under `core/`).
- **FR-010**: Layer 3 MUST define a written contract with three distinct
  artifacts:
  1. **Slicer definitions** — how each control on *this* report is operated
  2. **Value catalog** — alias keys to display labels (today: `filters.json`)
  3. **Scenario matrix** — which alias combinations to run (today:
     `filter_matrix.json`)
  The generic slicer consumes (1) plus already-resolved labels. Tests consume
  (2) and (3).
- **FR-011**: Implementation MUST follow Strangler Fig: introduce the
  component unused, then move close-open, dropdown select, clear-all, search,
  and config-driven apply in separate gated steps. After every **major** step
  the fleet smoke suite MUST stay 100% green. Do not delete fleet wrapper
  methods in the same change that first introduces the empty module.
- **FR-012**: Allure steps and CSV filter/UI log lines for select, apply,
  clear, and reset MUST remain equivalent to today. Failures MUST still
  produce screenshot and trace attachments.
- **FR-013**: KPI cards, tabs, tables, charts, tooltips, and drilldown MUST
  stay on `MainDashboardPage`. This feature extracts slicer interaction only.
- **FR-014**: `conftest.py` MUST NOT be edited. The `filter_data` / 
  `filter_matrix` fixtures MAY keep loading the existing JSON paths.
- **FR-015**: Constitution Principle VII MUST be updated in the same feature
  so Layer 2 slicer *chrome* is authorized shared behavior, while domain
  filter *names and values* remain outside `core/`. Layer 0 scope is
  unchanged.

### Key Entities

- **Generic Slicer (Layer 2)**: Report-agnostic operator of Power BI filter
  controls. Knows dropdown, checkbox, search, close, and clear-all. Does not
  know any one dashboard's business filters.
- **Slicer definition**: Per-control description supplied by the domain page
  (opaque id, accessible name, kind, cascade rank, optional search host).
- **Settle hook**: Domain callback invoked after a selection or clear so
  visuals can refresh without `core/` naming those visuals.
- **Value catalog (Layer 3)**: Alias → display label map for one report
  (today: `data/filters.json` with sections `districts`, `sub_units`,
  `categories`, `sources`).
- **Scenario matrix (Layer 3)**: Named combinations of catalog aliases for
  tests (today: `data/filter_matrix.json`).
- **Domain adapter**: Fleet page (and existing test helper) that resolves
  catalog aliases, holds locator aliases, and delegates interaction to the
  generic slicer.
- **ReportShell (Layer 0)**: Unchanged navigation host. Still calls
  `after_navigate`; fleet still implements that as filter reset.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic and MUST NOT
  gain fleet filter knowledge. Filter reset after navigate stays a domain
  `after_navigate` hook.
- **AC-002**: Layer 2 lives in `core/components/` (slicer module). Layer 3
  *data* stays under `data/` and `pages/<report>/` (or the existing test
  helper). `core/` may hold only generic types/schema comments, never fleet
  labels.
- **AC-003**: `MainDashboardPage` MUST compose the slicer and pass
  definitions + settle hook. Domain terms MUST NOT be imported into `core/`.
- **AC-004**: Public test-facing filter APIs listed in FR-003 MUST keep their
  contracts. Tests are not updated in this change.
- **AC-005**: Inheritance chain stays `BasePage` → `ReportShell` →
  `MainDashboardPage`. The slicer is a collaborator, not a base class.
- **AC-006**: Extract shared Power BI slicer chrome only. Do not genericize
  KPI maps, tabs, charts, tables, or drilldown in this feature.
- **AC-007**: Delivery MUST be Strangler Fig (FR-011). A single commit that
  both introduces the component and deletes the old methods is out of scope.

### Integration shape (normative)

```text
ReportShell (Layer 0)
  navigate(...) → after_navigate()          # unchanged

MainDashboardPage(ReportShell)              # Layer 1 / domain
  slicer = Slicer(frame, definitions, settle)
  select_district(label) → slicer.select(id, label)
  apply_filters(...)     → resolve catalog, then slicer.select in cascade order
  district_dropdown      → alias to slicer.control(id)
  after_navigate()       → reset_dashboard_filters() → slicer.clear_all + search clear

Slicer (Layer 2)                            # core/components/slicer.py
  select / select_many / search / clear_all / close_open
  uses definitions + settle; no fleet names

Value catalog + matrix (Layer 3)            # data/*.json, domain mapping
  alias → display label; tests keep current keys
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of existing fleet load, visibility, and filter checks pass
  after the extraction. Those check files are not edited. Binding suite:
  `tests/ui/fleet_dashboard/`.
- **SC-002**: 100% of existing warehouse-backed filter-matrix checks that apply
  filters through the shared dashboard entry pass without editing those files.
- **SC-003**: Testers still apply and clear filters through the same page-object
  verbs and locator names they use today, with no new required inputs.
- **SC-004**: A reviewer finds zero fleet business terms in `core/`
  (vehicles, district, subunit, fleet KPI or chart titles, fleet slicer
  display names).
- **SC-005**: A second report can reuse dropdown, checkbox, search, and
  clear-all behavior by supplying only its own slicer definitions, value
  catalog, and settle hook — without copying fleet filter methods.
- **SC-006**: After every major swap step (not only at the end), the binding
  fleet suite remains fully passing, so the old and new paths are never both
  broken at once.
- **SC-007**: Filter and reset actions still produce run-report evidence
  equivalent to today (step plus CSV filter/UI line).

## Assumptions

- Layer numbering: Layer 0 is `ReportShell` (already extracted); Layer 1 is
  the domain report page; Layer 2 is generic slicer interaction; Layer 3 is
  filter configuration data and mapping. No separate Layer 1 module is added
  in this feature.
- Composition (not inheritance) is the required integration style so
  `ReportShell` stays the only page-object base for navigation.
- The current fleet dropdown click, retry, Escape-to-close, clear-all, and
  vehicle-search behaviors are the correct behaviors to preserve; this
  feature relocates them, it does not redesign Power BI interaction.
- Fleet ready visual and KPI wait after select remain owned by the fleet
  page via the settle hook; only *ownership of the click sequence* moves.
- `filters.json` section names (`districts`, `sub_units`, `categories`,
  `sources`) and `apply_filters` keyword names stay as they are; a domain
  map connects them to opaque slicer ids. The JSON files are not renamed
  in this feature.
- Checkbox interaction is implemented generically even though fleet currently
  uses dropdowns only; no fleet test is rewritten to tick checkboxes.
- Vehicle search is in scope as a `search`-kind slicer. The fleet methods
  keep vehicle-specific names; `core/` talks about search fields, not vehicles.
- `tests/e2e/fleet/` does not exist; the binding UI suite is
  `tests/ui/fleet_dashboard/`, with `tests/e2e/` as the regression suite that
  must also stay green.
- No second production report is in scope; only the reuse *shape* must be
  possible.
- Constitution Principle VII is amended in this feature to authorize Layer 2
  slicer chrome; KPI/chart/table/drilldown extraction remains forbidden.
- Implementation sequencing and file-level steps live in `architecture.md`
  and `tasks.md`; this specification states the contract those documents
  must satisfy.
