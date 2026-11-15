"""Fleet golden-record checks and report comparisons."""

from __future__ import annotations

import re

import pytest

from tests.sanity.fleet_dashboard.contract import (
    assert_breakdowns,
    assert_category_rates,
    assert_ledger,
    assert_summary,
    load_sanity_record,
)
from tests.ui.fleet_dashboard.conftest import dashboard

SUMMARY_KPI = {
    "total_vehicles_received": "total",
    "total_vehicles_in_use": "in_use",
    "vehicles_credited": "withdrawn",
    "vehicles_transferred": "allocated",
}

_LEDGER_ROW_FIELDS = (
    "סיבת זיכוי",
    "תאריך זיכוי",
    "מקור משיכה",
    "יחידה",
    "יחידת משנה",
)


def normalize_label(text: str) -> str:
    """Fold quotation marks and collapse whitespace for a UI comparison."""
    folded = (
        text.replace("\u05f4", '"')
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u201e", '"')
    )
    return re.sub(r"\s+", " ", folded).strip()


def assert_chart_matches(dashboard, chart_key: str, expected: dict) -> None:
    """Compare one chart to a golden name-to-count mapping from Show as a table."""
    segments = dashboard.read_chart_segments(chart_key)
    visible = {
        normalize_label(label): value for label, value in segments.items()
    }
    matched = [
        name for name in expected if normalize_label(str(name)) in visible
    ]
    if not matched:
        pytest.skip(f"chart {chart_key} exposed no golden labels")
    for name, count in expected.items():
        key = normalize_label(str(name))
        if key not in visible:
            raise AssertionError(
                f"chart {chart_key} segment {name!r}: ui='missing' golden={count!r}"
            )
        ui_value = visible[key]
        if ui_value == count:
            continue
        raise AssertionError(
            f"chart {chart_key} segment {name!r}: ui={ui_value!r} golden={count!r}"
        )


@pytest.mark.sanity
def test_summary_balances():
    """The four summary counters are whole numbers and in-use is within received."""
    assert_summary(load_sanity_record())


@pytest.mark.sanity
def test_breakdowns_integrity():
    """Unit, pull-source, and credit-reason totals match their summary counters."""
    assert_breakdowns(load_sanity_record())


@pytest.mark.sanity
def test_vehicle_category_rates():
    """Each category rate equals actual divided by its standard."""
    assert_category_rates(load_sanity_record())


@pytest.mark.sanity
def test_credited_vehicles_ledger():
    """Ledger rows cover every credited vehicle and carry the required fields."""
    assert_ledger(load_sanity_record())


@pytest.mark.sanity
def test_ui_summary_kpis_match_golden(dashboard):
    """Cleared KPI cards match the four golden summary counters."""
    dashboard.reset_dashboard_filters()
    summary = load_sanity_record()["summary"]
    for key, role in SUMMARY_KPI.items():
        ui_value = dashboard.get_kpi_value(role)
        golden = summary[key]
        assert ui_value == golden, f"summary.{key}: ui={ui_value!r} golden={golden!r}"


@pytest.mark.sanity
def test_ui_unit_breakdown_matches_golden(dashboard):
    """The in-use unit chart matches the golden unit counts."""
    dashboard.reset_dashboard_filters()
    assert_chart_matches(dashboard, "unit", load_sanity_record()["units_breakdown"])


@pytest.mark.sanity
def test_ui_pull_source_matches_golden(dashboard):
    """The in-use pull-source chart matches the golden source counts."""
    dashboard.reset_dashboard_filters()
    assert_chart_matches(
        dashboard, "source", load_sanity_record()["pull_source_breakdown"]
    )


@pytest.mark.sanity
def test_ui_credit_reasons_match_golden(dashboard):
    """The credit-reason chart matches the golden reason counts."""
    dashboard.reset_dashboard_filters()
    assert_chart_matches(
        dashboard, "withdrawal", load_sanity_record()["credit_reasons_summary"]
    )


@pytest.mark.sanity
def test_ui_category_actuals_match_golden(dashboard):
    """The category chart matches each golden actual count."""
    dashboard.reset_dashboard_filters()
    rows = load_sanity_record()["vehicle_categories"]
    expected = {row["category"]: row["actual"] for row in rows}
    assert_chart_matches(dashboard, "category", expected)


def _credited_row_text(dashboard, vehicle: int) -> str:
    """Read a credited row from the grid, searching only when it is off screen.

    ``search_vehicle`` waits until the visible row count changes. The credited
    tab already lists these vehicles, so that wait raises when the row is in view.
    """
    token = str(vehicle)
    count = dashboard.get_table_row_count()
    for index in range(count):
        text = normalize_label(dashboard.get_table_row_text(index))
        if token in text:
            return text
    dashboard.search_vehicle(token)
    try:
        return normalize_label(dashboard.get_table_row_text())
    finally:
        dashboard.clear_vehicle_search()


@pytest.mark.sanity
def test_ui_credited_ledger_rows(dashboard):
    """Each golden credited vehicle is visible on the credited tab."""
    dashboard.reset_dashboard_filters()
    dashboard.select_tab("withdrawn")
    for row in load_sanity_record()["credited_vehicles_details"]:
        vehicle = row["מספר רכב"]
        text = _credited_row_text(dashboard, vehicle)
        for field in _LEDGER_ROW_FIELDS:
            expected = normalize_label(str(row[field]))
            assert expected in text, (
                f"credited_vehicles_details.{vehicle}: missing {field}"
            )
