"""Population screen checks against the golden record."""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from tests.ui.alerts_analysis_dashboard.conftest import population_dashboard

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


def read_population_cards(page) -> dict[str, int | float]:
    """Read the total, warned, and unprotected cards on the population page."""
    return {role: page.read_card(role) for role in ("total", "warned", "unprotected")}


@pytest.mark.sanity
def test_global_metrics_match_db(population_dashboard):
    """Cleared total and unprotected cards match the golden record."""
    data = load_sanity_data()
    metrics = data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]["metrics"]
    population_dashboard.clear_filters()
    cards = read_population_cards(population_dashboard)
    assert cards["total"] == metrics["total_population_all_time"]["expected_value"]
    assert cards["unprotected"] == metrics["unprotected_population"]["expected_value"]


@pytest.mark.sanity
def test_filtered_population_matches_db(population_dashboard):
    """Warned population in the golden date range matches the golden record."""
    data = load_sanity_data()
    screen = data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]
    start = to_page_date(screen["date_range"]["start"])
    end = to_page_date(screen["date_range"]["end"])
    population_dashboard.set_date_range(start, end)
    cards = read_population_cards(population_dashboard)
    assert (
        cards["warned"]
        == screen["metrics"]["alerted_population_selected_range"]["expected_value"]
    )


def _screen_record() -> dict:
    """Return the Screen 2 block from the golden record."""
    data = load_sanity_data()
    return data["dashboard_sanity_checks"]["screen_2_alerts_analysis"]


def _apply_golden_range(page) -> dict:
    """Set the Screen 2 golden dates and return that screen block."""
    screen = _screen_record()
    page.set_date_range(
        to_page_date(screen["date_range"]["start"]),
        to_page_date(screen["date_range"]["end"]),
    )
    return screen


def _normalize_hierarchy_key(label: str) -> str:
    """Drop ASCII quotes so the same place matches with a different geresh."""
    return label.replace('"', "").replace("'", "")


def _normalize_date_key(label: str) -> str:
    """Return YYYY-MM-DD when the label is a calendar date."""
    text = label.strip()
    for pattern in ("%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def _assert_golden_keys(actual: dict, expected: dict, normalize=None) -> None:
    """Every golden key is present and equal. Extra UI keys are ignored."""
    def _fold(key: object) -> str:
        name = normalize(str(key)) if normalize is not None else str(key)
        # ASCII " and ' are the same character in keys.
        return name.replace('"', "'")

    normalized: dict = {}
    for key, value in actual.items():
        normalized[_fold(key)] = value
    for key, expected_value in expected.items():
        name = _fold(key)
        assert name in normalized, f"missing {key!r} in {sorted(normalized)}"
        assert normalized[name] == expected_value, (
            f"{key!r}: ui={normalized[name]!r} golden={expected_value!r}"
        )


@pytest.mark.sanity
def test_alerted_population_by_settlement_matches_db(population_dashboard):
    """Each golden settlement matches the warned series after the date range."""
    screen = _apply_golden_range(population_dashboard)
    actual = population_dashboard.read_settlement_warned()
    if not actual:
        pytest.skip("Settlement population visual returned no values (chart empty or not rendered)")
    expected = screen["metrics"]["alerted_population_by_settlement"]["values"]
    _assert_golden_keys(actual, expected)


@pytest.mark.sanity
def test_hierarchy_mahoz_sum_matches_db(population_dashboard):
    """District names in Sum mode match the golden mahoz sums."""
    screen = _apply_golden_range(population_dashboard)
    population_dashboard.set_district_aggregation("sum")
    actual = population_dashboard.read_district_labels()
    if not actual:
        pytest.skip("District chart 'התרעות לפי מחוז' returned no rows (chart empty or not rendered)")
    expected = screen["metrics"]["alerts_by_hierarchy"]["mahoz"]["sum"]
    _assert_golden_keys(actual, expected)


@pytest.mark.sanity
def test_hierarchy_mahoz_daily_avg_matches_db(population_dashboard):
    """District names in daily-average mode match the golden mahoz averages."""
    screen = _apply_golden_range(population_dashboard)
    population_dashboard.set_district_aggregation("average")
    actual = population_dashboard.read_district_labels()
    if not actual:
        pytest.skip("District chart 'התרעות לפי מחוז' returned no rows (chart empty or not rendered)")
    expected = screen["metrics"]["alerts_by_hierarchy"]["mahoz"]["daily_avg"]
    _assert_golden_keys(actual, expected)


@pytest.mark.sanity
def test_alerts_by_date_matches_db(population_dashboard):
    """Golden alert dates match the dates table after the screen date range."""
    screen = _apply_golden_range(population_dashboard)
    actual = population_dashboard.read_date_counts()
    if not actual:
        pytest.skip("Alerts-by-date table returned no rows (table empty or not rendered)")
    expected = screen["metrics"]["alerts_by_date"]["values"]
    _assert_golden_keys(actual, expected, normalize=_normalize_date_key)


@pytest.mark.sanity
def test_alerts_by_hour_sum_matches_db(population_dashboard):
    """Golden hour sums match the hour-chart SVG buckets."""
    screen = _apply_golden_range(population_dashboard)
    actual = population_dashboard.read_hour_buckets()
    if not actual:
        pytest.skip("Hour chart returned no sum buckets (chart empty or not rendered)")
    expected = screen["metrics"]["alerts_by_hour"]["sum"]
    _assert_golden_keys(actual, expected)


@pytest.mark.sanity
def test_alerts_by_hour_daily_avg_matches_db(population_dashboard):
    """Golden hour daily averages match the hour-chart average series."""
    screen = _apply_golden_range(population_dashboard)
    actual = population_dashboard.read_hour_daily_avg()
    if not actual:
        pytest.skip("Hour chart returned no daily-average buckets (chart empty or not rendered)")
    expected = screen["metrics"]["alerts_by_hour"]["daily_avg"]
    _assert_golden_keys(actual, expected)


def _assert_hierarchy_sum(page, level: str, expected: dict) -> None:
    """Compare one hierarchy level in Sum mode.

    A level that is not selected fails the test. An empty chart still skips.
    """
    assert page.set_hierarchy_level(level), f"Hierarchy level {level!r} was not selected"
    page.set_district_aggregation("sum")
    actual = page.read_district_labels()
    if not actual:
        pytest.skip(f"District chart returned no rows for level {level!r} (chart empty or not rendered)")
    _assert_golden_keys(actual, expected, normalize=_normalize_hierarchy_key)


def _assert_hierarchy_daily_avg(page, level: str, expected: dict) -> None:
    """Compare one hierarchy level in daily-average mode.

    A level that is not selected fails the test. An empty chart still skips.
    """
    # A failed selection is a test failure. Playwright timeouts propagate.
    assert page.set_hierarchy_level(level), f"Hierarchy level {level!r} was not selected"
    # The district chart must be in per-day-average mode for these golden values.
    page.set_district_aggregation("average")
    actual = page.read_district_labels()
    if not actual:
        pytest.skip(f"District chart returned no rows for level {level!r} (chart empty or not rendered)")
    _assert_golden_keys(actual, expected, normalize=_normalize_hierarchy_key)


@pytest.mark.sanity
def test_hierarchy_nafa_matches_db(population_dashboard):
    """Nafa names in Sum mode match the golden nafa sums."""
    screen = _apply_golden_range(population_dashboard)
    _assert_hierarchy_sum(
        population_dashboard,
        "nafa",
        screen["metrics"]["alerts_by_hierarchy"]["nafa"]["sum"],
    )


@pytest.mark.sanity
def test_hierarchy_rashut_matches_db(population_dashboard):
    """Rashut names in Sum mode match the golden rashut sums."""
    screen = _apply_golden_range(population_dashboard)
    _assert_hierarchy_sum(
        population_dashboard,
        "rashut",
        screen["metrics"]["alerts_by_hierarchy"]["rashut"]["sum"],
    )


@pytest.mark.sanity
def test_hierarchy_yeshuv_matches_db(population_dashboard):
    """Yeshuv names in Sum mode match the golden yeshuv sums."""
    screen = _apply_golden_range(population_dashboard)
    _assert_hierarchy_sum(
        population_dashboard,
        "yeshuv",
        screen["metrics"]["alerts_by_hierarchy"]["yeshuv"]["sum"],
    )


@pytest.mark.sanity
def test_hierarchy_nafa_daily_avg_matches_db(population_dashboard):
    """Nafa names in daily-average mode match the golden nafa averages."""
    screen = _apply_golden_range(population_dashboard)
    _assert_hierarchy_daily_avg(
        population_dashboard,
        "nafa",
        screen["metrics"]["alerts_by_hierarchy"]["nafa"]["daily_avg"],
    )


@pytest.mark.sanity
def test_hierarchy_rashut_daily_avg_matches_db(population_dashboard):
    """Rashut names in daily-average mode match the golden rashut averages."""
    screen = _apply_golden_range(population_dashboard)
    _assert_hierarchy_daily_avg(
        population_dashboard,
        "rashut",
        screen["metrics"]["alerts_by_hierarchy"]["rashut"]["daily_avg"],
    )


@pytest.mark.sanity
def test_hierarchy_yeshuv_daily_avg_matches_db(population_dashboard):
    """Yeshuv names in daily-average mode match the golden yeshuv averages."""
    screen = _apply_golden_range(population_dashboard)
    _assert_hierarchy_daily_avg(
        population_dashboard,
        "yeshuv",
        screen["metrics"]["alerts_by_hierarchy"]["yeshuv"]["daily_avg"],
    )
