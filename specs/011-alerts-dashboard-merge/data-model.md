# Phase 1 Data Model: Unify Alerts Dashboard Folders

This feature has **no runtime data entities** (it is a structural refactor). The "model" here is the file
inventory before/after and the merged public surface of the surviving page object and conftest.

## Entity 1 — File inventory (before → after)

| File | Before (location) | After (location) | Action |
|------|-------------------|------------------|--------|
| `alerts_contract.yaml` | `tests/ui/alerts_dashboard/` | `tests/ui/alerts_analysis_dashboard/` | Move (verbatim) |
| `test_db_parity.py` | `tests/ui/alerts_dashboard/` | `tests/ui/alerts_analysis_dashboard/` | Move (verify imports) |
| `page.py` | both folders | `tests/ui/alerts_analysis_dashboard/` only | Merge slicer into analysis page; delete other |
| `conftest.py` | both folders | `tests/ui/alerts_analysis_dashboard/` only | Merge `alerts_db` into analysis conftest; delete other |
| `__init__.py` | both folders | `tests/ui/alerts_analysis_dashboard/` only | Keep analysis marker; delete other |
| `test_dashboard_smoke.py` | `tests/ui/alerts_analysis_dashboard/` | unchanged | None |

Post-state: `tests/ui/alerts_dashboard/` does not exist.

## Entity 2 — Merged `AlertsAnalysisPage` surface

After the merge, `tests/ui/alerts_analysis_dashboard/page.py` exposes:

| Member | Source | Used by |
|--------|--------|---------|
| `DASHBOARD_SEARCH_TERM = "ניתוח התרעות"` | existing (identical in both pages) | portal navigation |
| `_report_ready_locator()` | existing | `ReportShell` navigation |
| `DATE_RANGE_ROLE_NAME` + `_SLICER_DEFINITIONS` | merged from `AlertsDashboardPage` | slicer composition |
| `self._slicer` (`Slicer(...)`) | merged from `AlertsDashboardPage` | `select_date_range` |
| `select_date_range(value: str)` | merged from `AlertsDashboardPage` | `test_db_parity.py` |
| `_report_frame()` (inherited) | `ReportShell` | parity engine `KPI(...)` reads |
| `verify_freshness()` (inherited) | `ReportShell` | `test_dashboard_smoke.py` |

Invariant: the merged page keeps a single Hebrew domain string set (search term, slicer role name) in the
domain layer; nothing leaks into `core/`.

## Entity 3 — Merged `conftest.py` fixtures

| Fixture | Scope | Provides |
|---------|-------|----------|
| `dashboard` | function (via `bind_dashboard`) | `AlertsAnalysisPage` on the shared tab |
| `alerts_db` | session | `AlertsDBRunner()` read-only runner for parity |

## Entity 4 — Test collection map (post-merge)

```text
tests/ui/alerts_analysis_dashboard/
├── test_dashboard_smoke.py::test_dashboard_updated_within_24_hours   [marker: sanity]
└── test_db_parity.py::test_alerts_db_parity_last_30_days             [marker: db_parity]
```

Both must be collected by `pytest --collect-only tests/ui/alerts_analysis_dashboard/` with no import or
fixture-resolution errors.
