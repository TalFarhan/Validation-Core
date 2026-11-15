# Quickstart: Verifying Gauge Value Extraction

**Feature**: 013-kpi-gauge-visuals | **Date**: 2026-10-12

Fast path to confirm `extract_kpi_value_text` returns a Gauge's current value and still handles standard
KPI labels.

## Prerequisites

- Repo checked out; Python 3.11+ virtualenv active with project deps installed (`pip install -r requirements.txt`).
- No new dependencies are required for this feature.

## 1. Unit verification (pure logic — no browser)

```powershell
python -m pytest tests/unit/test_kpi_normalize.py -v
```

Expected: all cases pass, including:

- Existing normalize cases — commas, bidi, nbsp, decimals unchanged.
- Existing extract cases — mixed Hebrew title + one figure, space thousands, `"N/A"` fallback.
- **New** labeled Gauge: `"distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337."` → `"3"`
  (not `"1,337"` and not `"1337133733"`).
- **New** compact Gauge: `"0 1,337 3"` → `"3"`.
- **New** extract → normalize on those strings → `"3"`.

## 2. Regression gate (Constitution III)

The `role="button"` path and `normalize_kpi_text` are unchanged:

```powershell
python -m pytest tests/ui/fleet_dashboard/
```

Expected: 100% pass (requires portal access / configured `.env`).

## 3. End-to-end spot check (Alerts Gauges, when present)

If the Alerts report exposes a Gauge-rendered pilot metric, the existing parity test is the consumer:

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -v
```

Expected: `KPI.number(title)` returns the Gauge's current reading (the warehouse scalar), not a
concatenated min/max/current integer.

## What "done" looks like

- Unit suite green (step 1), including the new Gauge rows.
- Fleet smoke green (step 2).
- No public API or locator changes; parity engine still calls `KPI.number(name)`.

## Where to look

- Implementation: `core/components/kpi.py` (`extract_kpi_value_text`, `_GAUGE_BOUND_PAIR`,
  `_NUMBER_TOKEN_COMPACT`).
- Tests: `tests/unit/test_kpi_normalize.py`.
- Consumer (unchanged): `tests/helpers/db_parity_engine.py`.
- Contract: `specs/013-kpi-gauge-visuals/contracts/kpi-component.md`.
