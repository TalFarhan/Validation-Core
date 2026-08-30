"""Shared `dashboard` fixture body for Layer 0 report suites.

Do not put a `dashboard` fixture in `tests/ui/conftest.py`: that directory
also contains `fleet_dashboard`, which must keep the root fixture
(`MainDashboardPage`). Each suite shadows `dashboard` locally by binding
its page class.
"""

from __future__ import annotations

from typing import TypeVar

import pytest
from playwright.sync_api import BrowserContext, Page

from browser_session import ensure_single_tab
from core.portal.page import ReportShell

PageT = TypeVar("PageT", bound=ReportShell)


def open_report(
    page_cls: type[PageT],
    auth_page: Page,
    browser_context: BrowserContext,
) -> PageT:
    """Open a report on the shared tab, retrying transient portal glitches."""
    from conftest import save_auth_state

    ensure_single_tab(browser_context, auth_page)
    page_obj = page_cls(auth_page)
    was_ready = page_obj._dashboard_ready()
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            page_obj.navigate(force_reload=attempt > 0)
            last_error = None
            break
        except AssertionError as exc:
            last_error = exc
            msg = str(exc)
            transient = (
                "Could not open products catalog" in msg
                or "Failed to get user" in msg
                or page_obj._is_portal_profile_error()
            )
            if not transient or attempt == 1:
                raise
            print(f"\n[nav] ניווט נכשל (ניסיון {attempt + 1}) — retry...\n{exc}\n")
            page_obj._recover_from_portal_glitch()
    if last_error is not None:
        raise last_error
    ensure_single_tab(browser_context, auth_page)
    if not was_ready and not page_obj._is_login_page():
        save_auth_state(browser_context)
    return page_obj


def bind_dashboard(page_cls: type[PageT]):
    """Return a `dashboard` fixture that constructs `page_cls` on the shared tab."""

    @pytest.fixture
    def dashboard(auth_page, browser_context):
        return open_report(page_cls, auth_page, browser_context)

    dashboard.__doc__ = (
        f"Reuse the shared tab; open {page_cls.__name__} via this page's search term."
    )
    return dashboard
