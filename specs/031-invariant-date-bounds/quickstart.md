# Quickstart: Bound the Global Invariant Tests by Date

**Feature**: 031-invariant-date-bounds | **Date**: 2026-10-18

## What changed

`test_day_plus_night_equals_untoggled_sum` applies `set_date_range("01/09/2026", "15/10/2026")` before the untoggled dates total.

`test_clear_restores_population_snapshot` applies that call before the before snapshot, and again after `clear_filters()` before the after snapshot.

## Run

From the repository root, with portal credentials and a saved auth state:

```text
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_day_plus_night_equals_untoggled_sum tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot -v
```

## Pass

Both tests pass. Neither is marked expected-fail. The edit list for this slice is `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` only.
