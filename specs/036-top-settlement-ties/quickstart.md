# Quickstart: Top Settlement Tie Assertion

Branch stays `feature/reportportal-integration`. Feature directory: `specs/036-top-settlement-ties`.

## What changes

`test_screen_1_top_settlements` in `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`.

Golden counts of 32 and above must match by name. The other four UI rows must each be 31. Their names may differ from יגל, גינתון, צפרייה, and חיפה.

## What stays

- `data/alerts/db_sanity_am_kalavi.yaml`
- `pages/status_picture/status_picture_page.py`
- `test_screen_1_global_metrics`, `test_screen_1_filtered_metrics`, `test_screen_1_alerts_by_category`
- `core/` and the Screen 2 sanity module

## Collect

From the repository root:

```powershell
python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py --collect-only
```

Expect the same four tests as feature 035.

## Live check

Portal auth is required. Fleet smoke is not a gate.

```powershell
python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py::test_screen_1_top_settlements -v
```

A pass means the six stable settlements match and four other rows are each 31.

A fail means a stable count is wrong, the remainder is not four rows, or one of those rows is not 31.

An empty reader still skips with `Missing Page Object reader for top_10_settlements`.
