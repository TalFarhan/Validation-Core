# Phase 0 Research: Population SVG Circle and Value Regex

**Feature**: 025-population-svg-refine | **Date**: 2026-10-15

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Query circle with rect and path

**Decision**: The mark locator inside the tight visual container is
`svg rect, svg path, svg circle`. `aria-label` is read with `get_attribute`.
`inner_text` is not used.

**Rationale**: The dates chart's data point was a `circle` with role `option` and the label
`תאריך 2026-10-15. התרעות 0.` Rect and path labels on that chart had no integer. The hour
bars were integer `aria-label` values on the shapes.

**Alternatives considered**:

- *Query `rect, path, circle` with no `svg` prefix*: rejected. The `svg` prefix keeps the
  search on the drawing and matches the marks already found.
- *Sum `[role="option"]` together with the shapes*: rejected. A circle that is also an option
  would be added twice.

## Decision 2 — Integer after `התרעות`, otherwise a bare integer

**Decision**: Skip a label that contains `ממוצע`. Skip a label that contains a fractional
number (`5895.54`, `5,895.54`). If the label contains `התרעות`, add the integer from
`התרעות\s*([0-9,]+)` after removing thousands separators. If the whole label is one integer,
add that integer. Every other label is skipped.

**Rationale**: `תאריך 2026-10-15. התרעות 0.` must contribute `0`, not `2026`. The hour bars
found on 2026-10-15 were bare labels `5293`, `5587`, `4181`, `3584`, `3802`, `4429`, `6286`,
and `7734`. Requiring `התרעות` on every label would drop those bars.

**Alternatives considered**:

- *Always take the last integer*: rejected. A date token can be last when the alert count is
  missing or written first.
- *Require `התרעות` on every kept label*: rejected. The live hour bars are bare integers.

## Decision 3 — Wait for the first mark

**Decision**: Before counting marks, `expect` the first `svg rect, svg path, svg circle`
inside the container to be visible, using the population page timeout. Then read every
`aria-label`.

**Rationale**: The user asked for a visibility wait so a chart still drawing is not totaled
early. On the last run the hour total was already `141493`, and a debug print showed only
`kept[:8]`. Those eight strings were the first slice of the list, not proof that sixteen bars
were absent. The wait still runs before the collection.

**Alternatives considered**:

- *Sleep for a fixed number of seconds*: rejected. `expect` stops when the mark is visible.
- *Treat the eight printed labels as the full set*: rejected. The print was limited to eight.

## Decision 4 — District and settlement stay

**Decision**: `DISTRICT_CHART` and `SETTLEMENT_CHART` keep their current readers.
`test_hour_date_and_district_sums_match` is not edited. Its second assertion still compares
the dates total with the current district reader.

**Rationale**: This slice changes the dates and hour mark reader. The user named circles, the
regex, and the wait. The district reader is outside that list, and changing it inside `Chart`
would edit `core/`.

**Alternatives considered**:

- *Send the district chart through the same SVG reader*: rejected. The user did not name that chart.
- *Weaken the test*: rejected. The test stays the contract.
