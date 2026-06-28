import pytest

from tests.helpers.dashboard_validation import TAB_KPI_MAP, TAB_NAMES, apply_filters, db_filter_kwargs


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("tab_name", TAB_NAMES)
def test_tab_kpi_matches_db(dashboard, db_client, tab_name):
    """Each tab's KPI must match the warehouse count for the same status."""
    kpi_type = TAB_KPI_MAP[tab_name]
    dashboard.select_tab(tab_name)
    db_count = db_client.count_vehicles(kpi_type=kpi_type)
    assert dashboard.get_kpi_value(kpi_type) == db_count


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("tab_name", TAB_NAMES)
def test_tab_table_row_count_matches_kpi(dashboard, tab_name):
    """Visible table rows must match the KPI for the active tab."""
    kpi_type = TAB_KPI_MAP[tab_name]
    dashboard.select_tab(tab_name)
    kpi_value = dashboard.get_kpi_value(kpi_type)
    table_rows = dashboard.get_table_row_count()

    if kpi_value > 50:
        pytest.skip("Table may paginate; skipping row-count check for large result sets")

    assert table_rows == kpi_value, (
        f"Tab '{tab_name}': table rows={table_rows}, KPI={kpi_value}"
    )


@pytest.mark.data
@pytest.mark.regression
def test_vehicle_search_matches_db(dashboard, db_client):
    """Searching by vehicle ID must surface the same record as the warehouse."""
    vehicle_id = db_client.get_sample_vehicle_id(kpi_type="total")
    dashboard.select_tab("all")
    dashboard.search_vehicle(vehicle_id)

    assert dashboard.table_contains_text(str(vehicle_id))
    vehicle = db_client.get_vehicle_by_id(vehicle_id)
    assert dashboard.table_contains_text(str(vehicle["Unit"]))


@pytest.mark.data
@pytest.mark.regression
def test_filtered_tab_count_matches_db(dashboard, filter_data, db_client):
    """Filtered in-use tab must match DB count for the same filters."""
    resolved = apply_filters(dashboard, filter_data, district="dan", category="truck")
    dashboard.select_tab("in_use")

    db_count = db_client.count_vehicles(kpi_type="in_use", **db_filter_kwargs(resolved))
    assert dashboard.get_kpi_value("in_use") == db_count

    if db_count <= 50:
        assert dashboard.get_table_row_count() == db_count
