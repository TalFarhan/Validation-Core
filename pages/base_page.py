import re

from playwright.sync_api import Locator, Page, expect

from config.settings import settings


class BasePage:
    ACTIVE_TAB_CLASS = re.compile(r"(selected|active)")

    def __init__(self, page: Page):
        self.page = page
        self.timeout = settings.DEFAULT_TIMEOUT

    def wait_for_visible(self, locator: Locator) -> None:
        expect(locator).to_be_visible(timeout=self.timeout)

    def wait_for_kpi_update(self, kpi_locator: Locator, previous_value: int) -> None:
        def read_value() -> int:
            text = kpi_locator.locator(".kpi-number").text_content() or ""
            return int(text.strip().replace(",", ""))

        expect.poll(read_value).not_to_be(previous_value, timeout=self.timeout)

    def assert_tab_active(self, tab_locator: Locator) -> None:
        expect(tab_locator).to_have_class(self.ACTIVE_TAB_CLASS, timeout=self.timeout)

    def assert_tab_inactive(self, tab_locator: Locator) -> None:
        expect(tab_locator).not_to_have_class(self.ACTIVE_TAB_CLASS, timeout=self.timeout)
