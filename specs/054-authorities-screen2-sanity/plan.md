# Implementation Plan: Authorities Status Screen 2 YAML Sanity

**Branch**: `feature/reportportal-integration` (spec directory `054-authorities-screen2-sanity`) | **Date**: 2026-11-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/054-authorities-screen2-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Spec documents under `specs/053-authorities-screen1-sanity/` are not edited.

## Summary

Add a Screen 2 reader on the existing Authorities Status page and a golden-YAML sanity test for
הערכת מצב רשויות Screen 2. The check covers `dashboard.screen_2_service_targets` only.

`AuthoritiesStatusPage` already opens the report (`DASHBOARD_SEARCH_TERM = הערכת מצב רשויות`)
and has Screen 1 select, idle, read, virtualized date-pick, and anchors. This slice adds
`open_screen_2(title)`, `select_screen_2_filter`, `wait_for_screen_2_idle`,
`read_screen_2_metrics`, and `screen_2_section_visible`. The sanity test compares the reading
to `data/reshuyot/db_sanity.yaml`. The smoke test stays a one-line `verify_freshness()` call.
Screen 1 public methods and `test_screen1_sanity.py` stay as they are. There is no SQL client
and no new comparison engine. Hosen and `core/` stay unchanged.
`dashboard.screen_1_national_status` is not loaded by the Screen 2 test.

1. **Navigate** — The test passes golden `title` into `open_screen_2`. The page uses that
   string only as a page-navigation target (full title or trailing segment after ` - `).
   The walk does not assert `title`. `screen_2_section_visible("title")` is false.
2. **Date and filters** — If `date` is present, the test selects it first through
   `select_screen_2_filter`. Then it walks `filters` in YAML key order. A string is one call.
   A list is one call per item, in order. The second call does not clear the first.
   Date reuses Screen 1 `_pick_open_date`. District and sub-district go through Layer 2
   `Slicer` (or the existing sandbox input). Hebrew role names stay on the page. After
   every selection, and once more before the read, the test waits for Screen 2 idle.
3. **Idle** — A visible spinner is expected hidden, then the Screen 2 ready locator is
   expected visible. No `sleep`, no `wait_for_timeout`, and no `networkidle`. Screen 1 idle
   stays the spinner plus `הערכת מצב רשויות`.
4. **Read** — `read_screen_2_metrics()` returns `date`, `filters`, `sector_profile`,
   `protection_data`, `service_targets`, and the as-loaded trend keys. `title` stays in the
   YAML and is not returned. PyYAML loads `grade_trends` as `null` and the trend rows as
   sibling `data`; the file is not edited; the reader returns that shape.
5. **Anchors** — `screen_2_section_visible` answers for `date`, `filters`, `sector_profile`,
   `protection_data`, `service_targets`, and `data`. `title` and `grade_trends` are false.
   A missing anchor skips that block. A visible anchor with an empty read fails.
6. **Compare** — Private helpers in `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`
   walk the golden block the way Screen 1 `_assert_tree` does. Every YAML key in a checked
   block matches. Extra UI rows are ignored. An integer matches grouped digits. A float
   matches the displayed number. A string matches display text after bidi marks are stripped.
   `service_targets` rows match on `name`. Trend rows match on `date`, then score keys.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `bind_dashboard`. Layer 2
`Slicer` for district and sub-district. Screen 1 `_pick_open_date` for the virtualized date
dropdown. `VisualTable.read_rows` for trend rows. `collect_virtualized_rows` when
`service_targets` is a virtualized grid. No new package.

**Storage**: Existing golden file `data/reshuyot/db_sanity.yaml`, block
`dashboard.screen_2_service_targets`. The file is not edited. No warehouse query and no
`db/clients/` module in this slice.

**Testing**: `pytest tests/sanity/authorities_status_dashboard/test_screen2_sanity.py -m sanity --reportportal`.
Screen 1 `pytest tests/sanity/authorities_status_dashboard/test_screen1_sanity.py -m sanity --reportportal`
must still pass and that file must not be edited. Authorities smoke under
`tests/ui/authorities_status_dashboard/` must still pass and must not be edited. Fleet smoke
is not a gate: Layer 0, Layer 2, and the fleet page are not edited. Hosen suites are not
a gate and are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal validation framework. Domain page `pages/authorities_status/page.py`.
Golden YAML `data/reshuyot/db_sanity.yaml`. Sanity test
`tests/sanity/authorities_status_dashboard/test_screen2_sanity.py`.

**Performance Goals**: N/A. One catalog open, one Screen 2 navigation, the Screen 2
selections, and one read per test.

**Constraints**:

- Do not edit `core/portal` or `core/components`. Do not add a scroll-and-search method to
  `Slicer`. Date click stays the existing `_pick_open_date` loop. `VisualTable` and
  `collect_virtualized_rows` are composed, not edited.
- Do not edit `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`,
  `tests/ui/hosen_status_dashboard/`, or `data/hosen/`. Do not copy or import Hosen code.
- Do not edit `tests/ui/authorities_status_dashboard/`. The smoke fixture stays `dashboard`.
- Do not edit `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`.
- Do not edit `data/reshuyot/db_sanity.yaml`. Do not load or compare
  `screen_1_national_status` from the Screen 2 test.
- Do not edit `specs/053-authorities-screen1-sanity/`.
- Do not add `tests/helpers/` comparison code. The subset walk stays private in the Screen 2
  test. Do not import the Screen 1 test module. Do not import the Hosen test module.
- Do not add a generic YAML loader or visual reader in `core/`.
- Hebrew role names and block headings live on `pages/authorities_status/page.py`. They do
  not move into `core/` or into the test.
- Numbers, service names, dates, and filter values live only in the YAML. The page and the
  test do not embed them. `title` is passed from YAML into `open_screen_2` and is not
  hardcoded on the page.
- No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`.
- A list filter value is applied one item at a time. `str(list)` is not a slicer label.
- `select_screen_2_filter` does not clear prior labels on that slicer.
- `navigate` and `verify_freshness` stay as they are. Screen 1 public methods stay as they
  are. Root `conftest.py` does not import this page.
- Comments and new Python identifiers stay English. Hebrew is limited to locator constants.
- Do not switch git branches.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/authorities_status/page.py` | EDIT | Additive Screen 2 open, select, idle, read, and anchors. Reuse `_pick_open_date`. Screen 1 public methods keep their contracts. |
| `tests/sanity/authorities_status_dashboard/test_screen2_sanity.py` | NEW | Load `screen_2_service_targets`, apply date then filters, private tree walk |
| `tests/sanity/authorities_status_dashboard/conftest.py` | UNCHANGED | Existing `authorities_status_dashboard` fixture |
| `docs/COVERAGE_CATALOG.md` | EDIT | Screen 2 YAML block ↔ reader ↔ test. Screen 1 rows stay. |
| `data/reshuyot/db_sanity.yaml` | UNCHANGED | Golden values stay, including the `grade_trends`/`data` indent |
| `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` | UNCHANGED | Screen 1 walk stays the Screen 1 contract |
| `tests/ui/authorities_status_dashboard/` | UNCHANGED | `verify_freshness()` smoke, fixture name `dashboard` |
| `core/` | NONE | Compose `Slicer`, `VisualTable`, `collect_virtualized_rows` |
| `pages/hosen_status/` and Hosen tests | NONE | Do not copy or import |
| `specs/053-authorities-screen1-sanity/` | NONE | Closed |
| hasbara / credit / alerts | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `AuthoritiesStatusPage` already subclasses `ReportShell`.
  Login, catalog search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0.
  Screen 1 ready locator stays on the domain page. Screen 2 ready locator is a domain
  locator derived from the navigation title. District and sub-district compose `Slicer`.
  Date click stays `_pick_open_date`. Trends compose `VisualTable`. Name lists compose
  `collect_virtualized_rows`. `core/` is not edited.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Hebrew titles, slicer role names, and
  block headings stay on `pages/authorities_status/page.py` and in `data/reshuyot/db_sanity.yaml`.
  `core/` is not edited. Root `conftest.py` does not import the page. The page does not load
  the YAML.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Screen 2 methods are
  additive. Screen 1 public methods keep their contracts. `test_screen1_sanity.py` is not
  edited. Smoke `verify_freshness` stays, and that module is not edited. Fleet smoke is not
  the gate because Layer 0, Layer 2, and the fleet navigation surface are not edited. Hosen
  tests are not edited.
- **Page object discipline (IV)**: PASS. The sanity test iterates the YAML and calls
  `open_screen_2` and `select_screen_2_filter`. Combobox locators, `Slicer.select`,
  `_pick_open_date`, `VisualTable.read_rows`, and `collect_virtualized_rows` stay on
  `AuthoritiesStatusPage`. The test body does not locate a dropdown or a grid.
- **Warehouse as source of truth (V)**: PASS for this slice. The user scoped the work to the
  existing golden YAML, which this repository already uses under `tests/sanity/`. No business
  SQL is added to Layer 0 or to a new client. A later warehouse slice is out of scope.
- **Observability (VI)**: PASS. The new test is a normal pytest sanity test. Existing CSV,
  screenshot, and trace hooks on the shared session stay in place. `--reportportal` is the
  existing run switch. This slice does not remove them.
- **Extract shared behavior only (VII)**: PASS. The page composes existing Layer 2 helpers.
  Block headings, role names, and Screen 2 navigation stay on the domain page. Assertion
  helpers stay private in the Screen 2 test. No new generic API is added under `core/` or
  `tests/helpers/`. See Complexity Tracking for the as-loaded `grade_trends`/`data` shape
  and for page-local quote variants on the navigation title.

**Post-design re-check**: PASS. Phase 1 did not add a `core/` edit, a Screen 1 test edit, a
shared compare helper, a YAML edit, or a Hosen import. Screen 2 methods are additive.
District and sub-district stay on `Slicer`. Date click stays `_pick_open_date`. Trends stay
on `VisualTable`. The walk stays private to the Screen 2 test.

## Project Structure

### Documentation (this feature)

```text
specs/054-authorities-screen2-sanity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── authorities-screen2-sanity.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pages/authorities_status/page.py                  # AuthoritiesStatusPage + additive Screen 2 methods
data/reshuyot/db_sanity.yaml                      # dashboard.screen_2_service_targets (unchanged)
tests/sanity/authorities_status_dashboard/        # existing fixture + new Screen 2 test
tests/ui/authorities_status_dashboard/            # unchanged freshness smoke
docs/COVERAGE_CATALOG.md                          # Screen 2 rows added beside Screen 1
```

**Structure Decision**: Extend the existing domain page. Add one sanity module beside the
existing Screen 1 test. Reuse the existing `authorities_status_dashboard` fixture. Golden
data stays in `data/reshuyot/`. Layer 0 and Layer 2 are consumed, not modified.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Page-local slicer role names and block headings, instead of a Layer 2 catalog | `Slicer` and `VisualTable` are report-agnostic. Authorities Hebrew names must not enter `core/`. | Putting the names in Layer 2 would leak this report into `core/`, which this slice is forbidden to edit. |
| Reuse of `_pick_open_date` instead of Layer 2 scroll-and-search | The date option sits in a virtualized dropdown. `Slicer.select` clicks an option that is already visible. `core/` cannot gain a scroll-and-search method. Screen 1 already solved this on the page. | Extending `Slicer` would edit `core/`. Rewriting the loop for Screen 2 would duplicate a working page-local walk. |
| As-loaded `grade_trends: null` plus sibling `data` list, instead of nesting rows under `grade_trends` | PyYAML loads the checked-in indent that way. The user forbade editing the YAML. The reader must return the loaded shape so the walk can see every golden key. | Fixing the indent would edit `data/reshuyot/db_sanity.yaml`. Nesting rows under `grade_trends` in the reader would make golden key `data` missing. |
| Private Screen 2 assertion helpers, instead of importing Screen 1 or Hosen | Screen 1 helpers key object rows on `name`/`title` only. Trend rows key on `date`. Importing Screen 1 would edit coupling the user said not to touch. Importing Hosen is forbidden. | A new engine under `tests/helpers/` is forbidden. Sharing would also pull Screen 1 into a Screen 2 identity rule. |
| Page-local quote variants for the navigation title | The golden title contains `תמ"צ`. Power BI may paint ASCII quotes or Hebrew gershayim. That is a locator concern on the page, not a golden value. | Copying Hosen `_quote_variants` would import or paste Hosen code. Hardcoding one spelling would miss the live control. |
| Golden YAML instead of a new SQL client | The user named `data/reshuyot/db_sanity.yaml` as the source, and the file already exists. | A new `db/clients/` module would invent a warehouse contract this slice does not have. |

## Phase 0 and Phase 1 outputs

- [research.md](./research.md) — directory choice, navigation, apply order, date-pick reuse, idle, as-loaded trend keys, reader shape, private walk, files that stay closed.
- [data-model.md](./data-model.md) — YAML schema as loaded, reader dict, compare rules, anchors.
- [contracts/authorities-screen2-sanity.md](./contracts/authorities-screen2-sanity.md) — page methods, fixture, test order, catalog row.
- [quickstart.md](./quickstart.md) — files to touch and the two pytest commands.

## Implementation notes for `/speckit-tasks`

- Keep Screen 1 public methods unchanged. Internal helpers may take an optional settle
  callable that defaults to Screen 1 idle so `_pick_open_date` is not copied.
- Do not route Screen 2 selections through `select_screen_1_filter`.
- `open_screen_2(title)` receives the YAML title. Do not hardcode that string on the page
  or in the test.
- `filters` iteration must detect a list. Never pass `str(list)`.
- `read_screen_2_metrics()` returns as-loaded keys: `grade_trends` is empty/`None`; trend
  rows are `data`. Do not rewrite the YAML.
- Duplicate Screen 1 `_assert_tree` / `_assert_rows` / `assert_value` into the Screen 2
  test. Extend row identity: `name` if present, else `date` if present, else `title`.
  Nested `scores` maps use the existing mapping walk. Do not import Screen 1 or Hosen.
- `service_targets` uses `collect_virtualized_rows` when the list is a grid. Trend rows
  use `VisualTable.read_rows` on the trends visual host. Map header→cell dicts on the page.
- Leave `title` in the YAML. `screen_2_section_visible("title")` returns false.
- Do not edit the YAML when a live number disagrees with it. The test fails, and the file stays.
- Done when both `test_screen2_sanity.py` and `test_screen1_sanity.py` pass with
  `-m sanity --reportportal`.
