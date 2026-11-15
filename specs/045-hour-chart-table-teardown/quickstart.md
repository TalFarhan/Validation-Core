# Quickstart: YAML-Only UI Blockers

## What this slice does

Keeps UI-to-YAML sanity and ignores direct SQL for the alerts dashboard. Fixes two Playwright
blocks on the population page: the district drill-down click, and the hour-chart title that
Playwright treats as invisible.

- `test_alerts_db_parity_last_30_days` is skipped with reason
  `Focusing strictly on YAML validation; DB checks temporarily disabled`. That is the smoke-path
  test that runs `[FACT].[AlertsRedWeb]` through `alerts_db` and `alerts_contract.yaml`.
- The YAML module is not skipped. It still loads `data/alerts/db_sanity_am_kalavi.yaml`.
- `set_hierarchy_level` clicks `נפה`, `רשות`, and `יישוב` with `click(force=True)` so the
  visual header toolbar does not intercept the pointer.
- For `HOUR_CHART` only (`גרף התרעות וגם ממוצע לפי שעה`), `_title_anchor` and the post-back
  wait in `_leave_visual_table` do not use `.filter(visible=True)`. A hidden tooltip that is
  not inside a visual container is not the anchor. Other titles, and `מרחק מהגבול`, stay
  visible matches.

`core/` is not edited. Golden YAML is not edited. The SQL client and the alerts contract are
not edited.

## Prerequisites

- Portal auth configured (the YAML sanity tests open the live Power BI report).
- Python env with `pytest` and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by the existing alerts fixtures.
- A warehouse connection is not required for this slice. The parity test is skipped before
  `alerts_db` runs.

## Files you will touch

- `tests/ui/alerts_analysis_dashboard/test_db_parity.py`
  - Add `@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")`
    on `test_alerts_db_parity_last_30_days`.
  - Replace the in-function "Do not skip it" comment with an English comment that the skip is
    temporary and the SQL contract is unchanged.
- `tests/unit/test_db_parity_engine.py`
  - In `test_remaining_visuals_use_stub_sql`, `test_alerts_stubs_do_not_hide_connection_errors`,
    and `test_population_page_stubs`, remove only `assert "mark.skip" not in ...`.
  - Keep the `pytest.skip` and `importorskip` asserts.
- `pages/alerts_analysis/population_page.py`
  - `set_hierarchy_level`: `control.click(force=True)`, with an English comment about the
    visual header toolbar.
  - `_title_anchor`: for `HOUR_CHART`, fall back to attached text or group inside a visual
    container when no visible match exists.
  - `_leave_visual_table`: for `HOUR_CHART`, wait until the title is attached. Do not call
    `to_be_visible` for that title.

## Preserve

- `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` (no new skips).
- `data/alerts/db_sanity_am_kalavi.yaml` and `data/alerts/alerts_contract.yaml`.
- `db/clients/alerts.py` and the `alerts_db` fixture.
- `_report_ready_locator` and `_SCREEN2_READY_ANCHOR` (`מרחק מהגבול`, still visible).
- `before_report_ready_check` (Screen 2 tab click).
- `read_hour_daily_avg` (התרעות column only, after `ממוצע ליום`).
- `_assert_golden_keys` quote folding.
- `set_date_range` wait on `אוכלוסייה מותרעת`.
- Bilingual Back (`חזרה לדוח` / `Back to report`) inside `finally`.
- Visible-title behavior for every chart that is not `HOUR_CHART`.

## Do NOT touch

- YAML files under `data/`.
- `core/portal/` and `core/components/`.
- Fleet, status-picture, or credit modules.
- The root `conftest.py`.
- `set_district_aggregation`.
- `networkidle`.

## Run it

```powershell
# Unit scans: mark.skip is allowed; pytest.skip and importorskip stay banned
pytest tests/unit/test_db_parity_engine.py

# Alerts UI smoke: parity test is skipped; freshness and invariants still run
pytest tests/ui/alerts_analysis_dashboard/

# YAML sanity (needs portal auth). Hierarchy and hour-chart tests are the UI checks.
pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -m sanity
```

Fleet smoke is not a gate. `core/` and the fleet page are not edited.

Confirm the skip without a browser:

```powershell
pytest tests/ui/alerts_analysis_dashboard/test_db_parity.py --collect-only
```

The node is collected as skipped. It does not connect to SQL.

## Done when

- `test_alerts_db_parity_last_30_days` carries the exact skip reason above.
- The YAML sanity module has no new skip marks.
- `pytest tests/unit/test_db_parity_engine.py` passes, and the parity file still has no
  `pytest.skip` or `importorskip`.
- `set_hierarchy_level` uses `click(force=True)` for `נפה`, `רשות`, and `יישוב`.
- The hour-chart title can anchor a visual container when Playwright marks that title
  invisible, and the post-back wait for that title does not require visibility.
- `_report_ready_locator` still requires visible `מרחק מהגבול`.
- No YAML, SQL client, contract, `core/`, fleet, status-picture, or credit edit.
- In-function comments are English.
