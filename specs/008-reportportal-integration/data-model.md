# Phase 1 Data Model: ReportPortal Integration

This feature has no application/business data model. The "entities" here are
configuration and reporting objects that describe how a run maps into
ReportPortal. No warehouse schema and no `data/*.json` catalogs are involved.

## Entity: RP Configuration (`pytest.ini` `rp_*` block)

| Field | Source | Required | Notes |
|-------|--------|----------|-------|
| `rp_endpoint` | `pytest.ini` | Yes | Base URL of the RP instance (default `http://localhost:8080`). |
| `rp_project` | `pytest.ini` | Yes | RP project created in the UI after first bring-up. |
| `rp_api_key` | env `RP_API_KEY` via `${RP_API_KEY}` | Yes to enable | Secret token; never committed as a literal. |
| `rp_launch` | `pytest.ini` | Yes | Human-readable launch name on the dashboard. |
| `rp_launch_attributes` | `pytest.ini` | No | `key:value` pairs for filtering (e.g. `env:local suite:ui`). |
| `--reportportal` | CLI flag | Yes to enable | Opt-in switch; absence = current behavior, no launch. |

**Validation rules**:
- Reporting activates only when `--reportportal` is passed AND `rp_endpoint`
  resolves. Otherwise the agent is inert (no launch, no network).
- `rp_api_key` MUST resolve from the environment; an empty value disables
  reporting rather than committing a placeholder secret.

## Entity: Launch

| Field | Value | Notes |
|-------|-------|-------|
| name | `rp_launch` | One launch per `pytest` invocation. |
| attributes | `rp_launch_attributes` | Generic run metadata only — no domain labels (Constitution II). |
| status | derived | Aggregated from child test items by the agent. |

**Lifecycle**: created at session start, finished at session end — both managed
by the `pytest-reportportal` agent, not by our code.

## Entity: Test Item

| Field | Value | Notes |
|-------|-------|-------|
| name | pytest nodeid | Maps 1:1 to a pytest test. |
| status | pass/fail/skip | Set by the agent from the pytest report. |
| duration | measured | Set by the agent. |
| logs | `logging` records | Routed via the RP logging handler. |
| attachments | failure screenshot | PNG bytes pushed from the existing capture, once per item (guarded by `_failure_screenshot_taken`). |

## Entity: Attachment (failure screenshot)

| Field | Value | Notes |
|-------|-------|-------|
| name | `screenshot` / descriptive | Same image already sent to Allure + HTML. |
| data | PNG bytes | Captured full-page on failure; reused, not re-captured. |
| mime | `image/png` | Passed via the logging record `attachment` extra. |

**State transitions (per test item)**:

```text
created (agent, on test start)
  → logs streamed (agent handler)
  → on failure: screenshot attached once  [guard: _failure_screenshot_taken]
  → finished with status (agent, on test stop)
```

## Non-entities (explicitly out of scope)

- No `core/portal` or `core/components` objects change.
- No `pages/<report>/` objects, no `.env` schema change beyond the optional
  `RP_API_KEY` passthrough.
- ReportPortal's own persistence (Postgres/MinIO) is server-internal and not
  modeled by the framework.
