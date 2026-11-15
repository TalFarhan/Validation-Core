# Quickstart: Hosen Status Screen 1 YAML Sanity

## What this slice does

Adds a landing-screen reader and a golden-YAML check for תמ"צ חוסן:

- Right-hand filters through Layer 2 `Slicer` (read the selected label, do not click).
- National assessment card and its category cards through Layer 2 `KPI` (title, percentage, trend).
- `ציון חוסן` rows through `collect_virtualized_rows` (authority, score, green or yellow).
- Top-left survey counts and missing authorities through locators on `HosenStatusPage`.
- One sanity test compares that dict to `data/hosen/db_sanity.yaml`.

The smoke test still calls `verify_freshness()` only.

## Prerequisites

- Portal auth configured (the sanity test opens the live Power BI report).
- Python env with `pytest`, `PyYAML`, and Playwright (already in `requirements.txt`).
- Windows workstation; Chromium driven by `bind_dashboard`.

## Files you will touch

- `pages/hosen_status/page.py` — `read_screen_1_metrics()` and the four section readers.
- `data/hosen/db_sanity.yaml` — create `hosen_dashboard.screen_1_landing` from one live read.
- `tests/sanity/hosen_status_dashboard/conftest.py` — `hosen_status_dashboard` fixture.
- `tests/sanity/hosen_status_dashboard/test_screen1_sanity.py` — subset compare.
- `docs/COVERAGE_CATALOG.md` — YAML block ↔ reader ↔ test rows.

Live-copied during implementation (not invented in the plan): the eight category titles, the
survey phrasing, slicer accessible names, and every number.

## Do NOT touch

- `core/portal/`, `core/components/`.
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

Smoke must stay green. The sanity test fails with a YAML path when a golden key is missing or
different, and when a visible section comes back empty while the golden block has data.

## Done when

- `read_screen_1_metrics()` returns `survey_status`, `kpis`, `resilience_scores`, and `active_filters`.
- The YAML file holds the numbers. The page and the test do not.
- Extra UI rows do not fail the test. A golden key that is absent does.
- `core/` is unchanged.
