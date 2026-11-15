"""Population page module checks. No browser."""

from pages.alerts_analysis.page import AlertsAnalysisPage
from pages.alerts_analysis.population_page import AlertsPopulationPage

_PAGE1_SCOPES = (
    "ירי רקטות וטילים",
    "חדירת מחבלים",
    "חדירת כלי טיס עוין",
    "אוכלוסייה מותרעת",
    "אזורי התרעה תחת ירי",
)


def test_population_page_module():
    assert issubclass(AlertsPopulationPage, AlertsAnalysisPage)
    assert AlertsPopulationPage.district_chart_title_for("mahoz") == "התרעות לפי מחוז"
    title = AlertsPopulationPage.PAGE_TITLE
    assert title.strip()
    assert "בין" not in title
    for scope in _PAGE1_SCOPES:
        assert title != scope
        assert title not in scope
        assert scope not in title
    source = (
        __import__("pathlib")
        .Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("ui", "alerts_analysis_dashboard", "conftest.py")
        .read_text(encoding="utf-8")
    )
    assert "bind_dashboard(AlertsAnalysisPage)" in source
    assert 'bind_dashboard(AlertsPopulationPage, "population_dashboard")' in source
