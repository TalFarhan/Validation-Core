# Contract: Module Layout

Normative for implementation. Spec FR-001 through FR-015 and research R1–R7
are the source. Behavior, SQL text, JSON, and YAML contents do not change.
Imports and paths do.

## 1. Report pages

Move the class module. Delete the old `page.py`. Do not add `__init__.py`
(the `pages/` tree is already a namespace package).

| From | Class | To | Suite conftest import |
|---|---|---|---|
| `tests/ui/alerts_analysis_dashboard/page.py` | `AlertsAnalysisPage` | `pages/alerts_analysis/page.py` | `from pages.alerts_analysis.page import AlertsAnalysisPage` |
| `tests/ui/authorities_status_dashboard/page.py` | `AuthoritiesStatusPage` | `pages/authorities_status/page.py` | `from pages.authorities_status.page import AuthoritiesStatusPage` |
| `tests/ui/credit_consumption_dashboard/page.py` | `CreditConsumptionPage` | `pages/credit_consumption/page.py` | `from pages.credit_consumption.page import CreditConsumptionPage` |
| `tests/ui/hosen_status_dashboard/page.py` | `HosenStatusPage` | `pages/hosen_status/page.py` | `from pages.hosen_status.page import HosenStatusPage` |
| `tests/ui/life_saving_guidelines_dashboard/page.py` | `LifeSavingGuidelinesPage` | `pages/life_saving_guidelines/page.py` | `from pages.life_saving_guidelines.page import LifeSavingGuidelinesPage` |
| `tests/ui/marsal_dashboard/page.py` | `MarsalPage` | `pages/marsal/page.py` | `from pages.marsal.page import MarsalPage` |
| `tests/ui/mass_events_dashboard/page.py` | `MassEventsPage` | `pages/mass_events/page.py` | `from pages.mass_events.page import MassEventsPage` |
| `tests/ui/maya_system_dashboard/page.py` | `MayaSystemPage` | `pages/maya_system/page.py` | `from pages.maya_system.page import MayaSystemPage` |
| `tests/ui/power_outages_dashboard/page.py` | `PowerOutagesPage` | `pages/power_outages/page.py` | `from pages.power_outages.page import PowerOutagesPage` |
| `tests/ui/public_inquiries_dashboard/page.py` | `PublicInquiriesPage` | `pages/public_inquiries/page.py` | `from pages.public_inquiries.page import PublicInquiriesPage` |
| `tests/ui/public_shelters_dashboard/page.py` | `PublicSheltersPage` | `pages/public_shelters/page.py` | `from pages.public_shelters.page import PublicSheltersPage` |
| `tests/ui/rescue_capabilities_dashboard/page.py` | `RescueCapabilitiesPage` | `pages/rescue_capabilities/page.py` | `from pages.rescue_capabilities.page import RescueCapabilitiesPage` |

Each suite conftest keeps `from tests.helpers.dashboard_fixture import bind_dashboard`
and `dashboard = bind_dashboard(<PageClass>)`.

Alerts also keeps:

```python
from db.clients.alerts import AlertsDBRunner
```

and the `alerts_db` fixture. That fixture stays in the alerts conftest.

Unchanged page module:

- `pages/fleet_dashboard/main_dashboard_page.py` (`MainDashboardPage`)

Inside the four gated pages, replace:

```python
from tests.helpers.secondary_auth import bypass_secondary_auth
```

with:

```python
from pages.secondary_auth import bypass_secondary_auth
```

Those pages are Mass Events, Life-Saving Guidelines, Maya System, and Public Shelters.

## 2. Root conftest

Remove these imports and fixtures from `conftest.py`:

- `from db.client import DatabaseClient`
- `from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage`
- `DATA_DIR`
- `db_client`
- `filter_data`
- `filter_matrix`
- `zero_count_filters`
- `dashboard`

Delete `from tests.helpers.dashboard_fixture import open_report`. The root
`dashboard` fixture is the only caller. `open_report` stays available to the
fleet and e2e conftests.

Keep `save_auth_state`, `browser_context`, `session_page`, `auth_page`,
`run_report_book`, `test_run_report`, `video_run_dir`, screenshot, trace, and
the pytest HTML/report hooks.

## 3. Fleet fixtures

Define this set in **both** `tests/ui/fleet_dashboard/conftest.py` and
`tests/e2e/conftest.py`.

Fleet conftest path base (`tests/ui/fleet_dashboard/conftest.py`):

```python
FLEET_DATA = Path(__file__).resolve().parents[3] / "data" / "fleet"
```

E2E conftest path base (`tests/e2e/conftest.py`):

```python
FLEET_DATA = Path(__file__).resolve().parents[2] / "data" / "fleet"
```

Shared shape:

```python
from db.clients.fleet import DatabaseClient
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage
from tests.helpers.dashboard_fixture import open_report

@pytest.fixture
def dashboard(auth_page, browser_context):
    return open_report(MainDashboardPage, auth_page, browser_context)

@pytest.fixture(scope="session")
def db_client():
    return DatabaseClient()

@pytest.fixture(scope="session")
def filter_data():
    with open(FLEET_DATA / "filters.json", encoding="utf-8") as file:
        return json.load(file)

@pytest.fixture(scope="session")
def filter_matrix():
    with open(FLEET_DATA / "filter_matrix.json", encoding="utf-8") as file:
        return json.load(file)

@pytest.fixture(scope="session")
def zero_count_filters(db_client, filter_data):
    combo = db_client.find_zero_count_filters(filter_data)
    if combo is None:
        pytest.skip("No zero-count filter combination found in test data")
    return combo
```

Do not register this set from root `conftest.py` or from `pytest_plugins`.

## 4. SQL clients

- Create `db/clients/fleet.py` by moving `DatabaseClient`, `KpiType`, and their
  helpers from `db/client.py`. Imports stay `config.settings`, `db.connection`,
  and `reports.test_run_report`.
- Delete `db/client.py`.
- `db/__init__.py` MUST NOT import `DatabaseClient` or `AlertsDBRunner`.
  Replace the "QA Fleet validation" package docstring with a generic
  read-only warehouse package line.
- Do not edit `db/connection.py` or `db/clients/alerts.py`.

`dashboard_validation.py`, after it moves, imports:

```python
from db.clients.fleet import DatabaseClient, KpiType
```

## 5. Helpers

| Module | Action |
|---|---|
| `tests/helpers/db_parity_engine.py` | Stay. Do not change `validate_dashboard_generic`. |
| `tests/helpers/dashboard_fixture.py` | Stay. Keep the lazy `from conftest import save_auth_state` inside `open_report`. |
| `tests/helpers/dashboard_validation.py` | Move to `tests/ui/fleet_dashboard/dashboard_validation.py`. |
| `tests/helpers/secondary_auth.py` | Move to `pages/secondary_auth.py`. Update the docstring path. Do not change `bypass_secondary_auth`. |

Update `from tests.helpers.dashboard_validation import ...` in:

- `tests/e2e/test_chart_drilldown.py`
- `tests/e2e/test_chart_tooltips.py`
- `tests/e2e/test_chart_validation.py`
- `tests/e2e/test_edge_cases.py`
- `tests/e2e/test_filter_matrix.py`
- `tests/e2e/test_kpi_validation.py`
- `tests/e2e/test_table_validation.py`
- `tests/ui/fleet_dashboard/test_dashboard_smoke.py`

New import target: `tests.ui.fleet_dashboard.dashboard_validation`.

`tests/e2e/test_chart_drilldown.py` keeps
`from pages.fleet_dashboard.main_dashboard_page import ExpandHierarchyUnavailable`.

## 6. Data files

| From | To |
|---|---|
| `data/filters.json` | `data/fleet/filters.json` |
| `data/filter_matrix.json` | `data/fleet/filter_matrix.json` |
| `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` | `data/alerts/alerts_contract.yaml` |

`data/raw/` stays.

`tests/e2e/test_filter_matrix.py`:

```python
MATRIX_PATH = Path(__file__).resolve().parents[2] / "data" / "fleet" / "filter_matrix.json"
```

`tests/ui/alerts_analysis_dashboard/test_db_parity.py`:

```python
CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "alerts" / "alerts_contract.yaml"
)
```

(`parents[0]` is the suite directory, `[1]` is `ui`, `[2]` is `tests`, `[3]` is the repo root.)

`tests/unit/test_db_parity_engine.py` `CONTRACT` becomes:

```python
CONTRACT = (
    Path(__file__).resolve().parents[2] / "data" / "alerts" / "alerts_contract.yaml"
)
```

The test still passes `CONTRACT_PATH` or `CONTRACT` into `validate_dashboard_generic`.
It does not skip on a missing database.

## 7. Files this feature does not edit

- `core/portal/page.py`
- `core/components/slicer.py`, `kpi.py`, `chart.py`, `visual.py`, `__init__.py`
- `core/base_page.py`, `core/errors.py`
- `pages/fleet_dashboard/main_dashboard_page.py` (no method moves)
- `db/connection.py`, `db/clients/alerts.py`
- `tests/helpers/db_parity_engine.py` (path arguments stay caller-owned)
- `specs/001-*` through `specs/017-*`

## 8. Structural checks

These are the acceptance checks for the layout. The quickstart runs them.

- No file matches `tests/ui/**/page.py`.
- Root `conftest.py` does not mention `MainDashboardPage`, `DatabaseClient`, `db.client`, or `db.clients.fleet`.
- Importing `tests.ui.alerts_analysis_dashboard.conftest` does not load `pages.fleet_dashboard.main_dashboard_page` or `db.clients.fleet`.
- `python -m pytest tests/unit/test_db_parity_engine.py tests/ui/alerts_analysis_dashboard tests/ui/fleet_dashboard tests/e2e --collect-only -q` succeeds.
- `pytest tests/ui/fleet_dashboard/` is 100% green when the portal is available (Constitution III).
