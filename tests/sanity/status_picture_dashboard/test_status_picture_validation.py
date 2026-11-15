"""Status-picture checks against the golden record."""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from tests.sanity.status_picture_dashboard.conftest import status_picture_dashboard

_GOLDEN_RECORD = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "alerts"
    / "db_sanity_am_kalavi.yaml"
)


def load_sanity_data() -> dict:
    """Load the alerts golden record from the repository data directory."""
    with _GOLDEN_RECORD.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def to_page_date(iso_date: str) -> str:
    """Turn a golden YYYY-MM-DD date into the page's DD/MM/YYYY format."""
    parsed = datetime.strptime(iso_date, "%Y-%m-%d")
    return parsed.strftime("%d/%m/%Y")


def _screen_record() -> dict:
    """Return the Screen 1 block from the golden record."""
    data = load_sanity_data()
    return data["dashboard_sanity_checks"]["screen_1_status_picture"]


def _apply_golden_range(page) -> dict:
    """Select the Screen 1 golden operation by name and return that screen block."""
    screen = _screen_record()
    # Select the named operation directly on the slicer instead of passing dates.
    page.select_operation(screen["operation"])
    return screen


def _require_card(cards: dict, key: str):
    """Return one card, or skip when the page did not expose that title."""
    if key not in cards:
        pytest.skip(f"Missing Page Object reader for {key}")
    return cards[key]


def _assert_golden_entries(actual: dict, expected: dict) -> None:
    """Every golden key is present and equal. Extra UI keys are ignored."""
    missing = [key for key in expected if key not in actual]
    assert not missing, f"missing golden keys: {missing}"
    for key, value in expected.items():
        assert actual[key] == value, f"{key}: ui={actual[key]} golden={value}"


def _tie_value(expected: dict) -> int:
    """The count shared by the lowest-ranked golden settlements (the tie)."""
    # The tie is the lowest golden count, and more than one settlement shares it.
    tie = min(expected.values())
    shared = [name for name, count in expected.items() if count == tie]
    assert len(shared) > 1, f"golden file has no tie to verify: {sorted(expected.items())}"
    return tie


def _stable_rankings(expected: dict, tie: int) -> dict:
    """Golden settlements whose count is above the tie value."""
    return {name: count for name, count in expected.items() if count > tie}


def _golden_tie_names(expected: dict, tie: int) -> set:
    """Golden settlement names that share the tie count."""
    return {name for name, count in expected.items() if count == tie}


@pytest.mark.sanity
def test_screen_1_global_metrics(status_picture_dashboard):
    """Cleared warning-zone and alerted-population cards match the golden record."""
    metrics = _screen_record()["metrics"]
    status_picture_dashboard.clear_filters()
    cards = status_picture_dashboard.read_cards()
    assert _require_card(cards, "total_warning_zones") == (
        metrics["total_warning_zones_all_time"]["expected_value"]
    )
    assert _require_card(cards, "total_alerted_population") == (
        metrics["total_alerted_population_all_time"]["expected_value"]
    )


@pytest.mark.sanity
def test_screen_1_filtered_metrics(status_picture_dashboard):
    """Range warning-zone and alerted-population cards match the golden record."""
    screen = _apply_golden_range(status_picture_dashboard)
    metrics = screen["metrics"]
    cards = status_picture_dashboard.read_cards()
    assert _require_card(cards, "warning_zones_under_fire") == (
        metrics["warning_zones_under_fire"]["expected_value"]
    )
    assert _require_card(cards, "alerted_population") == (
        metrics["alerted_population_selected_range"]["expected_value"]
    )


@pytest.mark.sanity
def test_screen_1_alerts_by_category(status_picture_dashboard):
    """Threat totals in the golden range match the golden category map."""
    screen = _apply_golden_range(status_picture_dashboard)
    actual = status_picture_dashboard.read_alerts_by_category()
    if not actual:
        pytest.skip("Missing Page Object reader for alerts_by_category")
    expected = screen["metrics"]["alerts_by_category"]["values"]
    _assert_golden_entries(actual, expected)


@pytest.mark.sanity
def test_screen_1_top_settlements(status_picture_dashboard):
    """Stable settlements match exactly. The tie slots match the golden tie names by name."""
    screen = _apply_golden_range(status_picture_dashboard)
    actual = status_picture_dashboard.read_top_10_settlements()
    if not actual:
        pytest.skip("Missing Page Object reader for top_10_settlements")
    expected = screen["metrics"]["top_10_settlements"]["values"]
    tie = _tie_value(expected)
    # Settlements above the tie keep their exact names and counts.
    stable = _stable_rankings(expected, tie)
    for name, count in stable.items():
        assert name in actual, f"{name}: missing from ui"
        assert actual[name] == count, f"{name}: ui={actual[name]} golden={count}"
    # The remaining UI rows are the tie slots; verify their exact names as a set.
    remaining = {name: count for name, count in actual.items() if name not in stable}
    golden_tie_names = _golden_tie_names(expected, tie)
    assert set(remaining) == golden_tie_names, (
        f"tie names: ui={sorted(remaining)} golden={sorted(golden_tie_names)}"
    )
    for name, count in remaining.items():
        assert count == tie, f"{name}: ui={count} golden tie={tie}"
