# Phase 0 Research: Complete Alerts DB Sanity Validations

All Technical Context items are resolved. No `NEEDS CLARIFICATION` remains.

## Decision 1 — Screen 2 daily averages reuse the existing hierarchy readers

- **Decision**: Add three tests to `tests/sanity/alerts_analysis_dashboard/test_data_validation.py`
  that, for each of `nafa`, `rashut`, `yeshuv`, call `set_hierarchy_level(level)`,
  `set_district_aggregation("average")`, and `read_district_labels()`, then compare the
  result to `screen["metrics"]["alerts_by_hierarchy"][level]["daily_avg"]` with the existing
  `_assert_golden_keys` helper. Factor the shared steps into one `_assert_hierarchy_daily_avg`
  helper that mirrors the existing `_assert_hierarchy_sum`.
- **Rationale**: `test_hierarchy_mahoz_daily_avg_matches_db` already proves this exact path
  (average mode + `read_district_labels`) for the mahoz level. The nafa/rashut/yeshuv sums are
  already covered by `_assert_hierarchy_sum`; only their `daily_avg` branch is missing. Reusing
  the readers keeps the page object unchanged (Principle III/IV) and adds no new locator.
- **Alternatives considered**:
  - A new page-object reader for "daily average by level" — rejected: the existing
    `read_district_labels()` already returns name→int in whichever aggregation mode is active,
    so a new reader would duplicate it and widen the public surface for no gain.
  - Asserting the sum of averages — rejected: the golden file gives per-name daily averages, so
    a per-name comparison (the established pattern) is both available and stricter.

## Decision 2 — Screen 1 tie slots are compared by exact name, as an unordered set

- **Decision**: In `test_screen_1_top_settlements`, keep the stable-set assertions (golden count
  above the tie value, names and counts matched exactly). Replace the count-only tie check with:
  compute the golden tie names (entries whose count equals the tie value) from the YAML; take the
  UI rows outside the stable set; assert that their name set equals the golden tie-name set and
  that every tie count equals the tie value.
- **Rationale**: The user explicitly asked to "extract and verify their exact string names from
  the UI, instead of just asserting the row count." Set equality (order-independent) satisfies that
  while tolerating Power BI's reordering of equal counts, which was feature 036's concern.
- **Tension with feature 036 (recorded, resolved)**: [036-top-settlement-ties](../036-top-settlement-ties/spec.md)
  deliberately *removed* exact tie-name checks (FR-005: "MUST NOT require the golden tie names")
  because Power BI shuffles equal counts between loads. This feature reverses that decision at the
  user's direction. The reversal is bounded: names are read from the YAML (not hard-coded), compared
  as a set (not by position), so shuffling of the four equal-count rows still passes. The residual
  risk — a *different* settlement that also has the tie count entering a tie slot — is now treated as
  a failure *by design*, which is precisely the stronger assertion the user requested. This is logged
  in the plan's Complexity Tracking.
- **Alternatives considered**:
  - Keep 036's count-only check — rejected: it cannot detect a non-golden settlement in a tie slot,
    which is the exact case the user wants caught.
  - Ordered/positional name comparison — rejected: Power BI reorders equal counts, so position is not
    stable; set equality is the correct comparison.

## Decision 3 — Timeout bump lives on the two Alerts domain page objects

- **Decision**: Raise `self.timeout` (and the paired `page.set_default_timeout` /
  `set_default_navigation_timeout`) from `60_000` to a larger value (plan target: `120_000`) in both
  `AlertsPopulationPage` and `StatusPicturePage`. Keep the progressive early steps so the fast path is
  unchanged; only the final budget grows.
- **Rationale**: `LoadTimeoutError` is raised by `ReportShell.navigate()` and the wait helpers using
  `self.timeout`. The Alerts pages hard-code `self.timeout = 60_000`, which overrides
  `settings.DEFAULT_TIMEOUT`, so bumping `settings` would not help the Alerts pages. Changing the value
  on the two domain pages is a page-object value change (not a `core/` change and not a new locator), so
  it does not trigger the fleet smoke gate and keeps `core/` report-agnostic.
- **Alternatives considered**:
  - Raise `settings.DEFAULT_TIMEOUT` / `TIMEOUT_STEPS_MS` — rejected: the Alerts pages override
    `self.timeout`, so the change would not reach the Alerts navigate budget, and it would also change
    the fleet pages' budget (out of scope: "do NOT touch the fleet module").
  - Edit `core/portal/page.py` to widen the budget — rejected: forbidden by Principle II (no
    report-specific behavior in `core/`) and would trigger the fleet smoke contract gate.

## Decision 4 — Expected values come only from the golden YAML

- **Decision**: Every expected count and name is read from `data/alerts/db_sanity_am_kalavi.yaml`
  via the module's existing `load_sanity_data()` / `_screen_record()` helpers. The stable/tie
  partition for Screen 1 is derived from the loaded `top_10_settlements.values`.
- **Rationale**: Matches FR-001 and the established pattern in the sibling Alerts sanity modules.
  Keeps a single source of truth and avoids a second, drifting settlement list in the test.
- **Alternatives considered**: Hard-coding the tie names or daily-average values in the test —
  rejected by FR-001 and FR-004/FR-005.

## Decision 5 — Golden file and fleet modules stay unchanged

- **Decision**: `data/alerts/db_sanity_am_kalavi.yaml` is read-only in this slice, and no fleet
  module, `core/` module, or root `conftest.py` is edited.
- **Rationale**: The YAML already contains the three `daily_avg` maps and the `top_10_settlements`
  values needed, so no data edit is required. The user scoped the work to the Alerts dashboards and
  explicitly excluded the fleet module.
- **Alternatives considered**: None needed; the data is already present and correct.
