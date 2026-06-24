import pytest


@pytest.mark.data
@pytest.mark.skip(reason="Enable after QA DB is configured and count_vehicles is implemented.")
def test_total_kpi_matches_db(dashboard, db_client, filter_data):
    """Validates that the dashboard total KPI matches the warehouse count."""
    district = filter_data["districts"]["dan"]
    dashboard.select_district(district)

    ui_total = dashboard.get_kpi_value("total")
    db_total = db_client.count_vehicles(district=district)

    assert ui_total == db_total, (
        f"UI total ({ui_total}) does not match DB count ({db_total}) for district '{district}'."
    )
