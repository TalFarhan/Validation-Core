from pages.credit_consumption.credit_consumption_page import CreditConsumptionPage
from tests.helpers.dashboard_fixture import bind_dashboard

credit_consumption_dashboard = bind_dashboard(
    CreditConsumptionPage, "credit_consumption_dashboard"
)
