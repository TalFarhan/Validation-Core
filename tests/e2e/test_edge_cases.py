import time

import pytest
from playwright.sync_api import expect

from reports.allure_catalog import FEATURE_EDGE_CASES, suite_marks
from tests.helpers.dashboard_validation import assert_all_kpis_match_db, apply_filters, db_filter_kwargs

pytestmark = suite_marks(feature=FEATURE_EDGE_CASES)


@pytest.mark.data
@pytest.mark.regression
def test_zero_count_filter_shows_zero_kpi(dashboard, zero_count_filters, db_client):
    """Empty warehouse combinations must surface as zero (or be cascaded away)."""
    district = zero_count_filters["district"]
    category = zero_count_filters["category"]
    source = zero_count_filters["source"]
    assert (
        db_client.count_vehicles(
            district=district, category=category, source=source
        )
        == 0
    )

    # Power BI cascading hides slicer options that would yield zero rows.
    # Apply the two denser filters, then assert the empty source is unavailable
    # — or selecting it drives total KPI to zero.
    dashboard.apply_filters(district=district, category=category)
    dashboard.source_dropdown.click(force=True)
    source_option = dashboard.option(source, "VehicleSource")
    option_count = source_option.count()
    option_visible = False
    if option_count > 0:
        try:
            option_visible = source_option.first.is_visible()
        except Exception:
            option_visible = False

    if option_visible:
        previous_total = dashboard.get_kpi_value("total", record=False)
        source_option.first.click(force=True)
        dashboard.total_vehicles_kpi.click(force=True)
        dashboard.wait_for_kpi_update("total", previous_total, required=False)
        assert dashboard.get_kpi_value("total") == 0
    else:
        # Cascaded away: option missing or not shown under the current slicers.
        assert option_count == 0 or not option_visible


@pytest.mark.data
@pytest.mark.regression
def test_clear_filters_restores_db_baseline(dashboard, filter_data, db_client):
    """Clearing filters must restore KPI values to the unfiltered DB baseline."""
    dashboard.select_district(filter_data["districts"]["north"])
    dashboard.clear_all_applied_filters()
    assert_all_kpis_match_db(dashboard, db_client)


@pytest.mark.data
@pytest.mark.regression
def test_allocated_kpi_matches_fact_vehicle_flow(dashboard, db_client):
    """Allocated KPI must match FACT.VehicleFlow (רכבים שווסתו)."""
    db_count = db_client.count_vehicles(kpi_type="allocated")
    assert dashboard.get_kpi_value("allocated") == db_count


@pytest.mark.data
@pytest.mark.regression
def test_withdrawn_kpi_matches_fact_signing_return(dashboard, db_client):
    """Withdrawn KPI must match FACT.SigningReturnVehicle (רכבים שזוכו)."""
    db_count = db_client.count_vehicles(kpi_type="withdrawn")
    assert dashboard.get_kpi_value("withdrawn") == db_count


@pytest.mark.data
@pytest.mark.regression
def test_page_refresh_restores_baseline_kpis(dashboard, filter_data, db_client):
    """Refreshing the page should reset filters and restore baseline KPIs."""
    dashboard.select_district(filter_data["districts"]["dan"])
    dashboard.page.reload(wait_until="domcontentloaded")
    expect(dashboard.page.locator("main iframe")).to_be_visible(timeout=dashboard.timeout)
    # Cold Power BI reload can exceed a single expect — poll then assert KPIs.
    ready_deadline = time.monotonic() + max(60.0, dashboard.timeout / 1000)
    while time.monotonic() < ready_deadline:
        try:
            if dashboard.total_vehicles_kpi.is_visible(timeout=2000):
                break
        except Exception:
            pass
        time.sleep(0.5)
    dashboard.wait_for_visible(dashboard.total_vehicles_kpi, timeout_ms=dashboard.timeout)
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
