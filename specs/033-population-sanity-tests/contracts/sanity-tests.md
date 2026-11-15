# Contract: Population Sanity Tests

**Feature**: 033-population-sanity-tests | **Date**: 2026-10-19

New tests only. `tests/ui/` and `core/` are not edited. The golden file is not edited. The population page is not edited.

## Package

| Path | Content |
|------|---------|
| `tests/sanity/__init__.py` | Empty. |
| `tests/sanity/alerts_analysis_dashboard/__init__.py` | Empty. |
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | The module below. |

## Imports

The test module imports:

- `pytest`
- `yaml`
- `Path` from `pathlib`
- `population_dashboard` from `tests.ui.alerts_analysis_dashboard.conftest`
- `datetime` for the date translation

## `load_sanity_data() -> dict`

Opens `Path(__file__).resolve().parents[3] / "data" / "alerts" / "db_sanity_am_kalavi.yaml"` as UTF-8 and returns `yaml.safe_load`.

## `to_page_date(iso_date: str) -> str`

Parses `YYYY-MM-DD` and returns `DD/MM/YYYY`.

| Input | Output |
|-------|--------|
| `2026-09-01` | `01/09/2026` |
| `2025-10-18` | `18/10/2025` |

## `read_population_cards(page) -> dict`

Returns a dict with keys `total`, `warned`, and `unprotected`. Each value is `page.read_card(role)`.

## `test_global_metrics_match_db(population_dashboard)`

Marked `@pytest.mark.sanity`.

1. Load the golden dict.
2. Read `data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]["metrics"]`.
3. Call `population_dashboard.clear_filters()`.
4. `cards = read_population_cards(population_dashboard)`.
5. Assert `cards['total']` equals `metrics["total_population_all_time"]["expected_value"]`.
6. Assert `cards['unprotected']` equals `metrics["unprotected_population"]["expected_value"]`.

The function does not call `set_date_range`.

## `test_filtered_population_matches_db(population_dashboard)`

Marked `@pytest.mark.sanity`.

1. Load the golden dict.
2. Read `data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]`.
3. `start = to_page_date(screen["date_range"]["start"])`.
4. `end = to_page_date(screen["date_range"]["end"])`.
5. Call `population_dashboard.set_date_range(start, end)`.
6. `cards = read_population_cards(population_dashboard)`.
7. Assert `cards['warned']` equals `screen["metrics"]["alerted_population_selected_range"]["expected_value"]`.

## Comments

Comments inside functions are English. No Hebrew comments in this module.

## Unchanged

- `data/alerts/db_sanity_am_kalavi.yaml`
- `pages/alerts_analysis/population_page.py`
- `tests/ui/`
- `core/`
- `db/clients/alerts.py`

## Examples (normative)

| Step | Call | Expected card |
|------|------|----------------|
| Filters cleared | `clear_filters()` | `cards['total'] == 10142584` |
| Filters cleared | `clear_filters()` | `cards['unprotected'] == 3389879` |
| Range set | `set_date_range("01/09/2026", "18/10/2025")` | `cards['warned'] == 9474` |

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Both tests collect | `python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py --collect-only` |
| The three golden values are the assertions | review of `test_data_validation.py` against this contract |
| `tests/ui/` and `core/` are untouched | review of the edit list |
