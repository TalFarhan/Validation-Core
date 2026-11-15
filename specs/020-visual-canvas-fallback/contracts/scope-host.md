# Contract: Scope Host (Layer 2)

**Feature**: 020-visual-canvas-fallback | **Module**: `core/components/visual.py` | **Date**: 2026-10-14

Supersedes the feature 014 / 015 rule that a non-blank scope is always a `role="group"`. Blank
scope, the two group queries, and the ban on `locator("*")` stay. The new clause is the visible
canvas when both group queries are empty.

`KPI._scope_host`, `Chart._container`, and the parity engine's map container MUST keep calling
`scope_host`. They MUST NOT grow a parallel host policy.

## Signature

```python
def scope_host(frame: FrameLocator, scope: str | None) -> FrameLocator | Locator: ...
```

The signature MUST NOT change. The return MUST be the frame, one group, or the visible-container
locator. Callers MUST keep passing an opaque string, not a locator.

## Resolution

Given `pattern = re.compile(re.escape(scope.strip()))` for a non-blank scope:

1. **Frame**. If `scope` is `None` or `str(scope).strip()` is empty, return `frame`. Do not query
   groups. Do not query visual containers.
2. **Tier 1, accessible name**. Let `named = frame.get_by_role("group", name=pattern)`. If
   `named.count() > 0`, return `named.first`.
3. **Tier 2, visible canvas**. When no group has that accessible name, return
   `frame.locator(VISUAL_CONTAINERS).filter(visible=True)`. A group that only contains the scope
   text is not a host.

`count()` MUST be the probe. The function MUST NOT call `text_content`, `get_attribute`, `click`,
`wait_for`, or another action on a group that counted zero.

`VISUAL_CONTAINERS` MUST be a comma-separated CSS selector for generic Power BI visual containers:

- `.visualContainerHost`, `.visual-container-host`, `[class*='visualContainerHost']`
- `.visualContainer`, `.visual-container`, `.visual-container-component`
- `[class*='visualContainer']`, `[class*='visual-container']`

It MUST NOT include a report name, a page title, a metric title, or a visual GUID.

## Canvas shape

The tier 2 locator MAY match more than one element. Inner `get_by_role` / `get_by_text` calls MUST
run against that locator so they see descendants of the visible containers only.

Tier 2 MUST NOT:

- filter those containers by the scope string
- use `locator("*").filter(has_text=...)`
- pass `has_state` to `filter` (`visible=True` is the parameter)
- prefer a hidden container over a visible one
- click a page tab or read a catalog

## Unchanged neighbors

- `classify_presence`: `0` with no marks is `"value"`. All `None` and zero marks is `"empty"`.
- `count_data_marks` and `displayed_title_text` keep their current behavior.
- `KPI.number`, `KPI.read_text`, `KPI.scale`, and `Chart.read` keep their signatures, including
  optional `scope`.
- A positive tier 1 count MUST win over the canvas.

## Examples (normative)

| Scope | Groups found | Host |
|-------|----------------|------|
| `None` or `"   "` | ignored | report frame |
| `"Section A"` | accessible name matches | that group |
| `"Section A"` | name misses, a group's text contains it | that group |
| `"Section A"` | both counts are 0 | visible visual containers |
| a page title that is only a text node | both counts are 0 | visible visual containers |

The strings in the table are stand-ins. They MUST NOT appear as literals in `core/`.

## Invariants

- Deciding the tier does not wait the action timeout.
- A scope that matches a group is never widened to the canvas.
- `core/components/visual.py` contains no Hebrew letters.
- Feature 019 files are not required to change for this contract to hold.

## Verification

| Guarantee | Verified by |
|-----------|-------------|
| Blank scope returns the frame and does not build a canvas | `tests/unit/test_scope_host.py` |
| Named group wins and the canvas selector is not queried | `tests/unit/test_scope_host.py` |
| Contained-text group wins when the named count is 0 | `tests/unit/test_scope_host.py` |
| Both counts 0 return `filter(visible=True)` on the container selector | `tests/unit/test_scope_host.py` |
| No Hebrew in `visual.py` | `tests/unit/test_scope_host.py` |
| Fleet section scopes still read | `pytest tests/ui/fleet_dashboard/` |
| Alerts page 1 still reads | `test_dashboard_smoke.py`, `test_db_parity.py` |
| Parity engine still passes scope through | `tests/unit/test_db_parity_engine.py` |
