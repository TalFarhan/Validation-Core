# Phase 1 Data Model: Gauge Value Extraction

**Feature**: 013-kpi-gauge-visuals | **Date**: 2026-10-12

This feature has no persistent entities (it reads live DOM). The model is an update to feature 012's
value-resolution pipeline: a Gauge-shaped `RawValueText` now yields a single current-value token before
normalize/parse.

## Conceptual Entities

### KpiVisual (unchanged from 012)

A titled scalar located by an opaque title. Gauges resolve as `kind == "group"`; there is no new kind.

| Field | Type | Notes |
|-------|------|-------|
| `title` | str | Opaque accessible name supplied by the caller. |
| `kind` | `"button"` \| `"group"` | Unchanged. Gauges are groups. |
| `locator` | Playwright `Locator` | Unchanged. |

### RawValueText (source unchanged; parse rules extended)

The un-normalized text pulled from the visual **before** numeric cleanup.

| Source by kind | Where read |
|----------------|------------|
| button | last `<p>` text (unchanged; Gauge work does not run here). |
| group | `img` `aria-label` → `img` `title` → group `text_content()` (unchanged). |

`extract_kpi_value_text` now classifies that raw string:

| Shape | Detection | Current-value token |
|-------|-----------|---------------------|
| Labeled Gauge | Bound-chrome regex matches (`ערך מינימלי` / `ערך מקסימלי` / `Minimum value` / `Maximum value` + following number) | Longest `_NUMBER_TOKEN` in the string **after** bound pairs are removed |
| Compact Gauge | No bound chrome, and `_NUMBER_TOKEN_COMPACT` finds **exactly three** tokens | The last compact token |
| Standard (fallback) | Neither shape | Longest `_NUMBER_TOKEN` (space-as-thousands allowed), else cleaned text |

### KpiValue (unchanged)

| Field | Type | Produced by |
|-------|------|-------------|
| value (string) | str | `normalize_kpi_text(read_text(title))` |
| number | `int \| float` | `_to_number(value)` |

## Transformation Pipeline

```text
title
  └─ _resolve_card(title) ───────────────► (locator, kind)          # unchanged
       kind == "button":  last <p> text ────────────────────────────┐
       kind == "group":   img aria-label | img title | group text    │
                          └─ extract_kpi_value_text(raw)             │
                               ├─ labeled Gauge?  strip bound pairs ─┤
                               │                 then longest token ─┤
                               ├─ compact Gauge? last of 3 tokens ───┤
                               └─ else longest _NUMBER_TOKEN ────────┴─► RawValueText

RawValueText ─► normalize_kpi_text ─► KpiValue.value ─► _to_number ─► KpiValue.number
```

## Rules & Invariants

1. **Button path untouched**: `extract_kpi_value_text` is only invoked from `_read_group_value`.
2. **Labeled bound pairs are discarded**: a number that immediately follows Gauge min/max chrome is never
   the current value.
3. **Compact order is min, max, current**: when exactly three compact tokens are present, the last token is
   the current value. Two compact tokens (space-as-thousands split) are **not** a Gauge.
4. **Fallback is feature 012**: non-Gauge strings keep longest `_NUMBER_TOKEN` / cleaned-text behavior.
5. **Separator-preserving extraction**: returned tokens still carry commas/nbsp so `normalize_kpi_text` can
   strip them (`"1,337"` stays `"1,337"` until normalize).
6. **No-number fallback**: unchanged — cleaned text is returned so `_to_number` raises a clear `ValueError`.
7. **Opacity**: `title` is never parsed for meaning. Bound-chrome phrases are generic visual labels, not
   titles.
8. **English comments only** in production and test code.

## New / Changed Symbols

| Symbol | Kind | Status |
|--------|------|--------|
| `_NUMBER_TOKEN_COMPACT` | module regex | NEW — `-?\d[\d.,\u00a0\u202f]*\d\|-?\d` (no ASCII space) |
| `_GAUGE_BOUND_PAIR` | module regex | NEW — chrome label + compact number + optional `.` |
| `extract_kpi_value_text(raw)` | module function | CHANGED — Gauge pre-pass then existing fallback |
| `_NUMBER_TOKEN`, `_strip_bidi`, `normalize_kpi_text`, `_to_number` | — | UNCHANGED |
| `KPI` public methods and locators | — | UNCHANGED |
