# Data Model: Visual Canvas Fallback

**Feature**: 020-visual-canvas-fallback | **Date**: 2026-10-14

No stored records. These are the values `scope_host` distinguishes at lookup time.

## Entities

### Scope

| Field | Type | Rule |
|-------|------|------|
| raw | `str \| None` | Caller argument. Opaque. Never interpreted as a report name inside `core/`. |
| normalized | `str` | `str(raw).strip()` when raw is not `None`. |
| kind | enum | `frame` when raw is `None` or normalized is empty. `section` when a group host exists. `page` otherwise. |

Relationships: one scope chooses one host. The same `KPI` or `Chart` instance accepts a different
scope per call.

### Group host

| Field | Type | Rule |
|-------|------|------|
| query | enum | `accessible-name`, then `contained-text`. |
| pattern | regex | `re.compile(re.escape(normalized))`. No added anchors. |
| node | locator | `.first` of the `role="group"` query whose `count()` is greater than zero. |

A group host exists only when the winning query's count is positive. An empty `.first` is not a
group host.

Order is fixed: accessible name wins over contained text. Document order of `.first` is unchanged.
Visibility is not a field of the group host.

### Visible canvas

| Field | Type | Rule |
|-------|------|------|
| selector | string | Generic visual-container classes: `visualContainerHost`, `visual-container-host`, `visualContainer`, `visual-container`, `visual-container-component`, and the substring class forms of those names. |
| visibility | Playwright | `filter(visible=True)`. Not `has_state`. |
| node | locator | The filtered locator, which may match many containers. |

The canvas is not a `role="group"`. It is not `locator("*")`. It does not filter by the scope text.
Hidden containers (no box, `display: none`, `visibility: hidden`) are outside the locator.

### Metric lookup

Unchanged pipeline, new host input:

```text
scope
  └─ scope_host(frame, scope) → frame | group host | visible canvas
       └─ KPI._resolve_card / Chart._container / _map_container
            └─ title pattern inside that host
```

`KPI._scope_host` remains a delegate. It does not grow a second policy.

## Validation rules

1. Blank scope never constructs a group query and never constructs the canvas.
2. A positive group count skips the canvas, even if visible containers also exist.
3. A zero count on both group queries skips returning `group.first`.
4. The canvas selector contains no letters in the Hebrew block and no metric title.
5. `classify_presence` inputs and outputs are not part of this model. A rendered 0 stays `value`.
6. Two titles on one visible page are still one lookup. The canvas does not invent a section.

## State transitions

```text
scope omitted or blank
    → frame

scope text
    → accessible-name group count > 0 → group host
    → else contained-text group count > 0 → group host
    → else visible canvas
```

There is no transition from group host to canvas. There is no error state for "page label". A
missing title after the host is chosen is the existing read failure, not a new state.

## What is not an entity

- Population page title, contract rows, and slicer labels. They stay in feature 019.
- SQL, gauge scales, chart categories, and presence. Unchanged models from features 013–016.
