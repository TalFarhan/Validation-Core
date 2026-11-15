from pages.status_picture.status_picture_page import StatusPicturePage
from tests.helpers.dashboard_fixture import bind_dashboard

status_picture_dashboard = bind_dashboard(
    StatusPicturePage, "status_picture_dashboard"
)
