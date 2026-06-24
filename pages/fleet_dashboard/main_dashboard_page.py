import re

from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage


class MainDashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.DASHBOARD_URL

        self.district_dropdown = page.locator("div.filter-dropdown", has_text="יחידה")
        self.sub_unit_dropdown = page.locator("div.filter-dropdown", has_text="יחידת משנה")
        self.source_dropdown = page.locator("div.filter-dropdown", has_text="מקור משיכה")
        self.category_dropdown = page.locator("div.filter-dropdown", has_text="קטגוריית רכב")
        self.clear_filters_btn = page.locator("button", has_text="מחק מסננים")

        self.total_vehicles_kpi = page.locator("div.kpi-card", has_text="סה\"כ רכבים שנקלטו")
        self.in_use_kpi = page.locator("div.kpi-card", has_text="סה\"כ רכבים בשימוש")
        self.withdrawn_vehicles_kpi = page.locator("div.kpi-card", has_text="רכבים שזוכו")
        self.allocated_vehicles_kpi = page.locator("div.kpi-card", has_text="רכבים שווסתו")

        self.all_vehicles_tab = page.locator("div.tab-item", has_text="כל הרכבים")
        self.in_use_tab = page.locator("div.tab-item", has_text="בשימוש")
        self.allocated_tab = page.locator("div.tab-item", has_text="שווסתו")
        self.withdrawn_tab = page.locator("div.tab-item", has_text="שזוכו")

        self._kpi_map = {
            "total": self.total_vehicles_kpi,
            "in_use": self.in_use_kpi,
            "withdrawn": self.withdrawn_vehicles_kpi,
            "allocated": self.allocated_vehicles_kpi,
        }

        self._tab_map = {
            "all": self.all_vehicles_tab,
            "in_use": self.in_use_tab,
            "allocated": self.allocated_tab,
            "withdrawn": self.withdrawn_tab,
        }

    def navigate(self) -> None:
        self.page.goto(self.url)
        self.wait_for_visible(self.total_vehicles_kpi)

    def _select_dropdown_option(self, dropdown_locator, option_name: str) -> None:
        previous_total = self.get_kpi_value("total")
        dropdown_locator.click()
        option = self.page.locator(f"role=option[name='{option_name}']")
        expect(option).to_be_visible(timeout=self.timeout)
        option.click()
        self.page.keyboard.press("Escape")
        self.wait_for_kpi_update(self.total_vehicles_kpi, previous_total)
        expect(self.clear_filters_btn).to_be_visible(timeout=self.timeout)

    def select_district(self, district_name: str) -> None:
        self._select_dropdown_option(self.district_dropdown, district_name)

    def select_sub_unit(self, sub_unit_name: str) -> None:
        self._select_dropdown_option(self.sub_unit_dropdown, sub_unit_name)

    def select_source(self, source_name: str) -> None:
        self._select_dropdown_option(self.source_dropdown, source_name)

    def select_category(self, category_name: str) -> None:
        self._select_dropdown_option(self.category_dropdown, category_name)

    def click_tab(self, tab_name: str) -> None:
        if tab_name not in self._tab_map:
            raise ValueError(f"Targeted navigation tab is invalid: {tab_name}")

        tab = self._tab_map[tab_name]
        tab.click()
        self.assert_tab_active(tab)

    def get_kpi_value(self, metric_type: str) -> int:
        if metric_type not in self._kpi_map:
            raise ValueError(f"Unknown metric representation targeted: {metric_type}")

        text_value = self._kpi_map[metric_type].locator(".kpi-number").text_content()
        return int(text_value.strip().replace(",", ""))

    def clear_all_applied_filters(self) -> None:
        if self.clear_filters_btn.is_visible():
            filtered_total = self.get_kpi_value("total")
            self.clear_filters_btn.click()
            expect(self.clear_filters_btn).to_be_hidden(timeout=self.timeout)
            self.wait_for_kpi_update(self.total_vehicles_kpi, filtered_total)
