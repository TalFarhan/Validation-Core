import pytest
from playwright.sync_api import expect

from config.settings import settings
from tests.ui.fleet_dashboard.dashboard_validation import KPI_TYPES

@pytest.mark.sanity
def test_dashboard_loads_within_sla(dashboard):
    """Authenticated reload must show the total KPI within the load SLA (default 5s)."""
    elapsed_ms = dashboard.reload_and_measure_ready_ms()
    assert elapsed_ms <= settings.DASHBOARD_LOAD_SLA_MS, (
        f"Dashboard load took {elapsed_ms}ms; "
        f"SLA is {settings.DASHBOARD_LOAD_SLA_MS}ms "
        f"(set DASHBOARD_LOAD_SLA_MS to override)"
    )
    assert dashboard.get_kpi_value("total") >= 0

@pytest.mark.sanity
def test_dashboard_loads_all_kpi_cards(dashboard):
    """All KPI cards must load with non-negative values."""
    for kpi_type in KPI_TYPES:
        assert dashboard.get_kpi_value(kpi_type) >= 0

@pytest.mark.sanity
def test_iframe_and_filters_visible(dashboard):
    """Core iframe and slicers must be visible on load."""
    expect(dashboard.page.locator("main iframe")).to_be_visible(timeout=dashboard.timeout)
    expect(dashboard.district_dropdown).to_be_visible()
    expect(dashboard.sub_unit_dropdown).to_be_visible()
    expect(dashboard.source_dropdown).to_be_visible()
    expect(dashboard.category_dropdown).to_be_visible()
    expect(dashboard.clear_filters_btn).to_be_visible()

@pytest.mark.sanity
def test_all_charts_visible_on_load(dashboard):
    """All chart sections must render on initial load."""
    for chart_key in ("source", "unit", "category", "withdrawal"):
        dashboard.assert_chart_visible(chart_key)

@pytest.mark.sanity
def test_vehicle_table_visible_on_load(dashboard):
    """The vehicle table must be visible on initial load."""
    expect(dashboard.vehicle_table).to_be_visible(timeout=dashboard.timeout)

@pytest.mark.sanity
def test_dashboard_updated_within_24_hours(dashboard):
    """Last-refresh caption on the open report must be within 24 hours."""
    dashboard.verify_freshness()
