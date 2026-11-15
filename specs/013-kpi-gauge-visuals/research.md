# Phase 0 Research: Power BI Gauge Value Extraction

**Feature**: 013-kpi-gauge-visuals | **Date**: 2026-10-12

This feature had no `NEEDS CLARIFICATION` markers in the Technical Context; the request names the file, the
failing patterns, and the required fallback. Research records the design decisions that shaped the
implementation and the alternatives weighed.

## Decision 1 — Pre-pass inside `extract_kpi_value_text` (do not add a Gauge locator kind)

**Decision**: Detect and strip Gauge scale text inside `extract_kpi_value_text`. Leave `_resolve_card` and
`_read_group_value` unchanged. Gauges already arrive as `kind == "group"` (feature 012) and surface their
figures on the inner `img` `aria-label` / `title` / group text.

**Rationale**:
- The failure is a **parse** bug, not a **find** bug. The group locator already matches; the longest-token
  extractor then concatenates min/max/current.
- Adding `kind == "gauge"` would require DOM heuristics (visual type, extra roles) that are brittle across
  Power BI builds and would put report-specific structure in Layer 2.
- Callers (`KPI.number`, the parity engine) stay on one API.

**Alternatives considered**:
- *New `GaugeKPI` class / `kind == "gauge"` branch*: rejected — same titled-scalar concept; Constitution VII
  forbids an unused second abstraction.
- *Tighten `_NUMBER_TOKEN` globally so ASCII space is never interior*: rejected — would break legitimate
  space-as-thousands labels (`"1 234"`, `"1 234.5"`) that feature 012 explicitly supports on the fallback
  path. The request requires a safe fallback for standard KPI cards.

## Decision 2 — Two observed Gauge text shapes, one current-value rule

**Decision**: Recognize exactly two shapes, both returning only the current (central) value:

| Shape | Example | How the current value is obtained |
|-------|---------|-----------------------------------|
| Labeled | `distinct_alerted_areas 3. ערך מינימלי 0. ערך מקסימלי 1,337.` | Remove each bound-label + following number, then run the existing longest-token extract on the remainder → `"3"` |
| Compact | `0 1,337 3` | Tokenize with a compact number regex (no ASCII space as interior). When **exactly three** tokens remain, return the **last** token → `"3"` |

**Rationale**:
- Labeled form is Power BI's Gauge accessibility string: title, current value, then generic
  "minimum value" / "maximum value" chrome and their figures. Stripping the bound pairs leaves a normal
  mixed label (`"distinct_alerted_areas 3."`) that the existing extractor already handles.
- Compact form is the same three figures without chrome words. Observed order is min, max, current. Taking
  the last token matches the request's `"0 1,337 3"` → `"3"`.
- Exactly-three is the compact detector: `"Population 1 234"` yields two compact tokens (`"1"`, `"234"`)
  and therefore falls through to the space-as-thousands longest-token path. A standard single-figure card
  yields one compact token and also falls through.

**Alternatives considered**:
- *Always take the longest token after splitting*: rejected — on the labeled example the longest figure is
  `"1,337"` (the max), which is the current bug in a different costume.
- *Take the numeric median of three tokens*: rejected — order-independent when current sits strictly
  between min and max, but wrong when current equals or exceeds a bound (e.g. `0, 100, 100` or an over-max
  reading). Last-token matches the observed compact order and the user's example.
- *Caller-declared visual type in the YAML contract*: rejected — leaks a Power BI rendering detail into
  every domain contract and defeats the opaque-title component.

## Decision 3 — Bound labels are generic Power BI chrome (Hebrew + English)

**Decision**: Detect these locale variants of the Gauge min/max chrome, each followed by a compact number
and an optional trailing period:

- Hebrew: `ערך מינימלי`, `ערך מקסימלי`
- English: `Minimum value`, `Maximum value` (case-insensitive)

Do **not** put report metric titles (e.g. `distinct_alerted_areas`, Alerts Hebrew KPI names) in `core/`.

**Rationale**:
- Constitution II forbids report-specific labels in `core/` but already authorizes generic Power BI chrome
  in Layer 2 (slicer "clear all" / Search) and Layer 0 (last-refresh caption). Gauge bound phrases are the
  same class: they are the visual's own scale captions, identical on every report that uses a Gauge.
- Matching English as well as Hebrew keeps the detector locale-complete rather than Alerts-only, which is
  the opposite of domain leakage.
- Pairing each label with the number that follows it is what lets the remainder extractor see only the
  current value.

**Alternatives considered**:
- *Hebrew-only literals*: rejected — works for the current portal locale but would fail on an English
  workspace and looks report-tied.
- *Any three numbers anywhere are a Gauge*: rejected — too aggressive; a future mixed label with an
  incidental extra digit would steal the last token. Compact detection stays at **exactly three** compact
  tokens, and only after the labeled path did not fire.

## Decision 4 — Keep `_NUMBER_TOKEN` (space-as-thousands) on the fallback path

**Decision**: Add `_NUMBER_TOKEN_COMPACT` (no ASCII space) for Gauge detection / bound-pair capture. Do not
change `_NUMBER_TOKEN`. The fallback remains: strip bidi → longest `_NUMBER_TOKEN` match → else cleaned
text.

**Rationale**:
- Feature 012's unit contract (`"Population 1 234"` → `"1 234"`, `"avg 3.5 days"` → `"3.5"`, `"N/A"` →
  `"N/A"`) must stay green (Constitution III).
- Compact tokenization is used only to (a) pull the number after a bound label and (b) decide whether a
  string is a three-token Gauge. It is not the default extractor.

**Alternatives considered**:
- *Remove ASCII space from `_NUMBER_TOKEN`*: rejected — see Decision 1.
- *Normalize first, then split on remaining non-digits*: rejected — `normalize_kpi_text` already drops
  spaces, so `"0 1,337 3"` becomes `"013373"` before any split; that is the failure mode we are fixing.

## Open Questions

None. All decisions are reflected in `core/components/kpi.py` (`extract_kpi_value_text` and the two new
module regexes).
