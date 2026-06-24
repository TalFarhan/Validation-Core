from typing import Optional


class DatabaseClient:
    """Read-only database access for UI-to-DB validation tests."""

    def __init__(self):
        self.vehicle_table = "[DIM].[Vehicle]"

    def get_vehicle_by_id(self, vehicle_id: str) -> dict:
        raise NotImplementedError(
            "Database queries will be implemented when QA DB access is available "
            "from a managed environment."
        )

    def count_vehicles(
        self,
        district: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
    ) -> int:
        raise NotImplementedError(
            "Database queries will be implemented when QA DB access is available "
            "from a managed environment."
        )
