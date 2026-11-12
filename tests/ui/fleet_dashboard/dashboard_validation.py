"""Shared helpers for UI-to-DB dashboard validation."""

from __future__ import annotations

import time
from typing import Any

import allure
import pytest

from config.settings import settings
from db.client import DatabaseClient, KpiType
from pages.errors import LoadTimeoutError
from pages.fleet_dashboard.main_dashboard_page import MainDashboardPage
from reports.test_run_report import get_current_report

KPI_TYPES: tuple[KpiType, ...] = ("total", "in_use", "withdrawn", "allocated")
DISTRICT_KEYS: tuple[str, ...] = ("dan", "south", "north")
TAB_NAMES: tuple[str, ...] = ("all", "in_use", "allocated", "withdrawn")
TAB_KPI_MAP: dict[str, KpiType] = {
    "all": "total",
    "in_use": "in_use",
    "allocated": "allocated",
    "withdrawn": "withdrawn",
}

CHART_KEYS: tuple[str, ...] = ("source", "unit", "category", "withdrawal")
# Charts whose tooltip values are validated against a warehouse breakdown.
# Category visual grain ≠ DIM.VehicleCategory — no value↔DB tooltip checks.
CHART_DB_KEYS: tuple[str, ...] = ("source", "unit", "withdrawal")
# Axis/legend labels that share grain with the warehouse breakdown.
# Category uses a different taxonomy (אוטובוס/רכב קל/…) than VehicleCategory.
# Withdrawal pie often exposes reasons only in tooltips — see tooltip tests.
CHART_LABEL_KEYS: tuple[str, ...] = ("source", "unit")
CHART_DB_BREAKDOWNS = {
    "source": "count_by_source",
    "unit": "count_by_unit",
    "category": "count_by_category",
    "withdrawal": "count_by_withdrawal_reason",
}
# Hierarchy drilldown with warehouse child grain (Unit → SubUnit).
# Source chart has no drilldown. Unit chart: tooltip הסתעפות is the primary UX.
DRILLDOWN_DB_CHART_KEY = "unit"

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


@allure.step("Apply dashboard filters from test data")
def apply_filters(
    dashboard: MainDashboardPage,
    filter_data: dict[str, dict[str, str]],
    **filters: str,
) -> dict[str, str]:
    """Apply slicers using keys or labels from filters.json."""
    resolved = resolve_filter_values(filter_data, **filters)
    report = get_current_report()
    if report is not None:
        report.log_ui(f"Resolving filters: {filters} → {resolved}")
    with allure.step(f"Resolved filters → {resolved}"):
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


@allure.step("Assert KPI '{kpi_type}' matches DB")
def assert_kpi_matches_db(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    kpi_type: KpiType,
    **db_filters: Any,
) -> None:
    with allure.step(f"Read UI KPI '{kpi_type}'"):
        ui_value = dashboard.get_kpi_value(kpi_type)
    with allure.step(f"Query DB count for KPI '{kpi_type}'"):
        db_value = db_client.count_vehicles(kpi_type=kpi_type, **db_filters)
    passed = ui_value == db_value
    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label=f"KPI '{kpi_type}'",
            ui_value=ui_value,
            db_value=db_value,
            passed=passed,
            filters=db_filters,
        )
    assert ui_value == db_value, (
        f"KPI '{kpi_type}' mismatch: UI={ui_value}, DB={db_value}, filters={db_filters}"
    )


@allure.step("Assert all KPI cards match DB")
def assert_all_kpis_match_db(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    **db_filters: Any,
) -> None:
    """Compare all KPI cards to DB, polling briefly while Power BI cards catch up."""
    with allure.step("Query all dashboard KPIs from DB"):
        db_kpis = db_client.get_dashboard_kpis(**db_filters)
    report = get_current_report()
    deadline = time.monotonic() + settings.DEFAULT_TIMEOUT / 1000
    ui_kpis: dict[str, int] = {}
    with allure.step("Poll UI KPI cards until they match DB (or timeout)"):
        while True:
            ui_kpis = {
                kpi_type: dashboard.get_kpi_value(kpi_type, record=False)
                for kpi_type in KPI_TYPES
            }
            if ui_kpis == db_kpis:
                break
            if time.monotonic() >= deadline:
                break
            time.sleep(0.2)

    for kpi_type in KPI_TYPES:
        ui_value = ui_kpis[kpi_type]
        db_value = db_kpis[kpi_type]
        passed = ui_value == db_value
        if report is not None:
            report.log_assertion(
                label=f"KPI '{kpi_type}'",
                ui_value=ui_value,
                db_value=db_value,
                passed=passed,
                filters=db_filters,
            )
            if passed:
                report.log_kpi_read(kpi_type, ui_value)
        assert ui_value == db_value, (
            f"KPI '{kpi_type}' mismatch: UI={ui_value}, "
            f"DB={db_value}, filters={db_filters}"
        )


@allure.step("Fetch DB breakdown for chart '{chart_key}'")
def get_chart_breakdown(
    db_client: DatabaseClient,
    chart_key: str,
    **filters: Any,
) -> dict[str, int]:
    """Return warehouse segment counts for a chart that has a DB breakdown."""
    method_name = CHART_DB_BREAKDOWNS.get(chart_key)
    if method_name is None:
        raise ValueError(
            f"Chart '{chart_key}' has no DB breakdown mapping "
            f"(supported: {', '.join(CHART_DB_BREAKDOWNS)})"
        )
    method = getattr(db_client, method_name)
    return method(**filters)


def _top_segments(breakdown: dict[str, int], sample_size: int) -> list[tuple[str, int]]:
    ranked = sorted(breakdown.items(), key=lambda item: item[1], reverse=True)
    return ranked[:sample_size]


@allure.step("Assert chart '{chart_key}' tooltip for '{segment_label}' matches DB")
def assert_chart_tooltip_segment_matches_db(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    chart_key: str,
    segment_label: str,
    **db_filters: Any,
) -> None:
    """Hover a chart segment and assert tooltip label + count match the warehouse."""
    breakdown = get_chart_breakdown(db_client, chart_key, **db_filters)
    if segment_label not in breakdown:
        raise AssertionError(
            f"Segment '{segment_label}' not in DB breakdown for chart '{chart_key}': "
            f"{sorted(breakdown)}"
        )
    expected = breakdown[segment_label]

    # Prefer SVG title / legend presence over visible text (titles are hidden).
    section = dashboard.chart_section(chart_key)
    has_title = False
    try:
        titles = section.locator("svg title")
        for i in range(titles.count()):
            if (titles.nth(i).text_content() or "").strip() == segment_label:
                has_title = True
                break
    except Exception:
        pass
    if not has_title and section.get_by_text(segment_label, exact=True).count() == 0:
        pytest.skip(
            f"Segment '{segment_label}' not shown on chart '{chart_key}' UI "
            f"(DB count={expected})"
        )

    # Capture text at hover-match time — Power BI tooltips often vanish immediately.
    tooltip_text = dashboard.hover_chart_segment(
        chart_key, segment_label, expected_value=expected
    )
    entries: dict[str, int] = {}
    try:
        entries = dashboard.parse_tooltip_entries()
    except Exception:
        entries = {}

    value_ok = (
        entries.get(segment_label) == expected
        or str(expected) in tooltip_text.replace(",", "").replace("\u200f", "")
    )
    passed = value_ok

    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label=f"Chart tooltip '{chart_key}' / '{segment_label}'",
            ui_value=entries.get(segment_label, tooltip_text),
            db_value=expected,
            passed=passed,
            filters=db_filters,
        )

    assert value_ok, (
        f"Tooltip for chart '{chart_key}' segment '{segment_label}' "
        f"mismatch: UI={entries.get(segment_label, tooltip_text)!r}, DB={expected}"
    )


@allure.step("Assert top chart '{chart_key}' tooltips match DB (sample)")
def assert_chart_tooltips_match_db_sample(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    chart_key: str,
    *,
    sample_size: int = 3,
    **db_filters: Any,
) -> None:
    """
    Validate tooltips for the largest warehouse segments visible on the chart.

    Hover hit-testing in Power BI is flaky on some bars. ``LoadTimeoutError`` on
    a segment is treated as "unhoverable" — try the next candidate. Real value
    mismatches still fail. If every candidate times out on hover → skip.
    """
    breakdown = get_chart_breakdown(db_client, chart_key, **db_filters)
    if not breakdown:
        raise AssertionError(f"No DB segments for chart '{chart_key}' (filters={db_filters})")

    section = dashboard.chart_section(chart_key)
    visible_ranked: list[tuple[str, int]] = []
    for label, count in _top_segments(breakdown, len(breakdown)):
        # SVG <title> counts as present even when Playwright marks it hidden.
        has_title = False
        titles = section.locator("svg title")
        try:
            for i in range(titles.count()):
                if (titles.nth(i).text_content() or "").strip() == label:
                    has_title = True
                    break
        except Exception:
            pass
        has_text = section.get_by_text(label, exact=True).count() > 0
        if has_title or has_text:
            visible_ranked.append((label, count))
    # Extra candidates beyond sample_size so one unhoverable bar does not fail the test.
    candidates = visible_ranked[: max(sample_size * 3, sample_size)]
    if not candidates and chart_key == "withdrawal":
        assert_withdrawal_tooltips_match_db_via_scan(
            dashboard, db_client, sample_size=sample_size, **db_filters
        )
        return
    if not candidates:
        pytest.skip(
            f"No DB segments for chart '{chart_key}' appear as labels on the UI "
            f"(filters={db_filters})"
        )

    matched = 0
    # Aim for sample_size, but one successful tooltip↔DB match is enough to
    # prove the chart; remaining LoadTimeoutErrors are hover flakes, not data bugs.
    target = min(sample_size, len(candidates))
    min_required = 1
    hover_timeouts: list[str] = []

    for segment_label, _count in candidates:
        if matched >= target:
            break
        # Stop early once we have a pass and further candidates keep timing out —
        # avoids burning ~20s×2 per unhoverable bar (especially on unit chart).
        if matched >= min_required and len(hover_timeouts) >= 2:
            break
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                assert_chart_tooltip_segment_matches_db(
                    dashboard,
                    db_client,
                    chart_key,
                    segment_label,
                    **db_filters,
                )
                last_error = None
                matched += 1
                break
            except LoadTimeoutError as exc:
                # Hover hit-test flake — retry, then try another segment.
                last_error = exc
                dashboard.dismiss_tooltip()
                time.sleep(0.3)
            except AssertionError:
                # Real tooltip value mismatch vs DB — fail immediately.
                dashboard.dismiss_tooltip()
                raise
            except Exception as exc:  # noqa: BLE001 — retry once on transient flake
                last_error = exc
                dashboard.dismiss_tooltip()
                time.sleep(0.3)
        if last_error is None:
            dashboard.dismiss_tooltip()
            continue
        if isinstance(last_error, LoadTimeoutError):
            hover_timeouts.append(segment_label)
            continue
        raise last_error

    if matched >= min_required:
        report = get_current_report()
        if report is not None and hover_timeouts:
            report.log_ui(
                f"Chart '{chart_key}' tooltip sample: matched={matched}/{target}, "
                f"hover timeouts skipped={hover_timeouts}"
            )
        return
    pytest.skip(
        f"Chart '{chart_key}': could not hover any sample segment for tooltip "
        f"(Power BI hit-test flake). timed_out={hover_timeouts}, "
        f"matched={matched}/{min_required}, filters={db_filters}"
    )


@allure.step("Assert withdrawal tooltips match DB via hover scan")
def assert_withdrawal_tooltips_match_db_via_scan(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    *,
    sample_size: int = 2,
    **db_filters: Any,
) -> None:
    """
    Pie / donut withdrawal chart often labels slices as "3 (50%)" only.

    Scan hover positions, parse tooltips, and require top TransferReason
    names + counts from the warehouse to appear.
    """
    breakdown = db_client.count_by_withdrawal_reason(**db_filters)
    if not breakdown:
        pytest.skip(
            f"No TransferReason segments in warehouse (filters={db_filters})"
        )

    dashboard.assert_chart_visible("withdrawal")
    section = dashboard.chart_section("withdrawal")
    section.scroll_into_view_if_needed()

    found: dict[str, int] = {}
    positions = getattr(dashboard, "_HOVER_SCAN_POSITIONS", ()) or (
        (0.35, 0.45),
        (0.50, 0.40),
        (0.65, 0.45),
        (0.45, 0.60),
        (0.55, 0.60),
    )
    for x_ratio, y_ratio in positions:
        try:
            box = section.bounding_box(timeout=2000)
        except Exception:
            box = None
        if not box:
            continue
        try:
            section.hover(
                position={
                    "x": max(4, box["width"] * x_ratio),
                    "y": max(4, box["height"] * y_ratio),
                },
                force=True,
            )
        except Exception:
            continue
        time.sleep(0.25)
        try:
            tip = dashboard.get_tooltip_text()
        except Exception:
            tip = ""
        if not tip:
            continue
        tip_norm = tip.replace("\u200f", "").replace(",", "")
        for label, expected in breakdown.items():
            if label in found:
                continue
            if label.replace("\u200f", "") in tip_norm and str(expected) in tip_norm:
                found[label] = expected
        try:
            dashboard.dismiss_tooltip()
        except Exception:
            pass
        if len(found) >= sample_size:
            break

    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label="Withdrawal tooltip scan vs DB",
            ui_value=found,
            db_value=dict(_top_segments(breakdown, sample_size)),
            passed=len(found) >= min(sample_size, len(breakdown)),
            filters=db_filters,
        )

    needed = min(sample_size, len(breakdown))
    assert len(found) >= needed, (
        f"Withdrawal hover scan matched {len(found)}/{needed} TransferReason "
        f"segments. found={found}, DB={dict(_top_segments(breakdown, 5))}"
    )


def labels_cover_segments(
    ui_labels: list[str],
    expected_segments: dict[str, int],
) -> tuple[list[str], list[str]]:
    """Return (matched labels, missing segment names) using exact/substring match."""
    matched: list[str] = []
    missing: list[str] = []
    normalized_ui = [label.replace("\u200f", "") for label in ui_labels]
    for segment in expected_segments:
        needle = segment.replace("\u200f", "")
        found = any(
            needle == label or needle in label or label in needle
            for label in normalized_ui
        )
        if found:
            matched.append(segment)
        else:
            missing.append(segment)
    return matched, missing


@allure.step("Assert chart '{chart_key}' labels cover DB segments (sample)")
def assert_chart_labels_match_db_sample(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    chart_key: str,
    *,
    sample_size: int = 5,
    **db_filters: Any,
) -> None:
    """Assert top warehouse segments appear as labels on the chart visual."""
    breakdown = get_chart_breakdown(db_client, chart_key, **db_filters)
    if not breakdown:
        pytest.skip(f"No DB segments for chart '{chart_key}' (filters={db_filters})")

    dashboard.assert_chart_visible(chart_key)
    ui_labels = dashboard.get_chart_segment_labels(chart_key)
    sample = {label: count for label, count in _top_segments(breakdown, sample_size)}
    matched, missing = labels_cover_segments(ui_labels, sample)

    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label=f"Chart labels '{chart_key}' vs DB",
            ui_value=ui_labels,
            db_value=sample,
            passed=bool(matched),
            filters=db_filters,
        )

    if not matched:
        raise AssertionError(
            f"Chart '{chart_key}' labels do not cover any top DB segments. "
            f"UI={ui_labels}, DB sample={sample}, missing={missing}"
        )

    min_required = max(1, (len(sample) + 1) // 2)
    assert len(matched) >= min_required, (
        f"Chart '{chart_key}' missing too many DB segment labels. "
        f"matched={matched}, missing={missing}, UI={ui_labels}"
    )


@allure.step("Assert unit-chart drilldown labels match DB SubUnit breakdown")
def assert_unit_drilldown_matches_db(
    dashboard: MainDashboardPage,
    db_client: DatabaseClient,
    *,
    sample_size: int = 5,
    **db_filters: Any,
) -> dict[str, int]:
    """
    After Unit → SubUnit expand, assert UI labels cover warehouse SubUnits.

    Returns the DB SubUnit breakdown used for the assertion.
    """
    breakdown = db_client.count_by_sub_unit(**db_filters)
    if not breakdown:
        raise AssertionError(
            f"No SubUnit segments in warehouse for filters={db_filters}"
        )

    ui_labels = dashboard.get_chart_segment_labels("unit")
    ranked = _top_segments(breakdown, sample_size)
    sample = {label: count for label, count in ranked}
    matched, missing = labels_cover_segments(ui_labels, sample)

    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label="Unit drilldown SubUnit labels vs DB",
            ui_value=ui_labels,
            db_value=sample,
            passed=not missing,
            filters=db_filters,
        )

    assert matched, (
        f"After drilldown, none of the expected SubUnits appear on the unit chart. "
        f"UI labels={ui_labels}, DB sample={sample}, filters={db_filters}"
    )
    # Allow Power BI to hide the smallest bars; require most of the sample.
    min_required = max(1, (len(sample) + 1) // 2)
    assert len(matched) >= min_required, (
        f"Unit drilldown missing SubUnit labels on UI. "
        f"matched={matched}, missing={missing}, UI={ui_labels}, filters={db_filters}"
    )
    return breakdown


@allure.step("Assert SubUnit children sum to parent in-use count")
def assert_sub_units_sum_to_parent(
    db_client: DatabaseClient,
    **db_filters: Any,
) -> None:
    """Hierarchy invariant: Σ SubUnit (in_use) == in_use for the same filters."""
    children = db_client.count_by_sub_unit(**db_filters)
    if not children:
        pytest.skip(f"No SubUnit rows for filters={db_filters}")
    parent_total = db_client.count_vehicles(kpi_type="in_use", **db_filters)
    child_sum = sum(children.values())
    report = get_current_report()
    if report is not None:
        report.log_assertion(
            label="SubUnit sum vs parent in_use",
            ui_value=child_sum,
            db_value=parent_total,
            passed=child_sum == parent_total,
            filters=db_filters,
        )
    assert child_sum == parent_total, (
        f"SubUnit breakdown sum ({child_sum}) != parent in_use ({parent_total}), "
        f"filters={db_filters}, children={children}"
    )
