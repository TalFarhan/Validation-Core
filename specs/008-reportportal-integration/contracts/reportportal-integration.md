# Contract: ReportPortal Integration Seam

This is the interface contract the implementation MUST satisfy. It is the
executable-ish specification for reviewers and for `/speckit-tasks`. All code
examples use English-only inline comments (project coding standard).

## C1. Dependency contract (`requirements.txt`)

- MUST append exactly one new line; MUST NOT remove or downgrade existing pins.

```text
# ReportPortal pytest agent (transitively installs reportportal-client).
pytest-reportportal>=5.4
```

## C2. Configuration contract (`pytest.ini`)

- MUST add an `rp_*` block under the existing `[pytest]` section.
- MUST NOT add `--reportportal` to `addopts` (reporting stays opt-in).
- `rp_api_key` MUST reference an environment variable, never a literal token.

```ini
# --- ReportPortal (opt-in; enable a run with: pytest --reportportal) ---
rp_endpoint = http://localhost:8080
rp_project = validation_core
rp_api_key = ${RP_API_KEY}
rp_launch = Validation-Core UI Suite
rp_launch_attributes = env:local suite:ui
```

**Behavioral guarantees**:
- No flag ⇒ agent inert: no launch, no network, identical run to today.
- Flag + reachable endpoint ⇒ one launch, live test tree.

## C3. Infrastructure contract (`docker-compose.reportportal.yml`)

- MUST be a NEW file; the existing `docker-compose.yml` MUST show zero diff.
- MUST pin the ReportPortal server to a fixed v5.x release tag.
- MUST expose the gateway/UI host port as an overridable variable (default
  `8080`).
- MUST include the reference topology: `gateway`, `api`, `ui`, authorization
  (`uat`), `jobs`, `analyzer` (+ `analyzer-train`), `migrations`, `postgres`,
  `rabbitmq`, `minio`.

**Behavioral guarantees**:
- `docker compose -f docker-compose.reportportal.yml up -d` brings the stack up
  in isolation.
- `docker compose -f docker-compose.reportportal.yml down` tears it down without
  touching the `ui-tests` service or `result/`.

## C4. Code integration contract (`conftest.py`)

The bridge is **additive** and **fail-safe**. It MUST NOT alter existing
capture logic; it only forwards already-captured evidence when RP is enabled.

### C4.1 Enablement probe

```python
def _reportportal_enabled(config) -> bool:
    # True only when the agent is switched on via --reportportal.
    # Keeps every existing run path untouched when the flag is absent.
    return bool(getattr(config.option, "reportportal", False))
```

### C4.2 Screenshot forwarding (reuse existing bytes)

- MUST be invoked from the SAME place the screenshot is already produced:
  `_attach_failure_screenshot` (call phase) and the `auth_page` teardown branch
  (setup phase).
- MUST respect the existing `_failure_screenshot_taken` guard — at most one
  screenshot per item reaches ReportPortal.
- MUST swallow all exceptions.

```python
def _push_screenshot_to_reportportal(config, image_bytes: bytes, name: str = "screenshot") -> None:
    # Forward the already-captured PNG to the active RP test item.
    # Never re-capture and never raise: reporting must not change outcomes.
    if not _reportportal_enabled(config):
        return
    try:
        rp_logger.error(
            name,
            extra={"attachment": {"name": name, "data": image_bytes, "mime": "image/png"}},
        )
    except Exception:
        # Mirror the existing Allure/trace hooks: swallow reporting errors.
        pass
```

### C4.3 Log routing

- When enabled, standard `logging` records MUST reach the current RP item via
  the handler the agent installs. No test body may call the RP client directly.

### C4.4 Fail-safe guarantee

- Any ReportPortal error (connection refused, auth failure, timeout) MUST be
  swallowed. Test pass/fail MUST be identical to a run with RP disabled.

## C5. Observability preservation contract

- HTML (timestamped), Hebrew CSV run book, Allure results, screenshots, and
  traces MUST all still be produced with RP enabled AND disabled
  (Constitution VI). ReportPortal is strictly additional.

## C6. Regression contract

- `pytest tests/ui/fleet_dashboard/` (no flag) ⇒ 100% pass, unchanged.
- `pytest tests/ui/fleet_dashboard/ --reportportal` (live stack) ⇒ 100% pass,
  launch visible, failure screenshots attached on any induced failure.

## C7. Acceptance checklist (maps to spec Success Criteria)

- [ ] `docker-compose.yml` unchanged (SC-004).
- [ ] Launch appears live on RP UI when enabled (SC-001).
- [ ] Every failed UI test carries a screenshot on its RP item (SC-002).
- [ ] Fleet smoke green with and without the flag (SC-003).
- [ ] Unreachable RP endpoint still yields HTML+CSV+Allure and no red passing
      tests (SC-005).
- [ ] No `core/` changes; English-only inline comments (SC-006).
