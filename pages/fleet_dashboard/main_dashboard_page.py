from playwright.sync_api import Page

class MainDashboardPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://portal.agamimp.net/applications/dashboard/fleet"
        
        # 1. Locators for the Side-Panel Filters (All 4 dropdowns)
        self.district_dropdown = page.locator("div.filter-dropdown", has_text="יחידה")
        self.sub_unit_dropdown = page.locator("div.filter-dropdown", has_text="יחידת משנה")
        self.source_dropdown = page.locator("div.filter-dropdown", has_text="מקור משיכה")
        self.category_dropdown = page.locator("div.filter-dropdown", has_text="קטגוריית רכב")
        self.clear_filters_btn = page.locator("button", has_text="מחק מסננים")
        
        # 2. Locators for the KPI Metric Cards (All 4 blocks)
        self.total_vehicles_kpi = page.locator("div.kpi-card", has_text="סה\"כ רכבים שנקלטו")
        self.in_use_kpi = page.locator("div.kpi-card", has_text="סה\"כ רכבים בשימוש")
        self.withdrawn_vehicles_kpi = page.locator("div.kpi-card", has_text="רכבים שזוכו")
        self.allocated_vehicles_kpi = page.locator("div.kpi-card", has_text="רכבים שווסתו")

        # 3. Locators for the Data View Tabs
        self.all_vehicles_tab = page.locator("div.tab-item", has_text="כל הרכבים")
        self.in_use_tab = page.locator("div.tab-item", has_text="בשימוש")
        self.allocated_tab = page.locator("div.tab-item", has_text="שווסתו")
        self.withdrawn_tab = page.locator("div.tab-item", has_text="שזוכו")

    def navigate(self):
        """Navigates to the fleet dashboard application web page."""
        self.page.goto(self.url)
        self.page.wait_for_load_state("networkidle")

    def select_district(self, district_name: str):
        """Selects a specific district filter option from the dropdown list."""
        self.district_dropdown.click()
        self.page.locator(f"role=option[name='{district_name}']").click()
        self.district_dropdown.click()
        self.page.wait_for_load_state("networkidle")

    def select_sub_unit(self, sub_unit_name: str):
        """Selects a specific sub-unit filter option from the dependent dropdown."""
        self.sub_unit_dropdown.click()
        self.page.locator(f"role=option[name='{sub_unit_name}']").click()
        self.sub_unit_dropdown.click()
        self.page.wait_for_load_state("networkidle")

    def select_source(self, source_name: str):
        """Selects a specific vehicle source pull filter option from the dropdown."""
        self.source_dropdown.click()
        self.page.locator(f"role=option[name='{source_name}']").click()
        self.source_dropdown.click()
        self.page.wait_for_load_state("networkidle")

    def select_category(self, category_name: str):
        """Selects a specific vehicle classification type from the filter list."""
        self.category_dropdown.click()
        self.page.locator(f"role=option[name='{category_name}']").click()
        self.category_dropdown.click()
        self.page.wait_for_load_state("networkidle")

    def click_tab(self, tab_name: str):
        """Switches the active data table display by clicking on the specified navigation tab."""
        tabs = {
            "all": self.all_vehicles_tab,
            "in_use": self.in_use_tab,
            "allocated": self.allocated_tab,
            "withdrawn": self.withdrawn_tab
        }
        if tab_name in tabs:
            tabs[tab_name].click()
            self.page.wait_for_load_state("networkidle")
        else:
            raise ValueError(f"Targeted navigation tab is invalid: {tab_name}")

    def get_kpi_value(self, metric_type: str) -> int:
        """Retrieves numerical values displayed within selected dashboard metric blocks."""
        kpi_map = {
            "total": self.total_vehicles_kpi,
            "in_use": self.in_use_kpi,
            "withdrawn": self.withdrawn_vehicles_kpi,
            "allocated": self.allocated_vehicles_kpi
        }
        
        if metric_type not in kpi_map:
            raise ValueError(f"Unknown metric representation targeted: {metric_type}")
            
        text_value = kpi_map[metric_type].locator(".kpi-number").text_content()
        return int(text_value.strip().replace(",", ""))

    def clear_all_applied_filters(self):
        """Resets application states to baseline view values."""
        if self.clear_filters_btn.is_visible():
            self.clear_filters_btn.click()
            self.page.wait_for_load_state("networkidle")