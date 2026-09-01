# Implementation Plan: ReportPortal Integration — Centralized Real-Time Reporting

**Branch**: `feature/reportportal-integration` | **Date**: 2026-09-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-reportportal-integration/spec.md`

**Note**: This plan is filled by `/speckit-plan`. Formal `tasks.md` is produced by
`/speckit-tasks` (not this command).

## Summary

Add ReportPortal as an **additive, opt-in** reporting backend alongside the
existing HTML + Hebrew CSV + Allure outputs. Four wiring points, zero `core/`
changes:

1. **Infrastructure** — a NEW isolated `docker-compose.reportportal.yml` (the
   existing `docker-compose.yml` is never touched).
2. **Dependency** — add `pytest-reportportal` to `requirements.txt`.
3. **Configuration** — add an `rp_*` block to `pytest.ini`; keep reporting OFF
   by default and turn it on per-run with the `--reportportal` flag so current
   runs and CI are unchanged until the stack exists.
4. **Code integration** — extend the root `conftest.py` failure hooks so the
   Playwright failure screenshot and captured logs are pushed to the active
   ReportPortal test item, reusing the existing single-capture guard so nothing
   is duplicated and a ReportPortal outage never turns a passing test red.

Technical approach: **treat ReportPortal as an observability sink**, exactly
like Allure/HTML today (Constitution VI). The `pytest-reportportal` agent owns
launch/test-item lifecycle; our only bespoke code is a thin bridge that
attaches the already-captured screenshot bytes and routes logs when — and only
when — reporting is enabled.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing — Playwright (sync API), pytest,
`pytest-html`, `allure-pytest`. New — `pytest-reportportal` (RP agent, pulls in
the `reportportal-client` transitively). Reuses root `conftest.py` failure
hooks (`_attach_failure_screenshot`, `auth_page`, `pytest_runtest_makereport`).

**Storage**: N/A for the framework. ReportPortal server persists to its own
Postgres + MinIO inside the compose stack; no project schema or `data/*.json`
changes.

**Testing**: `pytest` + Playwright Chromium. Regression gate:
`pytest tests/ui/fleet_dashboard/` MUST stay 100% green both with reporting
disabled (default) and enabled (`--reportportal`) against a live stack, because
the root `conftest.py` is touched (Constitution III).

**Target Platform**: Windows workstation + Docker (Compose plugin) for the
ReportPortal stack; Chromium against the organizational Agamim portal (same as
today). ReportPortal UI defaults to `http://localhost:8080`.

**Project Type**: Internal validation framework (pytest page objects) plus a
locally hosted ReportPortal server as sidecar infrastructure.

**Performance Goals**: ReportPortal reporting is asynchronous in the agent and
MUST NOT add meaningful wall-clock time to a run; when disabled it adds zero
network calls. Screenshot attach reuses bytes already captured on failure — no
extra Playwright screenshot is taken for ReportPortal.

**Constraints**: Constitution v1.2.0 — no `core/` edits, no domain leakage, and
all existing run evidence (HTML, CSV, Allure, screenshots, traces) preserved
(Principle VI). Existing `docker-compose.yml` MUST NOT be modified. Reporting
failures MUST be swallowed like the existing screenshot/trace hooks. The API
key is a secret and MUST come from the environment, not a committed literal.
All new/changed code carries English-only inline comments.

**Scale/Scope**: One new compose file, one line in `requirements.txt`, one
config block in `pytest.ini`, and ~30–50 lines of additive wiring in the root
`conftest.py`. No new page objects, no `pages/` packages, no `.env` schema
change beyond one optional secret variable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: PASS — no Layer 0/2 change. ReportPortal is run wiring in
  the root `conftest.py` and infrastructure files; `core/portal` and
  `core/components` are untouched.
- **Zero domain leakage**: PASS — no report names, KPIs, slicers, or locators
  are added anywhere. Launch name/attributes are generic run metadata read from
  config, not domain labels in `core/`.
- **Test contract**: PASS — reporting is OFF by default (opt-in `--reportportal`
  flag), so fleet smoke is byte-for-byte unchanged without the flag. With the
  flag on, the bridge only *adds* attachments/logs; assertions are untouched.
  Fleet smoke is the regression gate because the root `conftest.py` changes.
- **Extract shared only**: PASS — no new generic portal/slicer API. The RP
  bridge is observability plumbing, not a report abstraction.
- **Warehouse truth**: PASS — `db/` untouched; ReportPortal reports UI test
  outcomes only, it is not a source of business truth.
- **Observability**: PASS and reinforced — HTML, Hebrew CSV, and Allure keep
  emitting; screenshots and traces keep attaching. ReportPortal is an
  *additional* sink for the same evidence, satisfying Principle VI rather than
  replacing any output.

**Post-design re-check**: All gates still PASS. No Complexity Tracking rows —
the design adds an isolated sidecar and additive hooks with a hard "disabled by
default, never fail the run" contract.

## Project Structure

### Documentation (this feature)

```text
specs/008-reportportal-integration/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output (exact CLI commands)
└── contracts/           # Phase 1 output
    └── reportportal-integration.md
```

### Source Code (repository root)

```text
docker-compose.yml                  # UNCHANGED — existing ui-tests service, do NOT edit
docker-compose.reportportal.yml     # NEW — isolated ReportPortal stack (gateway/api/ui/auth/jobs/analyzer/postgres/rabbitmq/minio/migrations)

requirements.txt                    # CHANGED — add: pytest-reportportal>=5.4
pytest.ini                          # CHANGED — add [pytest] rp_* config block; reporting stays opt-in

conftest.py                         # CHANGED — additive RP bridge:
                                     #   - detect RP enabled/session (rp_launch present)
                                     #   - push existing failure screenshot bytes to RP item
                                     #   - route logs to RP via RPLogger/logging handler
                                     #   - swallow all RP errors (never fail the run)

config/settings.py                  # OPTIONAL — surface RP_API_KEY / RP_ENDPOINT env passthrough (no .env values committed)

core/                               # UNCHANGED — no portal or domain edits
pages/                              # UNCHANGED
tests/ui/fleet_dashboard/           # UNCHANGED — regression gate (run with and without --reportportal)
```

**Structure Decision**: ReportPortal is wired at the framework's existing
observability seam — the root `conftest.py` and repo-root config — never inside
`core/`. Infrastructure is isolated in a dedicated compose file per the user's
explicit non-destructive requirement, so the current `ui-tests` workflow is
provably untouched.

## Complexity Tracking

> No constitution violations.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |

## Implementation Approach: opt-in sink + isolated sidecar

Sequence (each step is independently reviewable):

1. **Dependency** — append `pytest-reportportal>=5.4` to `requirements.txt`
   (keep all existing pins). Install with `pip install -r requirements.txt`.

2. **Configuration** — add an `rp_*` block to `pytest.ini` under `[pytest]`.
   Keep it OFF by default: do NOT add `--reportportal` to `addopts`; callers
   pass the flag per run. The API key is read from an env var so no secret is
   committed. Example block (English comments only):

```ini
[pytest]
# --- ReportPortal (opt-in; enable per run with --reportportal) ---
# Base URL of the ReportPortal instance from docker-compose.reportportal.yml.
rp_endpoint = http://localhost:8080
# Target project created in the ReportPortal UI after first bring-up.
rp_project = validation_core
# API/UUID token; sourced from the RP_API_KEY environment variable, not committed.
rp_api_key = ${RP_API_KEY}
# Human-readable launch name shown on the dashboard.
rp_launch = Validation-Core UI Suite
# Launch attributes for filtering runs (key:value pairs).
rp_launch_attributes = env:local suite:ui
# Do not fail the pytest run if ReportPortal is unreachable.
rp_skip_analytics = true
```

3. **Infrastructure** — create `docker-compose.reportportal.yml` from the
   official ReportPortal Compose definition, pinned to a fixed release tag, with
   the UI/gateway host port made overridable (default `8080`) to dodge
   collisions. The existing `docker-compose.yml` is not opened for editing.

4. **Code integration (`conftest.py`)** — additive bridge only. Detect whether
   ReportPortal is active (the agent exposes a session-scoped `reportportal`
   fixture / config value only when `--reportportal` is on). Reuse the bytes the
   framework already captures on failure and push them to the current RP item;
   route logs through the RP logger. All RP calls are wrapped so any failure is
   swallowed. Illustrative sketch (English comments only):

```python
import logging

# ReportPortal's pytest agent registers a logging handler when enabled.
# Using a module logger keeps normal runs untouched when the agent is absent.
rp_logger = logging.getLogger(__name__)


def _reportportal_enabled(config) -> bool:
    # The agent only activates when --reportportal is passed AND rp_endpoint is set.
    return bool(getattr(config.option, "reportportal", False))


def _push_screenshot_to_reportportal(config, name: str, image_bytes: bytes) -> None:
    # Attach an already-captured failure screenshot to the live RP test item.
    # Wrapped defensively: a reporting error must never change test outcome.
    if not _reportportal_enabled(config):
        return
    try:
        # RP reads attachments from the logging record's `attachment` extra.
        rp_logger.error(
            "Playwright failure screenshot",
            extra={
                "attachment": {
                    "name": name,
                    "data": image_bytes,
                    "mime": "image/png",
                }
            },
        )
    except Exception:
        # Swallow like the existing Allure/trace hooks (Constitution VI safety).
        pass
```

   The call is placed in the SAME spot the screenshot is already produced
   (`_attach_failure_screenshot` for call-phase failures and the `auth_page`
   teardown branch for setup-phase failures), guarded by the existing
   `_failure_screenshot_taken` flag so ReportPortal never receives a duplicate.

5. **Regression** — run `pytest tests/ui/fleet_dashboard/` with NO flag (proves
   zero change) and again with `--reportportal` against a live stack (proves the
   launch, live tree, and failure screenshot all land). Confirm
   `docker-compose.yml` has zero git diff.

6. **Docs** — capture the exact bring-up / run / teardown commands in
   `quickstart.md`.

## Risk notes

- **First bring-up latency**: the ReportPortal stack pulls several images and
  runs DB migrations; the UI may take a minute to become healthy. Quickstart
  notes a health check before running tests.
- **API key provisioning**: the key does not exist until the project/user is
  created in the UI after first bring-up. Until `RP_API_KEY` is exported, runs
  simply omit the flag and behave as today (no failure).
- **Port collisions**: default `8080` may be busy; the compose file exposes the
  host port as an overridable variable.
- **Agent/server version skew**: `pytest-reportportal` 5.x targets ReportPortal
  server v5.x. Pin both (agent lower bound + a fixed server image tag) to avoid
  protocol drift.
- **Secret hygiene**: `rp_api_key` must resolve from the environment; never
  commit the literal token into `pytest.ini`.
