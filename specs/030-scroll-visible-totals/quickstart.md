# Quickstart: Scroll the Dates Table and Filter District Rows

**Feature**: 030-scroll-visible-totals | **Date**: 2026-10-18

Auth state is required. The command runs from the repository root.

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_hour_date_and_district_sums_match -v
```

## What the test does

1. Clears filters.
2. Sets the date range already in the test, `01/09/2026` through `15/10/2026`.
3. Sets the district chart to Sum.
4. Asserts `hour_total == district_total == dates_total`.

The dates total scrolls the accessible table and adds each visible row once. The district total waits and adds only visible rows. On this filtered dashboard that shared value is 13. The test has no expected-fail mark. Fleet smoke is not part of this slice.
