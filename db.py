"""Load Excel files from data/raw into SQL Server tables named like the files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import NVARCHAR

from config.settings import settings

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"


def _parse_schema_table(stem: str) -> tuple[str, str]:
    """'[DIM].[Vehicle]' -> ('DIM', 'Vehicle')."""
    parts = stem.replace("[", "").replace("]", "").split(".")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"Expected file stem like [Schema].[Table], got: {stem!r}"
        )
    return parts[0], parts[1]


def _ensure_database(driver: str) -> None:
    master_engine = create_engine(
        f"mssql+pyodbc://@{settings.DB_SERVER}/master"
        f"?driver={driver}&Trusted_Connection=yes",
        isolation_level="AUTOCOMMIT",
    )
    with master_engine.connect() as conn:
        conn.execute(
            text(
                f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{settings.DB_NAME}') "
                f"CREATE DATABASE [{settings.DB_NAME}]"
            )
        )


def _ensure_schema(engine, schema: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                f"IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = :schema) "
                f"EXEC('CREATE SCHEMA [{schema}]')"
            ),
            {"schema": schema},
        )


def import_excel_to_sql(raw_dir: Path | None = None) -> None:
    """Import every *.xlsx in data/raw into [Schema].[Table] matching the filename."""
    folder = raw_dir or RAW_DIR
    files = sorted(folder.glob("*.xlsx"))
    if not files:
        raise FileNotFoundError(f"No .xlsx files found in {folder}")

    driver = settings.DB_DRIVER.replace(" ", "+")
    _ensure_database(driver)

    engine = create_engine(
        f"mssql+pyodbc://@{settings.DB_SERVER}/{settings.DB_NAME}"
        f"?driver={driver}&Trusted_Connection=yes"
    )

    for path in files:
        schema, table = _parse_schema_table(path.stem)
        print(f"Reading {path.name} -> [{schema}].[{table}] ...")
        df = pd.read_excel(path)
        _ensure_schema(engine, schema)
        dtype_mapping = {
            col: NVARCHAR
            for col in df.select_dtypes(include=["object", "string"]).columns
        }
        df.to_sql(
            table,
            engine,
            schema=schema,
            if_exists="replace",
            index=False,
            dtype=dtype_mapping,
        )
        print(f"  Imported {len(df)} rows into [{schema}].[{table}]")


if __name__ == "__main__":
    import_excel_to_sql()
