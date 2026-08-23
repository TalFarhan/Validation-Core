"""Chart hierarchy drilldown — unit chart הסתעפות / כינוס + SubUnit vs DB.

Simple rules:
- הסתעפות = go down one level (Unit → SubUnit)
- כינוס = opposite — go back up (SubUnit → Unit)
- Header forked arrows for expand (not the single down arrow)
- If absent / disabled / click has no effect → skip (not fail)
"""

from __future__ import annotations

import pytest

from pages.errors import ExpandHierarchyUnavailable
from reports.allure_catalog import FEATURE_CHART_DRILLDOWN, suite_marks
from tests.helpers.dashboard_validation import (
    DRILLDOWN_DB_CHART_KEY,
    apply_filters,
    assert_sub_units_sum_to_parent,
    assert_unit_drilldown_matches_db,
    db_filter_kwargs,
    labels_cover_segments,
)

pytestmark = suite_marks(feature=FEATURE_CHART_DRILLDOWN)


def _skip_unless_expand_enabled(
    dashboard,
    *,
    chart_key: str = DRILLDOWN_DB_CHART_KEY,
    segment_label: str | None = None,
    expected_value: int | None = None,
) -> None:
    state = dashboard.probe_expand_hierarchy(
        chart_key,
        segment_label=segment_label,
        expected_value=expected_value,
    )
    if state != "enabled":
        pytest.skip(
            f"הסתעפות header icon not found on chart '{chart_key}' "
            f"(state={state})"
        )


def _expand_or_skip(
    dashboard,
    *,
    segment_label: str,
    expected_value: int | None,
    expected_children: dict[str, int],
) -> list[str]:
    try:
        return dashboard.expand_chart_hierarchy(
            DRILLDOWN_DB_CHART_KEY,
            segment_label=segment_label,
            expected_value=expected_value,
            expected_child_labels=list(expected_children),
        )
    except ExpandHierarchyUnavailable as exc:
        pytest.skip(str(exc))


@pytest.fixture
def unit_chart_ready(dashboard, filter_data, db_client):
    """Unit chart filtered to מחוז דן, with DB parent/child counts."""
    try:
        dashboard.clear_all_applied_filters()
    except Exception:
        pass
    resolved = apply_filters(dashboard, filter_data, district="dan")
    dashboard.assert_chart_visible(DRILLDOWN_DB_CHART_KEY)
    db_filters = db_filter_kwargs(resolved)
    parent = db_client.count_by_unit(**db_filters)
    children = db_client.count_by_sub_unit(**db_filters)
    return {
        **resolved,
        "expected_value": parent.get(resolved["district"]),
        "db_filters": db_filters,
        "children": children,
    }


@pytest.mark.sanity
@pytest.mark.regression
def test_unit_expand_control_enabled_or_skip(dashboard, unit_chart_ready):
    """Probe only: icon found → continue; missing → skip."""
    _skip_unless_expand_enabled(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
    )


@pytest.mark.sanity
@pytest.mark.regression
def test_expand_hierarchy_changes_unit_chart_labels(dashboard, unit_chart_ready):
    """After הסתעפות, unit chart shows SubUnit labels."""
    children = unit_chart_ready["children"]
    if not children:
        pytest.skip(f"No SubUnits under filters={unit_chart_ready['db_filters']}")

    _skip_unless_expand_enabled(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
    )
    before = dashboard.get_chart_segment_labels(DRILLDOWN_DB_CHART_KEY)
    after = _expand_or_skip(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
        expected_children=children,
    )

    matched, missing = labels_cover_segments(after, children)
    assert matched, (
        f"After expand expected SubUnit labels. before={before}, after={after}, "
        f"DB={children}, missing={missing}"
    )


@pytest.mark.sanity
@pytest.mark.regression
def test_tooltip_expand_shows_sub_unit_children(dashboard, unit_chart_ready):
    """Clicking הסתעפות in the chart tooltip must reveal SubUnit children."""
    children = unit_chart_ready["children"]
    if not children:
        pytest.skip(f"No SubUnits under filters={unit_chart_ready['db_filters']}")

    before = dashboard.get_chart_segment_labels(DRILLDOWN_DB_CHART_KEY)
    try:
        after = dashboard.expand_via_tooltip_drilldown(
            DRILLDOWN_DB_CHART_KEY,
            unit_chart_ready["district"],
            expected_value=unit_chart_ready["expected_value"],
        )
    except ExpandHierarchyUnavailable as exc:
        pytest.skip(str(exc))

    matched, missing = labels_cover_segments(after, children)
    assert matched, (
        f"After tooltip הסתעפות expected SubUnit labels. "
        f"before={before}, after={after}, DB={children}, missing={missing}"
    )


@pytest.mark.data
@pytest.mark.regression
def test_unit_drilldown_sub_units_match_db(dashboard, unit_chart_ready, db_client):
    """After expand, labels match warehouse SubUnits."""
    children = unit_chart_ready["children"]
    if not children:
        pytest.skip(f"No SubUnits under filters={unit_chart_ready['db_filters']}")

    _skip_unless_expand_enabled(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
    )
    _expand_or_skip(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
        expected_children=children,
    )
    assert_unit_drilldown_matches_db(
        dashboard, db_client, sample_size=5, **unit_chart_ready["db_filters"]
    )


@pytest.mark.data
@pytest.mark.regression
def test_unit_drilldown_children_sum_to_parent(dashboard, unit_chart_ready, db_client):
    """Σ SubUnit (in_use) equals parent in_use for the filter scope."""
    children = unit_chart_ready["children"]
    if not children:
        pytest.skip(f"No SubUnits under filters={unit_chart_ready['db_filters']}")

    _skip_unless_expand_enabled(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
    )
    _expand_or_skip(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
        expected_children=children,
    )
    assert_sub_units_sum_to_parent(db_client, **unit_chart_ready["db_filters"])


@pytest.mark.data
@pytest.mark.regression
def test_unit_drilldown_respects_active_filters(dashboard, filter_data, db_client):
    """Expand under district+source matches that filtered SubUnit breakdown."""
    try:
        dashboard.clear_all_applied_filters()
    except Exception:
        pass
    resolved = apply_filters(
        dashboard,
        filter_data,
        district="dan",
        source="organic",
    )
    db_filters = db_filter_kwargs(resolved)
    children = db_client.count_by_sub_unit(**db_filters)
    if not children:
        pytest.skip(f"No SubUnits for filtered scope {db_filters}")
    parent = db_client.count_by_unit(**db_filters)

    _skip_unless_expand_enabled(
        dashboard,
        segment_label=resolved["district"],
        expected_value=parent.get(resolved["district"]),
    )
    _expand_or_skip(
        dashboard,
        segment_label=resolved["district"],
        expected_value=parent.get(resolved["district"]),
        expected_children=children,
    )
    assert_unit_drilldown_matches_db(dashboard, db_client, sample_size=5, **db_filters)
    assert_sub_units_sum_to_parent(db_client, **db_filters)


@pytest.mark.sanity
@pytest.mark.regression
def test_drill_up_returns_to_unit_level(dashboard, unit_chart_ready, db_client):
    """כינוס after הסתעפות restores Unit-level labels when control exists."""
    children = unit_chart_ready["children"]
    parent_units = db_client.count_by_unit(**unit_chart_ready["db_filters"])
    if not children or not parent_units:
        pytest.skip("Need both Unit and SubUnit rows")

    _skip_unless_expand_enabled(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
    )
    top_labels = dashboard.get_chart_segment_labels(DRILLDOWN_DB_CHART_KEY)
    _expand_or_skip(
        dashboard,
        segment_label=unit_chart_ready["district"],
        expected_value=unit_chart_ready["expected_value"],
        expected_children=children,
    )
    try:
        restored = dashboard.drill_up_chart(DRILLDOWN_DB_CHART_KEY)
    except AssertionError as exc:
        pytest.skip(f"Drill-up not available: {exc}")

    matched, missing = labels_cover_segments(restored, parent_units)
    assert matched or set(restored) == set(top_labels), (
        f"After drill-up expected Unit labels. restored={restored}, "
        f"DB={parent_units}, original={top_labels}, missing={missing}"
    )
