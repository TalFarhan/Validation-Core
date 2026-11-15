# Data Model: Top Settlement Tie Assertion

No new stored entity. The test reads the existing golden map and the existing UI map.

## Golden ranking

`dashboard_sanity_checks.screen_1_status_picture.metrics.top_10_settlements.values`

A map of settlement name to integer count. This slice does not write the file.

Partition:

| Set | Rule on the current file | Role in the assert |
|-----|--------------------------|--------------------|
| Stable | count `>= 32` | Name must be in the UI map with that count |
| Golden tie rows | count `< 32` | Not matched by name. Their shared value is the tie count |

Current stable rows:

| Name | Count |
|------|-------|
| ראשון לציון | 39 |
| תל אביב-יפו | 36 |
| רמת השרון | 35 |
| נתניה | 34 |
| ראש העין | 32 |
| רמלה | 32 |

Current golden tie rows are יגל, גינתון, צפרייה, and חיפה, each 31. Those names are not required on the UI. The shared value 31 is the tie count.

If the below-32 golden values are not all the same integer, the test cannot choose a tie count and fails.

## UI ranking

`read_top_10_settlements() -> dict[str, int]`

| Check | Rule |
|-------|------|
| Empty map | Skip `Missing Page Object reader for top_10_settlements` |
| Stable names | Every stable golden name is present and equal |
| Tie slots | Keys that are not in the stable set |
| Tie size | Exactly 4 |
| Tie count | Each tie-slot value equals the golden tie count (31) |

Extra names are not free when they make the remainder longer than 4. A fifth non-stable row fails the size check.
