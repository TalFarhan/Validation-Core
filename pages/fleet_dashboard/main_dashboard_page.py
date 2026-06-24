import re

from playwright.sync_api import Page, expect

from config.settings import settings
from pages.base_page import BasePage


class MainDashboardPage(BasePage):
    _KPI_TITLES = {
        "total": 'סה"כ רכבים שנקלטו',
        "in_use": 'סה"כ רכבים בשימוש',
        "withdrawn": "רכבים שזוכו",
        "allocated": "רכבים שווסתו",
    }

    _SLICER_LISTBOXES = {
        "district": "Unit",
        "sub_unit": "SubUnit",
        "source": "VehicleSource",
        "category": "VehicleCategory",
    }

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.DASHBOARD_URL
        self.dashboard = page.frame_locator("main iframe")

        self.district_dropdown = self.dashboard.get_by_role("combobox", name="Unit", exact=True)
        self.sub_unit_dropdown = self.dashboard.get_by_role("combobox", name="SubUnit", exact=True)
        self.source_dropdown = self.dashboard.get_by_role("combobox", name="VehicleSource", exact=True)
        self.category_dropdown = self.dashboard.get_by_role("combobox", name="VehicleCategory", exact=True)
        self.clear_filters_btn = self.dashboard.get_by_role(
            "button", name=re.compile(r"נקה את כל")
        )

        self.total_vehicles_kpi = self._kpi_card(self._KPI_TITLES["total"])
        self.in_use_kpi = self._kpi_card(self._KPI_TITLES["in_use"])
        self.withdrawn_vehicles_kpi = self._kpi_card(self._KPI_TITLES["withdrawn"])
        self.allocated_vehicles_kpi = self._kpi_card(self._KPI_TITLES["allocated"])

        self.all_vehicles_tab = self._tab("כל הרכבים")
        self.in_use_tab = self._tab("בשימוש")
        self.allocated_tab = self._tab("שווסתו")
        self.withdrawn_tab = self._tab("שזוכו")

        self._tab_map = {
            "all": self.all_vehicles_tab,
            "in_use": self.in_use_tab,
            "allocated": self.allocated_tab,
            "withdrawn": self.withdrawn_tab,
        }

    def _tab(self, label: str):
        return self.dashboard.get_by_text(label, exact=True).first

    def _kpi_card(self, title: str):
        return self.dashboard.get_by_role("button", name=re.compile(re.escape(title)))

    def navigate(self) -> None:
        self.page.goto(self.url)
        expect(self.page.locator("main iframe")).to_be_visible(timeout=self.timeout)
        self.wait_for_visible(self.total_vehicles_kpi)

    def option(self, option_name: str, listbox_name: str):
        return self.dashboard.get_by_role("listbox", name=listbox_name, exact=True).get_by_role(
            "option", name=option_name, exact=True
        )

    def _close_open_slicers(self) -> None:
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")

    def _select_dropdown_option(
        self, dropdown_locator, option_name: str, listbox_name: str
    ) -> None:
        self._close_open_slicers()
        previous_total = self.get_kpi_value("total")
        dropdown_locator.click(force=True)
        option = self.option(option_name, listbox_name)
        expect(option).to_be_visible(timeout=self.timeout)
        option.click(force=True)
        self.total_vehicles_kpi.click(force=True)
        self.wait_for_kpi_update("total", previous_total, required=False)

    def select_district(self, district_name: str) -> None:
        self._select_dropdown_option(
            self.district_dropdown, district_name, self._SLICER_LISTBOXES["district"]
        )

    def select_sub_unit(self, sub_unit_name: str) -> None:
        self._select_dropdown_option(
            self.sub_unit_dropdown, sub_unit_name, self._SLICER_LISTBOXES["sub_unit"]
        )

    def select_source(self, source_name: str) -> None:
        self._select_dropdown_option(
            self.source_dropdown, source_name, self._SLICER_LISTBOXES["source"]
        )

    def select_category(self, category_name: str) -> None:
        self._select_dropdown_option(
            self.category_dropdown, category_name, self._SLICER_LISTBOXES["category"]
        )

    def click_tab(self, tab_name: str) -> None:
        if tab_name not in self._tab_map:
            raise ValueError(f"Targeted navigation tab is invalid: {tab_name}")

        self._tab_map[tab_name].click(force=True)

    def get_kpi_value(self, metric_type: str) -> int:
        if metric_type not in self._KPI_TITLES:
            raise ValueError(f"Unknown metric representation targeted: {metric_type}")

        return self._read_kpi_value(self._kpi_card(self._KPI_TITLES[metric_type]))

    def wait_for_kpi_update(
        self, metric_type: str, previous_value: int, *, required: bool = True
    ) -> None:
        card = self._kpi_card(self._KPI_TITLES[metric_type])
        super().wait_for_kpi_update(card, previous_value, required=required)

    def clear_all_applied_filters(self) -> None:
        filtered_total = self.get_kpi_value("total")
        self.clear_filters_btn.click()
        self.wait_for_kpi_update("total", filtered_total)
