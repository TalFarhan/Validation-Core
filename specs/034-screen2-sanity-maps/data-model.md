# Data Model: Screen 2 Sanity Maps

**Feature**: 034-screen2-sanity-maps | **Date**: 2026-10-19

No new stored records. The golden file is not edited.

## Screen range

`dashboard_sanity_checks.screen_2_alerts_analysis.date_range`

| Field | File value | Page argument |
|-------|------------|---------------|
| start | `2026-09-01` | `01/09/2026` |
| end | `2026-10-18` | `18/10/2026` |

Every new test sets this pair. The two existing card tests are not rewritten.

## Settlement map

`metrics.alerted_population_by_settlement.values`

| Golden name | Expected warned value |
|-------------|----------------------|
| ר'ג'ר | 2752 |
| הגושרים | 1344 |
| דפנה | 1096 |
| בית הלל | 1095 |
| מעיין ברוך | 889 |
| יובל | 836 |
| מלכייה | 577 |
| נחל עוז | 562 |
| מנרה | 323 |

The UI source is `Chart.read(SETTLEMENT_CHART, scope=PAGE_TITLE)`. The value column is the series named `מותרעת`.

## Hierarchy maps

`metrics.alerts_by_hierarchy`

| Level | UI source | sum | daily_avg |
|-------|-----------|-----|-----------|
| mahoz | `DISTRICT_CHART` after `set_district_aggregation` | מחוז צפון 12, פיקוד דרום 1 | both 1 |
| nafa | no level control | skipped | skipped |
| rashut | no level control | skipped | skipped |
| yeshuv | no level control | skipped | skipped |

`read_district_labels()` returns `{label: int}` for the visible district rows. Sum mode and daily-average mode are separate reads.

## Date map

`metrics.alerts_by_date.values`

| Golden key | Expected count |
|------------|----------------|
| 2023-09-29 | 1 |
| 2023-09-21 | 1 |
| 2023-09-17 | 1 |
| 2023-09-10 | 5 |
| 2023-09-02 | 5 |

`read_date_counts()` returns `{row header: int}`. A `DD/MM/YYYY` header is normalized to `YYYY-MM-DD` in the test. These keys sit outside the screen range above. The file stays as stored.

## Hour maps

`metrics.alerts_by_hour`

| Key | sum | daily_avg |
|-----|-----|-----------|
| 00:00 | 5 | 1 |
| 04:00 | 5 | 1 |
| 14:00 | 1 | 1 |
| 15:00 | 1 | 1 |
| 21:00 | 1 | 1 |

`read_hour_buckets()` returns the sum map from hour SVG labels that contain `HH:MM`. The daily-average column has no hour-scoped reader and is skipped.

## Validation rules

1. Every golden key in a checked map is present and equal.
2. Extra UI categories do not fail the map.
3. An empty district, date, or hour-sum map skips that test with `Missing page object method for <metric>`.
4. A present map that disagrees with the file fails that test.
5. נפה, רשות, יישוב, and the hour daily average skip even when the page is open.
6. `chart_total` still returns one number for each chart title.

## State transitions

```text
new map test
    → set_date_range(01/09/2026, 18/10/2026)
    → settlement: Chart.read warned series
    → mahoz sum: set_district_aggregation("sum") → read_district_labels()
    → mahoz daily avg: set_district_aggregation("average") → read_district_labels()
    → nafa / rashut / yeshuv: skip, no click
    → dates: read_date_counts() → leave the dates table
    → hour sum: read_hour_buckets()
    → hour daily avg: skip
```
