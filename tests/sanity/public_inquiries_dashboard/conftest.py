from pages.public_inquiries.page import PublicInquiriesPage
from tests.helpers.dashboard_fixture import bind_dashboard

public_inquiries_dashboard = bind_dashboard(
    PublicInquiriesPage, "public_inquiries_dashboard"
)
