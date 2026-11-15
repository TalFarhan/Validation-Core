# Implementation Plan: Fix Skipped Hierarchy Tests and Navigation Errors for Alerts Analysis

**Branch**: `feature/reportportal-integration` (spec directory `043-alerts-analysis-fixes`) | **Date**: 2026-11-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/043-alerts-analysis-fixes/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The sibling fleet slice `042-fleet-sanity-fixes` stays as its own
pin and is NOT touched by this slice.

## Summary

Resolve the `ERROR` (LoadTimeout) and `SKIPPED` results in the Alerts Analysis Screen 2 UI tests. Three
root causes live in `pages/alerts_analysis/population_page.py`:

1. **Bilingual accessibility names** — the page-rail switch (`before_report_ready_check`) and the date
   fields (`set_between_dates` → `_fill_input`) resolve only by Hebrew names (`ניווט בין עמודים`,
   `תאריך התחלה`, `תאריך סיום`). When Power BI renders them in English the locator never resolves and
   the report-ready wait raises `LoadTimeoutError`. Fix: wrap each in a Playwright `.or_()` over the
   Hebrew and English name (`Page navigation`, `Start date`, `End date`).
2. **Hardcoded dynamic title** — `DISTRICT_CHART = "התרעות לפי מחוז"` is the anchor for every district
   reader, and `set_hierarchy_level` still waits for that base title after a drill-down. Power BI
   retitles the visual (`התרעות לפי נפה` / `רשות` / `יישוב`), so the post-click check returns `False`
   and the hierarchy tests skip with "control not visible". Fix: remove the constant, add
   `district_chart_title()` (`"התרעות לפי " + level_name`) backed by an active-level field that
   `set_hierarchy_level` records, and wait for the *new* title.
3. **Unhandled `listbox` DOM** — the district and hour bar visuals render as a Power BI `listbox`, not
   the grid rows or SVG `aria-label` marks that `read_district_labels` / `read_hour_buckets` (and
   `read_hour_daily_avg`) expect, so they return `{}` and the tests skip. Fix: add a listbox-aware
   read path (pair category `listbox` options with the `התרעות` / average series options) with the
   Right-click → "Show as a table" fallback already used by the dates chart as the primary strategy.
   Parameterize the dates-table helpers so they can leave *any* visual's table, not only `DATES_CHART`.

The `pytest.skip` guards stay as a safety net for a genuinely absent control. The golden YAML values are
unchanged. The three test references to the removed `DISTRICT_CHART` constant are updated in the same
change. No fleet or status-picture module, no `core/`, and no golden metric value changes. In-function
comments are English.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through the existing alerts fixtures
(`population_dashboard` in `tests/ui/alerts_analysis_dashboard/conftest.py`). No new package.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml` (metric values unchanged). No warehouse
query in this slice.

**Testing**: `pytest -m sanity` on `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` (the
`test_hierarchy_*` and `test_alerts_by_hour_*` families), plus the alerts UI smoke suite
`tests/ui/alerts_analysis_dashboard/` as the contract gate (the alerts domain page object is edited) and
the unit test `tests/unit/test_population_page.py`. Portal auth is required for the UI/sanity tests.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Defect fix on one existing alerts page object plus three test references to a removed
class constant. No new page, no new module, no `core/` change.

**Performance Goals**: Locator resolution no longer depends on a single language, and the drilled-down
chart is found by its live title, so page-switch, date entry, and district/hour reads settle within the
existing `self.timeout` budget (`120_000`) instead of timing out.

**Constraints**:

- **Bilingual locators** (FR-001, FR-002). Page-rail switch and both date fields use a Playwright `.or_()`
  over the Hebrew and English name. The Hebrew side keeps working.
- **Dynamic district title** (FR-003, FR-004). The `DISTRICT_CHART` constant is removed; a
  `district_chart_title()` accessor evaluates `"התרעות לפי " + level_name` from the active level recorded
  by `set_hierarchy_level`. Every district reader anchors on the accessor. After a successful drill-down
  the method waits for the *new* title, not the base `מחוז` title.
- **Listbox extraction** (FR-005, FR-006, FR-007). `read_district_labels`, `read_hour_buckets`, and
  `read_hour_daily_avg` gain a listbox-aware path with the Show-as-a-table fallback. Dates-table helpers
  are parameterized by visual title so leaving the table does not wait for `DATES_CHART`.
- **Skips resolve, guards stay** (FR-007). The fixes remove the empty-read *and* false-negative
  `set_hierarchy_level` skip paths; the `pytest.skip` guards remain for a genuinely absent control.
- **No fleet / status / core edit** (FR-008). Only the alerts page object and the alerts/unit test
  references to the removed constant.
- **Golden values unchanged** (FR-009). `data/alerts/db_sanity_am_kalavi.yaml` is read-only here.
- **English comments** inside new or edited functions (FR-011).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/alerts_analysis/population_page.py` | EDIT | bilingual `.or_()` for page-rail + date fields; remove `DISTRICT_CHART`, add `district_chart_title()` + active-level state; wait for the drilled title in `set_hierarchy_level`; listbox/show-as-table read paths in `read_district_labels`, `read_hour_buckets`, and `read_hour_daily_avg`; parameterize `_click_show_as_table` / `_leave_dates_table` / `_alert_column_table` by visual title; English comments |
| `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` | EDIT | replace `DISTRICT_CHART` references with the dynamic title accessor (smoke gate) |
| `tests/ui/alerts_analysis_dashboard/population_snapshot.py` | EDIT | replace `page.DISTRICT_CHART` with the accessor |
| `tests/unit/test_population_page.py` | EDIT | assert the static title builder's base-level title instead of the removed constant |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | AUDIT | confirm `test_hierarchy_*` / `test_alerts_by_hour_*` reach assertions once reads work; no literal golden values in test bodies |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | golden values are read-only |
| `core/portal/`, `core/components/` | UNCHANGED | No layer change |
| `pages/fleet_dashboard/`, `pages/status_picture/` | UNCHANGED | Fleet/status untouched |
| `tests/**/fleet_dashboard/`, `tests/**/status_picture_dashboard/`, `db/clients/` | UNCHANGED | Fleet/status/SQL untouched |
| root `conftest.py` | UNCHANGED | No fixture import change |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` and `AlertsAnalysisPage` are not restructured. The population
  page keeps composing them; only its own locators/readers change.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Alerts chart titles, date-field labels, page-rail
  name, and `listbox` structure stay on the alerts domain page and in the alerts golden file. `core/`
  references none of them. Report tables, tooltips, and drilldowns live on the domain page, exactly as the
  constitution requires. The root `conftest.py` is untouched.
- **Existing tests are the contract (III)**: PASS with an explicit gate. The alerts domain page object IS
  edited, so the alerts UI smoke suite (`tests/ui/alerts_analysis_dashboard/`) MUST pass after the change;
  a task enforces this. Removing the `DISTRICT_CHART` class constant is a surface change, so its three test
  references are updated in the same change (allowed by Principle III). No `core/` or fleet navigation
  surface is touched, so the fleet smoke suite is unaffected and stays green.
- **Page object discipline (IV)**: PASS. Tests drive the browser through alerts page readers. The
  bilingual locators, title accessor, and listbox readers are page methods, not ad-hoc locators in a test
  body. The sanity comparison stays in the alerts sanity package.
- **Warehouse as source of truth (V)**: PASS with the same recorded deviation as the sibling alerts sanity
  slices. These sanity tests compare the report to the checked-in golden file, not to live SQL. Justified
  in Complexity Tracking. No SQL is added; `db/clients/alerts.py` is unchanged.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay on the existing pytest run path.
  The readers still raise/return as before on a true failure; the skip guards remain.
- **Extract shared behavior only (VII)**: PASS. No new abstraction in `core/`. The bilingual locators,
  dynamic title, listbox readers, and the parameterized show-as-table helpers are alerts-specific report
  behavior, which the constitution requires to stay on the alerts domain page — not in the generic
  Layer 2 `core/components/`.

**Result**: No unjustified violations.

## Project Structure

### Documentation (this feature)

```text
specs/043-alerts-analysis-fixes/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── population-fixes.md
```

### Source Code (repository root)

```text
pages/alerts_analysis/population_page.py              # EDIT
      ├── before_report_ready_check()                 #   bilingual .or_() page-rail switch (He/En)
      ├── set_between_dates(start, end)               #   bilingual .or_() date fields (He/En)
      ├── _fill_input(...)                            #   accept Hebrew+English aria-label prefixes
      ├── district_chart_title_for(level)             #   NEW static: "התרעות לפי " + level_name
      ├── district_chart_title(level=None)            #   NEW accessor from active-level state
      ├── set_hierarchy_level(level)                  #   record active level; wait for NEW title
      ├── set_district_aggregation / _hierarchy_control / chart_total / _visual_container / _district_visible_total
      ├── read_district_labels()                      #   listbox pairing + show-as-table fallback
      ├── read_hour_buckets()                         #   listbox pairing + show-as-table fallback
      ├── read_hour_daily_avg()                       #   same fallback; average column / series
      ├── _click_show_as_table()                      #   already He/En; parameterize error by title
      ├── _alert_column_table(header=...)             #   parameterize column header (התרעות / ממוצע)
      └── _leave_visual_table(title)                  #   leave any visual's table (not only dates)

tests/ui/alerts_analysis_dashboard/test_population_invariants.py  # EDIT (DISTRICT_CHART -> accessor; smoke gate)
tests/ui/alerts_analysis_dashboard/population_snapshot.py         # EDIT (DISTRICT_CHART -> accessor)
tests/unit/test_population_page.py                               # EDIT (assert static base title)

tests/sanity/alerts_analysis_dashboard/test_data_validation.py   # AUDIT (hierarchy + hour tests reach assertions)

data/alerts/db_sanity_am_kalavi.yaml                 # UNCHANGED (golden values read-only)
core/                                                # UNCHANGED (core/portal, core/components)
pages/fleet_dashboard/, pages/status_picture/        # UNCHANGED
tests/**/fleet_dashboard/, tests/**/status_picture_dashboard/, db/clients/  # UNCHANGED
conftest.py (root)                                   # UNCHANGED
```

**Structure Decision**: Fix the alerts domain page object in place — add bilingual `.or_()` locators for
the page-rail switch and date fields, replace the `DISTRICT_CHART` constant with a `district_chart_title()`
accessor backed by an active-level field, wait for the drilled title after `set_hierarchy_level`, and add
a listbox-aware read path (with the proven Show-as-a-table fallback, parameterized off the dates helpers)
to `read_district_labels`, `read_hour_buckets`, and `read_hour_daily_avg`. Update the three test
references to the removed constant, audit the hierarchy/hour tests, and leave the fleet/status suites, the
e2e suite, `core/`, and every golden metric value as they are.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: the `test_hierarchy_*` / `test_alerts_by_hour_*` tests compare the alerts report to `data/alerts/db_sanity_am_kalavi.yaml` instead of a live warehouse query | The alerts sanity suite already uses this golden file as the baseline; the numbers are a recorded snapshot. | A live SQL client would fail whenever the warehouse moves past the snapshot. The e2e suite remains the live comparison. |
| Removing a public class constant (`DISTRICT_CHART`) that three test modules reference | The constant is a hardcoded title that is wrong after a drill-down; a dynamic accessor is the only correct anchor. | Keeping the constant and layering a second dynamic title would leave two sources of truth and still break the drilled-down readers. The three references are updated in the same change. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- The tests load only `data/alerts/db_sanity_am_kalavi.yaml` and do not read `settings.DB_ENVIRONMENT`.
- Alerts chart titles, date-field labels, the page-rail name, and the `listbox` structure are owned by the
  alerts page / golden file; no alerts label is copied into `core/`.
- The alerts domain page object IS edited, so the alerts UI smoke gate (`tests/ui/alerts_analysis_dashboard/`)
  is triggered and enforced as a task; it must be green. The fleet smoke suite is unaffected (no `core/`
  or fleet edit) and stays green.
- Public alerts reader names and return types are unchanged; the title accessor and listbox readers are
  additive. The only surface change — removing `DISTRICT_CHART` — has its three references updated in the
  same change.
- Skip-guard behavior is preserved: a genuinely absent control still skips with its descriptive message.
- No SQL client and no `core/` parser is added; the fleet/status modules and the root `conftest.py` are
  absent from the edit list. The show-as-table generalization stays on the alerts domain page (Principle VII).
