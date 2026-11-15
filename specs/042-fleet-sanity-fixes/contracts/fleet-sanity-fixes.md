# Contract: Fleet DB Sanity Tooltip & Label Fixes

Page-object and test-package contract for resolving the skipped fleet chart tests.
No `core/` contract changes. No alerts/status change.

## Page object: `MainDashboardPage` (`pages/fleet_dashboard/main_dashboard_page.py`)

### `hover_chart_segment(self, chart_key, label, *, expected_value=None) -> str` — CHANGED (internal)

- **Signature**: unchanged. Return type `str` unchanged.
- **Before**: hover-only strategy with a hard-coded `overall_deadline` of 20s and
  small fixed per-attempt budgets; raises `LoadTimeoutError` when no tooltip opens.
- **After**:
  1. Resolve the segment target as today (SVG `<title>` glyph → largest shapes →
     axis/legend geometry → plot scan).
  2. Hover with per-attempt budgets **derived from `self.timeout`** (not literals).
  3. If no tooltip opens, **click-to-pin fallback**: click the resolved glyph to
     open a persistent tooltip, read it, then dismiss.
  4. Only after both hover and click fallback fail within the dynamic overall
     budget, raise `LoadTimeoutError` (preserved).
- **Guarantee**: returns the matched tooltip text for a renderable segment; a
  never-rendering tooltip still raises `LoadTimeoutError`.

### `get_chart_segment_labels(self, chart_key) -> list[str]` — CHANGED (internal)

- **Signature**: unchanged. Return type `list[str]` unchanged.
- **Change**: ensure pie reason names survive collection — exclude only pure
  numeric and `"n (x%)"` data chrome, do not drop the reason text that carries the
  name. No fleet label is moved into `core/`.

### Private helpers — ADDITIVE

- A private click-to-pin helper (e.g. `_pin_segment_tooltip`) MAY be added. It is
  private, fleet-only, and composes existing target resolution; no public API.

### Unchanged

- `parse_tooltip_entries() -> dict[str, int]`, `dismiss_tooltip()`,
  `get_kpi_value()`, `reset_dashboard_filters()`, `_report_ready_locator()`, and
  the `navigate()`/`reload_and_measure_ready_ms()` contract are unchanged.

## Test package: `tests/sanity/fleet_dashboard/`

### `contract.py::assert_chart_matches(dashboard, chart_key, expected)` — CHANGED

- Corrects the credit-reason mapping so both golden reasons fold to rendered
  labels and the test reaches its hover/assert loop.
- Keeps the two `pytest.skip` guards as a safety net for a genuinely absent
  control (no golden labels at all; no tooltip for a truly missing segment).
- No golden value is read into a literal in the test body.

### `contract.py::normalize_label(text)` — CHANGED (if needed)

- Extends folding only as needed so a rendered reason name matches the golden key.
  Quote and whitespace folding remain.

### `test_db_sanity.py` — AUDIT/EDIT

- `test_ui_credit_reasons_match_golden` and `test_ui_category_actuals_match_golden`
  reach pass/fail instead of skip when data is present. No date/value literal in a
  test body; values come from `load_sanity_record()`.

## Golden record contract

`data/fleet/db_sanity_all.yaml`:

- Metric values (`summary`, `units_breakdown`, `pull_source_breakdown`,
  `vehicle_categories`, `credit_reasons_summary`, `credited_vehicles_details`) are
  UNCHANGED.
- An additive credit-reason **label alias** MAY be added only if normalization
  cannot fold a rendered reason to its golden key. No count changes.

## Invariants

- `core/portal`, `core/components` (including `core/components/chart.py`), and the
  root `conftest.py` are not edited.
- No alerts or status-picture module is edited.
- Public fleet reader names and return types are unchanged; new helpers are private.
- The fleet smoke suite (`tests/ui/fleet_dashboard/`) passes at 100% after the edit.
- Comments inside new or edited functions are English.
