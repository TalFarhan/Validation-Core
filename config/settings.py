import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _env(key: str, default: str = "") -> str:
    value = os.getenv(key, default)
    return value.strip().strip('"')


class Settings:
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

    DB_SERVER = _env("DB_SERVER")
    DB_NAME = _env("DB_NAME")
    DB_USER = _env("DB_USER")
    DB_PASSWORD = _env("DB_PASSWORD")
    DB_DRIVER = _env("DB_DRIVER")
    DB_AUTH = _env("DB_AUTH", "aad_password")
    DB_MODE = _env("DB_MODE", "live")
    DB_SNAPSHOT_FILE = _env("DB_SNAPSHOT_FILE", "db_snapshot.json")
    DB_CONNECTION_STRING = _env("DB_CONNECTION_STRING")
    VEHICLE_DIM_TABLE = _env("VEHICLE_DIM_TABLE", "[DIM].[Vehicle]")
    DB_ENABLED = _env("DB_ENABLED", "false").lower() == "true"


settings = Settings()
