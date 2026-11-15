# Contract: Alerts Analysis Navigation & Hierarchy Read Fixes

Page-object and test contract for resolving the Alerts Analysis `ERROR` (LoadTimeout) and `SKIPPED`
results. No `core/` contract changes. No fleet/status-picture change.

## Page object: `AlertsPopulationPage` (`pages/alerts_analysis/population_page.py`)

### `before_report_ready_check(self) -> None` — CHANGED (internal)

- **Signature**: unchanged.
- **Before**: page-rail switch located only by the Hebrew name `ניווט בין עמודים`. Screen-2 probe uses
  `self.DISTRICT_CHART`.
- **After**: the switch locator is a Playwright `.or_()` over `ניווט בין עמודים` and `Page navigation`
  across the existing `get_by_role("link"|"button")` / `get_by_label` strategies. The Screen-2 probe uses
  `self.district_chart_title()` (base level `התרעות לפי מחוז` at navigate time).
- **Guarantee**: Screen 2 opens whether Power BI renders Hebrew or English; no new portal step.

### `set_between_dates(self, start, end) -> None` — CHANGED (internal)

- **Signature / return type**: unchanged.
- **After**: `_fill_input` resolves through `input[aria-label^='תאריך התחלה']`.or_()
  `input[aria-label^='Start date']` and the end-date pair (`תאריך סיום` / `End date`); `_commit_field`
  sequence unchanged.
- **Guarantee**: both fields fill under Hebrew or English aria-labels.

### `district_chart_title_for(level: str) -> str` — NEW (staticmethod, additive)

- Returns `"התרעות לפי " + level_name` for `mahoz` / `nafa` / `rashut` / `yeshuv`.
- Base level (`mahoz`) returns `"התרעות לפי מחוז"`.
- Used by the unit test (no Playwright `Page`) and by the instance accessor.

### `district_chart_title(self, level: str | None = None) -> str` — NEW (additive)

- Returns `district_chart_title_for(level or self._active_hierarchy_level)`.
- Replaces the removed `DISTRICT_CHART` class constant as the district-chart anchor.

### `set_hierarchy_level(self, level: str) -> bool` — CHANGED (internal)

- **Signature / return type**: unchanged (`bool`).
- **After**:
  1. Resolve the level control inside the *current* `district_chart_title()` container.
  2. Click and wait for selected (`_wait_for_level_selection`).
  3. Wait until `district_chart_title_for(level)` is visible (the *new* title, not `התרעות לפי מחוז`).
  4. Record `_active_hierarchy_level = level` and return `True`.
- **Guarantee**: a successful drill-down returns `True`. A missing control or a title that never appears
  leaves `_active_hierarchy_level` unchanged and returns `False` (skip guard preserved).

### `read_district_labels(self) -> dict[str, int]` — CHANGED (internal)

- **Signature / return type**: unchanged.
- **After**: existing row/mark/tooltip paths first. If empty: Show-as-a-table fallback on
  `district_chart_title()` with header `התרעות`, else pair category `listbox` options with the `התרעות`
  series `listbox` options.
- **Guarantee**: returns district→count for a rendered listbox; returns `{}` only when the control is
  genuinely absent (guard preserved).

### `read_hour_buckets(self) -> dict[str, int]` — CHANGED (internal)

- **Signature / return type**: unchanged.
- **After**: existing SVG/category/tooltip paths first. If empty: Show-as-a-table on `HOUR_CHART` with
  header `התרעות` (hour tokens normalized to `HH:MM`), else listbox pairing.
- **Guarantee**: returns hour→count for a rendered listbox; `{}` only when genuinely absent.

### `read_hour_daily_avg(self) -> dict[str, int]` — CHANGED (internal)

- **Signature / return type**: unchanged.
- **After**: existing average-series paths first. If empty: Show-as-a-table on `HOUR_CHART` with a
  `ממוצע`-containing column header, else pair category listbox options with the average series listbox.
  Hour tokens normalized to `HH:MM`.
- **Guarantee**: `test_alerts_by_hour_daily_avg_matches_db` can reach its assertion when the visual
  renders as a listbox (FR-007). `{}` only when genuinely absent.

### Readers / helpers repointed to the accessor — INTERNAL

`before_report_ready_check`, `set_district_aggregation`, `_hierarchy_control`, `chart_total` (district
branch), `_district_visible_total`, and `_visual_container`'s exclusion list call `district_chart_title()`
instead of the removed constant. Names and return types are unchanged.

### Table helpers — INTERNAL, parameterized

- `_click_show_as_table`: keep bilingual menu items `הצג כטבלה` / `Show as a table`; error text names the
  calling visual.
- `_alert_column_table(header: str = "התרעות")`: find a visible grid/table whose named column has integers.
- `_leave_visual_table(title: str)`: click `חזרה לדוח`, then wait for `title` to be visible. Dates keep
  passing `DATES_CHART`. District/hour pass their live title.
- `_collect_scrolled_rows(..., key="header")` and `_visible_date_entry` are reused as-is (already generic
  rowheader + integer).

### Unchanged

`read_card`, `read_settlement_warned`, `read_date_counts` (signature; internally uses parameterized
helpers with `DATES_CHART`), `set_date_range`, `set_district_aggregation` (signature), `clear_filters`,
and the `AlertsAnalysisPage` / `ReportShell` composition.

## Removed public constant

- `AlertsPopulationPage.DISTRICT_CHART` is REMOVED. Its three references are updated in the same change:
  - `tests/ui/alerts_analysis_dashboard/test_population_invariants.py` → `population_dashboard.district_chart_title()`
    (both the Screen-2 probe and `chart_total(...)`).
  - `tests/ui/alerts_analysis_dashboard/population_snapshot.py` → `page.chart_total(page.district_chart_title())`.
  - `tests/unit/test_population_page.py` → assert
    `AlertsPopulationPage.district_chart_title_for("mahoz") == "התרעות לפי מחוז"`.

## Test package: `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` — AUDIT

- `test_hierarchy_mahoz_sum_matches_db`, `test_hierarchy_mahoz_daily_avg_matches_db`,
  `test_hierarchy_nafa_matches_db`, `test_hierarchy_rashut_matches_db`, `test_hierarchy_yeshuv_matches_db`,
  `test_hierarchy_nafa_daily_avg_matches_db`, `test_hierarchy_rashut_daily_avg_matches_db`,
  `test_hierarchy_yeshuv_daily_avg_matches_db`, `test_alerts_by_hour_sum_matches_db`, and
  `test_alerts_by_hour_daily_avg_matches_db` reach pass/fail instead of skip when data is present.
- The `pytest.skip` guards stay as a safety net; no golden value is read into a literal in a test body.

## Golden record contract

`data/alerts/db_sanity_am_kalavi.yaml` metric values are UNCHANGED. No alias, no count change.

## Invariants

- `core/portal`, `core/components`, and the root `conftest.py` are not edited.
- No fleet or status-picture module is edited.
- Public alerts reader names and return types are unchanged; the title accessor and listbox paths are
  additive; the only surface change is the removed constant, with its references updated in the same change.
- The alerts UI smoke suite (`tests/ui/alerts_analysis_dashboard/`) and `tests/unit/test_population_page.py`
  pass after the edit.
- Comments inside new or edited functions are English.
