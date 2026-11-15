"""Read-only DB runner for the Alerts dashboard parity checks."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.settings import settings
from db.connection import create_db_engine
from reports.test_run_report import get_current_report

# Placeholder SELECTs for visuals whose warehouse SQL is not confirmed.
# They are executed as written. A missing database must surface as a connection error.
# The literal is not a business result, so a reachable server still fails parity.
SETTLEMENTS_CHART_SQL = (
    "SELECT 'placeholder' AS category_label, CAST(NULL AS int) AS metric_value"
)
MAP_PRESENCE_SQL = "SELECT 'placeholder'"
POLICY_STATUS_SQL = "SELECT 'placeholder'"

# Placeholder SELECTs for the time-bucket cards. Executed as written.
# A missing database must surface as a connection error.
THREAT_KPI_STUB_SQL = "SELECT 0"
POPULATION_KPI_STUB_SQL = "SELECT 0"
AREA_KPI_STUB_SQL = "SELECT 0"

# Current-day versus previous-day settlements. This statement ignores the
# slicer window: it must not reference AlertDate, :start_date, or :end_date.
# WHERE 1 = 0 yields no rows, so rows() does not see a blank label.
PERIOD_COMPARISON_CHART_SQL = (
    "SELECT CAST(NULL AS nvarchar(200)) AS category_label, "
    "CAST(NULL AS int) AS metric_value WHERE 1 = 0"
)

# Population page placeholders. Not executed by the population UI tests.
# The page-1 parity test excludes this page's scope.
#
# Future rules when these constants are replaced:
# - Half-open dates: AlertDate >= :start_date AND AlertDate < :end_date.
# - One grouping grain at a time, from district down to settlement.
#   Do not add a parent total to its children.
# - Sum mode is SUM of the grouped measure.
#   Average mode is that SUM divided by the group count
#   (SUM / NULLIF(COUNT, 0)), not a second measure.
POPULATION_PAGE_KPI_STUB_SQL = "SELECT 0"
POPULATION_PAGE_CHART_STUB_SQL = (
    "SELECT CAST(NULL AS nvarchar(200)) AS category_label, "
    "CAST(NULL AS int) AS metric_value WHERE 1 = 0"
)


class AlertsDBRunner:
    """Executes parameterized SELECTs against the Alerts database."""

    def __init__(self, engine: Engine | None = None) -> None:
        self._engine = engine or create_db_engine(database=settings.DB_ALERTS_NAME)

    def scalar(
        self,
        sql: str,
        *,
        start_date: datetime | date,
        end_date: datetime | date,
        category_id: str | None = None,
    ) -> int | float:
        """Run a single-scalar query binding dates and an optional category id.

        Dates and category_id are bound via SQLAlchemy text(). They are never
        formatted into the SQL string. NULL becomes 0, matching ISNULL sums.
        """
        params = self._params(start_date, end_date, category_id)
        with self._engine.connect() as conn:
            raw = conn.execute(text(sql), params).scalar()

        value = 0 if raw is None else self._coerce_number(raw)
        self._record_query("alerts.scalar", sql, params, value)
        return value

    def rows(
        self,
        sql: str,
        *,
        start_date: datetime | date,
        end_date: datetime | date,
        category_id: str | None = None,
    ) -> list[tuple[str, int | float | None]]:
        """Run a two-column query: category label, then one numeric value.

        A SQL NULL value stays None so a missing chart bar is not stored as 0.
        A NULL or blank label is a contract error.
        """
        params = self._params(start_date, end_date, category_id)
        with self._engine.connect() as conn:
            fetched = conn.execute(text(sql), params).fetchall()

        parsed: list[tuple[str, int | float | None]] = []
        for row in fetched:
            label = row[0]
            if label is None or not str(label).strip():
                raise ValueError("Chart query returned a blank category label")
            raw_value = row[1]
            value = None if raw_value is None else self._coerce_number(raw_value)
            parsed.append((str(label).strip(), value))

        self._record_query("alerts.rows", sql, params, parsed)
        return parsed

    def cell(
        self,
        sql: str,
        *,
        start_date: datetime | date,
        end_date: datetime | date,
        category_id: str | None = None,
    ) -> int | float | str | None:
        """Return the first column unchanged enough for text and map presence.

        SQL NULL stays None so an empty map is not stored as 0. A string is
        stripped. A number uses the same coercion as scalar.
        """
        params = self._params(start_date, end_date, category_id)
        with self._engine.connect() as conn:
            raw = conn.execute(text(sql), params).scalar()

        if raw is None:
            value = None
        elif isinstance(raw, str):
            value = raw.strip()
        else:
            value = self._coerce_number(raw)
        self._record_query("alerts.cell", sql, params, value)
        return value

    @staticmethod
    def _params(
        start_date: datetime | date,
        end_date: datetime | date,
        category_id: str | None,
    ) -> dict:
        """Bind dates always. Include category_id only when the caller set it."""
        params: dict = {"start_date": start_date, "end_date": end_date}
        if category_id is not None:
            params["category_id"] = category_id
        return params

    @staticmethod
    def _coerce_number(raw) -> int | float:
        """Coerce a SQL scalar to int (when integral) or float. NULL is not passed here."""
        number = float(raw)
        if number.is_integer():
            return int(number)
        return number

    @staticmethod
    def _record_query(method: str, sql: str, params: dict, result) -> None:
        report = get_current_report()
        if report is not None:
            report.log_db_query(method=method, sql=sql, params=params, result=result)
