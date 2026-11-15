# Phase 0 Research: Generic DB Parity Engine + Alerts Pilot

All items below were resolved against the live codebase; no open **NEEDS CLARIFICATION** remain.

## R1 — How is a Power BI KPI value read today, and how to genericize it

- **Decision**: Model `core/components/kpi.py` on the `Slicer` (Layer 2) pattern: a class composed by the
  caller with a `FrameLocator`, holding no report-specific strings. It locates a card by the **title string
  passed in** and reads the value node.
- **Rationale**: `BasePage._read_kpi_value` already reads a KPI as
  `kpi_locator.locator("p").last.text_content()` and normalizes with `.replace(",", "")`
  (see `core/base_page.py` lines 22-24). The fleet card locator is
  `self.dashboard.get_by_role("button", name=re.compile(re.escape(title)))`
  (`pages/fleet_dashboard/main_dashboard_page.py` `_kpi_card`). The generic component reuses exactly this
  approach but takes the title as an opaque argument, keeping Layer 2 report-agnostic (Constitution II).
- **Normalization**: Across the fleet page, raw Power BI text is cleaned with
  `.replace("\u200f", "").replace(",", "")` and `.strip()` in many places (e.g. lines 821, 1087, 1141).
  The generic normalizer strips commas, all whitespace (including NBSP `\u00a0`), and the RTL mark `\u200f`
  (plus `\u200e`), returning both a cleaned string and an `int`/`float` when the cleaned text is numeric.
- **Alternatives considered**: Extending `BasePage._read_kpi_value` in place — rejected because the card
  *lookup by title* (not just value parsing) is the shared behavior a second report needs, and a dedicated
  Layer 2 component mirrors the existing `Slicer` design and keeps the title opaque.

## R2 — Is genericizing KPI reading constitutionally "earned" now (Principle VII)?

- **Decision**: Yes. Extract KPI card lookup + value normalization to Layer 2.
- **Rationale**: Constitution VII says "KPI cards … MUST stay on the domain page until a **second report**
  requires the same behavior." The Alerts Dashboard is that second report. The extracted behavior (find card
  by title, read value, normalize) is report-agnostic; the titles themselves stay in the Alerts contract and
  test, never in `core/`.
- **Scope guard**: Fleet is **not** refactored in this feature (Non-Goal). The component is additive; fleet
  keeps `_read_kpi_value`. Adopting the component in fleet is a later, separate change gated by fleet smoke.

## R3 — Multi-database connection to the Alerts DB

- **Decision**: Reuse `db/connection.py:create_db_engine(database=...)` and
  `build_connection_string(database=...)`, which already accept a `database` override. Add a settings value
  `DB_ALERTS_NAME` (env `DB_ALERTS_NAME`) for the Alerts database name; `db/clients/alerts.py` builds its
  engine with that database.
- **Rationale**: The connection helpers are already parameterized by database name and use
  `Trusted_Connection=yes` against `settings.DB_SERVER` with the configured ODBC driver. No new connection
  machinery is required — only a database-name setting and a thin runner.
- **Alternatives considered**: A separate connection module for Alerts — rejected as duplication; the existing
  helper already supports per-database engines.

## R4 — Safe parameter binding for dates (SQLAlchemy `text()`)

- **Decision**: Execute every contract query with `sqlalchemy.text(sql)` and pass
  `{"start_date": start_date, "end_date": end_date}` as bound parameters to `conn.execute(...)`.
- **Rationale**: This matches the established pattern throughout `db/client.py`
  (`conn.execute(text(sql), params)`). Named binds `:start_date` / `:end_date` in the YAML `sql_query` map
  directly to the params dict. Dates are passed as Python `datetime`/`date` objects; pyodbc + SQL Server
  handle type coercion. No f-strings or `.format()` touch the SQL (Constitution-adjacent safety; FR-006).
- **Alternatives considered**: String interpolation of dates — rejected (injection risk, violates the strict
  rule in the request and project SQL conventions).

## R5 — Loading the YAML contract

- **Decision**: Parse the contract with `PyYAML` (`yaml.safe_load`). Add `pyyaml>=6.0` to `requirements.txt`.
- **Rationale**: `requirements.txt` has no YAML parser today. `PyYAML` is the de-facto standard and
  `safe_load` avoids arbitrary object construction. The contract is a trusted, in-repo file.
- **Schema**: top-level `metrics:` list; each item has `name` (UI KPI title, string) and `sql_query`
  (parameterized SQL returning a single scalar). Optional future keys (e.g. `tolerance`) are ignored by the
  pilot engine.
- **Alternatives considered**: JSON contract — rejected; the request specifies YAML and YAML comments/readability
  suit human-authored SQL contracts better.

## R6 — Alerts Dashboard page object and the "שלושים יום אחרונים" slicer

- **Decision**: Reuse the existing `tests/ui/alerts_analysis_dashboard/page.py` pattern (a `ReportShell`
  subclass with a `DASHBOARD_SEARCH_TERM`) and compose a `Slicer` with a single dropdown definition for the
  date-range control. The pilot test selects the value "שלושים יום אחרונים".
- **Rationale**: `AlertsAnalysisPage` already binds Layer 0 for the Alerts Analysis report. The pilot needs a
  date-range dropdown; the generic `Slicer.select(slicer_id, value)` already handles dropdown selection and
  retry/settle. The slicer's `role_name` (accessible name of the date-range control) is a domain value that
  lives on the page object / test, not in `core/`.
- **Open implementation detail (non-blocking)**: the exact accessible `role_name` of the Alerts date-range
  dropdown is confirmed at implementation time by inspecting the live control; it is a domain locator value,
  not an architectural unknown.
- **Alternatives considered**: Hardcoding the slicer click in the test body — rejected (Constitution IV: page
  objects / shared components drive the browser, not ad-hoc test locators).

## R7 — 30-day window computation and `start_date` / `end_date` semantics

- **Decision**: Compute `end_date = datetime.now()` (or `date.today()` normalized to midnight) and
  `start_date = end_date - timedelta(days=30)` in Python. The SQL uses a half-open interval
  `AlertDate >= :start_date AND AlertDate < :end_date` (matches the contract's queries).
- **Rationale**: The provided SQL already uses `>= :start_date AND < :end_date`, so Python supplies a
  half-open `[start, end)` window. Computing in Python keeps the engine declarative and the window explicit in
  the test, and mirrors the UI's "last 30 days" slicer semantics.
- **Alternatives considered**: Computing dates inside SQL (`DATEADD`) — rejected; the request requires Python
  date calculation and parameter binding.

## R8 — Test marker, fixtures, and observability

- **Decision**: Register `db_parity` in `pytest.ini` `markers`. Reuse the session-scoped `db_client` style for
  an Alerts client (a new fixture or direct construction in the test) and the shared `dashboard` fixture
  pattern via `bind_dashboard`. Route reads/queries/assertions through `get_current_report()` hooks.
- **Rationale**: `pytest.ini` uses `--strict-markers`, so an unregistered marker fails collection. The repo
  already logs via `report.log_kpi_read`, `report.log_db_query`, `report.log_assertion`
  (see `db/client.py` and the fleet page), satisfying Constitution VI without new plumbing.
- **Alternatives considered**: Reusing the fleet `db_client` fixture — rejected; that client targets the Fleet
  DB and vehicle tables. The Alerts runner is a distinct, minimal client.
