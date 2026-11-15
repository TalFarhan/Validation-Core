"""Arrival snapshot for the population page. Calls page methods only."""

from __future__ import annotations

from dataclasses import dataclass

from pages.alerts_analysis.population_page import AlertsPopulationPage

_CARD_ROLES = ("total", "warned", "unprotected")


@dataclass(frozen=True)
class PopulationSnapshot:
    """Three card values and the distribution totals taken on arrival."""

    cards: dict[str, int | float]
    totals: dict[str, int | float]


def take_snapshot(page: AlertsPopulationPage) -> PopulationSnapshot:
    """Read the cards and chart totals the clear test must restore."""
    cards = {role: page.read_card(role) for role in _CARD_ROLES}
    totals = {
        "hour": page.chart_total(page.HOUR_CHART),
        "dates": page.chart_total(page.DATES_CHART),
        "district": page.chart_total(page.district_chart_title()),
        "settlement_warned": page.chart_total(page.SETTLEMENT_CHART, 0),
        "settlement_unwarned": page.chart_total(page.SETTLEMENT_CHART, 1),
    }
    return PopulationSnapshot(cards=cards, totals=totals)


def same_snapshot(left: PopulationSnapshot, right: PopulationSnapshot) -> bool:
    """Exact equality, including zeros."""
    return left.cards == right.cards and left.totals == right.totals
