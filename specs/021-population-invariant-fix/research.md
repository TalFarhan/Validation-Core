# Phase 0 Research: Population Invariant Fix

**Feature**: 021-population-invariant-fix | **Date**: 2026-10-14

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Sum on the page, not in the chart reader

**Decision**: Change `AlertsPopulationPage.chart_total`. Leave `core/components/chart.py` and
`tests/ui/alerts_analysis_dashboard/population_snapshot.py` as they are.

**Rationale**: `take_snapshot`, the day/night test, and the three-chart test all call
`chart_total`. One filter fixes all three. The snapshot helper is specified to call page methods
only. The request forbids a `core/` edit.

**Alternatives considered**:

- *Filter inside `population_snapshot.py` only*: rejected. The day/night test and the three-chart
  test call `chart_total` directly, so they would still raise.
- *Drop settlement labels inside `Chart.read`*: rejected. That is a `core/` change.

## Decision 2 — Skip non-numbers; do not coerce them to 0

**Decision**: A selected cell is included only when it is an `int` or a `float` (`bool` is
excluded). `None` and any other type are skipped. If the running total never receives a cell, raise
the same empty-chart failure used today. A total that is a whole float is returned as `int`, as
today.

**Rationale**: The live failure is `AssertionError: Chart 'התרעות לפי תאריך' is missing a value
for 'ראשון לציון'` (and the same shape for the hour chart and `פתח תקווה`). The label is text.
The cell is `None`. Adding 0 would make day-plus-night and the three-chart identity compare a
padded sum. Skipping leaves the numeric bars in the total.

**Alternatives considered**:

- *Keep raising on `None`*: rejected. That is the current crash.
- *Skip only when the category label is not a date or hour*: rejected. The page would need a
  catalog of real category shapes. "Is the cell a number?" matches the request and stays local.

## Decision 3 — One Sum button via `.first`

**Decision**: `set_district_aggregation` looks for an exact-name button inside the district chart
container. When that count is not 1, it clicks
`get_by_role("button", name=label, exact=True).first` on the report frame. It never clicks a
locator whose count is greater than 1.

**Rationale**: The live page has two `סכום` buttons (`5 פריטים` and `3 פריטים וקבוצת משנה אחת`).
A strict click on the unscoped exact name throws. A group named with the district chart title does
not contain the button and waits out the timeout. `.first` is the request's allowed resolution and
does not touch the slicer engine.

**Alternatives considered**:

- *Click every unpressed Sum button*: rejected. That changes a second chart the test does not name.
- *Teach `Slicer` a scoped click*: rejected. That is generic engine behavior under `core/`.

## Decision 4 — What "no core diff" means for this slice

**Decision**: The implementation edits `pages/alerts_analysis/population_page.py` only. It does not
stage, revert, or reformat anything under `core/`. Feature 020's canvas host remains in the working
tree from the earlier slice. This slice's own file list does not include `core/`.

**Rationale**: The request says the canvas fallback works and cards already read. Reverting `core/`
would remove that host. "Do not edit `core/`" means this fix adds no core change.

**Alternatives considered**:

- *Revert `core/` so `git diff core/` is empty against HEAD*: rejected. That undoes the host the
  card tests now depend on.
