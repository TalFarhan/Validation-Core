# Phase 0 Research: Force the Date Field Click Past the Overlay

**Feature**: 032-date-input-force-click | **Date**: 2026-10-18

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Force the click inside `_commit_field`

**Decision**: Replace `field.click()` with `field.click(force=True)` in `_commit_field` on `pages/alerts_analysis/population_page.py`.

**Rationale**: After `clear_filters()`, a transparent `<div class="cdk-overlay-backdrop">` covers the date inputs. Playwright's default click waits until the field can receive the pointer, and that wait ends at 60 seconds. `force=True` sends the click to the field without that wait. The method still fills the value and presses Enter.

**Alternatives considered**:

- *Leave `field.click()`*: rejected. That is the 60-second timeout.
- *Press Escape or click the page body before every date fill*: rejected. The user asked for the forced click on this field. `_dismiss_overlay` already runs and does not remove this backdrop.

## Decision 2 — Leave `_dismiss_overlay` on `.cdk-overlay-backdrop-showing`

**Decision**: `_dismiss_overlay` stays a click on `.cdk-overlay-backdrop-showing`. This slice does not widen that selector to every `.cdk-overlay-backdrop`.

**Rationale**: The lingering node is `cdk-overlay-backdrop` without the `-showing` class. The existing dismiss already runs at the start of `_commit_field` and returns when no `-showing` backdrop is present. The forced click is the bypass for the backdrop that dismiss does not see.

**Alternatives considered**:

- *Also click `.cdk-overlay-backdrop`*: rejected. A click on the backdrop can close a menu the page still needs, and the user asked to force the field click.

## Decision 3 — Share the forced click with every `_commit_field` caller

**Decision**: Do not add a date-only click path. `_fill_input` (date labels) and `_fill_exact` (value range) both call `_commit_field`.

**Rationale**: The user pointed at `_commit_field`. The same backdrop can cover the value-range inputs. One forced click covers both.

**Alternatives considered**:

- *Force only `תאריך התחלה` and `תאריך סיום`*: rejected. That duplicates the commit steps and leaves the value-range click on the timing-out path.

## Decision 4 — Do not edit the invariant test

**Decision**: `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` stays as it is, including both `set_date_range("01/09/2026", "15/10/2026")` calls in `test_clear_restores_population_snapshot`.

**Rationale**: The test order is already clear, then the date range, then the mutations, then clear, then the date range again. The failure is the click under the backdrop, not the assertion. The user said the test logic is already right.

**Alternatives considered**:

- *Dismiss the overlay from the test*: rejected. The test must keep driving the page object, and this slice must not edit the test file.
- *Mark the test expected-fail*: rejected. The click is fixable on the page.
