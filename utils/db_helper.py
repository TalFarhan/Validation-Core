import pyodbc

from config.settings import settings

_PREFERRED_DRIVERS = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server",
)


def _resolve_driver() -> str:
    if settings.DB_DRIVER:
        return settings.DB_DRIVER

    installed = set(pyodbc.drivers())
    for driver in _PREFERRED_DRIVERS:
        if driver in installed:
            if driver == "SQL Server" and (
                "@" in settings.DB_USER or settings.DB_AUTH.startswith("aad_")
            ):
                raise RuntimeError(
                    "Azure AD login requires 'ODBC Driver 17/18 for SQL Server' on the machine "
                    "where pytest runs (same requirement as Azure Data Studio). "
                    "Install from https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server "
                    "or set DB_MODE=ads_export to use a JSON export from Azure Data Studio."
                )
            return driver

    raise RuntimeError(
        "No SQL Server ODBC driver found. Install 'ODBC Driver 18 for SQL Server', "
        "or set DB_MODE=ads_export to use a JSON export from Azure Data Studio."
    )


def _format_value(key: str, value: str) -> str:
    """Wrap values that contain reserved ODBC characters (e.g. @ in AAD emails)."""
    if any(char in value for char in (";", "}", "@")):
        escaped = value.replace("}", "}}")
        return f"{key}={{{escaped}}}"
    return f"{key}={value}"


def build_connection_string() -> str:
    if settings.DB_CONNECTION_STRING:
        return settings.DB_CONNECTION_STRING

    driver = _resolve_driver()
    is_modern_driver = "17" in driver or "18" in driver

    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={settings.DB_SERVER}",
        f"DATABASE={settings.DB_NAME}",
        "Connection Timeout=30",
    ]

    if settings.DB_AUTH == "aad_interactive":
        if not settings.DB_USER:
            raise ValueError("DB_USER is required for aad_interactive authentication.")
        parts.append(_format_value("UID", settings.DB_USER))
        if is_modern_driver:
            parts.extend(
                [
                    "Encrypt=yes",
                    "TrustServerCertificate=no",
                    "Authentication=ActiveDirectoryInteractive",
                ]
            )
    elif settings.DB_AUTH == "aad_password":
        parts.extend(
            [
                _format_value("UID", settings.DB_USER),
                _format_value("PWD", settings.DB_PASSWORD),
            ]
        )
        if is_modern_driver:
            parts.extend(
                [
                    "Encrypt=yes",
                    "TrustServerCertificate=no",
                    "Authentication=ActiveDirectoryPassword",
                ]
            )
    else:
        parts.extend(
            [
                _format_value("UID", settings.DB_USER),
                _format_value("PWD", settings.DB_PASSWORD),
            ]
        )
        if is_modern_driver:
            parts.extend(["Encrypt=yes", "TrustServerCertificate=no"])
        elif settings.DB_SERVER.endswith(".database.windows.net"):
            parts.append("Encrypt=yes")

    return ";".join(parts) + ";"


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(build_connection_string())
