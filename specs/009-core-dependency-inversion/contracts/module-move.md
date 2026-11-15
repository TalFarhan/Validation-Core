# Contract: Module Relocation & Public-API Stability

The "interface" this feature exposes is the **import contract** between layers and the **public API** of the
moved symbols. These contracts MUST hold after the refactor.

## C1 — Import contract (new canonical paths)

| Symbol | Canonical import AFTER refactor |
|--------|---------------------------------|
| `BasePage` | `from core.base_page import BasePage` |
| `LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| `ExpandHierarchyUnavailable` | from the fleet domain (`pages/fleet_dashboard/main_dashboard_page.py`) |

Forbidden after refactor (MUST NOT appear in `core/`, `pages/`, `tests/` live code):

```text
from pages.base_page import ...
from pages.errors import ...
import pages.base_page
import pages.errors
```

## C2 — Public API stability (no behavioral drift)

The following signatures MUST remain identical (byte-for-byte equivalent bodies; only import lines and file
location change):

```python
class BasePage:
    ACTIVE_TAB_CLASS: re.Pattern
    def __init__(self, page: Page) -> None: ...
    def retry_with_backoff(self, attempt, *, description, timeout_ms=None, recover=None): ...
    def wait_for_visible(self, locator, *, timeout_ms=None, recover=None, description=None) -> None: ...
    def wait_for_kpi_update(self, kpi_locator, previous_value, *, required=True, timeout_ms=None) -> None: ...
    def assert_tab_active(self, tab_locator) -> None: ...
    def assert_tab_inactive(self, tab_locator) -> None: ...

class LoadTimeoutError(AssertionError):
    def __init__(self, description: str, *, steps_ms: list[int], cause: BaseException | None = None): ...

class ExpandHierarchyUnavailable(AssertionError):
    def __init__(self, chart_key: str, reason: str): ...
```

## C3 — Each affected import, enumerated

| # | File | Before | After |
|---|------|--------|-------|
| 1 | `core/portal/page.py` | `from pages.base_page import BasePage` | `from core.base_page import BasePage` |
| 2 | `core/portal/page.py` | `from pages.errors import LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| 3 | `core/base_page.py` (moved) | `from pages.errors import LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| 4 | `pages/fleet_dashboard/main_dashboard_page.py` | `from pages.errors import ExpandHierarchyUnavailable, LoadTimeoutError` | `from core.errors import LoadTimeoutError` + local `ExpandHierarchyUnavailable` definition |
| 5 | `tests/helpers/dashboard_validation.py` | `from pages.errors import LoadTimeoutError` | `from core.errors import LoadTimeoutError` |
| 6 | `tests/e2e/test_chart_drilldown.py` | `from pages.errors import ExpandHierarchyUnavailable` | `from pages.fleet_dashboard.main_dashboard_page import ExpandHierarchyUnavailable` |

## C4 — Alternative placement for `ExpandHierarchyUnavailable` (documented, not chosen)

If a future second fleet module needs the error, create `pages/fleet_dashboard/errors.py` owning
`ExpandHierarchyUnavailable`, and update rows #4 and #6 to import from there. This feature chooses the
in-page definition to minimize surface area; the e2e import path (row #6) is the only external coupling and is
trivial to repoint later.

## C5 — Acceptance gate

- `pytest tests/ui/fleet_dashboard/` → 100% pass.
- Collection of `tests/e2e/test_chart_drilldown.py` succeeds (import resolves).
- Structural grep guards (INV-1, INV-2) return the expected zero/one matches.
