# Quickstart: Unify Alerts Dashboard Folders

Goal: one Alerts suite — `tests/ui/alerts_analysis_dashboard/` — holding both the smoke (freshness) test and
the DB-parity test, with `tests/ui/alerts_dashboard/` deleted.

## What changes

| Layer | File | Action |
|-------|------|--------|
| Domain page | `tests/ui/alerts_analysis_dashboard/page.py` | Merge date-range `Slicer` + `select_date_range()` into `AlertsAnalysisPage` |
| Fixtures | `tests/ui/alerts_analysis_dashboard/conftest.py` | Add `alerts_db` session fixture |
| Data | `tests/ui/alerts_analysis_dashboard/alerts_contract.yaml` | Moved from `alerts_dashboard/` |
| Test | `tests/ui/alerts_analysis_dashboard/test_db_parity.py` | Moved from `alerts_dashboard/` |
| Cleanup | `tests/ui/alerts_dashboard/` | Deleted in full |
| Docs | `docs/COVERAGE_CATALOG.md` | Repoint Alerts paths + page class |

## Verify (primary gate — collection only)

```powershell
pytest --collect-only tests/ui/alerts_analysis_dashboard/
```

Expected: both tests collected, no errors —

```text
tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py::test_dashboard_updated_within_24_hours
tests/ui/alerts_analysis_dashboard/test_db_parity.py::test_alerts_db_parity_last_30_days
```

## Verify (deletion + no stale live references)

```powershell
Test-Path tests/ui/alerts_dashboard        # expect: False
rg "alerts_dashboard" tests core db pages   # expect: no matches
rg "AlertsDashboardPage" tests core db pages # expect: no matches
```

## Verify (regression — no production code touched)

```powershell
pytest tests/ui/fleet_dashboard/            # expect: 100% green
```

## Optional (full parity run — needs live portal + Alerts SQL Server)

```powershell
pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity -v
```

Requires `DB_ALERTS_NAME` set and the date-range slicer `role_name` confirmed against the live control.

## Done when

- [ ] `pytest --collect-only tests/ui/alerts_analysis_dashboard/` collects smoke **and** parity tests cleanly.
- [ ] `tests/ui/alerts_dashboard/` is deleted; no live references to it or `AlertsDashboardPage` remain.
- [ ] `AlertsAnalysisPage` exposes `select_date_range`; `conftest.py` exposes `dashboard` + `alerts_db`.
- [ ] `docs/COVERAGE_CATALOG.md` points at the analysis-folder paths.
- [ ] All inline comments in moved/merged code are English only.
- [ ] `pytest tests/ui/fleet_dashboard/` stays 100% green.
