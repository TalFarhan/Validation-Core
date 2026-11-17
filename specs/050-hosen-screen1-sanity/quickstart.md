# Quickstart: Hosen Status Screen 1 YAML Sanity

## What this slice does

Adds a landing-screen reader and a golden-YAML check for תמ"צ חוסן:

- The Screen 1 date combobox, driven by `screen_1_landing.date`, before the district and
  subdistrict smart filters. The page opens the control `_filter_control` returned, once, and
  chooses that YAML value in the control's frame, including a nested iframe.
- Right-hand district and subdistrict filters through the smart-filter path, driven by
  `screen_1_landing.filters`, before any metric is read. A visible spinner is expected hidden,
  then the ready locator.
- National assessment card through Layer 2 `KPI` for the card, then `.value tspan` via
  `text_content()` (`title`, `percentage`, `trend`). Category cards use the same SVG read and
  are published as `title`, `score`, and `trend_direction`.
- `ציון חוסן` rows through `collect_virtualized_rows` (authority, score, green or yellow).
  `authority` is the first line of the cell, so `קרית מלאכי` is not stored with a following
  accessibility line.
- Top-left survey counts and missing authorities through locators on `HosenStatusPage`.
- One sanity test compares that dict to `data/hosen/db_sanity.yaml`.

The smoke test still calls `verify_freshness()` only.

## Prerequisites

- Portal auth configured (the sanity test opens the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.

## Files you will touch

- `pages/hosen_status/page.py` — date selection stays as already planned. Category grades are
  `_svg_grade`: `.value tspan` read with `text_content()`, then published as `score` and
  `trend_direction`. The national card stays `percentage` and `trend`. In
  `_visible_resilience_rows`, `authority` becomes
  `_plain(extracted_text.split("\n")[0])`. Comments inside the function stay English.
  `select_screen_1_filter` does not call `page.wait_for_timeout`.
- `data/hosen/db_sanity.yaml` — leave `hosen_dashboard.screen_1_landing` as it is, including
  `date`.
- `tests/sanity/hosen_status_dashboard/conftest.py` — `hosen_status_dashboard` fixture.
- `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` — already applies
  `screen_1_landing.date`, then `filters`. This amendment does not edit the test.
  `_assert_rows` already reads `score` with `actual.get(field, "")`.
- `docs/COVERAGE_CATALOG.md` — YAML block ↔ reader ↔ test rows.

Live-copied during implementation (not invented in the plan): the eight category titles, the
survey phrasing, slicer accessible names, and every number.

## Do NOT touch

- `core/portal/`, `core/components/`.
- `data/hosen/db_sanity.yaml` for this amendment. The date stays the value already in the file.
- `data/hasbara/`, `data/credit/`, `data/alerts/`.
- Hasbara, Credit, and Alerts page modules and tests.
- `tests/ui/hosen_status_dashboard/test_dashboard_smoke.py` and its conftest.
- The root `conftest.py`.
- `db/`.

## Run

```powershell
pytest tests/ui/hosen_status_dashboard/test_dashboard_smoke.py
pytest tests/sanity/hosen_status_dashboard/test_screen1_sanity.py
```

Smoke must stay green. The sanity test applies every `filters` entry, waits until the spinner
is gone and the ready locator is visible, and only then reads Screen 1. It fails with a YAML
path when a golden key is missing or different, and when a visible section comes back empty
while the golden block has data.

## Done when

- `select_screen_1_filter("date", value)` opens the resolved date combobox once, chooses
  `value` in that control's frame (nested iframe included), and raises when the combobox text
  after `_screen_1_settle` does not contain `value`.
- `section_anchor_visible("date")` is true when the date combobox is visible.
- `read_screen_1_metrics()` runs after `date` and `filters` are applied and returns
  `survey_status`, `kpis`, `resilience_scores`, `filters`, and `date`. `date` is the selected
  label, not a hardcoded literal.
- The `בחירת נפה` search input is clicked with `force=True`, so `ul.TokensContainer` does not
  time out that click.
- The YAML file holds the numbers. The page and the test do not.
- A category `score` such as `88%` is `text_content()` of that card's `.value tspan`, not
  `inner_text()`, and the category dict uses `score` and `trend_direction`.
- A resilience authority cell whose text is `קרית מלאכי\nעיצוב מותנה נוסף` is published as
  `קרית מלאכי`. `_assert_rows` is not edited. The golden file is not edited.
- Extra UI rows do not fail the test. A golden key that is absent does.
- `core/` is unchanged.
