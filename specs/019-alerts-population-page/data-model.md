# Data Model: Alerts Population Page

**Feature**: 019-alerts-population-page | **Date**: 2026-10-14

Entities are contract rows, a page-object snapshot, and placeholder SQL. No warehouse table is
added. Page-1 rows in `data/alerts/alerts_contract.yaml` stay as they are.

## 1. Population page

| Field | Type | Rule |
|-------|------|------|
| `PAGE_TITLE` | string | Accessible name of the second report-page tab. Copied from the live report. Single source for every new `scope`. |
| Catalog term | string | Inherited. `ניתוח התרעות`. Not a new product. |
| Ready phrase | string | `התרעות לפי מחוז`. Page 2 is ready only when this anchor is visible. |

`PAGE_TITLE` MUST NOT equal, contain, or be contained in any scope already used on page 1:

- `ירי רקטות וטילים`
- `חדירת מחבלים`
- `חדירת כלי טיס עוין`
- `אוכלוסייה מותרעת`
- `אזורי התרעה תחת ירי`

Blank scope is page 1's unscoped charts and is not valid for page 2.

## 2. Metric contract (page 2 rows)

Same fields the engine already loads. This feature does not add a key.

| Field | Required | Rule for page 2 |
|-------|----------|-----------------|
| `name` | yes | Stable title prefix. If the displayed title contains ` בין `, `name` is the text before it. MUST NOT contain `בין`. |
| `scope` | yes | Exactly `PAGE_TITLE`. |
| `visual` | yes | `kpi` for the three cards. `chart` for the distributions and the settlement chart. |
| `series_index` | charts that are not the default series | Integer `>= 0`. Settlement chart only: two different indexes. |
| `label` | no | Documentation. Engine ignores it. Settlement series use `מותרעות` and `לא מותרעות`. |
| `sql_query` | yes | Card: `POPULATION_PAGE_KPI_STUB_SQL`. Chart: `POPULATION_PAGE_CHART_STUB_SQL`. |
| `category_id` | no | Omit. These metrics are not split by threat category. |
| `compare` | no | Omit. Default `number`. |
| `maximum_sql` | no | Omit. Cards are `kpi`, not `gauge`. |

### 2.1 Rows whose names are known now

| Role | `name` | `visual` | `series_index` | `label` | SQL constant |
|------|--------|----------|----------------|---------|--------------|
| District distribution | `התרעות לפי מחוז` | `chart` | omit (0) | — | chart stub |
| Settlement, warned series | `אוכלוסייה לפי יישוב` | `chart` | `0` | `מותרעות` | chart stub |
| Settlement, unwarned series | `אוכלוסייה לפי יישוב` | `chart` | `1` | `לא מותרעות` | chart stub |

If the live legend order disagrees with those indexes, swap the indexes. Do not rename the series.

### 2.2 Rows copied from the live page

Apply the `בין` cut, then add one row each. Scope is still `PAGE_TITLE`.

| Role | `visual` | SQL constant | Notes |
|------|----------|--------------|-------|
| Total population card | `kpi` | card stub | Stable prefix of the total card |
| Warned population card | `kpi` | card stub | Stable prefix of the warned card |
| Unprotected population card | `kpi` | card stub | Stable prefix of the unprotected card |
| 24-hour distribution | `chart` | chart stub | One category per hour. Series 0 |
| Dates distribution | `chart` | chart stub | One category per date. Series 0. This is the day/night sum |

The three card names MUST be different from each other. They MAY match a page-1 `name` because
`scope` differs. They MUST NOT use a page-1 scope.

### 2.3 Name rule

```text
displayed = title as shown, bidi marks removed, trimmed
if " בין " in displayed:
    name = displayed.split(" בין ", 1)[0].strip()
else:
    name = displayed
```

`התרעות לפי מחוז בין ה-01/10/2026` becomes `התרעות לפי מחוז`.
Do not apply this cut to the existing page-1 chart whose name contains `ביממה הנוכחית והקודמת`.

## 3. Arrival snapshot

Taken by the test helper from page methods, after the population page is ready and before the
clear test changes slicers.

| Field | Type | Source |
|-------|------|--------|
| `cards` | map of role → number | total, warned, unprotected. A rendered 0 stays 0 |
| `totals` | map of role → number | 24-hour series 0; dates series 0; district series 0; settlement series 0; settlement series 1 |

A total is the sum of numeric category cells. Rules:

- `None` is skipped only when a sibling cell on that category is numeric. A category whose
  selected series is `None` fails that total (missing bar is not 0).
- `ChartReading.state == "empty"` fails the snapshot. The total is not 0.
- Values are `int` when integral, otherwise `float`. Restore uses `==`.

The clear mutation is not part of the snapshot. It is applied after the snapshot and must change
at least one field. Clear then requires field-by-field equality.

District Sum mode is not part of the arrival snapshot. The cross-chart test sets Sum mode on its
own and does not require clear to restore an aggregation toggle.

## 4. Day/night state

| Mode | Control | Dates-chart total used as |
|------|---------|----------------------------|
| `off` | day off and night off | `Sum(No Toggle)` |
| `day` | only day on | `Sum(Day Toggle)` |
| `night` | only night on | `Sum(Night Toggle)` |

Identity: `day + night == off`. Measured with the between-dates control and the numeric range
cleared. The three readings are three visits, not one overlaid state.

If the live control is a single slicer with day and night options, `set_day_night` still exposes
these three modes.

## 5. District aggregation

| Mode | Meaning on the visual | Used in this feature |
|------|------------------------|----------------------|
| `sum` | Category value is the sum of the grouped measure | Yes. Cross-chart identity |
| `average` | Category value is that sum divided by the group count | No. Comment on the SQL placeholder only |

## 6. Placeholder SQL

No new table and no new runner method.

| Constant | Text | Used by |
|----------|------|---------|
| `POPULATION_PAGE_KPI_STUB_SQL` | `SELECT 0` | The three card metrics |
| `POPULATION_PAGE_CHART_STUB_SQL` | `SELECT CAST(NULL AS nvarchar(200)) AS category_label, CAST(NULL AS int) AS metric_value WHERE 1 = 0` | Every new chart metric |

The chart statement MUST NOT mention `:start_date`, `:end_date`, or `AlertDate`. The runner may
still pass those binds; unused binds are ignored, as in feature 017.

Comments above the constants, English only, record:

1. Future date predicate: `AlertDate >= :start_date AND AlertDate < :end_date`.
2. Future grouping: one level at a time, district down to settlement. Do not add a parent and its children.
3. Future aggregation: Sum is `SUM`. Average is `SUM / NULLIF(COUNT, 0)` of that same grouped set.

## 7. Engine exclusion

`exclude_scopes` is an optional set of opaque scope strings.

| Input | Behavior |
|-------|----------|
| omitted, `None`, or empty | Every metric in the file runs, as today |
| set containing `PAGE_TITLE` | Metrics with that normalized scope are neither read nor queried |
| a metric with blank scope | Not excluded by `PAGE_TITLE` |

Page-1 parity passes `{PAGE_TITLE}`. New UI tests do not call the engine.

## 8. State transitions

```text
report closed or on page 1
    -> population suite navigate
    -> tab selected
    -> district anchor visible
    -> snapshot (cards + totals)
    -> mutate dates, day, night, range 0–349
    -> at least one snapshot field differs
    -> clear-all
    -> snapshot fields match the arrival snapshot
```

The identity tests start from a cleared page (or the arrival page when it is already clear) and
do not share mutated slicer state with the clear test. Each test sets the controls it needs.

```text
cleared page
    -> read dates total (off)
    -> day only -> read dates total
    -> night only -> read dates total
    -> assert day + night == off

cleared page
    -> district aggregation = sum
    -> assert 24-hour total == dates total == district total

cleared page
    -> assert warned <= total and unprotected <= total
```
