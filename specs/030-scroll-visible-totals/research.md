# Phase 0 Research: Scroll the Dates Table and Filter District Rows

**Feature**: 030-scroll-visible-totals | **Date**: 2026-10-18

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Scroll the dates table and keep only visible rows

**Decision**: For `DATES_CHART`, keep the right-click and `הצג כטבלה`. After the table
opens, scroll its scroll parent in overlapping steps. After each step, add integers from
rows that pass `is_visible()`. Store each row once, keyed by `aria-rowindex` or by the
row-header text when that index is absent. Stop when one pass does not move the scroll
position and does not add a new key, and a second pass is also unchanged. Also stop at
`self.timeout`. Skip a header row and a `סה"כ` row. Then click `חזרה לדוח`.

**Rationale**: On 2026-10-18 a visible-only read of the first viewport returned `11`. The
filtered table totals `13`. The missing alerts are in virtualized rows. An earlier scroll
that used `evaluate_all` without `is_visible()` added hidden DOM rows. This scroll adds a
row only while it is visible, and the key stops the overlap from adding it twice.

**Alternatives considered**:

- *Stay on the first viewport*: rejected. That read is the `11`.
- *Scroll and sum every DOM row*: rejected. That path produced the stale hidden totals.

## Decision 2 — District uses visible rows and a settle wait

**Decision**: `chart_total` for `DISTRICT_CHART` no longer sums `_rows_for_total`. Inside
the tight visual container for `התרעות לפי מחוז`, add integers from `role="row"` elements
that pass `is_visible()`. Use the same header and `סה"כ` skips as the dates column, and
the `התרעות` grid cell when that header is present. Poll until two consecutive visible
reads match, up to `self.timeout`. Do not scroll the district visual. `SETTLEMENT_CHART`
still uses `_rows_for_total`.

**Rationale**: On 2026-10-18 the hour total was `13` and this district branch returned
`5847`. `_rows_for_total` calls `Chart.read`, which parses the container with no per-row
`is_visible()` check. Hidden rows in that container are the extra `5847`. The visible
district rows are the `13` on the dashboard. The district chart is not virtualized the
way the dates table is, so this slice does not scroll it.

**Alternatives considered**:

- *Edit `core/components/chart.py`*: rejected. This slice must not edit `core/`.
- *Open `הצג כטבלה` on the district chart too*: rejected. The user asked for `is_visible()` and a settle wait on the district reader, not a second menu table.

## Decision 3 — The three-chart test stays

**Decision**: Do not edit `test_hour_date_and_district_sums_match` except to leave it as
it is. The assertion stays `hour_total == district_total == dates_total`. The date strings
stay `01/09/2026` and `15/10/2026`. There is no `pytest.mark.xfail`.

**Rationale**: The filtered dashboard shows `13` on all three visuals. The readers are
what this slice changes.

**Alternatives considered**:

- *Mark the test expected-fail*: rejected. The user ruled that out.

## Decision 4 — The hour reader stays

**Decision**: `HOUR_CHART` still calls `_svg_mark_total`.

**Rationale**: That reader already returned `13`, which matches the dashboard.
