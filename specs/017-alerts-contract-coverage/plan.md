# Implementation Plan: Alerts Contract Coverage

**Branch**: `feature/reportportal-integration` (spec directory `017-alerts-contract-coverage`) | **Date**: 2026-10-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/017-alerts-contract-coverage/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration` at the time of this plan). Feature 016 stays as the
engine upgrade; this slice only fills the contract and the stub constants.

## Summary

The parity engine already forwards `scope`, `category_id`, and `visual` (`kpi`, `gauge`, `chart`,
`map`). The Alerts contract still lacks the repeated time-bucket cards and the static
current-versus-previous settlement chart. Feature 016 deferred that chart on purpose.

This feature does not change Layer 2 or the engine. It adds contract rows and matching stub SQL:

- Nine threat KPIs. `scope` is the Hebrew section. `name` is `היום`, `אתמול`, or
  `סה"כ בטווח שנבחר`. `category_id` is `"1"`, `"2"`, or `"10"` as specified.
- Six general KPIs. `scope` is the stable base `אוכלוסייה מותרעת` or `אזורי התרעה תחת ירי`.
  The same three card titles. No `category_id`. `visual` is `kpi` (no invented gauge denominator).
- One chart whose `name` is the full static title, including `ביממה הנוכחית והקודמת`. Its SQL
  returns no rows and does not mention the date window.
- Existing feature-016 metrics stay, including their real category SQL and the three older stubs.
- Connection errors keep propagating. No skip is added.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: PyYAML (contract load) and SQLAlchemy 2.0.51 `text()` (already used by
`AlertsDBRunner`). No new package. Playwright is unchanged.

**Storage**: Read-only SQL Server, database `settings.DB_ALERTS_NAME`. No schema change. New KPI
stubs are `SELECT 0`. The new chart stub selects two columns with `WHERE 1 = 0` and does not bind
dates. The runner still passes `start_date` and `end_date`; unused binds are ignored.

**Testing**: `pytest`. Extend `tests/unit/test_db_parity_engine.py` so it loads the real contract
and asserts the new rows by `(name, scope)`. No browser. Live gate stays
`pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity` and is not skipped.
Constitution III: `pytest tests/ui/fleet_dashboard/` stays 100% green. `core/` and the engine are
not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal
for the live gate only.

**Project Type**: Internal validation framework. Domain contract under
`tests/ui/alerts_analysis_dashboard/`. SQL constants in `db/clients/alerts.py`.

**Performance Goals**: N/A. Sixteen additional metrics, one scalar or one empty row set each.

**Constraints**:

- `core/` and `tests/helpers/db_parity_engine.py` MUST NOT change (Constitution II, FR-007).
- Hebrew, category ids, and SQL stay in the contract and the Alerts client (FR-007, AC-005).
  The client MUST NOT hardcode `'1'`, `'2'`, `'10'`, or Hebrew.
- New KPI `visual` is `kpi`. Do not add `maximum_sql` (FR-002, research R3).
- Metric `name` and `scope` MUST NOT contain `שלושים יום אחרונים` (FR-003). The comparison
  chart name MUST keep `ביממה הנוכחית והקודמת` and the one-yod spelling `ישובים` (FR-004).
- Chart SQL MUST NOT reference `:start_date`, `:end_date`, or `AlertDate` (FR-005).
- Do not add `pytest.skip`, `pytest.importorskip`, or `pytest.mark.skip` on
  `test_alerts_db_parity_last_30_days`. Do not catch a connection error (FR-009).
- Inline comments in edited Python and YAML MUST be English only (FR-008).
- `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` keeps its signature.

**Scale/Scope**: Contract, Alerts SQL constants, catalog section 8, and the contract unit test.
Sixteen new metrics. No `core/` diff.

| Path | Change | Purpose |
|------|--------|---------|
| `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` | EDIT | Nine threat KPIs, six general KPIs, one static chart |
| `db/clients/alerts.py` | EDIT | Stub constants only. No new method, no try/except |
| `tests/unit/test_db_parity_engine.py` | EDIT | Assert the new rows by name plus scope, and the chart SQL |
| `docs/COVERAGE_CATALOG.md` | EDIT | Catalog the new stubs beside the feature-016 rows |
| `tests/ui/alerts_analysis_dashboard/test_db_parity.py` | NONE | Already loads the whole file and does not skip |
| `tests/helpers/db_parity_engine.py` | NONE | Scope, category id, and chart rows already work |
| `core/components/` | NONE | `KPI.number` and `Chart.read` already take `scope` |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. No portal, SSO, iframe, or slicer work. `AlertsAnalysisPage` is
  unchanged.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. New Hebrew strings and category ids live in
  the YAML. Stub SQL lives in `db/clients/alerts.py` with no Hebrew and no id literals. `core/` is
  not edited.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. The unit test that loads the
  real contract is updated in the same change so the new duplicate titles are asserted by
  `(name, scope)`. Fleet smoke is the regression gate. Public engine and page APIs stay.
- **Page object discipline (IV)**: PASS. The date-range click stays on
  `AlertsAnalysisPage.select_date_range`. Visual reads stay inside `KPI` and `Chart`.
- **Warehouse as source of truth (V)**: PASS. New queries are stubs and are still executed, so a
  missing database fails the test. The catalog marks them unconfirmed. The six existing category
  queries stay real SQL. Layer 0 still has no business SQL.
- **Observability (VI)**: PASS. No logging path changes. `scalar` and `rows` already call
  `log_db_query`. HTML and CSV artifacts stay on the current run-report path.
- **Extract shared behavior only (VII)**: PASS. No new generic API. Scope and chart parsing stay
  the feature 014 and 015 readers.

**Result**: No violations. Complexity Tracking has no rows.

## Project Structure

### Documentation (this feature)

```text
specs/017-alerts-contract-coverage/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    └── alerts-contract-coverage.md
```

### Source Code (repository root)

```text
tests/ui/alerts_analysis_dashboard/alerts_contract.yaml
  ├── existing six category KPIs, ranking chart, map, policy status (unchanged)
  ├── nine threat KPIs: scope + time-bucket name + category_id + SELECT 0
  ├── six general KPIs: population or area scope + time-bucket name + SELECT 0
  └── one static chart: full title, empty row set, no date predicate

db/clients/alerts.py
  ├── THREAT_KPI_STUB_SQL = "SELECT 0"
  ├── POPULATION_KPI_STUB_SQL = "SELECT 0"
  ├── AREA_KPI_STUB_SQL = "SELECT 0"
  └── PERIOD_COMPARISON_CHART_SQL = empty two-column SELECT (no dates)

tests/unit/test_db_parity_engine.py
  └── contract assertions keyed by (name, scope) for the new rows

docs/COVERAGE_CATALOG.md
  └── section 8 rows for the new stubs
```

**Structure Decision**: Keep the feature-010 split. The engine is already the reader. This feature
only adds domain rows and the SQL text those rows execute. Layer 2 is a dependency, not a work surface.

## Complexity Tracking

No constitution violations. Table left empty.

## Constitution Check (Post-Design)

Re-evaluated after Phase 0 and Phase 1. Still PASS on I–VII:

- Design adds no file under `core/` and no edit to `tests/helpers/db_parity_engine.py`.
- Threat ids stay in the YAML as strings. The Python constants are `SELECT 0` and one empty chart
  query. They contain no Hebrew and no category id.
- General population and area cards are `visual: kpi` with no `maximum_sql`. Gauge remains
  available in the engine for a later confirmed denominator. This slice does not invent one.
- The comparison chart name is the full static title, including the one-yod `ישובים` spelling and
  the permanent day-pair phrase. It is not folded into the ranking-chart anchor.
- The chart statement omits date binds. Research R5 confirmed SQLAlchemy 2.0.51 accepts the extra
  `start_date` and `end_date` the runner always sends.
- Existing category measures, the ranking chart, the map, and the policy status are unchanged.
- Unresolved `NEEDS CLARIFICATION` markers: none.
- The Alerts parity test is not skipped when the database connection fails. Stub statements are
  executed.
