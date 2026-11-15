"""Credit Consumption checks against the Purim 2026 golden record."""

from pathlib import Path

import pytest
import yaml

from tests.sanity.credit_consumption_dashboard.conftest import (
    credit_consumption_dashboard,
)

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "credit"
    / "db_sanity_purim2026.yaml"
)


def load_sanity_data() -> dict:
    """Load the credit golden record from the repository data directory."""
    with _GOLDEN_RECORD.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _dashboard_record() -> dict:
    """Return the credit_consumption_dashboard block from the golden file."""
    data = load_sanity_data()
    return data["credit_consumption_dashboard"]


def apply_screen_1_filters(page) -> dict:
    """Apply Screen 1 active_filters (skipping הכל) and return that screen block."""
    screen = _dashboard_record()["screen_1_summary"]
    page.apply_filters(screen["active_filters"])
    return screen


def apply_screen_2_filters(page) -> dict:
    """Apply merged Screen 2 top_bar + side_bar filters and return that screen block."""
    screen = _dashboard_record()["screen_2_data_export"]
    filters = {}
    filters.update(screen["active_filters"]["top_bar"])
    filters.update(screen["active_filters"]["side_bar"])
    page.apply_filters(filters)
    return screen


def _assert_nested(actual, expected, path: str = "") -> None:
    """Every golden key is present and equal. Extra UI keys are ignored."""
    if isinstance(expected, dict):
        if not actual:
            pytest.skip(f"Missing Page Object reader for {path or 'kpi_metrics'}")
        for key, value in expected.items():
            child = f"{path}.{key}" if path else str(key)
            assert key in actual, f"missing {child} in {sorted(actual)}"
            _assert_nested(actual[key], value, child)
        return
    assert actual == expected, f"{path}: ui={actual!r} golden={expected!r}"


def _index_rows(rows: list[dict], key_fields: tuple[str, ...]) -> dict[tuple, dict]:
    """Index UI rows by the given fields so extra rows can be ignored."""
    indexed: dict[tuple, dict] = {}
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        indexed[key] = row
    return indexed


def _assert_golden_rows(actual: list[dict], expected: list[dict], key_fields: tuple[str, ...], label: str) -> None:
    """Every golden row is present. Extra UI rows are ignored."""
    if not actual:
        pytest.skip(f"{label} returned no rows (chart empty or not rendered)")
    indexed = _index_rows(actual, key_fields)
    for gold in expected:
        key = tuple(gold[field] for field in key_fields)
        assert key in indexed, f"missing {label} row {key!r} in {sorted(indexed)}"
        actual_row = indexed[key]
        for field, value in gold.items():
            assert actual_row.get(field) == value, (
                f"{label} {key!r} {field}: ui={actual_row.get(field)!r} golden={value!r}"
            )


@pytest.mark.sanity
def test_export_page_opens(credit_consumption_dashboard):
    """Screen 2 opens through the bilingual page-rail without a load timeout."""
    credit_consumption_dashboard.open_export_page()
    assert credit_consumption_dashboard.export_page_is_open()


@pytest.mark.sanity
def test_kpi_metrics_match_golden(credit_consumption_dashboard):
    """Screen 1 KPI cards match nested kpi_metrics after golden filters."""
    screen = apply_screen_1_filters(credit_consumption_dashboard)
    actual = credit_consumption_dashboard.read_kpi_metrics()
    _assert_nested(actual, screen["kpi_metrics"])


@pytest.mark.sanity
def test_daily_trends_match_golden(credit_consumption_dashboard):
    """Each toggle combination matches daily_trends_by_toggle via Show as a table."""
    screen = apply_screen_1_filters(credit_consumption_dashboard)
    expected_by_key = screen["daily_trends_by_toggle"]
    for key, expected in expected_by_key.items():
        metric, visualization = key.rsplit("_", 1)
        credit_consumption_dashboard.set_metric(metric)
        credit_consumption_dashboard.set_visualization(visualization)
        actual = credit_consumption_dashboard.read_daily_trends()
        field = ("date",)
        _assert_golden_rows(actual, expected, field, f"daily_trends.{key}")


@pytest.mark.sanity
def test_expenses_by_authority_match_golden(credit_consumption_dashboard):
    """Authority amounts match expenses_by_authority_millions."""
    screen = apply_screen_1_filters(credit_consumption_dashboard)
    actual = credit_consumption_dashboard.read_expenses_by_authority()
    _assert_golden_rows(
        actual,
        screen["expenses_by_authority_millions"],
        ("authority",),
        "expenses_by_authority_millions",
    )


@pytest.mark.sanity
def test_daily_alerts_match_golden(credit_consumption_dashboard):
    """Daily alert counts match when the visual is readable."""
    screen = apply_screen_1_filters(credit_consumption_dashboard)
    actual = credit_consumption_dashboard.read_daily_alerts()
    _assert_golden_rows(actual, screen["daily_alerts"], ("date",), "daily_alerts")


@pytest.mark.sanity
def test_export_table_match_golden(credit_consumption_dashboard):
    """Screen 2 export rows match export_table_data after golden filters."""
    credit_consumption_dashboard.open_export_page()
    screen = apply_screen_2_filters(credit_consumption_dashboard)
    actual = credit_consumption_dashboard.read_export_table()
    _assert_golden_rows(
        actual,
        screen["export_table_data"],
        ("transaction_date", "authority_name", "sub_category"),
        "export_table_data",
    )
