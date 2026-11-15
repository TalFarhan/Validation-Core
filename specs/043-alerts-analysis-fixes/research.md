# Phase 0 Research: Fix Skipped Hierarchy Tests and Navigation Errors for Alerts Analysis

All Technical Context items are known from the existing code; there are no open
`NEEDS CLARIFICATION` markers. This file records the decisions that resolve the
"how" of each fix.

## Decision 1 — Where the ERRORs come from (bilingual names)

**Decision**: Treat the `LoadTimeout` errors as single-language locators that fail when Power BI renders
English accessibility names.

**Rationale**: Reading the code:

- `before_report_ready_check` builds the page-rail locator only from the Hebrew name
  `_PAGE_NAV_LABEL = "ניווט בין עמודים"` (`get_by_role("link"/"button", name=...)` and
  `get_by_label(...)`). When the control's accessible name is `Page navigation`, `count()` is 0, the
  page never switches to Screen 2, and the report-ready anchor (`TOTAL_CARD`) never appears, so
  `navigate`/ready raises `LoadTimeoutError`.
- `set_between_dates` fills the fields via `_fill_input("תאריך התחלה", ...)` / `_fill_input("תאריך סיום", ...)`,
  and `_fill_input` builds `input[aria-label^='{prefix}']`. An English `Start date` / `End date` aria-label
  does not match the Hebrew prefix, so `_commit_field` waits on an invisible field and times out.

**Fix**: Wrap each control in a Playwright `.or_()` over the Hebrew and English name. For the page-rail,
`.or_()` the existing role/label locators with the `Page navigation` variants. For the date fields, change
`_fill_input` (only caller: `set_between_dates`) so it `.or_()`s `input[aria-label^='תאריך התחלה']` with
`input[aria-label^='Start date']` (and the end-date pair), keeping the existing `_commit_field` sequence.

**Alternatives considered**: Detecting the UI language once and switching locators. Rejected — `.or_()` is
simpler, order-independent, and resolves whichever variant Power BI renders without extra state.

## Decision 2 — Dynamic district chart title (and the false "control not visible" skip)

**Decision**: Remove `DISTRICT_CHART = "התרעות לפי מחוז"` and replace it with:

- a class-level map `{mahoz: מחוז, nafa: נפה, rashut: רשות, yeshuv: יישוב}`
- a `@staticmethod district_chart_title_for(level: str) -> str` that returns `"התרעות לפי " + name`
- an instance method `district_chart_title(level: str | None = None) -> str` that reads
  `self._active_hierarchy_level` (default `"mahoz"`) and delegates to the static helper

Record the active level in `set_hierarchy_level` only after a successful selection, then wait for the
*new* title (`district_chart_title_for(level)`) to be visible — not the base `התרעות לפי מחוז`.

**Rationale**: The constant is the anchor passed to `_visual_container` by `before_report_ready_check`,
`set_district_aggregation`, `_hierarchy_control`, `set_hierarchy_level`, `chart_total`,
`read_district_labels`, `_district_visible_total`, and the `others` list in `_visual_container`. Power BI
retitles the visual on drill-down, so after `set_hierarchy_level("nafa")` the title `התרעות לפי מחוז` no
longer exists.

Worse, `set_hierarchy_level` currently clicks the level control and then returns `True` only if
`self.DISTRICT_CHART` (`התרעות לפי מחוז`) is still visible. After a successful drill-down that title is
gone, so the method returns `False` even though the click worked. The sanity helpers then skip with
`"Hierarchy level {level!r} control not visible on district chart"` — a false-negative skip, not a missing
control. Waiting for the *new* title removes that skip path.

A level→Hebrew-name map already exists inside `set_hierarchy_level` for `nafa` / `rashut` / `יישוב`;
promote it to a class-level map that also includes `mahoz`, and reuse it in the accessor.

**Unit-test shape**: `tests/unit/test_population_page.py` currently asserts the class constant and does
not construct a Playwright `Page`. The static helper lets that test assert
`AlertsPopulationPage.district_chart_title_for("mahoz") == "התרעות לפי מחוז"` without a browser. UI tests
call the instance method on the live page (`page.district_chart_title()`).

**`_visual_container` others list**: replace `self.DISTRICT_CHART` in the exclusion set with
`self.district_chart_title()` so a drilled title is not treated as a foreign chart.

**`chart_total` dispatch**: `if title == self.DISTRICT_CHART` becomes `if title == self.district_chart_title()`
(callers pass the accessor). `_district_visible_total` resolves the container via the accessor.

**`set_hierarchy_level` order**:

1. Resolve the level control inside the *current* title's container (`district_chart_title()`).
2. Click and wait for `aria-pressed` / `aria-selected`.
3. Record `_active_hierarchy_level = level` only after the new title is visible.
4. Return `True`. On a missing control or a title that never appears, leave the field unchanged and
   return `False` (existing skip guard still fires).

**Alternatives considered**:

- Keeping the constant and also trying drilled titles. Rejected — two sources of truth; the readers must
  anchor on exactly the live title.
- Matching any title that starts with `התרעות לפי`. Rejected — `_container_is_one_chart` disambiguates by
  excluding the *other* known chart titles, so an exact current title is cleaner and keeps that logic.

**Test impact**: `DISTRICT_CHART` is referenced by `tests/ui/alerts_analysis_dashboard/test_population_invariants.py`
(x2), `tests/ui/alerts_analysis_dashboard/population_snapshot.py`, and `tests/unit/test_population_page.py`.
All three are updated in the same change. Principle III permits same-change test updates for a surface change.

## Decision 3 — Listbox data extraction (district, hour sum, hour daily avg)

**Decision**: Add a listbox-aware read path to `read_district_labels`, `read_hour_buckets`, and
`read_hour_daily_avg`. Primary strategy: reuse the Right-click → "Show as a table" fallback already
proven by the dates chart. Secondary strategy: pair the category `listbox` options with the measure
`listbox` options in draw order (`התרעות` for sums; a series whose name contains `ממוצע` for daily avg).

**Rationale**: `read_district_labels` tries `_scrolled_district_rows` (grid `role="row"`),
`_labeled_mark_values` (category text + SVG `aria-label` marks), then a tooltip hover; `read_hour_buckets`
tries SVG `aria-label` marks, chart categories, labeled marks, then a tooltip. When the visual renders as a
Power BI `listbox`, none of those match: there are no grid rows, the marks carry no numeric `aria-label`,
and the categories come back empty.

`read_hour_daily_avg` is the same visual with the average series. FR-006 names `read_hour_buckets`; FR-007
also requires `test_alerts_by_hour_daily_avg_matches_db` to stop skipping, so the daily-avg reader gets
the same fallback (average column / average listbox) even though it is not named in FR-006.

The dates chart already solves the same "no rows, no marks" problem by opening the visual as an accessible
table. `_visible_date_entry` is already generic (rowheader text + integer column) — it does not parse
dates — so district names and hour tokens work without a new row parser. `_header_index` /
`_last_table_with_header` already take a header string; `_alert_column_table` currently hardcodes
`התרעות` and `_leave_dates_table` waits for `DATES_CHART`. Those two must be parameterized:

- `_alert_column_table(header: str = "התרעות")` (daily avg passes a header that equals or contains
  `ממוצע`).
- `_leave_visual_table(title: str)` replaces the dates-only leave: click `חזרה לדוח`, then wait for
  `title` (the calling visual) to be visible again. Dates keep calling it with `DATES_CHART`.
- `_click_show_as_table` already tries `("הצג כטבלה", "Show as a table")`; keep that bilingual menu. Change
  only the error text so it names the calling visual instead of always `DATES_CHART`.

Try existing row/mark/category paths first (preserve current behavior when those work). If they return
empty, open Show-as-a-table; if that also yields nothing, pair listbox options. Return `{}` only when
every path is empty so the skip guard still fires.

**Listbox pairing**: inside the visual container, find `role="listbox"` nodes. Category options are the
non-numeric labels (district names / `HH:MM` tokens). The measure listbox is the one named `התרעות`
(sum) or whose accessible name contains `ממוצע` (daily avg). Zip by draw order; drop a pair whose value
is not an integer.

**Hour token shape**: keep the existing `HH:MM` normalization (`_HOUR_TOKEN`) so golden keys such as
`"00:00"` still match.

**Alternatives considered**:

- Moving the fix into `core/components/chart.py`. Rejected — the constitution keeps report tables/tooltips/
  drilldowns on the domain page; Layer 2 must stay report-agnostic (AC-001, Principle VII). Chart.py has
  no listbox path today and must not gain alerts headers.
- A pure listbox reader with no table fallback. Rejected — the Show-as-a-table path is already hardened for
  virtualization/scrolling on Screen 2; relying only on raw listbox options would be more fragile.
- Deleting `_leave_dates_table` and always pressing Escape. Rejected — the dates suite already depends on
  the named back button plus a title-visible wait.

## Decision 4 — Skips resolve, guards stay

**Decision**: The bilingual, title, and listbox fixes remove both skip families:

- empty-read skips (`read_district_labels` / `read_hour_buckets` / `read_hour_daily_avg` returning `{}`)
- false-negative `set_hierarchy_level` skips (waiting for the old `מחוז` title after a drill-down)

Keep every `pytest.skip` guard as a safety net for a genuinely absent control. Do not edit the skip
messages or the sanity test bodies beyond the audit (no golden literals).

**Rationale**: The request asks to resolve the skips into assertions (FR-007), not to delete the guards. A
control that is truly missing (e.g. a level that does not render) should still skip with its descriptive
message rather than fail opaquely.

**Alternatives considered**: Deleting the guards. Rejected — same reason as the sibling fleet slice; the
guards protect against a genuinely absent control.

## Decision 5 — Contract gate

**Decision**: Because the alerts domain page object is edited, run the alerts UI smoke suite
(`tests/ui/alerts_analysis_dashboard/`) and the unit test (`tests/unit/test_population_page.py`) green as
part of the work, in addition to the sanity module. The fleet smoke suite is not a gate here because no
`core/` or fleet navigation surface is touched.

**Rationale**: Principle III requires the edited domain page's test contract to stay green. The alerts
smoke suite and the unit test directly exercise the changed surface (page open, district title, chart
totals, `set_between_dates`). The constitution's fleet-smoke gate targets Layer 0 / fleet changes, which
this slice does not make.

**Alternatives considered**: Running the full fleet smoke suite. Not required — unaffected by an
alerts-only edit — but it remains green and is cheap to confirm if desired.

## Decision 6 — Out of scope (do not expand)

- English variants of chart *titles* (`Alerts by district`) are not in the request; titles stay Hebrew.
- The numeric-range inputs (`התחל` / `סיום`) and the dates-table back button (`חזרה לדוח`) are not in
  the bilingual list. Leave them Hebrew unless a later run proves they ERROR in English.
- No fleet, status-picture, `core/`, root `conftest.py`, or golden metric-value edit.
