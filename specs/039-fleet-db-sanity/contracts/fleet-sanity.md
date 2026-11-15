# Contract: Fleet DB Sanity

**Feature**: 039-fleet-db-sanity | **Date**: 2026-10-29

New sanity package plus a citation-suffix repair in the golden file. `core/`, the fleet page, `tests/ui/`, `tests/e2e/`, and `db/clients/fleet.py` are not edited.

## Package

| Path | Content |
|------|---------|
| `tests/sanity/fleet_dashboard/__init__.py` | Empty. |
| `tests/sanity/fleet_dashboard/contract.py` | Pure loader and checks. No Playwright. |
| `tests/sanity/fleet_dashboard/test_db_sanity.py` | Structural tests and UI tests. |

## Golden file repair

In `data/fleet/db_sanity_all.yaml`, each rate line changes from `"…%"[cite: 1]` to a quoted percent. No count changes.

| Category | Rate after repair |
|----------|-------------------|
| אוטובוס | `"0.57%"` |
| אמבולנס | `"16.92%"` |
| אמצעי הובלה | `"34.24%"` |
| רכב קל | `"10.74%"` |

## `load_sanity_record(path: Path | None = None) -> dict`

Default path is `Path(__file__).resolve().parents[3] / "data" / "fleet" / "db_sanity_all.yaml"`. Opens UTF-8. Returns `yaml.safe_load`. Raises `AssertionError` naming any missing top-level key among `summary`, `units_breakdown`, `pull_source_breakdown`, `vehicle_categories`, `credit_reasons_summary`, `credited_vehicles_details`.

## `assert_summary(record: dict) -> None`

Reads `record["summary"]` only.

1. Require `total_vehicles_in_use`, `total_vehicles_received`, `vehicles_transferred`, `vehicles_credited`.
2. Each is an `int` and `>= 0`. A `bool` is rejected.
3. `total_vehicles_in_use <= total_vehicles_received`.
4. Do not compare received to any sum of the other three.

Failure shape: `summary.<key>: actual=<value> expected=<rule>`.

## `assert_breakdowns(record: dict) -> None`

| Section | Expected sum |
|---------|----------------|
| `units_breakdown` | `summary.total_vehicles_in_use` |
| `pull_source_breakdown` | `summary.total_vehicles_in_use` |
| `credit_reasons_summary` | `summary.vehicles_credited` |

Every value is an `int` `>= 0`. Keys are taken from the mapping. Failure shape: `<section>: sum=<n> expected <summary_key>=<n>`.

## `assert_category_rates(record: dict) -> None`

For each row in `vehicle_categories`:

1. Require non-empty `category`, int `actual` `>= 0`, int `standard` `>= 1`, and a `rate` string.
2. Parse the leading percent. Ignore a trailing `[cite: …]` if one is still attached to the string.
3. Computed rate is `(actual / standard) * 100`, quantized half-up to two decimal places, then formatted with a `%` suffix.
4. Stored rate must equal that string.

The sum of `actual` must equal `summary.total_vehicles_received`. Category names are not hard-coded.

Failure shape: `vehicle_categories.<category>: rate=<stored> computed=<rate> (actual=<a>, standard=<s>)`.

## `assert_ledger(record: dict) -> None`

Required fields, in order: `סיבת זיכוי`, `תאריך זיכוי`, `מקור משיכה`, `יחידה`, `יחידת משנה`, `מספר רכב`.

1. `len(credited_vehicles_details) == summary.vehicles_credited`.
2. Each required text field is a non-empty string. `תאריך זיכוי` matches `DD/MM/YYYY`.
3. `מספר רכב` is an `int` and is unique.
4. `סיבת זיכוי` is a key of `credit_reasons_summary`.
5. Counts of `סיבת זיכוי` equal `credit_reasons_summary` exactly (no extra reason, no missing reason).
6. Do not join `מקור משיכה` to `pull_source_breakdown` or `יחידה` to `units_breakdown`.

Failure shape: `credited_vehicles_details.<מספר רכב>: missing <field>` or `…: actual=<value> expected=<value>`.

## UI binding (test module only)

`contract.py` does not contain this table.

| Golden section | Page call |
|----------------|-----------|
| `summary.total_vehicles_received` | `get_kpi_value("total")` |
| `summary.total_vehicles_in_use` | `get_kpi_value("in_use")` |
| `summary.vehicles_credited` | `get_kpi_value("withdrawn")` |
| `summary.vehicles_transferred` | `get_kpi_value("allocated")` |
| `units_breakdown` | chart `unit` |
| `pull_source_breakdown` | chart `source` |
| `credit_reasons_summary` | chart `withdrawal` |
| `vehicle_categories[].actual` | chart `category` |
| `credited_vehicles_details` | `select_tab("withdrawn")`, then `search_vehicle(str(מספר רכב))` |

Each UI test calls `reset_dashboard_filters()` first and does not call `apply_filters`.

Label compare folds `״` and `"` to `"`, strips, and collapses whitespace. The failure message prints the original UI string and the original golden string.

Chart tests: if no golden key is visible, `pytest.skip` with the chart key. If any golden key is visible, every golden key must match. A mismatch message includes the chart key, the segment, `ui=`, and `golden=`.

Ledger UI: the row text must contain the reason, date, pull source, unit, and subunit for that vehicle number. A missing piece names the vehicle number and the field.

## Tests

All marked `@pytest.mark.sanity`. Comments inside functions are English.

| Test | Fixture | Behavior |
|------|---------|----------|
| `test_summary_balances` | none | `assert_summary` |
| `test_breakdowns_integrity` | none | `assert_breakdowns` |
| `test_vehicle_category_rates` | none | `assert_category_rates` |
| `test_credited_vehicles_ledger` | none | `assert_ledger` |
| `test_ui_summary_kpis_match_golden` | `dashboard` | Four KPI cards |
| `test_ui_unit_breakdown_matches_golden` | `dashboard` | Chart `unit` |
| `test_ui_pull_source_matches_golden` | `dashboard` | Chart `source` |
| `test_ui_credit_reasons_match_golden` | `dashboard` | Chart `withdrawal` |
| `test_ui_category_actuals_match_golden` | `dashboard` | Chart `category`, actuals only |
| `test_ui_credited_ledger_rows` | `dashboard` | Withdrawn tab, one search per row |

The UI tests import `dashboard` from `tests.ui.fleet_dashboard.conftest`.

## Unchanged

- `pages/fleet_dashboard/main_dashboard_page.py`
- `tests/ui/`
- `tests/e2e/`
- `db/clients/fleet.py`
- `core/`
- `tests/helpers/`
- `tests/conftest.py`
- `data/alerts/db_sanity_am_kalavi.yaml`
