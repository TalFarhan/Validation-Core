import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from config.settings import settings
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage

DATA_DIR = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="session")
def filter_data():
    with open(DATA_DIR / "filters.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def browser_context():
    """Initializes the browser, handles auth state, and configures video recording."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=settings.HEADLESS,
            slow_mo=settings.SLOW_MO or None,
        )

        context_options = {
            "record_video_dir": "test-results/videos",
            "viewport": {"width": 1920, "height": 1080},
        }

        if Path(settings.AUTH_FILE).exists():
            context = browser.new_context(storage_state=settings.AUTH_FILE, **context_options)
        else:
            context = browser.new_context(**context_options)
            page = context.new_page()
            page.goto(settings.LOGIN_URL)

            if settings.MANUAL_LOGIN:
                page.pause()
            else:
                raise RuntimeError(
                    f"Missing auth file '{settings.AUTH_FILE}'. "
                    "Set MANUAL_LOGIN=true for interactive login, or provide a valid auth_state.json."
                )

            context.storage_state(path=settings.AUTH_FILE)
            page.close()

        yield context
        browser.close()


@pytest.fixture
def auth_page(browser_context, request):
    """Provides a fresh page for each test with tracing and failure artifacts."""
    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = browser_context.new_page()
    yield page

    test_failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False

    if test_failed:
        os.makedirs("test-results/screenshots", exist_ok=True)
        screenshot_path = f"test-results/screenshots/{request.node.name}_FAILED.png"
        page.screenshot(path=screenshot_path, full_page=True)

        os.makedirs("test-results/traces", exist_ok=True)
        trace_path = f"test-results/traces/{request.node.name}.zip"
        browser_context.tracing.stop(path=trace_path)

        if settings.PAUSE_ON_FAILURE:
            page.pause()
    else:
        browser_context.tracing.stop()

    video = page.video
    page.close()

    if video:
        if test_failed:
            os.makedirs("test-results/videos", exist_ok=True)
            video_path = f"test-results/videos/{request.node.name}_FAILED.webm"
            os.replace(video.path(), video_path)
        else:
            try:
                os.remove(video.path())
            except FileNotFoundError:
                pass


@pytest.fixture
def dashboard(auth_page):
    """Instantiates the MainDashboardPage and navigates to it."""
    page_obj = MainDashboardPage(auth_page)
    page_obj.navigate()
    return page_obj


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)
