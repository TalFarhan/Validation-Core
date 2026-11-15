# Phase 0 Research: YAML-Only UI Blockers

All Technical Context items for the 2026-11-03 YAML-only brief are resolved from the current
page object, the alerts UI tests, and the unit scans that forbid a skip. There are no open
`NEEDS CLARIFICATION` markers.

## Decision 1 — Skip only the alerts parity test

**Decision**: Add `@pytest.mark.skip(reason="Focusing strictly on YAML validation; DB checks temporarily disabled")`
on `test_alerts_db_parity_last_30_days` in `tests/ui/alerts_analysis_dashboard/test_db_parity.py`.

That function is collected by `pytest tests/ui/alerts_analysis_dashboard/` (the alerts UI
smoke path). It is marked `db_parity`, takes the `alerts_db` fixture (`AlertsDBRunner`), and
calls `validate_dashboard_generic` with `data/alerts/alerts_contract.yaml`. Confirmed KPIs in
that contract execute `SELECT ... FROM [FACT].[AlertsRedWeb]`.

The YAML module `tests/sanity/alerts_analysis_dashboard/test_data_validation.py` is not a SQL
test. `load_sanity_data()` reads `data/alerts/db_sanity_am_kalavi.yaml`. Those tests are not
skipped, even though their names end in `_matches_db`.

`alerts_db` is not autouse. Skipping its only caller means smoke does not open a connection.
The fixture, `db/clients/alerts.py`, and the contract file stay.

**Rationale**: The brief isolates UI-to-YAML and ignores direct SQL while `[FACT].[AlertsRedWeb]`
is failing the smoke path. A decorator leaves the body in place so the check can return.
Deleting SQL or skipping the YAML suite would drop the wrong check.

**Alternatives considered**:

- Skip every `*_matches_db` sanity test. Rejected — those tests never open SQL, and the brief
  keeps YAML validation.
- Delete or stub `[FACT].[AlertsRedWeb]` in the contract. Rejected — the brief says not to
  edit YAML, and the contract is how the check comes back.
- Call `pytest.skip()` inside the function. Rejected — three unit tests ban the substring
  `pytest.skip`, and the brief asks for the decorator.

## Decision 2 — Relax only the `mark.skip` source scans

**Decision**: In `tests/unit/test_db_parity_engine.py`, remove `assert "mark.skip" not in ...`
from `test_remaining_visuals_use_stub_sql`, `test_alerts_stubs_do_not_hide_connection_errors`,
and `test_population_page_stubs`. Keep `assert "pytest.skip" not in ...` and
`assert "importorskip" not in ...`.

**Rationale**: `@pytest.mark.skip` contains the substring `mark.skip` and does not contain
`pytest.skip` or `importorskip`. Leaving the `mark.skip` asserts makes the unit file fail as
soon as the decorator is added. Keeping the other two bans still rejects a body-level skip
and an import skip.

**Alternatives considered**:

- Leave the unit asserts and use a different skip mechanism that hides the string. Rejected —
  that dodges the contract the unit file is enforcing and is not the decorator the brief names.
- Delete the three unit tests. Rejected — they also lock stub SQL and `exclude_scopes`. Only
  the one assertion changes.

## Decision 3 — Force-click the hierarchy control

**Decision**: `set_hierarchy_level` calls `control.click(force=True)` on the locator from
`_hierarchy_control`. That helper returns the first visible `button`, `tab`, or `option`
named `נפה`, `רשות`, or `יישוב` inside the district visual. One click site covers the two
buttons the brief names and `יישוב`, which uses the same method. The visible filter on the
lookup stays. `set_district_aggregation` is a different click and is not changed.

An English comment inside `set_hierarchy_level` says `force=True` bypasses the visual header
toolbar that intercepts the drill-down button.

**Rationale**: Playwright's actionability check fails when the Power BI visual header toolbar
covers the button, even though the button is visible. `force=True` dispatches the click
without that hit test. Removing `filter(visible=True)` from the lookup would click a hidden
duplicate. The failure mode is interception, not a missing node.

**Alternatives considered**:

- Dismiss the toolbar and retry a normal click. Rejected — `_dismiss_overlay` already runs
  before the click, and the header toolbar is part of the visual, not the report overlay.
- `click(force=True)` only for `nafa` and `rashut`. Rejected — `yeshuv` is the same control
  family and the same line. A branch would leave the third button intercepted.

## Decision 4 — Drop the visible filter on the hour title only

**Decision**: `HOUR_CHART` (`גרף התרעות וגם ממוצע לפי שעה`) is the only title that skips
`.filter(visible=True)`.

`_title_anchor` still prefers a visible text match. If that count is 0, it uses
`get_by_text(HOUR_CHART)` and then the exact group, without the visible filter, and returns
the first match that has a `visualContainer` or `visual-container` ancestor. A hidden tooltip
with no such ancestor is skipped. The error, when nothing is attached in a visual, says the
hour title is not attached.

`_leave_visual_table`, after Back, waits for that hour title to be attached. It does not call
`to_be_visible` for this title. Every other title keeps `filter(visible=True)` and
`to_be_visible`.

`_report_ready_locator` keeps `filter(visible=True)` on `מרחק מהגבול`.

**Rationale**: Power BI sometimes exposes the hour title in the accessibility tree in a state
Playwright treats as hidden, so the current visible filter raises `Chart '...' title is not
visible` or times out on `to_be_visible`. The comment already in `_title_anchor` says the full
hour title also sits in a hidden tooltip. Preferring a visual-container ancestor keeps that
tooltip from becoming the chart. Applying the same drop to every title would accept hidden
titles on the district, dates, and settlement charts, which this brief does not ask for.

**Alternatives considered**:

- Remove `.filter(visible=True)` for every title in `_title_anchor`. Rejected — the tooltip
  note and the other charts still need a visible anchor.
- Change only the assertion message and keep the filter. Rejected — the brief says the
  visible requirement is what fails.
- Point the hour chart at a new DOM path or visual id. Rejected — no stable visual id is
  part of this page's contract, and a container walk from the title already exists once the
  title node can be found.

## Preserved from the page-switch research

`before_report_ready_check` still force-clicks the inner `ניתוח התרעות` tab inside
`ניווט בין עמודים` / `Page navigation` and returns when `מרחק מהגבול` is visible. That
behavior is already implemented. This slice does not edit it. The earlier research decisions
for the hour `התרעות` column, Show-as-a-table teardown, quote folding, and the warned-card
date wait stay in force and are not reopened.

---

# Phase 0 Research: Screen 2 Page-Switch Click

All Technical Context items are known from the current hook, `ReportShell.navigate`, and the
2026-11-03 page-switch brief. There are no open `NEEDS CLARIFICATION` markers.

## Decision 1 — Click the inner Screen 2 tab, with force

**Decision**: `before_report_ready_check` clicks the Screen 2 page tab inside the page-navigation
visual, not the visual's own chrome.

The rail is the visible `navigation`, `group`, or label named `ניווט בין עמודים`
(`_PAGE_NAV_LABEL`) or `Page navigation` (`_PAGE_NAV_LABEL_EN`), searched on
`self._report_frame()` only.

Inside that rail, the target is the first visible exact match of `PAGE_TITLE`
(`ניתוח התרעות`) across `button`, `tab`, `link`, `option`, and exact text. The click is
`click(force=True)`. A 400 ms `page.wait_for_timeout` follows so Power BI can apply the page
change before the anchor is checked. `no_wait_after=True` is not used. `networkidle` is not used.

If that inner locator matches nothing, the hook falls back to the first visible rail control
(the existing Hebrew/English link, button, and label union) and still uses `click(force=True)`.

The comment inside the function is English and says the click is the Screen 2 tab inside the
page navigator.

**Rationale**: The current union matches the rail by the visual name `ניווט בין עמודים` and
then clicks `.nth(attempts % count)`. Power BI page navigators put the page name on an inner
button. A forced click on the container does not select Screen 2, which is why
`מרחק מהגבול` never appears. `PAGE_TITLE` is the Screen 2 page name (document title
`ניתוח התרעות | ניתוח התרעות`; golden section "מסך ניתוח התרעות"). The same words are the
report header and the Screen 1 title, so an unscoped `get_by_text("ניתוח התרעות")` would hit
Screen 1. Scoping to the rail is what makes the name safe. `force=True` is already on the
container click and is kept on the inner node, because Power BI often ignores a click that
fails the actionability check. The 400 ms settle replaces `no_wait_after=True`, which returns
before the iframe has switched.

**Alternatives considered**:

- Keep clicking the rail container with `force=True`. Rejected — that is the current miss
  (FR-013).
- Click the first `ניתוח התרעות` node in the frame. Rejected — Screen 1's header and title
  contain that phrase (FR-010, FR-013).
- Use the district chart `התרעות לפי מחוז` as proof the click worked. Rejected — the ready
  contract is `מרחק מהגבול`. `_iframe_phrase_locator` on the chart title can also return early
  on Screen 1 and skip the click.
- `page.wait_for_load_state("networkidle")` after the click. Rejected — Power BI keeps
  connections open, and FR-012 already forbids that wait on this page.
- Edit `ReportShell.navigate` to click the tab. Rejected — Constitution II and VII. The tab
  name is alerts-specific. The hook already exists for this.

## Decision 2 — Retry until `מרחק מהגבול` is visible, without a lifetime cap of 3

**Decision**: The hook's success probe is `_report_ready_locator().is_visible` with a short
timeout (about 500 ms). That method already targets `_SCREEN2_READY_ANCHOR` (`מרחק מהגבול`)
and is not edited.

Each call:

1. If the anchor is visible, return.
2. Otherwise click the inner tab (`force=True`), wait 400 ms, and check the anchor again.
3. Repeat while the anchor is absent, for at most about 8 seconds in this call, then return.

`_page_switch_attempts >= 3` and the 12-second cooldown are removed from the click path.
Those fields must not suppress a later call. The district-chart early return is removed.

The hook does not raise `LoadTimeoutError`. `ReportShell.navigate` still does, after
`self.timeout` (`120_000`), and is not edited.

**Rationale**: `navigate` calls `before_report_ready_check` on every poll of its ready loop
(`core/portal/page.py`). After three clicks the hook returns immediately for the rest of the
page object's life, the distance filter never shows, and the following `expect` raises
`LoadTimeoutError`. Three clicks are not evidence the page changed. The anchor is that
evidence, and it is already the ready locator.

A loop that runs for the full `self.timeout` inside the hook is rejected. `_dashboard_ready`
calls the hook and then expects the ready locator for only 5 seconds. `reload_and_measure_ready_ms`
calls the hook on each short poll and returns elapsed milliseconds. A 120-second hook would
stall those probes and, on a failed `navigate`, would stack on the trailing
`expect(..., timeout=self.timeout)`. About 8 seconds per call is enough for several
force-clicks and anchor checks. The next call from `navigate` tries again until the outer
deadline. A call that finds the anchor visible returns immediately, so a report already on
Screen 2 does not pay the 8 seconds.

**Alternatives considered**:

- Leave the cap at 3 and only add `force=True`. Rejected — `force=True` is already on the
  container click, and the cap still abandons Screen 1.
- One click per call and no in-hook loop, relying only on `navigate`. Rejected as the whole
  fix — the caller does retry the hook, but a single missed click still needs a recheck of
  the anchor before the call returns, and the lifetime cap must go either way. The short
  in-hook loop is the verification the brief asks for.
- Block until `self.timeout` inside the hook. Rejected — it breaks the short probes above.
- Raise `LoadTimeoutError` from the hook. Rejected — that error stays in `ReportShell`, which
  this slice does not edit.

## Decision 3 — Do not change the ready locator

**Decision**: `_SCREEN2_READY_ANCHOR` stays `"מרחק מהגבול"`. `_report_ready_locator` stays:

```python
self._report_frame().get_by_text(self._SCREEN2_READY_ANCHOR).filter(visible=True).first
```

The hook calls that method for its visibility check. It does not copy the phrase into a second
locator and does not call `_iframe_phrase_locator` for the anchor.

**Rationale**: The brief says the ready locator is already correct. The timeout is the missing
page change, not the phrase. FR-010 still forbids a title or a metric card as the ready match.

**Alternatives considered**:

- Point the ready locator back at `ניתוח התרעות` or the piped title. Rejected — those strings
  are on Screen 1 (FR-010).
- Wait on `אוכלוסייה לא ממוגנת`. Rejected — KPI titles on this report are often images.

## Decision 4 — Preserve the hour column, table teardown, date wait, and quote fold

**Decision**: Do not edit `read_hour_daily_avg`, `_visual_table_map`, `_leave_visual_table`,
`set_date_range`, or `_assert_golden_keys`. Do not edit
`data/alerts/db_sanity_am_kalavi.yaml`.

**Rationale**: Those behaviors already match FR-001 through FR-006, FR-011, and FR-012. This
revision's file list is the page-switch hook (FR-007, AC-006).

**Alternatives considered**:

- Re-tuning the hour column or the warned-card wait in the same edit. Rejected — out of scope,
  and a regression risk the brief does not ask for.

## Decision 5 — Files in scope

**Decision**: Edit `before_report_ready_check` in `pages/alerts_analysis/population_page.py`.
A private helper used only by that hook (rail locator, inner tab, anchor check) may live on
the same class. English comments inside those functions. Do not edit `core/portal/page.py`.

**Verification**:

- Alerts UI smoke (`pytest tests/ui/alerts_analysis_dashboard/`) opens the population page and
  reaches `מרחק מהגבול`.
- Sanity (`pytest -m sanity` on `test_data_validation.py`) covers rashut and yeshuv setup,
  which call `navigate` and then read Screen 2.
- Fleet smoke is not required. `ReportShell` and `pages/fleet_dashboard/` are not edited, and
  fleet tests do not import `AlertsPopulationPage`.

## Decision 6 — Out of scope

- Changing `_SCREEN2_READY_ANCHOR`, `_report_ready_locator`, `PAGE_TITLE`, `TOTAL_CARD`,
  `UNPROTECTED_CARD`, or `read_card`.
- Editing `_iframe_phrase_locator` or `navigate` in `core/portal/page.py`.
- `networkidle` anywhere, including Layer 0.
- Decimal parsing or rounding of the `ממוצע` column.
- Golden YAML edits and edits to `_assert_golden_keys`.
- Removing `pytest.skip` guards.
- Lifting the page-tab click into `core/`.
- Credit, fleet, or status-picture modules.
