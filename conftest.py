import os
import pytest
from playwright.sync_api import sync_playwright

# Path to store authentication credentials
AUTH_FILE = "auth_state.json"

@pytest.fixture(scope="session")
def browser_context():
    """Initializes the browser and handles authentication state reuse."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        # Check if login state already exists to skip manual authentication
        if os.path.exists(AUTH_FILE):
            context = browser.new_context(storage_state=AUTH_FILE)
        else:
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://portal.agamimp.net/application/66f13eebe5a555c71f580633?environment=%D7%A1%D7%91%D7%99%D7%91%D7%94%20%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%AA")      
            page.pause()
            
            context.storage_state(path=AUTH_FILE)
            
        yield context
        browser.close()

@pytest.fixture
def auth_page(browser_context, request):
    """Provides an authenticated page instances and manages video/screenshot lifecycle."""
    # Configure video recording option inside the context
    context = browser_context
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    
    page = context.new_page()
    page.set_viewport_size({"width": 1920, "height": 1080})
    
    yield page
    #
    video = page.video
    test_failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False
    
    if test_failed:
        screenshot_dir = "test-results/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        page.screenshot(path=f"{screenshot_dir}/{request.node.name}.png")
        
        if video:
            video_path = video.path()
            video_dir = "test-results/videos"
            os.makedirs(video_dir, exist_ok=True)
            os.replace(video_path, f"{video_dir}/{request.node.name}_FAILED.webm")
    else:
        if video:
            try:
                os.remove(video.path())
            except FileNotFoundError:
                pass

    page.close()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to inject test outcome inside the fixture cleanup stage."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        setattr(item, "rep_call", rep)