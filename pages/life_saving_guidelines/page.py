"""Life-Saving Guidelines report — Layer 0 binding only (no slicers / KPIs).

Gated behind an ArcGIS secondary-auth/entry screen shown after the catalog
click; ``_bypass_secondary_auth`` drives it via the shared helper.
"""

from playwright.sync_api import Page

from config.settings import settings
from core.portal.page import ReportShell
from pages.secondary_auth import bypass_secondary_auth


class LifeSavingGuidelinesPage(ReportShell):
    DASHBOARD_SEARCH_TERM = 'תמ"צ שליטה - סטטוס הנחיות מצילות חיים'

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL

    def _report_ready_locator(self):
        # Temporary: use the catalog search term as an exact-text ready visual
        # until the real landing title is confirmed from a live run.
        return self._report_frame().get_by_text(
            'תמ"צ שליטה - סטטוס הנחיות מצילות חיים',
            exact=True,
        )

    def _bypass_secondary_auth(self) -> None:
        # Dismiss the ArcGIS secondary sign-in shown after the catalog click.
        # No-op when the screen is absent (reused/saved session).
        bypass_secondary_auth(self.page)
