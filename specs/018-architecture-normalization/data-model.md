# Data Model: Architecture Normalization

This feature moves modules. It does not add a runtime entity or a database table.
Field lists below are the stable surface that MUST survive the move.

## Entity: ReportPage

A `ReportShell` subclass. One module per report.

| Field | Rule |
|---|---|
| Module | `pages/<report>/page.py` |
| Class name | Unchanged (see the map in spec FR-001) |
| Base | `ReportShell` |
| Ready locator | Stays on the subclass (`_report_ready_locator`) |
| Test binding | `tests/ui/<suite>/conftest.py` sets `dashboard = bind_dashboard(PageClass)` |
| Fleet exception | `MainDashboardPage` stays in `pages/fleet_dashboard/main_dashboard_page.py` |

Relationships:

- A suite conftest imports exactly one `ReportPage`.
- Four pages (`MassEventsPage`, `LifeSavingGuidelinesPage`, `MayaSystemPage`,
  `PublicSheltersPage`) call `SharedSecondaryAuth`.
- `AlertsAnalysisPage` also composes `Slicer` for the date-range control. That
  composition moves with the class. `Slicer` stays in `core/components/slicer.py`.
- `CreditConsumptionPage` keeps its info-popup methods on the page class.

Validation:

- No `page.py` under `tests/ui/`.
- The class does not re-implement portal login, catalog search, iframe wait,
  visual-load timeout, or last-refresh verification.

## Entity: FleetFixtureSet

Pytest fixtures that construct the fleet page and the fleet warehouse client.

| Fixture | Scope | Provides |
|---|---|---|
| `dashboard` | function | `open_report(MainDashboardPage, auth_page, browser_context)` |
| `db_client` | session | `DatabaseClient()` from `db.clients.fleet` |
| `filter_data` | session | JSON object from `data/fleet/filters.json` |
| `filter_matrix` | session | JSON object from `data/fleet/filter_matrix.json` |
| `zero_count_filters` | session | `db_client.find_zero_count_filters(filter_data)`, or skip when none |

Registration (both required):

- `tests/ui/fleet_dashboard/conftest.py`
- `tests/e2e/conftest.py`

Not registered on root `conftest.py`.

Root keeps, and this feature does not redefine:

- `browser_context`, `session_page`, `auth_page`
- `run_report_book`, `test_run_report`, `video_run_dir`
- failure screenshot and trace hooks

Relationships:

- `dashboard` depends on root `auth_page` and `browser_context`.
- `zero_count_filters` depends on `db_client` and `filter_data`.
- Alerts and the other non-fleet suites keep their own `dashboard` fixture via
  `bind_dashboard`. They do not see this set.

## Entity: ReportSqlClient

A read-only runner. SQL text is report-specific. The connection factory is not.

| Client | Module | Class | Engine |
|---|---|---|---|
| Fleet | `db/clients/fleet.py` | `DatabaseClient` (`KpiType` beside it) | `create_db_engine()` default database |
| Alerts | `db/clients/alerts.py` | `AlertsDBRunner` | `create_db_engine(database=settings.DB_ALERTS_NAME)` |
| Generic | `db/connection.py` | functions only | `build_connection_string`, `create_db_engine` |

`DatabaseClient` public methods that MUST keep their signatures:

- `count_vehicles`
- `get_dashboard_kpis`
- `get_vehicle_by_id`
- `get_sample_vehicle_id`
- `get_unique_vehicle_id_for_search`
- `count_vehicles_by_id_contains`
- `count_grouped_by`
- `count_by_source`
- `count_by_unit`
- `count_by_sub_unit`
- `count_by_category`
- `count_by_withdrawal_reason`
- `find_zero_count_filters`

`AlertsDBRunner` public methods that MUST keep their signatures: `scalar`,
`rows`, `cell`. SQL constants in `db/clients/alerts.py` MUST keep their text.

Validation:

- `db/client.py` does not exist.
- `db/__init__.py` does not import `DatabaseClient` or `AlertsDBRunner`.
- `db/connection.py` has no vehicle, district, or alerts SQL.
- `core/` does not import `db.clients`.

## Entity: ReportDataCatalog

Domain files. Contents are copied verbatim. Only the path changes.

| Catalog | Path | Consumer |
|---|---|---|
| Fleet value catalog | `data/fleet/filters.json` | `filter_data` fixture |
| Fleet scenario matrix | `data/fleet/filter_matrix.json` | `filter_matrix` fixture and `tests/e2e/test_filter_matrix.py` `MATRIX_PATH` |
| Alerts metric contract | `data/alerts/alerts_contract.yaml` | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` and `tests/unit/test_db_parity_engine.py` |
| Fleet spreadsheet extracts | `data/raw/` (unchanged) | out of scope |

Relationship: `tests/helpers/db_parity_engine.py` receives the alerts path as
an argument. It does not store a report directory.

Validation:

- JSON object keys `districts`, `sub_units`, `categories`, and `sources` stay.
- YAML metric `name`, `scope`, `visual`, `sql_query`, and `category_id` values stay.

## Entity: SharedSecondaryAuth

| Field | Value |
|---|---|
| Module | `pages/secondary_auth.py` |
| Function | `bypass_secondary_auth(page)` |
| Callers | The four page overrides of `_bypass_secondary_auth` |
| Layer 0 | `ReportShell._bypass_secondary_auth` stays a no-op |

Validation: the module is not under `core/` and not under `tests/helpers/`.

## Entity: GenericHelper

Modules that stay in `tests/helpers/`.

| Module | Public surface |
|---|---|
| `db_parity_engine.py` | `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)` |
| `dashboard_fixture.py` | `open_report(page_cls, auth_page, browser_context)`, `bind_dashboard(page_cls)` |

`dashboard_validation.py` is not a `GenericHelper`. After the move it is a fleet
module: `tests/ui/fleet_dashboard/dashboard_validation.py`. Its functions keep
their signatures, including `KPI_TYPES`, `apply_filters`, `db_filter_kwargs`,
and `assert_all_kpis_match_db`.

## Entity: ConstitutionRule

The governance record of this layout.

| Field | Value |
|---|---|
| Document | `.specify/memory/constitution.md` |
| Version | 1.3.0 (from 1.2.0, MINOR) |
| Amended | 2026-10-14 |
| Paths it requires | `pages/<report>/`, `core/components/`, `db/clients/<report>.py`, `data/<report>/` |
| Propagated to | plan, spec, and tasks templates; `README.md`; `docs/COVERAGE_CATALOG.md` |

State of a report page:

```text
tests/ui/<suite>/page.py  →  pages/<report>/page.py
```

State of a report SQL client:

```text
db/client.py (fleet)      →  db/clients/fleet.py
db/clients/alerts.py      →  unchanged
```

State of a catalog file:

```text
data/filters.json                              →  data/fleet/filters.json
data/filter_matrix.json                        →  data/fleet/filter_matrix.json
tests/ui/alerts_analysis_dashboard/alerts_contract.yaml
                                               →  data/alerts/alerts_contract.yaml
```
