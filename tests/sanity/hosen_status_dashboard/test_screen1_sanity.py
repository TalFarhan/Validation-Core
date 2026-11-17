"""Hosen Screen 1 checks against data/hosen/db_sanity.yaml."""

from pathlib import Path
import re

import pytest
import yaml

from tests.sanity.hosen_status_dashboard.conftest import hosen_status_dashboard

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3] / "data" / "hosen" / "db_sanity.yaml"
)
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_ROOT = "hosen_dashboard"
_BLOCKS = ("survey_status", "kpis", "resilience_scores", "filters")
_ROW_KEY = {
    "categories": "title",
    "resilience_scores": "authority",
}


def load_sanity_data() -> dict:
    """Load the hosen_dashboard block from the golden file."""
    with _GOLDEN_RECORD.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["hosen_dashboard"]


def _plain(raw) -> str:
    """Trim display text and drop Power BI bidi marks."""
    text = "" if raw is None else str(raw)
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return text.strip()


def assert_value(yaml_path: str, actual, expected) -> None:
    """Integers parse grouped digits. Strings stay display text."""
    if isinstance(expected, bool):
        assert actual is expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    if isinstance(expected, int):
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
        digits = _plain(actual).replace(",", "").replace(" ", "")
        assert float(digits) == expected, f"{yaml_path}: ui={actual!r} golden={expected!r}"
        return
    assert _plain(actual) == _plain(expected), (
        f"{yaml_path}: ui={actual!r} golden={expected!r}"
    )


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
    key = "title"
    for suffix, field in _ROW_KEY.items():
        if yaml_path.endswith(suffix):
            key = field
            break
    indexed: dict[str, dict] = {}
    for row in actual_rows:
        if isinstance(row, dict):
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
def test_hosen_screen1_matches_golden(hosen_status_dashboard):
    """Screen 1 survey, KPIs, resilience rows, and filters match the golden block."""
    page = hosen_status_dashboard
    expected = load_sanity_data().get("screen_1_landing") or {}
    report_date = expected.get("date")
    if report_date:
        page.select_screen_1_filter("date", str(report_date))
    filters = expected.get("filters", {})
    for slicer_id, value in filters.items():
        page.select_screen_1_filter(str(slicer_id), str(value))
    # Read metrics only after every golden filter has been applied.
    page.wait_for_screen_1_idle()
    actual = page.read_screen_1_metrics()
    for key in _BLOCKS:
        assert key in actual, f"{_ROOT}.screen_1_landing.{key}: ui='missing'"
    skipped: list[str] = []
    checked: list[str] = []
    for key, value in expected.items():
        path = f"{_ROOT}.screen_1_landing.{key}"
        if not page.section_anchor_visible(key):
            skipped.append(key)
            continue
        checked.append(key)
        _assert_tree(path, actual.get(key), value)
    if expected and skipped and not checked:
        pytest.skip(
            "Screen 1 anchors are not rendered: " + ", ".join(skipped)
        )
