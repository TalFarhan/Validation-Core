# Quickstart: Verifying the Dates Accessible Table

**Feature**: 026-dates-accessible-table | **Date**: 2026-10-15

Confirm the three-chart population test. `core/` is not part of the edit.

## Prerequisites

- Repo checked out on `feature/reportportal-integration`.
- Python 3.11+ venv with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/026-dates-accessible-table`.
- `auth_state.json` and `.env` for the live portal.

## 1. The three-chart test

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

Expected: pass. The dates total is the sum of the `התרעות` column in the accessible table. The hour total remains the SVG bar sum. The table is closed before the district total is read.

## 2. This slice did not edit core

The change set for this work is `pages/alerts_analysis/population_page.py`.
`tests/ui/alerts_analysis_dashboard/test_population_invariants.py` and
`tests/ui/alerts_analysis_dashboard/population_snapshot.py` still call `page.chart_total`.
