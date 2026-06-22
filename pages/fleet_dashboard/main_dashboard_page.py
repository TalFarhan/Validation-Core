from playwright.sync_api import Page

class MainDashboardPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://portal.agamimp.net/applications/dashboard/fleet"
        
        # Locators for filters and dropdowns
        self.district_dropdown = page.locator("div.filter-dropdown", has_text="מחוז")
        self.category_dropdown = page.locator("div.filter-dropdown", has_text="קטגוריה")
        self.clear_filters_btn = page.locator("button", has_text="נקה מסננים")
        
        # Locators for KPI metric summary cards
        self.total_vehicles_kpi = page.locator("div.kpi-card", has_text="סה\"כ רכבים")
        self.in_use_kpi = page.locator("div.kpi-card", has_text="רכבים בשימוש")

    def navigate(self):
        """Navigates to the fleet dashboard application web page."""
        self.page.goto(self.url)
        self.page.wait_for_load_state("networkidle")

    def select_district(self, district_name: str):
        """Selects a specific district filter options from the dropdown list."""
        self.district_dropdown.click()
        self.page.locator(f"role=option[name='{district_name}']").click()
        self.page.wait_for_load_state("networkidle")

    def select_category(self, category_name: str):
        """Selects a specific vehicle classification type from the filter list."""
        self.category_dropdown.click()
        self.page.locator(f"role=option[name='{category_name}']").click()
        self.page.wait_for_load_state("networkidle")

    def get_kpi_value(self, metric_type: str) -> int:
        """Retrieves numerical values displayed within selected dashboard metric blocks."""
        if metric_type == "total":
            text_value = self.total_vehicles_kpi.locator(".kpi-number").text_content()
        elif metric_type == "in_use":
            text_value = self.in_use_kpi.locator(".kpi-number").text_content()
        else:
            raise ValueError(f"Unknown metric representation targeted: {metric_type}")
        
        return int(text_value.strip().replace(",", ""))

    def clear_all_applied_filters(self):
        """Resets application states to baseline view values."""
        if self.clear_filters_btn.is_visible():
            self.clear_filters_btn.click()
            self.page.wait_for_load_state("networkidle")