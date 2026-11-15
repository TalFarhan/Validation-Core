# Feature Specification: Refactor Dependency Inversion — Move `base_page` and `errors` to `core`

**Feature Branch**: `009-core-dependency-inversion`
**Created**: 2026-10-11
**Status**: Ready for planning
**Input**: Resolve the reverse dependency where `core/` imports from `pages/` by relocating the generic UI
infrastructure (`base_page`, generic `errors`) into `core/`, while keeping chart-specific errors in the fleet domain.

## Problem Statement

The `core` layer currently has a reverse dependency on the `pages` layer: `core/portal/page.py` imports
`BasePage` from `pages/base_page.py` and `LoadTimeoutError` from `pages/errors.py`. In the layered
architecture, `core/` MUST be domain-agnostic and MUST NOT depend on the `pages/` directory
(Constitution: Zero Domain Leakage). The current direction of the dependency inverts the intended layering
(`BasePage` → `ReportShell` → domain page), making Layer 0 unusable in isolation and coupling generic
portal chrome to the fleet page tree.

## User Scenarios & Testing

### Primary Scenario

As a framework maintainer, I need the generic `BasePage` and generic error types to live in `core/` so that
`core/portal/page.py` (`ReportShell`) depends only on `core/`, never on `pages/`, and the fleet dashboard
test suite continues to pass unchanged.

### Acceptance Criteria

- **AC1**: `pages/base_page.py` content is available at `core/base_page.py`; no module under `core/` imports
  from `pages/`.
- **AC2**: `pages/errors.py` generic errors (`LoadTimeoutError`) are available at `core/errors.py`.
- **AC3**: `ExpandHierarchyUnavailable` (a fleet chart-specific error containing the Hebrew term `הסתעפות`)
  no longer lives in the generic errors module; it lives in the fleet domain.
- **AC4**: Every `import` across the repository that referenced `pages.base_page` or `pages.errors` is updated
  to the new path (`core.base_page`, `core.errors`, or the fleet error location).
- **AC5**: `pytest tests/ui/fleet_dashboard/` is 100% green with no changes to business logic or UI
  interaction flow (Constitution III — Existing Tests Are the Contract).
- **AC6**: No chart logic is refactored; this is a mechanical move + import-rewrite only.
- **AC7**: All inline code comments within functions are in English only.

## Requirements

### Functional Requirements

- **FR-001**: Relocate `BasePage` to `core/base_page.py` with identical behavior.
- **FR-002**: Relocate generic error types to `core/errors.py` with identical behavior.
- **FR-003**: Move `ExpandHierarchyUnavailable` into the fleet domain
  (`pages/fleet_dashboard/`), either into `main_dashboard_page.py` or a fleet-specific error module.
- **FR-004**: Rewrite all affected imports in `core/`, `pages/`, and `tests/`.
- **FR-005**: Preserve all observability (Allure steps, CSV logs, screenshots, traces) — move does not drop
  run evidence.

### Non-Goals

- No refactor of chart/drilldown logic.
- No behavioral change to portal navigation, slicers, KPIs, or wait policy.
- No change to the warehouse `db` client or SQL.

## Success Criteria

- `core/` has zero imports from `pages/` (verifiable by grep).
- Fleet smoke + the drilldown e2e that uses `ExpandHierarchyUnavailable` import from the new locations.
- Fleet dashboard suite passes at 100%.
