# Quickstart: Screen 2 Sanity Maps

**Feature**: 034-screen2-sanity-maps | **Date**: 2026-10-19

## What this slice adds

New tests in `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` for the Screen 2 settlement, hierarchy, date, and hour golden maps. Basic district, date, and hour readers are added on `pages/alerts_analysis/population_page.py` where the page only had a total. The two card tests stay as they are.

## Collect

From the repository root:

```text
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only
```

Expect the two existing card tests plus the settlement test, two מחוז tests, three skipped hierarchy-level tests, the date test, the hour-sum test, and the skipped hour daily-average test.

## Run

From the repository root, with portal credentials and a saved auth state:

```text
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -v
```

## Pass

- `test_global_metrics_match_db` and `test_filtered_population_matches_db` pass.
- Settlement names match `alerted_population_by_settlement.values` on the warned series.
- מחוז sum matches `12` and `1`. מחוז daily average matches `1` and `1`. An empty district label map skips only that mode.
- נפה, רשות, and יישוב skip with `Missing page object method for hierarchy level <level>`.
- Hour daily average skips with `Missing page object method for hour daily_avg`.
- The edit list does not include `tests/ui/` or `core/`.

The golden alert dates remain in September 2023 while the screen range is `01/09/2026` through `18/10/2026`. The date test asserts the file. It is not skipped because of that year gap.
