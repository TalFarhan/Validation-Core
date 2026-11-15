# Implementation Plan: Alerts DB Parity Upgrade

**Branch**: `feature/reportportal-integration` (spec directory `016-alerts-parity-upgrade`) | **Date**: 2026-10-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/016-alerts-parity-upgrade/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command). `.specify/feature.json` pins this directory. Planning does not switch the git
checkout (`feature/reportportal-integration` at the time of this plan).

## Summary

The Alerts parity pilot still calls `KPI.number(name)` with no scope, treats every visual as a scalar
card, and filters `[FACT].[AlertsRedWeb]` with one grouped `CategoryID IN ('1', '2', '10')`. Metric
titles also embed the 30-day slicer phrase.

This feature does not change Layer 2. `KPI.number` / `KPI.scale`, `Chart.read`, and
`classify_presence` already exist (features 014 and 015). The work is to teach the parity engine
and the Alerts contract to use those readers, to teach `AlertsDBRunner` to bind one `category_id`
at a time, and to add the three remaining report visuals with stub SQL that is actually executed.

Technical approach:

- Extend the YAML metric with optional `scope`, `visual` (`kpi` | `gauge` | `chart` | `map`),
  `compare` (`number` | `text` on a KPI), `maximum_sql`, `series_index`, and `category_id`.
- Numeric `kpi` keeps `KPI.number`. Text `kpi` uses `KPI.read_text` and compares strings. `gauge`
  uses `KPI.scale` and checks `value` and `maximum` against two scalars. `chart` uses `Chart.read`
  and checks category rows. `map` locates the visual and checks `classify_presence` (`value` versus
  `empty`, with 0 counted as `value`).
- The Alerts contract gains three metrics whose SQL is the stub constants in `db/clients/alerts.py`:
  settlements chart, alerts map, and policy status. The live test does not skip when the database
  is missing. Connection errors propagate.
- `AlertsDBRunner.scalar` and a new `rows` method bind `:start_date`, `:end_date`, and, when the
  metric sets it, `:category_id`. No string formatting.
- Alerts metric `name` values drop the date phrase. The test still selects the slicer option and
  passes the window.
- Category ids, Hebrew titles, scopes, and SQL stay in `tests/ui/alerts_analysis_dashboard/` and in
  the runner's parameter list. Nothing new under `core/`.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright sync API (already used by `KPI` and `Chart`), pytest, PyYAML,
SQLAlchemy 2.x `text()` + pyodbc. No new package.

**Storage**: Read-only SQL Server, database `settings.DB_ALERTS_NAME`, table `[FACT].[AlertsRedWeb]`.
No schema change. Dates and `category_id` are bound parameters.

**Testing**: `pytest`. New unit tests drive the engine with fake page, KPI, chart, and DB objects
(no portal). Live gate: `pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity`.
Constitution III: `pytest tests/ui/fleet_dashboard/` stays 100% green. `core/` is not edited, so that
suite is a non-regression check rather than a Layer 2 rewrite.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework (Layer 0 `core/portal`, Layer 2 `core/components`,
domain Alerts page under `tests/ui/alerts_analysis_dashboard/`, engine in `tests/helpers/`).

**Performance Goals**: N/A. One UI read and one or two SQL round-trips per metric. Chart queries
return the category grain, not the fact grain.

**Constraints**:

- `core/` MUST NOT gain Alerts titles, scopes, category ids, Hebrew strings, or SQL (Constitution II,
  FR-008, FR-014).
- Dates and category ids MUST be SQLAlchemy binds. The grouped `IN ('1', '2', '10')` list leaves the
  parity queries (FR-006, FR-007).
- `KPI.number` remains the reader for `visual: kpi` with `compare: number` (the default).
  `compare: text` uses `KPI.read_text` and does not parse a number (FR-002a, FR-003).
  Gauges MUST use `KPI.scale` so the maximum is visible (FR-004). `0` is a real value, a real
  maximum, and a present map (`value`), not an empty map (FR-002b).
- The three new metrics execute stub SQL from `db/clients/alerts.py`. Do not add `pytest.skip`,
  `pytest.importorskip`, or `pytest.mark.skip` on `test_alerts_db_parity_last_30_days`. Do not
  catch a connection error to force a pass (FR-016, FR-017).
- Metric names MUST NOT contain the slicer phrase `שלושים יום אחרונים` (FR-009).
- Inline comments in edited Python and YAML MUST be English only (FR-013).
- `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` keeps its signature
  (AC-004).
- `AlertsDBRunner.scalar` NULL coercion stays `0`, matching today's KPI path. Chart NULL cells stay
  `None` so a missing bar is not stored as zero.

**Scale/Scope**: Engine, Alerts runner, Alerts contract, Alerts parity test, coverage catalog, and
unit tests. No `core/` diff. Three additional contract metrics use stub SQL.

| Path | Change | Purpose |
|------|--------|---------|
| `tests/helpers/db_parity_engine.py` | EDIT | Scope, visual dispatch, gauge pair, chart rows, map presence, text KPI |
| `db/clients/alerts.py` | EDIT | Bind optional `category_id`; add `rows` and `cell`; stub SQL constants |
| `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` | EDIT | Stable names, per-id filters, settlements chart, map, policy text |
| `tests/ui/alerts_analysis_dashboard/test_db_parity.py` | EDIT | Slicer option stays in the test; no skip on database errors |
| `tests/unit/test_db_parity_engine.py` | NEW | Scope, gauge maximum, chart rows, map presence, text compare, binds |
| `docs/COVERAGE_CATALOG.md` | EDIT | Per-category rows plus the three stubbed visuals |
| `core/components/` | NONE | Consume `scope`, `KPI.scale`, `KPI.read_text`, `Chart.read`, `classify_presence` |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `AlertsAnalysisPage` already composes `ReportShell` and `Slicer`.
  This feature does not re-implement portal, SSO, iframe, or last-refresh behavior. A category
  slicer is added on that page only if a visual is hidden until the control changes, and the click
  still goes through `Slicer`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. No edit under `core/`. Scope strings, titles,
  category labels, and SQL are contract and test data. The engine forwards `scope` and `category_id`
  as opaque values and does not branch on UAV, Rockets, Terrorists, or Hebrew.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Fleet page and Layer 2 call
  shapes stay. `KPI.number(name)` remains valid. The Alerts parity test is updated in the same
  change as the contract. Fleet smoke is the regression gate in the quickstart.
- **Page object discipline (IV)**: PASS. The date-range click stays on `AlertsAnalysisPage.select_date_range`.
  Visual reads go through `KPI` and `Chart`, not locators in the test body.
- **Warehouse as source of truth (V)**: PASS. UI values are compared to bound `SELECT`s. The three
  new queries are stubs and are still executed, so a missing database fails the test instead of
  being marked covered. The catalog records them as unconfirmed SQL. Layer 0 still has no business SQL.
- **Observability (VI)**: PASS. Scalar reads keep `log_kpi_read`. Every check keeps `log_assertion`.
  Queries keep `log_db_query`, including `category_id` in the logged params. HTML and CSV artifacts
  stay on the current run-report path.
- **Extract shared behavior only (VII)**: PASS. No new generic API and no `Map` class. Gauge scale,
  scope, chart parsing, and `classify_presence` were extracted in features 012–015. This feature
  only calls them. Map lookup stays in the engine because feature 015 left presence on the caller.

**Result**: No violations. Complexity Tracking has no rows.

## Project Structure

### Documentation (this feature)

```text
specs/016-alerts-parity-upgrade/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    └── alerts-parity-engine.md
```

### Source Code (repository root)

```text
tests/helpers/db_parity_engine.py
  ├── metric fields: name, visual, compare, scope, category_id, sql_query, maximum_sql, series_index
  ├── kpi number → KPI.number(name, scope=scope) vs scalar
  ├── kpi text   → KPI.read_text(name, scope=scope) vs cell
  ├── gauge      → KPI.scale(name, scope=scope); value vs sql_query; maximum vs maximum_sql
  ├── chart      → Chart.read(name, scope=scope) vs rows()
  └── map        → classify_presence on the titled container vs cell

db/clients/alerts.py
  ├── scalar(..., category_id: str | None = None)   # NULL → 0, unchanged
  ├── rows(..., category_id: str | None = None)     # NULL number → None
  ├── cell(..., category_id: str | None = None)     # raw first column; NULL stays None
  └── SETTLEMENTS_CHART_SQL, MAP_PRESENCE_SQL, POLICY_STATUS_SQL

tests/ui/alerts_analysis_dashboard/
  ├── alerts_contract.yaml    # titles, scopes, ids, SQL (domain)
  ├── test_db_parity.py       # slicer option + date window (domain)
  └── page.py                 # unchanged unless a category slicer is required

core/components/kpi.py        # UNCHANGED — number, read_text, scale
core/components/chart.py      # UNCHANGED — read(title, scope)
core/components/visual.py     # UNCHANGED — classify_presence, count_data_marks, scope_host
docs/COVERAGE_CATALOG.md      # EDIT
```

**Structure Decision**: Keep the feature-010 split. The engine is a test helper, the Alerts runner is
the only SQL client that learns `category_id`, and the contract file is the only place that lists
ids `1`, `2`, and `10` or Hebrew titles. Layer 2 is a dependency, not a work surface.

## Complexity Tracking

No constitution violations. Table left empty.

## Constitution Check (Post-Design)

Re-evaluated after Phase 0 and Phase 1. Still PASS on I–VII:

- Design adds no file under `core/` and no report string to the engine. `category_id` is a bind name
  on the Alerts runner; the values stay in the YAML.
- Gauge checks use `KPI.scale` fields `value` and `maximum`. `minimum` is ignored unless a later
  feature adds `minimum_sql`. This feature's spec requires value and maximum only.
- Chart alignment is by label, with `None` for a missing cell or a SQL NULL. Scalar NULL→0 is
  unchanged so existing `ISNULL` KPI queries keep their meaning.
- Metric names are stable anchors. The 30-day option remains a test argument to
  `select_date_range`. The engine does not concatenate it onto `name`.
- Unresolved `NEEDS CLARIFICATION` markers: none. The id-to-label pairing is domain data confirmed
  at implementation and stored in the contract, not an open design choice (see research R4).
- Map, text KPI, and the three stub queries are specified in research R12–R16. `visual: map` is
  legal. The unknown-visual unit test uses another token. Stub SQL is executed. The Alerts parity
  test is not skipped when the database connection fails.
- The settlements chart name is the ranking-chart anchor without the slicer phrase. It must match
  one visual. The neighboring period-comparison chart is not a fourth metric in this slice.
