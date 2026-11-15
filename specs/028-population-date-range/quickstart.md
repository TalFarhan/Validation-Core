# Quickstart: Population Date Range

**Feature**: 028-population-date-range | **Date**: 2026-10-17

Auth state is required. The command runs from the repository root.

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

## What the test does

1. Clears filters.
2. Sets the date range from `01/01/2020` through today in day/month/year form.
3. Waits until the total population card stops changing.
4. Sets the district chart to Sum.
5. Asserts `hour_total == district_total == dates_total`.

A failure leaves the assertion strict. Fleet smoke is not part of this slice.
