"""Run reports for UI and DB validation."""

from reports.allure_catalog import EPIC, suite_marks
from reports.test_run_report import RunReportBook, TestRunReport, get_current_report

__all__ = [
    "EPIC",
    "RunReportBook",
    "TestRunReport",
    "get_current_report",
    "suite_marks",
]
