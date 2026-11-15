# Quickstart: Fix Skipped Tests and Load Errors

## What this slice changes

1. **Population page ready anchor** — `_report_ready_locator()` returns `TOTAL_CARD`
   (`סה"כ אוכלוסייה`) instead of the data-dependent `DISTRICT_CHART`, so `navigate()`
   succeeds under the default empty filter.
2. **Status-picture setup** — `_apply_golden_range()` selects the operation by name
   (`עם כלביא`, read from the golden record) via a new `select_operation()` page method
   instead of passing `start`/`end` dates.
3. **Golden record** — adds `operation: "עם כלביא"` under `screen_1_status_picture`.
4. Skip guards stay as a safety net; English-only in-function comments.

## Files touched

| Path | Change |
|------|--------|
| `pages/alerts_analysis/population_page.py` | `_report_ready_locator()` → `TOTAL_CARD` |
| `pages/status_picture/status_picture_page.py` | add `select_operation()`; golden path no longer uses `_OPERATION_RANGES` |
| `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` | `_apply_golden_range()` selects by operation name |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | audit: every chart test applies the golden range before reading |
| `data/alerts/db_sanity_am_kalavi.yaml` | add Screen 1 `operation` key |

## Run (requires portal auth)

```powershell
# Screen 2 (Alerts Analysis) sanity
pytest -m sanity tests/sanity/alerts_analysis_dashboard/test_data_validation.py

# Screen 1 (Status Picture) sanity
pytest -m sanity tests/sanity/status_picture_dashboard/test_status_picture_validation.py
```

## Expected results

- No `LoadTimeoutError` on a cold load with the default empty filter (US1).
- No chart test skips with an empty-reader / missing-reader message when data is present (US3).
- The status-picture warning-zones gauge settles on the `עם כלביא` value after selection (US2).
- `AlertsPopulationPage._report_ready_locator()` resolves to `TOTAL_CARD` (US4).

## Negative checks

- Break the ready anchor (point it at a non-existent phrase) → `navigate()` still raises
  `LoadTimeoutError`.
- Set the Screen 1 `operation` to an unknown name → `select_operation()` raises an
  assertion naming the missing operation.

## Non-goals / guardrails

- No change to `self.timeout` (already `120_000`).
- No edit to fleet modules, `core/`, or the root `conftest.py`.
- Only `data/` edit is the Screen 1 `operation` name.
