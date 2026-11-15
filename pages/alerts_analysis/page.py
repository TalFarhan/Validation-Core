"""Alerts Analysis report page object.

Binds Layer 0 (``ReportShell``) for portal navigation and composes the generic
Layer 2 ``Slicer`` for the date-range control. Serves both the freshness smoke
test and the UI-vs-DB parity test. Domain strings (catalog search term, slicer
role name, option labels) live here, never in ``core/``.
"""

from playwright.sync_api import Page

from config.settings import settings
from core.components.slicer import Slicer, SlicerDefinition
from core.portal.page import ReportShell


class AlertsAnalysisPage(ReportShell):
    # Catalog product name used to open the report from the portal.
    DASHBOARD_SEARCH_TERM = "ניתוח התרעות"
    # Accessible name of the date-range dropdown slicer on this report.
    DATE_RANGE_ROLE_NAME = "FilterName"

    _SLICER_DEFINITIONS = (
        SlicerDefinition(
            id="date_range",
            role_name=DATE_RANGE_ROLE_NAME,
            kind="dropdown",
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL
        self.dashboard = page.frame_locator("main iframe")
        self._slicer = Slicer(
            page=page,
            frame=self.dashboard,
            definitions=self._SLICER_DEFINITIONS,
            timeout_ms=self.timeout,
        )

    def _report_ready_locator(self):
        return self._iframe_phrase_locator(self.DASHBOARD_SEARCH_TERM)

    def select_date_range(self, value: str) -> None:
        """Select a date-range option (e.g. 'שלושים יום אחרונים') via the Slicer."""
        self._slicer.select("date_range", value)
