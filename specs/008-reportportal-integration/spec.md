# Feature Specification: ReportPortal Integration — Centralized Real-Time Reporting

**Feature Branch**: `feature/reportportal-integration`

**Created**: 2026-09-01

**Status**: Draft

**Audience**: Validation / QA Automation engineers own the run experience.
The reporting-observability contract (existing HTML + Hebrew CSV + Allure
artifacts stay intact; ReportPortal is additive and opt-in) is normative
under Constitution v1.2.0 Principle VI (Observability of Validation Runs).

**Input**: User description: "Integrate ReportPortal into the existing
`pytest` + Playwright automation project (currently Allure + HTML reports)
for a centralized real-time dashboard and failure analysis. Do NOT overwrite
the existing `docker-compose.yml` — prefer a separate
`docker-compose.reportportal.yml`. Add `pytest-reportportal` to
`requirements.txt`, add the ReportPortal config block to `pytest.ini`, and
update `conftest.py` fixtures so executions, logs, and Playwright
failure screenshots are sent to ReportPortal. Provide the exact CLI commands
to start the containers and run the tests. All inline code comments MUST be
in English only."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time launch dashboard (Priority: P1)

A Validation engineer starts a test run with ReportPortal enabled and watches
the launch populate in real time on the ReportPortal UI — suites, tests,
pass/fail status, and durations — without waiting for the run to finish.

**Why this priority**: The centralized real-time dashboard is the manager's
primary ask; it is the MVP of the whole feature.

**Independent Test**: Bring up the ReportPortal stack, run any existing smoke
suite with the ReportPortal flag, and confirm a new launch appears live in the
ReportPortal UI with the correct test tree and results.

**Acceptance Scenarios**:

1. **Given** the ReportPortal containers are healthy and `pytest.ini` holds a
   valid endpoint/project/API key, **When** a run starts with ReportPortal
   enabled, **Then** a launch is created and tests stream in live.
2. **Given** ReportPortal is NOT enabled (no flag), **When** a run starts,
   **Then** no launch is created and the run behaves exactly as today
   (HTML + CSV + Allure only).

### User Story 2 - Failure analysis with screenshots and logs (Priority: P1)

When a UI test fails, the engineer opens the failed test in ReportPortal and
sees the Playwright full-page failure screenshot and the captured logs
attached to that test item, enabling root-cause analysis from the dashboard.

**Why this priority**: "Failure analysis" is the second explicit ask and the
main reason to centralize beyond a static HTML file.

**Independent Test**: Force a UI test to fail, run with ReportPortal enabled,
and confirm the failed item in ReportPortal carries the failure screenshot and
log lines.

**Acceptance Scenarios**:

1. **Given** a UI test fails during the call phase, **When** the run reports to
   ReportPortal, **Then** the failure screenshot is attached to that test item.
2. **Given** a UI test fails during fixture setup (e.g. `navigate`), **When**
   the run reports to ReportPortal, **Then** the failure screenshot is still
   attached to that item.
3. **Given** a test emits log lines, **When** it reports to ReportPortal,
   **Then** those log lines appear under the test item.

### User Story 3 - Isolated, non-destructive infrastructure (Priority: P1)

A DevOps-minded engineer brings up ReportPortal without altering the existing
`ui-tests` container definition, and can tear ReportPortal down independently.

**Why this priority**: The user explicitly forbids overwriting the existing
`docker-compose.yml`; isolation protects the current CI/local workflow.

**Independent Test**: Start the ReportPortal stack from its own compose file,
confirm the existing `docker-compose.yml` file is byte-for-byte unchanged, and
tear the ReportPortal stack down without affecting `ui-tests`.

**Acceptance Scenarios**:

1. **Given** the existing `docker-compose.yml`, **When** ReportPortal is added,
   **Then** that file is unchanged and ReportPortal lives in
   `docker-compose.reportportal.yml`.
2. **Given** the ReportPortal stack is running, **When** it is torn down,
   **Then** the `ui-tests` service and its artifacts are unaffected.

### Edge Cases

- ReportPortal endpoint unreachable or API key invalid — the run MUST still
  complete and still produce HTML + CSV + Allure; the ReportPortal failure MUST
  NOT fail otherwise-passing tests.
- ReportPortal flag off — zero behavioral change vs. today (no launch, no
  network calls, fleet smoke stays 100% green).
- Screenshot capture already taken for a failing item — the item MUST NOT get a
  duplicate/second screenshot pushed to ReportPortal.
- Port collision on the ReportPortal UI/gateway port — the compose file MUST
  expose an overridable host port so it can move off a busy port.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST add `pytest-reportportal` to `requirements.txt`
  with a pinned lower bound, without removing or downgrading existing pins.
- **FR-002**: `pytest.ini` MUST gain a ReportPortal configuration block
  (`rp_endpoint`, `rp_project`, `rp_api_key`, `rp_launch`, and launch
  attributes). Reporting MUST be OFF by default and enabled per-run via a CLI
  flag so existing runs are unchanged.
- **FR-003**: ReportPortal infrastructure MUST be defined in a NEW file
  `docker-compose.reportportal.yml`. The existing `docker-compose.yml` MUST NOT
  be modified.
- **FR-004**: When enabled, a run MUST create exactly one ReportPortal launch
  and stream test items (suites, tests, statuses, durations) in real time.
- **FR-005**: When a UI test fails (call phase OR setup/fixture phase), the
  Playwright full-page failure screenshot MUST be attached to that test item in
  ReportPortal, reusing the existing single-capture logic (no duplicate shots).
- **FR-006**: Test log lines MUST be routed to ReportPortal test items when
  enabled, using the ReportPortal logging handler/logger.
- **FR-007**: All existing observability outputs (timestamped HTML report,
  Hebrew CSV run book, Allure results, screenshots, traces) MUST continue to be
  produced whether or not ReportPortal is enabled (Constitution VI).
- **FR-008**: A ReportPortal outage/misconfiguration MUST NOT change test
  pass/fail outcomes; reporting errors MUST be swallowed like the existing
  screenshot/trace hooks.
- **FR-009**: The fleet smoke suite (`tests/ui/fleet_dashboard/`) MUST pass at
  100% with ReportPortal disabled AND with it enabled against a live stack
  (Constitution III).
- **FR-010**: Documentation MUST provide the exact CLI commands to bring up the
  ReportPortal containers, run tests with reporting enabled, and tear the stack
  down.
- **FR-011**: `core/` MUST NOT be modified for this feature — ReportPortal is
  run/observability wiring, not portal or domain logic (Constitution I/II).
- **FR-012**: All new/changed code MUST contain inline comments in English only.

### Key Entities

- **ReportPortal launch**: One logical run in ReportPortal, named from
  `rp_launch`, tagged with launch attributes (e.g. suite, environment).
- **Test item**: A ReportPortal node per pytest test; carries status, duration,
  logs, and attachments (failure screenshot).
- **RP configuration**: `pytest.ini` keys plus a secret API key sourced from
  environment/`.env` rather than committed in clear text.
- **ReportPortal stack**: The set of ReportPortal services in
  `docker-compose.reportportal.yml` (gateway, api, ui, auth, jobs, analyzer,
  postgres, rabbitmq, minio, migrations).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With the stack up and the flag on, a launch appears in the
  ReportPortal UI within seconds of run start and updates live.
- **SC-002**: 100% of failed UI tests in a ReportPortal-enabled run show the
  failure screenshot on the failed item.
- **SC-003**: 100% of existing fleet smoke checks still pass both with and
  without ReportPortal enabled.
- **SC-004**: The existing `docker-compose.yml` shows zero diff after the
  feature lands; ReportPortal is fully contained in its own compose file.
- **SC-005**: A run against an unreachable ReportPortal endpoint still produces
  HTML + CSV + Allure artifacts and does not turn passing tests red.
- **SC-006**: A reviewer finds no `core/` changes and English-only inline
  comments in all new code.

## Assumptions

- Docker (with the Compose plugin) is available on the engineer's workstation.
- The ReportPortal API key/project are provisioned in the ReportPortal UI after
  first bring-up and supplied via environment variables, not committed secrets.
- The existing single-tab Playwright session and failure-artifact hooks in the
  root `conftest.py` remain the capture path; ReportPortal reuses their output.
- Enabling ReportPortal via a CLI flag (rather than always-on) is acceptable to
  keep current CI runs unchanged until the stack is provisioned.
