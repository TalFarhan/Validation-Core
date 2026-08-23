"""Canonical Allure epic / feature labels for the Fleet Dashboard suite.

Use these constants via ``pytestmark`` on test modules so the HTML report
groups tests into a stable business hierarchy (not a flat file list).
"""

from __future__ import annotations

import allure

# Single product surface under validation.
EPIC = "Fleet Dashboard Validation"

# Per-area features — one per test module (or closely related modules).
FEATURE_UI_SMOKE = "UI Smoke"
FEATURE_UI_FILTERS = "UI Filters"
FEATURE_KPI_ACCURACY = "KPI Accuracy"
FEATURE_FILTER_COMBINATIONS = "Filter Combinations"
FEATURE_CHARTS = "Charts"
FEATURE_CHART_TOOLTIPS = "Chart Tooltips"
FEATURE_CHART_DRILLDOWN = "Chart Drilldown"
FEATURE_VEHICLE_TABLE = "Vehicle Table"
FEATURE_DATA_INTEGRITY = "Data Integrity"
FEATURE_EDGE_CASES = "Edge Cases"


def suite_marks(*, feature: str) -> list:
    """Module-level pytestmark: epic + feature."""
    return [
        allure.epic(EPIC),
        allure.feature(feature),
    ]
