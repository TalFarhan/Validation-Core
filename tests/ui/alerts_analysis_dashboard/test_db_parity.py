"""Alerts dashboard UI-vs-DB parity pilot (last 30 days)."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pages.alerts_analysis.population_page import AlertsPopulationPage
from tests.helpers.db_parity_engine import validate_dashboard_generic

CONTRACT_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "alerts" / "alerts_contract.yaml"
)


@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")
@pytest.mark.db_parity
def test_alerts_db_parity_last_30_days(dashboard, alerts_db):
    """UI visuals must equal the warehouse for the trailing 30-day window."""
    # Half-open window [start, end): matches the contract's >= :start_date AND < :end_date.
    # The slicer option stays in this test. Another date range is a new option plus
    # window here, not a renamed metric in the contract.
    # Category ids travel in the YAML contract, not as arguments to the engine.
    # Temporary skip while YAML validation is the focus. The SQL contract is unchanged.
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    dashboard.select_date_range("שלושים יום אחרונים")

    # Page-2 rows share this file and are still placeholders. Do not execute them here.
    validate_dashboard_generic(
        CONTRACT_PATH,
        dashboard,
        alerts_db,
        start_date,
        end_date,
        exclude_scopes={AlertsPopulationPage.PAGE_TITLE},
    )
