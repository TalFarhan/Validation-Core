import json
from pathlib import Path
from typing import Any, Optional

from config.settings import settings
from utils.db_helper import get_connection

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class DatabaseClient:
    """Read-only database access for UI-to-DB validation tests."""

    _VEHICLE_COLUMNS = (
        "VehicleID",
        "Unit",
        "SubUnit",
        "VehicleType",
        "VehicleCategory",
        "VehicleSource",
        "RecieveDate",
        "RecieveSite",
        "VehicleFuel",
        "IsActive",
        "Environment",
    )

    def __init__(self):
        self.vehicle_table = settings.VEHICLE_DIM_TABLE
        self._snapshot_rows: list[dict[str, Any]] | None = None

        if settings.DB_MODE == "ads_export":
            return

        if settings.DB_CONNECTION_STRING:
            return

        missing = []
        if not settings.DB_SERVER:
            missing.append("DB_SERVER")
        if not settings.DB_NAME:
            missing.append("DB_NAME")

        if settings.DB_AUTH != "aad_interactive":
            if not settings.DB_USER:
                missing.append("DB_USER")
            if not settings.DB_PASSWORD:
                missing.append("DB_PASSWORD")

        if missing:
            raise ValueError(f"Missing database configuration: {', '.join(missing)}")

    def _load_snapshot_rows(self) -> list[dict[str, Any]]:
        if self._snapshot_rows is not None:
            return self._snapshot_rows

        snapshot_path = Path(settings.DB_SNAPSHOT_FILE)
        if not snapshot_path.is_absolute():
            snapshot_path = DATA_DIR / snapshot_path

        if not snapshot_path.exists():
            raise FileNotFoundError(
                f"DB snapshot not found at '{snapshot_path}'. "
                "Export query results from Azure Data Studio and save as JSON."
            )

        with open(snapshot_path, encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and "vehicles" in payload:
            rows = payload["vehicles"]
        else:
            raise ValueError(
                f"Unsupported snapshot format in '{snapshot_path}'. "
                "Expected a JSON array or an object with a 'vehicles' array."
            )

        self._snapshot_rows = rows
        return rows

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value

    def _row_to_dict(self, row: tuple, columns: tuple[str, ...]) -> dict[str, Any]:
        return {column: row[index] for index, column in enumerate(columns)}

    def _matches_filters(
        self,
        row: dict[str, Any],
        *,
        district: Optional[str],
        sub_unit: Optional[str],
        category: Optional[str],
        source: Optional[str],
        environment: Optional[str],
        active_only: bool,
    ) -> bool:
        checks = [
            (district, "Unit"),
            (sub_unit, "SubUnit"),
            (category, "VehicleCategory"),
            (source, "VehicleSource"),
            (environment, "Environment"),
        ]
        for expected, field in checks:
            if expected is not None and str(row.get(field)) != str(expected):
                return False

        if active_only and self._normalize_value(row.get("IsActive")) not in (1, "1", True):
            return False

        return True

    def get_vehicle_by_id(self, vehicle_id: str) -> dict[str, Any]:
        """Returns a single vehicle row keyed by column name."""
        if settings.DB_MODE == "ads_export":
            for row in self._load_snapshot_rows():
                if str(row.get("VehicleID")) == str(vehicle_id):
                    return row
            raise LookupError(f"Vehicle '{vehicle_id}' was not found in DB snapshot.")

        columns_sql = ", ".join(self._VEHICLE_COLUMNS)
        query = f"SELECT {columns_sql} FROM {self.vehicle_table} WHERE VehicleID = ?"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, vehicle_id)
            row = cursor.fetchone()

        if row is None:
            raise LookupError(f"Vehicle '{vehicle_id}' was not found in {self.vehicle_table}.")

        return self._row_to_dict(row, self._VEHICLE_COLUMNS)

    def count_vehicles(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        environment: Optional[str] = None,
        active_only: bool = True,
    ) -> int:
        """Returns vehicle count from the warehouse for the given slicer values."""
        if settings.DB_MODE == "ads_export":
            return sum(
                1
                for row in self._load_snapshot_rows()
                if self._matches_filters(
                    row,
                    district=district,
                    sub_unit=sub_unit,
                    category=category,
                    source=source,
                    environment=environment,
                    active_only=active_only,
                )
            )

        conditions: list[str] = []
        params: list[Any] = []

        if district is not None:
            conditions.append("Unit = ?")
            params.append(district)
        if sub_unit is not None:
            conditions.append("SubUnit = ?")
            params.append(sub_unit)
        if category is not None:
            conditions.append("VehicleCategory = ?")
            params.append(category)
        if source is not None:
            conditions.append("VehicleSource = ?")
            params.append(source)
        if environment is not None:
            conditions.append("Environment = ?")
            params.append(environment)
        if active_only:
            conditions.append("IsActive = 1")

        where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT COUNT(*) FROM {self.vehicle_table}{where_clause}"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return int(cursor.fetchone()[0])
