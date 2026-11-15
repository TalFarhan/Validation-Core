# Contract: Hosen Status Screen 1 Sanity

**Feature**: `050-hosen-screen1-sanity` | **Date**: 2026-11-12

Hasbara, Credit, Alerts, fleet, and `core/` stay unchanged. Root `conftest.py` stays. The smoke
module stays a one-line freshness check.

## Page

`pages/hosen_status/page.py`

Class `HosenStatusPage` inherits `ReportShell`. Existing surface, unchanged:

| Rule | Value |
|------|--------|
| `DASHBOARD_SEARCH_TERM` | `תמ"צ חוסן` |
| `_report_ready_locator()` | iframe text `תמ"צ ארצי - דיווחי קה"א יקל"ר`, exact |
| `LAST_REFRESH_PHRASE` | `מועד רענון` |
| Freshness | inherited `verify_freshness()` |

Smoke conftest keeps:

```python
from pages.hosen_status.page import HosenStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

dashboard = bind_dashboard(HosenStatusPage)
```

## Method (additive)

### `read_screen_1_metrics(self) -> dict`

Reads the landing screen after `navigate()` has already waited for the ready locator. Returns
the four keys in [data-model.md](../data-model.md): `survey_status`, `kpis`,
`resilience_scores`, `active_filters`.

Waits use `expect(...).to_be_visible(timeout=self.timeout)` on each section anchor. The method
does not call `sleep`, `wait_for_timeout`, or a network-idle wait. It does not read a canvas
bitmap.

#### Filters

- Build `Slicer` with page-local `SlicerDefinition` rows (`id`, Hebrew `role_name`, `kind="dropdown"`).
- For each id that the YAML may name, read `self._slicer.control(id)` once it is visible.
- Return the selected label. The role name is not part of the returned string.
- Do not call `select`, `apply`, or `clear_all`.

#### KPIs

- Construct `KPI` with the report page and the report iframe.
- National card title constant starts as `הערכת קה״א - ממוצע ארצי`. Replace the quote character
  with the live accessible name if the DOM uses `"` instead of `״`.
- `percentage` is the card's display percentage, including `%`.
- `trend` is `up`, `down`, or `flat`, from a non-canvas node inside `KPI.card(title)`.
- `kpis.categories` lists every other card in that visual. Each item has `title`, `percentage`,
  and `trend`.

#### Resilience table

- Anchor text: `ציון חוסן`.
- Call `collect_virtualized_rows(grid, read_visible, row_id, timeout_ms=self.timeout)`.
- `read_visible` returns rows with `authority`, `score`, and `status`.
- `row_id` returns `authority`.
- `status` is `green`, `yellow`, or the raw `rgb(...)` when the computed background is neither.

#### Survey status

- Locators live on this page.
- `submitted` and `total` are the digit strings from the top-left block (a `7` out of `12`
  shape, whatever separator the live text uses).
- `missing_authorities` is the list of names in that block.

## Sanity module

`tests/sanity/hosen_status_dashboard/conftest.py`

```python
from pages.hosen_status.page import HosenStatusPage
from tests.helpers.dashboard_fixture import bind_dashboard

hosen_status_dashboard = bind_dashboard(HosenStatusPage, "hosen_status_dashboard")
```

`tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`

| Rule | Behavior |
|------|----------|
| Fixture | `hosen_status_dashboard` |
| Entry | `test_hosen_screen1_matches_golden` |
| Golden path | `data/hosen/db_sanity.yaml` → `hosen_dashboard` → `screen_1_landing` |
| Call | `read_screen_1_metrics()` once |
| Subset | Every golden key matches. Extra UI rows, categories, names, and slicers do not fail |
| Integers | YAML `1324` matches UI `1,324` and `1324` |
| Strings | Exact match after bidi marks and outer whitespace are removed |
| Empty reader | Fail when the anchor is visible and the golden block has data |
| Missing anchor | `pytest.skip` that block only |
| Helpers | Private functions in this module. No import from Hasbara, Credit, or Alerts. No new file under `tests/helpers/` |

## Out of scope

- `core/portal/`, `core/components/`
- `data/hasbara/`, `data/credit/`, `data/alerts/`
- Pages and tests of those three reports
- `db/clients/`
- Editing `test_dashboard_updated_within_24_hours`
- A second Hosen screen or a tab click
