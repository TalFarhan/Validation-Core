# Phase 0 Research: Credit Consumption UI Sanity Validation

All Technical Context items are known from feature 044, the current credit page and sanity
module, and Layer 0's last-refresh reader. No **NEEDS CLARIFICATION** remains.

## R1 — Expand the 044 page and tests

- **Decision**: Edit `pages/credit_consumption/credit_consumption_page.py` and
  `tests/sanity/credit_consumption_dashboard/test_data_validation.py` in place. Keep
  `tests/sanity/credit_consumption_dashboard/conftest.py`, `pages/credit_consumption/page.py`,
  and `tests/ui/credit_consumption_dashboard/test_dashboard_smoke.py` as they are.
- **Rationale**: Feature 044 already shipped `apply_filters`, `open_export_page`,
  `read_kpi_metrics`, `set_metric`, `set_visualization`, `read_daily_trends`,
  `read_daily_alerts`, `read_expenses_by_authority`, and `read_export_table`, plus the
  sanity fixture and the six tests. The user said to expand those files and not rebuild them.
- **Alternatives considered**: A new page class or a new test module. Rejected — the user
  named the existing paths. Re-planning 044 or 045 in place. Rejected — 044 is the build
  slice and 045 is the alerts hour-chart slice. This comparison contract is `046`.

## R2 — Subset match, and fail versus skip

- **Decision**: Comparison is a subset. Iterate golden keys and rows only. Extra UI keys and
  extra UI rows do not fail. Replace the empty-read `pytest.skip` in `_assert_nested` and
  `_assert_golden_rows` with an assertion when the golden side is non-empty. Call
  `pytest.skip` only before the read, and only when the visual is absent:
  - Trends, alerts, and authority: `visual_is_rendered(title)` is false for the existing
    chart title (`TRENDS_CHART`, `ALERTS_CHART`, `AUTHORITY_CHART`).
  - Export grid: `export_grid_is_rendered()` is false when no visible `grid` or `table` is
    on Screen 2.
  - KPIs: skip only when none of the existing `_KPI_SPECS` card titles are visible. If any
    card is visible, a missing or empty golden key fails.
- **Rationale**: `_show_as_table_rows` today catches a missing container and returns `[]`.
  `_assert_golden_rows` then skips, so a broken parser and a missing chart look the same.
  The user requires those cases to diverge. `pytest.skip` aborts the whole test, so the
  rendered check belongs once per visual, not inside the golden-row loop. Daily trends share
  one chart: if that title is absent, skip the trends test; if it is present, an empty series
  for any toggle key fails.
- **Alternatives considered**: Keep the 044 skip on every empty list. Rejected — the user
  said an empty UI against golden data is a failure. Skip the rest of a test from inside the
  row loop. Rejected — one absent row would hide later mismatches, and an absent row is a
  failure, not a skip. Copy the alerts `_assert_golden_keys` helper. Rejected — alerts code
  is off-limits, and that helper's quote-folding is not part of this slice.

## R3 — Assertion text

- **Decision**: Every mismatch uses one shape: `{json_path}: ui={actual!r} golden={expected!r}`.
  A missing row uses the same shape with `ui` set to the sorted keys that were present (or
  `[]` when the reader returned nothing). Paths are rooted at `credit_consumption_dashboard`:
  - `screen_1_summary.dashboard_info.title`
  - `screen_1_summary.dashboard_info.last_updated`
  - `screen_1_summary.kpi_metrics.<nested.key>`
  - `screen_1_summary.daily_trends_by_toggle.<toggle_key>[date=<date>].<field>`
  - `screen_1_summary.daily_alerts[date=<date>].<field>`
  - `screen_1_summary.expenses_by_authority_millions[authority=<authority>].<field>`
  - `screen_2_data_export.title`
  - `screen_2_data_export.export_table_data[transaction_date=<date>,authority_name=<name>,sub_category=<sub>].<field>`
- **Rationale**: The user requires the path, the UI value, and the golden value in the
  failure. The existing messages are close (`ui=` / `golden=`) but they skip instead of
  failing, and the row label is not a JSON path.
- **Alternatives considered**: A custom exception type. Rejected — a pytest assertion string
  is enough and stays in the test module.

## R4 — Titles use the existing phrase locator

- **Decision**: Add `title_is_visible(title: str) -> bool` on the credit page. It uses the
  existing `_iframe_phrase_locator` and does not introduce a new selector. Screen 1 passes
  `dashboard_info.title`. Screen 2 passes `screen_2_data_export.title` after
  `open_export_page()` and `apply_filters`. The test fails when the phrase is not visible.
  It does not skip: the report-ready wait has already required a Screen 1 or Screen 2 phrase.
  `SCREEN_1_TITLE` and `SCREEN_2_TITLE` stay as the page's known phrases. The expected string
  in the assertion is the YAML value, not a new literal in the test.
- **Rationale**: Both constants already match the golden titles (`תמ״צ צריכת אשראי`,
  `צריכת אשראי - ייצוא נתונים`). The user said to use existing page elements. A visibility
  check on the YAML string shows the live UI, and the message still prints both sides.
- **Alternatives considered**: Asserting only `page.SCREEN_1_TITLE == yaml_title` without
  looking at the iframe. Rejected — that checks a Python constant, not the rendered title.
  Scraping the document title with a new parser. Rejected — `_iframe_phrase_locator` already
  matches the phrase. Quote-folding `'` and `"`. Rejected — that rule belongs to the alerts
  slice and this user did not ask for it.

## R5 — Last updated without a second parser

- **Decision**: The Screen 1 test calls `page._last_refresh_caption_text()` after
  `apply_filters`. It normalizes whitespace and asserts the golden
  `dashboard_info.last_updated` string (`DD/MM/YYYY HH:MM`, for example `01/11/2026 11:38`)
  occurs in that caption. No new regex, no `strptime`, and no wrapper on the credit page.
  `verify_freshness` and `_parse_last_refresh_datetime` in `core/portal/page.py` are not
  modified and are not called by the sanity test.
- **Rationale**: The user named `_last_refresh_caption_text` and forbade a second date
  parser. That method already returns the iframe caption chunks joined by newlines, including
  the timestamp `verify_freshness` parses. A substring of the golden format is an exact match
  and does not reinterpret the clock. The smoke test keeps its own 24-hour age check.
- **Alternatives considered**: Formatting `_parse_last_refresh_datetime` with
  `strftime("%d/%m/%Y %H:%M")`. Rejected — that is a second formatting path in the test, and
  the Layer 0 parser also accepts month-first formats, so it can accept a string the golden
  file would reject. Editing the golden timestamp when the live report has refreshed.
  Rejected — YAML files are not edited. Overriding `verify_freshness` to assert the snapshot.
  Rejected — the smoke test must stay the 24-hour check and stay green on its own terms.

## R6 — Filters come from the YAML

- **Decision**: Keep `apply_screen_1_filters` passing `screen_1_summary.active_filters` into
  `apply_filters`. Keep `apply_screen_2_filters` merging `top_bar` then `side_bar` with
  `dict.update`. Keep `apply_filters` skipping values equal to `הכל` and skipping ids that
  are not in `_SLICER_DEFINITIONS`. Do not add the period name as a literal in tests or in
  new code. The current golden file's non-default values are `time_range` and `period`; the
  test must not mention them.
- **Rationale**: `apply_filters` already implements the default. Hardcoding the period would
  drift when another golden file is pointed at the same helpers. Screen 2's two maps do not
  share keys today; `side_bar` wins if they ever do, which matches the existing helper.
- **Alternatives considered**: Selecting the period by a test literal. Rejected — the user
  forbade that. Clicking `הכל` to "confirm" the default. Rejected — it is already selected
  and the extra settle is flake-prone. A new `SlicerKind`. Rejected — Constitution VII, and
  the dropdown definitions from 044 already cover these ids.

## R7 — Daily trends, alerts, and authority

- **Decision**: Keep the test loop `metric, visualization = key.rsplit("_", 1)`, then
  `set_metric`, `set_visualization`, `read_daily_trends`. Row key is `date`. Compare `day`
  with equality so it stays a string. For `transactions_count_bar`, the reader keeps
  `values` as the list of numbers from the table row (`[3, 1]`, `[3]`). It must not unwrap
  that list. Other toggle keys keep scalar `value`. Alerts use `read_daily_alerts()` with
  key `date`. Authority uses `read_expenses_by_authority()` with key `authority`. Extraction
  remains `_show_as_table_rows` (right-click, `הצג כטבלה` / `Show as a table`, read, back).
- **Rationale**: `rsplit("_", 1)` is required because `expense_amount` and
  `transactions_count` themselves contain underscores. `_trend_row` already switches on
  `_active_metric == "transactions_count"` and `_active_visualization == "bar"`. The tests
  must set both toggles before the read so that flag is correct. SVG and tooltip readers
  stay unused. Alerts Analysis table helpers stay unimported.
- **Alternatives considered**: Splitting the key on every underscore. Rejected — that yields
  three tokens for `expense_amount_line`. Coercing `values[0]` to `value`. Rejected — the
  golden bar rows are lists. Sorting the list before compare. Rejected — column order is
  part of the value. Parsing `day` as an integer. Rejected — the golden `day` is a Hebrew
  weekday string.

## R8 — Export table types

- **Decision**: Keep `read_export_table`. `quantity` goes through `_parse_number` and is
  stored as `int` when the cell is a whole number. `amount` stays `_plain_cell` output so
  thousands separators remain (`"1,944.97"`). Do not run `_parse_number` on `amount`.
  Composite key is `(transaction_date, authority_name, sub_category)`. Header aliases stay
  the existing `_EXPORT_HEADERS`. A Hebrew header that does not match the live grid is
  replaced by copying the live header, with an English comment only.
- **Rationale**: The golden `quantity` values are ints and the golden `amount` values are
  comma-formatted strings. `_plain_cell` strips bidi marks and a doubled Power BI label; it
  does not remove commas. `_parse_number` does remove commas, so it must not be used for
  `amount`.
- **Alternatives considered**: Parsing `amount` to `float`. Rejected — `"1,944.97"` would
  become `1944.97` and fail the golden string. Leaving `quantity` as a string. Rejected —
  the user requires an int. Building a new grid reader. Rejected — `_visible_table_rows`
  already maps the visible `grid` / `table`.

## R9 — What stays green and what is not edited

- **Decision**: Do not change `verify_freshness`, the smoke test, `core/portal/page.py`,
  `core/components/`, `db/`, the root `conftest.py`, the YAML, or any alerts, status-picture,
  or fleet file. Update `docs/COVERAGE_CATALOG.md` section 9 with rows for
  `dashboard_info.title`, `dashboard_info.last_updated`, and the fail-versus-skip rule so
  the catalog matches the suite.
- **Rationale**: The user listed those trees as out of scope and said the smoke test must
  stay green. The catalog is the constitution's map of measure to test. It already describes
  this suite and would omit the new asserts if left as 044 wrote it. The catalog edit does
  not change runtime behavior.
- **Alternatives considered**: Skipping the catalog because the user did not name it.
  Rejected — the quality gate says the catalog stays consistent with page-object and
  assertion changes, and section 9 is the credit sanity map. Folding the golden timestamp
  into `verify_freshness`. Rejected — that would change Layer 0 and the smoke contract.
  The snapshot `01/11/2026 11:38` can be older than 24 hours while a later refresh is not;
  the two checks are different and both stay.

## R10 — Known runtime tension (accepted)

- **Decision**: Implement both checks as specified. Do not edit the YAML and do not relax
  `verify_freshness` when the snapshot timestamp and the 24-hour window disagree on a given
  day.
- **Rationale**: They answer different questions. Smoke asks whether the caption is recent.
  Sanity asks whether the caption still contains the golden snapshot string. A mismatch is a
  real result, not a defect in the reader.
- **Alternatives considered**: Documenting the golden `last_updated` as informational again.
  Rejected — 044 left it informational; this user made it an assertion.
