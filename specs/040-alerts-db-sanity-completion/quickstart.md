# Quickstart: Complete Alerts DB Sanity Validations

## Scope

Close the remaining Alerts sanity gaps against `data/alerts/db_sanity_am_kalavi.yaml`:

- **Screen 2** (Alerts Analysis): add nafa / rashut / yeshuv **daily-average** tests.
- **Screen 1** (Status Picture): verify the **exact tie-slot names** instead of only the row count.
- Raise the Alerts page locator timeout so Power BI rendering is less likely to raise `LoadTimeoutError`.

Fleet modules, `core/`, and the golden YAML are not edited.

## Prerequisites

- Python 3.11+ with repo `requirements.txt` installed.
- Portal auth available for the UI tests (`auth_state.json`, per the existing Alerts suites).
- Windows shell is PowerShell; use `python -m pytest` (not `pwsh`).

## What changes

| File | Change |
|------|--------|
| `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` | Add `_assert_hierarchy_daily_avg` + three `*_daily_avg_matches_db` tests |
| `tests/sanity/status_picture_dashboard/test_status_picture_validation.py` | Tie slots checked by exact name (set equality) |
| `pages/alerts_analysis/population_page.py` | `self.timeout` 60000 → 120000 |
| `pages/status_picture/status_picture_page.py` | `self.timeout` 60000 → 120000 |

## Run the new and changed tests

```powershell
# Screen 2 daily averages (new)
python -m pytest tests/sanity/alerts_analysis_dashboard/test_data_validation.py -k daily_avg -m sanity -v

# Screen 1 tie-name check (edited)
python -m pytest tests/sanity/status_picture_dashboard/test_status_picture_validation.py::test_screen_1_top_settlements -m sanity -v

# Whole Alerts sanity set
python -m pytest tests/sanity/alerts_analysis_dashboard tests/sanity/status_picture_dashboard -m sanity -v
```

## Expected results

- Screen 2: `test_hierarchy_nafa_daily_avg_matches_db`, `..._rashut_...`, `..._yeshuv_...` pass when
  every golden `daily_avg` name reads `1` in average mode. They **skip** (not fail) if a level control
  is not visible or the reader returns nothing.
- Screen 1: `test_screen_1_top_settlements` passes when the six stable settlements match exactly and the
  four UI tie slots carry the four golden tie names (יגל, גינתון, צפרייה, חיפה) in any order, each at the
  tie count. It **fails** if a tie slot holds a non-golden settlement, and **skips** if the ranking reader
  returns an empty map.
- Timeouts: a cold Power BI load has a 120s budget before `LoadTimeoutError`; a never-rendering visual
  still raises `LoadTimeoutError`.

## Verification without the browser

```powershell
# Golden file still parses and holds the three daily_avg maps and the tie names
python -c "import yaml; d=yaml.safe_load(open('data/alerts/db_sanity_am_kalavi.yaml',encoding='utf-8')); s=d['dashboard_sanity_checks']; print(list(s['screen_2_alerts_analysis']['metrics']['alerts_by_hierarchy']['nafa']['daily_avg'])); print(s['screen_1_status_picture']['metrics']['top_10_settlements']['values'])"
```

## Guardrails

- Expected values come only from the YAML; no count or name is hard-coded in a test.
- No fleet module, `core/`, `db/clients/`, or the root `conftest.py` is edited.
- Comments inside new or edited functions are English only.
- Next step after this plan: run `/speckit-tasks` to generate `tasks.md`.
