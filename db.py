import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import NVARCHAR

from config.settings import settings


def import_csv_to_sql():
    """Optional home setup: load Vehicle.csv into the existing DB table."""
    file_path = settings.DB_CSV_PATH
    table_name = settings.DB_TABLE

    print(f"Reading data from {file_path}...")

    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

        master_conn_str = (
            f"mssql+pyodbc://@{settings.DB_SERVER}/master"
            f"?driver={settings.DB_DRIVER.replace(' ', '+')}&Trusted_Connection=yes"
        )
        master_engine = create_engine(master_conn_str, isolation_level="AUTOCOMMIT")

        with master_engine.connect() as conn:
            conn.execute(
                text(
                    f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{settings.DB_NAME}') "
                    f"CREATE DATABASE {settings.DB_NAME}"
                )
            )

        db_conn_str = (
            f"mssql+pyodbc://@{settings.DB_SERVER}/{settings.DB_NAME}"
            f"?driver={settings.DB_DRIVER.replace(' ', '+')}&Trusted_Connection=yes"
        )
        db_engine = create_engine(db_conn_str)

        dtype_mapping = {
            col_name: NVARCHAR for col_name in df.select_dtypes(include=["object"]).columns
        }

        df.to_sql(table_name, db_engine, if_exists="replace", index=False, dtype=dtype_mapping)
        print(f"Data imported successfully into '{table_name}'.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    import_csv_to_sql()
