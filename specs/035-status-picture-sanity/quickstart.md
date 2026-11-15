# Quickstart: Status Picture Sanity Tests

**Feature**: 035-status-picture-sanity | **Date**: 2026-10-19

## What this slice adds

`pages/status_picture/status_picture_page.py` opens the first page of `ניתוח התרעות`. `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` checks `screen_1_status_picture` in the golden file. The Screen 2 sanity module is not edited.

## Collect

From the repository root:

```text
python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py --collect-only
```

Expect `test_screen_1_global_metrics`, `test_screen_1_filtered_metrics`, `test_screen_1_alerts_by_category`, and `test_screen_1_top_settlements`.

## Run

From the repository root, with portal credentials and a saved auth state:

```text
python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py -v
```

## Pass

- After a clear, warning zones are `1337` and alerted population is `10142584`.
- After `set_date_range("13/06/2025", "25/06/2025")`, zones under fire are `1271` and alerted population is `10091037`.
- Rockets are `16817`, category 2 is `519`, and category 10 is `0`, or that test skips with `Missing Page Object reader for alerts_by_category`.
- The ten settlement counts match, or that test skips with `Missing Page Object reader for top_10_settlements`.
- The edit list does not include `tests/conftest.py`, `core/`, or `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`.
