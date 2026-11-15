# Implementation Plan: Fix Skipped Tests and Tooltips for Fleet DB Sanity

**Branch**: `feature/reportportal-integration` (spec directory `042-fleet-sanity-fixes`) | **Date**: 2026-11-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/042-fleet-sanity-fixes/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The sibling alerts/status slice `041-fix-dashboard-data-rendering`
stays as its own pin and is NOT touched by this slice.

## Summary

Resolve the two skipped fleet DB-sanity chart tests — `test_ui_credit_reasons_match_golden` and
`test_ui_category_actuals_match_golden` — whose root cause is in `tests/sanity/fleet_dashboard/`.
`assert_chart_matches` skips on two paths: (a) "exposed no golden labels" when no golden name folds to a
rendered label (the credit-reason pie), and (b) "exposed golden labels but no tooltip appeared" when
`hover_chart_segment` raises `LoadTimeoutError` because the Power BI tooltip never opened (the unit and
category charts). The fix hardens `hover_chart_segment` on the fleet domain page — a more robust hover
sequence plus a click-to-pin fallback — and makes its wait budgets a function of `self.timeout` instead
of the hard-coded 20-second deadline and small literals. For the credit-reason pie, the label mapping is
corrected in the fleet sanity reader/normalization so the golden reasons (`אחר`, `פקודת רידוד פיקודית`)
fold to the rendered labels, with an additive YAML alias allowed only if normalization cannot. The skip
guards remain as a safety net for a genuinely absent control. No alerts/status module, no `core/`, and
no root `conftest.py` change. The golden YAML metric values are unchanged. In-function comments are English.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through the existing fleet fixtures
(`dashboard` in `tests/ui/fleet_dashboard/conftest.py`, via `tests/helpers/dashboard_fixture.open_report`).
No new package.

**Storage**: Golden record `data/fleet/db_sanity_all.yaml` (metric values unchanged; at most one additive
label alias, only if required). No warehouse query in this slice.

**Testing**: `pytest -m sanity` on `tests/sanity/fleet_dashboard/test_db_sanity.py`, plus the fleet smoke
suite `tests/ui/fleet_dashboard/` as the Constitution III gate (the fleet domain page is edited). Portal
auth is required because these are UI tests. The alerts/status suites are not a gate and are not touched.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Defect fix on one existing fleet page object and the fleet sanity test package, plus an
optional additive golden-record alias. No new page, no new module, no `core/` change.

**Performance Goals**: Hover/tooltip budgets scale off `self.timeout` (`120_000`), so a slow render gets
proportionally more time to settle. A click-to-pin fallback opens a persistent tooltip when a plain hover
does not, reducing retries. A never-rendering tooltip still raises `LoadTimeoutError` once the budget ends.

**Constraints**:

- **Tooltips must open** (FR-001, FR-002). `hover_chart_segment` hardens its hover sequence and adds a
  click-to-pin fallback before raising. Signature and `str` return type unchanged.
- **Golden label mapping** (FR-003). The credit-reason reasons fold to rendered labels via the fleet
  sanity reader/normalization; the golden YAML values are not changed. An additive alias is the only
  permitted YAML edit, and only if normalization alone cannot fold a rendered label.
- **Dynamic waits** (FR-005). The 20s `overall_deadline` and per-attempt literals become functions of
  `self.timeout`. A never-rendering tooltip still raises `LoadTimeoutError`.
- **Skips resolve, guards stay** (FR-004). The tooltip/mapping fixes remove the skip paths; guards remain
  for a genuinely absent control.
- **No alerts / core / root conftest edit** (FR-006). Only the fleet page, the fleet sanity package, and
  (optionally) one additive YAML alias.
- **English comments** inside new or edited functions (FR-007).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/fleet_dashboard/main_dashboard_page.py` | EDIT | harden `hover_chart_segment` (robust hover + click-to-pin fallback); scale hover/tooltip budgets off `self.timeout` |
| `tests/sanity/fleet_dashboard/contract.py` | EDIT | correct credit-reason label mapping/normalization in `assert_chart_matches` / `normalize_label`; keep skip guards as safety net |
| `tests/sanity/fleet_dashboard/test_db_sanity.py` | AUDIT/EDIT | confirm the two named tests reach assertions once mapping/tooltips work; no literal values in test bodies |
| `data/fleet/db_sanity_all.yaml` | OPTIONAL EDIT (additive alias only) | add a label alias for a credit reason only if normalization cannot fold it; no metric value change |
| `core/portal/`, `core/components/` (incl. `chart.py`) | UNCHANGED | No layer change |
| `pages/alerts_analysis/`, `pages/status_picture/` | UNCHANGED | Alerts/status untouched |
| `tests/ui/`, `tests/e2e/`, `tests/sanity/alerts_analysis_dashboard/`, `tests/sanity/status_picture_dashboard/`, `db/clients/` | UNCHANGED | Alerts and SQL untouched |
| root `conftest.py` | UNCHANGED | No fixture import change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The fleet page keeps composing it; only the
  internal hover/tooltip strategy of an existing fleet chart reader changes.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Fleet chart titles, tooltip selectors, and credit
  reasons stay on the fleet domain page and in the fleet golden file. `core/` references none of them.
  Report tooltips and drilldowns live on the domain page, exactly as the constitution requires. The root
  `conftest.py` is untouched.
- **Existing tests are the contract (III)**: PASS with an explicit gate. The fleet domain page object IS
  edited, so the fleet smoke suite (`tests/ui/fleet_dashboard/`) MUST pass at 100% after the change; a
  task enforces this. Public fleet reader names and return types are unchanged; new helpers are private.
- **Page object discipline (IV)**: PASS. Tests drive the browser through fleet page readers. The hover,
  click-to-pin, and label collection are page methods, not ad-hoc locators in a test body. The sanity
  comparison logic stays in the fleet sanity package, which wraps page-object calls.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the sibling fleet sanity
  slice (039). These sanity tests compare the report to the checked-in golden file, not to live SQL.
  Justified in Complexity Tracking. No SQL is added; `db/clients/fleet.py` is unchanged.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay on the existing pytest run path.
  `hover_chart_segment` still raises `LoadTimeoutError` on a real failure.
- **Extract shared behavior only (VII)**: PASS. No new abstraction in `core/`. The hover/click-to-pin and
  label-fold fixes are fleet-specific tooltip behavior, which the constitution requires to stay on the
  fleet domain page — not in the generic Layer 2 `core/components/chart.py`.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/042-fleet-sanity-fixes/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── fleet-sanity-fixes.md
```

### Source Code (repository root)

```text
pages/fleet_dashboard/main_dashboard_page.py     # EDIT
      ├── hover_chart_segment(chart_key, label)   #   robust hover + click-to-pin fallback
      ├── _hover_until_match / _hover_chart_shapes #   dynamic budgets from self.timeout
      └── get_chart_segment_labels(chart_key)      #   keep reason names for pie (exclude only "n (x%)" chrome)

tests/sanity/fleet_dashboard/contract.py          # EDIT
      ├── assert_chart_matches(dashboard, key, exp) #   correct credit-reason mapping; keep skip guards
      └── normalize_label(text)                     #   fold so golden reasons match rendered labels

tests/sanity/fleet_dashboard/test_db_sanity.py     # AUDIT/EDIT
      ├── test_ui_credit_reasons_match_golden       #   reaches assertions (no "no golden labels" skip)
      └── test_ui_category_actuals_match_golden     #   reaches assertions (no "no tooltip" skip)

data/fleet/db_sanity_all.yaml                      # OPTIONAL EDIT (additive label alias only)

core/                                              # UNCHANGED (incl. core/components/chart.py)
pages/alerts_analysis/, pages/status_picture/      # UNCHANGED
tests/ui/, tests/e2e/                              # UNCHANGED (tests/ui/fleet_dashboard is the smoke gate)
tests/sanity/alerts_analysis_dashboard/, tests/sanity/status_picture_dashboard/, db/clients/  # UNCHANGED
conftest.py (root)                                 # UNCHANGED
```

**Structure Decision**: Fix the fleet domain page object in place (harden `hover_chart_segment` and make
its budgets dynamic), correct the credit-reason label mapping in the fleet sanity package, audit the two
named tests, and add at most one additive golden-record alias. Do not add a new module, a new reader
name, or a `core/` API. Leave the alerts/status suites, the e2e suite, `core/components/chart.py`, and
every golden metric value as they are.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: sanity tests compare the fleet report to `data/fleet/db_sanity_all.yaml` instead of a live warehouse query | The sibling fleet sanity slice (039) already uses this golden file as the baseline; the numbers are a recorded snapshot. | A live SQL client would fail whenever the warehouse moves past the snapshot. The e2e suite remains the live comparison. |
| An optional additive `data/` edit (one credit-reason label alias) despite the slice's "no data value change" posture | The credit-reason pie may render a reason name that cannot fold to the golden key by normalization alone; a data-driven alias is better than hard-coding the rendered form in test code. | Hard-coding the rendered label in the test body would violate the YAML-as-source rule the sibling slice follows. The edit is purely additive — no metric value changes — and is used only if normalization cannot bridge the gap. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The tests load only `data/fleet/db_sanity_all.yaml` and do not read `settings.DB_ENVIRONMENT`.
- Fleet chart titles, tooltip selectors, and credit-reason labels are owned by the fleet page / golden
  file; no fleet label is copied into `core/` (including `core/components/chart.py`).
- The fleet domain page object IS edited, so the fleet smoke gate (`tests/ui/fleet_dashboard/`) is
  triggered and enforced as a task; it must be 100% green.
- Public fleet reader names and return types are unchanged; the click-to-pin step is a private additive
  helper; the hover budget change is internal to existing methods.
- `LoadTimeoutError` behavior is preserved: a never-rendering tooltip still raises it once the dynamic
  budget is exhausted.
- No SQL client and no `core/` parser is added; the alerts/status modules and the root `conftest.py` are
  absent from the edit list.
