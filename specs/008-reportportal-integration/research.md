# Phase 0 Research: ReportPortal Integration

All NEEDS CLARIFICATION items from the Technical Context are resolved below.
Each entry is a decision with rationale and rejected alternatives.

## R1. Which ReportPortal pytest agent?

- **Decision**: Use `pytest-reportportal` (the official RP pytest agent),
  pinned `>=5.4`. It transitively pulls `reportportal-client`.
- **Rationale**: First-party, actively maintained, targets ReportPortal server
  v5.x, and integrates through native pytest hooks so launch/test-item
  lifecycle is handled for us. It reads all configuration from `pytest.ini`
  `rp_*` keys, matching the user's request for a config block.
- **Alternatives considered**:
  - Raw `reportportal-client` + custom hooks — rejected: reinvents launch/item
    lifecycle the agent already provides.
  - Allure→ReportPortal import — rejected: batch import is not real-time; the
    manager explicitly asked for a *real-time* dashboard.

## R2. Always-on vs. opt-in reporting?

- **Decision**: Opt-in per run via the agent's `--reportportal` CLI flag. Do NOT
  add it to `addopts`.
- **Rationale**: Constitution III (existing tests are the contract) — current
  CI/local runs must be byte-for-byte unchanged until the RP stack and API key
  are provisioned. Opt-in guarantees zero network calls and zero behavior change
  when the flag is absent.
- **Alternatives considered**:
  - Always-on with `addopts` — rejected: a missing/unhealthy server would add
    latency and noise to every run before the stack exists.

## R3. How to attach Playwright failure screenshots to RP?

- **Decision**: Reuse the bytes already captured by the existing
  `_attach_failure_screenshot` / `auth_page` teardown logic and emit them
  through the ReportPortal logging handler using the `attachment` extra on a log
  record (`{"name", "data", "mime"}`). Guard with the existing
  `_failure_screenshot_taken` flag to avoid duplicates.
- **Rationale**: The framework already takes exactly one full-page screenshot on
  failure (call-phase in `pytest_runtest_makereport`, setup-phase in `auth_page`
  teardown) and attaches it to Allure + pytest-html. RP's canonical attachment
  path is the logging record `attachment` extra, so we push the same bytes with
  no second Playwright call and no duplication.
- **Alternatives considered**:
  - Separate RP screenshot capture — rejected: double capture, slower, and can
    diverge from the Allure/HTML image.
  - `pytest-playwright --screenshot` — rejected: this project deliberately does
    not use that flag (see `conftest.py` docstring); capture stays centralized.

## R4. How to route logs to RP test items?

- **Decision**: Use the RP logging handler the agent installs when enabled; a
  module-level `logging.getLogger(__name__)` is sufficient for the bridge, and
  test/helper log lines flow to the current item automatically.
- **Rationale**: The agent wires a handler that maps standard `logging` records
  to the active test item, so no bespoke transport is needed. When the agent is
  absent, the same logger is a normal no-op logger — nothing changes.
- **Alternatives considered**:
  - Manual `rp_client.log(...)` calls sprinkled in tests — rejected: couples
    test bodies to RP and violates page-object discipline.

## R5. Docker layout — append vs. separate file?

- **Decision**: Create a NEW `docker-compose.reportportal.yml`. Never edit the
  existing `docker-compose.yml`.
- **Rationale**: The user explicitly forbids overwriting the existing file and
  prefers isolation. A separate file lets ReportPortal be started/stopped
  independently (`docker compose -f docker-compose.reportportal.yml up -d`) and
  guarantees the `ui-tests` service definition shows zero diff (SC-004).
- **Alternatives considered**:
  - Append RP services to the existing file — rejected by requirement; also
    riskier (one file, coupled lifecycles, larger blast radius).
  - Compose `include:`/merge of both files — acceptable later, but not needed;
    isolation is the stated preference.

## R6. Which ReportPortal server version / services?

- **Decision**: Base `docker-compose.reportportal.yml` on the official RP
  Compose for server v5.x, pinned to a fixed release tag. Core services:
  `gateway` (traefik), `api`, `ui`, `uat`/authorization, `jobs`, `analyzer`
  (+ `analyzer-train`), `migrations`, and backing stores `postgres`,
  `rabbitmq`, `minio`. Expose the gateway/UI host port as an overridable
  variable (default `8080`).
- **Rationale**: This is the vendor-supported topology; pinning a tag avoids
  protocol drift against the `pytest-reportportal` 5.x agent (R1). An overridable
  port avoids collisions with the existing workstation services.
- **Alternatives considered**:
  - `latest` tags — rejected: reproducibility and agent/server skew risk.
  - Trimming services (e.g. dropping analyzer) — deferred: keep the reference
    topology first; optimize only if resource-constrained.

## R7. Secret handling for the API key.

- **Decision**: `pytest.ini` references `rp_api_key = ${RP_API_KEY}`; the real
  token is exported in the environment (or an untracked `.env`) and provisioned
  from the RP UI after first bring-up.
- **Rationale**: Keeps secrets out of version control; aligns with existing
  settings-from-environment patterns in `config/settings.py`.
- **Alternatives considered**:
  - Hardcoding the token — rejected: secret leakage.

## R8. Failure-isolation contract.

- **Decision**: Every RP call in `conftest.py` is wrapped in `try/except` that
  swallows exceptions, mirroring the existing screenshot/trace hooks.
- **Rationale**: FR-008 / SC-005 — an RP outage must never turn a passing test
  red nor abort teardown. The existing hooks already follow this pattern.
- **Alternatives considered**:
  - Let RP errors propagate — rejected: violates the run-stability contract.
