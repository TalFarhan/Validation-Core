import pytest
from playwright.sync_api import expect

@pytest.mark.sanity
def test_basic_district_and_category_filtering(dashboard, filter_data):
    """Verifies standard filters update KPIs logic correctly."""
    initial_total = dashboard.get_kpi_value("total")

    dashboard.select_district(filter_data["districts"]["dan"])
    dashboard.select_category(filter_data["categories"]["truck"])

    filtered_total = dashboard.get_kpi_value("total")
    assert filtered_total <= initial_total, "Filtered total should not exceed the unfiltered baseline."
    assert filtered_total < initial_total, "Applying district and category filters should reduce the total count."
    expect(dashboard.clear_filters_btn).to_be_visible()

@pytest.mark.sanity
def test_cross_category_filter_aggregation(dashboard, filter_data):
    """Validates combined filters progressively narrow KPI results."""
    initial_total = dashboard.get_kpi_value("total")

    dashboard.select_district(filter_data["districts"]["dan"])
    after_district = dashboard.get_kpi_value("total")

    dashboard.select_category(filter_data["categories"]["truck"])
    after_category = dashboard.get_kpi_value("total")

    dashboard.select_source(filter_data["sources"]["organic"])
    combined_total = dashboard.get_kpi_value("total")

    assert after_district <= initial_total
    assert after_category <= after_district
    assert combined_total <= after_category
    assert combined_total > 0, "Combined filters should still return a positive vehicle count."

@pytest.mark.sanity
def test_cascading_dropdown_dependency(dashboard, filter_data):
    """Ensures sub-filters dynamically adapt depending on top-level parent scope."""
    dashboard.select_district(filter_data["districts"]["south"])

    dashboard.sub_unit_dropdown.click()

    south_sub_unit = dashboard.option(filter_data["sub_units"]["south"], "SubUnit")
    expect(south_sub_unit).to_be_visible(timeout=5000)

    # Sub-unit belonging to a different district must not appear under South.
    dan_sub_unit = dashboard.option(filter_data["sub_units"]["dan"], "SubUnit")
    expect(dan_sub_unit).not_to_be_visible()

@pytest.mark.sanity
def test_clear_filter_functionality_restoration(dashboard, filter_data):
    """Confirms reset action restores default view parameters."""
    baseline_total = dashboard.get_kpi_value("total")

    dashboard.select_district(filter_data["districts"]["north"])
    dashboard.clear_all_applied_filters()

    restored_total = dashboard.get_kpi_value("total")
    assert restored_total == baseline_total, "Clearing filters should restore exact baseline totals."

@pytest.mark.sanity
def test_tab_navigation_functionality(dashboard):
    """Verifies each tab exposes its KPI card with a readable value."""
    tabs = [
        ("all", dashboard.total_vehicles_kpi, "total"),
        ("in_use", dashboard.in_use_kpi, "in_use"),
        ("allocated", dashboard.allocated_vehicles_kpi, "allocated"),
        ("withdrawn", dashboard.withdrawn_vehicles_kpi, "withdrawn"),
    ]

    for tab_name, kpi_card, kpi_metric in tabs:
        dashboard.click_tab(tab_name)
        expect(kpi_card).to_be_visible(timeout=dashboard.timeout)
        assert dashboard.get_kpi_value(kpi_metric) >= 0
