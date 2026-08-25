# Data Model: Dashboard Freshness Verification

**Feature**: `003-dashboard-freshness` | **Date**: 2026-08-25

This feature does not introduce warehouse tables. The model is the
last-refresh caption, the freshness window, and the Layer 0 method.

## Entities

### Last-refresh caption

| Field | Meaning | Rules |
|-------|---------|-------|
| Phrase | `הדשבורד עודכן לאחרונה ב:` | Generic Power BI chrome; MAY live in `core/` |
| Timestamp text | Substring after the phrase | Required; failure if missing |
| Parsed value | Naive `datetime` | Local time; see format list in research.md |
| Scope | Inside the report iframe | First visible match |

**Validation**: Phrase match is containment (regex / text locator), not an
exact full-string equality on the whole visual.

### Freshness window

| Field | Meaning | Rules |
|-------|---------|-------|
| `max_hours` | Maximum allowed age | `int`, default `24` |
| Now | `datetime.now()` | Local machine clock |
| Age | `now - parsed` | Future timestamps → negative age → pass |
| Pass | `age <= timedelta(hours=max_hours)` | Inclusive |

### ReportShell.verify_freshness

| Field / member | Meaning | Rules |
|----------------|---------|-------|
| Location | `core/portal/page.py` | Layer 0 only |
| Args | `max_hours: int = 24` | Additive public API |
| Wait | Existing iframe wait | MUST NOT wait on a fleet KPI |
| Errors | `AssertionError` | Distinct messages: not found / unparseable / too old |
| Observability | Allure step | Failures keep screenshot/trace via existing hooks |

**Relationships**: Inherited by `MainDashboardPage`. Tests call it on the
`dashboard` fixture. No new fixture.

### Fleet smoke test

| Attribute | Value |
|-----------|--------|
| Name | `test_dashboard_updated_within_24_hours` |
| File | `tests/ui/fleet_dashboard/test_dashboard_smoke.py` |
| Fixture | `dashboard` (already navigated) |
| Call | `dashboard.verify_freshness()` |
| Marker | `sanity` |

## State transitions (verify_freshness)

```text
[start]
  → wait for report iframe
  → locate caption containing the standard phrase
       ├─ not found → fail (caption missing)
       └─ found → extract timestamp text
            ├─ unparseable → fail (include captured text)
            └─ parsed → compare to datetime.now()
                 ├─ age > max_hours → fail (include parsed time and age)
                 └─ else → pass
```

## Out of scope

- DIM/FACT warehouse last-refresh queries
- New KPI or filter models
- A second production report entity
- Parser unit-test doubles (optional later)
