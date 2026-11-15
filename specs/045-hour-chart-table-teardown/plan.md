# Implementation Plan: YAML-Only UI Blockers

**Branch**: `feature/reportportal-integration` (spec directory `045-hour-chart-table-teardown`) | **Date**: 2026-11-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/045-hour-chart-table-teardown/spec.md`, revised by the 2026-11-03 YAML-only UI blockers brief.

**Note**: This plan is filled by `/speckit-plan`. `tasks.md` is not regenerated here.
`.specify/feature.json` stays on this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`).

## Summary

UI-to-YAML sanity on Screen 2 stays the check. The one alerts UI test that runs warehouse SQL
is skipped so a missing or refusing `[FACT].[AlertsRedWeb]` does not fail the smoke path.
Two Playwright interactions on `AlertsPopulationPage` are adjusted so the YAML tests can click
the district drill-down and find the hour chart.

1. **Skip the live SQL test** — Decorate `test_alerts_db_parity_last_30_days` with
   `@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")`.
   That test is the only alerts UI test that calls `AlertsDBRunner` (`alerts_db`) and
   `validate_dashboard_generic` against `data/alerts/alerts_contract.yaml`, whose confirmed
   KPIs read `[FACT].[AlertsRedWeb]`. The YAML module
   `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` is not skipped. Its
   `*_matches_db` names load `data/alerts/db_sanity_am_kalavi.yaml`. Do not edit that file,
   the contract, or `db/clients/alerts.py`.
   Three unit tests scan the parity file and assert `"mark.skip" not in` its source
   (`test_remaining_visuals_use_stub_sql`, `test_alerts_stubs_do_not_hide_connection_errors`,
   `test_population_page_stubs`). Drop only that assertion. Keep the bans on `pytest.skip`
   and `importorskip`. `@pytest.mark.skip` does not contain those two substrings.
   Replace the in-function sentence "A missing or refusing Alerts database must fail this
   test. Do not skip it." with an English comment that the skip is temporary and the SQL
   contract is unchanged.
2. **Force-click hierarchy drill-down** — In `set_hierarchy_level`, change `control.click()`
   to `control.click(force=True)`. `_hierarchy_control` already returns the visible button,
   tab, or option named `נפה`, `רשות`, or `יישוב` inside the district visual. The visual
   header toolbar intercepts the pointer; `force=True` sends the click anyway. `יישוב` uses
   the same method, so it gets the same click. Do not change `set_district_aggregation`.
   An English comment inside the function says the force click bypasses the visual header
   toolbar.
3. **Hour-chart title without a visible filter** — `HOUR_CHART` is
   `גרף התרעות וגם ממוצע לפי שעה`. `_title_anchor` today requires
   `get_by_text(title).filter(visible=True)`, then a visible group, and raises
   `Chart {title!r} title is not visible`. `_leave_visual_table` then
   `expect`s that same visible text after Back. For `HOUR_CHART` only, drop
   `.filter(visible=True)`. Prefer a match inside a visual-container ancestor so a hidden
   tooltip that is not in a visual is not the anchor. The post-back wait for this title uses
   attached text, not `to_be_visible`. Other titles keep `.filter(visible=True)` and
   `to_be_visible`. `_report_ready_locator` keeps `.filter(visible=True)` on `מרחק מהגבול`.

Page-switch, the ready phrase, the `התרעות` hour column, quote folding, the warned-card date
wait, and Show-as-a-table `finally` teardown stay as they are. `core/` is not edited.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, Playwright (`Locator.click(force=True)`, `get_by_text`
without a visible filter). No new package.

**Storage**: Golden record `data/alerts/db_sanity_am_kalavi.yaml` is read by sanity and is not
edited. Contract `data/alerts/alerts_contract.yaml` still contains `[FACT].[AlertsRedWeb]`
SQL and is not edited. `db/clients/alerts.py` is not edited. The parity test that executes
that SQL is skipped.

**Testing**: `pytest tests/unit/test_db_parity_engine.py` after the three `mark.skip` scans
are relaxed. `pytest tests/ui/alerts_analysis_dashboard/` must skip
`test_alerts_db_parity_last_30_days` and still run freshness and population invariants.
`pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity` is the
YAML gate (needs portal auth). Fleet smoke is not a gate.

**Target Platform**: Windows workstation; Chromium against the organizational Power BI portal.

**Project Type**: Temporary test skip plus two locator/click fixes on the alerts population
page. No new page, no new module, no `core/` change.

**Performance Goals**: `click(force=True)` does not add a wait. The hour-title lookup does
not spend `self.timeout` proving a node Playwright has marked hidden. The ready locator is
unchanged.

**Constraints**:

- Skip reason string is exactly `Focusing strictly on YAML validation; DB checks temporarily disabled` (FR-014).
- YAML sanity tests are not skipped. They do not open SQL (FR-014).
- Golden YAML, `alerts_contract.yaml`, and `db/clients/alerts.py` are not edited (FR-014, AC-007).
- `pytest.skip` and `importorskip` stay absent from `test_db_parity.py` (FR-014).
- Hierarchy click is `control.click(force=True)` inside `set_hierarchy_level` (FR-015).
- Visible filter is removed only for `HOUR_CHART` in `_title_anchor` and the post-back wait
  in `_leave_visual_table` (FR-016).
- `_report_ready_locator` stays a visible match on `מרחק מהגבול` (FR-010, FR-016).
- In-function comments are English (FR-009).
- Do not lift the hierarchy label or the hour title into Layer 0 or Layer 2
  (Constitution II, VII).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `tests/ui/alerts_analysis_dashboard/test_db_parity.py` | EDIT | Skip `test_alerts_db_parity_last_30_days` with the required reason. Update the in-function comment. |
| `tests/unit/test_db_parity_engine.py` | EDIT | Remove the three `"mark.skip" not in` assertions against that file. Keep `pytest.skip` and `importorskip` bans. |
| `pages/alerts_analysis/population_page.py` | EDIT | `set_hierarchy_level` uses `click(force=True)`. `_title_anchor` and the hour branch of `_leave_visual_table` drop `filter(visible=True)` for `HOUR_CHART` only. |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | UNCHANGED | YAML comparisons stay collected |
| `data/alerts/db_sanity_am_kalavi.yaml` | UNCHANGED | Not edited |
| `data/alerts/alerts_contract.yaml` | UNCHANGED | SQL text stays; the test that runs it is skipped |
| `db/clients/alerts.py` | UNCHANGED | `AlertsDBRunner` stays |
| `core/portal/`, `core/components/` | UNCHANGED | |
| fleet / status-picture / credit | UNCHANGED | |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `ReportShell` is not edited. Hierarchy click and the hour-title
  locator stay on `AlertsPopulationPage`, which already inherits `AlertsAnalysisPage` →
  `ReportShell`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `נפה`, `רשות`, `יישוב`, and
  `גרף התרעות וגם ממוצע לפי שעה` stay on the alerts page. `core/` is not edited. Root
  `conftest.py` is untouched. The skip does not move SQL into `core/`.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS with a recorded, temporary
  exception on one alerts test. The shared `ReportShell` and the fleet page are not edited, so
  fleet smoke is not the gate. Alerts UI smoke still runs freshness and population invariants.
  The parity test is skipped instead of failing on `[FACT].[AlertsRedWeb]`. Public reader names
  and return types stay. The three unit scans that would reject the decorator are updated in
  the same change. The YAML sanity module stays the executable check for Screen 2.
- **Page object discipline (IV)**: PASS. The force click and the hour-title locator stay on the
  page object. Sanity tests do not gain locators.
- **Warehouse as source of truth (V)**: PASS with a temporary, justified deviation. This slice
  skips the only alerts UI test that executes warehouse SQL. It does not delete the client, the
  contract, or the golden comparison. Sanity still compares UI to
  `data/alerts/db_sanity_am_kalavi.yaml`, which is the existing recorded deviation for this
  suite. See Complexity Tracking.
- **Observability (VI)**: PASS. HTML, CSV, screenshots, and traces stay. A skipped test is
  reported as skipped.
- **Extract shared behavior only (VII)**: PASS. The drill-down click and the hour-title
  exception stay on the alerts page. They are not lifted into `core/components/` or
  `core/portal/`.

**Result**: No unjustified violations. Phase 0 may proceed.

## Project Structure

### Documentation (this feature)

```text
specs/045-hour-chart-table-teardown/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── hour-chart-table.md
│   ├── screen2-ready-and-quotes.md
│   ├── page-switch-hook.md
│   └── yaml-only-ui-blockers.md
└── tasks.md             # Not regenerated by this /speckit-plan
```

### Source Code (repository root)

```text
tests/ui/alerts_analysis_dashboard/test_db_parity.py
      └── test_alerts_db_parity_last_30_days()   # @pytest.mark.skip, exact reason

tests/unit/test_db_parity_engine.py
      └── three source scans                     # drop "mark.skip" not in; keep the other two bans

pages/alerts_analysis/population_page.py
      ├── set_hierarchy_level()                  # control.click(force=True) for נפה / רשות / יישוב
      ├── _title_anchor()                        # HOUR_CHART: no filter(visible=True); prefer a visual container
      ├── _leave_visual_table()                  # HOUR_CHART post-back wait: attached, not visible
      ├── _report_ready_locator()                # unchanged: visible מרחק מהגבול
      └── before_report_ready_check()            # unchanged page-switch click

tests/sanity/alerts_analysis_dashboard/test_data_validation.py
      └── YAML loaders                           # UNCHANGED, still collected

data/alerts/db_sanity_am_kalavi.yaml             # UNCHANGED
data/alerts/alerts_contract.yaml                 # UNCHANGED
db/clients/alerts.py                             # UNCHANGED
core/                                            # UNCHANGED
```

**Structure Decision**: The skip lives on the single test that opens SQL, not on the fixture
and not on the YAML suite. The click and the title exception live on the alerts population
page because both labels are report-specific. A hidden hour title is accepted only when it
sits in a visual container, so the existing tooltip note in `_title_anchor` still holds.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: `test_alerts_db_parity_last_30_days` no longer compares UI to live SQL, including `[FACT].[AlertsRedWeb]` | The brief isolates UI-to-YAML and ignores direct SQL until that table is available. The client and the contract stay so the check can return later by removing the decorator. | Leaving the test active fails alerts UI smoke on the warehouse error. Deleting the SQL would throw away the contract. Skipping the YAML `*_matches_db` tests would drop the check this slice is keeping. |
| Principle V (existing): sanity still compares Screen 2 to `data/alerts/db_sanity_am_kalavi.yaml` | That file is already the suite's snapshot. This slice does not edit it. | A live nafa or hour query is the check being turned off. |
| Principle III: three unit assertions that forbid `mark.skip` in the parity file are relaxed | Those asserts reject the decorator the brief requires. `pytest.skip` and `importorskip` stay banned, so a body-level skip is still rejected. | Leaving the asserts in place makes `pytest tests/unit/test_db_parity_engine.py` fail as soon as the decorator is added. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the justified Principle V and III
deviations above:

- The SQL skip is one decorator on `test_alerts_db_parity_last_30_days`. `alerts_db`,
  `AlertsDBRunner`, and `alerts_contract.yaml` stay. YAML sanity stays collected.
- The three unit scans drop only `"mark.skip" not in`. They still reject `pytest.skip` and
  `importorskip`.
- `set_hierarchy_level` force-clicks the control `_hierarchy_control` already resolved.
  Lookup still uses a visible role. `set_district_aggregation` is not edited.
- `_title_anchor` and `_leave_visual_table` drop `filter(visible=True)` only when
  `title == self.HOUR_CHART`. The chosen node must sit in a visual container. Other titles
  and `_report_ready_locator` keep the visible filter.
- `core/` is not edited. Fleet smoke is not required.
- In-function comments stay English.

**Result**: No unjustified violations.
