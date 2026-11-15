# Quickstart: Alerts Population Page

**Feature**: 019-alerts-population-page | **Date**: 2026-10-14

Confirm the contract and the engine exclusion without a portal. Run the population UI tests only
when a saved portal session can open the Alerts Analysis report. No new dependency.

## Prerequisites

- Repo checked out; Python 3.11+ with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/019-alerts-population-page`.
- For the UI tests only: `.env` portal settings and `auth_state.json`.
- Do not start the UI tests until `AlertsPopulationPage.PAGE_TITLE` is the live page-tab name
  and the hour, dates, and three card titles are the stable prefixes copied from that page.

## 1. Copy the live strings (once)

Open the Alerts Analysis report, select the second page, and record:

1. The page tab's accessible name → `AlertsPopulationPage.PAGE_TITLE` and every new YAML `scope`.
2. The 24-hour chart title, the dates chart title, and the three card titles. Cut each one at
   ` בין ` and store the prefix. District stays `התרעות לפי מחוז`. Settlement stays
   `אוכלוסייה לפי יישוב`.
3. Confirm a group whose accessible name matches `PAGE_TITLE` contains the district chart.
   If it does not, stop. Do not point `scope` at a section title and do not edit `core/`.
4. Confirm legend order. Index 0 is `מותרעות` and index 1 is `לא מותרעות`. If the legend is
   reversed, swap `series_index` in the YAML.

## 2. Contract and exclusion (no browser, no database)

```powershell
python -m pytest tests/unit/test_db_parity_engine.py -v
```

Expected after implementation:

- Page-2 metrics use `PAGE_TITLE` as `scope`.
- No page-2 `name` contains `בין`.
- `התרעות לפי מחוז` is a page-2 chart.
- `אוכלוסייה לפי יישוב` has two series indexes and the labels `מותרעות` and `לא מותרעות`.
- Card SQL is `SELECT 0`. Chart SQL is `POPULATION_PAGE_CHART_STUB_SQL` and does not mention
  `AlertDate` or `:start_date`.
- `PAGE_TITLE` does not collide with a page-1 scope.
- Page-1 metrics are still in the file.
- `exclude_scopes` skips matching scopes.
- `test_db_parity.py` passes that exclusion and still has no skip marker.

## 3. Domain leakage check

```powershell
git diff -- core/ pages/fleet_dashboard/
```

Expected: no diff. This feature does not edit Layer 0, Layer 2, or the fleet page.

```powershell
git diff -- tests/helpers/db_parity_engine.py
```

Expected: the `exclude_scopes` keyword only. No Hebrew strings.

## 4. Population UI tests (portal)

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v
```

Expected:

- The suite is on the second page before the assertions.
- Clear restores the arrival snapshot after dates, day, night, and the range 0–349, and at
  least one figure changed before clear.
- Day total plus night total equals the untoggled dates-chart total.
- The 24-hour total, the dates total, and the district total in Sum mode are equal.
- Warned population and unprotected population are each at most the total population.

These tests do not connect to the Alerts database.

## 5. Page-1 parity still ignores page 2

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -m db_parity -v
```

Expected: the existing page-1 result. A missing database still fails the test. The run does not
query `POPULATION_PAGE_KPI_STUB_SQL` or `POPULATION_PAGE_CHART_STUB_SQL`.

Do not treat a red page-1 run caused by an unimplemented `exclude_scopes` as a product failure
on page 2. Finish the keyword first.
