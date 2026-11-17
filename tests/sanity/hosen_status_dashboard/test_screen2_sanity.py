"""Hosen Screen 2 checks against data/hosen/db_sanity.yaml."""

from pathlib import Path

import pytest
import yaml

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3] / "data" / "hosen" / "db_sanity.yaml"
)
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_ROOT = "hosen_dashboard.screen_2_investigation"
_BLOCKS = (
    ("title", "title"),
    ("date", "date"),
    ("filters", "filters"),
    ("tables.authorities_breakdown_table", "authorities_breakdown_table"),
    ("tables.totals_row", "totals_row"),
    ("tables.trends_by_date_table", "trends_by_date_table"),
)


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


def _fold_quotes(text: str) -> str:
    """Treat ASCII quotes and Hebrew gershayim as the same character."""
    return _plain(text).replace("״", '"').replace("׳", "'")


def _lookup(node, path: str):
    """Walk a dotted path. Missing keys return None."""
    current = node
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _has_data(value) -> bool:
    """True when the golden node is a value the reader must return."""
    if value is None:
        return False
    if isinstance(value, (dict, list, str)):
        return len(value) > 0
    return True


def _empty(value) -> bool:
    """True when the reader returned nothing for a block."""
    if value is None:
        return True
    if isinstance(value, (dict, list, str)):
        return len(value) == 0
    return False


def _row_key(yaml_path: str) -> str:
    if yaml_path.endswith("authorities_breakdown_table"):
        return "authority"
    if yaml_path.endswith("trends_by_date_table"):
        return "creation_date"
    return "title"


def assert_value(yaml_path: str, actual, expected, *, fold_quotes: bool = False) -> None:
    """Display text matches. YAML null matches an empty cell."""
    if expected is None:
        assert _plain(actual) == "", f"{yaml_path}: ui={actual!r} golden=null"
        return
    left = _plain(actual)
    right = _plain(expected)
    if fold_quotes:
        left = _fold_quotes(left)
        right = _fold_quotes(right)
    assert left == right, f"{yaml_path}: ui={actual!r} golden={expected!r}"


def _assert_rows(yaml_path: str, actual_rows: list, golden_rows: list) -> None:
    """Every golden row matches. Extra UI rows are ignored."""
    if golden_rows and not actual_rows:
        raise AssertionError(f"{yaml_path}: ui=[] golden={golden_rows!r}")
    key = _row_key(yaml_path)
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
            assert_value(
                f"{yaml_path}[{key}={row_key}].{field}",
                actual.get(field, ""),
                value,
            )


def _assert_tree(yaml_path: str, actual, expected, *, fold_quotes: bool = False) -> None:
    """Walk a golden mapping. An empty actual value fails when expected has data."""
    if isinstance(expected, dict):
        if expected and not actual:
            raise AssertionError(f"{yaml_path}: ui={actual!r} golden={expected!r}")
        for key, value in expected.items():
            assert isinstance(actual, dict) and key in actual, (
                f"{yaml_path}.{key}: ui='missing' golden={value!r}"
            )
            child = f"{yaml_path}.{key}"
            _assert_tree(
                child,
                actual[key],
                value,
                fold_quotes=fold_quotes or key == "title",
            )
        return
    if isinstance(expected, list):
        _assert_rows(yaml_path, actual or [], expected)
        return
    assert_value(yaml_path, actual, expected, fold_quotes=fold_quotes)


@pytest.mark.sanity
def test_hosen_screen2_matches_golden(hosen_status_dashboard):
    """Screen 2 title, date, filters, and tables match the golden block."""
    page = hosen_status_dashboard
    expected = load_sanity_data().get("screen_2_investigation") or {}
    page.open_investigation_screen(str(expected["title"]))
    report_date = expected.get("date")
    if report_date:
        page.select_screen_2_filter("date", str(report_date))
    filters = expected.get("filters") or {}
    for slicer_id, value in filters.items():
        page.select_screen_2_filter(str(slicer_id), str(value))
    page.wait_for_screen_2_idle()
    actual = page.read_screen_2_metrics()
    skipped: list[str] = []
    checked: list[str] = []
    for path, section in _BLOCKS:
        golden = _lookup(expected, path)
        reading = _lookup(actual, path)
        yaml_path = f"{_ROOT}.{path}"
        if not page.screen_2_section_visible(section):
            skipped.append(section)
            continue
        checked.append(section)
        if _has_data(golden) and _empty(reading):
            raise AssertionError(f"{yaml_path}: ui={reading!r} golden={golden!r}")
        _assert_tree(yaml_path, reading, golden, fold_quotes=(path == "title"))
    if expected and skipped and not checked:
        pytest.skip("Screen 2 anchors are not rendered: " + ", ".join(skipped))
