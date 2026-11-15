# Quickstart: Architecture Normalization

Structural checks. No browser is required for steps 1–4. Step 5 is the
Constitution III gate and needs the portal session.

Run from the repository root.

## 1. Pages are not inside test packages

```powershell
Get-ChildItem -Recurse tests/ui -Filter page.py
```

Expected: no files.

```powershell
python -c "from pages.alerts_analysis.page import AlertsAnalysisPage; from pages.power_outages.page import PowerOutagesPage; from pages.maya_system.page import MayaSystemPage; from pages.secondary_auth import bypass_secondary_auth; print(AlertsAnalysisPage.__name__, PowerOutagesPage.__name__, bypass_secondary_auth.__name__)"
```

Expected: `AlertsAnalysisPage PowerOutagesPage bypass_secondary_auth`

## 2. Root conftest does not know the fleet page

```powershell
rg -n "MainDashboardPage|DatabaseClient|db\.client|db\.clients\.fleet|filters\.json" conftest.py
```

Expected: no matches.

```powershell
python -c "import tests.ui.alerts_analysis_dashboard.conftest as alerts; import sys; assert 'pages.fleet_dashboard.main_dashboard_page' not in sys.modules; assert 'db.clients.fleet' not in sys.modules; print('alerts collection is fleet-free')"
```

Expected: `alerts collection is fleet-free`

## 3. Clients and catalogs

```powershell
python -c "from db.clients.fleet import DatabaseClient, KpiType; from db.connection import create_db_engine; import db; assert not hasattr(db, 'DatabaseClient'); print('fleet client', DatabaseClient.__name__)"
```

Expected: `fleet client DatabaseClient`

Confirm these paths exist and the old ones do not:

- `db/clients/fleet.py` exists
- `db/client.py` does not exist
- `data/fleet/filters.json` and `data/fleet/filter_matrix.json` exist
- `data/alerts/alerts_contract.yaml` exists
- `data/filters.json`, `data/filter_matrix.json`, and `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` do not exist
- `tests/helpers/dashboard_validation.py` and `tests/helpers/secondary_auth.py` do not exist
- `tests/helpers/db_parity_engine.py` and `tests/helpers/dashboard_fixture.py` exist
- `tests/ui/fleet_dashboard/dashboard_validation.py` and `pages/secondary_auth.py` exist

## 4. Collection and unit parity

```powershell
python -m pytest tests/unit/test_db_parity_engine.py tests/ui/alerts_analysis_dashboard tests/ui/fleet_dashboard tests/e2e --collect-only -q
```

Expected: exit code 0. Alerts tests still collect `dashboard` from the alerts
conftest. Fleet and e2e tests still collect `dashboard`, `db_client`, and
`filter_data`.

```powershell
python -m pytest tests/unit/test_db_parity_engine.py -q --tb=line
```

Expected: pass. These tests load `data/alerts/alerts_contract.yaml` and do not
open a browser.

## 5. Fleet smoke gate

```powershell
python -m pytest tests/ui/fleet_dashboard/ -q --tb=short
```

Expected: 100% green. This is required before the feature is called done
(Constitution III). It needs the saved portal session and, for any test that
hits the warehouse, the read-only SQL Server connection.

## 6. Constitution

Open `.specify/memory/constitution.md` and confirm:

- Version is **1.3.0**
- Last amended **2026-10-14**
- Architecture constraints name `pages/<report>/`, `core/components/`, `db/clients/<report>.py`, and `data/<report>/`
