# Phase 0 Research: Fleet DB Sanity and Validation Tests

**Feature**: 039-fleet-db-sanity | **Date**: 2026-10-29

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Pin a new spec directory

**Decision**: Plan this work as `specs/039-fleet-db-sanity`. `.specify/feature.json` now points there. The git checkout stays `feature/reportportal-integration`.

**Rationale**: The previous pin was `specs/038-population-page-refactor`, which already has a plan for the population page refactor. Writing this fleet sanity slice into that directory would replace an unrelated plan. Spec numbering in this repo is sequential, and `039` is the next free prefix.

**Alternatives considered**:

- *Fill `038-population-page-refactor/plan.md` again*: rejected. That spec is the population page refactor, not the fleet golden file.

## Decision 2 — Repair the golden file, then parse it with `yaml.safe_load`

**Decision**: Delete the trailing `[cite: 1]` from each `vehicle_categories[].rate` so the value is a quoted percent (`"0.57%"` and the three siblings). Load the file with `yaml.safe_load` and UTF-8. The checker still parses a rate by taking the leading `N.NN%` token, so a future citation suffix on an otherwise quoted string is ignored rather than compared.

**Rationale**: `yaml.safe_load` on the current file raises `ParserError` at `rate: "0.57%"[cite: 1]` (`expected <block end>, but found '['`). The alerts sanity loader uses `yaml.safe_load`. The percents already match `actual / standard` to two decimal places, so the repair does not change a business number.

**Alternatives considered**:

- *A custom parser that accepts the broken lines*: rejected. The file would stay invalid YAML and the next editor would hit the same error.
- *Rewrite rates as floats*: rejected. The file publishes a percent string. The check compares that string's numeric value to the computed rate.

## Decision 3 — Pure checker beside the tests, not in `tests/helpers/` or `core/`

**Decision**: `tests/sanity/fleet_dashboard/contract.py` loads the file and runs summary, breakdown, rate, and ledger checks. It does not import Playwright, the page, or `db.clients`. `test_db_sanity.py` calls that checker and, in the UI tests, binds results to the fleet page.

**Rationale**: Constitution VII says fleet validation helpers live with the fleet suite, not in `tests/helpers/`. Constitution II says `core/` must not load `data/fleet/` or contain vehicle labels. The alerts sanity module keeps its loader next to its tests. Splitting the pure checks into `contract.py` lets the structural tests run without a browser while the UI tests share one loader.

**Alternatives considered**:

- *One module, as in the population sanity file*: rejected for this slice. The user asked for validation logic that stays generic and separate from the page session. A pure module is that boundary.
- *A new engine under `tests/helpers/`*: rejected. That package is reserved for the parity engine and the dashboard opener.

## Decision 4 — Map the four summary keys onto the four existing KPI roles

**Decision**:

| Golden key | `get_kpi_value` role | Card title |
|------------|----------------------|------------|
| `total_vehicles_received` | `total` | `סה"כ רכבים שנקלטו` |
| `total_vehicles_in_use` | `in_use` | `סה"כ רכבים בשימוש` |
| `vehicles_credited` | `withdrawn` | `רכבים שזוכו` |
| `vehicles_transferred` | `allocated` | `רכבים שווסתו` |

The binding table lives in the test module. The pure checker only sees the golden keys.

**Rationale**: The page already exposes exactly these four cards (`MainDashboardPage._KPI_TITLES`). The golden file has exactly four summary counters. The coverage catalog names the fourth card `allocated` and stores it in `FACT.VehicleFlow`. The golden key for that card is `vehicles_transferred`. This slice does not rename the page role.

**Alternatives considered**:

- *Add a new KPI role named `transferred`*: rejected. FR-012 forbids editing the page, and the card already exists as `allocated`.
- *Leave `vehicles_transferred` unchecked on the UI*: rejected. The user asked for transferred vehicles to be part of the baseline.

## Decision 5 — Which identities are real

**Decision**: Assert only these identities. Values below are what the current file satisfies; the tests read the file rather than these literals.

| Rule | Current file |
|------|----------------|
| Sum of `units_breakdown` = `total_vehicles_in_use` | 358 |
| Sum of `pull_source_breakdown` = `total_vehicles_in_use` | 358 |
| Sum of `vehicle_categories[].actual` = `total_vehicles_received` | 363 |
| Sum of `credit_reasons_summary` = `vehicles_credited` | 6 |
| Length of `credited_vehicles_details` = `vehicles_credited` | 6 |
| Reason counts on the ledger = `credit_reasons_summary` | `אחר` 3, `פקודת רידוד פיקודית` 3 |
| `total_vehicles_in_use` ≤ `total_vehicles_received` | 358 ≤ 363 |
| Each rate = `actual / standard`, half-up to two decimals, with a `%` | `3/525 → 0.57%`, `11/65 → 16.92%`, `139/406 → 34.24%`, `210/1955 → 10.74%` |

Do not assert `total_vehicles_received = in_use + credited + transferred` (358 + 6 + 1 = 365, and 358 + 6 = 364; neither is 363). Do not sum anything to `vehicles_transferred`. Do not require a ledger pull source to be a key of `pull_source_breakdown` (the ledger contains `ליסינג יר"ם`, which is not an in-use slice). Do not require a ledger unit to be a key of `units_breakdown`.

**Rationale**: The coverage catalog already records that credited vehicles come from `FACT.SigningReturnVehicle` and transferred/allocated vehicles come from `FACT.VehicleFlow`, so they are not partitions of the received DIM count. The ledger's unit and source strings are row metadata, not the in-use chart grain.

**Alternatives considered**:

- *Assert received = in use + credited − transferred*: rejected. That equation is an arithmetic coincidence of this snapshot, not a rule the user stated.

## Decision 6 — UI reads use the page that already exists

**Decision**: After `reset_dashboard_filters()`:

- Summary: `get_kpi_value` for the four roles in Decision 4.
- Units: chart key `unit`. Pull source: chart key `source`. Credit reasons: chart key `withdrawal`. Category actuals: chart key `category`.
- For each golden name, if `get_chart_segment_labels` contains it, `hover_chart_segment` and `parse_tooltip_entries` supply the count. Comparison uses the normalized label.
- Ledger: `select_tab("withdrawn")`, then `search_vehicle` with the row's vehicle number, then `get_table_row_text` must contain the reason, the date, the pull source, the unit, and the subunit.

If a chart returns no labels that match the golden mapping, that test calls `pytest.skip` and names the chart. If at least one golden label is visible, a missing or different count fails.

**Rationale**: `dashboard_validation.py` already uses these chart keys. The coverage catalog says the category visual uses the staffing taxonomy (`אוטובוס`, `רכב קל`, …), which is the taxonomy in the golden file, and that the withdrawal pie sometimes shows a count without a name. A skip on a fully unreadable chart matches the alerts sanity pattern. A wrong visible count must still fail. Standards and rates are not read from the chart; they are file checks only.

**Alternatives considered**:

- *Add a page method that reads standards*: rejected. FR-012 forbids a page edit, and the file already stores standard and rate.
- *One UI test for every chart*: rejected. `pytest.skip` would hide a chart that already matched. One test per chart matches the Screen 2 sanity research.

## Decision 7 — Do not compare the golden snapshot to live SQL

**Decision**: This slice does not call `DatabaseClient`. `tests/e2e/` remains the UI-versus-warehouse suite.

**Rationale**: The user asked for checks against `db_sanity_all.yaml` and for logic that is not tied to an environment. `DatabaseClient` filters on `settings.DB_ENVIRONMENT`. A green warehouse on another day would fail a snapshot assertion, and a matching warehouse would not prove the file's internal rates and ledger fields.

**Alternatives considered**:

- *Assert KPI cards against both the file and `get_dashboard_kpis()`*: rejected. The file would stop being a stable baseline the moment the warehouse changed.

## Decision 8 — Import the existing fixture

**Decision**: UI tests import `dashboard` from `tests.ui.fleet_dashboard.conftest`. Structural tests do not use it. The UI conftest is not edited.

**Rationale**: Same pattern as `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`, which imports `population_dashboard`. Pytest applies the fixture object imported into the test module. Root `conftest.py` already provides `auth_page` and `browser_context`.

**Alternatives considered**:

- *A new `conftest.py` that calls `open_report` again*: rejected. That duplicates the fixture and risks a second navigation policy.

## Decision 9 — Normalize labels before compare

**Decision**: Before a UI string is compared to a golden string, replace `״` and `"` with `"`, strip, and collapse internal whitespace. The pure file checks compare keys to each other without this fold, because both sides come from the same document.

**Rationale**: The golden file and the page titles do not use one quotation mark for `מפקע"ר` and `יר"ם`. A quote-only difference is not a count drift. The failure message still prints both original strings.

**Alternatives considered**:

- *Exact string equality with the raw UI text*: rejected. A quotation-mark difference would fail a row whose counts are right.
- *Fuzzy matching*: rejected. A different unit name must still fail.
