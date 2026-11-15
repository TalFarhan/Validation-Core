# Quickstart: Verifying SVG Aria-Label Totals

**Feature**: 024-population-svg-aria | **Date**: 2026-10-15

Confirm the three-chart population test. `core/` is not part of the edit.

## Prerequisites

- Repo checked out on `feature/reportportal-integration`.
- Python 3.11+ venv with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/024-population-svg-aria`.
- `auth_state.json` and `.env` for the live portal.

## 1. The three-chart test

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

Expected: pass. The hour total is not `141493` and not `5895.54`. The dates total is the sum of its SVG bar labels.

## 2. This slice did not edit core

The change set for this work is `pages/alerts_analysis/population_page.py`.
`tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and
`tests/ui/alerts_analysis_dashboard/population_snapshot.py` still call `page.chart_total`.
