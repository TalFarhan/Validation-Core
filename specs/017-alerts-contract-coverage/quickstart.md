# Quickstart: Alerts Contract Coverage

**Feature**: 017-alerts-contract-coverage | **Date**: 2026-10-13

Confirm the contract rows without a portal, then run the Alerts parity test and the fleet
regression gate. No new dependency. No engine change.

## Prerequisites

- Repo checked out; Python 3.11+ with `pip install -r requirements.txt` (PyYAML is already required).
- `.specify/feature.json` points at `specs/017-alerts-contract-coverage`.
- For the live test only: `.env` with `DB_ALERTS_NAME`, and a saved portal session (`auth_state.json`).

## 1. Contract rows (no browser, no database)

```powershell
python -m pytest tests/unit/test_db_parity_engine.py -v
```

Expected after implementation:

- Nine threat metrics: scopes `ירי רקטות וטילים`, `חדירת מחבלים`, and `חדירת כלי טיס עוין`
  with category ids `1`, `2`, and `10`, each with `היום`, `אתמול`, and `סה"כ בטווח שנבחר`.
- Six general metrics under `אוכלוסייה מותרעת` and `אזורי התרעה תחת ירי`, same three names,
  `visual: kpi`, no `category_id`.
- One chart named `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת`.
  Its SQL equals `PERIOD_COMPARISON_CHART_SQL` and contains neither `:start_date` nor `AlertDate`.
- The six existing category measures, the ranking chart (`יישובים`, two yods), the map, and the
  policy status are still present.
- No metric `name` or `scope` contains `שלושים יום`.
- `test_db_parity.py` still has no skip marker.

## 2. Domain leakage check

This feature does not edit `core/` or the parity engine. After implementation:

```powershell
git diff -- core/components core/portal tests/helpers/db_parity_engine.py
```

Expected: no diff.

## 3. Live Alerts parity

Requires the portal session and `DB_ALERTS_NAME`. The new stubs are executed. `SELECT 0` and the
empty chart will not match a populated report, so this run fails those metrics until real SQL
replaces the stubs. A missing database must fail the test rather than skip it.

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity -v
```

## 4. Fleet regression

```powershell
python -m pytest tests/ui/fleet_dashboard/ -v
```

Expected: 100% green. This feature does not change fleet pages or Layer 2.

## 5. Catalog

Section 8 of `docs/COVERAGE_CATALOG.md` lists the nine threat cards, the six general cards, and
the static comparison chart, and marks their SQL as stubs.
