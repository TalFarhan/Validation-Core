"""Chart tooltip coverage — presence (UX) and value match vs warehouse."""

import pytest

from tests.ui.fleet_dashboard.dashboard_validation import (
    CHART_DB_KEYS,
    CHART_KEYS,
    apply_filters,
    assert_chart_tooltips_match_db_sample,
    db_filter_kwargs,
    get_chart_breakdown,
)

@pytest.mark.sanity
@pytest.mark.regression
@pytest.mark.parametrize("chart_key", CHART_KEYS, ids=list(CHART_KEYS))
def test_chart_tooltip_appears_on_hover(dashboard, chart_key):
    """Every chart must expose a non-empty tooltip when hovered."""
    dashboard.assert_chart_visible(chart_key)
    dashboard.hover_chart(chart_key)
    dashboard.assert_tooltip_visible()
    assert dashboard.get_tooltip_text(), f"Empty tooltip for chart '{chart_key}'"

@pytest.mark.sanity
@pytest.mark.regression
@pytest.mark.parametrize("chart_key", CHART_KEYS, ids=list(CHART_KEYS))
def test_chart_tooltip_dismisses_on_leave(dashboard, chart_key):
    """Tooltip must close after the pointer leaves the chart."""
    dashboard.assert_chart_visible(chart_key)
    dashboard.hover_chart(chart_key)
    dashboard.assert_tooltip_visible()
    dashboard.dismiss_tooltip()
    dashboard.assert_tooltip_hidden()

@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("chart_key", CHART_DB_KEYS, ids=list(CHART_DB_KEYS))
def test_chart_tooltip_segment_matches_db(dashboard, db_client, chart_key):
    """Largest segments on source/unit/withdrawal charts must match DB counts."""
    breakdown = get_chart_breakdown(db_client, chart_key)
    if not breakdown:
        pytest.skip(f"No warehouse segments for chart '{chart_key}'")

    assert_chart_tooltips_match_db_sample(
        dashboard,
        db_client,
        chart_key,
        sample_size=2,
    )

@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("chart_key", CHART_DB_KEYS, ids=list(CHART_DB_KEYS))
def test_chart_tooltip_matches_db_after_filter(
    dashboard, filter_data, db_client, chart_key
):
    """Filtered chart tooltips must match the filtered warehouse breakdown."""
    resolved = apply_filters(dashboard, filter_data, district="dan")
    db_filters = db_filter_kwargs(resolved)
    breakdown = get_chart_breakdown(db_client, chart_key, **db_filters)
    if not breakdown:
        pytest.skip(
            f"No warehouse segments for chart '{chart_key}' with filters={db_filters}"
        )

    assert_chart_tooltips_match_db_sample(
        dashboard,
        db_client,
        chart_key,
        sample_size=2,
        **db_filters,
    )
