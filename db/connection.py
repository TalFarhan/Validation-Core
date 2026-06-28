"""SQL Server connection helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config.settings import settings


def build_connection_string(*, database: str | None = None) -> str:
    db_name = database or settings.DB_NAME
    return (
        f"mssql+pyodbc://@{settings.DB_SERVER}/{db_name}"
        f"?driver={settings.DB_DRIVER.replace(' ', '+')}"
        f"&Trusted_Connection=yes"
    )


def create_db_engine(*, database: str | None = None) -> Engine:
    return create_engine(build_connection_string(database=database))
