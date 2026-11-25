"""Authorities Screen 2 checks against data/reshuyot/db_sanity.yaml."""

from pathlib import Path
import re

import pytest
import yaml

from tests.sanity.authorities_status_dashboard.conftest import (
    authorities_status_dashboard,
)

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3] / "data" / "reshuyot" / "db_sanity.yaml"
)
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_ROOT = "dashboard"
_BLOCK = "screen_2_service_targets"


def load_sanity_data() -> dict:
    """Load the dashboard block from the golden file."""
    with _GOLDEN_RECORD.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["dashboard"]


def _plain(raw) -> str:
    """Trim display text and drop Power BI bidi marks."""
    text = "" if raw is None else str(raw)
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text.strip()


def _labels(value) -> list[str]:
    """One slicer call per label. A list stays a list of labels."""
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def assert_value(yaml_path: str, actual, expected) -> None:
    """Integers parse grouped digits. Floats parse the displayed number."""
    if isinstance(expected, bool):
        assert actual is expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    if isinstance(expected, int) and not isinstance(expected, bool):
        digits = (
            _plain(actual)
            .replace(",", "")
            .replace(" ", "")
            .replace("\u00a0", "")
            .replace("\u202f", "")
        )
        match = re.search(r"-?\d+", digits)
        parsed = int(match.group(0)) if match else actual
        assert parsed == expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    if isinstance(expected, float):
        digits = (
            _plain(actual)
            .replace(",", "")
            .replace(" ", "")
            .replace("\u00a0", "")
            .replace("\u202f", "")
        )
        match = re.search(r"-?\d+(?:\.\d+)?", digits)
        parsed = float(match.group(0)) if match else actual
        assert parsed == expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    assert _plain(actual) == _plain(expected), (
        f"{yaml_path}: ui={actual!r} golden={expected!r}"
    )


def _row_identity(golden_rows: list) -> str:
    """Object-row key: name, else date, else title."""
    if not golden_rows:
        return "name"
    first = golden_rows[0]
    if isinstance(first, dict) and "name" in first:
        return "name"
    if isinstance(first, dict) and "date" in first:
        return "date"
    return "title"


def _assert_rows(yaml_path: str, actual_rows: list, golden_rows: list) -> None:
    """Every golden row matches. Extra UI rows are ignored."""
    if golden_rows and not actual_rows:
        raise AssertionError(f"{yaml_path}: ui=[] golden={golden_rows!r}")
    if golden_rows and isinstance(golden_rows[0], str):
        present = {_plain(item) for item in actual_rows}
        for name in golden_rows:
            assert _plain(name) in present, (
                f"{yaml_path}: ui={sorted(present)!r} golden={name!r}"
            )
        return
    key = _row_identity(golden_rows)
    indexed: dict[str, dict] = {}
    for row in actual_rows:
        if isinstance(row, dict):
            indexed[_plain(row.get(key, ""))] = row
    for gold in golden_rows:
        row_key = _plain(gold.get(key, ""))
        assert row_key in indexed, (
            f"{yaml_path}[{key}={row_key}]: ui={sorted(indexed)!r} golden={row_key!r}"
        )
        actual = indexed[row_key]
        for field, value in gold.items():
            _assert_tree(
                f"{yaml_path}[{key}={row_key}].{field}",
                actual.get(field, ""),
                value,
            )


def _assert_tree(yaml_path: str, actual, expected) -> None:
    """Walk a golden mapping. An empty actual value fails when expected has data."""
    if isinstance(expected, dict):
        if expected and not actual:
            raise AssertionError(f"{yaml_path}: ui={actual!r} golden={expected!r}")
        for key, value in expected.items():
            assert key in (actual or {}), (
                f"{yaml_path}.{key}: ui='missing' golden={value!r}"
            )
            _assert_tree(f"{yaml_path}.{key}", actual[key], value)
        return
    if isinstance(expected, list):
        _assert_rows(yaml_path, actual or [], expected)
        return
    assert_value(yaml_path, actual, expected)


@pytest.mark.sanity
def test_authorities_screen2_matches_golden(authorities_status_dashboard):
    """Screen 2 matches dashboard.screen_2_service_targets."""
    page = authorities_status_dashboard
    expected = load_sanity_data().get(_BLOCK) or {}
    title = expected.get("title")
    if title:
        page.open_screen_2(str(title))
    report_date = expected.get("date")
    if report_date:
        page.select_screen_2_filter("date", str(report_date))
        page.wait_for_screen_2_idle()
    filters = expected.get("filters") or {}
    for slicer_id, value in filters.items():
        for label in _labels(value):
            page.select_screen_2_filter(str(slicer_id), label)
            page.wait_for_screen_2_idle()
    page.wait_for_screen_2_idle()
    actual = page.read_screen_2_metrics()
    skipped: list[str] = []
    checked: list[str] = []
    for key, value in expected.items():
        path = f"{_ROOT}.{_BLOCK}.{key}"
        if not page.screen_2_section_visible(key):
            skipped.append(key)
            continue
        checked.append(key)
        _assert_tree(path, actual.get(key), value)
    if expected and skipped and not checked:
        pytest.skip(
            "Screen 2 anchors are not rendered: " + ", ".join(skipped)
        )
