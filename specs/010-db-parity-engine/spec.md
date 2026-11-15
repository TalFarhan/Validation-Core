# Feature Specification: Generic DB Parity Engine + Alerts Dashboard Pilot

**Feature Branch**: `010-db-parity-engine`
**Created**: 2026-10-11
**Status**: Ready for planning
**Input**: Build a generic, declarative UI-vs-DB parity engine on top of the dependency-inversion refactor
(009) and pilot it on the Alerts Dashboard using 2 KPIs over a trailing 30-day window.

## Problem Statement

Today UI↔DB parity logic is fleet-specific: the warehouse client (`db/client.py`) hardcodes vehicle tables
and KPI shapes, and KPI reading lives inside `pages/fleet_dashboard/main_dashboard_page.py`. Adding a second
report (Alerts) would force copying both the KPI-reading chrome and bespoke SQL wiring. We need a
**report-agnostic** way to read a Power BI KPI card by its title and compare it to a parameterized SQL query
declared in a per-report **contract file**, so new reports are onboarded by adding data (a YAML contract),
not code.

The pilot proves the engine end-to-end on the Alerts Dashboard: two KPIs ("אזורי התרעה תחת יריי בשלושים יום
האחרונים" and "אוכלוסיה מותרעת בשלושים יום האחרונים") filtered to the last 30 days via the existing slicer.

## User Scenarios & Testing

### Primary Scenario

As a validation engineer, I declare each Alerts KPI once in a YAML contract (display title + parameterized
SQL), then run one `@pytest.mark.db_parity` test that navigates to the Alerts Dashboard, selects the
"שלושים יום אחרונים" date range, and asserts the UI KPI value equals the DB value for every metric in the
contract — with no report-specific Python in `core/`.

### Acceptance Criteria

- **AC1**: A generic `KPI` component (Layer 2, `core/components/kpi.py`) locates a KPI card by its title text
  inside the Power BI iframe, reads the displayed value, and normalizes it (strip commas, spaces, and
  invisible RTL marks such as `\u200f`) to a clean comparable value. It contains **no** report-specific
  titles or SQL.
- **AC2**: A declarative engine `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)`
  loads a YAML contract, iterates metrics, reads each UI value via the `KPI` component, runs the metric's
  parameterized SQL via the DB client, and asserts equality for every metric.
- **AC3**: The Alerts contract (`tests/ui/alerts_dashboard/alerts_contract.yaml`) declares the two pilot
  metrics with `name` (UI title) and `sql_query` using named binds `:start_date` and `:end_date`.
- **AC4**: An Alerts DB runner (`db/clients/alerts.py`) connects to the Alerts database and executes queries
  via SQLAlchemy `text()`, binding `:start_date` / `:end_date` as parameters (never string-formatted).
- **AC5**: A test (`tests/ui/alerts_dashboard/test_db_parity.py`, marked `@pytest.mark.db_parity`) navigates
  to the Alerts Dashboard, selects "שלושים יום אחרונים" via the `Slicer` component, computes `start_date` /
  `end_date` in Python, and calls `validate_dashboard_generic`.
- **AC6**: All parameterized SQL uses SQLAlchemy `text()` with bound parameters; no date is injected by
  string formatting / f-strings.
- **AC7**: All inline code comments within functions are in English only.
- **AC8**: The fleet smoke suite (`tests/ui/fleet_dashboard/`) remains 100% green (additive change only).

## Requirements

### Functional Requirements

- **FR-001**: Provide a generic `KPI` component that composes a Power BI iframe `FrameLocator`, finds a card
  by its (opaque) title string, extracts the value node, and returns a normalized string + numeric form.
- **FR-002**: Provide `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` that reads
  the contract, and for each metric compares UI vs DB, aggregating per-metric results and asserting equality.
- **FR-003**: Provide the Alerts YAML contract declaring the two pilot metrics (titles + parameterized SQL).
- **FR-004**: Provide `db/clients/alerts.py` that connects to the Alerts DB and runs `text()` queries with
  `:start_date` / `:end_date` binds, returning a scalar value.
- **FR-005**: Provide `tests/ui/alerts_dashboard/test_db_parity.py` (`@pytest.mark.db_parity`) that drives the
  slicer, computes the 30-day window, and invokes the engine.
- **FR-006**: Register the `db_parity` marker in `pytest.ini`.
- **FR-007**: Preserve observability: each UI read, DB query, and assertion is logged through the existing
  run-report hooks (`log_kpi_read`, `log_db_query`, `log_assertion`) when a report is active.

### Non-Goals

- No refactor of the fleet KPI reading or `db/client.py` vehicle logic (fleet keeps its current path).
- No chart / tooltip / drilldown parity for Alerts (KPI cards only in the pilot).
- No change to Layer 0 portal navigation or SSO.
- No new slicer kinds; reuse the existing `Slicer` dropdown behavior.

## Success Criteria

- The Alerts parity test passes with UI == DB for both pilot metrics over the trailing 30-day window.
- `core/` contains zero Alerts-specific strings or SQL (verifiable by grep); all domain values live in the
  YAML contract and the test.
- `pytest tests/ui/fleet_dashboard/` stays 100% green.
