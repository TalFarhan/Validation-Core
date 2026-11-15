# Implementation Plan: Fix Hierarchy Level Locators

**Branch**: `feature/reportportal-integration` (spec directory `047-hierarchy-level-locators`) | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/047-hierarchy-level-locators/spec.md`

**Note**: This plan is filled by `/speckit-plan`. `tasks.md` is not created here.
`.specify/feature.json` points at this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). `specs/046-credit-ui-validation/` stays as it is.

## Summary

The nafa, rashut, and yeshuv sanity tests skip because `set_hierarchy_level` looks for a
visible `button`, `tab`, or `option` inside the district visual container. The controls on
the page are custom tabs above that chart, labeled `נפה`, `רשות`, and `יישוב`. The role
lookup returns nothing, the method returns false, and the test skips with "control not
visible on district chart".

1. **Click the tab by exact text** — In `pages/alerts_analysis/population_page.py`,
   `_hierarchy_control` returns the report-iframe locator
   `get_by_text(label, exact=True)` for the Hebrew name already stored in
   `_HIERARCHY_LEVEL_NAMES`. It does not filter by role and it does not require the
   district visual container. `set_hierarchy_level` clicks `.first` with a normal click
   so Playwright waits until that text can take the pointer. The method does not
   `count()` the matches and return false before the click, and it does not use
   `force=True`.
2. **Fail when the tab cannot be selected** — In
   `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`,
   `_assert_hierarchy_sum` and `_assert_hierarchy_daily_avg` drop the `pytest.skip` that
   uses "control not visible on district chart". A false return from
   `set_hierarchy_level` fails the test. A Playwright timeout on the click fails the
   test on its own.
3. **Keep the empty-chart skip** — After a successful selection, an empty
   `read_district_labels()` result still skips with the existing "returned no rows"
   reason. The golden YAML is not edited.

The bool return, the active-level field, and the wait for `התרעות לפי <level>` stay.
Comments added inside these functions are English. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, Playwright (`FrameLocator.get_by_text(..., exact=True)`,
`Locator.click()` actionability wait). No new package.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml` is read by the hierarchy
tests and is not edited.

**Testing**: `pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity -k hierarchy`
is the gate (needs portal auth). No unit test calls `set_hierarchy_level`. Fleet smoke is
not a gate.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.
The visual is inside the report iframe.

**Project Type**: Locator and skip-guard fix on the alerts population page and its YAML
sanity helpers. No new page, no new module, no `core/` change.

**Performance Goals**: The click uses the page's existing 120-second Playwright timeout.
There is no extra visibility poll before that wait.

**Constraints**:

- Tab text is the exact string from `_HIERARCHY_LEVEL_NAMES`: `נפה`, `רשות`, `יישוב` (FR-001, FR-010).
- The locator is the report iframe, not the outer browser page (FR-001).
- No role filter and no district-visual-container requirement (FR-002, FR-003).
- Normal `click()`, not `click(force=True)`, and no early false return from a probe (FR-004).
- Both hierarchy helpers drop the "control not visible on district chart" skip (FR-005, FR-006).
- The empty-row skip text stays (FR-007).
- `set_hierarchy_level(level: str) -> bool` stays (FR-008).
- In-function comments are English (FR-009).
- YAML, `core/`, `db/`, and other reports stay unchanged (FR-010).
- Hebrew tab labels stay on the alerts page (Constitution II, VII).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | Text locator and a waiting click in `_hierarchy_control` / `set_hierarchy_level` |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | EDIT | Drop the control-not-visible skip; fail on a false return |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Golden hierarchy blocks stay |
| `core/portal/`, `core/components/` | UNCHANGED | |
| fleet / status-picture / credit | UNCHANGED | |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The tab click stays on
  `AlertsPopulationPage`, which already inherits the alerts page and `ReportShell`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `נפה`, `רשות`, and `יישוב` stay on
  the alerts page. `core/` is not edited. Root `conftest.py` is untouched.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. The shared shell and
  the fleet page are not edited, so fleet smoke is not the gate. The public method keeps
  `set_hierarchy_level(level: str) -> bool`. The two sanity helpers are updated in the
  same change so a false return fails instead of skipping. The empty-chart skip stays.
- **Page object discipline (IV)**: PASS. The text locator lives on the page object. The
  sanity helpers do not gain their own locators.
- **Warehouse as source of truth (V)**: PASS. This slice does not open SQL and does not
  edit the golden YAML. The hierarchy tests keep comparing UI rows to
  `metrics.alerts_by_hierarchy`. That YAML comparison is the existing recorded source for
  this suite.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay. A missing tab is
  reported as a failure. An empty chart is still reported as a skip.
- **Extract shared behavior only (VII)**: PASS. The custom-tab locator stays on the alerts
  page. It is not lifted into `core/components/` or `core/portal/`.

**Result**: No unjustified violations. Phase 0 may proceed.

## Project Structure

### Documentation (this feature)

```text
specs/047-hierarchy-level-locators/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── hierarchy-tabs.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py
      ├── _HIERARCHY_LEVEL_NAMES                 # unchanged: nafa/rashut/yeshuv → נפה/רשות/יישוב
      ├── _hierarchy_control(label)              # report-frame get_by_text(label, exact=True)
      ├── set_hierarchy_level(level)             # normal click on .first; title wait stays
      └── _wait_for_level_selection(control)     # unchanged: no aria attribute means selected

tests/sanity/alerts_analysis_dashboard/test_data_validation.py
      ├── _assert_hierarchy_sum()                # no control-not-visible skip; assert the bool
      └── _assert_hierarchy_daily_avg()          # same; empty-row skip stays

data/alerts/db_sanity_am_kalavi.yaml             # UNCHANGED
core/                                            # UNCHANGED
```

**Structure Decision**: The locator stays on the alerts population page because the three
labels belong to that report. The skip change stays in the two helpers that call
`set_hierarchy_level`. Callers outside this sanity module do not exist.

## Complexity Tracking

> No constitution violations require justification. The table is empty on purpose.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII:

- `_hierarchy_control` returns `self._report_frame().get_by_text(label, exact=True)`.
  The outer `page.get_by_text` is not used, because these labels live in the report iframe.
- The click is `control.first.click()` with no role filter, no visual-container scope, and
  no `force=True`. Playwright's actionability wait is the wait.
- A missing label surfaces as that click's timeout. The helpers also assert a true return
  so a title that never changes fails the test. Neither path calls the old skip.
- The empty `read_district_labels()` skip, its reason string, `_active_hierarchy_level`,
  and the `התרעות לפי <name>` wait stay.
- `core/` is not edited. Fleet smoke is not required.
- In-function comments stay English.

**Result**: No unjustified violations.
