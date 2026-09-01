# Quickstart: ReportPortal Integration

Exact commands to install the dependency, bring up ReportPortal in isolation,
run the tests with reporting enabled, and tear the stack down. Commands are
shown for PowerShell (the workstation shell); Docker commands are identical on
any OS with the Compose plugin.

> Reporting is **opt-in**. Without the `--reportportal` flag, everything runs
> exactly as today (HTML + Hebrew CSV + Allure only).

## 0. Prerequisites

- Docker Desktop with the Compose plugin (`docker compose version`).
- Python env with project deps installed.

## 1. Install the dependency

```powershell
pip install -r requirements.txt
```

## 2. Bring up the ReportPortal stack (isolated file)

```powershell
# Start ReportPortal in the background from its OWN compose file.
# The existing docker-compose.yml is never referenced here.
docker compose -f docker-compose.reportportal.yml up -d

# Watch until the stack is healthy (Ctrl+C to stop watching).
docker compose -f docker-compose.reportportal.yml ps
```

Open the UI at http://localhost:8080 (default). First bring-up runs DB
migrations and may take a minute.

Default demo login: `superadmin` / `erebus` (change it immediately in the UI).

## 3. Create the project + API key (one-time, in the UI)

1. Log in, create/confirm the project matching `rp_project` (`validation_core`).
2. Open **Profile → API Keys**, generate a key.
3. Export it for the shell session (do NOT commit it):

```powershell
$env:RP_API_KEY = "<paste-your-api-key>"
```

## 4. Run tests with ReportPortal enabled

```powershell
# Full UI suite, reporting ON. A launch appears live in the RP UI.
pytest tests/ui --reportportal

# Regression gate (must be 100% green), reporting ON against the live stack.
pytest tests/ui/fleet_dashboard/ -m sanity --reportportal

# Same suite, reporting OFF (proves unchanged behavior — no flag).
pytest tests/ui/fleet_dashboard/ -m sanity
```

Optional per-run overrides (handy in CI or ad-hoc):

```powershell
# Override launch name / endpoint without editing pytest.ini.
pytest tests/ui --reportportal `
  -o rp_launch="Nightly UI" `
  -o rp_endpoint="http://localhost:8080"
```

## 5. Verify the integration

- A launch named from `rp_launch` shows up in the RP UI within seconds and
  updates live (SC-001).
- Induce a failure and confirm the failed item carries the Playwright full-page
  screenshot and log lines (SC-002).
- Confirm the existing outputs are still written: `results/reports/*.html`, the
  Hebrew CSV run book, and `results/allure-results/` (Constitution VI).
- Confirm no diff on the existing compose file:

```powershell
git diff --exit-code docker-compose.yml
```

## 6. Tear down ReportPortal

```powershell
# Stop and remove RP containers (keeps volumes/data).
docker compose -f docker-compose.reportportal.yml down

# Full reset including RP data volumes (optional).
docker compose -f docker-compose.reportportal.yml down -v
```

The `ui-tests` service in `docker-compose.yml` and everything under `results/`
are unaffected by these commands.

## Troubleshooting

- **Port 8080 busy**: set the overridable host port before `up`, e.g.
  `$env:RP_UI_PORT = "8090"` (then browse to that port).
- **Endpoint unreachable during a run**: the run still finishes and still emits
  HTML+CSV+Allure; passing tests stay green (fail-safe contract, SC-005).
- **No launch appears**: confirm `$env:RP_API_KEY` is set in the SAME shell and
  that `--reportportal` was passed.
