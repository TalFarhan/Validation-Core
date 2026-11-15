# Phase 0 Research: Visual Canvas Fallback

**Feature**: 020-visual-canvas-fallback | **Date**: 2026-10-14

No `NEEDS CLARIFICATION` markers remain. The technical context is closed by the decisions below.

## Decision 1 — Stay on the current branch and pause 019

**Decision**: Keep git checkout `feature/reportportal-integration`. Pin `.specify/feature.json` at
`specs/020-visual-canvas-fallback`. Do not edit feature 019's page, contract, or tests in this
slice.

**Rationale**: The user asked to pause 019 and keep the branch. The blocked population reads need a
Layer 2 host fix before those tests are meaningful. Mixing the host fix into 019's plan would hide
a framework change inside a page-2 slice.

**Alternatives considered**:

- *New git branch via `/speckit-git-feature`*: rejected. The request says to keep the current branch.
- *Patch 019's research note that forbids changing `scope_host`*: rejected for this command. 019
  stays as written. This feature is the authorized change to that rule.

## Decision 2 — Two tiers, and `count()` before returning a group

**Decision**: `scope_host` keeps today's order, and it returns a group only when that query's
`count()` is greater than zero.

1. `None` or whitespace → the frame.
2. First `role="group"` whose accessible name matches `re.compile(re.escape(scope.strip()))`, if
   `count() > 0`.
3. Else the first `role="group"` filtered with `has_text` of that pattern, if `count() > 0`.
4. Else the visible canvas (Decision 3).

`Locator.count()` does not use the action timeout. Today's bug is step 3's `return ....first`
when the count is zero: the following `get_attribute` / `text_content` waits for an element that
is not there (Playwright's default action timeout is 30 seconds; `KPI` passes `DEFAULT_TIMEOUT`
when it acts).

**Rationale**: Fleet and Alerts page 1 scopes are real groups. Returning those groups unchanged
preserves Constitution III. The page title on the population page is not such a group, so the
unconditional `.first` is what times out. Checking `count()` makes "does not resolve" a fact
instead of a 30-second wait.

**Alternatives considered**:

- *Drop the `has_text` group fallback*: rejected. Feature 014 uses it for groups whose accessible
  name is empty. Removing it would retarget existing section scopes.
- *Add `visible=True` to tier 1*: rejected. The first matching group in document order is the
  current contract. Filtering tier 1 by visibility could switch which group a duplicated name hits.
- *Raise when no group matches*: rejected. A page-level scope would still fail. The request treats
  that case as the visible page, not as an error.
- *Require the scope text to be visible before using the canvas*: rejected. The page label is not a
  visual title. A second text search would couple the host to where the tab renders. An unmatched
  scope widening to the visible page is the specified behavior; callers that need a section keep
  passing a scope that is a real group.

## Decision 3 — Canvas is `filter(visible=True)` on visual containers

**Decision**: Tier 2 returns:

```text
frame.locator(<generic visual-container selector>).filter(visible=True)
```

The selector is the Power BI container class list already used to bound a visual (container host
and container, including the hyphenated and substring class forms, plus
`visual-container-component`). It is defined once on `visual.py` for this host. `chart.py` and the
fleet page keep their own copies in this slice.

`visible=True` is the installed Playwright 1.61 parameter. `Locator.filter` does not accept
`has_state`. The user's `has_state='visible'` example is the same intent, spelled with the real
argument.

The return value may match many containers. `host.get_by_role(...)` then searches inside each of
them, so a title on a hidden page is not a hit. Callers are not changed to accept a list.

**Rationale**: A single `.first` container would search only the first visual. The page-level host
has to cover every visible visual. A `*` / `has_text` ancestor would include hidden pages and the
report root, which feature 014 already forbids. Playwright's visibility check excludes
`display: none`, `visibility: hidden`, and an empty box, which is how inactive Power BI pages are
usually kept out of the layout.

**Alternatives considered**:

- *Common ancestor of the visible containers*: rejected. Finding that ancestor needs a DOM walk, and
  the ancestor is often the report root that also wraps hidden pages.
- *Viewport intersection in addition to `visible=True`*: rejected for this slice. Visuals below the
  fold on the active page have a box and must remain readable. A hidden page that is only
  `opacity: 0` or parked off-screen with a real box can still match `visible=True`. That residual
  is recorded in the spec; it is not solved by clipping to the viewport.
- *Hardcode the population page title and click its tab inside `core/`*: rejected. Constitution II.
  The caller already passes the scope string. `core/` only sees that no group owns it.

## Decision 4 — What stays unchanged

**Decision**: Do not change `classify_presence`, `count_data_marks`, `displayed_title_text`,
`KPI.card` / `read_text` / `value` / `number` / `scale`, `Chart.read`, or
`_map_container`'s title walk. Update the `KPI._scope_host` docstring so it no longer says every
non-blank scope is a group. Do not import the fleet page into `core/`.

**Rationale**: The timeout is the host, not the parser. A wider edit would put fleet and alerts
reads at risk for no requirement.

**Alternatives considered**:

- *Share one selector constant by editing `chart.py` and the fleet page now*: rejected. The user
  limited the slice to the host upgrade. Duplicating the generic class list inside `visual.py`
  avoids a drive-by refactor. The classes are Power BI chrome, not a report label.

## Decision 5 — Regression boundary

**Decision**: The implementation gate is:

- `python -m pytest tests/unit/`
- `python -m pytest tests/ui/fleet_dashboard/`
- `python -m pytest tests/ui/alerts_analysis_dashboard/test_dashboard_smoke.py tests/ui/alerts_analysis_dashboard/test_db_parity.py`

`tests/ui/alerts_analysis_dashboard/test_population_invariants.py` is feature 019 and is not
required to pass before this slice is done. A source assertion scans `core/components/visual.py`
for Hebrew letters so a report title cannot land in that module unnoticed.

**Rationale**: The user asked for unit parity, fleet smoke, and Alerts page 1, and asked to return
to the blocked 019 tests only after those are green. Page 1 parity is `test_db_parity.py` in the
alerts UI suite. The unit parity engine is `tests/unit/test_db_parity_engine.py`, which is inside
`tests/unit/`.

**Alternatives considered**:

- *Run the population invariants as the proof*: rejected for the gate. They are the next slice.
  This plan may make them able to run; it does not expand their assertions.
- *Run every `tests/e2e` module*: rejected. Those are fleet warehouse tests, not the three suites
  named in the request. Fleet smoke remains the constitution gate.
