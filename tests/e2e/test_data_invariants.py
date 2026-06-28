import pytest

from config.settings import settings


@pytest.mark.data
@pytest.mark.regression
def test_db_kpi_sum_invariant(db_client):
    """in_use + withdrawn must equal total in the warehouse."""
    kpis = db_client.get_dashboard_kpis()
    assert kpis["in_use"] + kpis["withdrawn"] == kpis["total"]


@pytest.mark.data
@pytest.mark.regression
def test_ui_kpi_sum_invariant(dashboard):
    """in_use + withdrawn must equal total on the dashboard."""
    total = dashboard.get_kpi_value("total")
    in_use = dashboard.get_kpi_value("in_use")
    withdrawn = dashboard.get_kpi_value("withdrawn")
    assert in_use + withdrawn == total


@pytest.mark.data
@pytest.mark.regression
def test_db_allocated_not_exceeds_in_use(db_client):
    """Allocated vehicles cannot exceed vehicles in use."""
    kpis = db_client.get_dashboard_kpis()
    assert kpis["allocated"] <= kpis["in_use"]


@pytest.mark.data
@pytest.mark.regression
def test_ui_allocated_not_exceeds_in_use(dashboard):
    """Allocated KPI cannot exceed in-use KPI on the dashboard."""
    assert dashboard.get_kpi_value("allocated") <= dashboard.get_kpi_value("in_use")


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
