# Feature Specification: Visual Canvas Fallback

**Feature Branch**: `feature/reportportal-integration` (spec directory `020-visual-canvas-fallback`; git checkout stays put)

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Core Visual Scope Enhancement (Generic Canvas Fallback). Pause feature 019 on the current branch. `scope_host` must keep the existing bounding-group lookup, and when the scope is not a group it must search the visible report canvas. No report names in `core/`. Existing unit, fleet smoke, and alerts page 1 tests must stay green."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A section scope still finds that section (Priority: P1)

A validation author passes a scope that is the accessible name of a section on the report. Metric lookup stays inside that section, including when the same title exists elsewhere.

**Why this priority**: Fleet and Alerts page 1 already depend on this. A page-level fallback that runs first would bind the wrong visual.

**Independent Test**: A scope that matches a `role="group"` resolves to that group. The visible-canvas query is not used. Blank scope still searches the whole report frame.

**Acceptance Scenarios**:

1. **Given** a non-empty scope whose accessible name matches a group, **When** a metric is read with that scope, **Then** the search root is that group.
2. **Given** no group has that accessible name, but a group contains the scope text, **When** a metric is read, **Then** the search root is that group.
3. **Given** scope is omitted or blank, **When** a metric is read, **Then** the search root is the report frame, as it is today.

---

### User Story 2 - A page title scopes the visible page (Priority: P1)

A validation author passes a scope that is the page's title text, not a bounding section. The title is a text node. Lookup uses the visuals on the active page and does not spend the action timeout waiting for a group that will never appear.

**Why this priority**: Page-level metrics on the alerts population page cannot be read until this works. The failure today is a timeout, not a wrong number.

**Independent Test**: When neither group query matches, the search root is the set of visual containers that are visible. Hidden pages are not part of that root. Resolving the root itself does not wait the action timeout.

**Acceptance Scenarios**:

1. **Given** a scope that matches no group, **When** the search root is resolved, **Then** it is the visible visual containers, not an empty group locator.
2. **Given** the same title exists on a hidden page and on the visible page, **When** the scope matched no group, **Then** the read uses a container on the visible page.
3. **Given** a scope that matches no group, **When** the root is resolved, **Then** the decision finishes without waiting the action timeout.

---

### User Story 3 - Existing suites stay green (Priority: P1)

A validation author upgrades the shared lookup and re-runs the suites that already pass: unit parity, fleet smoke, and Alerts page 1.

**Why this priority**: The canvas fallback is shared by every report. A regression there fails fleet and alerts together.

**Independent Test**: Those three suites pass after the lookup change. The blocked population-page tests are not the gate for this slice.

**Acceptance Scenarios**:

1. **Given** the lookup change, **When** the unit suite runs, **Then** it passes, including parity-engine tests that call scoped reads.
2. **Given** the lookup change, **When** fleet smoke runs, **Then** it passes at 100%.
3. **Given** the lookup change, **When** Alerts page 1 smoke and parity run, **Then** they pass. Population-page tests are not required to pass in this slice.

---

### Edge Cases

- A scope that matches a group is never widened to the whole visible page, even if a canvas of visual containers also exists.
- Two visuals with the same title on the same visible page are not separated by a page-level scope. That still requires a group scope.
- A scope that matches nothing, including no visible visual with the requested title, still fails the read. The failure is the missing title, not a wait for a missing group.
- An empty visible canvas (report not ready) does not invent a value.
- Rendered 0 versus a blank visual is unchanged.
- The first matching group in document order stays the tier-1 host. This slice does not reorder groups by visibility.
- A hidden page that Playwright still treats as visible (painted box, not hidden) can still contribute a container. This slice uses Playwright's visibility check only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `scope_host` MUST return the report frame when scope is omitted, `None`, or whitespace.
- **FR-002**: A non-empty scope MUST resolve to the first `role="group"` whose accessible name matches the scope, when one exists. The match MUST stay a literal (escaped) pattern.
- **FR-003**: When no group matches by accessible name, and a `role="group"` contains the scope text, the host MUST be the first such group.
- **FR-004**: When neither group query matches, the host MUST be the visible visual containers of the report. The lookup MUST NOT return a group locator that matched nothing.
- **FR-005**: Choosing the host MUST use a non-waiting count. It MUST NOT perform an action that waits the action timeout on a missing group.
- **FR-006**: `core/` MUST NOT contain a report name, page title, metric title, or other label that belongs to one dashboard. The canvas rule MUST use Playwright visibility and generic Power BI structure only.
- **FR-007**: `KPI`, `Chart`, and the parity engine MUST keep calling `scope_host`. Their public method signatures MUST stay the same. Callers MUST NOT pass a locator host.
- **FR-008**: Presence classification, data-mark counting, and displayed-title text MUST keep their current results.
- **FR-009**: The group host MUST NOT be produced by filtering every element (`*`) with the scope text.
- **FR-010**: This slice MUST NOT retarget feature 019 metrics, page objects, or contract rows. It only changes how an unresolved scope is hosted.

### Key Entities

- **Scope**: Opaque caller string. Blank means the whole frame. Non-blank is either a section group or a page-level label.
- **Group host**: A `role="group"` located by accessible name, or by contained text when the name does not match.
- **Visible canvas**: The visual containers Playwright currently treats as visible. This is the host only when no group host exists.
- **Metric lookup**: The existing title search (`KPI`, `Chart`, map container) run inside whichever host was chosen.

## Architectural Constraints *(mandatory for core/portal and page-object work)*

- **AC-001**: Layer 0 (`core/portal`) MUST remain report-agnostic. This feature MUST NOT edit portal login, catalog search, iframe wait, or last-refresh.
- **AC-002**: Domain page objects MUST keep composing `ReportShell`. This feature MUST NOT copy portal steps onto a page.
- **AC-003**: Report-ready state stays on the domain page. The canvas host is not a ready-signal.
- **AC-004**: Public page-object and `KPI` / `Chart` method signatures MUST keep their contracts.
- **AC-005**: Layer 2 MUST stay report-agnostic. `core/` MUST NOT load `data/<report>/` or hardcode a filter name, page title, or metric title.
- **AC-006**: No report page and no report SQL move in this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Resolving a scope that matches no group completes without waiting the action timeout.
- **SC-002**: Fleet smoke (`tests/ui/fleet_dashboard/`) passes at 100%.
- **SC-003**: Alerts page 1 smoke and page 1 parity pass. Population-page tests are outside this gate.
- **SC-004**: The unit suite passes, including the parity-engine unit tests.
- **SC-005**: `core/components/visual.py` contains no dashboard title. A source check fails if Hebrew letters appear in that module.

## Assumptions

- Feature 019 stays on disk and stays paused. The git branch remains `feature/reportportal-integration`. This directory is the active spec.
- The population page title is a text node, not a bounding group. That string stays on the alerts page module. It is the motivating caller, not a constant in `core/`.
- "Visible" means Playwright's visibility filter (`visible=True`). `Locator.filter` has no `has_state` argument in the installed Playwright.
- Inactive report pages are hidden from that visibility check often enough to separate page 1 from the active page. A page hidden only by opacity or by an off-screen box is a residual limit.
- Action timeout observed in the field is the Playwright default (about 30 seconds) on a locator that never matches. The probe that chooses the host must not be that wait.
- Inline comments in the edited Python stay English.
