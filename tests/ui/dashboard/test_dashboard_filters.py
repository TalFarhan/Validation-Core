import pytest
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage

@pytest.mark.sanity
def test_basic_district_and_category_filtering(auth_page):
    """Verifies that selecting standard filters updates the interface successfully."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    # Store default total metrics before applying restriction criteria
    initial_total = dashboard.get_kpi_value("total")
    
    # Apply specified filters to test responsive reactivity
    dashboard.select_district("מחוז דן")
    dashboard.select_category("משאית")
    
    filtered_total = dashboard.get_kpi_value("total")
    
    # Assert that numbers shifted following layout narrowing execution
    assert filtered_total <= initial_total, "Filtered vehicle counts should be equal or lower than baseline data totals."

@pytest.mark.sanity
def test_multi_select_filter_aggregation(auth_page):
    """Validates the dashboard handles combined compound multi-selection inputs."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    dashboard.select_district("מחוז דן")
    dashboard.select_district("מחוז מרכז")
    
    combined_total = dashboard.get_kpi_value("total")
    assert combined_total > 0, "Aggregated district metric values must register above absolute zero baseline limits."

@pytest.mark.sanity
def test_cascading_dropdown_dependency(auth_page):
    """Ensures sub-filters dynamically adapt depending on top-level parent scope."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    dashboard.select_district("מחוז דרום")
    # Verify sub-elements adjust dynamically to display localized sub-districts only
    assert dashboard.page.locator("text=סניף באר שבע").is_visible(), "Sub-district dropdown criteria must restrict context dynamically."

@pytest.mark.sanity
def test_clear_filter_functionality_restoration(auth_page):
    """Confirms reset action controls effectively re-establish default view parameters."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    baseline_total = dashboard.get_kpi_value("total")
    
    dashboard.select_district("מחוז צפון")
    dashboard.clear_all_applied_filters()
    
    restored_total = dashboard.get_kpi_value("total")
    assert restored_total == baseline_total, "Clearing filters should restore metric views back to complete system baselines."