import json
from pathlib import Path

import pytest

from tests.helpers.dashboard_validation import (
    KPI_TYPES,
    assert_all_kpis_match_db,
    apply_filters,
    db_filter_kwargs,
)

MATRIX_PATH = Path(__file__).resolve().parents[2] / "data" / "filter_matrix.json"


def _load_matrix():
    with open(MATRIX_PATH, encoding="utf-8") as file:
        return json.load(file)


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("filter_combo", _load_matrix()["single_filters"], ids=str)
def test_single_filter_all_kpis_match_db(dashboard, filter_data, db_client, filter_combo):
    """Every single-filter scenario must keep all KPI cards aligned with the DB."""
    resolved = apply_filters(dashboard, filter_data, **filter_combo)
    assert_all_kpis_match_db(dashboard, db_client, **db_filter_kwargs(resolved))


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("filter_combo", _load_matrix()["combined_filters"], ids=str)
def test_combined_filter_all_kpis_match_db(dashboard, filter_data, db_client, filter_combo):
    """Multi-filter combinations must keep all KPI cards aligned with the DB."""
    resolved = apply_filters(dashboard, filter_data, **filter_combo)
    assert_all_kpis_match_db(dashboard, db_client, **db_filter_kwargs(resolved))


@pytest.mark.data
@pytest.mark.regression
@pytest.mark.parametrize("kpi_type", KPI_TYPES)
def test_north_truck_transport_center_matches_db(
    dashboard, filter_data, db_client, kpi_type
):
    """North + truck + transport center slice must match DB for every KPI."""
    resolved = apply_filters(
        dashboard,
        filter_data,
        district="north",
        category="truck",
        source="transport_center",
    )
    db_filters = db_filter_kwargs(resolved)
    ui_value = dashboard.get_kpi_value(kpi_type)
    db_value = db_client.count_vehicles(kpi_type=kpi_type, **db_filters)
    assert ui_value == db_value


@pytest.mark.data
@pytest.mark.regression
def test_south_sub_unit_lachish_matches_db(dashboard, filter_data, db_client):
    """South district with Lachish sub-unit must match DB baseline KPIs."""
    resolved = apply_filters(
        dashboard,
        filter_data,
        district="south",
        sub_unit="lachish",
    )
    assert_all_kpis_match_db(dashboard, db_client, **db_filter_kwargs(resolved))
