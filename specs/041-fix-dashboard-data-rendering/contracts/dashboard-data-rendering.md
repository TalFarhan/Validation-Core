# Contract: Dashboard Data Rendering (Alerts + Status Picture)

Page-object and test-setup contract for resolving the skipped chart tests and
`LoadTimeoutError`. No `core/` contract changes.

## Page object: `AlertsPopulationPage` (`pages/alerts_analysis/population_page.py`)

### `_report_ready_locator(self) -> Locator` — CHANGED

- **Before**: returns `self._iframe_phrase_locator(self.DISTRICT_CHART)`.
- **After**: returns `self._iframe_phrase_locator(self.TOTAL_CARD)`.
- **Guarantee**: The anchor is visible on Screen 2 regardless of the active date filter.
- **Preserved**: `before_report_ready_check()` still inspects `DISTRICT_CHART` to decide the
  Screen 1 → Screen 2 page switch. `navigate()` still raises `LoadTimeoutError` when the
  anchor never appears.
- **Unchanged signatures**: `set_date_range`, `set_district_aggregation`,
  `set_hierarchy_level`, `read_district_labels`, `read_card`, `clear_filters`.

## Page object: `StatusPicturePage` (`pages/status_picture/status_picture_page.py`)

### `select_operation(self, name: str) -> None` — NEW (additive)

- **Input**: an operation option label (e.g. `עם כלביא`), supplied by the caller.
- **Behavior**:
  1. Dismiss any overlay.
  2. Capture the current warning-zones gauge value.
  3. `self._slicer.select("date_range", name)`.
  4. Wait until the warning-zones gauge changes and settles (`_wait_until_gauge_changes`).
- **Failure**: if `name` is not a selectable option, raise `AssertionError` naming the
  missing operation (the `Slicer.select` failure is surfaced, not swallowed).
- **Note**: `set_date_range` retains its existing behavior for non-golden callers. The
  golden path no longer depends on `_OPERATION_RANGES` or `_date_fields_visible()`.

### `_report_ready_locator(self) -> Locator` — UNCHANGED

- Returns the warning-zones gauge card anchor (`UNDER_FIRE_CARD`), already filter-independent
  and Screen-1-specific. Documented here as compliant with the "consistently visible element"
  requirement; no code change.

## Test setup contracts

### `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`

- Every chart-reading test MUST call `_apply_golden_range(population_dashboard)` (which reads
  `screen_2_alerts_analysis.date_range` and calls `set_date_range`) before any reader. This is
  already present; the slice audits and keeps it. No date literal appears in a test body.

### `tests/sanity/status_picture_dashboard/test_status_picture_validation.py`

- `_apply_golden_range(page)` — CHANGED:
  - Reads `screen["operation"]` from the golden record.
  - Calls `page.select_operation(screen["operation"])` instead of `page.set_date_range(start, end)`.
  - Returns the Screen 1 block, same as today.
- The `_require_card` / empty-reader skip guards remain unchanged (safety net).

## Golden record contract

`data/alerts/db_sanity_am_kalavi.yaml`:

- Add `operation: "עם כלביא"` under `dashboard_sanity_checks.screen_1_status_picture`.
- No existing metric or map value changes.

## Invariants

- `core/portal`, `core/components`, and the root `conftest.py` are not edited.
- No fleet module is edited; the fleet smoke gate is not triggered.
- Public reader names and return types are unchanged; `select_operation` is additive.
- Comments inside new or edited functions are English.
