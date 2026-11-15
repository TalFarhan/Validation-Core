# Implementation Plan: Fix Skipped Tests and Load Errors for Alerts and Status Dashboards

**Branch**: `feature/reportportal-integration` (spec directory `041-fix-dashboard-data-rendering`) | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/041-fix-dashboard-data-rendering/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The previous pin, `040-alerts-db-sanity-completion`, stays as its own slice.

## Summary

Resolve the skipped Alerts/Status chart tests and `LoadTimeoutError` whose root cause is empty data
blocking dynamic charts from rendering. `navigate()` fails before any test runs because the
population page's report-ready locator is the data-dependent district chart (`התרעות לפי מחוז`), which
does not render under the default 7-day empty filter. The fix retargets that anchor to a
filter-independent, Screen-2-specific element (`TOTAL_CARD`, `סה"כ אוכלוסייה`) so navigation succeeds,
then the existing per-test golden `date_range` application makes the charts render. For Status Picture,
`_apply_golden_range()` is refactored to select the operation by name (`עם כלביא`, read from the golden
record) directly on the `FilterName` slicer via a new additive `select_operation()` method, instead of
passing `start`/`end` dates through the brittle `_OPERATION_RANGES` reverse map. Once data loads, the
existing `pytest.skip` guards stop firing (they remain only as a safety net for a genuinely absent
control). The locator timeout is unchanged (already `120_000`). Only the Screen 1 `operation` name is
added to the golden YAML. No fleet, `core/`, or root `conftest.py` change. In-function comments are English.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through the existing Alerts fixtures
(`population_dashboard` in `tests/ui/alerts_analysis_dashboard/conftest.py`;
`status_picture_dashboard` in `tests/sanity/status_picture_dashboard/conftest.py`, both via
`tests/helpers/dashboard_fixture.bind_dashboard`). No new package.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml` (one additive `operation` key; no
metric value changes). No warehouse query in this slice.

**Testing**: `pytest -m sanity` on `tests/sanity/alerts_analysis_dashboard/` and
`tests/sanity/status_picture_dashboard/`. Portal auth is required because these are UI tests. The
fleet smoke suite is not a gate: Layer 0, Layer 2, and the fleet page are untouched.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Defect fix on two existing Alerts page objects and two existing Alerts sanity test
modules, plus one additive golden-record key. No new page, no new module, no `core/` change.

**Performance Goals**: The population ready anchor becomes filter-independent, so a cold load reaches
`after_navigate()` without waiting out the full budget on an empty chart. Status Picture selects one
slicer option and waits for the gauge to settle — one interaction, no extra reads.

**Constraints**:

- **Ready anchor is filter-independent** (FR-002, FR-007). `AlertsPopulationPage._report_ready_locator()`
  returns `TOTAL_CARD`, not `DISTRICT_CHART`. `before_report_ready_check()` keeps using the district
  chart only for the Screen 1 → Screen 2 page switch. A never-rendering anchor still raises `LoadTimeoutError`.
- **Operation by name** (FR-003, FR-004, FR-006). Screen 1 setup reads `screen_1_status_picture.operation`
  and selects it directly on the `FilterName` slicer; an unknown option fails with a clear message.
- **Golden range before reads** (FR-001). Every Screen 2 chart test applies `date_range` before reading
  (already present; audited and kept). No date literal in a test body.
- **Skips resolve, guards stay** (FR-005). Data loading removes the skip paths; guards remain for a
  genuinely absent control.
- **No budget change**. `self.timeout` stays `120_000` on both pages.
- **No fleet / core / root conftest edit** (FR-008). Only `data/` edit is the Screen 1 `operation` key.
- **English comments** inside new or edited functions (FR-009).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | `_report_ready_locator()` → `TOTAL_CARD` |
| `pages/status_picture/status_picture_page.py` | EDIT | add `select_operation()`; golden path selects by name |
| `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` | EDIT | `_apply_golden_range()` selects operation by name |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | AUDIT/EDIT | confirm each chart test applies the golden range before reading |
| `data/alerts/db_sanity_am_kalavi.yaml` | EDIT (additive) | add Screen 1 `operation: "עם כלביא"` |
| `core/portal/`, `core/components/` | UNCHANGED | No layer change |
| `tests/ui/`, `tests/e2e/`, `tests/sanity/fleet_dashboard/`, `db/clients/` | UNCHANGED | Fleet and SQL untouched |
| root `conftest.py` | UNCHANGED | No fixture import change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The Alerts pages keep composing it; only
  which locator a domain page awaits changes, via the existing `_report_ready_locator()` override.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. The `TOTAL_CARD` phrase and the `עם כלביא`
  operation name stay on the domain pages / golden file. `core/` references neither. Report-ready state
  remains a domain-supplied locator, exactly as the constitution requires. The root `conftest.py` is
  untouched.
- **Existing tests are the contract (III)**: PASS. No Layer 0, Layer 2, or fleet navigation-surface
  change, so the fleet smoke gate is not triggered. Public Alerts reader names and return types are
  unchanged; `select_operation` is additive.
- **Page object discipline (IV)**: PASS. Tests drive the browser through page readers. The operation
  selection is a page method over the existing `Slicer`, not an ad-hoc locator in a test body. The ready
  anchor is a value on the page object.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the sibling Alerts
  sanity slices (034–040). These sanity tests compare the report to the checked-in golden file, not to
  live SQL. Justified in Complexity Tracking. No SQL is added.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay on the existing pytest run path.
  `navigate()` still logs its path and still raises `LoadTimeoutError` on a real failure.
- **Extract shared behavior only (VII)**: PASS. No new abstraction in `core/`. `select_operation()` is a
  thin domain wrapper over the existing `Slicer.select` plus the page's own gauge-settle wait.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/041-fix-dashboard-data-rendering/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── dashboard-data-rendering.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py        # EDIT: _report_ready_locator() -> TOTAL_CARD
      └── _report_ready_locator()                #   filter-independent Screen-2 anchor
      └── before_report_ready_check()            #   UNCHANGED (still uses DISTRICT_CHART for page switch)

pages/status_picture/status_picture_page.py     # EDIT
      ├── select_operation(name)                 #   NEW: select FilterName option by name + gauge settle
      └── _report_ready_locator()                #   UNCHANGED (UNDER_FIRE_CARD gauge, already compliant)

tests/sanity/status_picture_dashboard/test_status_picture_validation.py  # EDIT
      └── _apply_golden_range(page)              #   reads screen["operation"], calls select_operation

tests/sanity/alerts_analysis_dashboard/test_data_validation.py           # AUDIT/EDIT
      └── chart tests call _apply_golden_range   #   ensure range applied before reads

data/alerts/db_sanity_am_kalavi.yaml            # EDIT (additive): screen_1 operation: "עם כלביא"

core/                                            # UNCHANGED
tests/ui/, tests/e2e/                            # UNCHANGED
tests/sanity/fleet_dashboard/, db/clients/       # UNCHANGED
conftest.py (root)                               # UNCHANGED
```

**Structure Decision**: Fix the two existing Alerts domain page objects in place (retarget the
population ready anchor; add an additive operation-by-name selector to the status-picture page), refactor
the Status Picture test setup to select by name, audit the Alerts test setup, and add one golden-record
key. Do not add a new module, a new reader name, or a `core/` API. Leave the fleet suite, the e2e suite,
and every other `data/` value as they are.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: sanity tests compare the Alerts report to `data/alerts/db_sanity_am_kalavi.yaml` instead of a live warehouse query | The sibling Alerts sanity slices (034–040) already use this golden file as the baseline; the numbers are a recorded snapshot. | A live SQL client would fail whenever the warehouse moves past the snapshot. The e2e suite remains the live comparison. |
| One `data/` edit (add Screen 1 `operation`) despite the slice's "no data value change" posture | The user asked to select the operation by name, and the name must be data-driven, not hard-coded in the test (FR-003/FR-004). | Hard-coding `עם כלביא` in the test body would violate the YAML-as-source rule the sibling slices follow. The edit is purely additive — no metric value changes. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The tests load only `data/alerts/db_sanity_am_kalavi.yaml` and do not read `settings.DB_ENVIRONMENT`.
- The `עם כלביא` operation name and `TOTAL_CARD` anchor are read/owned by the domain pages and golden
  file; no Hebrew label is copied into `core/`.
- No Layer 0 or Layer 2 change, so the fleet smoke gate is not triggered; fleet modules are absent from
  the edit list.
- Public Alerts reader names and return types are unchanged; `select_operation` is additive; the ready
  anchor is a value change on an existing override.
- `LoadTimeoutError` behavior is preserved: a never-rendering ready anchor still raises it once the
  (unchanged) budget is exhausted.
- No SQL client and no `core/` parser is added.
