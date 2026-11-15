"""Read-only queries against DIM / FACT warehouse tables."""

from __future__ import annotations

from typing import Any, Literal, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.settings import settings
from db.connection import create_db_engine
from reports.test_run_report import get_current_report

KpiType = Literal["total", "in_use", "withdrawn", "allocated"]

# Status predicates apply only on DIM.[Vehicle].
_DIM_STATUS_FILTERS = {
    "total": "1 = 1",
    "in_use": "[IsActive] = 1",
}

class DatabaseClient:
    """Runs SELECT/COUNT queries for dashboard KPI validation."""

    def __init__(self, engine: Engine | None = None):
        self._engine = engine or create_db_engine()
        self._dim_table = settings.DB_TABLE
        self._withdrawn_table = settings.DB_WITHDRAWN_TABLE
        self._allocated_table = settings.DB_ALLOCATED_TABLE

    def _table_for(self, kpi_type: KpiType) -> str:
        if kpi_type in ("total", "in_use"):
            return self._dim_table
        if kpi_type == "withdrawn":
            return self._withdrawn_table
        if kpi_type == "allocated":
            return self._allocated_table
        raise ValueError(f"Unknown kpi_type: {kpi_type}")

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

    def _filter_clause(self, *, on_dim: bool) -> str:
        """Build WHERE predicates for DIM or FACT KPI counts.

        DIM slicers are applied on DIM columns directly.
        FACT cards in Power BI are cross-filtered through the DIM relationship
        (VehicleID) — Unit / SubUnit / Category / Source on FACT rows can differ
        from the DIM attributes of the same vehicle, so FACT filters resolve via
        a DIM subquery rather than FACT.[Unit] / FACT.[VehicleSource].
        """
        if on_dim:
            return """
            [Environment] = :environment
            AND (:unit IS NULL OR [Unit] = :unit)
            AND (:sub_unit IS NULL OR [SubUnit] = :sub_unit)
            AND (:category IS NULL OR [VehicleCategory] = :category)
            AND (:source IS NULL OR [VehicleSource] = :source)
            """

        return f"""
            [Environment] = :environment
            AND (
                  (
                    :unit IS NULL AND :sub_unit IS NULL
                    AND :category IS NULL AND :source IS NULL
                  )
                  OR [VehicleID] IN (
                        SELECT [VehicleID]
                        FROM {self._dim_table}
                        WHERE [Environment] = :environment
                          AND (:unit IS NULL OR [Unit] = :unit)
                          AND (:sub_unit IS NULL OR [SubUnit] = :sub_unit)
                          AND (:category IS NULL OR [VehicleCategory] = :category)
                          AND (:source IS NULL OR [VehicleSource] = :source)
                  )
            )
            """

    @staticmethod
    def _record_query(
        method: str, sql: str, params: dict[str, Any] | None, result: Any
    ) -> None:
        report = get_current_report()
        if report is not None:
            report.log_db_query(method=method, sql=sql, params=params, result=result)

    def count_vehicles(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        kpi_type: KpiType = "total",
    ) -> int:
        table = self._table_for(kpi_type)
        on_dim = kpi_type in ("total", "in_use")
        # FACT KPIs use the same slicers as DIM, resolved via VehicleID→DIM
        # (matches Power BI relationship cross-filter behavior).
        status_filter = _DIM_STATUS_FILTERS.get(kpi_type, "1 = 1")
        sql = f"""
            SELECT COUNT(*) AS [VehicleCount]
            FROM {table}
            WHERE {self._filter_clause(on_dim=on_dim)}
              AND ({status_filter})
            """
        params = self._filter_params(
            district=district,
            sub_unit=sub_unit,
            category=category,
            source=source,
        )
        params_with_kpi = {**params, "kpi_type": kpi_type}

        with self._engine.connect() as conn:
            row = conn.execute(text(sql), params).mappings().one()

        value = int(row["VehicleCount"])
        self._record_query("count_vehicles", sql, params_with_kpi, value)
        return value

    def get_dashboard_kpis(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
    ) -> dict[str, int]:
        filters = {
            "district": district,
            "sub_unit": sub_unit,
            "category": category,
            "source": source,
        }
        result = {
            kpi: self.count_vehicles(kpi_type=kpi, **filters)
            for kpi in ("total", "in_use", "withdrawn", "allocated")
        }
        self._record_query("get_dashboard_kpis", "composed count_vehicles", filters, result)
        return result

    def get_vehicle_by_id(self, vehicle_id: int | str) -> dict[str, Any]:
        sql = f"SELECT * FROM {self._dim_table} WHERE [VehicleID] = :vehicle_id"
        params = {"vehicle_id": int(vehicle_id)}

        with self._engine.connect() as conn:
            row = conn.execute(text(sql), params).mappings().first()

        if row is None:
            self._record_query("get_vehicle_by_id", sql, params, None)
            raise KeyError(f"Vehicle {vehicle_id} not found")

        result = dict(row)
        self._record_query("get_vehicle_by_id", sql, params, result)
        return result

    def get_sample_vehicle_id(
        self,
        *,
        district: Optional[str] = None,
        sub_unit: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        kpi_type: KpiType = "total",
    ) -> int:
        table = self._table_for(kpi_type)
        on_dim = kpi_type in ("total", "in_use")
        status_filter = _DIM_STATUS_FILTERS.get(kpi_type, "1 = 1")
        sql = f"""
            SELECT TOP 1 [VehicleID]
            FROM {table}
            WHERE {self._filter_clause(on_dim=on_dim)}
              AND ({status_filter})
            ORDER BY [VehicleID]
            """
        params = self._filter_params(
            district=district,
            sub_unit=sub_unit,
            category=category,
            source=source,
        )
        params_with_kpi = {**params, "kpi_type": kpi_type}

        with self._engine.connect() as conn:
            row = conn.execute(text(sql), params).mappings().first()

        if row is None:
            self._record_query("get_sample_vehicle_id", sql, params_with_kpi, None)
            raise LookupError("No vehicle matches the given filters")

        value = int(row["VehicleID"])
        self._record_query("get_sample_vehicle_id", sql, params_with_kpi, value)
        return value

    def get_unique_vehicle_id_for_search(
        self,
        *,
        kpi_type: KpiType = "total",
    ) -> int:
        """
        Pick a VehicleID that is unique under contains-search.

        The dashboard search slicer matches by vehicle number as a substring,
        so short IDs like 111111 can return multiple rows. Prefer a longer ID
        that does not appear inside any other VehicleID string.
        """
        if kpi_type not in ("total", "in_use"):
            raise ValueError(
                "get_unique_vehicle_id_for_search supports only DIM KPIs "
                f"(total/in_use), got {kpi_type!r}"
            )
        status_filter = (
            "1 = 1" if kpi_type == "total" else "v.[IsActive] = 1"
        )
        sql = f"""
            SELECT TOP 1 v.[VehicleID]
            FROM {self._dim_table} v
            WHERE v.[Environment] = :environment
              AND ({status_filter})
              AND NOT EXISTS (
                    SELECT 1
                    FROM {self._dim_table} o
                    WHERE o.[Environment] = :environment
                      AND o.[VehicleID] <> v.[VehicleID]
                      AND CAST(o.[VehicleID] AS VARCHAR(50)) LIKE
                          '%' + CAST(v.[VehicleID] AS VARCHAR(50)) + '%'
              )
            ORDER BY LEN(CAST(v.[VehicleID] AS VARCHAR(50))) DESC,
                     v.[VehicleID] DESC
            """
        params = {"environment": settings.DB_ENVIRONMENT, "kpi_type": kpi_type}

        with self._engine.connect() as conn:
            row = conn.execute(text(sql), params).mappings().first()

        if row is None:
            self._record_query("get_unique_vehicle_id_for_search", sql, params, None)
            raise LookupError("No VehicleID is unique under contains-search")

        value = int(row["VehicleID"])
        self._record_query("get_unique_vehicle_id_for_search", sql, params, value)
        return value

    def count_vehicles_by_id_contains(
        self,
        needle: int | str,
        *,
        kpi_type: KpiType = "total",
    ) -> int:
        """Count DIM vehicles whose VehicleID string contains ``needle``."""
        if kpi_type not in ("total", "in_use"):
            raise ValueError(
                "count_vehicles_by_id_contains supports only DIM KPIs "
                f"(total/in_use), got {kpi_type!r}"
            )
        status_filter = _DIM_STATUS_FILTERS[kpi_type]
        sql = f"""
            SELECT COUNT(*) AS [VehicleCount]
            FROM {self._dim_table}
            WHERE [Environment] = :environment
              AND ({status_filter})
              AND CAST([VehicleID] AS VARCHAR(50)) LIKE :pattern
            """
        params = {
            "environment": settings.DB_ENVIRONMENT,
            "pattern": f"%{needle}%",
            "kpi_type": kpi_type,
            "needle": str(needle),
        }

        with self._engine.connect() as conn:
            row = conn.execute(
                text(sql),
                {
                    "environment": params["environment"],
                    "pattern": params["pattern"],
                },
            ).mappings().one()

        value = int(row["VehicleCount"])
        self._record_query("count_vehicles_by_id_contains", sql, params, value)
        return value

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
        """Group counts on DIM.[Vehicle] only (chart breakdowns)."""
        if kpi_type not in ("total", "in_use"):
            raise ValueError(
                f"count_grouped_by supports only DIM KPIs (total/in_use), got {kpi_type!r}"
            )

        status_filter = _DIM_STATUS_FILTERS[kpi_type]
        sql = f"""
            SELECT [{group_column}] AS [GroupValue], COUNT(*) AS [VehicleCount]
            FROM {self._dim_table}
            WHERE {self._filter_clause(on_dim=True)}
              AND ({status_filter})
              AND [{group_column}] IS NOT NULL
              AND LTRIM(RTRIM(CAST([{group_column}] AS NVARCHAR(4000)))) <> ''
            GROUP BY [{group_column}]
            """
        params = self._filter_params(
            district=district,
            sub_unit=sub_unit,
            category=category,
            source=source,
        )
        params_with_meta = {
            **params,
            "group_column": group_column,
            "kpi_type": kpi_type,
        }

        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        result = {str(row["GroupValue"]): int(row["VehicleCount"]) for row in rows}
        self._record_query("count_grouped_by", sql, params_with_meta, result)
        return result

    def count_by_source(self, **filters: Any) -> dict[str, int]:
        return self.count_grouped_by("VehicleSource", kpi_type="in_use", **filters)

    def count_by_unit(self, **filters: Any) -> dict[str, int]:
        return self.count_grouped_by("Unit", kpi_type="in_use", **filters)

    def count_by_sub_unit(self, **filters: Any) -> dict[str, int]:
        """In-use vehicles grouped by SubUnit (unit-chart hierarchy child level)."""
        return self.count_grouped_by("SubUnit", kpi_type="in_use", **filters)

    def count_by_category(self, **filters: Any) -> dict[str, int]:
        return self.count_grouped_by("VehicleCategory", kpi_type="total", **filters)

    def count_by_withdrawal_reason(self, **filters: Any) -> dict[str, int]:
        """Withdrawn rows grouped by TransferReason (withdrawal-reasons chart)."""
        sql = f"""
            SELECT [TransferReason] AS [GroupValue], COUNT(*) AS [VehicleCount]
            FROM {self._withdrawn_table}
            WHERE {self._filter_clause(on_dim=False)}
              AND [TransferReason] IS NOT NULL
              AND LTRIM(RTRIM(CAST([TransferReason] AS NVARCHAR(4000)))) <> ''
            GROUP BY [TransferReason]
            """
        params = self._filter_params(
            district=filters.get("district"),
            sub_unit=filters.get("sub_unit"),
            category=filters.get("category"),
            source=filters.get("source"),
        )

        with self._engine.connect() as conn:
            rows = conn.execute(text(sql), params).mappings().all()

        result = {str(row["GroupValue"]): int(row["VehicleCount"]) for row in rows}
        self._record_query("count_by_withdrawal_reason", sql, params, result)
        return result

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
