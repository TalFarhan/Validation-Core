# Feature Specification: Force the Date Field Click Past the Overlay

**Feature Branch**: `feature/reportportal-integration` (spec directory `032-date-input-force-click`; git checkout stays put)

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "After clear_filters, a transparent cdk-overlay-backdrop intercepts the next click on the date inputs and the click times out at 60 seconds. Change field.click() in _commit_field to field.click(force=True). Do not edit the invariant test."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Date inputs accept the range after a clear (Priority: P1)

A validation author clears the population filters and then sets `01/09/2026` through `15/10/2026`. A transparent overlay backdrop is still in the report frame. The date fields still receive focus and the range is committed.

**Why this priority**: `test_clear_restores_population_snapshot` calls `clear_filters()` and then `set_date_range`. The next `field.click()` waits on a `<div class="cdk-overlay-backdrop">` and times out at 60 seconds. The test logic is already the check this slice must keep.

**Independent Test**: `test_clear_restores_population_snapshot` passes with its current assertions. The date commit uses `field.click(force=True)`. The test file is unchanged.

**Acceptance Scenarios**:

1. **Given** `clear_filters()` has left a `cdk-overlay-backdrop` over the report, **When** `set_date_range` fills `תאריך התחלה` and `תאריך סיום`, **Then** each field is clicked with `force=True` and the value is filled.
2. **Given** the click is forced, **When** the field is committed, **Then** the method still fills the value and presses Enter.
3. **Given** the invariant test file, **When** this story is implemented, **Then** `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is unchanged.

---

### Edge Cases

- `_dismiss_overlay` still runs before the click. It only clicks `.cdk-overlay-backdrop-showing`. A backdrop without that class remains, and `force=True` is what gets the click to the field.
- `_commit_field` is also used by the value-range inputs. Those clicks use `force=True` too, because they share this method.
- The test file, `core/`, and `population_snapshot.py` are not modified.
- No `pytest.mark.xfail` is added.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `_commit_field` in `pages/alerts_analysis/population_page.py` MUST click the field with `field.click(force=True)`.
- **FR-002**: `_commit_field` MUST still call `_dismiss_overlay()` before the click, then `field.fill(value)` and `field.press("Enter")`, then `_dismiss_overlay()` again.
- **FR-003**: `set_date_range` and `set_between_dates` MUST keep their names and arguments. They MUST keep reaching the date inputs through `_fill_input` and `_commit_field`.
- **FR-004**: This feature MUST NOT modify `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`.
- **FR-005**: This feature MUST NOT modify `core/` or `tests/ui/alerts_analysis_dashboard/population_snapshot.py`.
- **FR-006**: The slice MUST NOT add `pytest.mark.xfail` to `test_clear_restores_population_snapshot`.

### Key Entities

- **Date field**: The input whose `aria-label` starts with `תאריך התחלה` or `תאריך סיום`.
- **Lingering backdrop**: A `div.cdk-overlay-backdrop` in the report frame that is still present after `clear_filters()` and is not removed by `_dismiss_overlay`.
- **Forced click**: `field.click(force=True)` inside `_commit_field`, so the backdrop does not consume the 60-second click wait.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 is unchanged.
- **AC-002**: The population page still composes `ReportShell`.
- **AC-003**: Report-ready state stays the district chart.
- **AC-004**: `set_date_range`, `clear_filters`, and `chart_total` keep their names and arguments.
- **AC-005**: `cdk-overlay-backdrop` stays a page-local locator. It is not added under `core/`.
- **AC-006**: No SQL change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `test_clear_restores_population_snapshot` passes.
- **SC-002**: The date commit no longer waits out a 60-second click intercepted by `cdk-overlay-backdrop`.
- **SC-003**: The diff for this slice contains `_commit_field` in `pages/alerts_analysis/population_page.py` and no change under `core/` or in `test_population_invariants.py`.

## Assumptions

- The timeout is Playwright's click actionability wait on `field.click()` inside `_commit_field`, after `clear_filters()`.
- The backdrop that remains does not match `.cdk-overlay-backdrop-showing`, so the existing dismiss click does not remove it.
- `force=True` delivers the click to the date input while that backdrop is up.
- The clear-restore test already applies `set_date_range("01/09/2026", "15/10/2026")` after each `clear_filters()`. This slice does not change that order.
- Inline comments in edited Python stay English.
