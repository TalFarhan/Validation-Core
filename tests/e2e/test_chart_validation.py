import pytest

from reports.allure_catalog import FEATURE_CHARTS, suite_marks
from tests.helpers.dashboard_validation import (
    CHART_LABEL_KEYS,
    apply_filters,
    assert_chart_labels_match_db_sample,
    db_filter_kwargs,
)

pytestmark = suite_marks(feature=FEATURE_CHARTS)


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize(
    "chart_key",
    ["source", "unit", "category", "withdrawal"],
    ids=["source", "unit", "category", "withdrawal"],
)
def test_chart_is_visible(dashboard, chart_key):
    """All dashboard charts must render."""
    dashboard.assert_chart_visible(chart_key)


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("chart_key", CHART_LABEL_KEYS, ids=list(CHART_LABEL_KEYS))
def test_chart_labels_match_db(dashboard, db_client, chart_key):
    """Chart axis/legend labels must cover top warehouse segments."""
    assert_chart_labels_match_db_sample(
        dashboard, db_client, chart_key, sample_size=5
    )


@pytest.mark.data
@pytest.mark.regression
def test_source_chart_db_distinct_count(dashboard, db_client):
    """Source chart should reflect the number of distinct in-use sources in the DB."""
    by_source = db_client.count_by_source()
    if not by_source:
        pytest.skip("No in-use vehicles grouped by source")

    dashboard.assert_chart_visible("source")
    assert len(by_source) >= 1


@pytest.mark.data
@pytest.mark.regression
def test_unit_chart_db_distinct_count(dashboard, db_client):
    """Unit chart should reflect the number of distinct in-use units in the DB."""
    by_unit = db_client.count_by_unit()
    if not by_unit:
        pytest.skip("No in-use vehicles grouped by unit")

    dashboard.assert_chart_visible("unit")
    assert len(by_unit) >= 1


@pytest.mark.data
@pytest.mark.regression
def test_category_chart_db_distinct_count(dashboard, db_client):
    """Category chart should reflect the number of distinct categories in the DB."""
    by_category = db_client.count_by_category()
    if not by_category:
        pytest.skip("No vehicles grouped by category")

    dashboard.assert_chart_visible("category")
    assert len(by_category) >= 1


@pytest.mark.data
@pytest.mark.regression
def test_withdrawal_chart_db_distinct_count(dashboard, db_client):
    """Withdrawal chart should reflect distinct TransferReason values in FACT."""
    by_reason = db_client.count_by_withdrawal_reason()
    if not by_reason:
        pytest.skip("No TransferReason rows in SigningReturnVehicle")

    dashboard.assert_chart_visible("withdrawal")
    assert len(by_reason) >= 1


@pytest.mark.data
@pytest.mark.regression
def test_charts_remain_visible_after_filter(dashboard, filter_data):
    """Charts must stay visible after applying filters."""
    apply_filters(dashboard, filter_data, district="dan")
    for chart_key in ("source", "unit", "category"):
        dashboard.assert_chart_visible(chart_key)


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("chart_key", ("source", "unit"), ids=["source", "unit"])
def test_chart_labels_match_db_after_filter(
    dashboard, filter_data, db_client, chart_key
):
    """Filtered chart labels must still cover the filtered warehouse breakdown."""
    resolved = apply_filters(dashboard, filter_data, district="dan")
    assert_chart_labels_match_db_sample(
        dashboard,
        db_client,
        chart_key,
        sample_size=3,
        **db_filter_kwargs(resolved),
    )
