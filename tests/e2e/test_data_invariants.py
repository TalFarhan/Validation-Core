import pytest

@pytest.mark.data
@pytest.mark.regression
def test_db_in_use_not_exceeds_total(db_client):
    """In-use vehicles are a subset of received vehicles on DIM."""
    kpis = db_client.get_dashboard_kpis()
    assert kpis["in_use"] <= kpis["total"]

@pytest.mark.data
@pytest.mark.regression
def test_ui_in_use_not_exceeds_total(dashboard):
    """In-use KPI cannot exceed total received on the dashboard."""
    assert dashboard.get_kpi_value("in_use") <= dashboard.get_kpi_value("total")

@pytest.mark.data
@pytest.mark.regression
def test_db_withdrawn_comes_from_fact_table(db_client):
    """Withdrawn KPI counts rows in FACT.SigningReturnVehicle (not DIM IsActive=0)."""
    kpis = db_client.get_dashboard_kpis()
    assert kpis["withdrawn"] == db_client.count_vehicles(kpi_type="withdrawn")
    assert kpis["withdrawn"] >= 0

@pytest.mark.data
@pytest.mark.regression
def test_db_allocated_comes_from_fact_table(db_client):
    """Allocated KPI counts rows in FACT.VehicleFlow."""
    kpis = db_client.get_dashboard_kpis()
    assert kpis["allocated"] == db_client.count_vehicles(kpi_type="allocated")
    assert kpis["allocated"] >= 0

@pytest.mark.data
@pytest.mark.regression
def test_db_source_breakdown_sums_to_in_use(db_client):
    """Source chart segments must sum to the in-use total."""
    by_source = db_client.count_by_source()
    if not by_source:
        pytest.skip("No in-use vehicles grouped by source")
    assert sum(by_source.values()) == db_client.count_vehicles(kpi_type="in_use")

@pytest.mark.data
@pytest.mark.regression
def test_db_unit_breakdown_sums_to_in_use(db_client):
    """Unit chart segments must sum to the in-use total."""
    by_unit = db_client.count_by_unit()
    if not by_unit:
        pytest.skip("No in-use vehicles grouped by unit")
    assert sum(by_unit.values()) == db_client.count_vehicles(kpi_type="in_use")

@pytest.mark.data
@pytest.mark.regression
def test_db_category_breakdown_sums_to_total(db_client):
    """Category chart segments must sum to the total vehicle count."""
    by_category = db_client.count_by_category()
    if not by_category:
        pytest.skip("No vehicles grouped by category")
    assert sum(by_category.values()) == db_client.count_vehicles(kpi_type="total")

@pytest.mark.data
@pytest.mark.regression
def test_db_withdrawal_reason_breakdown_sums_to_withdrawn(db_client):
    """Withdrawal-reason segments must sum to the withdrawn FACT total."""
    by_reason = db_client.count_by_withdrawal_reason()
    if not by_reason:
        pytest.skip("No TransferReason rows in SigningReturnVehicle")
    assert sum(by_reason.values()) == db_client.count_vehicles(kpi_type="withdrawn")
