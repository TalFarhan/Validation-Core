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
    DB_TABLE = _env("DB_TABLE", "DIM_Vehicle")
    DB_ENVIRONMENT = _env("DB_ENVIRONMENT", "מבצעי")
    DB_HAS_ALLOCATED = _env("DB_HAS_ALLOCATED", "false").lower() == "true"
    DB_CSV_PATH = _env("DB_CSV_PATH", "data/raw/Vehicle.csv")

    LOGIN_URL = _env(
        "LOGIN_URL",
        "https://portal.agamimp.net/application/66f13eebe5a555c71f580633"
        "?environment=%D7%A1%D7%91%D7%99%D7%91%D7%94%20%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%AA",
    )
    DASHBOARD_URL = _env(
        "DASHBOARD_URL",
        "https://portal.agamimp.net/application/66f13eebe5a555c71f580633"
        "?environment=%D7%A1%D7%91%D7%99%D7%91%D7%94%20%D7%9E%D7%91%D7%A6%D7%A2%D7%99%D7%AA",
    )
    AUTH_FILE = _env("AUTH_FILE", "auth_state.json")
    HEADLESS = _env("HEADLESS", "false").lower() == "true"
    MANUAL_LOGIN = _env("MANUAL_LOGIN", "true").lower() == "true"
    DEFAULT_TIMEOUT = int(_env("DEFAULT_TIMEOUT", "15000"))
    SLOW_MO = int(_env("SLOW_MO", "0"))
    PAUSE_ON_FAILURE = _env("PAUSE_ON_FAILURE", "false").lower() == "true"


settings = Settings()
