"""Unit tests for the declarative UI-vs-DB parity engine. No browser and no database."""

from datetime import datetime
from pathlib import Path

import pytest

from core.components.chart import ChartCategory, ChartReading
from tests.helpers import db_parity_engine as engine
from tests.helpers.db_parity_engine import validate_dashboard_generic

CONTRACT = (
    Path(__file__).resolve().parents[2] / "data" / "alerts" / "alerts_contract.yaml"
)
START = datetime(2026, 9, 1, 8, 0, 0)
END = datetime(2026, 10, 1, 8, 0, 0)


class FakePage:
    """Stand-in for a ReportShell page. The engine only needs the iframe hook."""

    page = object()

    def _report_frame(self):
        return object()


class FakeKPI:
    """Records number/scale calls. Scope is MISSING when the caller omits it."""

    number_calls: list = []
    scale_calls: list = []
    text_calls: list = []
    number_result = 1
    text_result = "Active"
    scale_result = {"state": "value", "value": 1, "minimum": None, "maximum": 10}

    def __init__(self, page, frame, timeout_ms=None):
        pass

    def number(self, title, *args, **kwargs):
        scope = args[0] if args else kwargs.get("scope", "MISSING")
        type(self).number_calls.append((title, scope))
        return type(self).number_result

    def scale(self, title, *args, **kwargs):
        scope = args[0] if args else kwargs.get("scope", "MISSING")
        type(self).scale_calls.append((title, scope))
        return dict(type(self).scale_result)

    def read_text(self, title, *args, **kwargs):
        scope = args[0] if args else kwargs.get("scope", "MISSING")
        type(self).text_calls.append((title, scope))
        return type(self).text_result


class FakeChart:
    """Records read() calls and returns a scripted ChartReading."""

    read_calls: list = []
    reading = ChartReading(title="t", categories=(), series=(), state="empty")

    def __init__(self, page, frame, timeout_ms=None):
        pass

    def read(self, title, *args, **kwargs):
        scope = args[0] if args else kwargs.get("scope", "MISSING")
        type(self).read_calls.append((title, scope))
        return type(self).reading


class FakeDB:
    """Records scalar/rows keywords. Maps each SQL string to a scripted result."""

    def __init__(self, scalars=None, rows=None, cells=None):
        self.scalars = scalars or {}
        self.row_data = rows or []
        self.cells = cells or {}
        self.scalar_calls = []
        self.row_calls = []
        self.cell_calls = []

    def scalar(self, sql, **kwargs):
        self.scalar_calls.append((sql, kwargs))
        if sql not in self.scalars:
            raise AssertionError(f"unexpected scalar sql: {sql!r}")
        return self.scalars[sql]

    def rows(self, sql, **kwargs):
        self.row_calls.append((sql, kwargs))
        return list(self.row_data)

    def cell(self, sql, **kwargs):
        self.cell_calls.append((sql, kwargs))
        if sql not in self.cells:
            raise AssertionError(f"unexpected cell sql: {sql!r}")
        return self.cells[sql]


class FakeReport:
    """Captures run-report hooks the engine emits before it raises."""

    def __init__(self):
        self.reads = []
        self.assertions = []

    def log_kpi_read(self, kpi_type, value):
        self.reads.append((kpi_type, value))

    def log_assertion(self, **kwargs):
        self.assertions.append(kwargs)

    def log_ui(self, message):
        return None


@pytest.fixture(autouse=True)
def _patch_readers(monkeypatch):
    FakeKPI.number_calls = []
    FakeKPI.scale_calls = []
    FakeKPI.text_calls = []
    FakeKPI.number_result = 1
    FakeKPI.text_result = "Active"
    FakeKPI.scale_result = {
        "state": "value",
        "value": 1,
        "minimum": None,
        "maximum": 10,
    }
    FakeChart.read_calls = []
    FakeChart.reading = ChartReading(title="t", categories=(), series=(), state="empty")
    monkeypatch.setattr(engine, "KPI", FakeKPI)
    monkeypatch.setattr(engine, "Chart", FakeChart)
    monkeypatch.setattr(engine, "get_current_report", lambda: None)


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "contract.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _run(path, db, **overrides):
    return validate_dashboard_generic(path, FakePage(), db, START, END)


def test_unknown_visual_fails_before_query(tmp_path):
    path = _write(
        tmp_path,
        "metrics:\n  - name: Zones\n    visual: sankey\n    sql_query: 'SELECT 1'\n",
    )
    db = FakeDB()
    with pytest.raises(ValueError, match="Zones"):
        _run(path, db)
    assert db.scalar_calls == []


def test_gauge_requires_maximum_sql(tmp_path):
    path = _write(
        tmp_path,
        "metrics:\n  - name: Dial\n    visual: gauge\n    sql_query: 'SELECT 1'\n",
    )
    with pytest.raises(ValueError, match="maximum_sql"):
        _run(path, FakeDB())


def test_kpi_rejects_maximum_sql(tmp_path):
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Card\n"
        "    visual: kpi\n"
        "    sql_query: 'SELECT 1'\n"
        "    maximum_sql: 'SELECT 2'\n",
    )
    with pytest.raises(ValueError, match="maximum_sql"):
        _run(path, FakeDB())


def test_metric_requires_name_and_sql(tmp_path):
    path = _write(tmp_path, "metrics:\n  - name: OnlyName\n")
    with pytest.raises(ValueError, match="sql_query"):
        _run(path, FakeDB())


def test_negative_series_index_rejected(tmp_path):
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Bars\n"
        "    visual: chart\n"
        "    sql_query: 'SELECT 1'\n"
        "    series_index: -1\n",
    )
    with pytest.raises(ValueError, match="series_index"):
        _run(path, FakeDB())


def test_plain_kpi_still_loads(tmp_path):
    path = _write(tmp_path, "metrics:\n  - name: Card\n    sql_query: 'SELECT 1'\n")
    db = FakeDB({"SELECT 1": 1})
    results = _run(path, db)
    assert results[0].passed is True
    assert results[0].check == "value"
    assert FakeKPI.number_calls == [("Card", None)]
    assert FakeKPI.scale_calls == []


def test_scope_is_forwarded_to_kpi_number(tmp_path):
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Card\n"
        "    scope: Section A\n"
        "    sql_query: 'SELECT 1'\n",
    )
    db = FakeDB({"SELECT 1": 1})
    _run(path, db)
    assert FakeKPI.number_calls == [("Card", "Section A")]


@pytest.mark.parametrize("scope_yaml", ["", "   ", "null"])
def test_blank_scope_is_none(tmp_path, scope_yaml):
    # YAML null is not a string. Empty and whitespace strings are blank too.
    if scope_yaml == "null":
        body = "metrics:\n  - name: Card\n    scope:\n    sql_query: 'SELECT 1'\n"
    else:
        body = (
            "metrics:\n"
            f"  - name: Card\n    scope: '{scope_yaml}'\n    sql_query: 'SELECT 1'\n"
        )
    path = _write(tmp_path, body)
    db = FakeDB({"SELECT 1": 1})
    _run(path, db)
    assert FakeKPI.number_calls == [("Card", None)]


def test_gauge_maximum_mismatch_records_passing_value(tmp_path, monkeypatch):
    report = FakeReport()
    monkeypatch.setattr(engine, "get_current_report", lambda: report)
    FakeKPI.scale_result = {
        "state": "value",
        "value": 5,
        "minimum": 0,
        "maximum": 10,
    }
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Dial\n"
        "    visual: gauge\n"
        "    sql_query: 'SELECT value'\n"
        "    maximum_sql: 'SELECT maximum'\n",
    )
    db = FakeDB({"SELECT value": 5, "SELECT maximum": 9})
    with pytest.raises(AssertionError, match="maximum"):
        _run(path, db)
    assert FakeKPI.scale_calls
    assert FakeKPI.number_calls == []
    passed = {item["label"]: item["passed"] for item in report.assertions}
    assert passed["Dial [value]"] is True
    assert passed["Dial [maximum]"] is False


def test_gauge_reports_both_mismatches(tmp_path):
    FakeKPI.scale_result = {
        "state": "value",
        "value": 5,
        "minimum": 0,
        "maximum": 10,
    }
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Dial\n"
        "    visual: gauge\n"
        "    sql_query: 'SELECT value'\n"
        "    maximum_sql: 'SELECT maximum'\n",
    )
    db = FakeDB({"SELECT value": 1, "SELECT maximum": 2})
    with pytest.raises(AssertionError) as exc:
        _run(path, db)
    message = str(exc.value)
    assert "value" in message
    assert "maximum" in message


def test_gauge_zero_matches_zero(tmp_path):
    FakeKPI.scale_result = {
        "state": "value",
        "value": 0,
        "minimum": 0,
        "maximum": 0,
    }
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Dial\n"
        "    visual: gauge\n"
        "    sql_query: 'SELECT value'\n"
        "    maximum_sql: 'SELECT maximum'\n",
    )
    db = FakeDB({"SELECT value": 0, "SELECT maximum": 0})
    results = _run(path, db)
    assert [item.passed for item in results] == [True, True]


def test_empty_gauge_fails(tmp_path):
    FakeKPI.scale_result = {
        "state": "empty",
        "value": None,
        "minimum": None,
        "maximum": None,
    }
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Dial\n"
        "    visual: gauge\n"
        "    sql_query: 'SELECT value'\n"
        "    maximum_sql: 'SELECT maximum'\n",
    )
    db = FakeDB({"SELECT value": 0, "SELECT maximum": 0})
    with pytest.raises(AssertionError):
        _run(path, db)


def test_category_id_is_stringified_and_optional(tmp_path):
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: WithId\n"
        "    category_id: 1\n"
        "    label: Ignored\n"
        "    sql_query: 'SELECT 1'\n"
        "  - name: NoId\n"
        "    sql_query: 'SELECT 2'\n",
    )
    db = FakeDB({"SELECT 1": 1, "SELECT 2": 1})
    FakeKPI.number_result = 1
    _run(path, db)
    with_id = db.scalar_calls[0][1]
    no_id = db.scalar_calls[1][1]
    assert with_id["category_id"] == "1"
    assert with_id["start_date"] == START
    assert with_id["end_date"] == END
    assert "category_id" not in no_id


def test_chart_labels_match_and_scope_is_forwarded(tmp_path):
    FakeChart.reading = ChartReading(
        title="Bars",
        categories=(
            ChartCategory(label="A", values=(4, 9)),
            ChartCategory(label="B", values=(1, 2)),
        ),
        series=("left", "right"),
        state="value",
    )
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Bars\n"
        "    visual: chart\n"
        "    scope: Section A\n"
        "    series_index: 1\n"
        "    sql_query: 'SELECT label, value'\n",
    )
    db = FakeDB(rows=[("A", 9), ("B", 2)])
    results = _run(path, db)
    assert FakeChart.read_calls == [("Bars", "Section A")]
    assert [item.passed for item in results] == [True, True]
    assert db.row_calls[0][0] == "SELECT label, value"


def test_chart_one_sided_label_fails(tmp_path):
    FakeChart.reading = ChartReading(
        title="Bars",
        categories=(ChartCategory(label="A", values=(1,)),),
        series=(),
        state="value",
    )
    path = _write(
        tmp_path,
        "metrics:\n  - name: Bars\n    visual: chart\n    sql_query: 'SELECT label, value'\n",
    )
    db = FakeDB(rows=[("B", 1)])
    with pytest.raises(AssertionError, match="A"):
        _run(path, db)


def test_chart_duplicate_label_fails(tmp_path):
    FakeChart.reading = ChartReading(
        title="Bars",
        categories=(
            ChartCategory(label="A", values=(1,)),
            ChartCategory(label="A", values=(2,)),
        ),
        series=(),
        state="value",
    )
    path = _write(
        tmp_path,
        "metrics:\n  - name: Bars\n    visual: chart\n    sql_query: 'SELECT label, value'\n",
    )
    db = FakeDB(rows=[("A", 1)])
    with pytest.raises(AssertionError):
        _run(path, db)


def test_chart_null_cell_matches_none(tmp_path):
    FakeChart.reading = ChartReading(
        title="Bars",
        categories=(ChartCategory(label="A", values=(None,)),),
        series=(),
        state="value",
    )
    path = _write(
        tmp_path,
        "metrics:\n  - name: Bars\n    visual: chart\n    sql_query: 'SELECT label, value'\n",
    )
    db = FakeDB(rows=[("A", None)])
    results = _run(path, db)
    assert results[0].passed is True
    assert results[0].ui_value is None
    assert results[0].db_value is None


def test_empty_chart_matches_no_rows(tmp_path):
    FakeChart.reading = ChartReading(title="Bars", categories=(), series=(), state="empty")
    path = _write(
        tmp_path,
        "metrics:\n  - name: Bars\n    visual: chart\n    sql_query: 'SELECT label, value'\n",
    )
    results = _run(path, FakeDB(rows=[]))
    assert results[0].passed is True


def test_empty_chart_fails_when_rows_exist(tmp_path):
    FakeChart.reading = ChartReading(title="Bars", categories=(), series=(), state="empty")
    path = _write(
        tmp_path,
        "metrics:\n  - name: Bars\n    visual: chart\n    sql_query: 'SELECT label, value'\n",
    )
    with pytest.raises(AssertionError):
        _run(path, FakeDB(rows=[("A", 1)]))


def test_chart_with_categories_fails_on_empty_rows(tmp_path):
    FakeChart.reading = ChartReading(
        title="Bars",
        categories=(ChartCategory(label="A", values=(1,)),),
        series=(),
        state="value",
    )
    path = _write(
        tmp_path,
        "metrics:\n  - name: Bars\n    visual: chart\n    sql_query: 'SELECT label, value'\n",
    )
    with pytest.raises(AssertionError):
        _run(path, FakeDB(rows=[]))


def test_series_index_past_the_row_fails(tmp_path):
    FakeChart.reading = ChartReading(
        title="Bars",
        categories=(ChartCategory(label="A", values=(4,)),),
        series=(),
        state="value",
    )
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Bars\n"
        "    visual: chart\n"
        "    series_index: 1\n"
        "    sql_query: 'SELECT label, value'\n",
    )
    db = FakeDB(rows=[("A", None)])
    with pytest.raises(AssertionError):
        _run(path, db)


def test_alerts_contract_names_and_category_ids():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "CategoryID IN" not in text
    loaded = __import__("yaml").safe_load(text)
    metrics = loaded["metrics"]
    for metric in metrics:
        assert "שלושים יום" not in metric["name"]
    zones = [item for item in metrics if item["name"] == "אזורי התרעה תחת ירי"]
    # The population page repeats this title under a different scope and has no category id.
    population = [
        item
        for item in metrics
        if item["name"] == "אוכלוסייה מותרעת" and item.get("category_id")
    ]
    assert {item["category_id"] for item in zones} == {"1", "2", "10"}
    assert {item["category_id"] for item in population} == {"1", "2", "10"}
    assert all(item["visual"] == "kpi" for item in zones + population)
    assert all("CategoryID = :category_id" in item["sql_query"] for item in zones + population)


def _reject(tmp_path, body, match):
    path = _write(tmp_path, body)
    db = FakeDB()
    with pytest.raises(ValueError, match=match):
        _run(path, db)
    assert db.scalar_calls == []
    assert db.cell_calls == []


@pytest.mark.parametrize("visual", ["gauge", "chart", "map"])
def test_text_compare_only_on_kpi(tmp_path, visual):
    _reject(
        tmp_path,
        "metrics:\n"
        f"  - name: Status\n    visual: {visual}\n    compare: text\n"
        "    sql_query: 'SELECT 1'\n"
        + ("    maximum_sql: 'SELECT 2'\n" if visual == "gauge" else ""),
        "Status",
    )


def test_unknown_compare_rejected(tmp_path):
    _reject(
        tmp_path,
        "metrics:\n  - name: Card\n    compare: other\n    sql_query: 'SELECT 1'\n",
        "Card",
    )


def test_map_rejects_maximum_sql(tmp_path):
    _reject(
        tmp_path,
        "metrics:\n"
        "  - name: Map\n    visual: map\n    sql_query: 'SELECT 1'\n"
        "    maximum_sql: 'SELECT 2'\n",
        "maximum_sql",
    )


def _script_map(monkeypatch, number, marks):
    monkeypatch.setattr(engine, "_map_container", lambda frame, name, scope: object())
    monkeypatch.setattr(engine, "_map_number", lambda container: number)
    monkeypatch.setattr(engine, "count_data_marks", lambda container: marks)


def test_map_zero_is_present(tmp_path, monkeypatch):
    _script_map(monkeypatch, 0, 0)
    path = _write(
        tmp_path,
        "metrics:\n  - name: Map\n    visual: map\n    scope: Section A\n    sql_query: 'SELECT 1'\n",
    )
    db = FakeDB(cells={"SELECT 1": 0})
    results = _run(path, db)
    assert results[0].check == "presence"
    assert results[0].ui_value == "value"
    assert results[0].db_value == "value"
    assert results[0].passed is True
    assert FakeKPI.number_calls == []


def test_map_with_nothing_is_empty(tmp_path, monkeypatch):
    _script_map(monkeypatch, None, 0)
    path = _write(tmp_path, "metrics:\n  - name: Map\n    visual: map\n    sql_query: 'SELECT 1'\n")
    results = _run(path, FakeDB(cells={"SELECT 1": None}))
    assert results[0].passed is True
    assert results[0].ui_value == "empty"
    assert results[0].db_value == "empty"


def test_map_placeholder_is_reported_raw(tmp_path, monkeypatch):
    _script_map(monkeypatch, None, 0)
    path = _write(tmp_path, "metrics:\n  - name: Map\n    visual: map\n    sql_query: 'SELECT 1'\n")
    with pytest.raises(AssertionError, match="placeholder") as exc:
        _run(path, FakeDB(cells={"SELECT 1": "placeholder"}))
    assert "empty" in str(exc.value)
    assert "0" not in str(exc.value).split("DB=")[-1]


def test_map_marks_without_a_number_are_present(tmp_path, monkeypatch):
    _script_map(monkeypatch, None, 2)
    path = _write(tmp_path, "metrics:\n  - name: Map\n    visual: map\n    sql_query: 'SELECT 1'\n")
    results = _run(path, FakeDB(cells={"SELECT 1": 3}))
    assert results[0].ui_value == "value"
    assert results[0].passed is True


def test_text_kpi_compares_strings_and_skips_number(tmp_path):
    FakeKPI.text_result = "Reduced"
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: Policy\n"
        "    visual: kpi\n"
        "    compare: text\n"
        "    scope: Section A\n"
        "    sql_query: 'SELECT status'\n",
    )
    db = FakeDB(cells={"SELECT status": "Reduced"})
    results = _run(path, db)
    assert results[0].passed is True
    assert results[0].check == "value"
    assert FakeKPI.text_calls == [("Policy", "Section A")]
    assert FakeKPI.number_calls == []
    assert db.scalar_calls == []


def test_text_kpi_placeholder_fails(tmp_path):
    FakeKPI.text_result = "Reduced"
    path = _write(
        tmp_path,
        "metrics:\n  - name: Policy\n    compare: text\n    sql_query: 'SELECT status'\n",
    )
    with pytest.raises(AssertionError, match="placeholder") as exc:
        _run(path, FakeDB(cells={"SELECT status": "placeholder"}))
    message = str(exc.value)
    assert "Reduced" in message
    assert FakeKPI.number_calls == []


def test_remaining_visuals_use_stub_sql():
    from db.clients.alerts import MAP_PRESENCE_SQL, POLICY_STATUS_SQL, SETTLEMENTS_CHART_SQL

    loaded = __import__("yaml").safe_load(CONTRACT.read_text(encoding="utf-8"))
    by_name = {item["name"]: item for item in loaded["metrics"]}
    chart = by_name["עשרת היישובים עם כמות ההתרעות הגבוהה ביותר"]
    presence = by_name["מפת התרעות ביישובים"]
    policy = by_name["סיכון לפי מדיניות התגוננות ברגע"]
    assert chart["visual"] == "chart"
    assert " ".join(chart["sql_query"].split()) == SETTLEMENTS_CHART_SQL
    assert presence["visual"] == "map"
    assert " ".join(presence["sql_query"].split()) == MAP_PRESENCE_SQL
    assert policy["visual"] == "kpi"
    assert policy["compare"] == "text"
    assert " ".join(policy["sql_query"].split()) == POLICY_STATUS_SQL
    assert "category_id" not in chart
    assert "category_id" not in presence
    assert "category_id" not in policy
    source = (
        Path(__file__).resolve().parents[1]
        / "ui"
        / "alerts_analysis_dashboard"
        / "test_db_parity.py"
    ).read_text(encoding="utf-8")
    assert "pytest.skip" not in source
    assert "importorskip" not in source


_TIME_BUCKETS = ("היום", "אתמול", 'סה"כ בטווח שנבחר')
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _contract_metrics():
    loaded = __import__("yaml").safe_load(CONTRACT.read_text(encoding="utf-8"))
    return loaded["metrics"]


def _collapsed_sql(metric):
    return " ".join(metric["sql_query"].split())


def test_alerts_contract_threat_time_buckets():
    from db.clients.alerts import THREAT_KPI_STUB_SQL

    scopes = {
        "ירי רקטות וטילים": ("1", "Rockets"),
        "חדירת מחבלים": ("2", "Terrorists"),
        "חדירת כלי טיס עוין": ("10", "UAV"),
    }
    found = []
    for metric in _contract_metrics():
        scope = metric.get("scope")
        if scope not in scopes or metric["name"] not in _TIME_BUCKETS:
            continue
        category_id, label = scopes[scope]
        assert metric["visual"] == "kpi"
        assert metric["category_id"] == category_id
        assert metric["label"] == label
        assert _collapsed_sql(metric) == THREAT_KPI_STUB_SQL
        assert "שלושים יום" not in metric["name"]
        assert "שלושים יום" not in scope
        found.append((metric["name"], scope, metric["category_id"]))
    expected = {
        (name, scope, category_id)
        for scope, (category_id, _label) in scopes.items()
        for name in _TIME_BUCKETS
    }
    assert set(found) == expected
    assert len(found) == 9


def test_alerts_contract_general_time_buckets():
    from db.clients.alerts import AREA_KPI_STUB_SQL, POPULATION_KPI_STUB_SQL

    expected_sql = {
        "אוכלוסייה מותרעת": POPULATION_KPI_STUB_SQL,
        "אזורי התרעה תחת ירי": AREA_KPI_STUB_SQL,
    }
    found = {scope: [] for scope in expected_sql}
    for metric in _contract_metrics():
        scope = metric.get("scope")
        if scope not in expected_sql or metric["name"] not in _TIME_BUCKETS:
            continue
        assert metric["visual"] == "kpi"
        assert "category_id" not in metric
        assert "maximum_sql" not in metric
        assert _collapsed_sql(metric) == expected_sql[scope]
        assert "שלושים יום" not in scope
        assert "שלושים יום" not in metric["name"]
        found[scope].append(metric["name"])
    for scope, names in found.items():
        assert set(names) == set(_TIME_BUCKETS)
        assert len(names) == 3


def test_alerts_contract_static_comparison_chart():
    from db.clients.alerts import PERIOD_COMPARISON_CHART_SQL

    metrics = _contract_metrics()
    name = "עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת"
    matches = [metric for metric in metrics if metric["name"] == name]
    assert len(matches) == 1
    chart = matches[0]
    assert chart["visual"] == "chart"
    assert "scope" not in chart
    assert "category_id" not in chart
    assert _collapsed_sql(chart) == PERIOD_COMPARISON_CHART_SQL
    assert ":start_date" not in chart["sql_query"]
    assert ":end_date" not in chart["sql_query"]
    assert "AlertDate" not in chart["sql_query"]
    ranking = "עשרת היישובים עם כמות ההתרעות הגבוהה ביותר"
    assert any(metric["name"] == ranking for metric in metrics)


def test_alerts_stubs_do_not_hide_connection_errors():
    alerts_source = (_REPO_ROOT / "db" / "clients" / "alerts.py").read_text(encoding="utf-8")
    for token in (
        "THREAT_KPI_STUB_SQL",
        "POPULATION_KPI_STUB_SQL",
        "AREA_KPI_STUB_SQL",
        "PERIOD_COMPARISON_CHART_SQL",
    ):
        assert token in alerts_source
    for hebrew in (
        "ירי רקטות",
        "חדירת מחבלים",
        "חדירת כלי טיס",
        "אוכלוסייה",
        "אזורי התרעה",
    ):
        assert hebrew not in alerts_source
    assert "except" not in alerts_source
    parity_source = (
        _REPO_ROOT / "tests" / "ui" / "alerts_analysis_dashboard" / "test_db_parity.py"
    ).read_text(encoding="utf-8")
    assert "pytest.skip" not in parity_source
    assert "importorskip" not in parity_source


def test_exclude_scopes_skips_matching_metrics(tmp_path):
    """A scope in exclude_scopes is neither read nor queried. Omitting it runs every metric."""
    path = _write(
        tmp_path,
        "metrics:\n"
        "  - name: One\n"
        "    scope: page-one\n"
        "    visual: kpi\n"
        "    sql_query: 'SELECT 1'\n"
        "  - name: Two\n"
        "    scope: page-two\n"
        "    visual: kpi\n"
        "    sql_query: 'SELECT 1'\n",
    )
    db = FakeDB(scalars={"SELECT 1": 1})
    # _run drops extra keywords, so this call passes exclude_scopes itself.
    excluded = validate_dashboard_generic(
        path,
        FakePage(),
        db,
        START,
        END,
        exclude_scopes={"page-two"},
    )
    assert len(db.scalar_calls) == 1
    assert [item.name for item in excluded] == ["One"]

    db_all = FakeDB(scalars={"SELECT 1": 1})
    both = validate_dashboard_generic(path, FakePage(), db_all, START, END)
    assert len(db_all.scalar_calls) == 2
    assert {item.name for item in both} == {"One", "Two"}


_PAGE1_SCOPES = (
    "ירי רקטות וטילים",
    "חדירת מחבלים",
    "חדירת כלי טיס עוין",
    "אוכלוסייה מותרעת",
    "אזורי התרעה תחת ירי",
)


def _page2_metrics():
    from pages.alerts_analysis.population_page import AlertsPopulationPage

    return [
        metric
        for metric in _contract_metrics()
        if metric.get("scope") == AlertsPopulationPage.PAGE_TITLE
    ]


def test_population_contract_scope():
    from pages.alerts_analysis.population_page import AlertsPopulationPage

    title = AlertsPopulationPage.PAGE_TITLE
    page2 = _page2_metrics()
    assert page2
    assert all(metric["scope"] == title for metric in page2)
    assert all("בין" not in metric["name"] for metric in page2)
    for scope in _PAGE1_SCOPES:
        assert title not in scope
        assert scope not in title

    district = [item for item in page2 if item["name"] == "התרעות לפי מחוז"]
    assert len(district) == 1
    assert district[0]["visual"] == "chart"
    assert "series_index" not in district[0]

    settlement = [item for item in page2 if item["name"] == AlertsPopulationPage.SETTLEMENT_CHART]
    assert {item["series_index"] for item in settlement} == {0, 1}
    assert {item["label"] for item in settlement} == {
        AlertsPopulationPage.WARNED_SERIES,
        AlertsPopulationPage.UNWARNED_SERIES,
    }
    cards = [item for item in page2 if item["visual"] == "kpi"]
    assert len(cards) == 3
    assert len({item["name"] for item in cards}) == 3
    charts = [item["name"] for item in page2 if item["visual"] == "chart"]
    assert AlertsPopulationPage.HOUR_CHART in charts
    assert AlertsPopulationPage.DATES_CHART in charts
    assert all("category_id" not in item and "maximum_sql" not in item for item in page2)

    names = {item["name"] for item in _contract_metrics()}
    for required in (
        "עשרת היישובים עם כמות ההתרעות הגבוהה ביותר",
        "מפת התרעות ביישובים",
        "סיכון לפי מדיניות התגוננות ברגע",
        "עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת",
    ):
        assert required in names


def test_population_page_stubs():
    from db.clients.alerts import (
        POPULATION_PAGE_CHART_STUB_SQL,
        POPULATION_PAGE_KPI_STUB_SQL,
    )
    from pages.alerts_analysis.population_page import AlertsPopulationPage

    for metric in _page2_metrics():
        collapsed = _collapsed_sql(metric)
        if metric["visual"] == "kpi":
            assert collapsed == POPULATION_PAGE_KPI_STUB_SQL
        else:
            assert collapsed == POPULATION_PAGE_CHART_STUB_SQL
    assert "AlertDate" not in POPULATION_PAGE_CHART_STUB_SQL
    assert ":start_date" not in POPULATION_PAGE_CHART_STUB_SQL
    assert ":end_date" not in POPULATION_PAGE_CHART_STUB_SQL

    alerts_source = (_REPO_ROOT / "db" / "clients" / "alerts.py").read_text(encoding="utf-8")
    comment = alerts_source.split("POPULATION_PAGE_KPI_STUB_SQL", 1)[0]
    assert ">=" in comment and "<" in comment
    assert "district" in comment and "settlement" in comment
    assert "SUM / NULLIF(COUNT, 0)" in comment

    parity_source = (
        _REPO_ROOT / "tests" / "ui" / "alerts_analysis_dashboard" / "test_db_parity.py"
    ).read_text(encoding="utf-8")
    assert "exclude_scopes" in parity_source
    assert AlertsPopulationPage.PAGE_TITLE
    assert "pytest.skip" not in parity_source
    assert "importorskip" not in parity_source
