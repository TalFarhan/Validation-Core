import pytest

from config.settings import settings


@pytest.mark.data
def test_north_truck_transport_center_matches_db(
    dashboard, db_client, filter_data, vehicle_data
):
    """Validates sample vehicle 111111 in DB and matching dashboard KPI count."""
    expected = vehicle_data["vehicle_111111"]
    district = filter_data["districts"]["north"]
    category = filter_data["categories"]["truck"]
    source = filter_data["sources"]["transport_center"]

    db_vehicle = db_client.get_vehicle_by_id(expected["VehicleID"])
    comparable_fields = (
        "Unit",
        "SubUnit",
        "VehicleCategory",
        "VehicleSource",
        "VehicleFuel",
        "IsActive",
        "Environment",
    )
    for field in comparable_fields:
        assert db_vehicle[field] == expected[field], (
            f"DB field '{field}' ({db_vehicle[field]!r}) "
            f"does not match expected snapshot ({expected[field]!r})."
        )

    dashboard.select_district(district)
    dashboard.select_category(category)
    dashboard.select_source(source)

    ui_total = dashboard.get_kpi_value("total")
    assert ui_total >= 1, "Filtered total should include sample vehicle 111111."

    if settings.DB_MODE != "live":
        return

    db_total = db_client.count_vehicles(
        district=district,
        category=category,
        source=source,
        environment=expected["Environment"],
    )

    assert ui_total == db_total, (
        f"UI total ({ui_total}) does not match DB count ({db_total}) "
        f"for Unit='{district}', VehicleCategory='{category}', VehicleSource='{source}'."
    )
