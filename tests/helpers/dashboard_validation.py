"""Shared helpers for UI-to-DB dashboard validation."""

from __future__ import annotations

from typing import Any

from db.client import DatabaseClient, KpiType
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage

KPI_TYPES: tuple[KpiType, ...] = ("total", "in_use", "withdrawn", "allocated")
DISTRICT_KEYS: tuple[str, ...] = ("dan", "south", "north")
TAB_NAMES: tuple[str, ...] = ("all", "in_use", "allocated", "withdrawn")
TAB_KPI_MAP: dict[str, KpiType] = {
    "all": "total",
    "in_use": "in_use",
    "allocated": "allocated",
    "withdrawn": "withdrawn",
}

FILTER_SECTIONS = {
    "district": "districts",
    "sub_unit": "sub_units",
    "category": "categories",
    "source": "sources",
}


def resolve_filter_values(
    filter_data: dict[str, dict[str, str]], **filters: str
) -> dict[str, str]:
    """Map filter keys from filters.json to their display labels."""
    resolved: dict[str, str] = {}
    for key, value in filters.items():
        section = FILTER_SECTIONS.get(key)
        if section and value in filter_data.get(section, {}):
            resolved[key] = filter_data[section][value]
        else:
            resolved[key] = value
    return resolved


def apply_filters(
    dashboard: MainDashboardPage,
    filter_data: dict[str, dict[str, str]],
    **filters: str,
) -> dict[str, str]:
    """Apply slicers using keys or labels from filters.json."""
    resolved = resolve_filter_values(filter_data, **filters)
    dashboard.apply_filters(
        district=resolved.get("district"),
        sub_unit=resolved.get("sub_unit"),
        category=resolved.get("category"),
        source=resolved.get("source"),
    )
    return resolved


def db_filter_kwargs(resolved: dict[str, str]) -> dict[str, Any]:
    return {
        "district": resolved.get("district"),
        "sub_unit": resolved.get("sub_unit"),
        "category": resolved.get("category"),
        "source": resolved.get("source"),
    }


def assert_kpi_matches_db(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    kpi_type: KpiType,
    **db_filters: Any,
) -> None:
    ui_value = dashboard.get_kpi_value(kpi_type)
    db_value = db_client.count_vehicles(kpi_type=kpi_type, **db_filters)
    assert ui_value == db_value, (
        f"KPI '{kpi_type}' mismatch: UI={ui_value}, DB={db_value}, filters={db_filters}"
    )


def assert_all_kpis_match_db(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    **db_filters: Any,
) -> None:
    db_kpis = db_client.get_dashboard_kpis(**db_filters)
    for kpi_type in KPI_TYPES:
        assert dashboard.get_kpi_value(kpi_type) == db_kpis[kpi_type], (
            f"KPI '{kpi_type}' mismatch: UI={dashboard.get_kpi_value(kpi_type)}, "
            f"DB={db_kpis[kpi_type]}, filters={db_filters}"
        )
