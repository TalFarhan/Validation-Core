# Quickstart: Verifying the Population Chart Scope

**Feature**: 022-population-chart-scope | **Date**: 2026-10-15

Confirm the three tests that are still red, then the rest of the population file. `core/` is not
part of the edit.

## Prerequisites

- Repo checked out on `feature/reportportal-integration`.
- Python 3.11+ venv with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/022-population-chart-scope`.
- `auth_state.json` and `.env` for the live portal.

## 1. The three red tests

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

Expected: pass. The dates total does not include `אשדוד` or `נתניה`. Setup waits for the district
chart instead of failing at 30 seconds.

## 2. The whole population file

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v
```

Expected: pass, including the page-open test, the card bounds, and the settlement legend.

## 3. This slice did not edit core

The change set for this work is `pages/alerts_analysis/population_page.py` only.
`tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total`.
