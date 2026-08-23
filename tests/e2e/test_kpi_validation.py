import pytest

from reports.allure_catalog import FEATURE_KPI_ACCURACY, suite_marks
from reports.test_run_report import get_current_report
from tests.helpers.dashboard_validation import (
    DISTRICT_KEYS,
    KPI_TYPES,
    assert_all_kpis_match_db,
    assert_kpi_matches_db,
    apply_filters,
    db_filter_kwargs,
)

pytestmark = suite_marks(feature=FEATURE_KPI_ACCURACY)


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
    db_filters = db_filter_kwargs(resolved)
    db_kpis = db_client.get_dashboard_kpis(**db_filters)
    ui_value = dashboard.get_kpi_value(kpi_type)
    db_value = db_kpis[kpi_type]
    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label=f"KPI '{kpi_type}'",
            ui_value=ui_value,
            db_value=db_value,
            passed=ui_value == db_value,
            filters=db_filters,
        )
    assert ui_value == db_value
