# Phase 0 Research: Hosen Status Screen 1 YAML Sanity

**Feature**: `050-hosen-screen1-sanity` | **Date**: 2026-11-12

All technical-context unknowns are resolved below. Nothing remains NEEDS CLARIFICATION.

## 1. Feature directory

- **Decision**: Plan this slice in `specs/050-hosen-screen1-sanity`. Repoint
  `.specify/feature.json` here. Stay on git branch `feature/reportportal-integration`.
- **Rationale**: Setup initially resolved the pinned directory `specs/049-hasbara-ui-validation`,
  which already has a finished Hasbara plan. The user task is the Hosen landing screen. Writing
  into `049` would replace that plan. This repository already plans a new spec directory without
  switching the long-lived checkout (see `049` and `044`).
- **Alternatives considered**: Overwrite `049` (rejects the current Hasbara plan). Create a new
  git branch (the established checkout for these slices is `feature/reportportal-integration`).

## 2. Where Screen 1 is read

- **Decision**: Add `read_screen_1_metrics()` to the existing `HosenStatusPage` in
  `pages/hosen_status/page.py`. Leave `tests/ui/hosen_status_dashboard/page.py` absent. The UI
  package only has the smoke test, its conftest, and `__init__.py`. The conftest already imports
  `pages.hosen_status.page.HosenStatusPage`.
- **Rationale**: The page object is already the Layer 0 binding: search `תמ"צ חוסן`, ready text
  `תמ"צ ארצי - דיווחי קה"א יקל"ר`, freshness phrase `מועד רענון`. Constitution IV puts new
  locators on that page.
- **Alternatives considered**: A new page class under `tests/` (forbidden by the constitution).
  A second page module beside `page.py` (the class is small enough to extend in place).

## 3. Selected filter text

- **Decision**: Compose `Slicer` on the page. Read the selection with the public
  `Slicer.control(slicer_id)` locator and `inner_text()`. Strip the Hebrew role name and bidi
  marks on the page so the returned string is the selected label. Do not add `Slicer.selected()`.
- **Rationale**: `Slicer` already exposes `control()` for dropdowns (`get_by_role("combobox")`).
  `_dropdown_shows_selection` is private and only answers a boolean during `select()`. Hasbara
  already reads slicer text the same way in `PublicInquiriesPage.read_slicer_text` without a
  Layer 2 change. A `selected()` helper would be a convenience used by one new call site.
  Constitution VII says not to add generic APIs that have not earned a second report.
- **Alternatives considered**: Edit `slicer.py` to return selected text (stops the "do not touch
  core" rule for a wrapper around `inner_text`). Copy a Hasbara slicer reader (the user forbade
  copying those scrapers).

## 4. KPI percentage and trend

- **Decision**: Locate each card with `KPI.card(title)` (and `KPI.read_text` for the value).
  Keep the percent sign in the string the test compares. Classify `trend` on the page from a
  non-canvas arrow inside that card: direction first (`up` / `down` / `flat`), then computed
  color (green → `up`, red → `down`, yellow → `flat`). Do not change `extract_kpi_value_text`.
- **Rationale**: `KPI.read_text` on a button returns the last paragraph, which can still contain
  `%`. On a group visual, `read_text` calls `extract_kpi_value_text`, which returns the longest
  numeric token and drops `%`. The page can recover `%` from the same card locator. `KPI` has
  no trend API. Arrow color is a Hosen display rule (`up` / `down` / `flat`), so it stays next
  to the Hebrew titles. Sampling a canvas would violate the task.
- **Alternatives considered**: `KPI.number`, which parses `55%` toward `55` and breaks exact
  string match. A new `KPI.trend()` in `core/` (not universal until a second report needs the
  same three-way map; this slice does not add it). Copying a Hasbara chart reader (those readers
  target different visuals).

## 5. Resilience rows and color

- **Decision**: Pass the `ציון חוסן` grid to `collect_virtualized_rows`. The page callback
  returns `authority`, score text, and `status`. Status comes from `getComputedStyle`
  background of the row or the score cell: green-dominant → `green`, yellow (high red and green,
  low blue) → `yellow`, otherwise the raw `rgb(...)` string. `row_id` is the authority name.
- **Rationale**: `collect_virtualized_rows` already scrolls a caller-supplied grid, dedupes by a
  caller-supplied id, and stores whatever fields the callback returns. It has no Hosen field
  names. Color vocabulary `green` / `yellow` is specified by this feature and belongs on the page.
  An unknown color must not be coerced, or a wrong paint would pass.
- **Alternatives considered**: A new color parameter on `virtual_grid.py` (domain status words
  would leak into Layer 2). Scraping the canvas bitmap (forbidden). Reading only the viewport
  without the collector (misses virtualized authorities).

## 6. Survey status

- **Decision**: Read the top-left submitted count, total count, and missing-authority list with
  Playwright locators on `HosenStatusPage`. Return counts as digit strings. No Layer 2 type is
  involved.
- **Rationale**: The block is report text, not a KPI card, slicer, or virtualized grid. The task
  assigns it to standard locators and forbids putting those Hebrew phrases in `core/`.
- **Alternatives considered**: Forcing the block through `KPI` (the two counts plus a name list
  are not one KPI value). A new generic "callout" reader (one report, so it has not earned a
  Layer 2 module).

## 7. Comparison

- **Decision**: Private helpers in `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py`
  implement subset match, integer coercion, and exact strings. They are not imported from
  Hasbara or Credit, and they are not placed in `tests/helpers/`.
- **Rationale**: The task says not to build a new comparison engine. Hasbara's `_assert_tree` /
  `assert_value` / `assert_rows` are the behavioral model (every golden key, ignore extra UI,
  `1324` matches `1,324`). Importing that module would couple the suites. A shared engine would
  be the new component the task rejects.
- **Alternatives considered**: `validate_dashboard_generic` (warehouse parity, no Hosen SQL).
  Importing the Hasbara helpers (edits the dependency boundary the task drew).

## 8. Golden literals

- **Decision**: The schema is fixed in data-model.md. During implementation, one live read of the
  open landing screen is written into `data/hosen/db_sanity.yaml`. The page and the test do not
  contain those numbers. Examples in the task (`7`, `12`, `55%`, `מחוז דרום`, `נפת לכיש`) document
  shape and the kind of label a slicer returns.
- **Rationale**: No checked-in Hosen golden file and no prior message in this workspace contain a
  verified full snapshot. Inventing `55%` would make the first run fail or, worse, hide a real
  value. Freezing the live screen is how the other YAML sanity files became the source of truth.
- **Alternatives considered**: Hardcode the examples as the golden file (treats illustrations as
  measurements). Leave the YAML empty and skip (the task requires a failing test when the golden
  block expects data and the reader is empty).

## 9. Empty visual versus skip

- **Decision**: If the section anchor is visible and the golden block has data, an empty reader
  fails. If that anchor is not rendered, skip that block and still assert the blocks that are
  present.
- **Rationale**: The task requires a failure when the generic component returns empty data for a
  visual that is on screen. Skipping the whole test when one corner is missing would hide the
  other three blocks. Hasbara uses the same present-versus-absent split.
- **Alternatives considered**: Always fail when an anchor is missing (breaks a report that has
  not finished publishing one visual). Always skip on empty (hides a broken reader).

## 10. Waits and canvas

- **Decision**: Visibility waits use Playwright `expect` with `self.timeout` (the `ReportShell`
  timeout). No `time.sleep`, no `wait_for_timeout`, no `networkidle`. No canvas pixel read.
- **Rationale**: `HosenStatusPage` already waits on a text locator inside the report iframe.
  `collect_virtualized_rows` already waits on animation frames inside its own loop. Adding a
  sleep or a network-idle wait would violate the task and the page-object wait policy.
- **Alternatives considered**: `page.wait_for_load_state("networkidle")` (Power BI keeps sockets
  open; the task forbids it). Screenshot diff of the canvas (not a structured read, and the task
  forbids canvas scraping).
