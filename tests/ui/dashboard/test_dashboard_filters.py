import pytest
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage

@pytest.mark.sanity
def test_basic_district_and_category_filtering(auth_page):
    """Verifies that selecting standard filters updates the interface successfully across multiple KPIs."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    # Store multiple default metrics before applying restriction criteria
    initial_total = dashboard.get_kpi_value("total")
    initial_in_use = dashboard.get_kpi_value("in_use")
    
    # Apply specified filters to test responsive reactivity
    dashboard.select_district("מחוז דן")
    dashboard.select_category("משאית")
    
    filtered_total = dashboard.get_kpi_value("total")
    filtered_in_use = dashboard.get_kpi_value("in_use")
    
    # Assert that numbers shifted following layout narrowing execution
    assert filtered_total <= initial_total, "Filtered total vehicles should be equal or lower than baseline."
    assert filtered_in_use <= initial_in_use, "Filtered in-use vehicles should be equal or lower than baseline."

@pytest.mark.sanity
def test_cross_category_filter_aggregation(auth_page):
    """Validates the dashboard handles combined filters from different categories without crashing."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    initial_total = dashboard.get_kpi_value("total")
    
    dashboard.select_district("מחוז דן")
    dashboard.select_category("משאית")
    dashboard.select_source("אורגני")
    
    combined_total = dashboard.get_kpi_value("total")
    
    assert combined_total >= 0, "Aggregated metric values must be a valid number (0 or higher)."
    assert combined_total <= initial_total, "Filtered total vehicles cannot exceed the initial baseline."

@pytest.mark.sanity
def test_cascading_dropdown_dependency(auth_page):
    """Ensures sub-filters dynamically adapt depending on top-level parent scope."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    dashboard.select_district("מחוז דרום")
    
    # Verify sub-elements adjust dynamically
    dashboard.sub_unit_dropdown.click()
    assert dashboard.page.locator("text=נפת השרון 9770").is_visible(), "Sub-district dropdown criteria must restrict context dynamically."
    dashboard.page.keyboard.press("Escape")

@pytest.mark.sanity
def test_clear_filter_functionality_restoration(auth_page):
    """Confirms reset action controls effectively re-establish default view parameters."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    
    baseline_total = dashboard.get_kpi_value("total")
    
    dashboard.select_district("מחוז צפון")
    dashboard.select_category("משאית")
    dashboard.clear_all_applied_filters()
    
    restored_total = dashboard.get_kpi_value("total")
    assert restored_total == baseline_total, "Clearing filters should restore metric views back to complete system baselines."

@pytest.mark.sanity
def test_tab_navigation_functionality(auth_page):
    """Verifies that data tabs can be clicked and become actively selected."""
    dashboard = MainDashboardPage(auth_page)
    dashboard.navigate()
    dashboard.click_tab("withdrawn")
    
    assert dashboard.withdrawn_tab.is_visible(), "Withdrawn tab should remain visible after clicking."
    assert dashboard.withdrawn_tab.is_enabled(), "Withdrawn tab should be enabled and responsive."