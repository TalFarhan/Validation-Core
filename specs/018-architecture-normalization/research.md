# Phase 0 Research: Architecture Normalization

All items below were resolved against the current tree (features 001–017) and
constitution 1.2.0. No **NEEDS CLARIFICATION** remains.

## R1 — Page package names

- **Decision**: Move each `tests/ui/<suite>/page.py` to `pages/<report>/page.py`,
  dropping the `_dashboard` suffix on the page package only. Keep the test
  directory name (`tests/ui/alerts_analysis_dashboard/`, and the same pattern
  for the other eleven suites). Keep class names. Leave
  `pages/fleet_dashboard/main_dashboard_page.py` where it is.
- **Rationale**: The user named `pages/alerts_analysis/page.py` and
  `pages/power_outages`, `pages/maya_system`, and the rest. Test node ids stay
  stable if the suite folders do not move. The fleet page is already under
  `pages/` and Story 6 names that file explicitly. Credit Consumption's popup
  dismissal is report behavior, so the whole module moves with
  `CreditConsumptionPage`. It is not split into `core/`.
- **Alternatives considered**: Rename test directories to match the page
  packages. Rejected. That rewrites every pytest path and every historical
  spec citation for no architectural gain. Renaming the fleet module to
  `pages/fleet/page.py` was rejected for the same reason: it is already legal.

## R2 — Where fleet fixtures are registered

- **Decision**: Delete `dashboard`, `db_client`, `filter_data`, `filter_matrix`,
  and `zero_count_filters` from root `conftest.py`, and define those five
  fixtures in both `tests/ui/fleet_dashboard/conftest.py` and
  `tests/e2e/conftest.py`. Keep browser, session, `auth_page`, video, trace,
  screenshot, and run-report fixtures on the root. Do not put the fleet
  fixtures in `tests/helpers/`.
- **Rationale**: Pytest fixture visibility follows directory conftest files.
  `tests/ui/fleet_dashboard/` and `tests/e2e/` are siblings, so one conftest
  cannot serve the other. Root registration is what makes alerts collection
  import `MainDashboardPage` (`conftest.py` imports it at module level).
  Call sites are: fleet filter and smoke tests (`dashboard`, `filter_data`);
  every file under `tests/e2e/` (`dashboard`, `db_client`, `filter_data`,
  `zero_count_filters`). `filter_matrix` has no test parameter today;
  `test_filter_matrix.py` opens the JSON itself. The fixture still moves so
  the root module does not own fleet files.
- **Alternatives considered**: `pytest_plugins = ["tests.ui.fleet_dashboard.conftest"]`
  from the e2e conftest. Rejected. A full-suite run would load that module both
  as a directory conftest and as a plugin. A shared factory in `tests/helpers/`
  was rejected because the user asked for fleet fixtures in the two conftest
  files and for `tests/helpers/` to stay generic. The duplicated bodies are
  the five short fixtures in `contracts/module-layout.md`.

## R3 — Fleet SQL module and the old `db/client.py`

- **Decision**: Move `DatabaseClient` and `KpiType` verbatim into
  `db/clients/fleet.py`. Delete `db/client.py`. Stop exporting a client from
  `db/__init__.py`. Leave `db/connection.py` as `build_connection_string` and
  `create_db_engine` only. Leave `AlertsDBRunner` and its SQL constants in
  `db/clients/alerts.py` untouched.
- **Rationale**: Alerts already follows `db/clients/<report>.py` and passes
  `database=settings.DB_ALERTS_NAME`. The fleet client uses the default
  engine (`settings.DB_NAME`) and vehicle, district, subunit, category, and
  source predicates. Keeping the class name `DatabaseClient` preserves
  Constitution III: e2e and `dashboard_validation.py` call those methods by
  name. Importers today are root `conftest.py` (dropped in R2),
  `tests/helpers/dashboard_validation.py` (moved in R4), and `db/__init__.py`.
  A re-export shim would leave `import db.client` as a fleet back door.
- **Alternatives considered**: Rename the class to `FleetDBRunner` for symmetry
  with `AlertsDBRunner`. Rejected. Every e2e signature would change without a
  behavior change. Keeping `db/client.py` as a one-line re-export was rejected
  because the split is the point of the feature.

## R4 — Where `dashboard_validation.py` goes

- **Decision**: Move it to `tests/ui/fleet_dashboard/dashboard_validation.py`.
  Update imports in `tests/e2e/test_chart_drilldown.py`,
  `test_chart_tooltips.py`, `test_chart_validation.py`, `test_edge_cases.py`,
  `test_filter_matrix.py`, `test_kpi_validation.py`, `test_table_validation.py`,
  and `tests/ui/fleet_dashboard/test_dashboard_smoke.py` (`KPI_TYPES`).
  `tests/e2e/test_data_invariants.py` uses the `db_client` fixture only and
  has no import to change.
- **Rationale**: The module imports `MainDashboardPage` and `DatabaseClient`.
  It is fleet validation. Fleet smoke needs `KPI_TYPES`. E2E tests are fleet
  UI-versus-warehouse tests, so importing the helper from the fleet package
  matches the dependency. `tests/helpers/` then contains only
  `db_parity_engine.py` and `dashboard_fixture.py`.
- **Alternatives considered**: `tests/e2e/dashboard_validation.py`. Rejected.
  Fleet smoke would import from the e2e tree. Splitting `KPI_TYPES` from the
  rest was rejected. The module moves as a whole; signatures stay.

## R5 — ArcGIS login module destination

- **Decision**: Move `tests/helpers/secondary_auth.py` to
  `pages/secondary_auth.py`. Keep `bypass_secondary_auth`. The four pages
  (`MassEventsPage`, `LifeSavingGuidelinesPage`, `MayaSystemPage`,
  `PublicSheltersPage`) import it from `pages.secondary_auth` after they move.
  Do not move the flow into `core/portal`.
- **Rationale**: The module's own docstring, and feature 007, keep ArcGIS
  dialog text outside Layer 0. Principle I's shared portal list is login/SSO,
  catalog search, iframe wait, visual-load timeout, and last-refresh.
  `ReportShell._bypass_secondary_auth` stays a no-op hook. Principle II forbids
  putting that organizational flow in `core/`. `pages/secondary_auth.py` is
  shared page behavior used by more than one report, which is what the user
  asked for, and it is not a test helper.
- **Alternatives considered**: `core/portal/secondary_auth.py`. Rejected.
  Hebrew ArcGIS strings and the account-type step would enter Layer 0.
  Leaving the file in `tests/helpers/` was rejected by the user request.

## R6 — Data paths and the parity engine

- **Decision**: Move `data/filters.json` and `data/filter_matrix.json` to
  `data/fleet/` with bytes unchanged. Move
  `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` to
  `data/alerts/alerts_contract.yaml` with bytes unchanged. Point
  `test_db_parity.py`, `tests/unit/test_db_parity_engine.py` (`CONTRACT`),
  and `tests/e2e/test_filter_matrix.py` (`MATRIX_PATH`) at the new files.
  Leave `validate_dashboard_generic(yaml_path, page, db_client, start_date, end_date)`
  unchanged. Leave `data/raw/` in place.
- **Rationale**: The engine already takes a path. It must not learn report
  names. JSON shape (`districts`, `sub_units`, `categories`, `sources`) and
  the YAML metric list are domain data, not code. `data/raw/` holds fleet
  spreadsheet extracts the user did not ask to relocate.
- **Alternatives considered**: Teaching the engine a report key that selects
  a file. Rejected. That puts catalog layout inside the generic helper.
  Rewriting specs 002, 010, 011, 016, and 017 to the new paths was rejected.
  Those specs describe the layout when they were written. `README.md` and
  `docs/COVERAGE_CATALOG.md` are living docs and do change (R8).

## R7 — What stays on the fleet page and in Layer 2

- **Decision**: Do not edit `core/components/` (`slicer.py`, `kpi.py`,
  `chart.py`, `visual.py`). Do not move `get_table_row_count`,
  `search_vehicle`, tooltip helpers, `expand_chart_hierarchy`,
  `drill_up_chart`, `get_chart_segment_labels`, or
  `expand_via_tooltip_drilldown` off `MainDashboardPage`.
- **Rationale**: Those methods encode fleet charts and the vehicle table.
  Generic readers already exist from features 002 and 012–015. This feature
  draws the boundary; it does not extract more UI. Constitution VII today
  says charts stay on the domain page until a second report needs them. The
  generic readers are already shared. The amendment in R8 records that split
  and still forbids moving fleet tables, tooltips, and drilldowns into `core/`.
- **Alternatives considered**: Collapsing `KPI` and `Chart` back onto the
  fleet page to match constitution 1.2.0 wording literally. Rejected. That
  undoes features 012–015 and is the opposite of the user's step 6.

## R8 — Constitution version and which docs move with it

- **Decision**: Amend `.specify/memory/constitution.md` from 1.2.0 to 1.3.0
  (MINOR: expand principles I, II, V, and VII and the architecture
  constraints). In the same change, update the layer wording in
  `.specify/templates/plan-template.md`, `.specify/templates/spec-template.md`,
  and `.specify/templates/tasks-template.md`, plus the layer table in
  `README.md` and the path strings in `docs/COVERAGE_CATALOG.md`. Do not edit
  `specs/001` through `specs/017`. Do not edit the blank
  `.specify/templates/constitution-template.md` (it has no Validation Core
  principles to sync).
- **Rationale**: Governance requires a version bump and template propagation
  in the same change as a constitution edit. 1.3.0 is MINOR because the
  amendment adds path rules and corrects VII so it matches
  `core/components/{kpi,chart,visual}.py`. It does not remove a principle or
  break the smoke-test contract. Living docs that cite `data/filters.json`,
  `tests/helpers/dashboard_validation.py`, and the alerts contract path would
  be wrong the moment the files move.
- **Alternatives considered**: PATCH, treating the edit as wording only.
  Rejected. New mandatory paths (`pages/<report>/`, `db/clients/`,
  `data/<report>/`) are a material expansion. MAJOR was rejected because
  Layer 0 and the fleet smoke contract stay.

## R9 — Root conftest import cycle

- **Decision**: `tests/helpers/dashboard_fixture.py` keeps its lazy
  `from conftest import save_auth_state` inside `open_report`. `save_auth_state`
  stays on the root conftest. After R2, importing the root conftest no longer
  imports a page or a SQL client, so the lazy import stays safe.
- **Rationale**: `save_auth_state` is session persistence, not fleet behavior.
  Moving it would touch every suite's navigation helper for no layout gain.
- **Alternatives considered**: Moving `save_auth_state` into `browser_session`.
  Rejected. Out of scope for a folder alignment, and the current lazy import
  already avoids a cycle (`conftest` imports `open_report` at module level;
  `open_report` imports `conftest` only when called).
