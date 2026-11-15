# Quickstart: Population Screen Data Validation Tests

**Feature**: 033-population-sanity-tests | **Date**: 2026-10-19

## What this slice adds

A sanity package at `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
It checks three population cards against `data/alerts/db_sanity_am_kalavi.yaml`.
`tests/ui/` and `core/` stay as they are.

## Collect

From the repository root:

```text
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only
```

Expect two tests: `test_global_metrics_match_db` and `test_filtered_population_matches_db`.

## Run

From the repository root, with portal credentials and a saved auth state:

```text
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -v
```

## Pass

- After a clear, the total card is `10142584` and the unprotected card is `3389879`.
- After `set_date_range("01/09/2026", "18/10/2025")`, the warned card is `9474`.
- The edit list does not include `tests/ui/` or `core/`.

The golden end date is earlier than the start date. The test keeps that order. It does not rewrite the YAML.
