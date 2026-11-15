# Quickstart: Fleet DB Sanity and Validation Tests

**Feature**: 039-fleet-db-sanity | **Date**: 2026-10-29

## What this slice adds

A sanity package at `tests/sanity/fleet_dashboard/`. `contract.py` checks
`data/fleet/db_sanity_all.yaml` for summary balances, breakdown sums, category
rates, and the credited-vehicle ledger. `test_db_sanity.py` runs those checks
and compares the open fleet report to the same file. The four rate lines lose
their `[cite: 1]` suffix so the file parses. `core/` and the fleet page stay
as they are.

## Collect

From the repository root:

```text
python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py --collect-only
```

Expect ten tests:

- `test_summary_balances`
- `test_breakdowns_integrity`
- `test_vehicle_category_rates`
- `test_credited_vehicles_ledger`
- `test_ui_summary_kpis_match_golden`
- `test_ui_unit_breakdown_matches_golden`
- `test_ui_pull_source_matches_golden`
- `test_ui_credit_reasons_match_golden`
- `test_ui_category_actuals_match_golden`
- `test_ui_credited_ledger_rows`

## Run the file checks

These four do not open a browser and do not need portal auth:

```text
python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py -v -k "not ui"
```

## Run the report checks

From the repository root, with portal credentials and a saved auth state:

```text
python -m pytest tests/sanity/fleet_dashboard/test_db_sanity.py -v -k ui
```

## Pass

- The golden file loads. Rates are `0.57%`, `16.92%`, `34.24%`, and `10.74%`.
- Unit and pull-source sums equal vehicles in use. Category actuals sum to vehicles received. Credit reasons and ledger rows equal vehicles credited.
- A cleared report's four KPI cards match `summary`.
- Each chart that shows golden labels matches those counts. A chart that shows none of them skips only that test.
- Each credited vehicle number is found on the credited tab with its reason, date, pull source, and unit metadata.
- The edit list does not include `core/`, `pages/fleet_dashboard/main_dashboard_page.py`, `tests/ui/`, `tests/e2e/`, or `db/clients/fleet.py`.

A failure names the section, the key or vehicle, and both the value read and the golden value.
