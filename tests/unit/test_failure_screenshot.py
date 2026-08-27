"""Unit tests for failure-screenshot capture in root conftest (no browser)."""

from pathlib import Path
from types import SimpleNamespace

import pytest


class _FakePage:
    def __init__(self, payload: bytes = b"\x89PNG\r\nfake", *, closed: bool = False):
        self.payload = payload
        self.closed = closed
        self.screenshot_kwargs = None

    def screenshot(self, **kwargs):
        self.screenshot_kwargs = kwargs
        if self.closed:
            raise RuntimeError("Target page, context or browser has been closed")
        return self.payload


def _root_conftest(request):
    for plugin in request.config.pluginmanager.get_plugins():
        path = Path(getattr(plugin, "__file__", "") or "")
        if path.name == "conftest.py" and "tests" not in path.parts:
            return plugin
    raise AssertionError("root conftest.py plugin was not loaded")


def test_call_failure_attaches_html_and_allure(request, monkeypatch, tmp_path):
    conftest = _root_conftest(request)
    monkeypatch.setattr(conftest, "SCREENSHOTS_DIR", tmp_path)
    attached = {}

    def _fake_allure_attach(body, name=None, attachment_type=None, extension=None):
        attached["body"] = body
        attached["name"] = name
        attached["attachment_type"] = attachment_type

    monkeypatch.setattr(conftest.allure, "attach", _fake_allure_attach)

    page = _FakePage()
    item = SimpleNamespace(name="test_example", funcargs={"auth_page": page})
    report = SimpleNamespace(when="call", failed=True, extras=[])

    assert conftest._attach_failure_screenshot(item, report) is True
    assert page.screenshot_kwargs == {"full_page": True}
    assert attached["body"] == page.payload
    assert attached["name"] == "screenshot"
    assert report.extras, "pytest-html extras.image must be appended"
    assert report.extras[0]["format_type"] == "image"
    assert list(tmp_path.glob("*_FAILED.png")), "screenshot file should be written"


def test_closed_page_does_not_raise(request):
    conftest = _root_conftest(request)
    item = SimpleNamespace(
        name="test_closed",
        funcargs={"auth_page": _FakePage(closed=True)},
    )
    report = SimpleNamespace(when="call", failed=True, extras=[])

    assert conftest._attach_failure_screenshot(item, report) is False
    assert report.extras == []


def test_passing_call_does_not_screenshot(request):
    conftest = _root_conftest(request)
    page = _FakePage()
    item = SimpleNamespace(name="test_pass", funcargs={"auth_page": page})
    report = SimpleNamespace(when="call", failed=False, extras=[])

    assert conftest._attach_failure_screenshot(item, report) is False
    assert page.screenshot_kwargs is None
