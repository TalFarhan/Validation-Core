# Implementation Plan: Credit Consumption UI Sanity Validation

**Branch**: `feature/reportportal-integration` (spec directory `046-credit-ui-validation`) | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/046-credit-ui-validation/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The sibling slices `044-credit-consumption-sanity` and
`045-hour-chart-table-teardown` stay as their own pins and are NOT edited by this slice.

## Summary

Tighten the existing Credit Consumption sanity suite so the live UI is compared to
`data/credit/db_sanity_purim2026.yaml` (`credit_consumption_dashboard`) as a subset match.

Feature 044 already added `CreditConsumptionPage` and
`tests/sanity/credit_consumption_dashboard/test_data_validation.py`. This slice expands those
files. It does not rebuild the page, the fixture, or the suite, and it does not query SQL.

1. **Filters** — Screen 1 calls the existing `apply_filters` with `active_filters` before any
   read. Screen 2 calls `open_export_page()` and then `apply_filters` with `top_bar` merged into
   `side_bar`. `הכל` stays the default. The period string is read from the YAML only.
2. **Identity** — The visible Screen 1 title equals `dashboard_info.title`. The visible Screen 2
   title equals `screen_2_data_export.title`. `dashboard_info.last_updated` is matched against
   the inherited `_last_refresh_caption_text()` as `DD/MM/YYYY HH:MM`. No second date parser.
3. **Subset asserts** — Every golden key and row must exist and be equal. Extra UI keys and rows
   are ignored. `_assert_nested` covers KPIs (percent strings stay strings). Row compares use
   `date` (trends and alerts), `authority`, and `(transaction_date, authority_name, sub_category)`.
   Trend keys split with `rsplit("_", 1)`. `transactions_count_bar` values stay a list. `day` stays
   a string. Export `quantity` stays an int and `amount` stays a comma-formatted string.
4. **Fail vs skip** — A rendered visual whose reader returns empty while the golden block has
   data fails. `pytest.skip` runs only when that visual's existing title or grid is absent.
   The current helpers skip on any empty read; that skip is removed.
5. **Messages** — Each assertion names the JSON path, the UI value, and the golden value.

Chart numbers still come from the credit page's Show as a table helpers. Alerts Analysis code is
not copied. `verify_freshness` on the credit smoke test is left unchanged.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through the existing
`credit_consumption_dashboard` fixture. Layer 2 `KPI` and `Slicer` stay as composed by the
page. No new package.

**Storage**: Golden record `data/credit/db_sanity_purim2026.yaml` (unchanged). No warehouse
query and no `db/clients/credit.py`.

**Testing**: `pytest tests/sanity/credit_consumption_dashboard/test_data_validation.py -m sanity`.
Credit smoke `pytest tests/ui/credit_consumption_dashboard/` is the navigation and freshness gate
(`verify_freshness` must stay green). Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet
page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework. Domain page under `pages/credit_consumption/`.
Sanity tests under `tests/sanity/credit_consumption_dashboard/`.

**Performance Goals**: N/A. One catalog open per test, the same toggle and table reads feature 044
already performs, plus a title check and one last-refresh caption read on Screen 1.

**Constraints**:

- Expand `credit_consumption_page.py` and `test_data_validation.py`. Do not rewrite them (FR-014).
- Do not edit `core/portal/` or `core/components/` (Constitution II, VII, FR-015).
- Do not edit alerts, status-picture, or fleet pages or their tests (FR-015).
- Do not edit `db/`, the root `conftest.py`, or any YAML file (FR-015).
- Do not hardcode the period name. `הכל` is not re-selected (FR-001).
- Do not add a date parser. Last-updated uses `_last_refresh_caption_text` (FR-004).
- Do not parse SVGs or tooltips, and do not copy `pages/alerts_analysis/` (FR-013).
- Empty UI data against a non-empty golden block fails. Skip only when the visual is not
  rendered (FR-011).
- Assertion text includes JSON path, UI actual, and golden expected (FR-012).
- `quantity` is an int. `amount` keeps commas. Percent KPIs and `day` stay strings.
  `transactions_count_bar` values stay a list (FR-005, FR-006, FR-009).
- Inline comments in new or edited functions stay English. Missing Hebrew labels are copied
  from the live report (FR-014).
- `verify_freshness` is not overridden. The smoke test body stays `dashboard.verify_freshness()`
  (FR-016).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/credit_consumption/credit_consumption_page.py` | EDIT | Title visibility, visual-rendered checks, keep list/int/string shapes |
| `tests/sanity/credit_consumption_dashboard/test_data_validation.py` | EDIT | Subset asserts, fail-on-empty, JSON-path messages, title and last-updated |
| `tests/sanity/credit_consumption_dashboard/conftest.py` | UNCHANGED | Existing fixture |
| `tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py` | UNCHANGED | `verify_freshness` stays |
| `data/credit/db_sanity_purim2026.yaml` | UNCHANGED | Source of truth |
| `docs/COVERAGE_CATALOG.md` | EDIT | Add title and last-updated rows |
| `core/`, `db/`, alerts, status-picture, fleet, root `conftest.py` | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `CreditConsumptionPage` already subclasses `ReportShell`. Login,
  catalog search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0. This slice
  calls `_last_refresh_caption_text` and does not re-implement it. Screen 2 still uses
  `open_export_page`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Titles, chart names, and slicer role names
  stay on the domain page. `core/` is not edited. Root `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Smoke `verify_freshness` and
  popup dismiss stay. New sanity asserts are additive. Fleet smoke is not the gate because Layer 0,
  Layer 2, and the fleet page are not edited. Credit smoke is the gate for this page's freshness
  surface.
- **Page object discipline (IV)**: PASS. Tests call page methods (`apply_filters`, readers,
  `open_export_page`, title and rendered checks). No new iframe locators in test bodies.
- **Warehouse as source of truth (V)**: PASS with a recorded deviation. Assertions compare the UI
  to `data/credit/db_sanity_purim2026.yaml`, not a live SQL query. The user forbade SQL and
  `db/clients/credit.py`. Layer 0 still has no business SQL. Same justification as 044/035/039.
- **Observability (VI)**: PASS. Existing screenshot, trace, HTML, and CSV hooks apply to the sanity
  module. No logging path is removed. The coverage catalog gains the title and last-updated rows.
- **Extract shared behavior only (VII)**: PASS. No new Layer 2 API. Show as a table stays on the
  credit page. The last-refresh reader stays the Layer 0 method that already exists. No alerts
  helper is imported.

**Result**: No unjustified violations. Principle V deviation is recorded in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/046-credit-ui-validation/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── credit-ui-validation.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
pages/credit_consumption/
├── page.py                            # UNCHANGED re-export
└── credit_consumption_page.py         # EDIT: title + rendered checks; keep readers
      ├── apply_filters(active_filters)          # skip הכל
      ├── open_export_page()                     # existing page rail
      ├── title_is_visible(title)                # existing iframe phrase
      ├── visual_is_rendered(title)              # existing chart title
      ├── export_grid_is_rendered()              # existing grid/table role
      ├── read_kpi_metrics() / _assert_nested
      ├── set_metric() / set_visualization()
      ├── read_daily_trends()                    # show-as-table; values stays a list
      ├── read_daily_alerts()                    # key: date
      ├── read_expenses_by_authority()           # key: authority
      └── read_export_table()                    # quantity int, amount string

data/credit/db_sanity_purim2026.yaml   # UNCHANGED

tests/ui/credit_consumption_dashboard/
└── test_dashboard_smoke.py            # UNCHANGED verify_freshness

tests/sanity/credit_consumption_dashboard/
├── conftest.py                        # UNCHANGED
└── test_data_validation.py            # EDIT comparison rules

docs/COVERAGE_CATALOG.md               # title + last_updated rows
core/  db/  alerts  status-picture  fleet   # UNCHANGED
```

**Structure Decision**: Validation Core layout. One existing domain page and one existing sanity
module. No new package, no `db/clients/credit.py`, and no `core/` change.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: tests compare the Credit Consumption report to `data/credit/db_sanity_purim2026.yaml` instead of a live warehouse query | The user named that golden file as the only baseline and forbade SQL and `db/clients/credit.py`. The numbers are a snapshot under the YAML `active_filters`. | A credit SQL client would ignore the file and fail whenever the warehouse moves past the snapshot. Feature 044 already recorded this deviation; this slice keeps it. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- `CreditConsumptionPage` still inherits `ReportShell`. `_last_refresh_caption_text` and
  `verify_freshness` stay in Layer 0. The credit page does not gain a date parser.
- Title and rendered checks use the page's existing iframe phrase, chart title, and grid/table
  locators. Tests do not grow locators.
- Show as a table stays `_show_as_table_rows` on the credit page. Alerts Analysis is not imported
  and `core/components/` is not extended.
- Sanity tests keep the local fixture. Root `conftest.py` is untouched.
- Alerts, status-picture, fleet, `db/`, and the golden YAML are absent from the edit list.
- Empty parsed data fails when the golden block is non-empty. Skip is limited to a visual whose
  existing title or grid is absent.
- Credit smoke remains the freshness gate. Fleet smoke is not required.

**Result**: No unjustified violations.
