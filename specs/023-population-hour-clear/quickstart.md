# Quickstart: Verifying the Hour Sum and Clear Baseline

**Feature**: 023-population-hour-clear | **Date**: 2026-10-15

Confirm the three population tests, then the rest of the file. `core/` is not part of the edit.

## Prerequisites

- Repo checked out on `feature/reportportal-integration`.
- Python 3.11+ venv with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/023-population-hour-clear`.
- `auth_state.json` and `.env` for the live portal.

## 1. The three tests

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

Expected: pass. The hour total is not `5895.54`. The clear test's baseline is the snapshot after the first clear.

## 2. The whole population file

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py -v
```

Expected: pass, including the page-open test, the card bounds, and the settlement legend.

## 3. This slice did not edit core

The change set for this work is `pages/alerts_analysis/population_page.py` and
`tests/ui/alerts_analysis_dashboard/test_population_invariants.py`.
`tests/ui/alerts_analysis_dashboard/population_snapshot.py` still calls `page.chart_total`.
