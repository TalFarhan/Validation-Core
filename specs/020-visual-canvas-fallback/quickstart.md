# Quickstart: Verifying the Visual Canvas Fallback

**Feature**: 020-visual-canvas-fallback | **Date**: 2026-10-14

Confirm the host decision without a portal, then run the live suites that must stay green. Feature
019's population tests are not part of this gate.

## Prerequisites

- Repo checked out on `feature/reportportal-integration`.
- Python 3.11+ venv with `pip install -r requirements.txt` (Playwright 1.61 or newer, so
  `Locator.filter(visible=...)` exists).
- `.specify/feature.json` points at `specs/020-visual-canvas-fallback`.
- Live gates need `.env` and a saved auth state. The unit gate does not.

## 1. Host decision (no browser)

```powershell
python -m pytest tests/unit/test_scope_host.py tests/unit/test_visual_state.py tests/unit/test_db_parity_engine.py -v
```

Expected:

- Blank scope returns the frame.
- A named group is returned and the canvas selector is not asked for.
- A contained-text group is returned when the named count is 0.
- When both group counts are 0, the result is the visual-container locator filtered with
  `visible=True`.
- `classify_presence([0], 0)` is still `value`.
- Parity-engine unit tests still pass `scope` through `KPI` and `Chart`.

## 2. No report literal in the visual module

```powershell
python -m pytest tests/unit/test_scope_host.py -v
```

The module test fails if `core/components/visual.py` contains a Hebrew letter. Do not satisfy it by
encoding a page title in another script under `core/`.

## 3. Full unit suite

```powershell
python -m pytest tests/unit/ -v
```

Expected: pass. This is the unit-parity gate, including `tests/unit/test_db_parity_engine.py`.

## 4. Fleet smoke (Constitution III)

```powershell
python -m pytest tests/ui/fleet_dashboard/ -v
```

Expected: 100% pass. Section scopes still resolve as groups.

## 5. Alerts page 1

```powershell
python -m pytest tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py tests/ui/alerts_analysis_dashboard/test_db_parity.py -v
```

Expected: pass. Do not require `test_population_invariants.py` in this slice. Those tests resume
under feature 019 after this gate is green.

## 6. Caller sketch (after the iframe is ready)

The strings below are caller data. They are not constants in `core/`.

```python
from core.components.kpi import KPI

kpi = KPI(page, frame)
kpi.number("Card title", scope="Section group")   # tier 1 when that group exists
kpi.number("Card title", scope="Page title text")  # tier 2 when no group owns that text
kpi.number("Card title")                            # whole frame, unchanged
```
