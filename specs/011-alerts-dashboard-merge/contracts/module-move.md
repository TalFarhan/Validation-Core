# Contract: Folder Merge, Import Stability & Clean Collection

The "interface" this feature exposes is the **test-collection contract** of the surviving Alerts suite and the
**import/path stability** of the moved files. These MUST hold after the merge.

## C1 — Move contract (file relocation)

| # | File | From | To |
|---|------|------|----|
| 1 | `alerts_contract.yaml` | `tests/ui/alerts_dashboard/` | `tests/ui/alerts_analysis_dashboard/` |
| 2 | `test_db_parity.py` | `tests/ui/alerts_dashboard/` | `tests/ui/alerts_analysis_dashboard/` |

Moved bodies are byte-for-byte identical. `test_db_parity.py` resolves its contract via
`Path(__file__).resolve().parent / "alerts_contract.yaml"`, so co-locating both files in the destination keeps
the path valid with no edit.

## C2 — Merge contract (page object)

`tests/ui/alerts_analysis_dashboard/page.py` → `AlertsAnalysisPage` MUST, after merge, provide the
date-range slicer surface previously on `AlertsDashboardPage`:

```python
class AlertsAnalysisPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "ניתוח התרעות"            # unchanged
    DATE_RANGE_ROLE_NAME = "טווח תאריכים"              # merged in
    _SLICER_DEFINITIONS = (                            # merged in
        SlicerDefinition(id="date_range", role_name=DATE_RANGE_ROLE_NAME, kind="dropdown"),
    )

    def __init__(self, page: Page) -> None: ...        # composes Slicer(definitions=_SLICER_DEFINITIONS)
    def _report_ready_locator(self): ...               # unchanged
    def select_date_range(self, value: str) -> None: ...# merged in — delegates to self._slicer.select("date_range", value)
```

- Domain strings stay in this file; `core/` is not modified.
- Inline comments inside functions MUST be English only.

## C3 — Merge contract (conftest fixtures)

`tests/ui/alerts_analysis_dashboard/conftest.py` MUST expose both fixtures:

```python
from tests.helpers.dashboard_fixture import bind_dashboard
from tests.ui.alerts_analysis_dashboard.page import AlertsAnalysisPage
from db.clients.alerts import AlertsDBRunner
import pytest

dashboard = bind_dashboard(AlertsAnalysisPage)         # existing — unchanged

@pytest.fixture(scope="session")
def alerts_db():                                        # merged in
    return AlertsDBRunner()
```

## C4 — Import contract (forbidden after merge)

These MUST NOT appear anywhere in live code (`tests/`, `core/`, `db/`, `pages/`) after the refactor:

```text
from tests.ui.alerts_dashboard... import ...
import tests.ui.alerts_dashboard
AlertsDashboardPage            # the merged-away class name must not be referenced in live code
```

Canonical live references after merge:

| Symbol / path | Canonical form |
|---------------|----------------|
| Page class | `from tests.ui.alerts_analysis_dashboard.page import AlertsAnalysisPage` |
| Parity test | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| Contract | `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` |

## C5 — Documentation contract

`docs/COVERAGE_CATALOG.md` MUST repoint the two Alerts rows and the slicer reference:

| Was | Becomes |
|-----|---------|
| `tests/ui/alerts_dashboard/test_db_parity.py` | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` |
| `tests/ui/alerts_dashboard/alerts_contract.yaml` | `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` |
| `tests/ui/alerts_dashboard/page.py` → `AlertsDashboardPage.select_date_range` | `tests/ui/alerts_analysis_dashboard/page.py` → `AlertsAnalysisPage.select_date_range` |

> `specs/010-db-parity-engine/*` references are historical records of that completed feature and are left
> unchanged.

## C6 — Acceptance gate

- `pytest --collect-only tests/ui/alerts_analysis_dashboard/` collects **both**
  `test_dashboard_updated_within_24_hours` (sanity) and `test_alerts_db_parity_last_30_days` (db_parity) with
  zero collection errors.
- The directory `tests/ui/alerts_dashboard/` no longer exists.
- Structural grep guard: `rg "alerts_dashboard" tests/ core/ db/ pages/` returns **no** matches in live code
  (matches allowed only in `specs/` and `docs/` after the doc update repoints live mappings).
- `pytest tests/ui/fleet_dashboard/` remains 100% green (no fleet/`core/` code was touched).
