# Quickstart: Screen 2 Chart Readers

Branch stays `feature/reportportal-integration`. Feature directory: `specs/037-screen2-chart-readers`.

## What changes

- `pages/alerts_analysis/population_page.py`: `set_hierarchy_level` and `read_hour_daily_avg`. District and hour readers may scroll or hover only when the cheaper read is empty.
- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`: נפה, רשות, יישוב, and the hour daily average call those methods.

## What stays

- `data/alerts/db_sanity_am_kalavi.yaml`
- `core/`
- The two card tests, the settlement test, both מחוז tests, the date test, and the hour-sum test

## Collect

From the repository root:

```powershell
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only
```

Expect the same eleven tests as feature 034. The four that used to skip before opening the page now have a `population_dashboard` parameter.

## Live check

Portal auth is required. Fleet smoke is not a gate.

```powershell
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -v
```

A level test passes when that level's golden sum matches. It skips with `Missing page object method for hierarchy level <level>` when the control is missing or the map is empty.

The hour daily-average test passes when the five golden hours are each `1`. It skips with `Missing page object method for hour daily_avg` when the average series cannot be paired.
