import base64
import json
import re
from datetime import datetime
from pathlib import Path

import allure
import pytest
from playwright.sync_api import sync_playwright

try:
    from pytest_html import extras as html_extras
except ImportError:  # pragma: no cover
    html_extras = None

from browser_session import ensure_single_tab, install_single_tab_policy
from config.settings import settings
from db.client import DatabaseClient
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage
from reports.test_run_report import (
    ALLURE_RESULTS_DIR,
    HTML_REPORTS_DIR,
    REPORT_DIR,
    RESULTS_DIR,
    RunReportBook,
    SCREENSHOTS_DIR,
    TRACES_DIR,
    TestRunReport,
    VIDEOS_DIR,
)
from tests.helpers.dashboard_fixture import open_report

DATA_DIR = Path(__file__).resolve().parent / "data"
AUTH_PATH = Path(settings.AUTH_FILE)


def _artifact_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_artifact_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\[\]{}\']', "_", name)
    cleaned = cleaned.replace(" ", "_")
    return cleaned.strip(" ._")[:120] or "test"


def _test_failed(request) -> bool:
    for phase in ("setup", "call"):
        report = getattr(request.node, f"rep_{phase}", None)
        if report is not None and report.failed:
            return True
    return False


def _as_playwright_page(candidate):
    """Return a Playwright Page (or None) from a fixture value or page object."""
    if candidate is None:
        return None
    if callable(getattr(candidate, "screenshot", None)):
        return candidate
    inner = getattr(candidate, "page", None)
    if inner is not None and callable(getattr(inner, "screenshot", None)):
        return inner
    return None


def _active_playwright_page(item):
    """Resolve the live Playwright page from the test's fixtures."""
    funcargs = getattr(item, "funcargs", None) or {}
    for key in ("auth_page", "session_page", "page", "dashboard"):
        page = _as_playwright_page(funcargs.get(key))
        if page is not None:
            return page
    return None


def _attach_failure_screenshot(item, report) -> bool:
    """Full-page screenshot on UI failure for pytest-html and Allure.

    This framework does not use pytest-playwright's ``--screenshot`` CLI flag.
    Capture here in ``pytest_runtest_makereport`` so extras land on the report
    before HTML generation. Failures in capture must never break teardown.
    """
    if not (report.when == "call" and report.failed):
        return False
    if getattr(item, "_failure_screenshot_taken", False):
        return True

    page = _active_playwright_page(item)
    if page is None:
        return False

    try:
        screenshot_bytes = page.screenshot(full_page=True)
        if not screenshot_bytes:
            return False

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = (
            SCREENSHOTS_DIR
            / f"{_safe_artifact_name(item.name)}_{_artifact_stamp()}_FAILED.png"
        )
        screenshot_path.write_bytes(screenshot_bytes)

        base64_image = base64.b64encode(screenshot_bytes).decode("ascii")
        if html_extras is not None:
            extra = getattr(report, "extras", [])
            extra.append(html_extras.image(base64_image))
            report.extras = extra

        allure.attach(
            screenshot_bytes,
            name="screenshot",
            attachment_type=allure.attachment_type.PNG,
        )
        item._failure_screenshot_taken = True
        return True
    except Exception:
        return False


def save_auth_state(context) -> None:
    """Persist cookies/localStorage so the next pytest run stays logged in."""
    try:
        context.storage_state(path=str(AUTH_PATH))
        print(f"\n[auth] Session saved → {AUTH_PATH.resolve()}\n")
    except Exception as exc:
        print(f"\n[auth] WARNING: could not save session: {exc}\n")


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


def pytest_addoption(parser):
    parser.addoption(
        "--video",
        action="store_true",
        default=False,
        help="Record a .webm of the full pytest session, including passing tests.",
    )


def _want_video(config) -> bool:
    return settings.ENABLE_VIDEO or bool(config.getoption("--video", default=False))


def _save_session_video(video, dest: Path) -> Path | None:
    """Finalize Playwright video after the page is closed. Keep previous runs intact."""
    try:
        video.save_as(str(dest))
    except Exception as exc:
        print(f"\n[video] WARNING: could not save recording: {exc}\n")
        return None
    try:
        video.delete()
    except Exception:
        pass
    if not dest.exists():
        return None
    for extra in dest.parent.glob("*.webm"):
        if extra.resolve() != dest.resolve():
            try:
                extra.unlink()
            except Exception:
                pass
    return dest


def pytest_configure(config):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # One timestamped HTML report per run so a re-run never overwrites the
    # previous one. pytest-html only generates a report when htmlpath is set.
    if hasattr(config.option, "htmlpath") and not config.option.htmlpath:
        HTML_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        config.option.htmlpath = str(
            HTML_REPORTS_DIR / f"report_{_artifact_stamp()}.html"
        )


@pytest.fixture(scope="session")
def run_report_book():
    """One CSV report file for the entire pytest run."""
    book = RunReportBook.start()
    yield book
    path = book.finalize()
    book.stop_context()
    print(f"\n[report] {path.resolve()}\n")


@pytest.fixture(scope="session")
def video_run_dir(pytestconfig):
    """Timestamped folder so a new recording never overwrites a previous run."""
    if not _want_video(pytestconfig):
        yield None
        return
    path = VIDEOS_DIR / f"run_{_artifact_stamp()}"
    path.mkdir(parents=True, exist_ok=True)
    yield path


@pytest.fixture(scope="session")
def browser_context(video_run_dir):
    """One Chromium context for the whole pytest session; loads/saves auth_state.json."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=settings.HEADLESS,
            slow_mo=settings.SLOW_MO or None,
            args=["--start-maximized"],
        )

        context_options = {"no_viewport": True}
        if video_run_dir is not None:
            context_options["record_video_dir"] = str(video_run_dir)
            context_options["record_video_size"] = {"width": 1920, "height": 1080}
            print(f"\n[video] Recording full run → {video_run_dir.resolve()}\n")
        if AUTH_PATH.exists():
            context_options["storage_state"] = str(AUTH_PATH)
            print(f"\n[auth] Loading saved session ← {AUTH_PATH.resolve()}\n")
        else:
            print(
                "\n[auth] No auth_state.json yet — login once this run; "
                "later runs should reuse it.\n"
            )

        context = browser.new_context(**context_options)
        context.set_default_timeout(settings.DEFAULT_TIMEOUT)

        yield context

        save_auth_state(context)
        context.close()
        if video_run_dir is not None:
            dest = video_run_dir / "full-run.webm"
            if not dest.exists():
                leftovers = sorted(video_run_dir.glob("*.webm"))
                if leftovers:
                    leftovers[0].replace(dest)
                    print(f"\n[video] {dest.resolve()}\n")
        browser.close()


@pytest.fixture(scope="session")
def session_page(browser_context, video_run_dir):
    """
    Exactly one browser tab for the entire run.

    Portal actions (התחברות / catalog / product cards) often open target=_blank.
    We intercept that and keep working on this same Page object.
    """
    page = browser_context.new_page()
    install_single_tab_policy(browser_context, page)
    ensure_single_tab(browser_context, page)
    yield page
    ensure_single_tab(browser_context, page)
    video = page.video if video_run_dir is not None else None
    try:
        page.close()
    except Exception:
        pass
    if video is None or video_run_dir is None:
        return
    dest = _save_session_video(video, video_run_dir / "full-run.webm")
    if dest is None:
        return
    print(f"\n[video] {dest.resolve()}\n")
    allure.attach.file(
        str(dest),
        name="session-video",
        attachment_type=allure.attachment_type.WEBM,
    )


@pytest.fixture(autouse=True)
def test_run_report(request, run_report_book):
    """Accumulate steps per test and append them to the run CSV."""
    report = TestRunReport.start(request.node.nodeid)
    yield report

    failed = _test_failed(request)
    error = None
    for phase in ("setup", "call"):
        phase_report = getattr(request.node, f"rep_{phase}", None)
        if phase_report is not None and phase_report.failed and phase_report.longrepr:
            error = str(phase_report.longrepr)
            break

    report.finish(passed=not failed, error=error)
    run_report_book.append_test(report)
    allure.attach(
        report.to_csv_text(),
        name="validation-steps.csv",
        attachment_type=allure.attachment_type.CSV,
        extension="csv",
    )
    report.stop_context()


def _stop_tracing(browser_context, *, path: str | None = None) -> None:
    """Stop tracing if running; ignore 'not started' errors between tests."""
    try:
        if path:
            browser_context.tracing.stop(path=path)
        else:
            browser_context.tracing.stop()
    except Exception:
        pass


@pytest.fixture
def auth_page(session_page, browser_context, request):
    """Always the same session tab."""
    ensure_single_tab(browser_context, session_page)
    tracing = settings.ENABLE_TRACING
    if tracing:
        # Shared context: previous test may have left tracing open after a failed setup.
        _stop_tracing(browser_context)
        browser_context.tracing.start(
            screenshots=True, snapshots=True, sources=False
        )
    yield session_page

    test_failed = _test_failed(request)
    if test_failed:
        # Call-phase screenshots are taken in pytest_runtest_makereport.
        # Setup-phase failures (e.g. navigate in a fixture) still need a shot here.
        if not getattr(request.node, "_failure_screenshot_taken", False):
            try:
                SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
                stamp = _artifact_stamp()
                base_name = f"{_safe_artifact_name(request.node.name)}_{stamp}_FAILED"
                screenshot_bytes = session_page.screenshot(full_page=True)
                screenshot_path = SCREENSHOTS_DIR / f"{base_name}.png"
                screenshot_path.write_bytes(screenshot_bytes)
                base64_image = base64.b64encode(screenshot_bytes).decode("ascii")
                if html_extras is not None:
                    for phase in ("setup", "call"):
                        rep = getattr(request.node, f"rep_{phase}", None)
                        if rep is not None and rep.failed:
                            extra = getattr(rep, "extras", [])
                            extra.append(html_extras.image(base64_image))
                            rep.extras = extra
                            break
                allure.attach(
                    screenshot_bytes,
                    name="screenshot",
                    attachment_type=allure.attachment_type.PNG,
                )
                request.node._failure_screenshot_taken = True
            except Exception:
                pass

        if tracing:
            stamp = _artifact_stamp()
            base_name = f"{_safe_artifact_name(request.node.name)}_{stamp}_FAILED"
            TRACES_DIR.mkdir(parents=True, exist_ok=True)
            trace_path = str(TRACES_DIR / f"{base_name}.zip")
            _stop_tracing(browser_context, path=trace_path)
            if Path(trace_path).exists():
                allure.attach.file(
                    trace_path,
                    name="playwright-trace",
                    attachment_type=allure.attachment_type.ZIP,
                )
        if settings.PAUSE_ON_FAILURE:
            session_page.pause()
    elif tracing:
        _stop_tracing(browser_context)


@pytest.fixture
def dashboard(auth_page, browser_context):
    """Reuse the open dashboard on the shared tab (reload only when needed)."""
    return open_report(MainDashboardPage, auth_page, browser_context)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    _attach_failure_screenshot(item, report)
