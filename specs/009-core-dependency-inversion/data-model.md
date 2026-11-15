# Phase 1 Data Model: Module & Class Topology

This feature has no runtime data entities. The "model" here is the **module/class topology** before and after
the move — the thing the refactor actually changes.

## Entities (modules & the symbols they own)

### `core.base_page` (NEW — moved from `pages.base_page`)

- **Owns**: class `BasePage`
- **Public surface (unchanged)**: `__init__(page)`, `retry_with_backoff(...)`, `wait_for_visible(...)`,
  `wait_for_kpi_update(...)`, `assert_tab_active(...)`, `assert_tab_inactive(...)`, class attribute
  `ACTIVE_TAB_CLASS`.
- **Internal dependency change**: `from pages.errors import LoadTimeoutError` → `from core.errors import LoadTimeoutError`
- **Rule**: body unchanged; comments English-only.

### `core.errors` (NEW — generic subset of `pages.errors`)

- **Owns**: class `LoadTimeoutError(AssertionError)`
- **Public surface (unchanged)**: `__init__(description, *, steps_ms, cause=None)`; attributes `description`,
  `steps_ms`, `cause`.
- **Does NOT own**: `ExpandHierarchyUnavailable` (relocated — see below).

### `pages.fleet_dashboard.main_dashboard_page` (MODIFIED)

- **Gains**: definition of `ExpandHierarchyUnavailable(AssertionError)` (moved verbatim).
  - Public surface (unchanged): `__init__(chart_key, reason)`; attributes `chart_key`, `reason`.
- **Import change**: `from pages.errors import ExpandHierarchyUnavailable, LoadTimeoutError`
  → `from core.errors import LoadTimeoutError` (and `ExpandHierarchyUnavailable` becomes a local definition).

### `core.portal.page` (`ReportShell`) (MODIFIED — imports only)

- `from pages.base_page import BasePage` → `from core.base_page import BasePage`
- `from pages.errors import LoadTimeoutError` → `from core.errors import LoadTimeoutError`

### Removed modules

- `pages/base_page.py` — removed (content lives in `core/base_page.py`).
- `pages/errors.py` — removed (generic part → `core/errors.py`; domain part → fleet page).

## Relationships (inheritance / dependency edges)

```text
BEFORE:  core.portal.page.ReportShell ──imports──▶ pages.base_page.BasePage
         core.portal.page.ReportShell ──imports──▶ pages.errors.LoadTimeoutError
         pages.base_page.BasePage     ──imports──▶ pages.errors.LoadTimeoutError
         (reverse edge: core ──▶ pages)   ❌ violates layering

AFTER:   core.portal.page.ReportShell ──imports──▶ core.base_page.BasePage
         core.portal.page.ReportShell ──imports──▶ core.errors.LoadTimeoutError
         core.base_page.BasePage      ──imports──▶ core.errors.LoadTimeoutError
         pages.fleet_dashboard.*      ──imports──▶ core.errors.LoadTimeoutError
         (no edge: core ──▶ pages)        ✅ layering restored
```

Inheritance chain is unchanged: `BasePage` → `ReportShell` → `MainDashboardPage`.

## Validation rules / invariants

- **INV-1**: `rg "from pages\.(base_page|errors)" core/` returns zero matches after the move.
- **INV-2**: `core/` contains no symbol whose text includes fleet terms (e.g. `הסתעפות`); the only such symbol
  (`ExpandHierarchyUnavailable`) resides under `pages/fleet_dashboard/`.
- **INV-3**: Public method/attribute signatures of `BasePage`, `LoadTimeoutError`, and
  `ExpandHierarchyUnavailable` are byte-for-byte equivalent to before (no API drift).
- **INV-4**: No change to `tests/ui/fleet_dashboard/` source; the suite passes at 100%.
