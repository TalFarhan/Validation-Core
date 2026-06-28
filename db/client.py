"""Read-only queries against the existing vehicle table."""

from __future__ import annotations
from typing import Any, Literal, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine
from config.settings import settings
from db.connection import create_db_engine

KpiType = Literal["total", "in_use", "withdrawn", "allocated"]

_STATUS_FILTERS = {
    "total": "1 = 1",
    "in_use": "[IsActive] = 1",
    "withdrawn": "[IsActive] = 0",
    "allocated": "[IsAllocated] = 1",
}


class DatabaseClient:
    """Runs SELECT/COUNT queries on the configured warehouse table."""

    def __init__(self, engine: Engine | None = None):
        self._engine = engine or create_db_engine()
        self._table = settings.DB_TABLE

    def _filter_params(
        self,
        *,
        district: Optional[str],
        sub_unit: Optional[str],
        category: Optional[str],
        source: Optional[str],
    ) -> dict[str, Any]:
        return {
            "environment": settings.DB_ENVIRONMENT,
            "unit": district,
            "sub_unit": sub_unit,
            "category": category,
            "source": source,
        }

    def _filter_clause(self) -> str:
        return """
            [Environment] = :environment
            AND (:unit IS NULL OR [Unit] = :unit)
            AND (:sub_unit IS NULL OR [SubUnit] = :sub_unit)
            AND (:category IS NULL OR [VehicleCategory] = :category)
            AND (:source IS NULL OR [VehicleSource] = :source)
        """

    def count_vehicles(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        kpi_type: KpiType = "total",
    ) -> int:
        if kpi_type == "allocated" and not settings.DB_HAS_ALLOCATED:
            return 0

        status_filter = _STATUS_FILTERS[kpi_type]
        query = text(
            f"""
            SELECT COUNT(*) AS [VehicleCount]
            FROM {self._table}
            WHERE {self._filter_clause()}
              AND ({status_filter})
            """
        )

        with self._engine.connect() as conn:
            row = conn.execute(
                query,
                self._filter_params(
                    district=district,
                    sub_unit=sub_unit,
                    category=category,
                    source=source,
                ),
            ).mappings().one()

        return int(row["VehicleCount"])

    def get_dashboard_kpis(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
    ) -> dict[str, int]:
        allocated_expr = (
            "SUM(CASE WHEN [IsAllocated] = 1 THEN 1 ELSE 0 END)"
            if settings.DB_HAS_ALLOCATED
            else "0"
        )
        query = text(
            f"""
            SELECT
                COUNT(*) AS [TotalReceived],
                SUM(CASE WHEN [IsActive] = 1 THEN 1 ELSE 0 END) AS [InUse],
                SUM(CASE WHEN [IsActive] = 0 THEN 1 ELSE 0 END) AS [Withdrawn],
                {allocated_expr} AS [Allocated]
            FROM {self._table}
            WHERE {self._filter_clause()}
            """
        )

        with self._engine.connect() as conn:
            row = conn.execute(
                query,
                self._filter_params(
                    district=district,
                    sub_unit=sub_unit,
                    category=category,
                    source=source,
                ),
            ).mappings().one()

        return {
            "total": int(row["TotalReceived"] or 0),
            "in_use": int(row["InUse"] or 0),
            "withdrawn": int(row["Withdrawn"] or 0),
            "allocated": int(row["Allocated"] or 0),
        }

    def get_vehicle_by_id(self, vehicle_id: int | str) -> dict[str, Any]:
        query = text(f"SELECT * FROM {self._table} WHERE [VehicleID] = :vehicle_id")

        with self._engine.connect() as conn:
            row = conn.execute(query, {"vehicle_id": int(vehicle_id)}).mappings().first()

        if row is None:
            raise KeyError(f"Vehicle {vehicle_id} not found")

        return dict(row)

    def get_sample_vehicle_id(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        kpi_type: KpiType = "total",
    ) -> int:
        if kpi_type == "allocated" and not settings.DB_HAS_ALLOCATED:
            raise LookupError("No allocated vehicles when DB_HAS_ALLOCATED is disabled")

        status_filter = _STATUS_FILTERS[kpi_type]
        query = text(
            f"""
            SELECT TOP 1 [VehicleID]
            FROM {self._table}
            WHERE {self._filter_clause()}
              AND ({status_filter})
            ORDER BY [VehicleID]
            """
        )

        with self._engine.connect() as conn:
            row = conn.execute(
                query,
                self._filter_params(
                    district=district,
                    sub_unit=sub_unit,
                    category=category,
                    source=source,
                ),
            ).mappings().first()

        if row is None:
            raise LookupError("No vehicle matches the given filters")

        return int(row["VehicleID"])

    def count_grouped_by(
        self,
        group_column: str,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        kpi_type: KpiType = "total",
    ) -> dict[str, int]:
        if kpi_type == "allocated" and not settings.DB_HAS_ALLOCATED:
            return {}

        status_filter = _STATUS_FILTERS[kpi_type]
        query = text(
            f"""
            SELECT [{group_column}] AS [GroupValue], COUNT(*) AS [VehicleCount]
            FROM {self._table}
            WHERE {self._filter_clause()}
              AND ({status_filter})
              AND [{group_column}] IS NOT NULL
              AND LTRIM(RTRIM(CAST([{group_column}] AS NVARCHAR(4000)))) <> ''
            GROUP BY [{group_column}]
            """
        )

        with self._engine.connect() as conn:
            rows = conn.execute(
                query,
                self._filter_params(
                    district=district,
                    sub_unit=sub_unit,
                    category=category,
                    source=source,
                ),
            ).mappings().all()

        return {str(row["GroupValue"]): int(row["VehicleCount"]) for row in rows}

    def count_by_source(self, **filters: Any) -> dict[str, int]:
        return self.count_grouped_by("VehicleSource", kpi_type="in_use", **filters)

    def count_by_unit(self, **filters: Any) -> dict[str, int]:
        return self.count_grouped_by("Unit", kpi_type="in_use", **filters)

    def count_by_category(self, **filters: Any) -> dict[str, int]:
        return self.count_grouped_by("VehicleCategory", kpi_type="total", **filters)

    def find_zero_count_filters(
        self,
        filter_data: dict[str, dict[str, str]],
    ) -> dict[str, str] | None:
        for district in filter_data["districts"].values():
            for category in filter_data["categories"].values():
                for source in filter_data["sources"].values():
                    if self.count_vehicles(
                        district=district,
                        category=category,
                        source=source,
                    ) == 0:
                        return {
                            "district": district,
                            "category": category,
                            "source": source,
                        }
        return None
