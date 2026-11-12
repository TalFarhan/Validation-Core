"""Hosen Status report — Layer 0 binding only (no slicers / KPIs)."""

from playwright.sync_api import Page

from config.settings import settings
from core.portal.page import ReportShell


class HosenStatusPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ חוסן'
    # This dashboard labels its freshness timestamp "מועד רענון" instead of
    # the generic Layer 0 caption ("הדשבורד עודכן לאחרונה ב:").
    LAST_REFRESH_PHRASE = "מועד רענון"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL

    def _report_ready_locator(self):
        return self._report_frame().get_by_text(
            'תמ"צ ארצי - דיווחי קה"א יקל"ר',
            exact=True,
        )
