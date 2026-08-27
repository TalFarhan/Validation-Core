"""Credit Consumption report — Layer 0 binding plus info-page popup dismiss."""

import re

from playwright.sync_api import Page

from config.settings import settings
from core.portal.page import ReportShell

_POPUP_CLOSE_NAME = re.compile(r"Close|סגור|סגירה|Dismiss|×|✕", re.I)


class CreditConsumptionPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "צריכת אשראי"

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = settings.LOGIN_URL or settings.DASHBOARD_URL

    def _report_ready_locator(self):
        return self._iframe_phrase_locator("כמות אוכלוסיה ברשויות")

    def before_report_ready_check(self) -> None:
        self._dismiss_info_popup()

    def after_navigate(self) -> None:
        self._dismiss_info_popup()

    def _dismiss_info_popup(self) -> None:
        """Click the overlay X/close if visible; no-op when the popup is absent.

        Uses a short timeout so ready-wait polling is not inflated when the
        popup is missing. The Credit Consumption report opens a bookmark
        "דף מידע" overlay whose close control is often an unlabeled shape.
        """
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass

        close = self._info_popup_close_locator()
        try:
            if close.count() > 0 and close.first.is_visible(timeout=250):
                close.first.click(force=True, timeout=1500)
                return
        except Exception:
            pass

        self._click_info_overlay_close_shape()

    def _click_info_overlay_close_shape(self) -> None:
        """Click the top-right of the info-page visual (typical Power BI X)."""
        frame = self._report_frame()
        for marker in ("מושגים חשובים", "דף מידע"):
            try:
                node = frame.get_by_text(marker, exact=False).first
                if not node.is_visible(timeout=250):
                    continue
                host = node.locator(
                    'xpath=ancestor::*[contains(@class,"visual") or '
                    'contains(@class,"Visual")][1]'
                )
                box = None
                try:
                    if host.count() > 0:
                        box = host.first.bounding_box(timeout=400)
                except Exception:
                    box = None
                if box is None:
                    box = node.bounding_box(timeout=400)
                if box is None or box["width"] < 40 or box["height"] < 40:
                    continue
                self.page.mouse.click(
                    box["x"] + max(24.0, box["width"] - 18),
                    box["y"] + 18,
                )
                return
            except Exception:
                continue

    def _info_popup_close_locator(self):
        frame = self._report_frame()
        return (
            frame.get_by_role("button", name=_POPUP_CLOSE_NAME)
            .or_(frame.get_by_label(_POPUP_CLOSE_NAME))
            .or_(
                frame.locator(
                    "[aria-label*='Close' i], [aria-label*='סגור'], "
                    "[title*='Close' i], [title*='סגור'], "
                    "[aria-label*='Dismiss' i], [title*='Dismiss' i]"
                )
            )
            .or_(frame.get_by_text("✕", exact=True))
            .or_(frame.get_by_text("×", exact=True))
            .first
        )
