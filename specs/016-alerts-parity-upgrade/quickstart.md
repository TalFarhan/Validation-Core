# Quickstart: Alerts DB Parity Upgrade

**Feature**: 016-alerts-parity-upgrade | **Date**: 2026-10-13

Confirm the engine dispatch without a portal, then run the Alerts parity test and the fleet
regression gate. No new dependency.

## Prerequisites

- Repo checked out; Python 3.11+ with `pip install -r requirements.txt` (PyYAML is already required).
- `.specify/feature.json` points at `specs/016-alerts-parity-upgrade`.
- For the live test only: `.env` with `DB_ALERTS_NAME`, and a saved portal session (`auth_state.json`).

## 1. Engine rules (no browser, no database)

```powershell
python -m pytest tests/unit/test_db_parity_engine.py -v
```

Expected:

- A metric `scope` is the string passed to `KPI.number`, `KPI.scale`, or `Chart.read`. A blank
  scope is `None`.
- A gauge whose value matches and whose maximum does not match fails, and the error names both
  checks when both fail. UI `0` equals DB `0`.
- Chart rows match by label. A SQL NULL matches a missing cell. An empty visual matches no rows.
- `category_id: 1` is recorded by the fake runner as `"1"`. A metric without `category_id` does
  not send the kwarg.
- An unknown `visual` (not `kpi`, `gauge`, `chart`, or `map`) fails at load.
- Map presence: a scripted `0` is `value`; no number and no marks is `empty`; a cell of
  `placeholder` fails the presence check and the error shows that raw value.
- A `compare: text` metric calls `read_text`, not `number`, and fails when the cell is
  `placeholder` and the UI text is a different string.

## 2. Domain leakage check

This feature does not edit `core/`. After implementation:

```powershell
git diff -- core/components core/portal
```

Expected: empty diff for this feature's commits. Category ids `1`, `2`, and `10`, Hebrew titles,
and SQL stay under `tests/ui/alerts_analysis_dashboard/` and the bind parameter on
`db/clients/alerts.py`.

Confirm the contract names dropped the date phrase (the slicer option remains in the test):

```powershell
rg "שלושים יום" tests/ui/alerts_analysis_dashboard
```

Expected: matches in `test_db_parity.py` (and `page.py` only if a comment quotes the option).
No matches in `alerts_contract.yaml` metric `name` values.

## 3. Live Alerts parity

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity -v
```

Expected when the portal and the Alerts database are both available: the test selects
`שלושים יום אחרונים`, binds a half-open 30-day window, and asserts UI equals DB for each
category id on its own (`CategoryID = :category_id`). The grouped predicate
`CategoryID IN ('1', '2', '10')` is gone from the contract. Gauge metrics check value and
maximum. The settlements chart checks category rows. The map checks presence. The policy metric
checks status text.

Expected when the Alerts database is missing: the test fails with the connection error. That
failure is the reminder. Do not add a skip, and do not catch the error to force a pass. The three
new metrics use the stub constants in `db/clients/alerts.py`. Against a reachable server those
stubs still fail parity, because the selected value is the literal `placeholder`.

Confirm the three anchors are present and the slicer phrase is not in any `name`:

```powershell
rg "עשרת היישובים עם כמות ההתרעות הגבוהה ביותר|מפת התרעות ביישובים|סיכון לפי מדיניות התגוננות ברגע" tests/ui/alerts_analysis_dashboard/alerts_contract.yaml
```

## 4. Regression gate (Constitution III)

```powershell
python -m pytest tests/ui/fleet_dashboard/
```

Expected: 100% pass. Layer 2 and the fleet page are unchanged. This needs the portal when those
tests open the fleet report.

## 5. Coverage catalog

`docs/COVERAGE_CATALOG.md` section for the Alerts pilot lists each measure with its visual kind,
category id, and `test_db_parity.py`. Titles in the catalog match the contract `name` anchors,
not the old date-suffixed titles. The settlements chart, the map, and the policy status are listed
as stub SQL (`SELECT 'placeholder'`), not as confirmed warehouse measures.
