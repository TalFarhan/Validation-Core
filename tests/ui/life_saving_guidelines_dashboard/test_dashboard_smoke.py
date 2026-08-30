import pytest

from reports.allure_catalog import FEATURE_UI_SMOKE, suite_marks

pytestmark = suite_marks(feature=FEATURE_UI_SMOKE)


@pytest.mark.sanity
def test_dashboard_updated_within_24_hours(dashboard):
    """Last-refresh caption on the open Life-Saving Guidelines report must be within 24 hours."""
    dashboard.verify_freshness()
