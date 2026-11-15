# Phase 0 Research: Population Screen Data Validation Tests

**Feature**: 033-population-sanity-tests | **Date**: 2026-10-19

No `NEEDS CLARIFICATION` markers remain.

## Decision 1 — Pin a new spec directory

**Decision**: Plan this work as `specs/033-population-sanity-tests`. `.specify/feature.json` now points there. The git checkout stays `feature/reportportal-integration`.

**Rationale**: The previous pin was `specs/032-date-input-force-click`, which already has a plan for the forced date click. Writing this golden-record slice into that directory would replace an unrelated plan. Spec numbering in this repo is sequential, and `033` is the next free prefix.

**Alternatives considered**:

- *Fill `032-date-input-force-click/plan.md` again*: rejected. That spec is the overlay click, not these sanity tests.

## Decision 2 — Call `clear_filters()`, not a new alias

**Decision**: `test_global_metrics_match_db` calls `population_dashboard.clear_filters()`.

**Rationale**: `AlertsPopulationPage.clear_filters` clears every slicer and waits until the total card repeats. The page has no `clear_all_filters` method. The request's clear-all step is this method. The page file stays unchanged.

**Alternatives considered**:

- *Add `clear_all_filters` as an alias*: rejected. The public method already clears every slicer, and this slice must not edit the page object.

## Decision 3 — Read cards with `read_card`, not `take_snapshot`

**Decision**: A helper `read_population_cards(page)` returns `{role: page.read_card(role)}` for `total`, `warned`, and `unprotected`. The tests assert `cards['total']`, `cards['unprotected']`, and `cards['warned']`.

**Rationale**: `read_card` is the page method for those three roles (`CardRole`). `take_snapshot` in `tests/ui/alerts_analysis_dashboard/population_snapshot.py` also sums the hour, dates, district, and settlement charts. This slice does not assert those totals, and it must not edit that helper. A local card map matches the requested `cards[...]` assertions without dragging chart reads into the sanity tests.

**Alternatives considered**:

- *Import `take_snapshot`*: rejected. A chart-read failure would fail a card assertion, and the helper lives in `tests/ui/`, which this slice does not modify.
- *Assert `read_card(...)` inline with no `cards` dict*: rejected. The request asserts `cards['total']`, `cards['unprotected']`, and `cards['warned']`.

## Decision 4 — Convert golden dates to the page format

**Decision**: `to_page_date` parses `YYYY-MM-DD` and returns `DD/MM/YYYY`. `test_filtered_population_matches_db` passes those strings to `set_date_range` in file order.

**Rationale**: The golden `date_range` stores `2026-09-01` and `2025-10-18`. `set_between_dates` documents that values use the page's date format, and the existing population tests pass `01/09/2026`. Typing the ISO strings into `תאריך התחלה` and `תאריך סיום` would not select the range the golden `expected_value` describes. Conversion yields `01/09/2026` and `18/10/2025`.

**Alternatives considered**:

- *Pass the YAML strings through unchanged*: rejected. The date inputs are day/month/year.
- *Edit the golden file to `DD/MM/YYYY`*: rejected. The file is the user's golden record and stays as stored. Conversion belongs at the test boundary.

## Decision 5 — Keep the inverted golden range in file order

**Decision**: Do not swap or rewrite `date_range`. Start stays `2026-09-01` (`01/09/2026`). End stays `2025-10-18` (`18/10/2025`).

**Rationale**: The request says to extract `start` and `end` from the file and pass them to `set_date_range`. The end date is earlier than the start date. That is a property of the golden file, not a second code path. This slice does not edit the YAML.

**Alternatives considered**:

- *Treat the end year as 2026*: rejected. That invents a date the file does not contain.
- *Swap start and end so the range is chronological*: rejected. The request names `start` and `end` from the file keys.

## Decision 6 — Import the existing fixture into the new module

**Decision**: `test_data_validation.py` imports `population_dashboard` from `tests.ui.alerts_analysis_dashboard.conftest`. Both tests request that fixture and nothing else. A helper `load_sanity_data()` reads the YAML inside each test.

**Rationale**: The fixture is `bind_dashboard(AlertsPopulationPage, "population_dashboard")`. It depends on root `auth_page` and `browser_context`, which apply to every test under `tests/`. Pytest's fixture scan sees a fixture object imported into the test module. The user's signatures take only `population_dashboard`, so the YAML load is a helper call rather than a second fixture argument. The UI conftest is not edited.

**Alternatives considered**:

- *Copy `bind_dashboard(...)` into a new sanity `conftest.py`*: rejected. That duplicates the fixture. The import is enough and leaves `tests/ui/` untouched.
- *Add a `sanity_data` fixture argument*: rejected. The requested signatures have one parameter.

## Decision 7 — Assert only the three named metrics

**Decision**: The tests read `dashboard_sanity_checks.screen_2_alerts_analysis` and assert only `total_population_all_time`, `unprotected_population`, and `alerted_population_selected_range`. Screen 1 and the other screen 2 blocks stay unused.

**Rationale**: The request names those three `expected_value` paths and two tests. Settlement rows, hierarchy sums, alerts by date, and alerts by hour are a larger slice.

**Alternatives considered**:

- *Generate one test per metric in the file*: rejected. That exceeds the two functions the request specified.

## Decision 8 — Mark the tests `sanity` only

**Decision**: Both tests use `@pytest.mark.sanity`. They do not use `data` or `db_parity`.

**Rationale**: `pytest.ini` already defines `sanity` for this kind of check, and `--strict-markers` rejects unknown marks. The `data` and `db_parity` marks in this repo mean a live warehouse comparison. These tests compare the UI to the golden file.

**Alternatives considered**:

- *Add `@pytest.mark.db_parity`*: rejected. That mark belongs to the YAML SQL contract, which has a different shape and a live query.

## Decision 9 — Resolve the golden file from the test file

**Decision**: `load_sanity_data` opens `Path(__file__).resolve().parents[3] / "data" / "alerts" / "db_sanity_am_kalavi.yaml"` with UTF-8 and `yaml.safe_load`.

**Rationale**: The test file is three directories under the repo root (`tests/sanity/alerts_analysis_dashboard/`). A path from `__file__` does not depend on the shell's current directory. `PyYAML` is already required.

**Alternatives considered**:

- *Hard-code a drive path*: rejected. The repo is checked out under a user directory that is not stable.
