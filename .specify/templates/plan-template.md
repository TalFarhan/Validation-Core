# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Layered portal**: Shared portal/SSO/iframe/timeout/last-refresh logic
  lives in Layer 0 (`core/portal`). Domain pages MUST inherit or compose
  `ReportShell`. Shared slicer chrome MAY live in Layer 2 (`core/components/`).
- **Zero domain leakage**: `core/` MUST NOT reference vehicles, district,
  fleet KPI titles, slicers, chart titles, or other report-specific labels.
  Report-ready state MUST be a domain locator, predicate, or override.
  Generic last-refresh chrome MAY live in Layer 0 and MUST use text/regex
  inside the report iframe, never dashboard-specific CSS.
- **Test contract**: After Layer 0, Layer 2, or page-object navigation changes, fleet
  smoke tests (`tests/ui/fleet_dashboard/`) MUST pass at 100% via `pytest`.
- **Extract shared only**: Generic last-refresh verification MAY live in
  Layer 0. Power BI slicer chrome MAY live in Layer 2
  (`core/components/`). Do not genericize KPI cards, tabs, charts, tables,
  or drilldown until a second report requires them. Domain filter names
  and catalogs stay outside `core/`.
- **Warehouse truth**: E2E assertions remain UI vs SQL through the read-only
  `db` client. Layer 0 MUST NOT embed business SQL.
- **Observability**: Allure steps, CSV UI logs, screenshots, and traces MUST
  be preserved across refactors.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# Validation Core (this repository) — prefer this layout when planning here:
# core/portal/          # Layer 0 ReportShell (generic portal / SSO / iframe)
# core/components/      # Layer 2 Slicer (dropdown / checkbox / search / clear-all)
# pages/<report>/       # Domain page objects (fleet: pages/fleet_dashboard/)
# tests/ui/<report>/    # Smoke / sanity (test contract for Layer 0 / Layer 2)
# tests/e2e/            # UI↔DB regression
# data/                 # Layer 3 filter catalogs and matrices
# db/                   # Read-only warehouse client
# config/               # Settings from .env

# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
