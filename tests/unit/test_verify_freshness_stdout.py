"""Unit tests for Layer 0 freshness stdout (pytest-html Captured Stdout)."""

from datetime import datetime, timedelta

from core.portal.page import ReportShell


def test_verify_freshness_prints_extracted_date_to_stdout(capsys, monkeypatch):
    shell = ReportShell.__new__(ReportShell)
    stamp = (datetime.now() - timedelta(hours=1)).strftime("%d/%m/%Y %H:%M")
    monkeypatch.setattr(shell, "_wait_for_dashboard_iframe", lambda: True)
    monkeypatch.setattr(
        shell,
        "_last_refresh_caption_text",
        lambda: f"הדשבורד עודכן לאחרונה ב: {stamp}",
    )

    shell.verify_freshness()

    out = capsys.readouterr().out
    assert f"---> EXTRACTED DASHBOARD DATE: {stamp} <---" in out
