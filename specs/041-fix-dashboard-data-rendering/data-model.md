# Phase 1 Data Model: Fix Skipped Tests and Load Errors

This slice changes navigation readiness and filter selection. The "entities" are
UI anchors, slicer selections, and the golden record keys that drive them.

## Entity: Report-ready anchor

| Field | Value | Notes |
|-------|-------|-------|
| Page | `AlertsPopulationPage` | Screen 2 (population) |
| Current anchor | `DISTRICT_CHART` = `התרעות לפי מחוז` | Data-dependent; empty under default filter |
| New anchor | `TOTAL_CARD` = `סה"כ אוכלוסייה` | All-time total, filter-independent, Screen-2-only |
| Page | `StatusPicturePage` | Screen 1 (status picture) |
| Anchor | `UNDER_FIRE_CARD` = `אזורי התרעה תחת ירי` | Gauge card, filter-independent, Screen-1-only — unchanged |

**Rule**: A report-ready anchor MUST be visible independent of the active date/operation
filter and MUST be specific to the screen being loaded. `before_report_ready_check()`
still uses `DISTRICT_CHART` only to decide the Screen 1 → Screen 2 page switch.

## Entity: Operation selection (Screen 1)

| Field | Value | Notes |
|-------|-------|-------|
| Slicer id | `date_range` | Defined on `AlertsAnalysisPage` (role `FilterName`) |
| Option label | `עם כלביא` | Read from the golden record, not hard-coded |
| Settle signal | Warning-zones gauge changes then repeats | Reuses `_wait_until_gauge_changes` |
| Failure | Option not in slicer | Assertion names the missing operation |

## Entity: Golden date range (Screen 2)

| Field | Value | Notes |
|-------|-------|-------|
| Source | `screen_2_alerts_analysis.date_range` | `start: 2026-09-01`, `end: 2026-10-18` |
| Page format | `DD/MM/YYYY` | Via `to_page_date` |
| Applied by | `set_date_range` in each chart test's setup | Already in `_apply_golden_range` |

## Golden record change

`data/alerts/db_sanity_am_kalavi.yaml`, under `dashboard_sanity_checks.screen_1_status_picture`:

```yaml
screen_1_status_picture:
  description: "מסך תמונת מצב - מבצע 'עם כלביא'"
  operation: "עם כלביא"        # NEW: selected directly on the FilterName slicer
  date_range:
    start: "2025-06-13"        # retained for reference / fallback
    end: "2025-06-25"
  metrics:
    ...                         # unchanged
```

**Rule**: Only the `operation` key is added. No metric `expected_value` or map value changes.

## State transitions (navigate readiness)

```
goto(url)
  └─ _dashboard_ready()?  (iframe present AND ready anchor visible)
        ├─ yes → after_navigate()
        └─ no  → authenticate / portal search
                 └─ poll ready anchor until self.timeout
                       ├─ visible → after_navigate()
                       └─ exhausted → raise LoadTimeoutError
```

The only change is that the population page's ready anchor is now filter-independent
(`TOTAL_CARD`), so the "visible" branch is reachable under the default empty filter.

## Reader → skip-guard map (behavior preserved)

| Reader | Skip message (safety net) | Resolves when |
|--------|---------------------------|---------------|
| `read_district_labels` | "District chart … returned no rows" | Golden range applied → chart renders |
| `read_top_10_settlements` | "Missing Page Object reader for top_10_settlements" | Operation selected → ranking renders |
| `read_alerts_by_category` | "Missing Page Object reader for alerts_by_category" | Operation selected → category cards render |
| `read_cards` → `_require_card` | "Missing Page Object reader for {key}" | Operation selected → gauges populate |
