import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _env(key: str, default: str = "") -> str:
    value = os.getenv(key, default)
    return value.strip().strip('"')


class Settings:
    DB_SERVER = _env("DB_SERVER", r"localhost\SQLEXPRESS")
    DB_NAME = _env("DB_NAME", "QA_Fleet_DB")
    DB_DRIVER = _env("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_TABLE = _env("DB_TABLE", "[DIM].[Vehicle]")
    DB_WITHDRAWN_TABLE = _env(
        "DB_WITHDRAWN_TABLE", "[FACT].[SigningReturnVehicle]"
    )
    DB_ALLOCATED_TABLE = _env("DB_ALLOCATED_TABLE", "[FACT].[VehicleFlow]")
    # Alerts database name for the DB-parity pilot (read-only, Trusted_Connection).
    DB_ALERTS_NAME = _env("DB_ALERTS_NAME", "QA_Alerts_DB")
    DB_ENVIRONMENT = _env("DB_ENVIRONMENT", "מבצעי")
    DB_CSV_PATH = _env("DB_CSV_PATH", "data/raw")

    LOGIN_URL = _env(
        "LOGIN_URL",
        "https://portal-agamim.orangepeak.net/application/66f13eebe5a555c71f580633"
        "?environment=%D7%A1%D7%91%D7%99%D7%91%D7%94%20%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%AA",
    )
    DASHBOARD_URL = _env(
        "DASHBOARD_URL",
        "https://portal-agamim.orangepeak.net/application/66f13eebe5a555c71f580633"
        "?environment=%D7%A1%D7%91%D7%99%D7%91%D7%94%20%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%AA",
    )
    DASHBOARD_SEARCH_TERM = _env("DASHBOARD_SEARCH_TERM", "שליטה בניוד")
    PORTAL_ALL_PRODUCTS_LABEL = _env(
        "PORTAL_ALL_PRODUCTS_LABEL", "למעבר לקטלוג המוצרים"
    )
    PORTAL_CATALOG_URL = _env(
        "PORTAL_CATALOG_URL",
        "https://portal-agamim.orangepeak.net/catalog"
        "?environment=%D7%A1%D7%91%D7%99%D7%91%D7%94%20%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%AA",
    )
    AUTH_FILE = _env("AUTH_FILE", "auth_state.json")
    HEADLESS = _env("HEADLESS", "false").lower() == "true"
    MANUAL_LOGIN = _env("MANUAL_LOGIN", "true").lower() == "true"
    DEFAULT_TIMEOUT = int(_env("DEFAULT_TIMEOUT", "15000"))
    # Max accepted time (ms) from reload → ready visual visible (warm / authenticated).
    # Power BI iframe load commonly exceeds 5s; 30s matches observed warm-load times.
    DASHBOARD_LOAD_SLA_MS = int(_env("DASHBOARD_LOAD_SLA_MS", "30000"))
    # Progressive wait budgets (ms), capped by DEFAULT_TIMEOUT.
    # Fast path uses the first step; slower steps run only after earlier ones fail.
    _timeout_steps_raw = _env("TIMEOUT_STEPS_MS", "3000,8000,20000")
    TIMEOUT_STEPS_MS: tuple[int, ...] = tuple(
        int(part.strip())
        for part in _timeout_steps_raw.split(",")
        if part.strip().isdigit() and int(part.strip()) > 0
    ) or (3000, 8000, 20000)
    # Max wait when a KPI change is optional (clear already-clear filters, etc.).
    # Avoids burning DEFAULT_TIMEOUT (~60s) on every reset between tests.
    KPI_OPTIONAL_WAIT_MS = int(_env("KPI_OPTIONAL_WAIT_MS", "2500"))
    # Playwright tracing is expensive (screenshots + DOM snapshots every action).
    # Keep off for normal runs; turn on when debugging flakes. Saved on failure only.
    ENABLE_TRACING = _env("ENABLE_TRACING", "false").lower() == "true"
    # Full-run .webm of the shared browser tab (pass and fail). Also: pytest --video
    ENABLE_VIDEO = _env("ENABLE_VIDEO", "false").lower() == "true"
    SLOW_MO = int(_env("SLOW_MO", "0"))
    PAUSE_ON_FAILURE = _env("PAUSE_ON_FAILURE", "false").lower() == "true"
    # ReportPortal endpoint/secret read from the environment only (opt-in reporting).
    # RP_API_KEY stays empty unless exported, so no secret is committed and
    # reporting simply stays inert until the stack is provisioned.
    RP_ENDPOINT = _env("RP_ENDPOINT", "http://localhost:8080")
    RP_API_KEY = _env("RP_API_KEY", "")

settings = Settings()