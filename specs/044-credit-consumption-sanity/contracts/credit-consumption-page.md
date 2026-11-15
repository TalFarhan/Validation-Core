# Contract: Credit Consumption Page and Sanity Suite

**Feature**: `044-credit-consumption-sanity` | **Date**: 2026-11-02

Alerts, status-picture, fleet, `core/`, and the golden metric values stay unchanged. Root
`conftest.py` stays.

## Page

`pages/credit_consumption/credit_consumption_page.py`

Class `CreditConsumptionPage` inherits `ReportShell`.

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `"צריכת אשראי"` |
| `_report_ready_locator()` | iframe phrase `"ממוצע הוצאות לקנייה בשגרה"` (Screen 1) |
| Popup | existing info-overlay dismiss (`דף מידע` / `מושגים חשובים`); no-op if absent |
| Freshness | inherited `verify_freshness` — no override |
| Screen 2 title | `"צריכת אשראי - ייצוא נתונים"` |

`pages/credit_consumption/page.py` re-exports:

```python
from pages.credit_consumption.credit_consumption_page import CreditConsumptionPage
```

Do not add `pages/credit_consumption/__init__.py`.

Smoke conftest keeps:

```python
from pages.credit_consumption.page import CreditConsumptionPage
dashboard = bind_dashboard(CreditConsumptionPage)
```

## Bilingual locators

### Page-rail (`open_export_page` / Screen 2 switch)

Playwright `.or_()` over `ניווט בין עמודים` and `Page navigation` on `get_by_role("link"|"button")`
and `get_by_label(..., exact=False)`, matching the Alerts Analysis 043 pattern. After the click,
wait for the Screen 2 title.

### Date fields

When present, fill `input[aria-label^='תאריך התחלה']`.or_(`input[aria-label^='Start date']`) and
the end-date pair (`תאריך סיום` / `End date`).

### Show as a table

Right-click the visual container, then click menuitem `הצג כטבלה` or `Show as a table`. Leave the
table after the read. Implemented on this page; do not import alerts helpers.

## Methods (additive)

### `apply_filters(self, filters: dict) -> None`

Apply a YAML `active_filters` map (Screen 1 flat, or a merged Screen 2 `top_bar` + `side_bar`).
Skip values equal to `הכל`. Dropdown ids match YAML keys; `role_name` constants are live-copied.
Settle on the current screen's ready phrase.

### `read_kpi_metrics(self) -> dict`

Return the nested `kpi_metrics` shape via Layer 2 `KPI`. Percent cards remain strings with `%`.
Omit a title that is not visible rather than raising for a single missing card (the test skip
guard names the missing key).

### `set_metric(self, kind: str) -> None`

`kind` is `"expense_amount"` or `"transactions_count"`. Click the live-copied toggle. Record
`_active_metric` after selection.

### `set_visualization(self, kind: str) -> None`

`kind` is `"line"` or `"bar"`. Record `_active_visualization` after selection.

### `read_daily_trends(self) -> list[dict]`

Show-as-a-table on the active trends visual. Return rows `{date, day, value}` or
`{date, day, values}` according to the active YAML key. Return `[]` when the table cannot be
read.

### `read_expenses_by_authority(self) -> list[dict]`

Show-as-a-table on the authority visual. Return `[{authority, amount}, ...]`. `[]` if unread.

### `read_daily_alerts(self) -> list[dict]`

Optional. Return `[{date, day, alerts_count}, ...]` or `[]`.

### `open_export_page(self) -> None`

Bilingual page-rail click. Wait for Screen 2 title. Subsequent ready checks use that title.

### `read_export_table(self) -> list[dict]`

Read the visible `grid` / `table`. Map headers to `export_table_data` keys. Amount stays a
thousands-separated string. Return `[]` if unread.

## Fixture

`tests/sanity/credit_consumption_dashboard/conftest.py`:

```text
credit_consumption_dashboard = bind_dashboard(
    CreditConsumptionPage, "credit_consumption_dashboard"
)
```

Setup helper (in the test module or conftest) loads
`data/credit/db_sanity_purim2026.yaml` as UTF-8 and applies the screen's `active_filters`
before assertions.

`tests/conftest.py` does not import the page.

## Tests

All `@pytest.mark.sanity`. Comments inside functions are English. Values come from the golden
file, not literals in the assertion source (except skip messages). Extra UI rows/keys are
ignored; every golden key/row must match.

| Test | Setup | Assert |
|------|--------|--------|
| `test_kpi_metrics_match_golden` | Screen 1 `active_filters` | `read_kpi_metrics()` vs `kpi_metrics` |
| `test_daily_trends_match_golden` | Screen 1 filters; each of the four toggle pairs | `read_daily_trends()` vs `daily_trends_by_toggle[key]` |
| `test_expenses_by_authority_match_golden` | Screen 1 filters | authority list vs `expenses_by_authority_millions` |
| `test_daily_alerts_match_golden` | Screen 1 filters | skip if empty; else vs `daily_alerts` |
| `test_export_table_match_golden` | `open_export_page` + Screen 2 `active_filters` | `read_export_table()` vs `export_table_data` |

Empty-read skip form: `pytest.skip("... returned no rows (chart empty or not rendered)")`.
Guards fire only when the visual is genuinely absent.

## Unchanged

- `data/credit/db_sanity_purim2026.yaml` metric values
- `tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py` body
- `pages/alerts_analysis/**`, `pages/status_picture/**`, `pages/fleet_dashboard/**`
- `tests/**/alerts_analysis_dashboard/**`, `tests/**/status_picture_dashboard/**`, `tests/**/fleet_dashboard/**`
- `core/portal/**`, `core/components/**`
- `tests/conftest.py`
- `db/**`

## Leakage

`core/**` MUST match none of:

```text
צריכת אשראי|ממוצע הוצאות לקנייה בשגרה|תמ״צ צריכת אשראי|פורים 2026
```

## Observability

Sanity tests use `@pytest.mark.sanity`. Failure screenshot and Playwright trace behavior in root
`conftest` is unchanged.
