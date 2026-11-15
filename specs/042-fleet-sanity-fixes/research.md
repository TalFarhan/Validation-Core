# Phase 0 Research: Fix Skipped Tests and Tooltips for Fleet DB Sanity

All Technical Context items are known from the existing code; there are no open
`NEEDS CLARIFICATION` markers. This file records the decisions that resolve the
"how" of each fix.

## Decision 1 — Where the skips come from

**Decision**: Treat the two named skips as two distinct root causes in
`tests/sanity/fleet_dashboard/contract.py::assert_chart_matches`.

**Rationale**: Reading the code:

- `assert_chart_matches` first builds `visible = {normalize_label(label): label}`
  from `dashboard.get_chart_segment_labels(chart_key)`. If no golden name folds
  into `visible`, it runs `pytest.skip("chart {key} exposed no golden labels")`.
  This is the credit-reason (`withdrawal`) path — a pie whose reason names do not
  currently fold to the golden keys.
- For each matched label it calls `dashboard.hover_chart_segment(...)`. When that
  raises `LoadTimeoutError` (no tooltip opened), it counts a timeout and, if
  `readable == 0 and timeouts >= 2`, runs
  `pytest.skip("chart {key} exposed golden labels but no tooltip appeared")`. A
  final `if readable == 0:` repeats the same skip. This is the unit/category path.

**Alternatives considered**: Deleting the skip guards. Rejected — the request
asks to *resolve* the skips into assertions while keeping the guards as a safety
net for a genuinely absent control (FR-004).

## Decision 2 — Making tooltips open (unit & category)

**Decision**: Keep `hover_chart_segment`'s hover-first strategy but (a) broaden
and order the segment targeting (SVG `<title>` glyph → largest shapes → axis/
legend geometry → plot scan, already present) and (b) add a **click-to-pin
fallback**: when hovering does not open a tooltip within the dynamic budget,
click the resolved segment glyph to pin a persistent Power BI tooltip, read it,
then dismiss. Only after the click fallback also fails may `LoadTimeoutError` be
raised. Return type stays `str`.

**Rationale**: Power BI hover hit-testing frequently fails to open a tooltip on
SVG bars/slices, which is exactly why the tests skip. A click pins the tooltip
reliably where a hover does not. The method already composes the shape/label
resolution helpers, so the fallback reuses `_segment_label_target` /
`_shapes_for_segment_label` rather than new locators.

**Alternatives considered**:
- Moving the fix into `core/components/chart.py`. Rejected — the constitution
  keeps report tooltips/drilldowns on the domain page; Layer 2 must stay
  report-agnostic (AC-001, Principle VII).
- CDP synthetic mouse events. Rejected — heavier and less portable than
  Playwright click on the already-resolved glyph.

## Decision 3 — Credit-reason label mapping

**Decision**: Fix the fold in the fleet sanity package so the pie's reason names
match the golden keys. `get_chart_segment_labels` already strips pure-numeric and
`"3 (50.0%)"` pie chrome; ensure the reason *name* portion still survives (do not
drop a `<title>` such as `אחר 3 (50%)` entirely — harvest the name). `normalize_label`
folds quotes/whitespace; extend only if a rendered reason cannot fold to the
golden key. As a last resort, add one additive label alias to the golden YAML.

**Rationale**: The golden YAML is the source of truth (Principle V/VII); the bug
is in the reader/normalization alignment, not the recorded numbers. Keeping the
fix in the mapping avoids changing any metric value.

**Alternatives considered**: Editing the golden counts. Rejected — values are a
recorded snapshot and are not wrong; only the label fold is.

## Decision 4 — Dynamic wait budgets

**Decision**: Replace the hard-coded `overall_deadline = time.monotonic() + 20.0`
and the small per-attempt literals in `hover_chart_segment` / `_hover_chart_shapes`
with values derived from `self.timeout` (e.g. an overall budget of
`self.timeout / 1000` capped sensibly, and per-attempt slices proportional to it).
Keep the `LoadTimeoutError` raise when the budget is exhausted.

**Rationale**: `self.timeout` is already `120_000` on the fleet page; deriving
budgets from it lets slow renders settle while preserving a real timeout. This
also removes magic numbers (FR-005).

**Alternatives considered**: Raising `self.timeout`. Rejected — the budget is
sufficient; the problem is fixed sub-budgets, not the overall ceiling.

## Decision 5 — Constitution III gate

**Decision**: Because the fleet domain page object is edited, run the fleet smoke
suite (`tests/ui/fleet_dashboard/`) to 100% green as part of the work, in addition
to the sanity module. Public fleet reader signatures/return types are unchanged.

**Rationale**: Principle III and the Quality Gates require the fleet smoke suite to
pass after any fleet page-object navigation/surface change. The change is internal
to chart readers, but the gate still applies and is cheap insurance.

**Alternatives considered**: Skipping the smoke run. Rejected — it is a hard gate.
