"""Population page mechanics. No warehouse comparison."""

from datetime import date

from core.components.chart import Chart
from tests.ui.alerts_analysis_dashboard.population_snapshot import (
    same_snapshot,
    take_snapshot,
)


def test_population_suite_opens_second_page(population_dashboard):
    """The suite is on the population page before any later assertion."""
    anchor = population_dashboard._iframe_phrase_locator(
        population_dashboard.district_chart_title()
    )
    assert anchor.is_visible()


def test_clear_restores_population_snapshot(population_dashboard):
    """Dates, day/night, and the 0-349 range clear back to the bounded window."""
    page = population_dashboard
    page.clear_filters()
    page.set_date_range("01/09/2026", "15/10/2026")
    before = take_snapshot(page)
    page.set_between_dates("01/09/2026", "01/10/2026")
    page.set_day_night("day")
    page.set_day_night("night")
    page.set_value_range(0, 349)
    during = take_snapshot(page)
    assert not same_snapshot(before, during)
    page.clear_filters()
    page.set_date_range("01/09/2026", "15/10/2026")
    assert same_snapshot(before, take_snapshot(page))


def test_day_plus_night_equals_untoggled_sum(population_dashboard):
    """Day hours plus night hours equal the dates chart inside one date window."""
    page = population_dashboard
    page.clear_filters()
    page.set_date_range("01/09/2026", "15/10/2026")
    untoggled = page.chart_total(page.DATES_CHART)
    page.set_day_night("day")
    day = page.chart_total(page.DATES_CHART)
    page.set_day_night("off")
    page.set_day_night("night")
    night = page.chart_total(page.DATES_CHART)
    assert day + night == untoggled


def test_hour_date_and_district_sums_match(population_dashboard):
    """The 24-hour, dates, and district charts agree on one explicit date range."""
    page = population_dashboard
    page.clear_filters()
    # page.set_date_range("01/09/2026", date.today().strftime("%d/%m/%Y"))
    page.set_date_range("01/09/2026", "15/10/2026")

    page.set_district_aggregation("sum")
    hour_total = page.chart_total(page.HOUR_CHART)
    dates_total = page.chart_total(page.DATES_CHART)
    district_total = page.chart_total(page.district_chart_title())
    assert hour_total == district_total == dates_total, (
        f"hour={hour_total} district={district_total} dates={dates_total}"
    )


def test_population_cards_within_total(population_dashboard):
    """Warned and unprotected populations are each at most the total."""
    page = population_dashboard
    page.clear_filters()
    total = page.read_card("total")
    assert page.read_card("warned") <= total
    assert page.read_card("unprotected") <= total


def test_settlement_series_match_legend(population_dashboard):
    """Legend order matches the contract indexes for the two settlement series."""
    page = population_dashboard
    chart = Chart(page=page.page, frame=page._report_frame(), timeout_ms=page.timeout)
    series = chart.read(page.SETTLEMENT_CHART, scope=page.PAGE_TITLE).series
    assert series[0] == page.WARNED_SERIES
    assert series[1] == page.UNWARNED_SERIES
