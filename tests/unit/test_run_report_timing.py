"""Per-test start/end/duration must appear in the Hebrew CSV."""

from datetime import datetime, timedelta

from reports.test_run_report import TEST_CSV_COLUMNS, TestRunReport

def test_csv_includes_start_end_and_duration():
    report = TestRunReport("tests/ui/sample.py::test_example")
    report.started_at = datetime(2026, 9, 3, 12, 0, 0)
    report.finished_at = datetime(2026, 9, 3, 12, 0, 12)
    report.status = "עבר"
    report.add_row("סיכום בדיקה", report.test_name, "עבר")

    csv_text = report.to_csv_text()
    header = csv_text.splitlines()[0]
    for column in TEST_CSV_COLUMNS:
        assert column in header

    assert "2026-09-03 12:00:00" in csv_text
    assert "2026-09-03 12:00:12" in csv_text
    assert "12.00" in csv_text
    assert report.timing_cells() == [
        "2026-09-03 12:00:00",
        "2026-09-03 12:00:12",
        "12.00",
    ]

def test_timing_summary_includes_duration():
    report = TestRunReport("tests/ui/sample.py::test_example")
    report.started_at = datetime(2026, 9, 3, 8, 15, 0)
    report.finished_at = report.started_at + timedelta(seconds=3.5)
    report.status = "נכשל"
    summary = report.timing_summary()
    assert "tests/ui/sample.py::test_example" in summary
    assert "נכשל" in summary
    assert "started=2026-09-03 08:15:00" in summary
    assert "duration_s=3.50" in summary
