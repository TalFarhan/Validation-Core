# Phase 1 Data Model: Fix Skipped Tests and Tooltips for Fleet DB Sanity

This slice changes behavior, not schema. The "entities" below are the in-memory
structures the fleet sanity flow already uses; no new persistent model is added.

## Golden record (`data/fleet/db_sanity_all.yaml`) — UNCHANGED values

Top-level sections (loaded by `load_sanity_record`): `summary`, `units_breakdown`,
`pull_source_breakdown`, `vehicle_categories`, `credit_reasons_summary`,
`credited_vehicles_details`.

Relevant to this slice:

- **`credit_reasons_summary`** — mapping of credit reason → count.
  - `אחר: 3`
  - `פקודת רידוד פיקודית: 3`
  - Used by `test_ui_credit_reasons_match_golden` (chart key `withdrawal`).
- **`vehicle_categories`** — list of `{category, actual, standard, rate}`.
  - `expected = {row["category"]: row["actual"]}` is used by
    `test_ui_category_actuals_match_golden` (chart key `category`).

**Validation rule**: metric values are not changed by this slice. The only
permitted edit is an **additive** label alias, and only if a rendered reason
cannot fold to a golden key by normalization (Decision 3 in research).

## Chart segment label mapping (runtime)

- **Source**: `MainDashboardPage.get_chart_segment_labels(chart_key)` → `list[str]`.
- **Fold**: `normalize_label(text)` folds quotation variants and collapses
  whitespace, then `assert_chart_matches` builds `{normalized: original}`.
- **Match**: a golden key matches when `normalize_label(str(name))` is a key of the
  normalized visible map.
- **Invariant**: for the credit-reason pie, both golden reasons MUST be keys of the
  normalized visible map after the fix; pie `"n (x%)"` data chrome is excluded
  without dropping the reason name.

## Chart segment tooltip (runtime)

- **Producer**: `MainDashboardPage.hover_chart_segment(chart_key, label, *, expected_value)` → `str`.
- **New behavior**: robust hover sequence, then a click-to-pin fallback on the
  resolved glyph; return the matched tooltip text.
- **Parsed form**: `parse_tooltip_entries()` → `dict[str, int]` (label → value),
  consumed by `assert_chart_matches` to compare against the golden count.
- **Failure mode**: `LoadTimeoutError` when no tooltip opens within the dynamic
  budget (preserved).

## Dynamic wait budget (runtime)

- **Source**: `self.timeout` (ms) on the fleet page (`120_000`).
- **Derived**: overall hover budget and per-attempt slices are computed from
  `self.timeout` instead of fixed literals. No new field; this is a local
  computation inside the hover helpers.
