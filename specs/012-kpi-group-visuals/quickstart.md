# Quickstart: Verifying KPI Group Visual Support

**Feature**: 012-kpi-group-visuals | **Date**: 2026-10-11

Fast path to confirm the generic `KPI` component reads both `role="button"` cards and `role="group"` visuals.

## Prerequisites

- Repo checked out; Python 3.11+ virtualenv active with project deps installed (`pip install -r requirements.txt`).
- No new dependencies are required for this feature.

## 1. Unit verification (pure logic — no browser)

Run the KPI normalizer/extractor unit suite:

```powershell
python -m pytest tests/unit/test_kpi_normalize.py -v
```

Expected: all cases pass, including:
- `test_normalize_strips_marks_commas_and_whitespace` — existing normalize behavior unchanged.
- `test_extract_pulls_numeric_token_from_group_label` — the number is isolated from a group `aria-label`
  that bundles the Hebrew title (e.g. `"אזורי התרעה ... 1,234"` → `"1,234"`), handles nbsp separators,
  decimals, RTL/bidi-wrapped values, and the no-digit fallback (`"N/A"` → `"N/A"`).
- `test_extract_then_normalize_is_parseable` — extract → normalize produces a clean, parseable value.

## 2. Regression gate (Constitution III)

The `role="button"` path is unchanged, so fleet smoke must stay green:

```powershell
python -m pytest tests/ui/fleet_dashboard/
```

Expected: 100% pass (requires portal access / configured `.env`). This proves button-rendered KPIs still read
exactly as before.

## 3. End-to-end spot check (Alerts group visuals)

With Alerts credentials configured, run the Alerts DB-parity test, which reads the pilot metrics that render
as groups:

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py -v
```

Expected: the parity engine now obtains numeric UI values for the group-rendered metrics (no "locator not
found" / empty-value errors) and compares them to the warehouse.

## What "done" looks like

- Unit suite green (step 1).
- Fleet smoke green (step 2) — no button-path regression.
- Alerts parity can read group KPIs (step 3) — values are pulled from the `img` `aria-label` and parsed.

## Where to look

- Implementation: `core/components/kpi.py` (`_resolve_card`, `_read_group_value`, `extract_kpi_value_text`).
- Consumer (unchanged): `tests/helpers/db_parity_engine.py` (`KPI.number(name)`).
- Contract: `specs/012-kpi-group-visuals/contracts/kpi-component.md`.
