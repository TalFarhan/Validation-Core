# Quickstart: Verifying the Population Invariant Fix

**Feature**: 021-population-invariant-fix | **Date**: 2026-10-14

Confirm the three tests that were failing, then the rest of the population file. `core/` is not
part of the edit.

## Prerequisites

- Repo checked out on `feature/reportportal-integration`.
- Python 3.11+ venv with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/021-population-invariant-fix`.
- `auth_state.json` and `.env` for the live portal.

## 1. The three failing tests

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

Expected: pass. A settlement name with no number does not abort `chart_total`. The Sum click does
not report a strict-mode violation.

## 2. The whole population file

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v
```

Expected: pass, including the page-open test, the card bounds, and the settlement legend.

## 3. This slice did not edit core

The change set for this work is `pages/alerts_analysis/population_page.py` only.
`tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total`.
