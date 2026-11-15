import json
from pathlib import Path

import pytest

from db.clients.fleet import DatabaseClient
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage
from tests.helpers.dashboard_fixture import open_report

FLEET_DATA = Path(__file__).resolve().parents[3] / "data" / "fleet"


@pytest.fixture
def dashboard(auth_page, browser_context):
    """Reuse the open dashboard on the shared tab (reload only when needed)."""
    return open_report(MainDashboardPage, auth_page, browser_context)


@pytest.fixture(scope="session")
def db_client():
    """Read-only SQL Server client for UI-to-DB validation."""
    return DatabaseClient()


@pytest.fixture(scope="session")
def filter_data():
    with open(FLEET_DATA / "filters.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def filter_matrix():
    with open(FLEET_DATA / "filter_matrix.json", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def zero_count_filters(db_client, filter_data):
    combo = db_client.find_zero_count_filters(filter_data)
    if combo is None:
        pytest.skip("No zero-count filter combination found in test data")
    return combo
