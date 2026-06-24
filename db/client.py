from typing import Optional

from config.settings import settings


class DatabaseClient:
    """Read-only database access for UI-to-DB validation tests."""

    def __init__(self):
        missing = [
            name
            for name, value in {
                "DB_SERVER": settings.DB_SERVER,
                "DB_NAME": settings.DB_NAME,
                "DB_USER": settings.DB_USER,
                "DB_PASSWORD": settings.DB_PASSWORD,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing database configuration: {', '.join(missing)}")

        self.server = settings.DB_SERVER
        self.database = settings.DB_NAME
        self.user = settings.DB_USER
        self.password = settings.DB_PASSWORD
        self.vehicle_table = settings.VEHICLE_DIM_TABLE

    def count_vehicles(
        self,
        district: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """Returns vehicle count from the warehouse. Implement when QA DB is ready."""
        raise NotImplementedError(
            "Database queries will be implemented in the next phase against a non-production QA DB."
        )
