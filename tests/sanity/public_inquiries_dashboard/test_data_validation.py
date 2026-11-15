"""Hasbara checks against data/hasbara/db_sanity.yaml for October 2026."""

from pathlib import Path
import re

import pytest
import yaml

from tests.sanity.public_inquiries_dashboard.conftest import (
    public_inquiries_dashboard,
)

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3] / "data" / "hasbara" / "db_sanity.yaml"
)
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_NAMED_SLICERS = ("hours", "language", "platform", "topic", "settlement")
_ROOT = "hasbara_dashboard"

_CHART_KEYS = {
    "written_media_breakdown": "platform",
    "language_breakdown": "language",
    "recurring_requests_breakdown": "type",
    "leading_topics": "topic",
}


def load_sanity_data() -> dict:
    """Load the hasbara_dashboard block from the golden file."""
    with _GOLDEN_RECORD.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["hasbara_dashboard"]


def _plain(raw) -> str:
    """Trim display text and drop Power BI bidi marks."""
    text = "" if raw is None else str(raw)
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text.strip()


def assert_value(yaml_path: str, actual, expected) -> None:
    """Compare one golden node. Integers parse grouped digits. Strings stay display text."""
    if isinstance(expected, bool):
        assert actual is expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    if isinstance(expected, int):
        digits = _plain(actual).replace(",", "").replace(" ", "").replace("\u00a0", "")
        match = re.search(r"-?\d+", digits)
        parsed = int(match.group(0)) if match else actual
        assert parsed == expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    if isinstance(expected, float):
        digits = _plain(actual).replace(",", "").replace(" ", "")
        assert float(digits) == expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    assert _plain(actual) == _plain(expected), (
        f"{yaml_path}: ui={actual!r} golden={expected!r}"
    )


def assert_rows(yaml_path: str, actual_rows: list, golden_rows: list, key: str) -> None:
    """Every golden row matches on key. Extra UI rows are ignored."""
    if golden_rows and not actual_rows:
        raise AssertionError(f"{yaml_path}: ui=[] golden={golden_rows!r}")
    indexed: dict[str, dict] = {}
    for row in actual_rows:
        indexed[_plain(row.get(key, ""))] = row
    for gold in golden_rows:
        row_key = _plain(gold[key])
        assert row_key in indexed, (
            f"{yaml_path}[{key}={row_key}]: ui={sorted(indexed)!r} golden={row_key!r}"
        )
        actual = indexed[row_key]
        for field, value in gold.items():
            assert_value(
                f"{yaml_path}[{key}={row_key}].{field}",
                actual.get(field, ""),
                value,
            )


def _screen(screen_key: str) -> dict:
    return load_sanity_data()[screen_key]


def _apply_screen(page, screen_id: str, screen: dict) -> None:
    page.open_screen(screen_id)
    page.apply_date_range(screen["dashboard_info"]["date_range"])


def _assert_phrase(page, yaml_path: str, phrase: str) -> None:
    assert page.phrase_is_visible(phrase), f"{yaml_path}: ui='absent' golden={phrase!r}"


def _assert_date_and_filters(page, screen_id: str, screen: dict, prefix: str) -> None:
    """Date range from YAML, then every active_filters value. הכל is not selected."""
    _apply_screen(page, screen_id, screen)
    active = screen.get("active_filters") or {}
    for slicer_id, expected in active.items():
        text = page.read_slicer_text(slicer_id)
        assert expected in text, (
            f"{prefix}.active_filters.{slicer_id}: ui={text!r} golden={expected!r}"
        )
    for slicer_id in _NAMED_SLICERS:
        if slicer_id in active:
            continue
        if not page.slicer_is_visible(slicer_id):
            continue
        text = page.read_slicer_text(slicer_id)
        assert "הכל" in text, (
            f"{prefix}.active_filters.{slicer_id}: ui={text!r} golden='הכל'"
        )
    date_range = screen["dashboard_info"]["date_range"]
    assert_value(
        f"{prefix}.dashboard_info.date_range",
        page.read_date_range(),
        date_range,
    )


def _assert_tree(yaml_path: str, actual, expected) -> None:
    """Walk a golden mapping. An empty actual map fails when expected has keys."""
    if isinstance(expected, dict):
        if not actual:
            raise AssertionError(f"{yaml_path}: ui={actual!r} golden={expected!r}")
        for key, value in expected.items():
            assert key in actual, f"{yaml_path}.{key}: ui='missing' golden={value!r}"
            _assert_tree(f"{yaml_path}.{key}", actual[key], value)
        return
    assert_value(yaml_path, actual, expected)


@pytest.mark.sanity
def test_hasbara_screen1_filters_match_golden(public_inquiries_dashboard):
    """Screen 1 date range and default slicers match the golden active_filters."""
    screen = _screen("screen_1_written_response")
    _assert_date_and_filters(
        public_inquiries_dashboard,
        "screen_1",
        screen,
        f"{_ROOT}.screen_1_written_response",
    )


@pytest.mark.sanity
def test_hasbara_screen2_filters_match_golden(public_inquiries_dashboard):
    """Written-investigation tab keeps the golden date range and הכל slicers."""
    screen = _screen("screen_2_written_response_investigation")
    _assert_date_and_filters(
        public_inquiries_dashboard,
        "screen_2",
        screen,
        f"{_ROOT}.screen_2_written_response_investigation",
    )


@pytest.mark.sanity
def test_hasbara_screen3_filters_match_golden(public_inquiries_dashboard):
    """Satisfaction tab has a date range and no active_filters map."""
    screen = _screen("screen_3_satisfaction_feedback")
    prefix = f"{_ROOT}.screen_3_satisfaction_feedback"
    _assert_date_and_filters(
        public_inquiries_dashboard, "screen_3", screen, prefix
    )
    info = screen["dashboard_info"]
    _assert_phrase(
        public_inquiries_dashboard,
        f"{prefix}.dashboard_info.platforms_included",
        info["platforms_included"],
    )


@pytest.mark.sanity
def test_hasbara_screen4_filters_match_golden(public_inquiries_dashboard):
    """Feedback tab slicers, including settlement, stay on the golden defaults."""
    screen = _screen("screen_4_feedback_investigation")
    _assert_date_and_filters(
        public_inquiries_dashboard,
        "screen_4",
        screen,
        f"{_ROOT}.screen_4_feedback_investigation",
    )


@pytest.mark.sanity
def test_hasbara_screen1_kpi_match_golden(public_inquiries_dashboard):
    """Screen 1 KPI cards, title, and data source match the golden block."""
    page = public_inquiries_dashboard
    screen = _screen("screen_1_written_response")
    prefix = f"{_ROOT}.screen_1_written_response"
    _apply_screen(page, "screen_1", screen)
    if not page.kpi_cards_rendered():
        pytest.skip("Screen 1 KPI cards are not rendered")
    info = screen["dashboard_info"]
    _assert_phrase(page, f"{prefix}.dashboard_info.title", info["title"])
    _assert_phrase(page, f"{prefix}.dashboard_info.data_source", info["data_source"])
    _assert_tree(f"{prefix}.kpi_metrics", page.read_kpi_metrics(), screen["kpi_metrics"])


@pytest.mark.sanity
def test_hasbara_screen1_charts_match_golden(public_inquiries_dashboard):
    """Screen 1 charts match the golden block. The hourly trend checks labels only."""
    page = public_inquiries_dashboard
    screen = _screen("screen_1_written_response")
    prefix = f"{_ROOT}.screen_1_written_response.charts"
    _apply_screen(page, "screen_1", screen)
    rendered = [key for key in screen["charts"] if page.chart_is_rendered(key)]
    if not rendered:
        pytest.skip("Screen 1 charts are not rendered")
    actual = page.read_screen1_charts()
    for key, expected in screen["charts"].items():
        path = f"{prefix}.{key}"
        if not page.chart_is_rendered(key):
            raise AssertionError(f"{path}: ui='absent' golden={expected!r}")
        if key == "requests_by_hour_trend":
            got = actual.get(key) or {}
            if not got.get("x_axis_labels") and not got.get("series"):
                raise AssertionError(f"{path}: ui=[] golden={expected!r}")
            golden_names = [item["name"] for item in expected["series"]]
            actual_names = [item["name"] for item in got.get("series", [])]
            present = [name for name in actual_names if name in golden_names]
            assert present == golden_names, (
                f"{path}.series: ui={actual_names!r} golden={golden_names!r}"
            )
            assert got.get("x_axis_labels") == expected["x_axis_labels"], (
                f"{path}.x_axis_labels: ui={got.get('x_axis_labels')!r} "
                f"golden={expected['x_axis_labels']!r}"
            )
            continue
        assert_rows(path, actual.get(key) or [], expected, _CHART_KEYS[key])


@pytest.mark.sanity
def test_hasbara_screen2_investigation_rows_match_golden(public_inquiries_dashboard):
    """Investigation rows match on request_id, including handling time, platform, and topic."""
    page = public_inquiries_dashboard
    screen = _screen("screen_2_written_response_investigation")
    prefix = f"{_ROOT}.screen_2_written_response_investigation"
    _apply_screen(page, "screen_2", screen)
    if not page.grid_is_rendered("screen_2"):
        pytest.skip("Screen 2 investigation grid is not rendered")
    info = screen["dashboard_info"]
    _assert_phrase(page, f"{prefix}.dashboard_info.title", info["title"])
    _assert_phrase(
        page,
        f"{prefix}.dashboard_info.platforms_included",
        info["platforms_included"],
    )
    assert_rows(
        f"{prefix}.investigation_table_data",
        page.read_investigation_rows(),
        screen["investigation_table_data"],
        "request_id",
    )


@pytest.mark.sanity
def test_hasbara_screen3_surveys_match_golden(public_inquiries_dashboard):
    """Survey summary cards match, including the comma string 1,062 and אין מידע."""
    page = public_inquiries_dashboard
    screen = _screen("screen_3_satisfaction_feedback")
    prefix = f"{_ROOT}.screen_3_satisfaction_feedback"
    _apply_screen(page, "screen_3", screen)
    if not page.phrase_is_visible("מוקד טלפוני") and not page.phrase_is_visible("בקרת איכות"):
        pytest.skip("Screen 3 survey cards are not rendered")
    info = screen["dashboard_info"]
    _assert_phrase(page, f"{prefix}.dashboard_info.title", info["title"])
    _assert_phrase(page, f"{prefix}.dashboard_info.data_source", info["data_source"])
    _assert_phrase(
        page,
        f"{prefix}.dashboard_info.platforms_included",
        info["platforms_included"],
    )
    _assert_tree(
        f"{prefix}.surveys_summary",
        page.read_satisfaction()["surveys_summary"],
        screen["surveys_summary"],
    )


@pytest.mark.sanity
def test_hasbara_screen3_distributions_match_golden(public_inquiries_dashboard):
    """Helpfulness bars, the courtesy tab, channels, and platforms match the golden block."""
    page = public_inquiries_dashboard
    screen = _screen("screen_3_satisfaction_feedback")
    prefix = f"{_ROOT}.screen_3_satisfaction_feedback"
    _apply_screen(page, "screen_3", screen)
    rendered = [
        key
        for key in (
            "message_reception",
            "service_reception",
            "leading_contact_channels",
            "platforms_breakdown",
        )
        if page.chart_is_rendered(key)
    ]
    if not rendered:
        pytest.skip("Screen 3 distribution charts are not rendered")
    message = screen["message_reception"]
    _assert_phrase(page, f"{prefix}.message_reception.question", message["question"])
    assert_rows(
        f"{prefix}.message_reception.responses",
        page.read_satisfaction()["message_reception"]["responses"],
        message["responses"],
        "level",
    )
    service = screen["service_reception"]
    page.select_satisfaction_tab(service["active_tab"])
    _assert_phrase(page, f"{prefix}.service_reception.question", service["question"])
    assert_rows(
        f"{prefix}.service_reception.responses",
        page.read_satisfaction()["service_reception"]["responses"],
        service["responses"],
        "level",
    )
    assert_rows(
        f"{prefix}.leading_contact_channels",
        page.read_satisfaction()["leading_contact_channels"],
        screen["leading_contact_channels"],
        "channel",
    )
    assert_rows(
        f"{prefix}.platforms_breakdown",
        page.read_satisfaction()["platforms_breakdown"],
        screen["platforms_breakdown"],
        "platform",
    )


@pytest.mark.sanity
def test_hasbara_screen4_feedback_rows_match_golden(public_inquiries_dashboard):
    """Feedback rows match on inquiry_id, including the comments cell."""
    page = public_inquiries_dashboard
    screen = _screen("screen_4_feedback_investigation")
    prefix = f"{_ROOT}.screen_4_feedback_investigation"
    _apply_screen(page, "screen_4", screen)
    if not page.grid_is_rendered("screen_4"):
        pytest.skip("Screen 4 feedback grid is not rendered")
    info = screen["dashboard_info"]
    _assert_phrase(page, f"{prefix}.dashboard_info.title", info["title"])
    _assert_phrase(
        page,
        f"{prefix}.dashboard_info.platforms_included",
        info["platforms_included"],
    )
    assert_rows(
        f"{prefix}.feedback_investigation_table_data",
        page.read_feedback_rows(),
        screen["feedback_investigation_table_data"],
        "inquiry_id",
    )
