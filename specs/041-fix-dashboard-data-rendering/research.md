# Phase 0 Research: Fix Skipped Tests and Load Errors

All unknowns from the Technical Context are resolved below. No `NEEDS CLARIFICATION` remains.

## Decision 1 — Root cause of the Alerts `LoadTimeoutError`

- **Decision**: The failure is in `navigate()`, not in the test body. `open_report()` (the shared `dashboard` fixture) calls `navigate()` before any test runs. `AlertsPopulationPage._report_ready_locator()` returns `self._iframe_phrase_locator(self.DISTRICT_CHART)` (`התרעות לפי מחוז`). Under the default 7-day filter the district chart has no data and does not render, so `navigate()` exhausts its budget and raises `LoadTimeoutError` before the test can apply the golden `date_range`.
- **Rationale**: The parent `AlertsAnalysisPage._report_ready_locator()` already uses the stable report title (`DASHBOARD_SEARCH_TERM` = `ניתוח התרעות`); only the population override couples readiness to a data-dependent chart. The chart tests already call `_apply_golden_range()` in their bodies, which proves the range handling works once navigation succeeds.
- **Alternatives considered**:
  - *Raise the timeout again*: Rejected. Both pages already run at `self.timeout = 120_000`; a longer budget only delays the same failure because the chart never renders on empty data.
  - *Apply the range inside `navigate()`*: Rejected. It couples navigation to a specific filter and violates the separation between portal navigation (Layer 0) and domain filtering.

## Decision 2 — The population report-ready anchor

- **Decision**: Override `AlertsPopulationPage._report_ready_locator()` to return `self._iframe_phrase_locator(self.TOTAL_CARD)` (`סה"כ אוכלוסייה`).
- **Rationale**: `TOTAL_CARD` is an all-time total rendered regardless of the date filter, and it only exists on Screen 2, so it confirms the correct screen is loaded without depending on filtered chart data. `before_report_ready_check()` keeps using `DISTRICT_CHART` visibility to decide the Screen 1 → Screen 2 page switch, so screen detection is unaffected.
- **Alternatives considered**:
  - *Use the shared report title* (`ניתוח התרעות`, the parent anchor): Rejected as the sole anchor because the title is visible on both Screen 1 and Screen 2, so `navigate()` could stop before switching to Screen 2.
  - *Keep the district chart*: Rejected — it is the root cause.

## Decision 3 — Status Picture operation selection by name

- **Decision**: Add an `operation` name to the Screen 1 golden block and select it directly on the `FilterName` slicer. The test's `_apply_golden_range()` reads `screen["operation"]` and calls a page method that performs `self._slicer.select("date_range", operation)` and waits for the warning-zones gauge to settle, mirroring the existing settle logic in `set_date_range`.
- **Rationale**: The page already selects `עם כלביא` internally via the `_OPERATION_RANGES` reverse map. Reading the operation name from the golden record and selecting it directly removes the brittle date→operation lookup and the `_date_fields_visible()` branch from the golden path, and makes the chosen window explicit and data-driven.
- **Alternatives considered**:
  - *Keep passing dates and reverse-mapping*: Rejected. The reverse map is implicit, duplicates the window definition, and the user explicitly asked for direct name selection.
  - *Hard-code `עם כלביא` in the test*: Rejected. Expected values and selectors come from the golden record (FR-003/FR-004).

## Decision 4 — Status Picture ready anchor

- **Decision**: Keep the warning-zones gauge card (`UNDER_FIRE_CARD`, `אזורי התרעה תחת ירי`) as the Screen 1 ready anchor.
- **Rationale**: It is a gauge whose scale (maximum) is an all-time figure present regardless of the selected operation, and it is Screen-1-specific. It already satisfies "consistently visible element". No change is needed on this page's ready locator; the slice documents it as compliant.
- **Alternatives considered**:
  - *Switch to the report title*: Rejected — the title is shared across screens and less screen-specific than the gauge card.

## Decision 5 — Preserve skip guards as a safety net

- **Decision**: Leave the `pytest.skip(...)` guards in place. They stop firing once data loads because the readers return populated maps; they remain only for a genuinely absent control.
- **Rationale**: The request is to *resolve* the skips via data loading, not to delete the guards. Deleting them would turn a real missing-control into a confusing hard failure instead of a labeled skip.

## Decision 6 — Timeout budget unchanged

- **Decision**: Do not change `self.timeout`. It is already `120_000` on both Alerts pages.
- **Rationale**: The former 60s→120s bump is already applied (feature 040). This slice changes which locator is awaited, not how long.

## Decision 7 — Scope boundaries

- **Decision**: Edit only the two Alerts sanity test modules, the two Alerts page objects, and the Screen 1 `operation` line in the golden YAML. Do not touch fleet, `core/`, or the root `conftest.py`.
- **Rationale**: Matches FR-008 and the constitution's zero-leakage and test-contract rules. No Layer 0 / Layer 2 change means the fleet smoke gate is not triggered.
