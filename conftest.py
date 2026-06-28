import json
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from config.settings import settings
from db.client import DatabaseClient
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage

DATA_DIR = Path(__file__).resolve().parent / "data"
VIDEO_DIR = Path("test-results/videos")


def _test_failed(request) -> bool:
    for phase in ("setup", "call"):
        report = getattr(request.node, f"rep_{phase}", None)
        if report is not None and report.failed:
            return True
    return False


def _discard_video(page) -> None:
    video = page.video
    page.close()
    if not video:
        return
    try:
        os.remove(video.path())
    except (FileNotFoundError, OSError):
        pass


def _save_video(page, dest_path: Path) -> None:
    video = page.video
    page.close()
    if not video:
        return

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    video.save_as(str(dest_path))

    try:
        os.remove(video.path())
    except (FileNotFoundError, OSError):
        pass


@pytest.fixture(scope="session")
def db_client():
    """Read-only SQL Server client for UI-to-DB validation."""
    return DatabaseClient()


@pytest.fixture(scope="session")
def filter_data():
    with open(DATA_DIR / "filters.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def filter_matrix():
    with open(DATA_DIR / "filter_matrix.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def zero_count_filters(db_client, filter_data):
    combo = db_client.find_zero_count_filters(filter_data)
    if combo is None:
        pytest.skip("No zero-count filter combination found in test data")
    return combo


@pytest.fixture(scope="session")
def browser_context():
    """Initializes the browser, handles auth state, and configures video recording."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=settings.HEADLESS,
            slow_mo=settings.SLOW_MO or None,
            args=["--start-maximized"]
        )

        context_options = {
            "record_video_dir": "test-results/videos",
            "no_viewport": True, 
        }

        if Path(settings.AUTH_FILE).exists():
            context = browser.new_context(storage_state=settings.AUTH_FILE, **context_options)
        else:
            context = browser.new_context(**context_options)            
            context.set_default_timeout(settings.DEFAULT_TIMEOUT)
            
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
            _discard_video(page)

        # Ensure the timeout is applied to the context for all tests
        context.set_default_timeout(settings.DEFAULT_TIMEOUT)

        yield context
        browser.close()


@pytest.fixture
def auth_page(browser_context, request):
    """Provides a fresh page for each test with tracing and failure artifacts."""
    browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = browser_context.new_page()
    yield page

    test_failed = _test_failed(request)

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

    if test_failed:
        _save_video(page, VIDEO_DIR / f"{request.node.name}_FAILED.webm")
    else:
        _discard_video(page)


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
    setattr(item, f"rep_{rep.when}", rep)
