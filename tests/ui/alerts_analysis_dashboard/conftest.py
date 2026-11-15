import pytest

from db.clients.alerts import AlertsDBRunner
from tests.helpers.dashboard_fixture import bind_dashboard
from pages.alerts_analysis.page import AlertsAnalysisPage
from pages.alerts_analysis.population_page import AlertsPopulationPage

dashboard = bind_dashboard(AlertsAnalysisPage)
population_dashboard = bind_dashboard(AlertsPopulationPage, "population_dashboard")


@pytest.fixture(scope="session")
def alerts_db():
    """Read-only Alerts DB runner for UI-to-DB parity validation."""
    return AlertsDBRunner()
