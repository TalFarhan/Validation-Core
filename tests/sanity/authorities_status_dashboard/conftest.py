from pages.authorities_status.page import AuthoritiesStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

authorities_status_dashboard = bind_dashboard(
    AuthoritiesStatusPage, "authorities_status_dashboard"
)
