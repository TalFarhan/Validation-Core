# Phase 0 Research: KPI Group Visual Support

**Feature**: 012-kpi-group-visuals | **Date**: 2026-10-11

This feature had no `NEEDS CLARIFICATION` markers in the Technical Context; the request specifies the file,
the locator change, and the extraction source. Research therefore records the design decisions that shaped
the implementation and the alternatives weighed.

## Decision 1 — Button→group fallback (not replace, not parallel union)

**Decision**: Try `get_by_role("button", name=title)` first; if it resolves to zero elements, fall back to
`get_by_role("group", name=title)`. A single `_resolve_card(title)` returns `(locator, kind)` where kind is
`"button"` or `"group"`.

**Rationale**:
- Preserves the existing `role="button"` behavior byte-for-byte for every current report (fleet smoke
  contract, Constitution III). The button is checked first and, when present, nothing else runs.
- Power BI "card" visuals render as buttons; "multi-row card" / image-backed visuals render as groups. A
  given titled metric is one or the other, so first-match-wins is unambiguous for KPI reads.
- `.count()` on the `.first` button locator is a cheap presence probe that does not wait, so the fallback
  only engages when the button genuinely does not exist.

**Alternatives considered**:
- *Replace button with group*: rejected — breaks every existing button-rendered report.
- *Query both roles and union the results*: rejected — ambiguous ordering and no clear "which node holds the
  value", plus added cost on the common button path.
- *Require the caller to declare the rendering kind*: rejected — leaks a Power BI rendering detail into every
  domain page/contract and defeats the point of an opaque-title component.

## Decision 2 — Value source for group visuals: img aria-label → img title → group text

**Decision**: For a group, read the inner `img`'s `aria-label`; if empty, its `title`; if still empty, the
group's own `text_content()`.

**Rationale**:
- In Power BI group/image visuals the rendered number is exposed to assistive tech on the data `img`, almost
  always via `aria-label` (occasionally `title`). The group's own accessible name is the *title*, not the value.
- Falling back to the group's inner text keeps the component working if a particular visual surfaces the value
  as text rather than on the image.

**Alternatives considered**:
- *Reuse the button path's last-`<p>` heuristic*: rejected — group visuals back the value with an image, so
  there is frequently no value `<p>` to read.
- *Hardcode `aria-label` only*: rejected — brittle; the two-step attribute fallback plus text fallback costs
  nothing and improves robustness.

## Decision 3 — Numeric extraction from mixed labels

**Decision**: Add `extract_kpi_value_text(raw)` that strips bidi marks, then returns the longest numeric run
found via a regex allowing internal thousands separators / decimals / spaces (`_NUMBER_TOKEN`). If no number
is present it returns the cleaned text so downstream parsing raises a meaningful error.

**Rationale**:
- Group `aria-label`s commonly bundle the Hebrew title with the value (e.g. `"אזורי התרעה ... 1,234"`). Feeding
  that whole string into `normalize_kpi_text` would yield `"...1234"` (unparseable). Extracting the numeric
  token first keeps the existing normalize → `_to_number` pipeline intact.
- "Longest numeric run" is a safe single-value heuristic: KPI labels carry exactly one figure, and titles in
  this report are spelled-out Hebrew words (e.g. "שלושים יום") with no competing digits.
- Keeps `normalize_kpi_text` semantics and its existing unit tests unchanged — the new behavior is additive.

**Alternatives considered**:
- *First numeric run instead of longest*: rejected — less robust if a label ever carries an incidental short
  number before the value; "longest" prefers the full figure (`"1,234"` over a stray `"2"`).
- *Extend `normalize_kpi_text` to drop non-digits*: rejected — would silently merge digits embedded in a title
  into the value and change behavior for the button path.

## Decision 4 — Keep one component (no GroupKPI subclass)

**Decision**: Collapse both renderings inside the existing `KPI` class behind `_resolve_card`; do not add a
new class or component.

**Rationale**: Button and group are two renderings of the same concept (a titled scalar). The parity engine
depends on a single uniform `KPI.number(title)`; a second type would fork that surface and force callers to
choose. Satisfies Constitution VII ("extract shared behavior only") by reusing the existing shared API.

## Open Questions

None. All decisions are reflected in the shipped `core/components/kpi.py`.
