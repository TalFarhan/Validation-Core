# Phase 0 Research: Population Chart SVG Aria Labels

**Feature**: 024-population-svg-aria | **Date**: 2026-10-15

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Read mark `aria-label` values, not text

**Decision**: For `DATES_CHART` and `HOUR_CHART`, `chart_total` reads `aria-label` from
`svg rect` and `svg path` inside the tight visual container from feature 022. It uses
`get_attribute`. It does not call `inner_text`. It does not read `role="option"`.

**Rationale**: On 2026-10-15 the dates total was `0` from text nodes, and the hour total was
`141493`. `141493` equals `5895.54 * 24`, the average line repeated across the hours. The
option-text reader in `_hour_bar_total` produced that figure. `inner_text` fails on these SVG
nodes with `Node is not an HTMLElement`. The bar value is on `aria-label`.

**Alternatives considered**:

- *Keep summing `role="option"` text*: rejected. That path returned `141493`.
- *Keep `Chart._parse` for the dates chart*: rejected. Its text path returned `0`, and its mark
  path drops a label that has no category name.
- *Change `Chart._parse`*: rejected. That edits `core/`.

## Decision 2 — Shapes first, image role only as a fallback

**Decision**: Sum integers from `svg rect` and `svg path`. If that set includes no integer,
read `[role="img"]` inside the same container, excluding the container node itself. Do not add
shape labels and image labels in one total.

**Rationale**: Power BI can expose one bar as a shape and again as an image role with the same
label. Adding both doubles the total. The shapes are the data marks. The image role covers the
case where the value exists only there.

**Alternatives considered**:

- *Sum every `role="img"`, `rect`, and `path` together*: rejected. One bar would be counted twice.
- *Use only `role="img"`*: rejected. The visual container itself can carry that role and a title
  with no bar value.

## Decision 3 — Page-local integer parse

**Decision**: Skip a label that contains `ממוצע`. Skip a label that contains a fractional
number (`digits`, a dot or comma, then more digits, such as `5895.54` or `5,895.54`). From a
kept label, take the last integer token and strip thousands separators and spaces. `5,293`
becomes `5293`. `0` is kept. A label with no integer is skipped.

**Rationale**: The average line is labeled with `ממוצע` and a float. The bars are integers.
The rule lives on the population page so `core/` stays free of this chart's labels.

**Alternatives considered**:

- *Call `parse_mark_label`*: rejected for this slice. The user asked for a regex on the page,
  and that helper also requires a category fragment before a point is kept.
- *Skip every comma*: rejected. `5,293` is one integer, not a float.

## Decision 4 — District and settlement stay

**Decision**: `chart_total` for `DISTRICT_CHART` and `SETTLEMENT_CHART` keeps the current
readers. `test_hour_date_and_district_sums_match` is not edited. Its first assertion compares
the new hour total with the new dates total. Its second assertion compares that dates total
with the current district reader.

**Rationale**: The live failure stopped at `141493 == 0`, before the district comparison. The
user scoped the new reader to the hours and dates charts. The district chart already returns a
number through `Chart.read`. This slice does not retarget it and does not edit `core/`.

**Alternatives considered**:

- *Send the district chart through the same SVG reader*: rejected. The user named the hours
  and dates charts.
- *Weaken the test when the district total differs*: rejected. The test stays the contract.

## Decision 5 — Empty means fail

**Decision**: When the chosen mark set yields no integer, `chart_total` raises
`AssertionError` naming the chart. It does not return `0` for that miss.

**Rationale**: The dates chart's current `0` was a successful sum of text zeros. A missed
`aria-label` must not look like that result.
