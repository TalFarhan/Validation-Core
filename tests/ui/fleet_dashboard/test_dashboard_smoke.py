import pytest
from playwright.sync_api import expect

from tests.helpers.dashboard_validation import KPI_TYPES


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
