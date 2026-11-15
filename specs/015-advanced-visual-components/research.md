# Phase 0 Research: Advanced Power BI Visual Components

**Feature**: 015-advanced-visual-components | **Date**: 2026-10-13

Technical Context had no `NEEDS CLARIFICATION` markers. The request names the behaviors, the layer,
and the leakage ban. Research records how those behaviors map onto the current `KPI` reader and the
fleet chart code without copying domain strings into `core/`.

## Decision 1 — Extend `KPI` with a scale result; do not add a `Gauge` class

**Decision**: Keep finding the visual through `KPI` (button, then group, optional `scope` from
feature 014). Add `extract_gauge_scale` and `KPI.scale`. Leave `extract_kpi_value_text` and
`KPI.number` on the feature 012/013 contract.

**Rationale**:
- A gauge is already a titled group. Feature 013 showed the failure is parsing, not a new locator kind.
- `KPI.number` is the parity engine's public call. Changing it for slash pairs would make the longest
  token (often the denominator) swap meaning under existing callers.
- Callers that need limits use `scale`. Callers that need today's current figure keep `number`.

**Alternatives considered**:
- *New `Gauge` component*: rejected — same locate path as `KPI`, second type to keep in sync with `scope`.
- *Teach `extract_kpi_value_text` to return the numerator*: rejected — that helper's contract is the
  current value for labeled/compact gauges and the longest token otherwise. Slash labels are not in
  that contract; a new function carries them.

## Decision 2 — One structured scale: `value`, `minimum`, `maximum`

**Decision**: Return a frozen structure (or equivalent dict) with those three fields. A denominator is
`maximum`. Missing limits are `None`, never `0`. Recognized shapes, in order:

| Shape | Detection | Mapping |
|-------|-----------|---------|
| Labeled | Feature 013 bound chrome followed by a number | Chrome word selects minimum or maximum; the current value is the longest number left after the pairs are removed (same remainder rule as `extract_kpi_value_text`) |
| Compact | Exactly three compact numeric tokens and no bound chrome | First = minimum, second = maximum, last = current |
| Slash pair | Exactly one `number / number` and no other number | Left = value, right = maximum, minimum = `None` |
| Single figure | One number, none of the above | Value only; both limits `None` |
| No number | No numeric token | All three `None` (presence may still be `empty`) |

Numbers are normalized with the existing KPI normalizer (`"1,337"` becomes `1337`) and returned as
`int` when integral, else `float`.

**Rationale**:
- The request allows a list or a dict. Named fields stay unambiguous when minimum is `0` and maximum
  is absent, which a bare list cannot show.
- Feature 013 already fixed compact order as minimum, maximum, current. Reusing it avoids a second
  interpretation of `"0 1,337 3"`.
- A real minimum of `0` is common on gauges. Using `0` as "missing" would hide that bound.

**Alternatives considered**:
- *List `[value, minimum, maximum]`*: rejected — positional nulls are easy to swap at the call site.
- *Separate `denominator` field*: rejected — on these visuals the denominator is the upper bound. A
  second field would invite report-specific names.
- *Hardcode a known population total*: rejected — Constitution II. The right-hand number is whatever
  the label contains.

## Decision 3 — Presence is structural: rendered 0 versus no marks

**Decision**: `classify_presence(numbers, mark_count)` returns `"value"` or `"empty"`.

- Any number in `numbers`, including `0`, returns `"value"`.
- No numbers and `mark_count == 0` returns `"empty"`. The chart or map title does not count as a mark
  or a number.
- No numbers and `mark_count > 0` returns `"value"` with the primary value left `None` (rendered, but
  the number was not readable). Callers MUST NOT substitute `0`.
- A missing series slot on an otherwise rendered chart is `None` for that slot only. It does not flip
  the whole visual to empty and it is not stored as `0`.

`KPI.scale` reads the raw label (before `extract_kpi_value_text` strips bounds). If that parse has a
value, the state is `"value"`. If it has no number, the card's data-mark count is passed to
`classify_presence`.

**Rationale**:
- `KPI.number("")` already raises. Some callers can turn that exception into `0`. An explicit state
  stops that coercion.
- Matching a "no data" caption would put locale copy in `core/`. Mark count and numeric tokens are
  the same on every Power BI visual.
- A zero-height category that still exposes a `0` label is a value. A plot with axes and a title but
  no bars and no numeric data label is empty.

**Alternatives considered**:
- *Treat an unreadable mark as empty*: rejected — a drawn bar is not a blank visual. `None` keeps it
  out of the zero bucket.
- *New `Map` component*: rejected — the request asks for a generic empty check, not map geography.

## Decision 4 — `Chart` reads bars and columns; fleet interaction stays on the fleet page

**Decision**: Add `core/components/chart.py`. It locates a visual by opaque title and optional `scope`,
then returns categories in visual order, one optional number per legend series, the series names, the
displayed title, and presence.

Parse order inside the visual container:

1. Data-mark accessible names (`aria-label` or `title`) that contain a category, an optional series,
   and a number.
2. Otherwise category tick text paired with numeric data labels in that same visual order.
3. Legend names are the non-numeric legend texts, excluding the visual title and the category ticks.
   Series columns follow legend order.

`is_descending(series_index=0)` compares that column with `>=` (ties pass). A `None` in the column
makes the check fail. An empty chart fails the check. A single category passes. `category_count` is
`len(categories)`, not the number of bars.

Power BI container and plot selectors already used on the fleet page (visual container classes, `svg`
text, legend text, bar rects) are generic chrome and may be reused. Fleet tooltip, drilldown, and
hover methods are not moved.

**Rationale**:
- Constitution VII allows the extract once a second dashboard needs the same read. The request states
  that condition. Interaction code is still fleet-specific.
- Sorting category labels inside `core/` would encode language and business order. Numeric order of a
  caller-chosen series index does not.
- Top-N is an assertion the caller writes (`category_count(...) == n`). `core/` does not store `n`.

**Alternatives considered**:
- *Move `MainDashboardPage` chart methods into `Chart`*: rejected — those methods include drill
  captions and tooltip noise lists tied to the fleet report, and Constitution III forbids a drive-by
  rewrite of the smoke surface.
- *Pixel-only bar alignment*: rejected as the primary rule — coordinates drift between layouts.
  Accessible names are the stable source; geometry is only a last resort inside one visual.

## Decision 5 — Displayed title is the visual's text, not the anchor

**Decision**: `displayed_title_text(container)` returns the first non-empty source among the visual
heading, the visual-title node, and the container's accessible name, with bidi marks stripped.
`Chart.displayed_title(anchor, scope)` and the title field on `Chart.read` use it. The anchor is only
the opaque substring Playwright already matches (escaped, unanchored), so a title that has grown past
the anchor still resolves, and the return value is the full current text.

**Rationale**:
- Slicer state changes the title in place. The caller asserts the dynamic phrase. `core/` only
  returns it.
- Putting an example suffix such as a relative date range into `core/` would freeze one report's
  slicer copy.

**Alternatives considered**:
- *Return only the text beyond the anchor*: rejected — the caller may need the whole title, and
  splitting on the anchor is a presentation choice.
- *Exact accessible-name match*: rejected — a dynamic suffix would make the lookup miss. Substring
  match is the same rule `KPI` uses today (`re.escape` without anchors).

## Decision 6 — One `scope_host` implementation

**Decision**: Move the feature 014 host rule into `visual.scope_host` and have `KPI._scope_host`
delegate to it. `Chart` uses the same function. Behavior stays: blank scope → iframe; else named
`role="group"`; else a group filtered by `has_text`; never `locator("*")`.

**Rationale**: Two copies of the "do not match the report root" rule will drift. Delegation is a
straight move of the current body.

**Alternatives considered**:
- *Duplicate the ten lines inside `Chart`*: rejected — the fallback is the easy part to get wrong.
- *Change the host rule*: rejected — feature 014 is the contract.

## Decision 7 — What stays out of scope

**Decision**: No edits to `pages/fleet_dashboard/main_dashboard_page.py`, `tests/helpers/db_parity_engine.py`,
Layer 0, or the parity YAML. No `Map` class. No SQL. No new third-party package. Inline comments in
the new code stay English only.

**Rationale**: The feature is a generic reader. Adopting it on a domain page is a later caller change
and must not ride along with the smoke contract.
