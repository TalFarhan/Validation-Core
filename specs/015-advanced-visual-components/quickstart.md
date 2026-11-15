# Quickstart: Verifying Advanced Visual Components

**Feature**: 015-advanced-visual-components | **Date**: 2026-10-13

Confirm gauge scale parsing, empty-versus-zero, and chart shape rules without a portal, then run the
fleet smoke gate. No new dependency.

## Prerequisites

- Repo checked out; Python 3.11+ venv with `pip install -r requirements.txt`.
- `.specify/feature.json` points at `specs/015-advanced-visual-components`.

## 1. Existing KPI extract (must stay green)

```powershell
python -m pytest tests/unit/test_kpi_normalize.py -v
```

Expected: every current row passes, including labeled and compact Gauge rows. `extract_kpi_value_text`
is not redefined by scale parsing.

## 2. New pure readers (no browser)

```powershell
python -m pytest tests/unit/test_gauge_scale.py tests/unit/test_visual_state.py tests/unit/test_chart_shape.py -v
```

Expected:

- Labeled and compact strings return value, minimum, and maximum. A slash pair returns value and
  maximum with minimum null. A lone `0` is state `value`. A blank string is state `empty`.
- `classify_presence([0], 0)` is `value`. `classify_presence([None], 0)` is `empty`.
- Descending check allows ties, rejects an increase, counts categories rather than bars, and keeps a
  missing series cell as null.

## 3. Caller compatibility

`tests/helpers/db_parity_engine.py` must still call `KPI.number(name)` with one argument.

```powershell
rg "kpi\.number\(" tests/helpers/db_parity_engine.py
```

Fleet chart methods stay on `pages/fleet_dashboard/main_dashboard_page.py`. This feature does not
require that page to import `Chart`.

## 4. Regression gate (Constitution III)

```powershell
python -m pytest tests/ui/fleet_dashboard/
```

Expected: 100% pass (portal / `.env` required). Default `scope=None` and existing KPI number reads
are unchanged.

## 5. Caller sketch (after the iframe is ready)

Titles below stand in for whatever the domain page passes. They are not framework constants.

```python
from core.components.chart import Chart
from core.components.kpi import KPI

kpi = KPI(page, frame)
scale = kpi.scale("<opaque kpi title>", scope="<opaque section or None>")
# scale["state"] == "value" and scale["value"] == 0  → rendered zero
# scale["state"] == "empty"                          → blank visual, not zero
# scale["maximum"]                                    → upper bound or denominator when present

chart = Chart(page, frame)
reading = chart.read("<opaque chart title>")
assert chart.category_count("<opaque chart title>") == len(reading.categories)
assert chart.is_descending("<opaque chart title>", series_index=0)
assert chart.displayed_title("<opaque chart title>")  # full current title, suffix included
```

Assert any slicer-dependent phrase in the test, against `displayed_title`, not inside `core/`.
