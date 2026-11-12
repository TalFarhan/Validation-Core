"""Rescue Capabilities report — Layer 0 binding only (no slicers / KPIs)."""

from playwright.sync_api import Page

from config.settings import settings
from core.portal.page import ReportShell


class RescueCapabilitiesPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "כשירויות חילוץ במרחב האזרחי"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL

    def _report_ready_locator(self):
        return self._report_frame().get_by_text(
            "כשירויות חילוץ במרחב האזרחי",
            exact=True,
        )
