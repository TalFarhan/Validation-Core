# Quickstart: Population Page Internal Refactor

Branch stays `feature/reportportal-integration`. Feature directory: `specs/038-population-page-refactor`.

## What changes

- `pages/alerts_analysis/population_page.py`: one visible-row scroll collector, one row script, one hover loop, no `Chart._container` or `Chart._parse`, no bare `except Exception`, appearance waits on `state="visible"`.
- `core/components/chart.py`: public `parse_container(container, title)` wrapping the existing parse. `Chart.read` stays.

## What stays

- Every public method signature on `AlertsPopulationPage`
- `tests/sanity/` and `tests/ui/`
- `data/alerts/db_sanity_am_kalavi.yaml`
- `core/portal/`
- District label order: visible rows, then marks, then tooltip
- Hour sum order: aria, then categories, then marks, then tooltip

## Static check

From the repository root, after implementation:

```powershell
python -m pytest tests/unit/test_population_page.py -q
```

That test does not open a browser. It checks the subclass, `DISTRICT_CHART`, `PAGE_TITLE`, and the population fixture binding.

Search the page and confirm the debt is gone:

```powershell
rg -n "except Exception|_chart\._container|_chart\._parse|time\.sleep" pages/alerts_analysis/population_page.py
```

Expect no matches.

## Live check

Portal auth is required. Do not edit the tests.

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_population_invariants.py tests/sanity/alerts_analysis_dashboard/test_data_validation.py -q
```

## Fleet gate

`core/components/chart.py` is edited, so the fleet smoke suite is the Layer 2 gate. Fleet page objects are not part of this slice.

```powershell
python -m pytest tests/ui/fleet_dashboard/ -q
```

The run is green only at 100%.
