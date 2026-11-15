# Implementation Plan: Generic DB Parity Engine + Alerts Dashboard Pilot

**Branch**: `010-db-parity-engine` | **Date**: 2026-10-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-db-parity-engine/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`
(not this command).

## Summary

Build a **declarative, report-agnostic UI↔DB parity engine** and pilot it on the Alerts Dashboard. A new
Layer 2 `KPI` component (mirroring `Slicer`) reads a Power BI KPI card by its title and normalizes the value.
A YAML-driven engine, `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)`, iterates
contract metrics, reads each UI value via `KPI`, runs the metric's parameterized SQL through an Alerts DB
runner, and asserts equality. The pilot adds an Alerts contract with two 30-day KPIs, a thin Alerts DB client
using SQLAlchemy `text()` binds, and a `@pytest.mark.db_parity` test that selects "שלושים יום אחרונים",
computes the 30-day window in Python, and invokes the engine.

Technical approach: additive feature. Nothing in `core/` learns Alerts-specific titles or SQL — those live
only in the YAML contract and the test. Fleet code is untouched (fleet smoke is the regression gate).

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Playwright (sync API), pytest, SQLAlchemy 2.x + pyodbc (SQL Server), **PyYAML
(new)** for contract loading. Reuses `config.settings`, `db/connection.py`, `core/components/`, and the
existing run-report hooks.

**Storage**: Read-only SQL Server. New: the **Alerts database** (name from `DB_ALERTS_NAME`), queried via a
thin runner on top of `db/connection.create_db_engine(database=...)`. No schema changes.

**Testing**: `pytest` + Playwright Chromium. New marker `db_parity` (registered in `pytest.ini`,
`--strict-markers` is on). Regression gate: `pytest tests/ui/fleet_dashboard/` MUST stay 100% green
(Constitution III). Pilot gate: the Alerts parity test asserts UI == DB for both metrics.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal (same as
today).

**Project Type**: Internal validation framework (pytest page objects) with layered portal architecture
(Layer 0 `core/portal`, Layer 2 `core/components`, domain `pages/<report>/` + `tests/ui/<report>/`).

**Performance Goals**: N/A — two KPI reads + two scalar SQL queries per run. No throughput target.

**Constraints**:
- Parameterized SQL MUST use SQLAlchemy `text()` with bound `:start_date` / `:end_date`; **no** string
  formatting of dates (FR-006 / request rule).
- `core/` MUST NOT contain Alerts titles, SQL, or the contract path (Constitution II).
- All inline code comments within functions MUST be English only (request rule / AC7).
- Additive only: fleet behavior and `db/client.py` vehicle logic unchanged.

**Scale/Scope**: ~5 new files + 3 small edits:

| Path | Change | Purpose |
|------|--------|---------|
| `core/components/kpi.py` | NEW | Layer 2 generic `KPI` card reader + normalizer |
| `tests/helpers/db_parity_engine.py` | NEW | `validate_dashboard_generic(...)` declarative engine |
| `tests/ui/alerts_dashboard/alerts_contract.yaml` | NEW | Two pilot metrics (title + parameterized SQL) |
| `db/clients/__init__.py` | NEW | Package marker for DB client runners |
| `db/clients/alerts.py` | NEW | Alerts DB runner; `text()` binds for `:start_date` / `:end_date` |
| `tests/ui/alerts_dashboard/__init__.py` | NEW | Test package marker |
| `tests/ui/alerts_dashboard/page.py` | NEW | `ReportShell` binding + date-range `Slicer` definition |
| `tests/ui/alerts_dashboard/conftest.py` | NEW | `dashboard` + `alerts_db` fixtures |
| `tests/ui/alerts_dashboard/test_db_parity.py` | NEW | `@pytest.mark.db_parity` pilot test |
| `config/settings.py` | EDIT | Add `DB_ALERTS_NAME` |
| `pytest.ini` | EDIT | Register `db_parity` marker |
| `requirements.txt` | EDIT | Add `pyyaml>=6.0` |
| `docs/COVERAGE_CATALOG.md` | EDIT | Map the two Alerts KPIs ↔ SQL ↔ test (Constitution V) |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. The Alerts page composes `ReportShell` (Layer 0) and `Slicer` (Layer 2) like
  `AlertsAnalysisPage`; no portal/SSO/iframe logic is re-implemented. The new `KPI` reader is Layer 2
  (`core/components/`), the correct home for report-agnostic Power BI chrome.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. `core/components/kpi.py` takes the KPI title as an
  opaque argument and holds no Alerts/fleet strings or SQL. All domain values (KPI titles, SQL, the date-range
  slicer `role_name`, contract path) live in `tests/ui/alerts_dashboard/` and the YAML contract — never in
  `core/`. The engine lives in `tests/helpers/`, not `core/`.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Change is additive; no fleet source or
  public page-object API changes. `pytest tests/ui/fleet_dashboard/` is the required gate (see quickstart).
- **Page object discipline (IV)**: PASS. The browser is driven through the Alerts page object + `Slicer` +
  `KPI` component, not ad-hoc locators in the test body. The date-range selection goes through `Slicer.select`.
- **Warehouse as source of truth (V)**: PASS. Parity compares UI to the warehouse through a read-only DB
  runner. `docs/COVERAGE_CATALOG.md` is updated to map the two KPIs ↔ SQL ↔ test. Business SQL lives in the
  Alerts contract (data), not in Layer 0/Layer 2.
- **Observability (VI)**: PASS. Each UI read, DB query, and assertion is logged through the existing
  `log_kpi_read` / `log_db_query` / `log_assertion` run-report hooks; HTML/CSV artifacts are unaffected.
- **Extract shared behavior only (VII)**: PASS — now earned. KPI-card reading is extracted to Layer 2 **only
  because a second report (Alerts) requires it** (the exact trigger VII names). The extracted behavior is
  report-agnostic; fleet is intentionally not refactored in this feature (documented Non-Goal), so no unused
  generic API is invented.

**Result**: No violations. Complexity Tracking table left empty.

## Project Structure

### Documentation (this feature)

```text
specs/010-db-parity-engine/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification (anchor)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (entities: contract, metric, parity result)
├── quickstart.md        # Phase 1 output (run + verification steps)
└── contracts/           # Phase 1 output (engine + YAML + DB-runner contract)
    └── db-parity-engine.md
```

### Source Code (repository root)

```text
core/
└── components/
    ├── slicer.py             # unchanged (Layer 2 reference pattern)
    └── kpi.py                # NEW — Layer 2 generic KPI card reader + normalizer

db/
├── connection.py             # unchanged — create_db_engine(database=...) reused
├── client.py                 # unchanged — fleet vehicle client
└── clients/
    ├── __init__.py           # NEW — package marker
    └── alerts.py             # NEW — Alerts DB runner (text() binds)

config/
└── settings.py               # EDIT — add DB_ALERTS_NAME

tests/
├── helpers/
│   └── db_parity_engine.py   # NEW — validate_dashboard_generic(...)
└── ui/
    └── alerts_dashboard/
        ├── __init__.py          # NEW
        ├── page.py              # NEW — ReportShell binding + date-range Slicer
        ├── conftest.py          # NEW — dashboard + alerts_db fixtures
        ├── alerts_contract.yaml # NEW — two pilot metrics (title + SQL)
        └── test_db_parity.py    # NEW — @pytest.mark.db_parity pilot

docs/COVERAGE_CATALOG.md      # EDIT — KPI ↔ SQL ↔ test mapping for the two Alerts metrics
pytest.ini                    # EDIT — register db_parity marker
requirements.txt              # EDIT — add pyyaml>=6.0
```

**Structure Decision**: Keep the existing layered layout. The only genuinely new generic surface is
`core/components/kpi.py` (Layer 2, earned by a second report). Everything report-specific is confined to
`tests/ui/alerts_dashboard/` (page, contract, test) and the Alerts DB runner under `db/clients/`. The engine
is a test helper (`tests/helpers/`), consistent with `dashboard_validation.py`, so `core/` stays
domain-free. A new `tests/ui/alerts_dashboard/` suite is used (rather than reusing
`tests/ui/alerts_analysis_dashboard/`) to match the paths named in the request; its `page.py` reuses the
`AlertsAnalysisPage` pattern and adds a date-range slicer definition.

## Complexity Tracking

> No Constitution Check violations — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |
