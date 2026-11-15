# Contract: Alerts Sanity Completion

This slice adds UI test contracts over existing Alerts page readers. It introduces no new
public page-object method and no new SQL. The contracts below are the test-facing behaviors
that `/speckit-tasks` and the implementation must satisfy.

## Reused page-object readers (unchanged surface)

| Method | Page | Signature | Used by |
|--------|------|-----------|---------|
| `set_hierarchy_level(level)` | `AlertsPopulationPage` | `(level: str) -> bool` (`"nafa"`/`"rashut"`/`"yeshuv"`) | Screen 2 daily-average tests |
| `set_district_aggregation(mode)` | `AlertsPopulationPage` | `(mode: "sum" \| "average") -> None` | Screen 2 daily-average tests |
| `read_district_labels()` | `AlertsPopulationPage` | `() -> dict[str, int]` | Screen 2 daily-average tests |
| `read_top_10_settlements()` | `StatusPicturePage` | `() -> dict[str, int]` | Screen 1 tie test |
| `set_date_range(start, end)` | both | `(str, str) -> None` (DD/MM/YYYY) | both screens |

These names and return types MUST NOT change (AC-003).

## Changed page-object value (not surface)

| Attribute | Page | Before | After |
|-----------|------|--------|-------|
| `timeout` | `AlertsPopulationPage` | `60_000` | `120_000` |
| `timeout` | `StatusPicturePage` | `60_000` | `120_000` |

`page.set_default_timeout(self.timeout)` and `set_default_navigation_timeout(self.timeout)`
follow the new value. `LoadTimeoutError` MUST still raise on an exhausted budget.

## Screen 2 daily-average test contract

For each `level` in `("nafa", "rashut", "yeshuv")`, a new test MUST:

1. Apply the Screen 2 golden date range (`_apply_golden_range`).
2. `if not page.set_hierarchy_level(level): pytest.skip("Missing page object method for hierarchy level <level>")`.
3. `page.set_district_aggregation("average")`.
4. `actual = page.read_district_labels()`; `if not actual: pytest.skip(...)`.
5. `_assert_golden_keys(actual, screen["metrics"]["alerts_by_hierarchy"][level]["daily_avg"])`.

A shared helper `_assert_hierarchy_daily_avg(page, level, expected)` SHOULD hold steps 2–5,
mirroring the existing `_assert_hierarchy_sum`.

**Pass**: every golden `daily_avg` name is present with an equal value.
**Skip**: the level control is not visible, or the reader returns an empty map.
**Fail**: a golden name is missing or its value differs — message names the key, the UI value, and the golden value.

## Screen 1 tie-name test contract

`test_screen_1_top_settlements` MUST:

1. Apply the Screen 1 golden date range and read `actual = read_top_10_settlements()`.
2. `if not actual: pytest.skip("Missing Page Object reader for top_10_settlements")`.
3. Compute the **tie value** from the golden `top_10_settlements.values` (the single lowest shared count).
4. Compute the **stable set** = golden entries with count above the tie value; assert each stable
   name is present in `actual` with its golden count.
5. Compute the **golden tie names** = golden entries whose count equals the tie value.
6. Compute the **UI tie slots** = `actual` entries whose name is not in the stable set.
7. Assert `set(ui_tie_names) == set(golden_tie_names)` and every UI tie count equals the tie value.

**Pass**: stable names/counts match and the four golden tie names fill the four UI tie slots in any order.
**Skip**: `actual` is empty.
**Fail**: a stable name/count is wrong; a UI tie slot holds a non-golden name; a tie slot count is not
the tie value; or the tie-slot count differs from four.

## Non-goals / guardrails

- No edit to `data/alerts/db_sanity_am_kalavi.yaml`.
- No edit to any fleet module, `core/`, `db/clients/`, `tests/ui/`, `tests/e2e/`, or the root `conftest.py`.
- No new page object, reader, or SQL client.
- English-only comments inside new or edited functions.
