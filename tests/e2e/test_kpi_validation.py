import pytest

from tests.helpers.dashboard_validation import (
    DISTRICT_KEYS,
    KPI_TYPES,
    assert_all_kpis_match_db,
    assert_kpi_matches_db,
    apply_filters,
    db_filter_kwargs,
)


@pytest.mark.data
@pytest.mark.regression
def test_dashboard_kpi_baseline_matches_db(dashboard, db_client):
    """Validates unfiltered KPI cards against the warehouse."""
    assert_all_kpis_match_db(dashboard, db_client)


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("district_key", DISTRICT_KEYS)
@pytest.mark.parametrize("kpi_type", KPI_TYPES)
def test_district_kpi_matches_db(dashboard, filter_data, db_client, district_key, kpi_type):
    """Each district filter must align every KPI with the database."""
    district = filter_data["districts"][district_key]
    dashboard.select_district(district)
    assert_kpi_matches_db(dashboard, db_client, kpi_type, district=district)


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("kpi_type", KPI_TYPES)
def test_filtered_kpis_match_db_get_dashboard_kpis(dashboard, filter_data, db_client, kpi_type):
    """Filtered get_dashboard_kpis() must match UI for all KPI types."""
    resolved = apply_filters(dashboard, filter_data, district="dan", category="truck")
    db_kpis = db_client.get_dashboard_kpis(**db_filter_kwargs(resolved))
    assert dashboard.get_kpi_value(kpi_type) == db_kpis[kpi_type]
