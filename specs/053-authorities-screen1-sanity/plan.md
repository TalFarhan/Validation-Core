# Implementation Plan: Authorities Status Screen 1 YAML Sanity

**Branch**: `feature/reportportal-integration` (spec directory `053-authorities-screen1-sanity`) | **Date**: 2026-11-18, amended 2026-11-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/053-authorities-screen1-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). Spec documents under `specs/052-hosen-screen34-sanity/` are not edited.

## Summary

Add a Screen 1 reader on the existing Authorities Status page and a golden-YAML sanity test for
הערכת מצב רשויות. The check covers `dashboard.screen_1_national_status` only.

`AuthoritiesStatusPage` already opens the report (`DASHBOARD_SEARCH_TERM = הערכת מצב רשויות`)
and waits for that phrase. This slice adds `select_screen_1_filter`, `wait_for_screen_1_idle`,
`read_screen_1_metrics`, and `section_anchor_visible`. The sanity test compares the reading to
`data/reshuyot/db_sanity.yaml`. The smoke test stays a one-line `verify_freshness()` call.
There is no SQL client and no new comparison engine. Hosen and `core/` stay unchanged.
`dashboard.screen_2_service_targets` is not opened or edited.

1. **Date and filters** — If `date` is present, the test selects it first. Then it walks
   `filters` in YAML key order. A string is one call. A list is one call per item, in order.
   `sub_district` is two names and stays two selections; the second call does not clear the
   first. District and sub-district go through Layer 2 `Slicer` (or the existing sandbox
   input when the control is not a combobox). Hebrew role names stay on the page. After
   every selection, and once more before the read, the test waits for idle.
   The open date dropdown is virtualized. `Slicer` has no scroll-and-search, and
   `collect_virtualized_rows` walks an entire grid. Neither is used to click the date.
   `_pick_open_date` in `pages/authorities_status/page.py` runs a bounded scroll loop,
   clicks `value` when that row is visible, and raises `AssertionError` with the visible
   rows when it is not. `core/` is not edited.
2. **Idle** — A visible spinner is expected hidden, then the existing ready locator is expected
   visible. No `sleep`, no `wait_for_timeout`, and no `networkidle`.
3. **Read** — `read_screen_1_metrics()` returns `date`, `filters`, `survey_status`,
   `authorities_status`, `facilities`, and `missing_daily_report` in the YAML shape. `title`
   stays in the YAML and is not returned.
4. **Anchors** — `section_anchor_visible` answers for `date`, `filters`, and the four metric
   blocks. `title` is false, so the walk skips it. A missing anchor skips that block. A visible
   anchor with an empty read fails.
5. **Compare** — Private helpers in `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`
   walk the golden block the way Hosen `_assert_tree` does. Every YAML key in a checked block
   matches. Extra UI rows are ignored. An integer matches grouped digits. A float matches the
   displayed number. A string matches display text after bidi marks are stripped. Authority
   rows match on `name`. `trend` is compared only when that YAML row has it.

## Survey count fix (2026-11-19)

`test_authorities_screen1_matches_golden` fails with:

`AssertionError: dashboard.screen_1_national_status.survey_status.filled: ui='' golden=18`

The golden value stays `18` in `data/reshuyot/db_sanity.yaml`. The UI string is empty because the reader returned `""` before the assertion ran. The walk is doing the job the spec requires: a visible survey anchor with an empty `filled` fails on that YAML path.

Implementation order, before any other Screen 1 change:

1. **Point `filled` at the digit text node** in `pages/authorities_status/page.py`.
   The survey anchor is already true (`רשויות הזינו את הסקר`), so the test does not skip the block. `_read_survey_status` then calls `_svg_text`, which reads `svg[aria-label^='GOALS_COUNT_MUNI']` with `text_content()` on the SVG element and turns a miss into `""`.
   Locate that SVG on the report frame by the aria prefix. The heading visual from `_section` can stop on a different `svg[aria-label]` and leave the count outside the section.
   Read a descendant `tspan` or `text` whose own text contains a digit. Use `text_content`. When the SVG has no such child, read the SVG's own `text_content` after the same digit wait.
   Send `out_of` through that same reader with `svg[aria-label*='Muni_Code']`. The walk stops on `filled`, so `out_of` has not been proven.
2. **Wait on that node, then read it.** On the locator chosen in step 1, call Playwright `expect` with `self.timeout` (`settings.DEFAULT_TIMEOUT`): `to_be_visible`, then `to_have_text` with a digit pattern. `expect` retries until the timeout. A painted `0` matches. An empty string does not.
   `wait_for_screen_1_idle()` stays the spinner plus the ready phrase. It does not learn this card.
   If the expect times out, return `""`. The existing assertion then still prints `ui='' golden=18`. The reader does not insert `18`.
   Status and facility callers of `_svg_text` keep their section scope. The report-frame lookup is only for `GOALS_COUNT_MUNI` and `Muni_Code`.
3. **Leave the assertion walk synchronous.** In `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py`, `assert_value` fails because `''` has no digit to parse against `18`. `_assert_tree` sees a non-empty `survey_status` dict and fails on `.filled`, which is the path in the error. Do not poll, sleep, or locate elements in those helpers. Do not coerce `''` to `0`. The test's current idle calls stay as they are.

No edit to `data/reshuyot/db_sanity.yaml`, `core/`, Hosen, the Authorities smoke suite, or Screen 2. After the reader change, run the single sanity test. A non-empty value other than `18` remains a golden mismatch.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `bind_dashboard`. Layer 2
`Slicer` for district and sub-district. `collect_virtualized_rows` only when a name list
is a virtualized grid. The date dropdown does not use that helper. No new package.

**Storage**: Existing golden file `data/reshuyot/db_sanity.yaml`, block
`dashboard.screen_1_national_status`. The file is not edited. No warehouse query and no
`db/clients/` module in this slice.

**Testing**: `pytest tests/sanity/authorities_status_dashboard -m sanity`. Authorities smoke
under `tests/ui/authorities_status_dashboard/` must still pass and must not be edited. Fleet
smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited. Hosen suites are not
a gate and are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Internal validation framework. Domain page `pages/authorities_status/page.py`.
Golden YAML `data/reshuyot/db_sanity.yaml`. Sanity test
`tests/sanity/authorities_status_dashboard/`.

**Performance Goals**: N/A. One catalog open, the Screen 1 selections, and one read per test.

**Constraints**:

- Do not edit `core/portal` or `core/components`. Do not add a scroll-and-search method to
  `Slicer`. Do not call `collect_virtualized_rows` from `_pick_open_date`. That helper stays
  available only for a virtualized authority-name list. The date click is a page-local loop.
- Do not edit `pages/hosen_status/`, `tests/sanity/hosen_status_dashboard/`,
  `tests/ui/hosen_status_dashboard/`, or `data/hosen/`.
- Do not edit `tests/ui/authorities_status_dashboard/`. The smoke fixture stays `dashboard`.
- Do not edit `data/reshuyot/db_sanity.yaml`. Do not open or compare
  `screen_2_service_targets`.
- Do not add `tests/helpers/` comparison code. The subset walk stays private in the Authorities
  test. Do not import the Hosen test module.
- Hebrew role names and block headings live on `pages/authorities_status/page.py`. They do not
  move into `core/` or into the test.
- Numbers, authority names, and filter values live only in the YAML. The page and the test do
  not embed them.
- No `sleep`, no `wait_for_timeout`, no `page.wait_for_load_state("networkidle")`.
  The survey digit wait is Playwright `expect` (`to_be_visible`, then `to_have_text` with a digit) on the page, bounded by `self.timeout`.
- A list filter value is applied one item at a time. `str(list)` is not a slicer label.
- `select_screen_1_filter` does not clear prior labels on that slicer.
- `navigate` and `verify_freshness` stay as they are. Root `conftest.py` does not import this page.
- Comments and new Python identifiers stay English. Hebrew is limited to locator constants and
  the existing search term.

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/authorities_status/page.py` | EDIT | Screen 1 select, idle, read, and anchors. `_pick_open_date` scrolls the open date list locally. Survey `filled` and `out_of` wait for the digit text node. Search term and ready locator stay. |
| `tests/sanity/authorities_status_dashboard/__init__.py` | NEW | Package marker |
| `tests/sanity/authorities_status_dashboard/conftest.py` | NEW | `authorities_status_dashboard` fixture via `bind_dashboard` |
| `tests/sanity/authorities_status_dashboard/test_screen1_sanity.py` | NEW | Apply date and filters, private tree walk |
| `docs/COVERAGE_CATALOG.md` | EDIT | Screen 1 YAML block ↔ reader ↔ test. Screen 2 noted as out of this slice. |
| `data/reshuyot/db_sanity.yaml` | UNCHANGED | Golden values stay, including Screen 2 |
| `tests/ui/authorities_status_dashboard/` | UNCHANGED | `verify_freshness()` smoke, fixture name `dashboard` |
| `core/` | NONE | No new `Slicer` method. Date scroll stays on the page. Name lists may still call `collect_virtualized_rows`. |
| `pages/hosen_status/` and Hosen tests | NONE | Mirror only; do not edit |
| hasbara / credit / alerts | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS with one tracked exception. `AuthoritiesStatusPage` already
  subclasses `ReportShell`. Login, catalog search, iframe wait, visual-load timeout, and
  last-refresh stay in Layer 0. The ready locator stays on the domain page. This slice does
  not add a Screen 2 tab switch. District and sub-district still compose `Slicer`. The open
  date list is virtualized, `Slicer.select` does not page it, and `core/` cannot gain a
  scroll-and-search method. The click therefore stays in `_pick_open_date`. See Complexity
  Tracking. It is not a copy of another report's slicer.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Hebrew titles, slicer role names, and
  block headings stay on `pages/authorities_status/page.py` and in `data/reshuyot/db_sanity.yaml`.
  `core/` is not edited. Root `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. The new methods are additive.
  Smoke `verify_freshness` stays, and that module is not edited. Fleet smoke is not the gate
  because Layer 0, Layer 2, and the fleet navigation surface are not edited. Hosen tests are not
  edited, so they stay the contract for תמ"צ חוסן.
- **Page object discipline (IV)**: PASS. The sanity test iterates the YAML and calls
  `select_screen_1_filter`. Combobox locators, `Slicer.select`, and the date scroll loop stay
  on `AuthoritiesStatusPage`. The test body does not locate a dropdown.
- **Warehouse as source of truth (V)**: PASS for this slice. The user scoped the work to the
  existing golden YAML, which this repository already uses under `tests/sanity/` (Hosen, Hasbara,
  Credit). No business SQL is added to Layer 0 or to a new client. A later warehouse slice is
  out of scope.
- **Observability (VI)**: PASS. The new test is a normal pytest sanity test. Existing CSV,
  screenshot, and trace hooks on the shared session stay in place. This slice does not remove them.
- **Extract shared behavior only (VII)**: PASS. The page composes `Slicer` for district and
  sub-district. A virtualized name list may compose `collect_virtualized_rows`. The date
  dropdown does not. Block headings, role names, and the `trend` word stay on the domain
  page. No new generic API is added under `core/`. See Complexity Tracking for the role
  table and for the date scroll loop.

**Post-design re-check**: PASS. Phase 1 did not add a `core/` edit, a Screen 2 method, a shared
compare helper, or a YAML edit. District and sub-district stay on `Slicer`. The date click
is the bounded loop in `_pick_open_date`. The walk stays private to the Authorities test.

**2026-11-19 re-check**: PASS. The survey fix stays on `AuthoritiesStatusPage`. The digit wait
uses `expect` and `self.timeout`. `assert_value` and `_assert_tree` stay pure compares, so the
test body still has no locator. `core/`, the golden YAML, Hosen, and the smoke suite stay
untouched. An empty `filled` still fails the YAML path. It is not rewritten to `18`.

## Project Structure

### Documentation (this feature)

```text
specs/053-authorities-screen1-sanity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── authorities-screen1-sanity.md
└── tasks.md              # /speckit-tasks — not created here
```

### Source Code (repository root)

```text
pages/authorities_status/page.py                  # AuthoritiesStatusPage + Screen 1 methods
data/reshuyot/db_sanity.yaml                      # dashboard.screen_1_national_status (unchanged)
tests/sanity/authorities_status_dashboard/        # fixture + private subset compare
tests/ui/authorities_status_dashboard/            # unchanged freshness smoke
docs/COVERAGE_CATALOG.md                          # Screen 1 rows
```

**Structure Decision**: Extend the existing domain page and add a sanity package beside the
other report sanity suites. The UI smoke package stays the freshness check. Golden data stays
in `data/reshuyot/`. Layer 0 and Layer 2 are consumed, not modified.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Page-local slicer role names and block headings, instead of a Layer 2 catalog | `Slicer` is report-agnostic. Authorities Hebrew names must not enter `core/`. The page table is the same pattern Hosen uses, without editing Hosen. | Putting the names in `Slicer` or in a shared helper would leak this report into Layer 2, which this slice is forbidden to edit. |
| Page-local scroll loop in `_pick_open_date`, instead of Layer 2 scroll-and-search | The date option sits in a virtualized dropdown. `Slicer.select` clicks an option that is already visible. `collect_virtualized_rows` reads every viewport of a data grid, including a horizontal sweep, and returns the rows. It does not click one label. `core/` cannot be edited, so neither helper can grow a one-click search. The loop lives only in `pages/authorities_status/page.py`, stops after 20 steps or a stuck `scrollTop`, and clicks one date. | Extending `Slicer` would edit `core/` and would put a one-report date walk into Layer 2. Calling `collect_virtualized_rows` from the dropdown would scrape the whole list to perform one click. |
| Golden YAML instead of a new SQL client | The user named `data/reshuyot/db_sanity.yaml` as the source, and the file already exists. Sanity suites in this repo already compare to YAML. | A new `db/clients/` module would invent a warehouse contract this slice does not have and would change numbers the user said not to fix. |

## Phase 0 and Phase 1 outputs

- [research.md](./research.md) — directory choice, apply order, `Slicer` for district and sub-district, the page-local date scroll loop, idle, reader shape, private walk, the files that stay closed, and the `survey_status.filled` empty-string failure.
- [data-model.md](./data-model.md) — YAML schema, reader dict, compare rules, anchors.
- [contracts/authorities-screen1-sanity.md](./contracts/authorities-screen1-sanity.md) — page methods, fixture, test order, catalog row.
- [quickstart.md](./quickstart.md) — files to touch and `pytest tests/sanity/authorities_status_dashboard -m sanity`.

## Implementation notes for `/speckit-tasks`

- Mirror the Hosen Screen 1 *shape*: fixture via `bind_dashboard` with an explicit fixture name,
  date then filters, idle after each selection and once before the read, private `_assert_tree`.
  Do not paste Hosen's smart-filter, date-iframe, KPI, or resilience-color helpers.
- `filters` iteration must detect a list. Hosen's `str(value)` path is the wrong mirror for
  `sub_district`.
- Replace the wait-only body of `_pick_open_date` with the bounded scroll loop in
  [research.md](./research.md) section 13 and in the page contract. Do not call
  `collect_virtualized_rows` from that method. Do not add a task that edits
  `core/components/slicer.py` or `core/components/virtual_grid.py`. Name-list readers may
  keep their existing `collect_virtualized_rows` calls.
- Authority object rows key on `name`, not Hosen's `title` / `authority`.
- Leave `title` in the YAML. `section_anchor_visible("title")` returns false.
- Do not edit the YAML when a live number disagrees with it. The test fails, and the file stays.
- Survey count fix, in this order: (1) in `_read_survey_status`, resolve `GOALS_COUNT_MUNI` and `Muni_Code` on the report frame and read the digit `tspan` or `text` with `text_content`; (2) `expect` that node visible and matching a digit before the read, and return `""` on timeout; (3) do not change `assert_value` or `_assert_tree`. See [research.md](./research.md) section 14.
