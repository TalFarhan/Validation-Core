# Data Model: Screen 2 Chart Readers

No new stored entity. The readers return maps the sanity tests already compare to the golden file.

## Hierarchy level

Selected on `התרעות לפי מחוז`.

| Key | Visible label | Click | Golden map this slice asserts |
|-----|---------------|-------|--------------------------------|
| `mahoz` | chart title `התרעות לפי מחוז` | none new | unchanged: existing sum and daily-average tests |
| `nafa` | נפה | `set_hierarchy_level("nafa")` | `alerts_by_hierarchy.nafa.sum` |
| `rashut` | רשות | `set_hierarchy_level("rashut")` | `alerts_by_hierarchy.rashut.sum` |
| `yeshuv` | יישוב | `set_hierarchy_level("yeshuv")` | `alerts_by_hierarchy.yeshuv.sum` |

`set_hierarchy_level` returns false when that label is not a visible button, tab, or option in the district visual.

`read_district_labels() -> dict[str, int]` is the map for every level. Names are the row or category text. Counts are integers from the alerts cell, the mark label, or the tooltip. Extra UI names are allowed. Every golden key must be present and equal.

Current sum rows the three new tests require:

| Level | Name | Sum |
|-------|------|-----|
| nafa | נפת חירם | 12 |
| nafa | חטמ'ר צפונית - 7643 | 1 |
| rashut | גליל עליון | 8 |
| rashut | מבואות החרמון | 3 |
| rashut | רג'ר | 1 |
| rashut | שער הנגב | 1 |
| yeshuv | הגושרים | 3 |
| yeshuv | יובל, מעיין ברוך | 2 each |
| yeshuv | בית הלל, דפנה, מלכייה, מנרה, נחל עוז, רג'ר | 1 each |

`daily_avg` for these three levels is in the golden file and is not asserted by this slice.

## Hour bucket

Chart title: `גרף התרעות וגם ממוצע לפי שעה`.

| Method | Keeps | Drops | Golden map |
|--------|-------|-------|------------|
| `read_hour_buckets` | `HH:MM` plus an integer that is not an average | `ממוצע`, fractional text | `alerts_by_hour.sum` |
| `read_hour_daily_avg` | `HH:MM` plus a whole average count | a fraction that is not a whole number, an unpaired label | `alerts_by_hour.daily_avg` |

Hour keys are `HH:MM`. The current daily-average rows are `00:00`, `04:00`, `14:00`, `15:00`, and `21:00`, each `1`.

An empty dict is the skip signal. A non-empty dict that misses a golden key fails.
