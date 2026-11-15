# Phase 0 Research: Status Picture Sanity Tests

**Feature**: 035-status-picture-sanity | **Date**: 2026-10-19

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Pin a new spec directory

**Decision**: Plan this work as `specs/035-status-picture-sanity`. `.specify/feature.json` now points there. The git checkout stays `feature/reportportal-integration`.

**Rationale**: `034-screen2-sanity-maps` is the Screen 2 slice. Screen 1 is a different page and a different golden block. Overwriting 034 would mix the two screens.

**Alternatives considered**:

- *Add Screen 1 tests to the Screen 2 module*: rejected. The user asked for a new page object and a new test module, and said not to modify the Screen 2 tests.

## Decision 2 — Stay on page 1 of `ניתוח התרעות`

**Decision**: `StatusPicturePage` inherits `AlertsAnalysisPage`. `DASHBOARD_SEARCH_TERM` stays `ניתוח התרעות`. The page does not click `ניווט בין עמודים`. The ready phrase is `אזורי התרעה תחת ירי`.

**Rationale**: The population page opens this same catalog product and then switches to page 2. The default report page is therefore page 1. The alerts contract places `אזורי התרעה תחת ירי` on that first page, before the page-2 metrics. A separate catalog product is not named in the golden file.

**Alternatives considered**:

- *Search the catalog for `תמונת מצב`*: rejected. That phrase in this repo is the power-outages product `תמונת מצב הפסקות חשמל`, which is a different report.
- *Subclass `AlertsPopulationPage`*: rejected. That class clicks through to page 2.

## Decision 3 — Register the fixture in the sanity package

**Decision**: `tests/sanity/status_picture_dashboard/conftest.py` calls `bind_dashboard(StatusPicturePage, "status_picture_dashboard")`. The test module imports that fixture. `tests/conftest.py` is not edited.

**Rationale**: The root conftest is forbidden from importing a report page. `bind_dashboard` is the existing way a suite opens a report on the shared tab. Putting the fixture next to the tests makes `status_picture_dashboard` available without a root import.

**Alternatives considered**:

- *Add the fixture to `tests/conftest.py`*: rejected. That imports a report page from the root conftest.

## Decision 4 — Convert the golden range at the test boundary

**Decision**: The test converts `date_range.start` and `date_range.end` from `YYYY-MM-DD` to `DD/MM/YYYY` and passes those strings to `set_date_range`. The current file yields `13/06/2025` and `25/06/2025`.

**Rationale**: Page 2 date fields use day/month/year. The golden file stores ISO dates. The status-picture page fills `תאריך התחלה` and `תאריך סיום` with a forced click, the same commit shape page 2 uses, copied onto this page rather than imported from the population module.

**Alternatives considered**:

- *Call `select_date_range` with a preset*: rejected. The golden window is a specific pair of dates, not a preset label.
- *Import `to_page_date` from the Screen 2 test module*: rejected. That would load the Screen 2 fixture into this package.

## Decision 5 — Four card titles, two test states

**Decision**: `read_cards()` returns the four current integers it can see:

| Key | Title |
|-----|--------|
| `total_warning_zones` | `מספר אזורי התרעה` |
| `warning_zones_under_fire` | `אזורי התרעה תחת ירי` |
| `total_alerted_population` | `כמות אוכלוסייה מותרעת` |
| `alerted_population` | `אוכלוסייה מותרעת` |

The global test asserts the two all-time keys after `clear_filters`. The filtered test asserts the two range keys after `set_date_range`. A missing title omits that key. The test that needs a missing key skips with `Missing Page Object reader for <key>`.

**Rationale**: The golden file has four expected values, two described as without a date and two described as the selected range. The contract already uses `אזורי התרעה תחת ירי` and `אוכלוסייה מותרעת` as stable card titles. The all-time titles are the phrases in the golden descriptions.

**Alternatives considered**:

- *Read one card twice, before and after the date range*: rejected. The golden keys are different metrics, not one metric sampled twice.

## Decision 6 — Map category keys by numeric id

**Decision**: `read_alerts_by_category()` reads `סה"כ בטווח שנבחר` in these scopes:

| Golden key | Scope |
|------------|--------|
| `category_1_rockets` | `ירי רקטות וטילים` |
| `category_2_aircraft` | `חדירת מחבלים` |
| `category_10_terrorists` | `חדירת כלי טיס עוין` |

**Rationale**: `data/alerts/alerts_contract.yaml` pairs category id `1` with rockets, id `2` with `חדירת מחבלים`, and id `10` with `חדירת כלי טיס עוין`. The golden key carries that id. The English suffix on keys 2 and 10 does not follow those scopes. This slice follows the id. Expected integers stay `16817`, `519`, and `0`.

**Alternatives considered**:

- *Swap scopes 2 and 10 to match the words aircraft and terrorists*: rejected. The contract's confirmed pairing is the id, and the golden key already includes the id.

## Decision 7 — Rank settlements from the chart named in the golden description

**Decision**: `read_top_10_settlements()` reads the visual titled `עשרת היישובים עם כמות ההתרעות הגבוהה ביותר` and returns `{settlement: count}` in draw order. Extra UI rows are allowed. Every golden name must match.

**Rationale**: That title is the golden description and the shorter ranking anchor in the alerts contract. The longer title about the current and previous day is a different chart and is not this metric.

**Alternatives considered**:

- *Read `עשרת הישובים עם כמות ההתרעות הגבוהה ביותר ביממה הנוכחית והקודמת`*: rejected. The contract says that chart is not the ranking metric.

## Decision 8 — Give each skip its own test

**Decision**: `test_screen_1_filtered_metrics` asserts only the two range cards. `test_screen_1_alerts_by_category` and `test_screen_1_top_settlements` perform the chart checks. Each chart test skips with `pytest.skip("Missing Page Object reader for alerts_by_category")` or `pytest.skip("Missing Page Object reader for top_10_settlements")` when its reader returns no labels.

**Rationale**: `pytest.skip` marks the whole test skipped. A skip after the range-card asserts would hide those passes. The user asked for both card asserts and a skip that does not fail the suite.

**Alternatives considered**:

- *Skip from inside `test_screen_1_filtered_metrics`*: rejected. The range-card result would be reported as skipped.

## Decision 9 — Do not edit Screen 2 or `core/`

**Decision**: The new date commit and the new readers live only on `StatusPicturePage`. `pages/alerts_analysis/population_page.py`, the Screen 2 sanity module, `tests/ui/`, and `core/` stay unchanged.

**Rationale**: The user forbade Screen 2 edits. The constitution forbids new domain strings in `core/`.

**Alternatives considered**:

- *Share a date helper from the population page*: rejected. That couples Screen 1 to page 2's private commit method.
