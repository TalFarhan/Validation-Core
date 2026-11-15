# Contract: Generic DB Parity Engine + Alerts Pilot

Interface contracts for the new components. These are the stable surfaces tests and future reports depend on.

## 1. Layer 2 — `core/components/kpi.py` (`KPI`)

Report-agnostic. No Alerts/fleet strings or SQL. Mirrors the `Slicer` composition model.

```python
class KPI:
    def __init__(
        self,
        page: Page,
        frame: FrameLocator,
        timeout_ms: int | None = None,
    ) -> None: ...

    def card(self, title: str) -> Locator:
        """Locate a KPI card by its (opaque) title text inside the report iframe."""

    def read_text(self, title: str) -> str:
        """Raw, un-normalized value text from the card's value node."""

    def value(self, title: str) -> str:
        """Normalized string value (commas, whitespace, RTL/LTR marks stripped)."""

    def number(self, title: str) -> int | float:
        """Normalized numeric value (int when integral, else float)."""


def normalize_kpi_text(raw: str) -> str:
    """Strip ',', whitespace (incl. NBSP), and \\u200f / \\u200e; return cleaned text."""
```

Contract rules:
- MUST NOT import from `pages/` or `tests/`; MUST NOT embed any report-specific title or SQL.
- Card lookup strategy: `frame.get_by_role("button", name=re.compile(re.escape(title)))`, value node
  `card.locator("p").last` (consistent with existing fleet KPI reading).
- `number()` raises `ValueError` if the normalized text is not numeric.

## 2. DB runner — `db/clients/alerts.py` (`AlertsDBRunner`)

```python
class AlertsDBRunner:
    def __init__(self, engine: Engine | None = None) -> None:
        """Defaults to create_db_engine(database=settings.DB_ALERTS_NAME)."""

    def scalar(
        self,
        sql: str,
        *,
        start_date,   # datetime | date
        end_date,     # datetime | date
    ) -> int | float:
        """Execute a parameterized SELECT returning one scalar."""
```

Contract rules:
- MUST execute via `sqlalchemy.text(sql)` with bound params
  `{"start_date": start_date, "end_date": end_date}`. **No** f-strings / `.format()` on dates.
- Read-only: `SELECT` only.
- MUST log through `get_current_report().log_db_query(...)` when a report is active.
- Numeric coercion: `int` when the scalar is integral, else `float`; `NULL` → treated as `0` only when the SQL
  itself returns `0` (e.g. `ISNULL(...)`) — the runner does not invent defaults.

## 3. Engine — `tests/helpers/db_parity_engine.py`

```python
def validate_dashboard_generic(
    yaml_path: str | Path,
    page,            # a ReportShell-based page object (exposes the report iframe FrameLocator)
    db_client,       # AlertsDBRunner (or any object with .scalar(sql, start_date=, end_date=))
    start_date,      # datetime | date
    end_date,        # datetime | date
) -> list[ParityResult]:
    """Load YAML contract; for each metric compare UI KPI vs DB scalar; assert all equal."""
```

Contract rules:
- Loads the contract with `yaml.safe_load`; errors clearly if `metrics` is missing/empty.
- Builds a `KPI` from the page's report iframe `FrameLocator` (e.g. `page._report_frame()` or the page's
  exposed `dashboard` frame).
- For each metric: read UI via `KPI.number(name)`, read DB via `db_client.scalar(sql_query, start_date,
  end_date)`, log `log_kpi_read` / `log_db_query` / `log_assertion`.
- Asserts every metric matches; raises a single `AssertionError` enumerating all mismatches
  (`name`, `ui_value`, `db_value`).
- Returns the list of `ParityResult` for optional inspection.

## 4. YAML contract — `tests/ui/alerts_dashboard/alerts_contract.yaml`

```yaml
metrics:
  - name: "<UI KPI title>"
    sql_query: "SELECT ... WHERE AlertDate >= :start_date AND AlertDate < :end_date ..."
```

Schema: top-level `metrics:` list; each item `{ name: str, sql_query: str }`. `sql_query` uses `:start_date` /
`:end_date` named binds only. (Full pilot content in [data-model.md](../data-model.md).)

## 5. Alerts page object — `tests/ui/alerts_dashboard/page.py`

```python
class AlertsDashboardPage(ReportShell):
    DASHBOARD_SEARCH_TERM = "<alerts product catalog name>"
    # Single dropdown SlicerDefinition for the date-range control (role_name = its accessible name).
    def select_date_range(self, value: str) -> None:
        """Select a date-range option (e.g. 'שלושים יום אחרונים') via the composed Slicer."""
```

Contract rules:
- Extends `ReportShell`; supplies `_report_ready_locator()` and a `Slicer` with the date-range definition.
- Domain strings (search term, slicer `role_name`, option value) live here/in the test — never in `core/`.

## 6. Settings / config

- `config/settings.py`: add `DB_ALERTS_NAME = _env("DB_ALERTS_NAME", "<alerts_db_name>")`.
- `pytest.ini`: add `db_parity: UI-vs-DB parity checks driven by a YAML contract` to `markers`.
- `requirements.txt`: add `pyyaml>=6.0`.

## 7. Test — `tests/ui/alerts_dashboard/test_db_parity.py`

```python
@pytest.mark.db_parity
def test_alerts_db_parity_last_30_days(dashboard, alerts_db):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dashboard.select_date_range("שלושים יום אחרונים")
    validate_dashboard_generic(
        CONTRACT_PATH, dashboard, alerts_db, start_date, end_date
    )
```

Contract rules:
- Marked `@pytest.mark.db_parity`.
- Computes the 30-day half-open window in Python; passes `datetime`/`date` objects (never strings) to the
  engine, which binds them via `text()`.
- Drives the slicer through the page object (Constitution IV), not ad-hoc locators.
