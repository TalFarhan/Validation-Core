# Tasks: ReportPortal Integration — Centralized Real-Time Reporting

**Input**: Design documents from `/specs/008-reportportal-integration/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/reportportal-integration.md, quickstart.md

**Tests**: This feature does NOT change `core/portal`, `ReportShell`, or shared
page-object navigation, so contract/integration tests are OPTIONAL. However, the
root `conftest.py` is modified, so fleet smoke validation
(`pytest tests/ui/fleet_dashboard/`) is a MANDATORY completion gate — run it both
WITH and WITHOUT `--reportportal` (Constitution III / plan regression contract).

**Organization**: Tasks are grouped by user story. All three stories are P1 and
independently testable. Coding standard: every new/changed line carries
**English-only inline comments**.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3
- Exact file paths are included in each task

## Path Conventions

- Repo root: `requirements.txt`, `pytest.ini`, `conftest.py`, `docker-compose.yml`
  (UNCHANGED), `docker-compose.reportportal.yml` (NEW), `config/settings.py`
- `core/` is UNCHANGED for this feature.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the ReportPortal dependency so the agent is importable.

- [ ] T001 Append `pytest-reportportal>=5.4` to `requirements.txt` as a new line, keeping all existing pins unchanged, with an English inline comment noting it pulls in `reportportal-client` transitively
- [ ] T002 Install dependencies with `pip install -r requirements.txt` and confirm `pytest --help` shows the `--reportportal` option (agent registered)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Configuration that US1 (dashboard) and US2 (failure analysis) both
depend on. Reporting MUST stay OFF by default.

**⚠️ CRITICAL**: US1 and US2 cannot be verified until this phase is complete.

- [ ] T003 Add the ReportPortal config block to `pytest.ini` under `[pytest]` (`rp_endpoint`, `rp_project`, `rp_api_key = ${RP_API_KEY}`, `rp_launch`, `rp_launch_attributes`) with English inline comments; do NOT add `--reportportal` to `addopts` so reporting remains opt-in
- [ ] T004 [P] Surface an `RP_API_KEY` / `RP_ENDPOINT` environment passthrough in `config/settings.py` (read-from-env only, no committed secret value) with English inline comments
- [ ] T005 Verify `pytest tests/ui/fleet_dashboard/ -m sanity` runs with NO `--reportportal` flag and behaves exactly as before (no launch, no network) — baseline for the regression gate

**Checkpoint**: Dependency installed and config present; opt-in switch confirmed inert when off.

---

## Phase 3: User Story 3 - Isolated, non-destructive infrastructure (Priority: P1) 🎯 MVP

**Goal**: Stand up ReportPortal from its OWN compose file without touching the
existing `docker-compose.yml`.

**Independent Test**: `docker compose -f docker-compose.reportportal.yml up -d`
brings the stack healthy; `git diff --exit-code docker-compose.yml` shows zero
diff; `down` tears it down without affecting `ui-tests`.

> Sequenced first because US1 and US2 need a live ReportPortal server to verify
> against, and this story is the user's explicit non-destructive requirement.

- [ ] T006 [US3] Create NEW `docker-compose.reportportal.yml` based on the official ReportPortal v5.x Compose topology (`gateway`, `api`, `ui`, `uat`, `jobs`, `analyzer`, `analyzer-train`, `migrations`, `postgres`, `rabbitmq`, `minio`), pinning a fixed release tag, with English inline comments
- [ ] T007 [US3] In `docker-compose.reportportal.yml`, expose the gateway/UI host port as an overridable variable (default `8080`, e.g. `${RP_UI_PORT:-8080}`) to avoid port collisions
- [ ] T008 [US3] Confirm `docker-compose.yml` is NOT opened or modified for this feature; run `git diff --exit-code docker-compose.yml` and confirm zero output
- [ ] T009 [US3] Bring the stack up (`docker compose -f docker-compose.reportportal.yml up -d`), wait until `ps` shows healthy, open the UI at `http://localhost:8080`, and create the `validation_core` project + an API key in the UI

**Checkpoint**: ReportPortal server is running in isolation; existing compose file provably untouched.

---

## Phase 4: User Story 1 - Real-time launch dashboard (Priority: P1)

**Goal**: A run with reporting enabled creates one launch that streams the test
tree live to the ReportPortal UI.

**Independent Test**: With the stack up and `RP_API_KEY` exported, run a smoke
suite with `--reportportal` and watch a live launch appear with correct
pass/fail/duration.

- [ ] T010 [US1] Export the API key for the shell session (`$env:RP_API_KEY = "<key>"`) and run `pytest tests/ui/fleet_dashboard/ -m sanity --reportportal`; confirm a launch named from `rp_launch` appears live in the UI with the correct test tree
- [ ] T011 [US1] Confirm `rp_launch_attributes` (e.g. `env:local suite:ui`) appear as filterable attributes on the launch, and that attributes are generic run metadata only (no domain/report labels — Constitution II)
- [ ] T012 [US1] Confirm the OFF path once more: the same suite WITHOUT `--reportportal` creates no launch (US1 must not regress the default run)

**Checkpoint**: Real-time dashboard works when enabled; default runs unaffected.

---

## Phase 5: User Story 2 - Failure analysis with screenshots and logs (Priority: P1)

**Goal**: Failed UI tests carry the Playwright failure screenshot and logs on
their ReportPortal item, for both call-phase and setup-phase failures, without
duplicates and without ever failing an otherwise-passing run.

**Independent Test**: Force a UI failure, run with `--reportportal`, and confirm
the failed RP item shows the screenshot and log lines; an unreachable endpoint
still yields HTML+CSV+Allure and no red passing tests.

### Implementation for User Story 2 (all edits in `conftest.py`, additive)

- [ ] T013 [US2] Add `_reportportal_enabled(config)` helper to `conftest.py` returning `bool(getattr(config.option, "reportportal", False))`, with an English inline comment (keeps all existing paths untouched when the flag is absent)
- [ ] T014 [US2] Add a module-level `rp_logger = logging.getLogger(__name__)` and `_push_screenshot_to_reportportal(config, image_bytes, name="screenshot")` to `conftest.py` that emits the PNG via the RP logging `attachment` extra, wrapped in `try/except` that swallows all errors, with English inline comments (per contract C4.2)
- [ ] T015 [US2] Call `_push_screenshot_to_reportportal(...)` from within `_attach_failure_screenshot` (call-phase failures) reusing the already-captured `screenshot_bytes`, respecting the existing `_failure_screenshot_taken` guard so RP never gets a duplicate
- [ ] T016 [US2] Call `_push_screenshot_to_reportportal(...)` from the setup-phase failure branch in the `auth_page` fixture teardown, reusing its captured `screenshot_bytes` and the same guard flag
- [ ] T017 [US2] Confirm test log lines route to the current RP item via the agent's logging handler when enabled (no direct RP-client calls in test bodies — page-object/observability discipline)
- [ ] T018 [US2] Induce a UI failure and run `pytest --reportportal`; confirm the failed RP item shows exactly one screenshot and the log lines
- [ ] T019 [US2] Fail-safe check: run `pytest --reportportal` against a stopped/unreachable endpoint; confirm the run still produces HTML+CSV+Allure and does NOT turn passing tests red (contract C4.4 / SC-005)

**Checkpoint**: Failure evidence lands in ReportPortal; reporting errors never change outcomes.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T020 [P] Verify existing observability outputs still emit with reporting ON and OFF: `results/reports/*.html`, the Hebrew CSV run book, and `results/allure-results/` (Constitution VI)
- [ ] T021 [P] Update `tests/unit/test_failure_screenshot.py` (or add a sibling unit test) to cover `_reportportal_enabled`/`_push_screenshot_to_reportportal` no-op behavior when the flag is absent, English-only comments
- [ ] T022 [P] Confirm `quickstart.md` commands are accurate end-to-end (up → provision → run → verify → down)
- [ ] T023 [P] Review all changed files for English-only inline comments and confirm zero `core/` changes (`git diff --stat` shows nothing under `core/`)
- [ ] T024 **MANDATORY GATE**: Run `pytest tests/ui/fleet_dashboard/ -m sanity` (no flag) AND `pytest tests/ui/fleet_dashboard/ -m sanity --reportportal` (live stack); both MUST pass 100% (Constitution III / plan C6)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks US1 and US2 (they need the config + inert-when-off proof).
- **US3 (Phase 3)**: Depends only on Setup for the dependency, but is otherwise independent (pure infra). Sequenced before US1/US2 because they need a live server to verify against.
- **US1 (Phase 4)**: Depends on Foundational + a running server (US3).
- **US2 (Phase 5)**: Depends on Foundational + a running server (US3). Independent of US1's verification.
- **Polish (Phase 6)**: Depends on all desired stories; T024 is the final regression gate.

### User Story Dependencies

- **US3 (P1)**: Independent — infrastructure only, no code coupling.
- **US1 (P1)**: Needs config (Phase 2) and a live server (US3) to observe a launch.
- **US2 (P1)**: Needs config (Phase 2) and a live server (US3); independent of US1.

### Within Each User Story

- US2 code order: helper (T013) → screenshot bridge (T014) → wire call-phase (T015) → wire setup-phase (T016) → logs (T017) → verify (T018, T019).
- Commit after each task or logical group.

### Parallel Opportunities

- T004 is [P] (config/settings.py) alongside T003 (pytest.ini) — different files.
- Polish tasks T020, T021, T022, T023 are [P] — different files/checks.
- US3 (infra) can be built in parallel with Phase 2 config work by a second person, since they touch disjoint files.

---

## Parallel Example: Phase 2 + US3

```bash
# Different files, no shared edits — safe to run in parallel:
Task: "Add rp_* block to pytest.ini (T003)"
Task: "Add RP_API_KEY passthrough to config/settings.py (T004)"
Task: "Create docker-compose.reportportal.yml (T006)"
```

---

## Implementation Strategy

### MVP First

1. Phase 1 Setup → Phase 2 Foundational → Phase 3 US3 (server up, existing compose untouched).
2. Phase 4 US1 → **STOP and VALIDATE**: live real-time dashboard is the manager's core ask (MVP).
3. Deploy/demo the live dashboard.

### Incremental Delivery

1. Setup + Foundational + US3 → server ready, isolation proven.
2. US1 → live launch/dashboard → demo (MVP!).
3. US2 → failure screenshots + logs → demo failure analysis.
4. Polish + mandatory fleet regression gate (T024).

---

## Notes

- [P] tasks = different files, no dependencies.
- All `conftest.py` edits are additive and fail-safe; assertions/capture logic are never altered.
- `docker-compose.yml` must show zero diff (T008); ReportPortal lives only in `docker-compose.reportportal.yml`.
- Every new/changed line uses English-only inline comments (spec FR-012 / SC-006).
- Do not declare done until T024 passes 100% both with and without `--reportportal`.
