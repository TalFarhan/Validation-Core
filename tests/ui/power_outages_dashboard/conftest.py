import pytest

from browser_session import ensure_single_tab
from conftest import save_auth_state
from tests.ui.power_outages_dashboard.page import PowerOutagesPage


@pytest.fixture
def dashboard(auth_page, browser_context):
    """Reuse the shared tab; open Power Outages via this page's search term."""
    ensure_single_tab(browser_context, auth_page)
    page_obj = PowerOutagesPage(auth_page)
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
