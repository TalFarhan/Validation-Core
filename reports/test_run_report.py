"""Collect validation steps and write one CSV report per pytest run."""

from __future__ import annotations

import csv
import io
import json
from contextvars import ContextVar, Token
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

REPORT_DIR = Path("test-results/run-reports")
ALLURE_RESULTS_DIR = Path("test-results/allure-results")

_current_report: ContextVar[TestRunReport | None] = ContextVar(
    "current_test_run_report", default=None
)
_run_book: ContextVar[RunReportBook | None] = ContextVar(
    "current_run_report_book", default=None
)


def get_current_report() -> TestRunReport | None:
    return _current_report.get()


def get_run_book() -> RunReportBook | None:
    return _run_book.get()


def _compact(value: Any, *, max_len: int = 800) -> str:
    if isinstance(value, str):
        text = " ".join(value.split())
    else:
        text = json.dumps(value, ensure_ascii=False, default=str)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def classify_failure(error: str | None) -> str:
    """Label failure cause for CSV / humans."""
    text = error or ""
    if "[LOAD_TIMEOUT]" in text or "LoadTimeoutError" in text:
        return "כשל טעינה (timeout)"
    lower = text.lower()
    if any(
        token in lower
        for token in (
            "timeout",
            "exceeded",
            "err_internet",
            "err_connection",
            "err_name_not_resolved",
            "net::",
            "executable doesn't exist",
        )
    ):
        return "כשל טעינה / רשת"
    if "mismatch" in lower or "ui=" in lower and "db=" in lower:
        return "כשל נתונים (UI≠DB)"
    return "שגיאת הרצה"


def _short_error(error: str, *, max_len: int = 500) -> str:
    lines = [ln.strip() for ln in error.strip().splitlines() if ln.strip()]
    for line in reversed(lines):
        if line.startswith("E ") or "Error:" in line or "Exception:" in line:
            return _compact(line.lstrip("E ").strip(), max_len=max_len)
    first = lines[0] if lines else error
    return _compact(first, max_len=max_len)


def _format_sql(sql: str, params: dict[str, Any] | None) -> str:
    sql_text = _compact(sql, max_len=2000)
    if not params:
        return sql_text
    relevant = {
        k: v
        for k, v in params.items()
        if v is not None or k in {"environment", "kpi_type", "group_column"}
    }
    return f"{sql_text} | פרמטרים: {_compact(relevant, max_len=400)}"


@dataclass
class ReportRow:
    action: str
    query: str
    output: str
    status: str  # עבר / נכשל / - (שלב ביניים)


class RunReportBook:
    """One CSV file for the entire pytest session."""

    def __init__(self) -> None:
        self.started_at = datetime.now()
        self.finished_at: datetime | None = None
        stamp = self.started_at.strftime("%Y-%m-%d_%H-%M-%S")
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.path = REPORT_DIR / f"run_{stamp}.csv"
        self._row_num = 0
        self._tests_passed = 0
        self._tests_failed = 0
        self._token: Token | None = None
        self._write_header()

    @classmethod
    def start(cls) -> RunReportBook:
        book = cls()
        book._token = _run_book.set(book)
        return book

    def stop_context(self) -> None:
        if self._token is not None:
            _run_book.reset(self._token)
            self._token = None

    def _write_header(self) -> None:
        with self.path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["שדה", "ערך"])
            writer.writerow(
                ["התחלת הרצה", self.started_at.strftime("%Y-%m-%d %H:%M:%S")]
            )
            writer.writerow([])
            writer.writerow(
                [
                    "#",
                    "בדיקה",
                    "סטטוס בדיקה",
                    "מה נבדק / סונן",
                    "שאילתת DB",
                    "פלט",
                    "עבר או נכשל",
                ]
            )

    def append_test(self, report: TestRunReport) -> None:
        if report.status == "עבר":
            self._tests_passed += 1
        elif report.status == "נכשל":
            self._tests_failed += 1

        with self.path.open("a", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            for row in report.rows:
                self._row_num += 1
                writer.writerow(
                    [
                        self._row_num,
                        report.test_name,
                        report.status,
                        row.action,
                        row.query,
                        row.output,
                        row.status,
                    ]
                )

    def finalize(self) -> Path:
        self.finished_at = datetime.now()
        with self.path.open("a", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([])
            writer.writerow(["שדה", "ערך"])
            writer.writerow(
                [
                    "סיום הרצה",
                    self.finished_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )
            writer.writerow(["בדיקות שעברו", self._tests_passed])
            writer.writerow(["בדיקות שנכשלו", self._tests_failed])
            writer.writerow(
                ["סה״כ בדיקות", self._tests_passed + self._tests_failed]
            )
        self._write_allure_environment()
        return self.path

    def _write_allure_environment(self) -> None:
        """Point the Allure report at the full Hebrew run CSV for this session."""
        ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        env_path = ALLURE_RESULTS_DIR / "environment.properties"
        lines = [
            f"run.csv={self.path.resolve().as_posix()}",
            f"run.started={self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if self.finished_at is not None:
            lines.append(
                f"run.finished={self.finished_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        lines.append(f"tests.passed={self._tests_passed}")
        lines.append(f"tests.failed={self._tests_failed}")
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestRunReport:
    """Accumulates one row per check for a single test; flushed into the run book."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.started_at = datetime.now()
        self.finished_at: datetime | None = None
        self.status: str = "RUNNING"
        self.rows: list[ReportRow] = []
        self._token: Token | None = None
        self._last_db_query: str = ""

    @classmethod
    def start(cls, test_name: str) -> TestRunReport:
        report = cls(test_name)
        report._token = _current_report.set(report)
        return report

    def stop_context(self) -> None:
        if self._token is not None:
            _current_report.reset(self._token)
            self._token = None

    def add_row(
        self,
        action: str,
        output: str,
        status: str = "-",
        *,
        query: str = "",
    ) -> None:
        self.rows.append(
            ReportRow(action=action, query=query, output=output, status=status)
        )

    def finish(self, *, passed: bool, error: str | None = None) -> None:
        self.finished_at = datetime.now()
        self.status = "עבר" if passed else "נכשל"
        if error:
            category = classify_failure(error)
            self.add_row(category, _short_error(error), "נכשל")
        if not any(row.status in {"עבר", "נכשל"} for row in self.rows):
            self.add_row("סיכום בדיקה", self.test_name, self.status)

    def to_csv_text(self) -> str:
        """CSV snippet for this test only — attached to the Allure result."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "#",
                "בדיקה",
                "סטטוס בדיקה",
                "מה נבדק / סונן",
                "שאילתת DB",
                "פלט",
                "עבר או נכשל",
            ]
        )
        for index, row in enumerate(self.rows, start=1):
            writer.writerow(
                [
                    index,
                    self.test_name,
                    self.status,
                    row.action,
                    row.query,
                    row.output,
                    row.status,
                ]
            )
        return buffer.getvalue()

    def log_ui(self, message: str) -> None:
        self.add_row("UI", _compact(message), "-")

    def log_filter(self, slicer: str, value: str) -> None:
        self.add_row(f"סינון UI — {slicer}", value, "-")

    def log_kpi_read(self, kpi_type: str, value: int) -> None:
        self.add_row(f"תצוגת KPI — {kpi_type}", str(value), "-")

    def log_assertion(
        self,
        *,
        label: str,
        ui_value: Any,
        db_value: Any,
        passed: bool,
        filters: dict[str, Any] | None = None,
    ) -> None:
        filters_text = ""
        if filters:
            cleaned = {k: v for k, v in filters.items() if v is not None}
            if cleaned:
                filters_text = f" | פילטרים: {_compact(cleaned, max_len=200)}"
        self.add_row(
            f"השוואה {label}{filters_text}",
            f"UI={ui_value} | DB={db_value}",
            "עבר" if passed else "נכשל",
            query=self._last_db_query,
        )

    def log_db_query(
        self,
        *,
        method: str,
        sql: str,
        params: dict[str, Any] | None,
        result: Any,
    ) -> None:
        query_text = _format_sql(sql, params)
        self._last_db_query = query_text
        self.add_row(
            f"DB — {method}",
            _compact(result, max_len=400),
            "-",
            query=query_text,
        )
