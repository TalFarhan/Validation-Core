import re
import time

from playwright.sync_api import Locator, Page, expect

from config.settings import settings


class BasePage:
    ACTIVE_TAB_CLASS = re.compile(r"(selected|active)")

    def __init__(self, page: Page):
        self.page = page
        self.timeout = settings.DEFAULT_TIMEOUT

    @staticmethod
    def _read_kpi_value(kpi_locator: Locator) -> int:
        text = kpi_locator.locator("p").last.text_content() or ""
        return int(text.strip().replace(",", ""))

    def wait_for_visible(self, locator: Locator) -> None:
        expect(locator).to_be_visible(timeout=self.timeout)

    def wait_for_kpi_update(
        self, kpi_locator: Locator, previous_value: int, *, required: bool = True
    ) -> None:
        deadline = time.monotonic() + self.timeout / 1000
        while time.monotonic() < deadline:
            if self._read_kpi_value(kpi_locator) != previous_value:
                return
            time.sleep(0.25)

        if required:
            current = self._read_kpi_value(kpi_locator)
            raise AssertionError(
                f"KPI stayed at {previous_value} (current: {current})"
            )

    def assert_tab_active(self, tab_locator: Locator) -> None:
        expect(tab_locator).to_have_class(self.ACTIVE_TAB_CLASS, timeout=self.timeout)

    def assert_tab_inactive(self, tab_locator: Locator) -> None:
        expect(tab_locator).not_to_have_class(self.ACTIVE_TAB_CLASS, timeout=self.timeout)
