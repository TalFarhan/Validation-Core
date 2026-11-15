# Implementation Plan: Complete Alerts DB Sanity Validations

**Branch**: `feature/reportportal-integration` (spec directory `040-alerts-db-sanity-completion`) | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/040-alerts-db-sanity-completion/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` pins this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The previous pin, `039-fleet-db-sanity`, stays as its own slice.

## Summary

Close the remaining Alerts sanity gaps against `data/alerts/db_sanity_am_kalavi.yaml`,
without touching the fleet module or `core/`. Screen 2 (Alerts Analysis population page)
gains three tests that read the district chart in per-day-average mode at the נפה, רשות,
and יישוב levels and compare them to `alerts_by_hierarchy.{nafa,rashut,yeshuv}.daily_avg`.
Those readers already exist and already back the `mahoz.daily_avg` test, so the tests are
new but the page object is not. Screen 1 (Status Picture) strengthens
`test_screen_1_top_settlements`: the four tie slots are now checked by exact settlement
name (unordered set equality against the golden tie names) instead of only counting four
rows. Both Alerts page objects raise their locator/navigation timeout above 60s so Power
BI rendering is less likely to raise `LoadTimeoutError`, while a never-rendering visual
still raises it. Expected values are read only from the YAML. All new or edited in-function
comments are English.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML` (already in `requirements.txt`),
Playwright through the existing Alerts fixtures
(`population_dashboard` in `tests/ui/alerts_analysis_dashboard/conftest.py`;
`status_picture_dashboard` in `tests/sanity/status_picture_dashboard/conftest.py`).
No new package.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml` (read only).
No warehouse query in this slice. `settings.DB_ENVIRONMENT` is not read.

**Testing**: `pytest -m sanity` on `tests/sanity/alerts_analysis_dashboard/` and
`tests/sanity/status_picture_dashboard/`. Portal auth is required because these are
UI tests. Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Test-coverage completion on two existing Alerts sanity modules, plus a
locator-timeout bump on two existing Alerts domain page objects. No new page, no new module,
no `core/` change, no data change.

**Performance Goals**: Each new Screen 2 test selects one hierarchy level, switches to average
mode, and reads the district chart once. The Screen 1 change reuses the existing scroll-and-read
ranking reader. The timeout bump raises the per-locator budget but keeps the fast-path early steps.

**Constraints**:

- **YAML-only expectations** (FR-001). Names and counts come from `db_sanity_am_kalavi.yaml`.
  No metric value is written into the test or the page object.
- **Reuse existing readers** (FR-002, FR-003). Screen 2 daily-average tests call
  `set_hierarchy_level(level)`, `set_district_aggregation("average")`, and
  `read_district_labels()` exactly as the `mahoz.daily_avg` test does, and reuse the
  module's `_assert_golden_keys` helper. They skip with the existing missing-reader message.
- **Tie by name** (FR-004, FR-005). The stable set is the golden entries above the tie value,
  computed from the file. The four UI tie-slot names must equal the golden tie names as an
  unordered set, each at the tie value.
- **Preserve the skip** (FR-006). An empty ranking map still skips with
  `Missing Page Object reader for top_10_settlements`.
- **Timeout bump on the domain pages** (FR-007). `self.timeout` (and
  `page.set_default_timeout` / `set_default_navigation_timeout`) rise above 60s on both Alerts
  pages. `LoadTimeoutError` still fires when the budget is exhausted.
- **No fleet, no core, no data edit** (FR-008). Fleet modules, `core/`, the root `conftest.py`,
  and every `data/` file are untouched.
- **English comments** inside new or edited functions (FR-009).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | EDIT | Add nafa/rashut/yeshuv `daily_avg` tests; add a helper for daily-average-by-level |
| `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` | EDIT | Change tie assertion from count-only to exact-name set equality |
| `pages/status_picture/status_picture_page.py` | EDIT | Raise `self.timeout` above 60s |
| `pages/alerts_analysis/population_page.py` | EDIT | Raise `self.timeout` above 60s |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Read-only golden source |
| `pages/alerts_analysis/population_page.py` readers | UNCHANGED (names/returns) | Existing readers reused |
| `core/` | UNCHANGED | No layer change |
| `tests/ui/`, `tests/e2e/`, `tests/sanity/fleet_dashboard/`, `db/clients/` | UNCHANGED | Fleet and SQL untouched |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. The Alerts pages keep composing it; only their timeout value changes.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Alerts labels and the golden file stay in the Alerts sanity modules and `data/alerts/`. `core/` does not load them. The root `conftest.py` is not touched.
- **Existing tests are the contract (III)**: PASS. No Layer 0, Layer 2, or navigation-surface change, so the fleet smoke gate is not triggered. Public Alerts reader names and return types are unchanged. Only the timeout constant on the Alerts pages changes.
- **Page object discipline (IV)**: PASS. Tests drive the browser through existing page readers. No new locator is added to a test body. The timeout bump is a value on the page object, not a new locator.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the sibling Alerts sanity slices. These tests compare the report to the checked-in golden file, not to live SQL. Justified in Complexity Tracking. No SQL is added.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay on the existing pytest run path. Assertion messages name the key and both values.
- **Extract shared behavior only (VII)**: PASS. No new abstraction. The timeout is a per-page value, not a generalized API; the readers already exist.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/040-alerts-db-sanity-completion/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── alerts-sanity-completion.md
```

### Source Code (repository root)

```text
tests/sanity/alerts_analysis_dashboard/test_data_validation.py   # EDIT
      ├── _assert_hierarchy_daily_avg(page, level, expected)      # NEW helper
      ├── test_hierarchy_nafa_daily_avg_matches_db                # NEW
      ├── test_hierarchy_rashut_daily_avg_matches_db              # NEW
      └── test_hierarchy_yeshuv_daily_avg_matches_db              # NEW

tests/sanity/status_picture_dashboard/test_status_picture_validation.py  # EDIT
      └── test_screen_1_top_settlements                           # tie by exact name
          (+ _golden_tie_names helper reading the YAML)

pages/alerts_analysis/population_page.py   # EDIT: self.timeout above 60s
pages/status_picture/status_picture_page.py # EDIT: self.timeout above 60s

data/alerts/db_sanity_am_kalavi.yaml        # UNCHANGED (read-only)
core/                                        # UNCHANGED
tests/ui/, tests/e2e/                        # UNCHANGED
tests/sanity/fleet_dashboard/, db/clients/   # UNCHANGED
```

**Structure Decision**: Extend the two existing Alerts sanity modules in place and bump the
timeout on the two Alerts domain page objects. Reuse the readers that already back the
`mahoz` sum and daily-average tests. Do not add a new module, a new reader, or a `core/`
API. Leave the fleet suite, the e2e suite, and the golden file as they are.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: tests compare the Alerts report to `data/alerts/db_sanity_am_kalavi.yaml` instead of a live warehouse query | The user named that file as the baseline, and the sibling Alerts sanity slices (034–037) already use it. The numbers are a snapshot. | Calling a live SQL client would fail whenever the warehouse moves past the snapshot. The e2e suite remains the live comparison. |
| Screen 1 reverses feature 036's count-only tie decision and checks exact tie names | The user explicitly asked to verify exact tie-slot names, which catches a wrong settlement in a tie slot. | Count-only (036) cannot detect a non-golden settlement entering a tie slot. The reversal is scoped to names read from the YAML, compared as an unordered set, so load-order shuffling of equal counts still passes. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The tests load only `data/alerts/db_sanity_am_kalavi.yaml` and do not read `settings.DB_ENVIRONMENT`.
- Screen 2 daily-average expectations and Screen 1 stable/tie names are iterated from the loaded document; no count or Hebrew name is copied into the assertion source.
- No Layer 0 or Layer 2 change, so the fleet smoke gate is not triggered; fleet modules are absent from the edit list.
- Public Alerts reader names and return types are unchanged; only `self.timeout` changes on the two Alerts pages.
- `LoadTimeoutError` behavior is preserved: a never-rendering visual still raises it once the (now larger) budget is exhausted.
- No SQL client and no `core/` parser is added.
