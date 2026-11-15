# Quickstart: Generic DB Parity Engine + Alerts Pilot

## Prerequisites

- Python env with project deps installed, plus the new one:

```powershell
pip install -r requirements.txt   # now includes pyyaml>=6.0
```

- `.env` configured for SQL Server (`DB_SERVER`, `DB_DRIVER`) and the new Alerts database name:

```ini
DB_ALERTS_NAME=<alerts_database_name>
```

- A saved portal session (`auth_state.json`) so the Alerts Dashboard opens without manual login
  (run any UI test once with `HEADLESS=false` to create it).

## What gets built

| Layer | File | Role |
|-------|------|------|
| Layer 2 | `core/components/kpi.py` | Generic `KPI` card reader + `normalize_kpi_text` |
| Helper | `tests/helpers/db_parity_engine.py` | `validate_dashboard_generic(...)` |
| DB | `db/clients/alerts.py` | `AlertsDBRunner.scalar(sql, start_date, end_date)` via `text()` |
| Domain | `tests/ui/alerts_dashboard/page.py` | `AlertsDashboardPage` (ReportShell + date-range Slicer) |
| Data | `tests/ui/alerts_dashboard/alerts_contract.yaml` | Two pilot metrics |
| Test | `tests/ui/alerts_dashboard/test_db_parity.py` | `@pytest.mark.db_parity` pilot |

## Run the pilot

```powershell
pytest tests/ui/alerts_dashboard/test_db_parity.py -m db_parity -v
```

Expected: the test navigates to the Alerts Dashboard, selects "שלושים יום אחרונים", computes a 30-day
half-open window in Python, reads both KPI cards, runs each contract query against the Alerts DB, and asserts
UI == DB for both metrics.

## Regression gate (Constitution III — MUST stay green)

```powershell
pytest tests/ui/fleet_dashboard/ -v
```

This feature is additive; the fleet suite must remain 100% green.

## Verification checklist

- [ ] `pytest tests/ui/alerts_dashboard/test_db_parity.py -m db_parity` passes (UI == DB for both metrics).
- [ ] `pytest tests/ui/fleet_dashboard/` is 100% green.
- [ ] `rg -n "אזורי התרעה|AlertsRedWeb|alerts_contract" core/` returns **nothing** (zero domain leakage).
- [ ] All contract SQL runs through `sqlalchemy.text()` with bound `:start_date` / `:end_date` (no f-strings).
- [ ] `docs/COVERAGE_CATALOG.md` lists both Alerts KPIs ↔ SQL ↔ test.
- [ ] `pytest --markers | rg db_parity` shows the registered marker.
- [ ] HTML + CSV run artifacts appear under `result/` with per-metric KPI/DB/assertion log lines.

## Troubleshooting

- **KPI not found**: confirm the `name` in the YAML matches the card's accessible title exactly (after RTL-mark
  stripping). Use Playwright codegen/inspector on the live iframe to read the card's `button` name.
- **Date-range slicer not selecting**: verify the dropdown `role_name` (accessible name) in
  `AlertsDashboardPage`'s `SlicerDefinition`; the option value must match "שלושים יום אחרונים" exactly.
- **DB connection fails**: check `DB_ALERTS_NAME` and that `Trusted_Connection=yes` can reach `DB_SERVER`.
- **Mismatch (UI != DB)**: confirm the window semantics — SQL uses `>= :start_date AND < :end_date`
  (half-open); ensure `end_date = now` and `start_date = now - 30d` align with the slicer's "last 30 days".
