import pytest

@pytest.mark.sanity
def test_dashboard_updated_within_24_hours(dashboard):
    """Last-refresh caption on the open Alerts Analysis report must be within 24 hours."""
    dashboard.verify_freshness()
