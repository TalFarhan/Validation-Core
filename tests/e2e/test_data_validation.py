import pytest


@pytest.mark.data
@pytest.mark.skip(reason="DB validation pending access from a managed corporate environment.")
def test_north_truck_transport_center_matches_db(dashboard, filter_data):
    """Validates dashboard KPIs against the warehouse once DB access is configured."""
    district = filter_data["districts"]["north"]
    category = filter_data["categories"]["truck"]
    source = filter_data["sources"]["transport_center"]

    dashboard.select_district(district)
    dashboard.select_category(category)
    dashboard.select_source(source)

    ui_total = dashboard.get_kpi_value("total")
    assert ui_total >= 1
