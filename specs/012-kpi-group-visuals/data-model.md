# Phase 1 Data Model: KPI Group Visual Support

**Feature**: 012-kpi-group-visuals | **Date**: 2026-10-11

This feature has no persistent entities (it reads live DOM). The "model" here is the component's internal
value-resolution model: the conceptual shapes it works with and the rules that transform a located visual
into a comparable number.

## Conceptual Entities

### KpiVisual (located node)
A titled scalar in the report, located by its opaque title string. Two renderings:

| Field | Type | Notes |
|-------|------|-------|
| `title` | str | Opaque accessible name supplied by the caller; never interpreted in `core/`. |
| `kind` | `"button"` \| `"group"` | Determined by `_resolve_card`: button if a `role="button"` with the title exists, else group. |
| `locator` | Playwright `Locator` | The `.first` match for the resolved role. |

### RawValueText
The un-normalized text pulled from the located visual before numeric cleanup.

| Source by kind | Where read |
|----------------|------------|
| button | `locator.locator("p").last.text_content()` (unchanged). |
| group | inner `img` `aria-label` → inner `img` `title` → `locator.text_content()` (first non-empty). |

### KpiValue (comparable output)
The normalized value the parity engine compares against SQL.

| Field | Type | Produced by |
|-------|------|-------------|
| value (string) | str | `normalize_kpi_text(read_text(title))` — strips bidi marks, commas, whitespace/nbsp. |
| number | `int \| float` | `_to_number(value)` — int when integral, else float. |

## Transformation Pipeline

```text
title
  └─ _resolve_card(title) ───────────────► (locator, kind)
       kind == "button":  read_text ─► last <p> text ─────────────────────────────┐
       kind == "group":   read_text ─► _read_group_value(locator)                  │
                                         └─ img aria-label | img title | group text │
                                             └─ extract_kpi_value_text(raw) ───────►├─► RawValueText
                                                                                    │
RawValueText ─► normalize_kpi_text ─► KpiValue.value ─► _to_number ─► KpiValue.number
```

## Rules & Invariants

1. **Button-first**: if a `role="button"` with the title exists, `kind == "button"` and the group branch
   never runs. (Preserves existing behavior.)
2. **Group value is a single figure**: `extract_kpi_value_text` returns the longest numeric run after bidi
   stripping; KPI labels carry exactly one number.
3. **Separator-preserving extraction**: the extracted token keeps thousands/decimal separators so the
   downstream `normalize_kpi_text` (which removes commas/whitespace/nbsp) parses it correctly.
4. **No-number fallback**: when a label has no digits, `extract_kpi_value_text` returns the cleaned text so
   `_to_number` raises a clear `ValueError` rather than silently returning garbage.
5. **Opacity**: `title` is never parsed for meaning in `core/`; only numeric extraction operates on label text.

## New / Changed Symbols

| Symbol | Kind | Status |
|--------|------|--------|
| `_strip_bidi(raw)` | module function | NEW (factored out of `normalize_kpi_text`) |
| `extract_kpi_value_text(raw)` | module function | NEW |
| `_NUMBER_TOKEN` | module regex | NEW |
| `KPI._resolve_card(title)` | method | NEW |
| `KPI._read_group_value(card)` | method | NEW |
| `KPI.card(title)` | method | CHANGED (delegates to `_resolve_card`; signature identical) |
| `KPI.read_text(title)` | method | CHANGED (branches on kind; button branch identical) |
| `normalize_kpi_text`, `_to_number`, `KPI.value`, `KPI.number` | — | UNCHANGED behavior |
