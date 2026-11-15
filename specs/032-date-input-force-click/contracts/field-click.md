# Contract: Force the Date Field Click Past the Overlay

**Feature**: 032-date-input-force-click | **Date**: 2026-10-18

`set_date_range` and `clear_filters` keep their names and arguments. `core/` is not edited. The invariant test is not edited.

## `_commit_field`

1. Call `_dismiss_overlay()`.
2. Expect the field to be visible within `self.timeout`.
3. Click the field with `field.click(force=True)`.
4. `field.fill(value)`.
5. `field.press("Enter")`.
6. Call `_dismiss_overlay()` again.

## Callers

- `_fill_input` still finds `input[aria-label^='תאריך התחלה']` and `input[aria-label^='תאריך סיום']` and passes each field to `_commit_field`.
- `_fill_exact` still passes its field to `_commit_field`.
- `set_between_dates` and `set_date_range` stay the public date calls. `set_date_range` still waits until the total card repeats.

## Unchanged

- `_dismiss_overlay` still clicks `.cdk-overlay-backdrop-showing` only.
- `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` stays as it is.
- `tests/ui/alerts_analysis_dashboard/population_snapshot.py` stays as it is.
- `core/` stays as it is.
- `test_clear_restores_population_snapshot` does not gain `pytest.mark.xfail`.

## Examples (normative)

| After `clear_filters()` | Next date click |
|-------------------------|-----------------|
| `div.cdk-overlay-backdrop` covers the input | `field.click()` waits 60 seconds |
| Same backdrop | `field.click(force=True)` focuses the input, then fill and Enter run |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| The clear-restore test still passes | `test_clear_restores_population_snapshot` |
| The test file and `core/` are untouched | review of the edit list |
