import pytest
from playwright.sync_api import expect

from config.settings import settings
from tests.helpers.dashboard_validation import assert_all_kpis_match_db, apply_filters, db_filter_kwargs


@pytest.mark.data
@pytest.mark.regression
def test_zero_count_filter_shows_zero_kpi(dashboard, zero_count_filters):
    """A filter combination with no DB rows must show zero on the dashboard."""
    dashboard.apply_filters(
        district=zero_count_filters["district"],
        category=zero_count_filters["category"],
        source=zero_count_filters["source"],
    )
    assert dashboard.get_kpi_value("total") == 0


@pytest.mark.data
@pytest.mark.regression
def test_clear_filters_restores_db_baseline(dashboard, filter_data, db_client):
    """Clearing filters must restore KPI values to the unfiltered DB baseline."""
    dashboard.select_district(filter_data["districts"]["north"])
    dashboard.clear_all_applied_filters()
    assert_all_kpis_match_db(dashboard, db_client)


@pytest.mark.data
@pytest.mark.regression
def test_allocated_kpi_when_db_flag_disabled(dashboard, db_client):
    """When DB_HAS_ALLOCATED is false, allocated KPI must be zero."""
    if settings.DB_HAS_ALLOCATED:
        pytest.skip("DB_HAS_ALLOCATED is enabled")

    assert dashboard.get_kpi_value("allocated") == 0
    assert db_client.count_vehicles(kpi_type="allocated") == 0


@pytest.mark.data
@pytest.mark.regression
def test_page_refresh_restores_baseline_kpis(dashboard, filter_data, db_client):
    """Refreshing the page should reset filters and restore baseline KPIs."""
    dashboard.select_district(filter_data["districts"]["dan"])
    dashboard.page.reload()
    expect(dashboard.page.locator("main iframe")).to_be_visible(timeout=dashboard.timeout)
    dashboard.wait_for_visible(dashboard.total_vehicles_kpi)
    assert_all_kpis_match_db(dashboard, db_client)


@pytest.mark.data
@pytest.mark.regression
def test_extreme_filter_narrows_all_kpis(dashboard, filter_data, db_client):
    """Progressively adding filters must monotonically decrease or hold KPI totals."""
    initial = db_client.get_dashboard_kpis()

    resolved = apply_filters(dashboard, filter_data, district="north")
    after_district = db_client.get_dashboard_kpis(**db_filter_kwargs(resolved))
    assert after_district["total"] <= initial["total"]

    resolved = apply_filters(
        dashboard,
        filter_data,
        district="north",
        category="truck",
        source="transport_center",
    )
    after_all = db_client.get_dashboard_kpis(**db_filter_kwargs(resolved))
    assert after_all["total"] <= after_district["total"]
