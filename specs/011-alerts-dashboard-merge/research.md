# Phase 0 Research: Unify Alerts Dashboard Folders

All unknowns were resolved by reading the two existing suites, the parity engine, and the shared fixtures. No
external research required. Decisions below drive Phase 1.

## D1 — Which folder survives

- **Decision**: Keep `tests/ui/alerts_analysis_dashboard/`; delete `tests/ui/alerts_dashboard/`.
- **Rationale**: `alerts_analysis_dashboard` predates the parity pilot, matches the one-folder-per-report
  naming used by every other dashboard suite (`*_dashboard` with the report's descriptive name), and already
  owns the canonical page class `AlertsAnalysisPage`. The 010 plan itself documented that a separate
  `alerts_dashboard/` folder was only a "path-matching" compromise, not a convention.
- **Alternatives considered**: Keep `alerts_dashboard/` and move smoke into it — rejected because it renames
  the established suite and the page class, creating churn in `conftest.py` bindings and docs for no benefit.

## D2 — Page-object merge: inherit vs copy

- **Decision**: Fold the date-range `Slicer` wiring and `select_date_range()` from `AlertsDashboardPage`
  directly into `AlertsAnalysisPage` (single class). Do not keep two classes.
- **Rationale**: Both classes already subclass `ReportShell` with an identical `DASHBOARD_SEARCH_TERM`
  (`"ניתוח התרעות"`) and identical `_report_ready_locator()`. The only delta is the slicer composition and the
  `select_date_range` helper. Merging yields one page object that satisfies both the smoke test (freshness via
  `ReportShell.verify_freshness`) and the parity test (slicer + `_report_frame()` consumed by the engine).
- **Alternatives considered**: Subclass `AlertsAnalysisPage` → `AlertsParityPage` — rejected as needless
  indirection for a single report; violates "extract shared only" minimalism.

## D3 — Does `test_db_parity.py` need import edits after the move?

- **Decision**: No source-import edits are required in `test_db_parity.py`.
- **Rationale**: The test imports only `tests.helpers.db_parity_engine.validate_dashboard_generic` and computes
  `CONTRACT_PATH = Path(__file__).resolve().parent / "alerts_contract.yaml"` (relative to its own location, so
  it stays correct after the move). It does **not** import any page class — it receives the `dashboard` fixture
  from `conftest.py`. The "update imports to `AlertsAnalysisPage`" requirement is therefore satisfied by the
  **conftest** binding (`dashboard = bind_dashboard(AlertsAnalysisPage)`), which already exists in the analysis
  folder. We will still read the moved test and fix any stray reference if present.
- **Alternatives considered**: Add a redundant page import to the test — rejected; tests use fixtures, not
  direct page construction (Page Object Discipline).

## D4 — Fixture merge strategy for `alerts_db`

- **Decision**: Copy the `alerts_db` session-scoped fixture into
  `tests/ui/alerts_analysis_dashboard/conftest.py`, preserving the existing `dashboard` binding.
- **Rationale**: The analysis `conftest.py` already defines `dashboard = bind_dashboard(AlertsAnalysisPage)`.
  Adding `alerts_db` makes both fixtures available to every test in the folder; pytest discovers fixtures per
  package via `conftest.py`. No scope or import change beyond adding `AlertsDBRunner`.
- **Alternatives considered**: Session fixture in a higher conftest — rejected to keep the Alerts DB runner
  scoped to its own suite and avoid leaking it into unrelated dashboards.

## D5 — Live references to the deleted path

- **Decision**: Update the only **live** references — `docs/COVERAGE_CATALOG.md` — to point at
  `tests/ui/alerts_analysis_dashboard/...` and `AlertsAnalysisPage.select_date_range`.
- **Rationale**: A workspace grep shows live references to `alerts_dashboard` only in the folder being deleted
  (self-contained) and in `docs/COVERAGE_CATALOG.md`. The `specs/010-db-parity-engine/*` references are
  historical planning records of that feature and are intentionally left as-is (they describe what 010 did).
- **Alternatives considered**: Rewrite the 010 spec docs — rejected; editing a completed feature's historical
  artifacts would misrepresent the record.

## D6 — Acceptance signal in this environment

- **Decision**: Use `pytest --collect-only tests/ui/alerts_analysis_dashboard/` as the primary gate; full
  execution of the parity test is out of scope here (needs live portal auth + Alerts SQL Server).
- **Rationale**: This feature is structural. Clean collection of both the `sanity` smoke test and the
  `db_parity` test proves imports, fixtures, and markers resolve after the merge. Runtime parity is already
  covered by feature 010's acceptance.
