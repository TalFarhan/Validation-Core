# Quickstart: Force the Date Field Click Past the Overlay

**Feature**: 032-date-input-force-click | **Date**: 2026-10-18

## What changed

`_commit_field` in `pages/alerts_analysis/population_page.py` clicks with `field.click(force=True)`. Fill and Enter stay. The invariant test is unchanged.

## Run

From the repository root, with portal credentials and a saved auth state:

```text
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py::test_clear_restores_population_snapshot -v
```

## Pass

The test passes. The edit list for this slice is `pages/alerts_analysis/population_page.py` only.
