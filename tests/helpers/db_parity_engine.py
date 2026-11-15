"""Declarative UI-vs-DB parity engine.

Loads a per-report YAML contract and compares each visual to a parameterized
SQL query. Report-agnostic: titles, scopes, category ids, and SQL live in the
contract file, never here.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

from core.components.chart import Chart
from core.components.kpi import KPI
from core.components.visual import classify_presence, count_data_marks, scope_host
from reports.test_run_report import get_current_report

_VISUALS = frozenset({"kpi", "gauge", "chart", "map"})
_COMPARES = frozenset({"number", "text"})
_BIDI_MARKS = ("\u200f", "\u200e", "\u202a", "\u202b", "\u202c")
_NUMBER_TOKEN = re.compile(r"-?\d[\d.,\u00a0\u202f]*\d|-?\d")
_WHITESPACE = re.compile(r"\s+")
# Same generic Power BI chrome Chart uses to climb from a title to its visual.
_CONTAINER_XPATHS = (
    'xpath=ancestor::*[contains(@class,"visualContainerHost")][1]',
    'xpath=ancestor::*[contains(@class,"visual-container-host")][1]',
    'xpath=ancestor::*[contains(@class,"visualContainer")][1]',
    'xpath=ancestor::*[contains(@class,"visual-container")][1]',
    'xpath=ancestor::*[@role="group"][1]',
)


@dataclass(frozen=True)
class ParityResult:
    """Outcome of one comparison inside a metric."""

    name: str
    ui_value: int | float | str | None
    db_value: int | float | str | None
    passed: bool
    check: str = "value"


def _present_text(value) -> str | None:
    """Return the original string when it contains non-whitespace text."""
    if isinstance(value, str) and value.strip():
        return value
    return None


def _normalize_scope(metric: dict) -> str | None:
    """Blank scope searches the whole iframe. Any other string is kept as written."""
    scope = metric.get("scope")
    if not isinstance(scope, str) or not scope.strip():
        return None
    return scope


def _category_id(metric: dict) -> str | None:
    """Opaque category id from the contract. Blank means the bind is omitted."""
    raw = metric.get("category_id")
    if raw is None:
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    return str(raw)


def _series_index(metric: dict, yaml_path: str | Path, name: str) -> int:
    """Chart column to compare. Defaults to 0. Rejects bools and negatives."""
    if "series_index" not in metric or metric.get("series_index") is None:
        return 0
    value = metric["series_index"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(
            f"Contract {yaml_path!r} metric {name!r} series_index must be an int >= 0"
        )
    return value


def _load_metrics(yaml_path: str | Path) -> list[dict]:
    """Read and validate the contract's metrics list."""
    with open(yaml_path, encoding="utf-8") as handle:
        contract = yaml.safe_load(handle)

    if not isinstance(contract, dict) or "metrics" not in contract:
        raise ValueError(f"Contract {yaml_path!r} must define a top-level 'metrics' list")

    metrics = contract["metrics"] or []
    if not metrics:
        raise ValueError(f"Contract {yaml_path!r} has no metrics to validate")

    for index, metric in enumerate(metrics):
        if not isinstance(metric, dict):
            raise ValueError(f"Contract {yaml_path!r} metric #{index} must be a mapping")
        name = metric.get("name")
        sql = _present_text(metric.get("sql_query"))
        if not isinstance(name, str) or not name.strip() or sql is None:
            raise ValueError(
                f"Contract {yaml_path!r} metric #{index} must have 'name' and 'sql_query'"
            )
        visual = metric.get("visual") or "kpi"
        if visual not in _VISUALS:
            raise ValueError(
                f"Contract {yaml_path!r} metric {name!r} has unknown visual {visual!r}"
            )
        maximum_sql = _present_text(metric.get("maximum_sql"))
        if visual == "gauge" and maximum_sql is None:
            raise ValueError(
                f"Contract {yaml_path!r} metric {name!r} gauge requires 'maximum_sql'"
            )
        if visual != "gauge" and maximum_sql is not None:
            raise ValueError(
                f"Contract {yaml_path!r} metric {name!r} {visual} must not set 'maximum_sql'"
            )
        compare = metric.get("compare") or "number"
        if compare not in _COMPARES:
            raise ValueError(
                f"Contract {yaml_path!r} metric {name!r} has unknown compare {compare!r}"
            )
        if compare == "text" and visual != "kpi":
            raise ValueError(
                f"Contract {yaml_path!r} metric {name!r} compare 'text' is only valid for kpi"
            )
        _series_index(metric, yaml_path, name)
        metric["visual"] = visual
        metric["compare"] = compare
    return metrics


def _filters(start_date, end_date, scope, category_id) -> dict:
    """Assertion context. Optional keys are included only when set."""
    filters = {"start_date": start_date, "end_date": end_date}
    if scope is not None:
        filters["scope"] = scope
    if category_id is not None:
        filters["category_id"] = category_id
    return filters


def _scalar(db_client, sql, start_date, end_date, category_id):
    """Call scalar, omitting category_id when this metric does not set one."""
    kwargs = {"start_date": start_date, "end_date": end_date}
    if category_id is not None:
        kwargs["category_id"] = category_id
    return db_client.scalar(sql, **kwargs)


def _cell(db_client, sql, start_date, end_date, category_id):
    """Call cell, omitting category_id when this metric does not set one."""
    kwargs = {"start_date": start_date, "end_date": end_date}
    if category_id is not None:
        kwargs["category_id"] = category_id
    return db_client.cell(sql, **kwargs)


def _rows(db_client, sql, start_date, end_date, category_id):
    """Call rows with the same date and category rules as scalar."""
    kwargs = {"start_date": start_date, "end_date": end_date}
    if category_id is not None:
        kwargs["category_id"] = category_id
    return db_client.rows(sql, **kwargs)


def _log_read(report, label: str, value) -> None:
    """Log a numeric visual read. Missing numbers stay on the assertion line."""
    if report is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        return
    report.log_kpi_read(label, value)


def _log_check(report, name, check, ui_value, db_value, passed, filters) -> None:
    if report is None:
        return
    report.log_assertion(
        label=f"{name} [{check}]",
        ui_value=ui_value,
        db_value=db_value,
        passed=passed,
        filters=filters,
    )


def _status_text(raw) -> str:
    """Comparable status phrase: bidi marks removed, whitespace collapsed."""
    text = "" if raw is None else str(raw)
    for mark in _BIDI_MARKS:
        text = text.replace(mark, "")
    return _WHITESPACE.sub(" ", text).strip()


def _map_container(frame, name: str, scope: str | None):
    """Visual container for an opaque map title. Not a report-specific id."""
    host = scope_host(frame, scope)
    pattern = re.compile(re.escape(name))
    named = host.get_by_role("group", name=pattern)
    try:
        if named.count() > 0:
            return named.first
    except Exception:
        pass
    title_node = host.get_by_text(pattern).first
    for xpath in _CONTAINER_XPATHS:
        try:
            node = title_node.locator(xpath)
            if node.count() > 0:
                return node.first
        except Exception:
            continue
    return title_node


def _map_number(container):
    """First numeric token on the map, including 0. None when no number is shown."""
    try:
        raw = container.text_content(timeout=1000) or ""
    except Exception:
        return None
    for mark in _BIDI_MARKS:
        raw = raw.replace(mark, "")
    matches = _NUMBER_TOKEN.findall(raw)
    if not matches:
        return None
    token = matches[0].replace(",", "").replace("\u00a0", "").replace("\u202f", "")
    try:
        number = float(token)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def _read_map_state(frame, name: str, scope: str | None) -> str:
    """Presence of a map: a rendered 0 is value; blank with no marks is empty."""
    container = _map_container(frame, name, scope)
    number = _map_number(container)
    numbers = [None] if number is None else [number]
    return classify_presence(numbers, count_data_marks(container))


def _map_db_value(cell):
    """Map a SQL cell to a presence state. Non-numeric cells stay raw and fail."""
    if cell is None:
        return "empty"
    if isinstance(cell, bool) or not isinstance(cell, (int, float)):
        return cell
    return "value"


def _ui_cell(category, series_index: int) -> tuple[int | float | None, bool]:
    """Return the selected cell and whether the index was inside the row."""
    if series_index >= len(category.values):
        return None, False
    return category.values[series_index], True


def _chart_results(name, reading, db_rows, series_index: int) -> list[ParityResult]:
    """Match chart categories to query rows by label.

    An empty visual matches an empty row list. A label on only one side fails.
    Duplicate labels fail. A series index past the row fails even when both
    sides are missing. SQL NULL and a missing cell are both None and match.
    """
    categories = () if reading.state == "empty" else reading.categories
    if not categories and not db_rows:
        return [ParityResult(name, None, None, reading.state == "empty", "empty")]

    ui_counts: dict[str, int] = {}
    for category in categories:
        ui_counts[category.label] = ui_counts.get(category.label, 0) + 1
    db_counts: dict[str, int] = {}
    for label, _value in db_rows:
        db_counts[label] = db_counts.get(label, 0) + 1

    ui_by_label = {
        category.label: category
        for category in categories
        if ui_counts[category.label] == 1
    }
    db_by_label = {
        label: value for label, value in db_rows if db_counts[label] == 1
    }

    order: list[str] = []
    for category in categories:
        if category.label not in order:
            order.append(category.label)
    for label, _value in db_rows:
        if label not in order:
            order.append(label)

    results: list[ParityResult] = []
    for label in order:
        in_ui = label in ui_counts
        in_db = label in db_counts
        duplicated = ui_counts.get(label, 0) > 1 or db_counts.get(label, 0) > 1
        if duplicated or not in_ui or not in_db:
            ui_value = None
            db_value = None
            if in_ui and ui_counts[label] == 1:
                ui_value, _in_range = _ui_cell(ui_by_label[label], series_index)
            if in_db and db_counts[label] == 1:
                db_value = db_by_label[label]
            results.append(ParityResult(name, ui_value, db_value, False, label))
            continue
        ui_value, in_range = _ui_cell(ui_by_label[label], series_index)
        db_value = db_by_label[label]
        passed = in_range and ui_value == db_value
        results.append(ParityResult(name, ui_value, db_value, passed, label))
    return results


def validate_dashboard_generic(
    yaml_path: str | Path,
    page,
    db_client,
    start_date: datetime | date,
    end_date: datetime | date,
    exclude_scopes: Collection[str] | None = None,
) -> list[ParityResult]:
    """Compare every contract metric to the warehouse and assert equality.

    ``page`` is a ReportShell-based page object exposing the report iframe via
    ``_report_frame()``. ``db_client`` exposes ``scalar`` and, for charts, ``rows``.
    ``exclude_scopes`` skips metrics whose scope is in that set. ``None`` or an
    empty collection runs every metric. The scope strings are opaque.
    """
    metrics = _load_metrics(yaml_path)
    frame = page._report_frame()
    kpi = KPI(page=page.page, frame=frame)
    chart = Chart(page=page.page, frame=frame)
    report = get_current_report()
    excluded = set(exclude_scopes) if exclude_scopes else set()

    results: list[ParityResult] = []
    for metric in metrics:
        name = metric["name"]
        visual = metric["visual"]
        scope = _normalize_scope(metric)
        if scope in excluded:
            continue
        category_id = _category_id(metric)
        sql = metric["sql_query"]
        compare = metric["compare"]
        filters = _filters(start_date, end_date, scope, category_id)

        if visual == "kpi" and compare == "text":
            ui_value = _status_text(kpi.read_text(name, scope=scope))
            db_raw = _cell(db_client, sql, start_date, end_date, category_id)
            db_value = _status_text(db_raw) if isinstance(db_raw, str) else db_raw
            passed = isinstance(db_raw, str) and ui_value == db_value
            _log_check(report, name, "value", ui_value, db_value, passed, filters)
            results.append(ParityResult(name, ui_value, db_value, passed, "value"))
            continue

        if visual == "kpi":
            ui_value = kpi.number(name, scope=scope)
            _log_read(report, name, ui_value)
            db_value = _scalar(db_client, sql, start_date, end_date, category_id)
            passed = ui_value == db_value
            _log_check(report, name, "value", ui_value, db_value, passed, filters)
            results.append(ParityResult(name, ui_value, db_value, passed, "value"))
            continue

        if visual == "gauge":
            scale = kpi.scale(name, scope=scope)
            ui_value = scale["value"]
            db_value = _scalar(db_client, sql, start_date, end_date, category_id)
            value_passed = (
                scale["state"] != "empty" and ui_value is not None and ui_value == db_value
            )
            _log_read(report, name, ui_value)
            _log_check(report, name, "value", ui_value, db_value, value_passed, filters)
            results.append(ParityResult(name, ui_value, db_value, value_passed, "value"))

            maximum = scale["maximum"]
            maximum_sql = metric["maximum_sql"]
            db_maximum = _scalar(
                db_client, maximum_sql, start_date, end_date, category_id
            )
            maximum_passed = maximum is not None and maximum == db_maximum
            _log_read(report, f"{name} maximum", maximum)
            _log_check(
                report, name, "maximum", maximum, db_maximum, maximum_passed, filters
            )
            results.append(
                ParityResult(name, maximum, db_maximum, maximum_passed, "maximum")
            )
            continue

        if visual == "map":
            ui_value = _read_map_state(frame, name, scope)
            db_raw = _cell(db_client, sql, start_date, end_date, category_id)
            numeric = isinstance(db_raw, (int, float)) and not isinstance(db_raw, bool)
            if db_raw is None or numeric:
                db_value = _map_db_value(db_raw)
                passed = db_value == ui_value
            else:
                # Keep the raw cell, including a placeholder string, visible in the failure.
                db_value = db_raw
                passed = False
            _log_check(report, name, "presence", ui_value, db_value, passed, filters)
            results.append(ParityResult(name, ui_value, db_value, passed, "presence"))
            continue

        reading = chart.read(name, scope=scope)
        db_rows = _rows(db_client, sql, start_date, end_date, category_id)
        series_index = _series_index(metric, yaml_path, name)
        for item in _chart_results(name, reading, db_rows, series_index):
            _log_check(
                report,
                item.name,
                item.check,
                item.ui_value,
                item.db_value,
                item.passed,
                filters,
            )
            results.append(item)

    mismatches = [item for item in results if not item.passed]
    if mismatches:
        details = "; ".join(
            f"{item.name!r} check={item.check!r}: UI={item.ui_value} DB={item.db_value}"
            for item in mismatches
        )
        raise AssertionError(
            f"UI vs DB parity failed for {len(mismatches)} check(s): {details}"
        )

    return results
