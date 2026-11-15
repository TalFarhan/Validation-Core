# Implementation Plan: Credit Consumption Dashboard UI Sanity

**Branch**: `feature/reportportal-integration` (spec directory `044-credit-consumption-sanity`) | **Date**: 2026-11-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/044-credit-consumption-sanity/spec.md`

**Note**: This plan is filled by `/speckit-plan`. The formal `tasks.md` is produced by `/speckit-tasks`.
`.specify/feature.json` is repointed to this directory. Planning does not switch the git checkout
(`feature/reportportal-integration`). The sibling alerts slice `043-alerts-analysis-fixes` stays as its own
pin and is NOT touched by this slice.

## Summary

Add Screen 1 (Summary) and Screen 2 (Data Export) readers to the Credit Consumption report and a
sanity suite that asserts them against `data/credit/db_sanity_purim2026.yaml`.

The report already has a Layer 0 binding (`CreditConsumptionPage`: catalog term `צריכת אשראי`, ready
visual `ממוצע הוצאות לקנייה בשגרה`, info-overlay dismiss). This slice moves the class to
`pages/credit_consumption/credit_consumption_page.py` with a re-export at `page.py`, then adds:

1. **Bilingual locators** — page-rail (`.or_()` over `ניווט בין עמודים` / `Page navigation`) and date
   fields (`תאריך התחלה` / `Start date`, `תאריך סיום` / `End date`) so Screen 2 and date entry do not
   raise `LoadTimeoutError` when Power BI renders English chrome.
2. **Golden filters** — the sanity fixture reads `active_filters` and applies non-`הכל` values
   (`time_range` / `period` = `פורים 2026`) through composed Layer 2 `Slicer` plus domain date fields.
3. **KPI cards** — `read_kpi_metrics()` returns the nested `kpi_metrics` shape via Layer 2 `KPI`.
4. **Daily trends** — metric and visualization toggles; extraction is Right-click → bilingual
   Show as a table, mapped to the four `daily_trends_by_toggle` keys (including list-shaped
   `values` on `transactions_count_bar`).
5. **Authority chart and export matrix** — Show-as-a-table for `expenses_by_authority_millions`;
   accessible grid/table for Screen 2 `export_table_data`.

No alerts, status-picture, fleet, or `core/` edit. Golden metric values stay. In-function comments
are English.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: `pytest`, `PyYAML`, Playwright through `bind_dashboard`. Layer 2 `KPI`,
`Slicer` (and `Chart` only as a non-assertion helper). No new package.

**Storage**: Golden record `data/credit/db_sanity_purim2026.yaml` (metric values unchanged). No
warehouse query and no `db/clients/credit.py` in this slice.

**Testing**: `pytest -m sanity` on `tests/sanity/credit_consumption_dashboard/test_data_validation.py`.
Credit smoke `pytest tests/ui/credit_consumption_dashboard/` is the navigation-surface gate.
Fleet smoke is not a gate: Layer 0, Layer 2, and the fleet page are not edited.

**Target Platform**: Windows workstation; Chromium against the organizational Agamim Power BI portal.

**Project Type**: Internal validation framework. Domain page under `pages/credit_consumption/`.
Golden YAML under `data/credit/`. Sanity tests under `tests/sanity/credit_consumption_dashboard/`.

**Performance Goals**: N/A. One catalog open, one period select, four toggle+table reads, one
export-page switch per full module run.

**Constraints**:

- Do not edit `core/portal` or `core/components` (Constitution II, VII, FR-012).
- Do not edit alerts, status-picture, or fleet modules (FR-012).
- Do not add a `SlicerKind` for toggles or between-dates (VII).
- Hebrew titles, toggle names, slicer role names, and export headers that are not already in the
  YAML or the Layer 0 page are copied from the live report (FR-016).
- Show-as-a-table stays on the credit domain page (do not import alerts helpers; do not add a
  Layer 2 API this slice).
- Golden metric values MUST NOT change (FR-013).
- Inline comments in new/edited functions MUST be English (FR-014).
- Public smoke APIs (`navigate`, `verify_freshness`, popup dismiss, `DASHBOARD_SEARCH_TERM`) stay
  (AC-004, FR-015).
- Root `conftest.py` MUST NOT import this page (II).

**Scale/Scope**:

| Path | Change | Purpose |
|------|--------|---------|
| `pages/credit_consumption/credit_consumption_page.py` | NEW (move+extend) | Screen 1/2 page object |
| `pages/credit_consumption/page.py` | EDIT | Re-export `CreditConsumptionPage` |
| `tests/ui/credit_consumption_dashboard/conftest.py` | UNCHANGED import | Smoke still binds the class |
| `tests/sanity/credit_consumption_dashboard/__init__.py` | NEW | Package marker |
| `tests/sanity/credit_consumption_dashboard/conftest.py` | NEW | `credit_consumption_dashboard` fixture |
| `tests/sanity/credit_consumption_dashboard/test_data_validation.py` | NEW | Golden assertions |
| `data/credit/db_sanity_purim2026.yaml` | UNCHANGED values | Source of truth |
| `docs/COVERAGE_CATALOG.md` | EDIT | Credit YAML ↔ page-method rows |
| `core/` | NONE | No layer change |
| alerts / status-picture / fleet | NONE | Off-limits |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal (I)**: PASS. `CreditConsumptionPage` already subclasses `ReportShell`. Login,
  catalog search, iframe wait, visual-load timeout, and last-refresh stay in Layer 0. Ready
  locator stays on the domain page. Screen 2 switch is domain `before_report_ready_check` /
  `open_export_page`.
- **Zero domain leakage (II, NON-NEGOTIABLE)**: PASS. Catalog term, KPI titles, toggle names,
  slicer role names, and Show-as-a-table labels live on the domain page. `core/` is not edited.
  Root `conftest.py` does not import the page.
- **Existing tests are the contract (III, NON-NEGOTIABLE)**: PASS. Additive methods. Smoke
  `verify_freshness` and popup dismiss stay. Fleet smoke is not the gate because Layer 0, Layer 2,
  and the fleet page are not edited. Credit smoke is the gate for this page's navigation surface.
- **Page object discipline (IV)**: PASS. Sanity tests call page methods and a filter-setup helper.
  No iframe locators in test bodies.
- **Warehouse as source of truth (V)**: PASS with a recorded deviation. Assertions compare the UI
  to `data/credit/db_sanity_purim2026.yaml`, not a live SQL query. Same justification as 035/039.
  Layer 0 still has no business SQL. Catalog rows document the YAML mapping.
- **Observability (VI)**: PASS. Existing screenshot / trace / HTML / CSV hooks apply to the new
  sanity module. No logging path is removed.
- **Extract shared behavior only (VII)**: PASS. Compose `Slicer` and `KPI`. Toggles, date fields,
  Show-as-a-table, and the export grid stay on the domain page. No new `SlicerKind`. Show-as-a-table
  is not lifted into Layer 2 because alerts cannot be migrated in this slice and a fleet-unused
  core API would be premature.

**Result**: No unjustified violations. Principle V deviation is recorded in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/044-credit-consumption-sanity/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── credit-consumption-page.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
pages/credit_consumption/
├── page.py                            # re-export CreditConsumptionPage
└── credit_consumption_page.py         # ReportShell subclass: popup, Screen 1/2
      ├── DASHBOARD_SEARCH_TERM        # "צריכת אשראי"
      ├── before_report_ready_check    # dismiss info overlay
      ├── open_export_page()           # bilingual page-rail
      ├── apply_filters(active_filters)
      ├── read_kpi_metrics()
      ├── set_metric() / set_visualization()
      ├── read_daily_trends()          # show-as-table
      ├── read_expenses_by_authority() # show-as-table
      ├── read_daily_alerts()          # optional
      └── read_export_table()

data/credit/db_sanity_purim2026.yaml   # UNCHANGED values

tests/ui/credit_consumption_dashboard/
├── conftest.py                        # UNCHANGED import path
└── test_dashboard_smoke.py            # UNCHANGED freshness smoke

tests/sanity/credit_consumption_dashboard/
├── __init__.py
├── conftest.py                        # credit_consumption_dashboard fixture
└── test_data_validation.py            # golden KPIs, trends, authority, export

docs/COVERAGE_CATALOG.md               # credit section
core/                                  # UNCHANGED
```

**Structure Decision**: Validation Core layout. One domain page under `pages/credit_consumption/`.
Sanity package mirrors alerts/status-picture. Golden YAML already lives in `data/credit/`. No
`db/clients/credit.py` and no `core/` change.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle V: tests compare the Credit Consumption report to `data/credit/db_sanity_purim2026.yaml` instead of a live warehouse query | The user named that golden file as the baseline for KPIs, toggle trends, authority amounts, and the export matrix. The numbers are a Purim 2026 snapshot. | Adding `db/clients/credit.py` would ignore the file and fail whenever the warehouse moves past the snapshot. No credit SQL client exists yet. |

## Constitution Check (Post-Design)

Re-evaluated after Phase 0/1. Still PASS on I–VII, with the same justified Principle V deviation:

- `CreditConsumptionPage` inherits `ReportShell`. Popup dismiss, search term, and ready visual stay.
- Bilingual `.or_()` locators and Show-as-a-table live on the domain page, not in `core/`.
- `Slicer` / `KPI` are composed with opaque titles supplied by the page.
- Sanity tests import a local fixture; root `conftest.py` is untouched.
- Alerts, status-picture, fleet, and `core/` are absent from the edit list.
- Golden metric values are not changed.
- Show-as-a-table is not extracted to Layer 2 in this slice (alerts off-limits; no unused core API).
- Credit smoke remains the navigation-surface gate; fleet smoke is not required.

**Result**: No unjustified violations.
