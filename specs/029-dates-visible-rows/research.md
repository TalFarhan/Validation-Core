# Phase 0 Research: Visible Dates Table Rows

**Feature**: 029-dates-visible-rows | **Date**: 2026-10-18

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Sum only rows that pass is_visible()

**Decision**: For `DATES_CHART` only, add a `התרעות` grid cell when its `role="row"`
returns true from Playwright `is_visible()`. Skip a row that fails that check even when
`evaluate_all` can still read its text. Do not call `_sum_scrolled_alert_column` for this
total. Do not scroll the table.

**Rationale**: On 2026-10-18 the filtered hour chart, district chart, and dates table each
show 13. The dates automation returns 5847. `_collect_alert_rows` uses `evaluate_all`,
which reads hidden nodes, and `_sum_scrolled_alert_column` then scrolls so more of those
nodes enter the sum. Power BI leaves filtered rows in the DOM. The visible table is the
dashboard value.

**Alternatives considered**:

- *Keep scrolling and dedupe by `aria-rowindex`*: rejected. Hidden stale rows still have indexes and integers.
- *Edit `core/components/chart.py`*: rejected. This slice must not edit `core/`.

## Decision 2 — Wait until the visible column repeats

**Decision**: After `הצג כטבלה` opens the table, poll the visible `התרעות` integers until
two consecutive reads return the same sum and the same included count. Use `self.timeout`
and a short pause between reads, in the same style as `clear_filters`. Then return that
sum. A header row and a row that contains `סה"כ` stay excluded.

**Rationale**: Opening the table can expose the previous filter for a moment. A single
immediate read can capture that stale column. Two identical visible reads mean the
filtered cells have stopped changing.

**Alternatives considered**:

- *A fixed sleep*: rejected. The page already settles other visuals by a repeated read.
- *Return on the first visible integer*: rejected. That integer can belong to the pre-filter render.

## Decision 3 — The three-chart test stays strict

**Decision**: `test_hour_date_and_district_sums_match` keeps
`hour_total == district_total == dates_total`. If `@pytest.mark.xfail` is present, remove
it. On 2026-10-18 the test body has no xfail decorator; the slice must leave that true.
Keep the date strings already in the test: `01/09/2026` and `15/10/2026`.

**Rationale**: The user read 13 on all three visuals for this filtered dashboard. An
expected-fail mark would hide a reader that still returns 5847. The date strings are the
filter the user already proved.

**Alternatives considered**:

- *Hard-code `assert dates_total == 13`*: rejected. The contract is equality of the three charts. The live filtered page is where 13 is expected.
- *Change the date range again*: rejected. The user asked to fix the reader, not the range.

## Decision 4 — Hour and district stay

**Decision**: `HOUR_CHART` still calls `_svg_mark_total`. `DISTRICT_CHART` and
`SETTLEMENT_CHART` still call `_rows_for_total`. `חזרה לדוח` still closes the dates table
before `chart_total` returns.

**Rationale**: Those two charts already agree with the visible dates table at 13. This
slice changes which dates rows are eligible for the sum.
