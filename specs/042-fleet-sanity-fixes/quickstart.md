# Quickstart: Fix Skipped Tests and Tooltips for Fleet DB Sanity

## What this slice does

Turns two skipped fleet DB-sanity chart tests into real assertions:

- `test_ui_category_actuals_match_golden` (category chart) and
  `test_ui_unit_breakdown_matches_golden` (unit chart) — were skipping because the
  Power BI tooltip never opened.
- `test_ui_credit_reasons_match_golden` (credit-reason pie) — was skipping because
  the golden reasons did not fold to the rendered labels.

## Prerequisites

- Portal auth configured (the UI tests open the live Power BI report).
- Python env with `pytest`, `PyYAML`, Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by the existing fleet fixtures.

## Files you will touch

- `pages/fleet_dashboard/main_dashboard_page.py` — harden `hover_chart_segment`
  (robust hover + click-to-pin fallback); derive hover/tooltip budgets from
  `self.timeout`; keep reason names in `get_chart_segment_labels`.
- `tests/sanity/fleet_dashboard/contract.py` — correct the credit-reason mapping in
  `assert_chart_matches` / `normalize_label`; keep the skip guards.
- `tests/sanity/fleet_dashboard/test_db_sanity.py` — audit the two named tests.
- `data/fleet/db_sanity_all.yaml` — optional additive label alias only (no values).

## Do NOT touch

- `core/portal/`, `core/components/` (including `core/components/chart.py`).
- Any alerts or status-picture module.
- The root `conftest.py`.
- Any golden metric value.

## Run it

```powershell
# The two target tests (needs auth)
pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_credit_reasons_match_golden -m sanity
pytest tests/sanity/fleet_dashboard/test_db_sanity.py::test_ui_category_actuals_match_golden -m sanity

# Full fleet sanity module
pytest tests/sanity/fleet_dashboard/test_db_sanity.py -m sanity

# Constitution III gate — fleet smoke must stay 100% green (fleet page was edited)
pytest tests/ui/fleet_dashboard/
```

## Done when

- Both named tests report pass/fail (not skip) with data present.
- A never-rendering tooltip still raises `LoadTimeoutError` (guards preserved).
- Hover/tooltip budgets are computed from `self.timeout`, not fixed literals.
- The fleet smoke suite is 100% green.
- No alerts/status/`core/`/root-conftest edit; no golden metric value changed.
- In-function comments are English.
